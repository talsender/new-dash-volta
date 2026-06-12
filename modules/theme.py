# modules/theme.py
import streamlit as st

_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Heebo:wght@300;400;500;600;700;800;900&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@24,400,0,0&display=swap');

/* ══════════════════════════════════════════════
   CSS VARIABLES
══════════════════════════════════════════════ */
:root {
  --bg:          #04080F;
  --bg-surface:  #081422;
  --bg-card:     rgba(255,255,255,0.04);
  --bg-card-h:   rgba(255,255,255,0.07);
  --bg-input:    rgba(255,255,255,0.06);
  --gold:        #F5A800;
  --gold-dim:    rgba(245,168,0,0.12);
  --gold-glow:   rgba(245,168,0,0.25);
  --blue:        #1B5FAA;
  --blue-dim:    rgba(27,95,170,0.12);
  --txt:         #EDF2F7;
  --txt-sub:     #7A9CBE;
  --txt-muted:   #3D5A73;
  --border:      rgba(255,255,255,0.07);
  --border-acc:  rgba(245,168,0,0.22);
  --r-card:      18px;
  --r-btn:       10px;
  --r-input:     10px;
}

/* ══════════════════════════════════════════════
   RTL + FONT
   Note: direction:rtl applied to body+app only,
   NOT html root — keeping html as LTR prevents
   Streamlit Cloud fixed-position UI elements
   (toolbar, AI hints, keyboard badges) from
   being displaced onto content areas.
══════════════════════════════════════════════ */
body { direction: rtl !important; }

/* Apply Heebo to everything EXCEPT Streamlit icon-font spans.
   Using :not() ensures the icon spans are never touched by this rule,
   so Streamlit's own CSS (which loads Material Symbols Rounded) can
   apply the correct icon font without any override battle. */
*:not([data-testid="stIconMaterial"]) {
  font-family: 'Heebo', 'Arial Hebrew', Arial, sans-serif !important;
  box-sizing: border-box;
}
[data-testid="stIconMaterial"] {
  box-sizing: border-box;
  direction: ltr !important;
}

/* ══════════════════════════════════════════════
   APP BACKGROUND — dot grid + radial glows
══════════════════════════════════════════════ */
.stApp {
  background-color: var(--bg) !important;
  background-image:
    radial-gradient(ellipse 60% 40% at 15% 15%, rgba(27,95,170,0.07) 0%, transparent 60%),
    radial-gradient(ellipse 50% 40% at 85% 85%, rgba(245,168,0,0.05) 0%, transparent 55%),
    radial-gradient(circle, rgba(255,255,255,0.025) 1px, transparent 1px) !important;
  background-size: auto, auto, 26px 26px !important;
  color: var(--txt) !important;
  direction: rtl !important;
}

/* ══════════════════════════════════════════════
   MAIN BLOCK
══════════════════════════════════════════════ */
.main .block-container {
  padding: 1.5rem 2.5rem 4rem 2.5rem !important;
  max-width: 100% !important;
}

/* ══════════════════════════════════════════════
   SIDEBAR
══════════════════════════════════════════════ */
[data-testid="stSidebar"] {
  background: rgba(2,6,14,0.97) !important;
  border-left: 2px solid var(--gold) !important;
}
[data-testid="stSidebar"] > div:first-child { background: transparent !important; }
[data-testid="stSidebar"] * { direction: rtl !important; }

/* Radio nav items */
[data-testid="stSidebar"] .stRadio > label { display: none !important; }
[data-testid="stSidebar"] .stRadio > div { gap: 4px !important; display: flex; flex-direction: column; }
[data-testid="stSidebar"] .stRadio label {
  color: var(--txt-sub) !important;
  padding: 9px 16px !important;
  border-radius: 10px !important;
  transition: all 0.18s ease !important;
  font-weight: 500 !important;
  font-size: 14px !important;
  cursor: pointer !important;
}
[data-testid="stSidebar"] .stRadio label:hover {
  background: var(--gold-dim) !important;
  color: var(--gold) !important;
}

/* Hide sidebar toggle/collapse button */
[data-testid="stSidebarCollapseButton"],
button[data-testid="baseButton-headerNoPadding"],
[data-testid="stHeader"],
[data-testid="stToolbar"] { display: none !important; }

/* ══════════════════════════════════════════════
   NATIVE HEADERS (st.header / st.subheader)
══════════════════════════════════════════════ */
[data-testid="stHeadingWithActionElements"] h2 {
  font-size: 1.8rem !important;
  font-weight: 900 !important;
  color: var(--txt) !important;
  border-right: 5px solid var(--gold) !important;
  padding-right: 16px !important;
  direction: rtl !important;
  text-align: center !important;
}
[data-testid="stHeadingWithActionElements"] h3 {
  font-size: 1.05rem !important;
  font-weight: 700 !important;
  color: var(--txt) !important;
  border-right: 3px solid var(--gold) !important;
  padding-right: 12px !important;
  direction: rtl !important;
  text-align: center !important;
  margin: 20px 0 12px !important;
}
h1,h2,h3,h4 { direction: rtl !important; text-align: center !important; }

/* ══════════════════════════════════════════════
   METRICS
══════════════════════════════════════════════ */
[data-testid="stMetric"],
[data-testid="metric-container"] {
  background: var(--bg-card) !important;
  border: 1px solid var(--border-acc) !important;
  border-radius: var(--r-card) !important;
  padding: 22px 20px 18px !important;
  position: relative !important;
  overflow: hidden !important;
  transition: transform 0.2s ease, box-shadow 0.2s ease !important;
}
[data-testid="stMetric"]::before,
[data-testid="metric-container"]::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 2px;
  background: linear-gradient(90deg, var(--gold) 0%, var(--blue) 50%, var(--gold) 100%);
  background-size: 200%;
  animation: shimmer 4s linear infinite;
}
[data-testid="stMetric"]:hover,
[data-testid="metric-container"]:hover {
  transform: translateY(-3px) !important;
  box-shadow: 0 8px 32px rgba(245,168,0,0.12) !important;
}
[data-testid="stMetricLabel"] p,
[data-testid="stMetricLabel"] {
  color: var(--txt-sub) !important;
  font-size: 12px !important;
  font-weight: 600 !important;
  text-transform: uppercase !important;
  letter-spacing: 0.7px !important;
  direction: rtl !important;
  text-align: center !important;
  width: 100% !important;
}
[data-testid="stMetricValue"] {
  color: var(--txt) !important;
  font-size: 2.1rem !important;
  font-weight: 800 !important;
  line-height: 1.15 !important;
  direction: rtl !important;
  text-align: center !important;
}
[data-testid="stMetricDelta"] {
  font-size: 13px !important;
  font-weight: 600 !important;
  text-align: center !important;
  display: block !important;
}

/* ══════════════════════════════════════════════
   BUTTONS
══════════════════════════════════════════════ */
.stButton > button,
button[kind="primary"],
button[kind="secondary"] {
  background: linear-gradient(135deg, var(--gold) 0%, #FFB820 100%) !important;
  color: #040C14 !important;
  font-weight: 800 !important;
  font-size: 14px !important;
  letter-spacing: 0.3px !important;
  border: none !important;
  border-radius: var(--r-btn) !important;
  padding: 11px 28px !important;
  width: 100% !important;
  cursor: pointer !important;
  transition: all 0.22s cubic-bezier(0.4,0,0.2,1) !important;
}
.stButton > button:hover { transform: translateY(-2px) !important; box-shadow: 0 8px 28px rgba(245,168,0,0.38) !important; }
.stButton > button:active { transform: translateY(0) !important; }

[data-testid="stDownloadButton"] > button {
  background: transparent !important;
  border: 1.5px solid var(--gold) !important;
  color: var(--gold) !important;
}
[data-testid="stDownloadButton"] > button:hover {
  background: var(--gold-dim) !important;
  box-shadow: 0 4px 20px var(--gold-glow) !important;
  transform: translateY(-1px) !important;
}

/* ══════════════════════════════════════════════
   TEXT INPUTS / NUMBER INPUTS
══════════════════════════════════════════════ */
/* Target multiple selector levels for reliability */
.stTextInput > div > div > input,
.stTextInput input,
.stNumberInput > div > div > div > input,
.stNumberInput input,
[data-baseweb="input"] input,
input[type="text"],
input[type="number"] {
  background: var(--bg-input) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--r-input) !important;
  color: var(--txt) !important;
  direction: rtl !important;
  text-align: right !important;
  transition: border-color 0.2s, box-shadow 0.2s !important;
  font-size: 14px !important;
}
.stTextInput > div > div > input:focus,
.stNumberInput input:focus,
input[type="text"]:focus,
input[type="number"]:focus {
  border-color: var(--gold) !important;
  box-shadow: 0 0 0 3px rgba(245,168,0,0.12) !important;
  outline: none !important;
}

/* Textarea */
.stTextArea > div > div > textarea,
textarea {
  background: var(--bg-input) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--r-input) !important;
  color: var(--txt) !important;
  direction: rtl !important;
  text-align: right !important;
  font-size: 14px !important;
  resize: vertical !important;
}
textarea:focus { border-color: var(--gold) !important; outline: none !important; }

/* Labels */
.stTextInput label, .stNumberInput label, .stTextArea label,
.stFileUploader label, .stSelectbox label, .stCheckbox label,
[data-testid="stWidgetLabel"] p,
[data-testid="stWidgetLabel"] {
  color: var(--txt-sub) !important;
  font-size: 12px !important;
  font-weight: 600 !important;
  text-transform: uppercase !important;
  letter-spacing: 0.5px !important;
  direction: rtl !important;
  text-align: right !important;
}

/* ══════════════════════════════════════════════
   FILE UPLOADER
══════════════════════════════════════════════ */
[data-testid="stFileUploadDropzone"],
[data-testid="stFileUploader"] section {
  background: rgba(255,255,255,0.02) !important;
  border: 2px dashed rgba(255,255,255,0.1) !important;
  border-radius: 16px !important;
  transition: all 0.2s !important;
  direction: rtl !important;
}
[data-testid="stFileUploadDropzone"]:hover,
[data-testid="stFileUploader"] section:hover {
  border-color: var(--gold) !important;
  background: var(--gold-dim) !important;
}
[data-testid="stFileUploadDropzone"] *,
[data-testid="stFileUploader"] section * {
  direction: rtl !important;
  text-align: right !important;
}
[data-testid="stFileUploader"] button {
  background: var(--gold-dim) !important;
  border: 1px solid var(--gold) !important;
  color: var(--gold) !important;
  border-radius: 8px !important;
  font-weight: 700 !important;
  font-size: 13px !important;
  width: auto !important;
  padding: 6px 16px !important;
}

/* ══════════════════════════════════════════════
   DATAFRAME
══════════════════════════════════════════════ */
[data-testid="stDataFrame"],
[data-testid="stDataFrameResizable"] {
  border-radius: 16px !important;
  overflow: hidden !important;
  border: 1px solid var(--border) !important;
}

/* ══════════════════════════════════════════════
   ALERTS
══════════════════════════════════════════════ */
[data-testid="stAlert"],
.stAlert > div {
  border-radius: 14px !important;
  direction: rtl !important;
  text-align: right !important;
}
[data-testid="stAlert"] p { direction: rtl !important; text-align: right !important; }

/* ══════════════════════════════════════════════
   EXPANDER
══════════════════════════════════════════════ */
[data-testid="stExpander"],
details {
  background: var(--bg-card) !important;
  border: 1px solid var(--border) !important;
  border-radius: 14px !important;
  overflow: hidden !important;
}
[data-testid="stExpander"] summary,
details summary {
  direction: rtl !important;
  font-weight: 600 !important;
  color: var(--txt) !important;
  padding: 14px 18px !important;
  cursor: pointer !important;
  list-style: none !important;
  user-select: none !important;
}
[data-testid="stExpander"] summary:hover { background: rgba(255,255,255,0.03) !important; }

/* ══════════════════════════════════════════════
   CHECKBOX
══════════════════════════════════════════════ */
.stCheckbox { direction: rtl !important; }
.stCheckbox label {
  text-transform: none !important;
  letter-spacing: normal !important;
  font-size: 14px !important;
  font-weight: 500 !important;
  color: var(--txt) !important;
}

/* ══════════════════════════════════════════════
   FORM
══════════════════════════════════════════════ */
[data-testid="stForm"] {
  background: var(--bg-card) !important;
  border: 1px solid var(--border) !important;
  border-radius: 20px !important;
  padding: 24px 24px 20px !important;
}

/* ══════════════════════════════════════════════
   DIVIDER / HR
══════════════════════════════════════════════ */
hr { border-color: var(--border) !important; margin: 28px 0 !important; }
[data-testid="stDivider"] hr { border-color: var(--border) !important; }

/* ══════════════════════════════════════════════
   SCROLLBAR
══════════════════════════════════════════════ */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: rgba(245,168,0,0.28); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--gold); }

/* ══════════════════════════════════════════════
   ANIMATIONS
══════════════════════════════════════════════ */
@keyframes shimmer {
  0%   { background-position: -200% 0; }
  100% { background-position:  200% 0; }
}
@keyframes fadeSlideDown {
  from { opacity: 0; transform: translateY(-14px); }
  to   { opacity: 1; transform: translateY(0); }
}
@keyframes fadeSlideRight {
  from { opacity: 0; transform: translateX(14px); }
  to   { opacity: 1; transform: translateX(0); }
}
@keyframes fadeIn {
  from { opacity: 0; }
  to   { opacity: 1; }
}

/* ══════════════════════════════════════════════
   CUSTOM COMPONENTS
══════════════════════════════════════════════ */

/* — Page Header — */
.kpi-page-header {
  position: relative;
  padding: 26px 28px 22px;
  margin-bottom: 30px;
  background: var(--bg-card);
  border: 1px solid var(--border-acc);
  border-radius: var(--r-card);
  overflow: hidden;
  direction: rtl;
  animation: fadeSlideDown 0.45s cubic-bezier(0.4,0,0.2,1);
}
.kpi-page-header::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0; height: 2px;
  background: linear-gradient(90deg, var(--gold) 0%, var(--blue) 50%, var(--gold) 100%);
  background-size: 200%;
  animation: shimmer 4s linear infinite;
}
.kpi-page-header::after {
  content: '';
  position: absolute;
  top: -60px; right: -40px;
  width: 220px; height: 220px;
  background: radial-gradient(circle, rgba(245,168,0,0.055) 0%, transparent 70%);
  pointer-events: none;
}
.kpi-page-header { text-align: center !important; }
.kpi-page-header h1 {
  display: inline !important;
  font-size: 1.85rem !important;
  font-weight: 900 !important;
  color: var(--txt) !important;
  line-height: 1.15 !important;
  letter-spacing: -0.4px;
  border: none !important;
  padding: 0 !important;
}
.kpi-page-header .ph-icon { font-size: 1.75rem; margin-left: 10px; vertical-align: middle; }
.kpi-page-header .ph-sub {
  color: var(--txt-sub);
  font-size: 13px;
  font-weight: 400;
  margin-top: 8px;
  letter-spacing: 0.2px;
  text-align: center;
}

/* — Section Header — */
.kpi-section-header {
  display: flex;
  align-items: center;
  gap: 12px;
  direction: rtl;
  margin: 32px 0 16px;
  animation: fadeSlideRight 0.35s ease;
}
.kpi-section-header .sh-step {
  background: linear-gradient(135deg, var(--gold) 0%, #FFB820 100%);
  color: #04080F;
  font-size: 11px;
  font-weight: 900;
  padding: 3px 11px;
  border-radius: 20px;
  flex-shrink: 0;
  letter-spacing: 0.2px;
}
.kpi-section-header .sh-title {
  color: var(--txt);
  font-size: 1rem;
  font-weight: 700;
  white-space: nowrap;
  text-align: center;
}
.kpi-section-header .sh-line {
  flex: 1;
  height: 1px;
  background: linear-gradient(90deg, var(--border-acc) 0%, transparent 100%);
}

/* — Agent Card — */
.kpi-agent-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 18px 20px;
  direction: rtl;
  transition: all 0.22s ease;
  animation: fadeIn 0.4s ease;
  cursor: default;
}
.kpi-agent-card:hover {
  border-color: var(--border-acc);
  background: var(--bg-card-h);
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0,0,0,0.3), 0 0 0 1px var(--border-acc);
}
.kpi-agent-card .ac-id {
  color: var(--txt-muted);
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.8px;
  margin-bottom: 5px;
  text-align: center;
}
.kpi-agent-card .ac-name {
  color: var(--txt);
  font-size: 1.25rem;
  font-weight: 700;
  line-height: 1.2;
  text-align: center;
}

/* — Agent Label in forms — */
.kpi-agent-label {
  color: var(--gold);
  font-size: 14px;
  font-weight: 700;
  text-align: right;
  padding: 8px 0 6px;
  border-bottom: 1px solid var(--border);
  margin-bottom: 10px;
  direction: rtl;
}
"""


def apply_theme():
    st.markdown(f"<style>{_CSS}</style>", unsafe_allow_html=True)
