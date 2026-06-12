# screens/agent_management.py
import streamlit as st
from modules.config_manager import load_agents, save_agents
from modules import ui


def render():
    ui.page_header("ניהול נציגים", icon="👥", subtitle="הוספה, עריכה והסרה של נציגים")

    agents = load_agents()

    ui.section_header("נציגים קיימים")
    for i, agent in enumerate(agents):
        with st.container():
            c1, c2, c3, c4, c5, c6 = st.columns([2, 2, 2, 2, 1, 1])
            with c1:
                agents[i]["name"] = st.text_input("שם עברי", agent["name"], key=f"n_{i}")
            with c2:
                agents[i]["employee_id"] = int(st.number_input(
                    "מ. עובד", value=agent["employee_id"], step=1, key=f"e_{i}"))
            with c3:
                agents[i]["voicenter_name"] = st.text_input(
                    "שם ב-Voicenter", agent.get("voicenter_name", ""), key=f"vc_{i}",
                    help="השם כפי שמופיע בדוח Voicenter")
            with c4:
                agents[i]["email"] = st.text_input("מייל", agent.get("email", ""), key=f"m_{i}")
            with c5:
                agents[i]["active"] = st.checkbox("פעיל", agent.get("active", True), key=f"a_{i}")
            with c6:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("🗑️", key=f"d_{i}"):
                    agents.pop(i)
                    save_agents(agents)
                    st.rerun()

    if st.button("💾 שמור שינויים"):
        save_agents(agents)
        st.success("נשמר בהצלחה ✅")

    st.markdown("<hr/>", unsafe_allow_html=True)

    ui.section_header("הוספת נציג חדש")
    with st.form("add_agent"):
        col1, col2 = st.columns(2)
        with col1:
            name    = st.text_input("שם עברי", placeholder="למשל: ישראל ישראלי")
            vc_name = st.text_input("שם ב-Voicenter", placeholder="למשל: israel israeli")
        with col2:
            emp_id = st.number_input("מספר עובד", step=1, value=0)
            email  = st.text_input("מייל", placeholder="agent@example.com")
        if st.form_submit_button("➕ הוסף נציג") and name:
            agents.append({
                "id":             name.replace(" ", "_"),
                "name":           name,
                "voicenter_name": vc_name,
                "employee_id":    int(emp_id),
                "email":          email,
                "active":         True,
            })
            save_agents(agents)
            st.success(f"נציג {name} נוסף ✅")
            st.rerun()
