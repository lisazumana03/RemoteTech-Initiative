import streamlit as st

from branding import DEFAULT_BRANDING

st.set_page_config(page_title="RemoteTech", page_icon="🚀", layout="wide")
st.markdown(
    """
    <style>
        .hero { padding: 5rem 1rem 3rem; max-width: 900px; }
        .hero h1 { font-size: 4rem; color: #22d3ee; }
        .hero p { font-size: 1.25rem; max-width: 650px; }
        .feature { border-left: 4px solid #fbbf24; padding: 1rem 1.25rem; margin: 1rem 0; }
    </style>
    """,
    unsafe_allow_html=True,
)
st.markdown(
    """
    <section class="hero">
        <p>REMOTE LEARNING LAB</p>
        <h1>RemoteTech</h1>
        <p>A practical Python adventure for schools: guided quests, safe code execution,
        teacher progress tools, and certificates that make learning visible.</p>
    </section>
    """,
    unsafe_allow_html=True,
)

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("<div class='feature'><b>Learn by building</b><br>Short quests lead to a real mini-project.</div>", unsafe_allow_html=True)
with col2:
    st.markdown("<div class='feature'><b>Teacher visibility</b><br>Class-scoped progress, completion, and activity reports.</div>", unsafe_allow_html=True)
with col3:
    st.markdown("<div class='feature'><b>Ready for schools</b><br>POPIA-aware accounts, safe execution, and white-label settings.</div>", unsafe_allow_html=True)

st.divider()
col_start, col_demo = st.columns(2)
with col_start:
    if st.button("Create a learner account", type="primary", use_container_width=True):
        st.switch_page("register.py")
with col_demo:
    if st.button("Try the demo", use_container_width=True):
        st.switch_page("login.py")

st.caption(f"{DEFAULT_BRANDING['school_name']} © 2026")