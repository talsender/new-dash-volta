# app.py
import sys, os, glob

# Locate the project root reliably on Streamlit Cloud (Python 3.14 exec fix)
_root = None
# Method 1: use __file__ if available and absolute
try:
    _f = __file__
    if os.path.isabs(_f):
        _root = os.path.dirname(_f)
except NameError:
    pass
# Method 2: search Streamlit Cloud's standard mount point
if not _root:
    _hits = glob.glob('/mount/src/*/app.py')
    if _hits:
        _root = os.path.dirname(_hits[0])
# Method 3: cwd fallback
if not _root:
    _root = os.getcwd()

if _root not in sys.path:
    sys.path.insert(0, _root)

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
