import os
import streamlit as st
from remotetech_data import init_db, create_email_verification_token, EMAIL_VERIFICATION_TTL_HOURS
from email_utils import send_email, is_configured

init_db()
st.set_page_config(page_title="Resend Verification — RemoteTech", page_icon="📧")
st.title("📧 Resend email verification")
st.write("Enter the username and email address used to register. For privacy, the message below is the same whether or not the account matches.")
username = st.text_input("Username")
email = st.text_input("Email address")
if st.button("Send verification email", type="primary"):
    if not username.strip() or not email.strip():
        st.error("Enter both fields.")
    else:
        token = create_email_verification_token(username.strip(), email.strip())
        base_url = os.environ.get("APP_BASE_URL", "").rstrip("/")
        link = f"{base_url}/verify_email?token={token}" if token and base_url else ""
        if link and is_configured():
            sent = send_email(email.strip(), "Verify your RemoteTech email address",
                f"Hello,\n\nVerify your RemoteTech email address within {EMAIL_VERIFICATION_TTL_HOURS} hours:\n{link}\n\nIf you did not request this, ignore this email.")
        else:
            sent = False
        st.success("If the details match an unverified account, a verification email will be sent.")
        if not sent:
            st.warning("Email delivery is not configured or could not be completed. For security, no verification link is shown on screen. Contact the application administrator.")
if st.button("Back to Login"):
    st.switch_page("login.py")
