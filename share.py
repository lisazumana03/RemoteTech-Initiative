import streamlit as st

from branding import apply_branding, get_branding
from remotetech_data import get_shared_progress, init_db

st.set_page_config(page_title="RemoteTech Progress", page_icon="📈")
init_db()

token = st.query_params.get("token", "")
progress = get_shared_progress(token) if token else None

if not progress:
    st.error("This progress link is invalid or has expired.")
    st.stop()

apply_branding(get_branding(progress["school"]))
st.title(f"📈 {progress['full_name']}'s Progress")
if progress["school"]:
    st.caption(f"{progress['school']}" + (f" · {progress['class_name']}" if progress["class_name"] else ""))

col1, col2, col3 = st.columns(3)
col1.metric("Points", progress["points"])
col2.metric("Quests completed", len(progress["completed_lessons"]))
col3.metric("Badges", len(progress["badges"]))

if progress["badges"]:
    st.subheader("Badges")
    st.write("  ".join(progress["badges"]))

st.caption("Read-only progress summary. This link expires automatically.")