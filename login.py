import streamlit as st
from remotetech_data import init_db, login_user, load_user_progress

init_db()

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "user_id" not in st.session_state:
    st.session_state.user_id = None

if "user_name" not in st.session_state:
    st.session_state.user_name = ""

if "full_name" not in st.session_state:
    st.session_state.full_name = ""

if "avatar" not in st.session_state:
    st.session_state.avatar = "🚀"

st.title("🚀 RemoteTech — Login")

username = st.text_input("Username")
password = st.text_input("Password", type="password")

if st.button("Login", type="primary"):
    user = login_user(username, password)

    if user:
        st.session_state.authenticated = True
        st.session_state.user_id = user["user_id"]
        st.session_state.full_name = user["full_name"]
        st.session_state.user_name = user["user_name"]
        st.session_state.role = user["role"]
        st.session_state.points = user["points"]
        st.session_state.badges = user["badges"]
        st.session_state.completed_lessons = user["completed_lessons"]

        progress = load_user_progress(user["user_name"])

        if progress:
            st.session_state.points = progress["points"]
            st.session_state.badges = progress["badges"]
            st.session_state.completed_lessons = progress["completed_lessons"]
        else:
            st.session_state.points = 0
            st.session_state.badges = []
            st.session_state.completed_lessons = set()

        st.success(f"Welcome back, {user['full_name']}!")
        st.switch_page("remote_tech_app.py")

    else:
        st.error("Invalid username or password.")

st.markdown("---")
st.caption("Don't have an account? Use the Register page from the menu.")