import streamlit as st
from remotetech_data import init_db, register_user

init_db()

AVATAR_OPTIONS = ["🚀", "🦸", "🧑‍💻", "🌟", "🔥", "🛒", "🧪", "🏅"]

st.title("🚀 RemoteTech — Create an Account")

full_name           = st.text_input("Full Name")
username            = st.text_input("Username")
email               = st.text_input("Email")
class_name          = st.text_input(
    "Class Code",
    help="Ask your teacher for your class code (e.g. 'Sterkspruit-A'). "
         "Leave blank if you don't have one yet — you can add it later on your Profile page.",
)
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
**Information collected:** your name, username, email address, optional school/class code, and learning activity such as points, badges, and completed quests.

**Why it is used:** to create and secure your account, save learning progress, and let authorised school staff support your learning. Your display name may appear on a class leaderboard, depending on the feature and school setup.

**Sharing and providers:** RemoteTech does not sell learner data or use it for advertising. Hosting, email, and payment providers may process information needed to operate the service; the current providers and regions must be listed in the published Privacy Policy.

**Your rights:** you may request access to, correction of, or deletion of your information through the school's authorised contact or the RemoteTech privacy contact listed in the published policy. Deletion may be subject to applicable legal retention obligations and backup schedules.

Read `DATA_POLICY.md` / the published Privacy Policy for full details. This notice is not a substitute for the appropriate lawful basis and authorisations required for children's information under POPIA.
""")
    
popia_consent = st.checkbox(
    "✅ I have read the Privacy Notice and acknowledge how my information is used."
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
        st.error("Please acknowledge the Privacy Notice before registering.")
    elif not terms_accepted:
        st.error("Please agree to the Terms and Conditions.")
    else:
        success = register_user(
            full_name=full_name, 
            username=username, 
            email=email, 
            password=password, 
            avatar=avatar,  
            popia_consent=True,
            class_name=class_name.strip(),
        )
        if success:
            st.success("Account created successfully. You can now log in.")
        else:
            st.error("That username or email is already registered.")

st.divider()
st.markdown("Already registered?")
if st.button("👉 Go to Login"):
    st.switch_page("login.py")