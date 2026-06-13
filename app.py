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

_PAGE_KEY = "_current_page"
_NAV_KEY  = "_nav_radio"
_page_list = list(PAGES.keys())

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

# ── Navigation ────────────────────────────────────────────────────────────
# _current_page is the single source of truth for which page to render.
# The radio widget (key=_nav_radio) provides user interaction; on_change
# keeps _current_page in sync.  Programmatic navigation sets _current_page
# directly (and tries to sync _nav_radio, though widget-state pre-setting
# is not always reliable in all Streamlit versions — _current_page is the
# authoritative fallback).

if _PAGE_KEY not in st.session_state:
    st.session_state[_PAGE_KEY] = _page_list[0]

nav_to = st.session_state.pop("nav_goto", None)
if nav_to and nav_to in PAGES:
    st.session_state[_PAGE_KEY] = nav_to
    try:
        st.session_state[_NAV_KEY] = nav_to  # best-effort radio sync
    except Exception:
        pass

current_page = st.session_state[_PAGE_KEY]


def _on_nav_change():
    st.session_state[_PAGE_KEY] = st.session_state[_NAV_KEY]


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
    st.radio("ניווט", _page_list, label_visibility="collapsed",
             key=_NAV_KEY, on_change=_on_nav_change)

PAGES[current_page].render()
