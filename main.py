import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

login_page = st.Page("login.py", title="Login")
register_page = st.Page("register.py", title="Register")
main_app_page = st.Page("remote_tech_app.py", title="Main App")

pg = st.navigation(
    {
        "Authentication": [login_page, register_page],
        "Application": [main_app_page]
    }
)

pg.run()