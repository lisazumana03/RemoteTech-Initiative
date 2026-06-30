import streamlit as st

from remotetech_data import init_db, register_user

st.set_page_config(page_title="Register", page_icon="📝")
st.title("📝 RemoteTech Registration")

init_db()  # Initialize the database and create the users table if it doesn't exist

# Registration form
with st.form("register_form"):
    full_name = st.text_input("Full Name")
    user_name = st.text_input("Username")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    confirm_password = st.text_input("Confirm Password", type="password")
    # Checkbox for terms and conditions
    agree_terms = st.checkbox("I agree to the Terms and Conditions")
    
    submit_button = st.form_submit_button("Register")
    
    if submit_button:
        if not agree_terms:
            st.error("You must agree to the Terms and Conditions to register.")
        elif password != confirm_password:
            st.error("Passwords do not match. Please try again.")
        elif user_name == "" or full_name == "" or email == "" or password == "":
            st.error("All fields are required. Please fill in all the details.")
        else:
            # Attempt to register the user
            if register_user(full_name, user_name, email, password):
                st.success(f"Registration successful! Welcome to RemoteTech, {full_name}! 🎉")
                st.info("Please proceed to the login page to access your account. (Login on login.py)")
            else:
                st.error("Username or email already exists. Please choose a different username or email.")