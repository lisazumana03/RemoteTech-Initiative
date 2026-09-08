import streamlit as st

from remotetech_data import init_db, verify_reset_token, consume_reset_token

init_db()

st.title("🔑 Reset Your Password")

# Streamlit puts ?token=... from the URL here. We also let people paste it
# manually, in case the link was shared as plain text rather than clicked.
token_from_url = st.query_params.get("token", "")
token = st.text_input("Reset token", value=token_from_url,
                       help="This came from your password reset link or from your teacher/admin.")

if token:
    username = verify_reset_token(token)
    if not username:
        st.error("This reset link is invalid or has expired. Please request a new one.")
    else:
        st.success(f"Token verified for account **{username}**. Choose a new password below.")

        new_password = st.text_input("New Password", type="password")
        confirm_password = st.text_input("Confirm New Password", type="password")

        if st.button("Reset Password", type="primary"):
            if not new_password or not confirm_password:
                st.error("Please fill in both password fields.")
            elif new_password != confirm_password:
                st.error("Passwords do not match.")
            elif len(new_password) < 8:
                st.error("Password must be at least 8 characters.")
            else:
                if consume_reset_token(token, new_password):
                    st.success("✅ Your password has been reset. You can now log in.")
                    if st.button("👉 Go to Login"):
                        st.switch_page("login.py")
                else:
                    st.error("This reset link is no longer valid. Please request a new one.")
else:
    st.info("Enter or paste your reset token above (or use the link from your email).")

st.divider()
if st.button("⬅️ Back to Login", key="back_bottom"):
    st.switch_page("login.py")
if st.button("Request a new reset link"):
    st.switch_page("forgot_password.py")
