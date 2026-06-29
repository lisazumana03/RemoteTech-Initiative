import streamlit as st
from remotetech_data import init_db, register_user

# Create the database/table if it doesn't exist
init_db()

st.title("Create an Account")

full_name = st.text_input("Full Name")
username = st.text_input("Username")
email = st.text_input("Email")
password = st.text_input("Password", type="password")
confirm_password = st.text_input("Confirm Password", type="password")

if st.button("Register"):

    if not full_name or not username or not email or not password:
        st.error("Please fill in all fields.")

    elif password != confirm_password:
        st.error("Passwords do not match.")

    else:
        success = register_user(
            full_name,
            username,
            email,
            password
        )

        if success:
            st.success("Registration successful!")
            st.info("You can now login.")

            # Optional:
            # st.switch_page("login.py")

        else:
            st.error("Username or Email already exists.")