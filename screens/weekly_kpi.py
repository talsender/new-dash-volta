# screens/weekly_kpi.py
import streamlit as st
import tempfile, os
from modules.data_loader import parse_attendance, parse_voicenter
from modules.calculator import (calculate_work_hours, calculate_meetings_per_hour,
                                 calculate_idle_pct, calculate_center_rate)
from modules.config_manager import load_agents, load_settings
from modules.email_builder import build_weekly_management_email, build_weekly_agent_email
from modules.email_sender import send_email
from modules.excel_exporter import export_weekly_kpi


def _save_upload(uploaded, suffix):
    f = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    f.write(uploaded.read()); f.close()
    return f.name


def render():
    st.header("דוח KPI שבועי")
    agents = [a for a in load_agents() if a["active"]]
    settings = load_settings()

    st.subheader("1. העלאת קבצים")
    c1, c2 = st.columns(2)
    att_file = c1.file_uploader("נוכחות (.xlsx)", type=['xlsx'], key="w_att")
    vc_file  = c2.file_uploader("Voicenter (.xls)", type=['xls','xlsx'], key="w_vc")
    if not att_file or not vc_file:
        st.info("נא להעלות את שני הקבצים")
        return

    att_path = _save_upload(att_file, '.xlsx')
    vc_path  = _save_upload(vc_file, '.xls')
    try:
        att_df = parse_attendance(att_path)
        vc_df  = parse_voicenter(vc_path)
    except Exception as e:
        st.error(f"שגיאה בקריאת קבצים: {e}")
        return
    finally:
        os.unlink(att_path); os.unlink(vc_path)

    with st.expander("🔍 אבחון — נתונים שנקראו מהקבצים"):
        st.write("**נוכחות — עמודות:**", list(att_df.columns))
        st.write("**נוכחות — שורות לדוגמה:**")
        st.dataframe(att_df.head(5))
        st.write("**Voicenter — עמודות:**", list(vc_df.columns))
        st.write("**Voicenter — שורות לדוגמה:**")
        st.dataframe(vc_df.head(5))
        st.write("**מספרי עובד מהקבצים:**", list(att_df['מספר עובד'].unique()))
        st.write("**מספרי עובד מהגדרות:**", [a['employee_id'] for a in agents])

    st.subheader("2. הזנה ידנית")
    week_label = st.text_input("תיאור שבוע", "שבוע X — יוני 2026")
    manual = {}
    cols = st.columns(len(agents))
    for col, agent in zip(cols, agents):
        with col:
            st.markdown(f"**{agent['name']}**")
            manual[agent["id"]] = {
                "meetings":   st.number_input("תיאומים",  min_value=0, key=f"wm_{agent['id']}"),
                "phoenix":    st.number_input("פניקס",    min_value=0, key=f"wp_{agent['id']}"),
                "idle_calls": st.number_input("שיחות סרק", min_value=0, key=f"wi_{agent['id']}"),
            }

    if not st.button("חשב KPI"):
        return

    kpi_data = []
    for agent in agents:
        hours = calculate_work_hours(att_df, agent["employee_id"])
        inp = manual[agent["id"]]
        vc_name = agent.get('voicenter_name') or agent['name']
        vc_row = vc_df[vc_df['משתמש'].str.lower().str.contains(vc_name.lower(), na=False, regex=False)]
        if not len(vc_row):
            vc_row = vc_df[vc_df['משתמש'].str.contains(agent['name'].split()[0], na=False, regex=False)]
        answered = int(vc_row['נענו'].iloc[0]) if len(vc_row) else 0
        occ_pct  = float(vc_row['אחוז תעסוקה נטו'].iloc[0]) if len(vc_row) else 0.0
        kpi_data.append({
            "agent_id": agent["id"], "name": agent["name"],
            "email": agent.get("email", ""), "hours": hours,
            "meetings": inp["meetings"],
            "meetings_per_hour": calculate_meetings_per_hour(inp["meetings"], hours),
            "occupancy_pct": occ_pct, "idle_calls": inp["idle_calls"],
            "idle_pct": calculate_idle_pct(inp["idle_calls"], answered),
            "answered_calls": answered, "phoenix": inp["phoenix"],
        })

    center_rate = calculate_center_rate([{"hours": k["hours"], "meetings": k["meetings"]} for k in kpi_data])

    st.subheader("3. תוצאות")
    center_ok = center_rate >= settings["bonus_thresholds"]["meetings_per_hour_tier_a"]
    st.metric("קצב מוקד", f"{center_rate:.2f} פגישות/שעה",
              delta="✅ עמד ביעד" if center_ok else "❌ לא עמד")
    st.dataframe([{
        "נציג": k["name"], "שעות": f"{k['hours']:.1f}", "תיאומים": k["meetings"],
        "פגישות/שעה": f"{k['meetings_per_hour']:.2f}",
        "תעסוקה": f"{k['occupancy_pct']*100:.1f}%",
        "סרק": f"{k['idle_pct']*100:.2f}%", "פניקס": k["phoenix"],
    } for k in kpi_data], use_container_width=True)

    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
        xl_path = f.name
    export_weekly_kpi(kpi_data, xl_path)
    with open(xl_path, 'rb') as f:
        st.download_button("📥 הורד Excel", f.read(), file_name=f"kpi_{week_label}.xlsx")
    os.unlink(xl_path)

    st.subheader("4. שליחת מיילים")
    mgmt_html = build_weekly_management_email(kpi_data, week_label)
    with st.expander("תצוגה מקדימה — מייל הנהלה"):
        st.components.v1.html(mgmt_html, height=400, scrolling=True)

    confirmed = st.checkbox("בדקתי ואישרתי את התצוגה המקדימה")
    if not confirmed:
        return

    smtp = settings["smtp"]
    password = st.secrets.get("SMTP_PASSWORD", "")
    c_mgmt, c_agents = st.columns(2)
    with c_mgmt:
        if st.button("שלח להנהלה"):
            r = send_email(smtp, password, settings["recipients"]["management"],
                           f"KPI שבועי — {week_label}", mgmt_html)
            st.success("נשלח") if r.success else st.error(r.error)
    with c_agents:
        if st.button("שלח לנציגים"):
            for k in kpi_data:
                if not k.get("email"):
                    st.warning(f"חסר מייל: {k['name']}"); continue
                html = build_weekly_agent_email(k, k["name"], week_label)
                r = send_email(smtp, password, [k["email"]],
                               f"ביצועים שבועיים — {week_label}", html)
                st.success(f"נשלח ל-{k['name']}") if r.success else st.error(f"{k['name']}: {r.error}")
