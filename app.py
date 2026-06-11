# app.py
import sys
sys.stdout.reconfigure(encoding='utf-8')

import streamlit as st

st.set_page_config(
    page_title="KPI — וולטה סולאר",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

from screens import (dashboard, weekly_kpi, monthly_bonus,
                     agent_management, settings_screen, history)

PAGES = {
    "📊 לוח בקרה":        dashboard,
    "📅 KPI שבועי":       weekly_kpi,
    "💰 בונוסים חודשיים": monthly_bonus,
    "📈 היסטוריה":        history,
    "👥 ניהול נציגים":    agent_management,
    "⚙️ הגדרות":          settings_screen,
}

with st.sidebar:
    st.title("מוקד וולטה סולאר")
    st.markdown("---")
    selection = st.radio("ניווט", list(PAGES.keys()), label_visibility="collapsed")

PAGES[selection].render()
