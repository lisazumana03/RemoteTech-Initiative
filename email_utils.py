"""SMTP email helper for account verification, password recovery, and sharing.

Configure SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, and SMTP_FROM via
environment variables. Never put credentials in source control.
"""

from dotenv import load_dotenv
load_dotenv()
import os
import smtplib
from email.message import EmailMessage

SMTP_HOST = os.environ.get("SMTP_HOST", "").strip()
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
SMTP_FROM = os.environ.get("SMTP_FROM", "RemoteTech <no-reply@example.com>")


def is_configured():
    return bool(SMTP_HOST and SMTP_FROM)


def send_email(to_address, subject, body):
    """Send an email; return False if SMTP is missing or delivery fails."""
    if not is_configured():
        return False
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = SMTP_FROM
    msg["To"] = to_address
    msg.set_content(body)
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            if SMTP_USER:
                server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        return True
    except (OSError, smtplib.SMTPException):
        return False
