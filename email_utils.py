"""
Minimal SMTP email helper for the password-reset flow.

Configured entirely through environment variables so the same code works
locally (where you likely have no mail server) and in production:

    SMTP_HOST       e.g. smtp.sendgrid.net
    SMTP_PORT       default 587
    SMTP_USER
    SMTP_PASSWORD
    SMTP_FROM       default "RemoteTech <no-reply@remotetech.example>"

If SMTP_HOST isn't set, send_email() returns False without raising —
callers (see forgot_password.py) fall back to showing the reset link
directly on-screen, which is the right behaviour for a small classroom
pilot that may not have mail infrastructure set up yet.
"""

import os
import smtplib
from email.message import EmailMessage

SMTP_HOST = os.environ.get("SMTP_HOST", "").strip()
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
SMTP_FROM = os.environ.get("SMTP_FROM", "RemoteTech <no-reply@remotetech.example>")


def is_configured():
    return bool(SMTP_HOST)


def send_email(to_address, subject, body):
    """Best-effort send. Returns True on success, False if unconfigured or failed."""
    if not is_configured():
        return False

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = SMTP_FROM
    msg["To"] = to_address
    msg.set_content(body)

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
            server.starttls()
            if SMTP_USER:
                server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        return True
    except Exception:
        return False
