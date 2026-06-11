# screens/history.py
import streamlit as st
import json
from modules.history_manager import load_history, save_month

try:
    import plotly.express as px
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False


def render():
    st.header("היסטוריה וניתוח נתונים")
    history = load_history()

    if not history:
        st.info("אין נתונים היסטוריים עדיין. לאחר חישוב חודשי, לחץ 'שמור חודש להיסטוריה'.")
        _upload_section()
        return

    labels = [h["label"] for h in history]

    st.subheader("סיכום חודשים")
    summary_rows = [{
        "חודש": h["label"],
        "קצב מוקד": f"{h['center_rate']:.2f}",
        "עמד ביעד": "✅" if h["center_met_target"] else "❌",
        "בונוס מנהל ₪": f"{h['manager_bonus']:,}",
        "חיוב ללקוח ₪": f"{h['total_billing']:,}",
    } for h in history]
    st.dataframe(summary_rows, use_container_width=True)

    if HAS_PLOTLY:
        st.subheader("קצב מוקד לאורך זמן")
        fig = px.line(x=labels, y=[h["center_rate"] for h in history],
                      labels={"x": "חודש", "y": "פגישות/שעה"},
                      markers=True)
        fig.add_hline(y=1.0, line_dash="dash", line_color="green",
                      annotation_text="יעד 1.0")
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("פניקס לפי חודש")
        phoenix_by_month = [sum(a["phoenix"] for a in h["agents"]) for h in history]
        fig2 = px.bar(x=labels, y=phoenix_by_month,
                      labels={"x": "חודש", "y": "עסקאות פניקס"})
        st.plotly_chart(fig2, use_container_width=True)

        st.subheader("פגישות/שעה לפי נציג")
        agent_names = list({a["name"] for h in history for a in h["agents"]})
        for name in agent_names:
            rates = []
            month_labels = []
            for h in history:
                agent = next((a for a in h["agents"] if a["name"] == name), None)
                if agent:
                    rates.append(agent["meetings_per_hour"])
                    month_labels.append(h["label"])
            if rates:
                fig3 = px.line(x=month_labels, y=rates,
                               title=name, labels={"x": "חודש", "y": "פגישות/שעה"},
                               markers=True)
                fig3.add_hline(y=1.0, line_dash="dash", line_color="green")
                st.plotly_chart(fig3, use_container_width=True)

        st.subheader("מגמת בונוסים")
        for name in agent_names:
            bonuses = []
            month_labels = []
            for h in history:
                agent = next((a for a in h["agents"] if a["name"] == name), None)
                if agent:
                    bonuses.append(agent["bonus_total"])
                    month_labels.append(h["label"])
            if bonuses:
                fig4 = px.bar(x=month_labels, y=bonuses,
                              title=f"בונוס — {name}",
                              labels={"x": "חודש", "y": "בונוס ₪"})
                st.plotly_chart(fig4, use_container_width=True)
    else:
        st.warning("התקן את plotly לגרפים: `pip install plotly`")
        for h in history:
            with st.expander(h["label"]):
                st.json(h)

    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        st.download_button("📥 הורד היסטוריה (JSON)",
                           json.dumps(history, ensure_ascii=False, indent=2).encode('utf-8'),
                           file_name="kpi_history.json", mime="application/json")
    with col2:
        _upload_section()


def _upload_section():
    uploaded = st.file_uploader("📤 העלה היסטוריה (JSON)", type=['json'], key="hist_upload")
    if uploaded:
        data = json.loads(uploaded.read().decode('utf-8'))
        for month_data in data:
            save_month(month_data)
        st.success(f"שוחזרו {len(data)} חודשים")
        st.rerun()
