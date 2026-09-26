import os

import streamlit as st
from remotetech_data import (
    init_db, update_profile, update_password, login_user, delete_user_data,
    create_progress_share,
)
from branding import apply_branding, get_branding
from email_utils import send_email, is_configured as is_email_configured

init_db()

if not st.session_state.get("authenticated", False):
    st.warning("Please login first.")
    st.switch_page("login.py")
    st.stop()

apply_branding(get_branding(st.session_state.get("school", "")))

# Same env var forgot_password.py uses to build an absolute reset link —
# reused here so a shared/emailed progress link is a real clickable URL
# instead of a bare path when the deployment's public URL is known.
APP_BASE_URL = os.environ.get("APP_BASE_URL", "").rstrip("/")

AVATAR_OPTIONS = ["🚀", "🦸", "🧑‍💻", "🌟", "🔥", "🛒", "🧪", "🏅"]

if "avatar" not in st.session_state:
    st.session_state.avatar = "🚀"

st.title("👤 My Profile")
st.markdown(f"## {st.session_state.avatar} {st.session_state.full_name}")
st.caption(f"Username: {st.session_state.username}")

st.divider()

st.subheader("📈 Share Progress")
st.caption("Create a read-only link for a parent or teacher, or email it to them directly. It expires after 30 days.")

if st.button("Create Progress Link"):
    if st.session_state.get("is_demo"):
        st.warning("Demo progress links are disabled.")
    else:
        token = create_progress_share(st.session_state.user_name)
        share_path = f"/share?token={token}"
        st.session_state.progress_share_url = f"{APP_BASE_URL}{share_path}" if APP_BASE_URL else share_path

if st.session_state.get("progress_share_url"):
    st.code(st.session_state.progress_share_url, language=None)
    if not APP_BASE_URL:
        st.caption("Append this path to your RemoteTech site address before sharing it.")

    st.markdown("**Email it to a parent or teacher:**")
    recipient_email = st.text_input("Their email address", key="share_email_to")
    if st.button("📧 Email Progress Link"):
        if not recipient_email.strip():
            st.error("Please enter an email address.")
        elif not is_email_configured():
            # Same fallback behaviour as forgot_password.py: no mail server
            # configured on this deployment yet, so point back at the link
            # rather than silently failing.
            st.warning(
                "Email isn't configured on this deployment yet — please copy the link "
                "above and share it directly instead."
            )
        else:
            sent = send_email(
                to_address=recipient_email.strip(),
                subject=f"{st.session_state.full_name}'s RemoteTech progress",
                body=(
                    f"Hi,\n\n{st.session_state.full_name} wanted to share their RemoteTech "
                    f"learning progress with you.\n\nView it here (link expires in 30 days):\n"
                    f"{st.session_state.progress_share_url}\n\n— RemoteTech"
                ),
            )
            if sent:
                st.success(f"Progress link emailed to {recipient_email.strip()}.")
            else:
                st.error("Couldn't send the email right now — please share the link above instead.")

st.divider()

# ====================== EDIT NAME & AVATAR ======================
st.subheader("Edit Profile")

new_full_name = st.text_input("Full Name", value=st.session_state.full_name)
new_avatar = st.selectbox(
    "Choose an Avatar",
    AVATAR_OPTIONS,
    index=AVATAR_OPTIONS.index(st.session_state.avatar)
    if st.session_state.avatar in AVATAR_OPTIONS else 0,
)
new_class_name = st.text_input(
    "Class Code",
    value=st.session_state.get("class_name", ""),
    help="Ask your teacher for your class code. This determines which leaderboard and "
         "class group your teacher sees you in.",
)

if st.button("Save Profile", type="primary"):
    if not new_full_name.strip():
        st.error("Full name cannot be empty.")
    elif st.session_state.get("is_demo"):
        st.warning("Demo accounts can't edit their profile — create a real account to save changes.")
    else:
        update_profile(st.session_state.user_name, new_full_name, new_avatar, new_class_name.strip())
        st.session_state.full_name = new_full_name
        st.session_state.avatar = new_avatar
        st.session_state.class_name = new_class_name.strip()
        st.success("Profile updated!")
        st.rerun()

st.divider()

# ====================== CHANGE PASSWORD ======================
st.subheader("Change Password")

current_password    = st.text_input("Current Password",     type="password", key="current_pw")
new_password        = st.text_input("New Password",         type="password", key="new_pw")
confirm_new_password = st.text_input("Confirm New Password", type="password", key="confirm_new_pw")

if st.button("Update Password"):
    if st.session_state.get("is_demo"):
        st.warning("Demo accounts can't change their password.")
    elif not current_password or not new_password or not confirm_new_password:
        st.error("Please fill in all password fields.")
    elif new_password != confirm_new_password:
        st.error("New passwords do not match.")
    elif len(new_password) < 8:
        st.error("New password must be at least 8 characters.")
    else:
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
    st.metric("📚 Quests Completed", len(st.session_state.get("completed_lessons", set())))

st.divider()

#====POPIA Right to ensure=======
st.subheader("🔒 Your Data Rights (POPIA)")
st.markdown("""Under the **Protection of Personal Information Act (POPIA)**, you have the right to request
deletion of all personal data we hold about you. This will permanently erase your account,
progress, badges, and points. **This action cannot be undone.**
""")

with st.expander("⚠️ Delete my account and all my data"):
    st.warning("This will permanently delete your account and all learning progress.")
    confirm_delete = st.text_input(
        f'Type your username **{st.session_state.username}** to confirm:',
        key="delete_confirm"
    )
    if st.button("🗑️ Permanently Delete My Account", type="primary"):
        if st.session_state.get("is_demo"):
            st.warning("Demo accounts can't be deleted — there's nothing saved to remove.")
        elif confirm_delete != st.session_state.username:
            st.error("Username does not match. Deletion cancelled.")
        else:
            delete_user_data(st.session_state.username)
            st.session_state.clear()
            st.success("Your account and all data have been deleted.")
            st.switch_page("login.py")

st.divider()

if st.button("⬅️ Back to App"):
    st.switch_page("remote_tech_app.py")