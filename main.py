import streamlit as st

pages = [
    st.Page("login.py", title="Login", default=True),
    st.Page("register.py", title="Register"),
    st.Page("remote_tech_app.py", title="Main App"),
    st.Page("profile.py", title="User Profile"),
]

if st.session_state.get("role") == "admin":
    pages.append(
        st.Page("admin.py", title="Admin Dashboard")
    )

pg = st.navigation(pages)

pg.run()