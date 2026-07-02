import streamlit as st
from remotetech_data import init_db, register_user

init_db()

st.title("🚀 RemoteTech — Create an Account")

full_name = st.text_input("Full Name")
username = st.text_input("Username")
email = st.text_input("Email")
password = st.text_input("Password", type="password")
confirm_password = st.text_input("Confirm Password", type="password")
terms_accepted = st.checkbox("I agree to the Terms and Conditions")

if st.button("Register", type="primary"):
    if not full_name or not username or not email or not password:
        st.error("Please fill in all fields.")
    elif password != confirm_password:
        st.error("Passwords do not match.")
    elif len(password) < 8:
        st.error("Password must be at least 8 characters.")
    elif not terms_accepted:
        st.error("Please agree to the Terms and Conditions.")
    else:
        success = register_user(full_name, username, email, password)
        if success:
            st.success("Registration successful! You can now login.")
        else:
            st.error("Username or email already exists.")