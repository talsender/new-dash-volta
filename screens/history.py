# screens/history.py
import streamlit as st
import json
from modules.history_manager import load_history, save_month
from modules import ui

try:
    import plotly.express as px
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

_PLOT_LAYOUT = dict(
    paper_bgcolor="rgba(8,20,34,0.9)",
    plot_bgcolor="rgba(4,8,15,0.6)",
    font=dict(color="#7A9CBE", family="Heebo"),
    xaxis=dict(gridcolor="rgba(255,255,255,0.06)", color="#7A9CBE"),
    yaxis=dict(gridcolor="rgba(255,255,255,0.06)", color="#7A9CBE"),
    title_font=dict(color="#EDF2F7", size=14),
    margin=dict(l=20, r=20, t=40, b=20),
)


def render():
    ui.page_header("היסטוריה וניתוח", icon="📈", subtitle="מגמות ביצועים לאורך זמן")

    # GitHub persistence status
    try:
        token  = st.secrets.get("GITHUB_TOKEN", "")
        repo   = st.secrets.get("GITHUB_REPO",  "")
        github_ok = bool(token and repo)
    except Exception:
        github_ok = False

    if not github_ok:
        st.warning(
            "ההיסטוריה נשמרת זמנית בלבד — כדי שתישמר לצמיתות הגדר GITHUB_TOKEN ו-GITHUB_REPO ב-Streamlit Secrets.",
            icon="⚠️",
        )

    col_refresh, _ = st.columns([1, 4])
    if col_refresh.button("🔄 רענן היסטוריה"):
        # Clear session_state cache so load_history() fetches fresh data
        if "__history_data__" in st.session_state:
            del st.session_state["__history_data__"]
        st.rerun()

    history = load_history()
    if not history:
        st.info("אין נתונים היסטוריים עדיין. לאחר חישוב חודשי לחץ 'שמור חודש להיסטוריה'.")
        _upload_section()
        return

    labels = [h["label"] for h in history]

    ui.section_header("סיכום חודשים")
    st.dataframe(
        [{
            "חודש": h["label"],
            "קצב מוקד": f"{h['center_rate']:.2f}",
            "עמד ביעד": "✅" if h["center_met_target"] else "❌",
            "בונוס מנהל ₪": f"{h['manager_bonus']:,}",
            "חיוב ללקוח ₪": f"{h['total_billing']:,}",
        } for h in history],
        use_container_width=True,
    )

    if HAS_PLOTLY:
        ui.section_header("קצב מוקד לאורך זמן")
        fig = px.line(x=labels, y=[h["center_rate"] for h in history],
                      labels={"x": "חודש", "y": "פגישות/שעה"},
                      markers=True, color_discrete_sequence=["#F5A800"])
        fig.add_hline(y=1.0, line_dash="dash", line_color="#3DD68C", annotation_text="יעד")
        fig.update_layout(**_PLOT_LAYOUT)
        st.plotly_chart(fig, use_container_width=True)

        ui.section_header("פניקס לפי חודש")
        fig2 = px.bar(x=labels,
                      y=[sum(a["phoenix"] for a in h["agents"]) for h in history],
                      labels={"x": "חודש", "y": "עסקאות פניקס"},
                      color_discrete_sequence=["#1B5FAA"])
        fig2.update_layout(**_PLOT_LAYOUT)
        st.plotly_chart(fig2, use_container_width=True)

        agent_names = list({a["name"] for h in history for a in h["agents"]})

        ui.section_header("פגישות/שעה לפי נציג")
        for name in agent_names:
            rates, mlabels = [], []
            for h in history:
                ag = next((a for a in h["agents"] if a["name"] == name), None)
                if ag:
                    rates.append(ag["meetings_per_hour"])
                    mlabels.append(h["label"])
            if rates:
                fig3 = px.line(x=mlabels, y=rates, title=name,
                               labels={"x": "חודש", "y": "פגישות/שעה"},
                               markers=True, color_discrete_sequence=["#F5A800"])
                fig3.add_hline(y=1.0, line_dash="dash", line_color="#3DD68C")
                fig3.update_layout(**_PLOT_LAYOUT)
                st.plotly_chart(fig3, use_container_width=True)

        ui.section_header("מגמת בונוסים")
        for name in agent_names:
            bonuses, mlabels = [], []
            for h in history:
                ag = next((a for a in h["agents"] if a["name"] == name), None)
                if ag:
                    bonuses.append(ag["bonus_total"])
                    mlabels.append(h["label"])
            if bonuses:
                fig4 = px.bar(x=mlabels, y=bonuses, title=f"בונוס — {name}",
                              labels={"x": "חודש", "y": "בונוס ₪"},
                              color_discrete_sequence=["#F5A800"])
                fig4.update_layout(**_PLOT_LAYOUT)
                st.plotly_chart(fig4, use_container_width=True)
    else:
        st.warning("התקן `plotly` לגרפים: `pip install plotly`")
        for h in history:
            with st.expander(h["label"]):
                st.json(h)

    st.markdown("<hr/>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.download_button(
            "📥 הורד היסטוריה (JSON)",
            json.dumps(history, ensure_ascii=False, indent=2).encode("utf-8"),
            file_name="kpi_history.json", mime="application/json",
        )
    with c2:
        _upload_section()


def _upload_section():
    uploaded = st.file_uploader("📤 העלה היסטוריה (JSON)", type=["json"], key="hist_upload")
    if uploaded:
        data = json.loads(uploaded.read().decode("utf-8"))
        for m in data:
            save_month(m)
        st.success(f"שוחזרו {len(data)} חודשים ✅")
        st.rerun()
