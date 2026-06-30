import streamlit as st
from remotetech_data import (
    init_db,
    update_profile,
    update_password,
    login_user,
)

init_db()

# Guard: must be logged in to view this page
if not st.session_state.get("authenticated", False):
    st.warning("Please login first.")
    st.switch_page("login.py")
    st.stop()

st.title("👤 My Profile")

AVATAR_OPTIONS = ["🚀", "🦸", "🧑‍💻", "🌟", "🔥", "🛒", "🧪", "🏅"]

# Make sure avatar exists in session state
if "avatar" not in st.session_state:
    st.session_state.avatar = "🚀"

st.markdown(f"## {st.session_state.avatar} {st.session_state.full_name}")
st.caption(f"Username: {st.session_state.user_name}")

st.divider()

# ====================== EDIT NAME & AVATAR ======================
st.subheader("Edit Profile")

new_full_name = st.text_input("Full Name", value=st.session_state.full_name)
new_avatar = st.selectbox(
    "Choose an Avatar",
    AVATAR_OPTIONS,
    index=AVATAR_OPTIONS.index(st.session_state.avatar)
    if st.session_state.avatar in AVATAR_OPTIONS
    else 0,
)

if st.button("Save Profile", type="primary"):
    if not new_full_name.strip():
        st.error("Full name cannot be empty.")
    else:
        update_profile(st.session_state.user_name, new_full_name, new_avatar)
        st.session_state.full_name = new_full_name
        st.session_state.avatar = new_avatar
        st.success("Profile updated!")
        st.rerun()

st.divider()

# ====================== CHANGE PASSWORD ======================
st.subheader("Change Password")

current_password = st.text_input("Current Password", type="password", key="current_pw")
new_password = st.text_input("New Password", type="password", key="new_pw")
confirm_new_password = st.text_input(
    "Confirm New Password", type="password", key="confirm_new_pw"
)

if st.button("Update Password"):
    if not current_password or not new_password or not confirm_new_password:
        st.error("Please fill in all password fields.")
    elif new_password != confirm_new_password:
        st.error("New passwords do not match.")
    elif len(new_password) < 6:
        st.error("New password must be at least 6 characters long.")
    else:
        # Verify current password is correct before allowing change
        verified = login_user(st.session_state.user_name, current_password)
        if not verified:
            st.error("Current password is incorrect.")
        else:
            update_password(st.session_state.user_name, new_password)
            st.success("Password updated successfully!")

st.divider()

# ====================== STATS SUMMARY ======================
st.subheader("Your Stats")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("🔥 Points", st.session_state.get("points", 0))
with col2:
    st.metric("🏅 Badges", len(st.session_state.get("badges", [])))
with col3:
    st.metric("📚 Lessons Completed", len(st.session_state.get("completed_lessons", set())))

st.divider()

if st.button("⬅️ Back to App"):
    st.switch_page("remote_tech_app.py")