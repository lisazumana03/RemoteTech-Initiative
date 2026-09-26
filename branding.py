"""School branding shared by the Streamlit pages."""

import streamlit as st

from db import adapt, get_connection, USE_POSTGRES


DEFAULT_BRANDING = {
    "school_name": "RemoteTech",
    "logo_url": "",
    "primary_color": "#22d3ee",
    "accent_color": "#fbbf24",
}


def init_branding_table():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS school_branding (
            school_name TEXT PRIMARY KEY,
            logo_url TEXT NOT NULL DEFAULT '',
            primary_color TEXT NOT NULL DEFAULT '#22d3ee',
            accent_color TEXT NOT NULL DEFAULT '#fbbf24'
        )
    """)
    conn.commit()
    conn.close()


def get_branding(school_name):
    init_branding_table()
    if not school_name:
        return DEFAULT_BRANDING.copy()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(adapt("""
        SELECT school_name, logo_url, primary_color, accent_color
        FROM school_branding WHERE school_name = ?
    """), (school_name,))
    row = cur.fetchone()
    conn.close()
    if not row:
        values = DEFAULT_BRANDING.copy()
        values["school_name"] = school_name
        return values
    return dict(zip(("school_name", "logo_url", "primary_color", "accent_color"), row))


def save_branding(school_name, logo_url, primary_color, accent_color):
    init_branding_table()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(adapt("""
        INSERT INTO school_branding (school_name, logo_url, primary_color, accent_color)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(school_name) DO UPDATE SET logo_url=excluded.logo_url,
            primary_color=excluded.primary_color, accent_color=excluded.accent_color
    """), (school_name, logo_url.strip(), primary_color, accent_color))
    conn.commit()
    conn.close()


def apply_branding(branding):
    st.markdown(
        f"""
        <style>
            :root {{ --rt-primary: {branding['primary_color']}; --rt-accent: {branding['accent_color']}; }}
            .stButton > button {{ border-color: var(--rt-primary); }}
            h1, h2, h3 {{ color: var(--rt-primary); }}
            .rt-brand {{ display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1rem; }}
            .rt-brand img {{ max-height: 48px; max-width: 180px; object-fit: contain; }}
        </style>
        """,
        unsafe_allow_html=True,
    )
    if branding.get("logo_url"):
        st.markdown(
            f"<div class='rt-brand'><img src='{branding['logo_url']}' alt='School logo'>"
            f"<strong>{branding['school_name']}</strong></div>",
            unsafe_allow_html=True,
        )