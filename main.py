import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

pg = st.navigation([
    st.Page("login.py", title="Login", default=True),
    st.Page("register.py", title="Register"),
    st.Page("remote_tech_app.py", title="Main App"),
    st.Page("profile.py", title="User Profile"),
    st.Page("admin.py", title="Admin Dashboard")
])

pg.run()