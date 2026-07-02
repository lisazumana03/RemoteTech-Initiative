import streamlit as st
from remotetech_data import init_db, register_user

init_db()

AVATAR_OPTIONS = ["🚀", "🦸", "🧑‍💻", "🌟", "🔥", "🛒", "🧪", "🏅"]

st.title("🚀 RemoteTech — Create an Account")

full_name           = st.text_input("Full Name")
username            = st.text_input("Username")
email               = st.text_input("Email")
password            = st.text_input("Password", type="password")
confirm_password    = st.text_input("Confirm Password", type="password")

st.markdown("#### Choose an Avatar *(optional)*")
avatar = st.selectbox(
    "Avatar",
    AVATAR_OPTIONS,
    index=0,
    label_visibility="collapsed",
)

st.divider()

#===================== POPIA NOTICE ======================
with st.expander("📄 Privacy Notice (POPIA) — please read before registering"):
    st.markdown("""
**RemoteTech collects the following personal information:**

- Full Name - for identification purposes
- Username - account login and display
- Email - for account management and communication
- Learning progress (points, badges, completed quests) - to track your journey
                
**How we use your data:**
- Your progress is shown to you and to your teacher/admin so they can support you.
- Your first name may appear on the class leaderboard.
- We do not sell, share, or use your data for advertising.
                
**Your rights under POPIA (Protection of Personal Information Act, 2013):**
- You may request to view all data we hold about you at any time.
- You may request deletion of your account and all associated data from your Profile page.
- You may contact the system administrator to raise a data concern.

By registering, you consent to the collection and use of this information in accordance with our Privacy Policy.
""")
    
popia_consent = st.checkbox(
    "✅ I have read the Privacy Notice and consent to my personal information being processed as described."
)
terms_accepted = st.checkbox("I agree to the Terms and Conditions")

if st.button("Register", type="primary"):
    if not full_name or not username or not email or not password:
        st.error("Please fill in all fields.")
    elif password != confirm_password:
        st.error("Passwords do not match.")
    elif len(password) < 8:
        st.error("Password must be at least 8 characters.")
    elif not popia_consent:
        st.error("You must consent to the Privacy Notice to register.")
    elif not terms_accepted:
        st.error("Please agree to the Terms and Conditions.")
    else:
        success = register_user(
            full_name=full_name, 
            username=username, 
            email=email, 
            password=password, 
            avatar=avatar, 
            role="student", 
            popia_consent=True
        )
        if success:
            # Pre-load session so full name is available immediately on login
            st.session_state.registered_username = username
            st.session_state.registered_full_name = full_name
            st.success(f"🎉 Welcome, {full_name}! Your account has been created.")
            st.info("You can now login below.")
        else:
            st.error("That username or email is already registered.")

st.divider()
st.markdown("Already registered?")
if st.button("👉 Go to Login"):
    st.switch_page("login.py")