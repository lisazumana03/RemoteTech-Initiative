"""
Payment + licensing.

Flow:
  1. A school picks a plan on pricing.py -> create_checkout_session() opens
     a hosted Stripe Checkout page (no card data ever touches this app).
  2. Stripe redirects back to activate.py with ?session_id=...
  3. activate.py calls finalize_checkout_session(), which verifies payment
     with Stripe directly (never trusts the redirect alone — the session_id
     could otherwise be replayed/guessed), then mints a license key.
  4. The raw key is shown to the buyer ONCE. Only its hash is stored,
     the same pattern remotetech_data.py already uses for password-reset
     tokens.
  5. The teacher takes that key to register_school.py, which creates their
     admin account and marks a seat as used.

No webhook endpoint required for this MVP — Streamlit apps don't have a
convenient always-on place to receive webhooks, and confirming on the
redirect (by re-querying Stripe, not by trusting the URL) is good enough
for a low-volume B2B sale where the buyer is sitting there watching the
success page. If volume grows, add a small webhook receiver (e.g. a tiny
FastAPI service) as a second follow-up and keep this function as the
"reconcile on demand" fallback.

Env vars required in production:
  STRIPE_SECRET_KEY       - starts with sk_live_ or sk_test_
  STRIPE_PRICE_ID_SCHOOL  - Stripe Price ID for the "School" plan
  STRIPE_PRICE_ID_DISTRICT - Stripe Price ID for the "District" plan
If STRIPE_SECRET_KEY isn't set, pricing.py falls back to a "Request an
invoice" flow instead of Checkout, so the app still works before Stripe
is configured.
"""

from dotenv import load_dotenv
load_dotenv()

import hashlib
import json
import os
import secrets
from datetime import datetime

from db import get_connection, adapt, USE_POSTGRES

STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "").strip()

PLANS = {
    "school": {
        "label": "Single School",
        "seats": 5,
        "price_display": "R 2 500 / year",
        "price_env": "STRIPE_PRICE_ID_SCHOOL",
    },
    "district": {
        "label": "District (up to 10 schools)",
        "seats": 50,
        "price_display": "R 18 000 / year",
        "price_env": "STRIPE_PRICE_ID_DISTRICT",
    },
}


def stripe_configured():
    return bool(STRIPE_SECRET_KEY)


def _stripe():
    import stripe
    stripe.api_key = STRIPE_SECRET_KEY
    return stripe


# =============================================================================
# DB
# =============================================================================

def init_billing_tables():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS licenses (
            id {"SERIAL PRIMARY KEY" if USE_POSTGRES else "INTEGER PRIMARY KEY AUTOINCREMENT"},
            key_hash TEXT NOT NULL UNIQUE,
            school_name TEXT NOT NULL,
            contact_email TEXT NOT NULL,
            plan TEXT NOT NULL,
            seats INTEGER NOT NULL,
            redeemed_count INTEGER NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'active',
            stripe_checkout_session_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def _hash_key(raw_key):
    return hashlib.sha256(raw_key.encode()).hexdigest()


def _generate_raw_key():
    # Grouped like XXXX-XXXX-XXXX-XXXX so it's easy to read back over email/phone.
    raw = secrets.token_hex(8).upper()
    return "-".join(raw[i:i + 4] for i in range(0, len(raw), 4))


def list_licenses():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT school_name, plan, seats, redeemed_count, status, created_at
        FROM licenses ORDER BY created_at DESC
    """)
    rows = cur.fetchall()
    conn.close()
    return [
        {
            "school_name": r[0], "plan": r[1], "seats": r[2],
            "redeemed_count": r[3], "status": r[4], "created_at": r[5],
        }
        for r in rows
    ]


# =============================================================================
# STRIPE CHECKOUT
# =============================================================================

def create_checkout_session(plan_key, school_name, contact_email, success_url, cancel_url):
    """Returns the hosted Checkout URL to send the buyer to."""
    if plan_key not in PLANS:
        raise ValueError(f"Unknown plan: {plan_key}")
    plan = PLANS[plan_key]
    price_id = os.environ.get(plan["price_env"], "").strip()
    if not price_id:
        raise RuntimeError(f"{plan['price_env']} is not configured.")

    stripe = _stripe()
    session = stripe.checkout.Session.create(
        mode="payment",
        line_items=[{"price": price_id, "quantity": 1}],
        customer_email=contact_email,
        success_url=success_url + "?session_id={CHECKOUT_SESSION_ID}",
        cancel_url=cancel_url,
        metadata={"plan": plan_key, "school_name": school_name},
    )
    return session.url


def finalize_checkout_session(session_id):
    """
    Verify payment with Stripe and mint a license key. Idempotent: calling
    this twice for the same session_id returns the same license record
    (it just won't re-show the raw key — that's only returned the first
    time, matching how password-reset tokens work).
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(adapt("SELECT school_name, plan, seats, status FROM licenses WHERE stripe_checkout_session_id = ?"), (session_id,))
    existing = cur.fetchone()
    conn.close()
    if existing:
        return {"already_processed": True, "school_name": existing[0], "plan": existing[1]}

    stripe = _stripe()
    session = stripe.checkout.Session.retrieve(session_id)
    if session.payment_status != "paid":
        return {"error": "Payment not completed yet."}

    plan_key = session.metadata.get("plan", "school")
    school_name = session.metadata.get("school_name", "Unknown School")
    seats = PLANS.get(plan_key, PLANS["school"])["seats"]
    contact_email = session.customer_details.email if session.customer_details else session.customer_email

    raw_key = _generate_raw_key()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        adapt("""
            INSERT INTO licenses (key_hash, school_name, contact_email, plan, seats, stripe_checkout_session_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """),
        (_hash_key(raw_key), school_name, contact_email, plan_key, seats, session_id),
    )
    conn.commit()
    conn.close()

    return {
        "already_processed": False,
        "license_key": raw_key,
        "school_name": school_name,
        "plan": plan_key,
        "seats": seats,
    }


# =============================================================================
# LICENSE KEY REDEMPTION (used at teacher/admin self-registration)
# =============================================================================

def validate_license_key(raw_key):
    """Returns the license row (as a dict) if the key is active and has a
    free seat, else None."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        adapt("SELECT id, school_name, seats, redeemed_count, status FROM licenses WHERE key_hash = ?"),
        (_hash_key(raw_key.strip()),),
    )
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    license_id, school_name, seats, redeemed_count, status = row
    if status != "active" or redeemed_count >= seats:
        return None
    return {"id": license_id, "school_name": school_name, "seats": seats, "redeemed_count": redeemed_count}


def redeem_seat(license_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(adapt("UPDATE licenses SET redeemed_count = redeemed_count + 1 WHERE id = ?"), (license_id,))
    conn.commit()
    conn.close()
