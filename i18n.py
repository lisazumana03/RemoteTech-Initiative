"""
Minimal UI translation layer, mirroring the pattern in branding.py.

Scope: this translates *interface chrome* (buttons, labels, headings) —
not quest content in quests_seed.json, which is a separate, larger task
(see the note at the bottom of this file).

Usage in any page:
    from i18n import t
    st.title(t("login_title"))
    st.button(t("about_button"))

The active language lives in st.session_state["language"], set once by
language_selector() in main.py, so it persists across every page in the
st.navigation() flow without each page needing its own widget.
"""

import streamlit as st

LANGUAGES = {
    "en": "English",
    "af": "Afrikaans",
    "xh": "isiXhosa",
}

# NOTE: af/xh strings below are starting placeholders, not reviewed
# translations. Have a fluent speaker (ideally a teacher at a pilot
# school) check these before this ships to real classrooms — a wrong
# word in a login screen is a bad first impression, and getting isiXhosa
# noun-class agreement wrong is an easy, visible mistake for a non-speaker
# (or a machine translator) to make.
STRINGS = {
    "login_title": {
        "en": "🚀 RemoteTech — Login",
        "af": "🚀 RemoteTech — Meld aan",
        "xh": "🚀 RemoteTech — Ngena",
    },
    "about_button": {
        "en": "About RemoteTech",
        "af": "Oor RemoteTech",
        "xh": "Malunga neRemoteTech",
    },
    "please_login_first": {
        "en": "Please login first.",
        "af": "Meld asseblief eers aan.",
        "xh": "Cela ungene kuqala.",
    },
}


def language_selector():
    """Call once in main.py, before pg.run(), so it renders in the
    sidebar on every page and sets the session-wide language."""
    if "language" not in st.session_state:
        st.session_state.language = "en"
    st.sidebar.selectbox(
        "🌐 Language / Taal / Ulwimi",
        options=list(LANGUAGES.keys()),
        format_func=lambda code: LANGUAGES[code],
        key="language",
    )


def t(key):
    """Look up `key` in the active language, falling back to English,
    then to the key itself so a missing translation never crashes a page."""
    lang = st.session_state.get("language", "en")
    entry = STRINGS.get(key, {})
    return entry.get(lang) or entry.get("en") or key
