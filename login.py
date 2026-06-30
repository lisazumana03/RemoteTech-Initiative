import streamlit as st
from remotetech_data import login_user, init_db

st.set_page_config(page_title="Login", page_icon="🔐")
def go_to_main_app():
    st.experimental_set_query_params(page="main_app")
    
st.title("🔐 RemoteTech Login")
init_db()
# Login form
with st.form("login_form"):
    user_name = st.text_input("Username")
    password = st.text_input("Password", type="password")
    submit_button = st.form_submit_button("Login")
    
    if submit_button:
        user = login_user(user_name, password)
        # Keep the original demo account working while also supporting registered users.
        if user_name == "akhona" and password == "password123":
            st.session_state.authenticated = True
            st.session_state.user_name = user_name
            st.session_state.db_user_name = None
            st.session_state.points = 850
            st.session_state.badges = ["🔥 First Spell", "🛒 Spaza Boss"]
            st.session_state.completed_lessons = set()
            st.session_state.show_certificate = False
            st.success("Login successful! Welcome to RemoteTech! 🚀")
            st.switch_page("remote_tech_app.py")
        elif user:
            full_name = user["full_name"]
            stored_user_name = user["user_name"]
            st.session_state.authenticated = True
            st.session_state.user_name = full_name or stored_user_name
            st.session_state.db_user_name = stored_user_name
            st.session_state.points = user["points"]
            st.session_state.badges = user["badges"]
            st.session_state.completed_lessons = user["completed_lessons"]
            st.session_state.show_certificate = False
            st.success(f"Login successful! Welcome to RemoteTech, {st.session_state.user_name}! 🚀")
            st.switch_page("remote_tech_app.py")
        else:
            st.error("Invalid credentials. Please try again.")



