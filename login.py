import streamlit as st

st.set_page_config(page_title="Login", page_icon="🔐")
def go_to_main_app():
    st.experimental_set_query_params(page="main_app")
    
st.title("🔐 RemoteTech Login")
# Login form
with st.form("login_form"):
    user_name = st.text_input("Username")
    password = st.text_input("Password", type="password")
    submit_button = st.form_submit_button("Login")
    
    if submit_button:
        # For demo purposes, we use hardcoded credentials
        if user_name == "akhona" and password == "password123":
            st.session_state.authenticated = True
            st.session_state.user_name = user_name
            st.session_state.points = 850
            st.session_state.badges = ["🔥 First Spell", "🛒 Spaza Boss"]
            st.session_state.completed_lessons = set()
            st.success("Login successful! Welcome to RemoteTech! 🚀")
            st.switch_page("remote_tech_app.py")
        else:
            st.error("Invalid credentials. Please try again.")



