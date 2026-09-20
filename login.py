import streamlit as st
from remotetech_data import init_db, login_user, load_user_progress, get_or_create_demo_account

init_db()

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "user_id" not in st.session_state:
    st.session_state.user_id = None

if "username" not in st.session_state:
    st.session_state.username = ""

if "full_name" not in st.session_state:
    st.session_state.full_name = ""

if "avatar" not in st.session_state:
    st.session_state.avatar = "🚀"

st.title("🚀 RemoteTech — Login")

if st.button("About RemoteTech"):
    st.switch_page("landing.py")


def _start_session(user, is_demo=False):
    st.session_state.authenticated = True
    st.session_state.user_id = user["user_id"]
    st.session_state.full_name = user["full_name"]
    st.session_state.username = user["username"]
    st.session_state.db_user_name = user["username"]
    st.session_state.user_name = user["username"]
    st.session_state.role = user["role"]
    st.session_state.avatar = user.get("avatar") or "🚀"
    st.session_state.school = user.get("school", "")
    st.session_state.class_name = user.get("class_name", "")
    st.session_state.is_demo = is_demo

    if is_demo:
        # Skip the DB round-trip for progress — use what get_or_create_demo_account
        # already seeded, since a shared demo account's live DB row shouldn't be
        # treated as "this session's truth" once multiple people are trying it.
        st.session_state.points = user["points"]
        st.session_state.badges = list(user["badges"])
        st.session_state.completed_lessons = set(user["completed_lessons"])
        return

    progress = load_user_progress(user["username"])
    if progress:
        st.session_state.points = progress["points"]
        st.session_state.badges = progress["badges"]
        st.session_state.completed_lessons = progress["completed_lessons"]
    else:
        st.session_state.points = 0
        st.session_state.badges = []
        st.session_state.completed_lessons = set()


username = st.text_input("Username")
password = st.text_input("Password", type="password")

col_login, col_forgot = st.columns([1, 1])
with col_login:
    login_clicked = st.button("Login", type="primary")
with col_forgot:
    if st.button("Forgot password?"):
        st.switch_page("forgot_password.py")

if login_clicked:
    user = login_user(username, password)

    if user:
        _start_session(user)
        st.success(f"Welcome back, {user['full_name']}!")
        st.switch_page("remote_tech_app.py")

    else:
        st.error("Invalid username or password.")

st.divider()
st.markdown("### 🎮 Just want to look around first?")
st.caption("Try every quest with no signup — progress won't be saved.")
if st.button("🎮 Try the Demo (no signup needed)"):
    demo_user = get_or_create_demo_account()
    _start_session(demo_user, is_demo=True)
    st.success("Welcome to the RemoteTech demo!")
    st.switch_page("remote_tech_app.py")

st.markdown("---")
st.caption("Don't have an account? Register below.")
if st.button("👉 Go to Register"):
    st.switch_page("register.py")