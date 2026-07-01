import streamlit as st
from remotetech_data import login_user, init_db, load_user_progress

st.set_page_config(page_title="Login", page_icon="🔐")

def go_to_main_app():
    st.experimental_set_query_params(page="main_app")

st.title("🔐 RemoteTech Login")

init_db()

with st.form("login_form"):
    user_name = st.text_input("Username")
    password = st.text_input("Password", type="password")
    submit_button = st.form_submit_button("Login")

    if submit_button:
        user = login_user(user_name, password)

        if user:
            full_name = user["full_name"]
            stored_user_name = user["user_name"]

            st.session_state.authenticated = True
            st.session_state.user_name = full_name or stored_user_name
            st.session_state.db_user_name = stored_user_name
            st.session_state.role = user["role"]
            st.session_state.points = user["points"]
            st.session_state.badges = user["badges"]
            st.session_state.completed_lessons = user["completed_lessons"]
            st.session_state.show_certificate = False

            st.success(f"Welcome back, {st.session_state.user_name}! 🚀")
            st.switch_page("remote_tech_app.py")

        else:
            st.error("Invalid credentials. Please try again.")