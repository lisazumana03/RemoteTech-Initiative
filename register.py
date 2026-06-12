import streamlit as st

st.set_page_config(page_title="Register", page_icon="📝")
st.title("📝 RemoteTech Registration")
# Registration form
with st.form("register_form"):
    full_name = st.text_input("Full Name")
    user_name = st.text_input("Username")
    password = st.text_input("Password", type="password")
    confirm_password = st.text_input("Confirm Password", type="password")
    submit_button = st.form_submit_button("Register")
    
    if submit_button:
        if password != confirm_password:
            st.error("Passwords do not match. Please try again.")
        elif user_name == "" or full_name == "" or password == "":
            st.error("All fields are required. Please fill in all the details.")
        else:
            # For demo purposes, we just show a success message
            st.success(f"Registration successful! Welcome to RemoteTech, {full_name}! 🎉")
            st.info("Please proceed to the login page to access your account. (Login on login.py)")