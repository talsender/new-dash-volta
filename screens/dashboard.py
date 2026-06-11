# screens/dashboard.py
import streamlit as st
from modules.config_manager import load_agents
from modules.history_manager import load_history


def render():
    st.header("לוח בקרה — מוקד וולטה סולאר")
    agents = load_agents()
    active = [a for a in agents if a["active"]]

    history = load_history()
    last = history[-1] if history else None

    col1, col2, col3 = st.columns(3)
    col1.metric("נציגים פעילים", len(active))
    if last:
        col2.metric(f"קצב מוקד — {last['label']}", f"{last['center_rate']:.2f}",
                    delta="✅ עמד ביעד" if last["center_met_target"] else "❌ לא עמד")
        col3.metric(f"בונוס מנהל — {last['label']}", f"₪{last['manager_bonus']:,}")

    st.markdown("---")
    st.subheader("נציגים פעילים")
    for a in active:
        st.markdown(f"- **{a['name']}** (מ. עובד: {a['employee_id']})")

    if last:
        st.markdown("---")
        st.subheader(f"ביצועים אחרון — {last['label']}")
        st.dataframe([{
            "נציג": a["name"],
            "פגישות/שעה": f"{a['meetings_per_hour']:.2f}",
            "בונוס ₪": f"{a['bonus_total']:,}",
        } for a in last["agents"]], use_container_width=True)
