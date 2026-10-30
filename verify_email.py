import streamlit as st
from remotetech_data import init_db, verify_email_token

init_db()
st.set_page_config(page_title="Verify Email — RemoteTech", page_icon="📧")
st.title("📧 Verify your email")
token = st.query_params.get("token", "")
if not token:
    st.error("This verification link is missing its token. Request a new verification email.")
elif verify_email_token(token):
    st.success("Your email address has been verified. You can now log in to RemoteTech.")
else:
    st.error("This verification link is invalid, expired, or already used. Request a new link and try again.")
if st.button("Go to Login", type="primary"):
    st.switch_page("login.py")
