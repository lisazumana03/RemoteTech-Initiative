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
            reset_link = (
                f"{APP_BASE_URL}/reset_password?token={token}"
                if APP_BASE_URL else
                f"reset_password?token={token}"
            )

            emailed = False
            if is_configured():
                emailed = send_email(
                    to_address=email.strip(),
                    subject="RemoteTech password reset",
                    body=(
                        f"Hi,\n\nSomeone (hopefully you!) requested a password reset "
                        f"for the RemoteTech account '{username}'.\n\n"
                        f"Reset your password here (valid {RESET_TOKEN_TTL_MINUTES} minutes):\n"
                        f"{reset_link}\n\n"
                        "If you didn't request this, you can safely ignore this email."
                    ),
                )

            if not emailed:
                # No mail server configured (or the send failed) — this is expected
                # for a small pilot deployment without email infra set up yet.
                # Show the link directly so a teacher/admin can pass it along
                # to the student securely (in person, or via a trusted channel).
                st.warning(
                    "📧 Email isn't configured on this deployment yet, so here's your "
                    "reset link directly. Please don't share it — anyone with this "
                    "link can reset the password."
                )
                st.code(reset_link, language=None)

st.divider()
if st.button("⬅️ Back to Login"):
    st.switch_page("login.py")
