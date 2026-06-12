import streamlit as st

st.set_page_config(page_title="Login", page_icon="🔐")

# Initialize session state for authentication
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.user_name = ""
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
            st.success("Login successful! Welcome to RemoteTech! 🚀")
        else:
            st.error("Invalid credentials. Please try again.")

# If not registered, the user can sign up (for demo, this just shows a message) (Sign up on register.py)
if st.button("Don't have an account? Sign Up"):
    st.info("Please contact your administrator to create an account. (Sign up on register.py)")