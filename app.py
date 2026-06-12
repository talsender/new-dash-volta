# app.py
import sys, os, glob

_root = None
try:
    _f = __file__
    if os.path.isabs(_f):
        _root = os.path.dirname(_f)
except NameError:
    pass
if not _root:
    _hits = glob.glob('/mount/src/*/app.py')
    if _hits:
        _root = os.path.dirname(_hits[0])
if not _root:
    _root = os.getcwd()

if _root not in sys.path:
    sys.path.insert(0, _root)

import streamlit as st

st.set_page_config(
    page_title="KPI — וולטה סולאר",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

from modules.theme import apply_theme
apply_theme()

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

_NAV_KEY = "_nav_radio"

# Volta Solar V logo — triangular striped arms
_LOGO = (
    '<svg viewBox="0 0 100 90" xmlns="http://www.w3.org/2000/svg" width="76" height="68">'
    # Blue left arm — 5 triangular stripes
    '<polygon points="0,3 10,3 50,87" fill="#173E80"/>'
    '<polygon points="10,3 20,3 50,87" fill="#2060B8"/>'
    '<polygon points="20,3 30,3 50,87" fill="#1B5FAA"/>'
    '<polygon points="30,3 40,3 50,87" fill="#2570CC"/>'
    '<polygon points="40,3 50,3 50,87" fill="#1B5FAA"/>'
    # Gold right arm — 5 triangular stripes
    '<polygon points="50,3 60,3 50,87" fill="#D08800"/>'
    '<polygon points="60,3 70,3 50,87" fill="#F5A800"/>'
    '<polygon points="70,3 80,3 50,87" fill="#E09600"/>'
    '<polygon points="80,3 90,3 50,87" fill="#F5A800"/>'
    '<polygon points="90,3 100,3 50,87" fill="#D08800"/>'
    '</svg>'
)

# Support programmatic navigation: set st.session_state['nav_goto'] = page_name
# from any screen and call st.rerun() to jump to that page.
nav_to = st.session_state.pop("nav_goto", None)
if nav_to and nav_to in PAGES:
    st.session_state[_NAV_KEY] = nav_to

with st.sidebar:
    st.markdown(
        f'<div style="text-align:center;padding:28px 12px 20px;direction:rtl;">'
        f'{_LOGO}'
        f'<div style="color:#EDF2F7;font-size:16px;font-weight:800;margin-top:12px;letter-spacing:0.5px;">Volta Solar</div>'
        f'<div style="color:#4A6A8A;font-size:10px;font-weight:500;margin-top:4px;letter-spacing:1.5px;text-transform:uppercase;">מוקד תיאומים</div>'
        f'</div>'
        f'<div style="height:1px;background:linear-gradient(90deg,transparent,rgba(245,168,0,0.3),transparent);margin:0 16px 20px;"></div>',
        unsafe_allow_html=True,
    )
    selection = st.radio("ניווט", list(PAGES.keys()), label_visibility="collapsed",
                         key=_NAV_KEY)

PAGES[selection].render()
