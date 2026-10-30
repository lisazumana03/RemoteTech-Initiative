import os

import streamlit as st

from remotetech_data import init_db, create_password_reset_token, RESET_TOKEN_TTL_MINUTES
from email_utils import send_email, is_configured

init_db()

# Used to build a clickable reset link when we can actually email one out.
# Set this to your deployed URL, e.g. https://remotetech.streamlit.app
APP_BASE_URL = os.environ.get("APP_BASE_URL", "").rstrip("/")

st.title("🔑 Forgot Password")
st.write(
    "Enter your username and the email address on your account. "
    "If they match, we'll help you reset your password."
)

username = st.text_input("Username")
email = st.text_input("Email")

if st.button("Send Reset Link", type="primary"):
    if not username or not email:
        st.error("Please fill in both fields.")
    else:
        token = create_password_reset_token(username.strip(), email.strip())

        # Always show the same message whether or not it matched, so this
        # page can't be used to check which usernames/emails are registered.
        st.success(
            "If that username and email match an account, a password reset "
            f"link has been sent (valid for {RESET_TOKEN_TTL_MINUTES} minutes)."
        )

        if token:
            reset_link = f"{APP_BASE_URL}/reset_password?token={token}" if APP_BASE_URL else ""
            emailed = bool(reset_link and is_configured() and send_email(
                to_address=email.strip(),
                subject="RemoteTech password reset",
                body=(f"Hi,\n\nA password reset was requested for the RemoteTech account '{username}'.\n\n"
                      f"Reset your password within {RESET_TOKEN_TTL_MINUTES} minutes:\n{reset_link}\n\n"
                      "If you did not request this, ignore this email.")
            ))
            # Do not show account-dependent success/failure details here; that
            # would let visitors infer whether a username/email pair exists.
            # Links are never displayed in the browser.

        st.caption("If you cannot receive account emails, contact your application administrator.")

st.divider()
if st.button("⬅️ Back to Login"):
    st.switch_page("login.py")
