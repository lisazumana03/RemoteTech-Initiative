import streamlit as st
from remotetech_data import init_db, login_user

# Make sure the database exists
init_db()

# Initialize Session State
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "user_id" not in st.session_state:
    st.session_state.user_id = None

if "user_name" not in st.session_state:
    st.session_state.user_name = ""

if "full_name" not in st.session_state:
    st.session_state.full_name = ""

st.title("Login")

username = st.text_input("Username")
password = st.text_input("Password", type="password")

if st.button("Login"):

    user = login_user(username, password)

    if user:

        st.session_state.authenticated = True
        st.session_state.user_id = user[0]
        st.session_state.full_name = user[1]
        st.session_state.user_name = user[2]

        st.success(f"Welcome {user[1]}!")

        st.switch_page("remote_tech_app.py")

    else:
        st.error("Invalid username or password.")