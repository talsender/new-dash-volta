# screens/monthly_bonus.py
import streamlit as st
import tempfile, os
from modules.data_loader import parse_attendance, parse_voicenter, parse_feedback
from modules.calculator import (calculate_work_hours, calculate_meetings_per_hour,
                                 calculate_idle_pct, calculate_center_rate,
                                 calculate_agent_bonus, calculate_manager_bonus)
from modules.config_manager import load_agents, load_settings
from modules.email_builder import (build_monthly_client_email, build_monthly_agent_email)
from modules.email_sender import send_email
from modules.excel_exporter import export_monthly_bonus, export_agent_bonus
from modules.history_manager import save_month
from modules import ui


def _save_upload(uploaded, suffix):
    f = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    f.write(uploaded.read()); f.close()
    return f.name


def _get_feedback(scores: dict, agent_name: str):
    if not scores:
        return None
    # exact match
    if agent_name in scores:
        return scores[agent_name]
    # sheet name is a first-name substring of the agent name
    first = agent_name.split()[0]
    for key, val in scores.items():
        if first in key or key in agent_name:
            return val
    return None


def render():
    ui.page_header("בונוסים חודשיים", icon="💰", subtitle="חישוב בונוסים, Excel ושליחת מיילים")

    agents = [a for a in load_agents() if a["active"]]
    settings = load_settings()
    t = settings["bonus_thresholds"]

    ui.section_header("העלאת קבצים", step=1)
    c1, c2, c3 = st.columns(3)
    att_file = c1.file_uploader("נוכחות (.xlsx)", type=['xlsx'], key="b_att")
    vc_file  = c2.file_uploader("Voicenter (.xls)", type=['xls','xlsx'], key="b_vc")
    fb_file  = c3.file_uploader("משובים (.xlsx) — אופציונלי", type=['xlsx'], key="b_fb")
    if not att_file or not vc_file:
        st.info("נא להעלות לפחות קבצי נוכחות ו-Voicenter")
        return

    att_path = _save_upload(att_file, '.xlsx')
    vc_path  = _save_upload(vc_file, '.xls')
    fb_path  = _save_upload(fb_file, '.xlsx') if fb_file else None
    try:
        att_df = parse_attendance(att_path)
        vc_df  = parse_voicenter(vc_path)
        feedback_scores = parse_feedback(fb_path) if fb_path else {}
    except Exception as e:
        st.error(f"שגיאה בקריאת קבצים: {e}")
        return
    finally:
        for p in [att_path, vc_path, fb_path]:
            if p: os.unlink(p)

    ui.section_header("הזנה ידנית", step=2)
    month_label = st.text_input("חודש", "יוני 2026")
    manual = {}
    cols = st.columns(len(agents))
    for col, agent in zip(cols, agents):
        with col:
            st.markdown(
                f'<div style="color:#F5A800;font-weight:700;font-size:15px;'
                f'text-align:right;margin-bottom:8px;">{agent["name"]}</div>',
                unsafe_allow_html=True,
            )
            manual[agent["id"]] = {
                "meetings":   st.number_input("תיאומים",   min_value=0, key=f"bm_{agent['id']}"),
                "phoenix":    st.number_input("פניקס",     min_value=0, key=f"bp_{agent['id']}"),
                "idle_calls": st.number_input("שיחות סרק", min_value=0, key=f"bi_{agent['id']}"),
            }

    if not st.button("חשב בונוסים"):
        return

    kpi_data = []
    for agent in agents:
        hours = calculate_work_hours(att_df, agent["employee_id"])
        inp = manual[agent["id"]]
        vc_name = agent.get('voicenter_name') or agent['name']
        vc_row = vc_df[vc_df['משתמש'].str.lower().str.contains(vc_name.lower(), na=False, regex=False)]
        if not len(vc_row):
            first_name = agent['name'].split()[0]
            vc_row = vc_df[vc_df['משתמש'].str.contains(first_name, na=False, regex=False)]
        answered = int(vc_row['נענו'].iloc[0]) if len(vc_row) else 0
        occ_pct  = float(vc_row['אחוז תעסוקה נטו'].iloc[0]) if len(vc_row) else 0.0
        kpi_data.append({
            "agent_id": agent["id"], "name": agent["name"],
            "employee_id": agent["employee_id"], "email": agent.get("email", ""),
            "hours": hours, "meetings": inp["meetings"],
            "meetings_per_hour": calculate_meetings_per_hour(inp["meetings"], hours),
            "occupancy_pct": occ_pct, "idle_calls": inp["idle_calls"],
            "idle_pct": calculate_idle_pct(inp["idle_calls"], answered),
            "phoenix": inp["phoenix"],
            "feedback_score": _get_feedback(feedback_scores, agent["name"]),
        })

    center_rate  = calculate_center_rate([{"hours": k["hours"], "meetings": k["meetings"]} for k in kpi_data])
    center_meets = center_rate >= t["meetings_per_hour_tier_a"]

    bonus_data = []
    for k in kpi_data:
        kpi_in = {"meetings": k["meetings"], "individual_rate": k["meetings_per_hour"],
                  "occupancy_pct": k["occupancy_pct"], "idle_pct": k["idle_pct"],
                  "feedback_score": k["feedback_score"], "phoenix": k["phoenix"]}
        b = calculate_agent_bonus(kpi_in, center_meets, settings)
        bonus_data.append({"name": k["name"], "employee_id": k["employee_id"], **b})

    manager_bonus = calculate_manager_bonus(center_rate, settings)
    total_phoenix = sum(k["phoenix"] for k in kpi_data)
    billing = {"hours_by_agent": {k["name"]: k["hours"] for k in kpi_data},
               "total_hours": sum(k["hours"] for k in kpi_data),
               "phoenix_count": total_phoenix,
               "phoenix_billing": total_phoenix * t["phoenix_client_rate"]}

    ui.section_header("תוצאות", step=3)
    c_a, c_b = st.columns(2)
    c_a.metric("קצב מוקד", f"{center_rate:.2f}/שעה",
               delta="✅ עמד ביעד" if center_meets else "❌ לא עמד")
    c_b.metric("בונוס מנהל", f"₪{manager_bonus:,}")
    st.dataframe(
        [{
            "נציג": b["name"], "תיאומים ₪": b["meetings_bonus"],
            "תעסוקה ₪": b["occupancy_bonus"], "סרק ₪": b["idle_bonus"],
            "משוב ₪": b["feedback_bonus"], "פניקס ₪": b["phoenix_bonus"],
            "סה\"כ ₪": b["total"],
        } for b in bonus_data],
        use_container_width=True,
    )

    if st.button("💾 שמור חודש להיסטוריה"):
        snapshot = {
            "month": month_label.strip(),
            "label": month_label,
            "center_rate": center_rate,
            "center_met_target": center_meets,
            "manager_bonus": manager_bonus,
            "total_billing": billing["phoenix_billing"],
            "agents": [{
                "name": k["name"], "hours": k["hours"], "meetings": k["meetings"],
                "meetings_per_hour": k["meetings_per_hour"],
                "occupancy_pct": k["occupancy_pct"], "idle_pct": k["idle_pct"],
                "feedback_score": k["feedback_score"], "phoenix": k["phoenix"],
                "bonus_total": b["total"],
            } for k, b in zip(kpi_data, bonus_data)]
        }
        save_month(snapshot)
        st.success(f"חודש {month_label} נשמר להיסטוריה ✅")

    # ── per-agent cards ──────────────────────────────────────────────────────
    st.markdown("---")
    ui.section_header("פירוט לנציגים")
    for k, b in zip(kpi_data, bonus_data):
        with st.expander(f"📋  {k['name']}  —  סה\"כ ₪{b['total']:,}"):
            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("שעות",        f"{k['hours']:.1f}")
            c2.metric("תיאומים",     k["meetings"])
            c3.metric("תיאומים/שעה", f"{k['meetings_per_hour']:.2f}")
            c4.metric("תעסוקה",      f"{k['occupancy_pct']*100:.1f}%")
            c5.metric("סרק",         f"{k['idle_pct']*100:.2f}%")
            st.dataframe(
                [
                    {"רכיב": "עמלת תיאומים",    "₪": b["meetings_bonus"]},
                    {"רכיב": "בונוס תעסוקה",    "₪": b["occupancy_bonus"]},
                    {"רכיב": "בונוס סרק",        "₪": b["idle_bonus"]},
                    {"רכיב": "בונוס משוב",       "₪": b["feedback_bonus"]},
                    {"רכיב": "בונוס פניקס",      "₪": b["phoenix_bonus"]},
                    {"רכיב": 'סה"כ',             "₪": b["total"]},
                ],
                use_container_width=True, hide_index=True,
            )
            with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as af:
                af_path = af.name
            export_agent_bonus(k, b, month_label, af_path, center_meets=center_meets)
            with open(af_path, "rb") as af:
                st.download_button(
                    f"📥 הורד Excel אישי — {k['name']}",
                    af.read(),
                    file_name=f"bonus_{k['name']}_{month_label}.xlsx",
                    key=f"dl_{k['agent_id']}",
                )
            os.unlink(af_path)

    # ── center Excel download ────────────────────────────────────────────────
    st.markdown("---")
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
        xl_path = f.name
    export_monthly_bonus(bonus_data, billing, month_label, xl_path,
                         kpi_data=kpi_data,
                         manager_bonus=manager_bonus,
                         manager_name="טל סנדר",
                         center_meets=center_meets)
    with open(xl_path, 'rb') as f:
        xl_bytes = f.read()
    st.download_button("📥 הורד Excel מוקד מלא", xl_bytes, file_name=f"bonuses_{month_label}.xlsx")
    os.unlink(xl_path)

    ui.section_header("שליחת מיילים", step=4)
    client_html = build_monthly_client_email(billing, month_label)
    with st.expander("📧 תצוגה מקדימה — מייל ללקוח"):
        st.components.v1.html(client_html, height=300, scrolling=True)

    confirmed = st.checkbox("בדקתי ואישרתי את כל המיילים")
    if not confirmed:
        return

    smtp = settings["smtp"]
    password = st.secrets.get("SMTP_PASSWORD", "")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("שלח ללקוח (וולטה) + Excel"):
            with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
                xl2 = f.name
                f.write(xl_bytes)
            r = send_email(smtp, password, settings["recipients"]["client"],
                           f"חיוב חודש {month_label}", client_html, attachment_path=xl2)
            os.unlink(xl2)
            st.success("נשלח ללקוח ✅") if r.success else st.error(r.error)
    with c2:
        if st.button("שלח בונוסים לכל נציג"):
            for k, b in zip(kpi_data, bonus_data):
                if not k.get("email"):
                    st.warning(f"חסר מייל: {k['name']}"); continue
                html = build_monthly_agent_email(k, b, k["name"], month_label)
                agent_xl = tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False)
                agent_xl.close()
                export_agent_bonus(k, b, month_label, agent_xl.name)
                r = send_email(smtp, password, [k["email"]],
                               f"בונוס חודש {month_label}", html,
                               attachment_path=agent_xl.name)
                os.unlink(agent_xl.name)
                st.success(f"נשלח ל-{k['name']} ✅") if r.success else st.error(f"{k['name']}: {r.error}")
