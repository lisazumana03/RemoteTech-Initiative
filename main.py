import streamlit as st

from i18n import language_selector

language_selector()

pages = [
    st.Page("landing.py", title="About RemoteTech", url_path="about"),
    st.Page("login.py", title="Login", default=True),
    st.Page("register.py", title="Register"),
    st.Page("register_school.py", title="Register a School", url_path="register_school"),
    st.Page("pricing.py", title="Pricing", url_path="pricing"),
    st.Page("activate.py", title="Activate License", url_path="activate"),
    st.Page("forgot_password.py", title="Forgot Password", url_path="forgot_password"),
    st.Page("reset_password.py", title="Reset Password", url_path="reset_password"),
    st.Page("share.py", title="Shared Progress", url_path="share"),
    st.Page("remote_tech_app.py", title="Main App"),
    st.Page("profile.py", title="User Profile"),
]

if st.session_state.get("role") == "admin":
    pages.append(
        st.Page("admin.py", title="Admin Dashboard")
    )

pg = st.navigation(pages)

pg.run()