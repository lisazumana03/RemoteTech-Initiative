import streamlit as st

import billing

billing.init_billing_tables()

st.set_page_config(page_title="RemoteTech — Activate", page_icon="🔑")
st.title("🔑 Activate Your License")

session_id = st.query_params.get("session_id")

if not session_id:
    st.warning("No checkout session found. If you just paid, use the link from your Stripe receipt email, "
               "or go back to Pricing and try again.")
    if st.button("⬅️ Back to Pricing"):
        st.switch_page("pricing.py")
    st.stop()

result = billing.finalize_checkout_session(session_id)

if result.get("error"):
    st.error(result["error"])
elif result.get("already_processed"):
    st.info(
        f"This checkout session was already processed for **{result['school_name']}**. "
        "For security we only show a license key once — if you lost it, contact us and "
        "we'll help you recover access."
    )
else:
    st.success(f"🎉 Payment confirmed for **{result['school_name']}** — {billing.PLANS[result['plan']]['label']} plan.")
    st.markdown("### Your License Key")
    st.code(result["license_key"], language=None)
    st.warning(
        "⚠️ **Save this now** — it's only shown once. Give it to whoever will register "
        f"as the first teacher/admin account for your school (up to {result['seats']} teacher accounts on this license)."
    )
    st.caption("Next step: go to Register a School and enter this key.")
    if st.button("👉 Register a School"):
        st.switch_page("register_school.py")
