# screens/monthly_bonus.py
import streamlit as st
import tempfile, os
from modules.month_calc import (compute_month, build_snapshot, agents_missing_data,
                                days_in_month, _month_bounds)
from modules.config_manager import load_agents, load_settings
from modules.email_builder import (build_monthly_client_email, build_monthly_agent_email)
from modules.email_sender import send_email
from modules.excel_exporter import export_monthly_bonus, export_agent_bonus
from modules.history_manager import save_month
from modules.calculator import employee_attendance_range
from modules.data_loader import parse_attendance
from modules import ui

_SS_KEY = "mb_results"
_SAVE_LABELS = {"github": "GitHub — קבוע", "local": "מקומי", "session": "זיכרון"}

# Must match app.py constants
_APP_PAGE_KEY = "_current_page"
_APP_NAV_KEY  = "_nav_radio"
_HISTORY_PAGE = "📈 היסטוריה"


def _do_save_and_navigate(res, month_label):
    """Save results to history and navigate."""
    try:
        snapshot = build_snapshot(res, month_label)
    except Exception as exc:
        st.error(f"❌ שגיאה ביצירת snapshot: {exc}")
        return
    save_src = save_month(snapshot)
    st.toast(f"✅ חודש {month_label} נשמר ({_SAVE_LABELS.get(save_src, 'נשמר')})")
    # Set navigation target via multiple mechanisms for Cloud reliability
    st.session_state["nav_goto"]    = _HISTORY_PAGE
    st.session_state[_APP_PAGE_KEY] = _HISTORY_PAGE  # direct fallback
    try:
        st.session_state[_APP_NAV_KEY] = _HISTORY_PAGE  # radio sync (best-effort)
    except Exception:
        pass
    st.rerun()


def _attendance_hints(att_file, agents):
    """{employee_id: (first, last)} — when the attendance file first and last
    sees each agent, which is the best evidence of entering or leaving the role.

    A hint only: the file may cover a partial period, so it never drives the
    calculation. Returns {} when the file cannot be read, so a bad upload
    never blocks the screen.
    """
    if not att_file:
        return {}
    try:
        att_file.seek(0)
        df = parse_attendance(att_file)
        att_file.seek(0)          # compute_month reads the same handle afterwards
        return {a["employee_id"]: employee_attendance_range(df, a["employee_id"])
                for a in agents}
    except Exception:
        return {}


def render():
    ui.page_header("בונוסים חודשיים", icon="💰", subtitle="חישוב בונוסים, Excel ושליחת מיילים")

    agents   = [a for a in load_agents() if a["active"]]
    settings = load_settings()

    # ── Step 1: file upload ──────────────────────────────────────────────────
    ui.section_header("העלאת קבצים", step=1)
    c1, c2, c3 = st.columns(3)
    att_file = c1.file_uploader("נוכחות (.xlsx)",              type=['xlsx'],       key="b_att")
    vc_file  = c2.file_uploader("Voicenter (.xls / .xlsx / .csv)",
                                type=['xls', 'xlsx', 'csv'],         key="b_vc")
    fb_file  = c3.file_uploader("משובים (.xlsx) — אופציונלי", type=['xlsx'],       key="b_fb")

    # ── Step 2: manual input ─────────────────────────────────────────────────
    ui.section_header("הזנה ידנית", step=2)
    month_label = st.text_input("חודש", "יוני 2026")
    month_first, month_last = _month_bounds(month_label)
    month_days = days_in_month(month_label)
    st.caption(f"החודש נספר כ-{month_days} ימים. הבונוסים הקבועים מחולקים יחסית "
               "לחלק מהחודש שבו הנציג היה בתפקיד — היעדרות אינה מקטינה אותם.")

    hints  = _attendance_hints(att_file, agents)
    manual = {}
    cols = st.columns(len(agents))
    for col, agent in zip(cols, agents):
        with col:
            st.markdown(
                f'<div style="color:#F5A800;font-weight:700;font-size:15px;'
                f'text-align:right;margin-bottom:8px;">{agent["name"]}</div>',
                unsafe_allow_html=True,
            )
            period = st.date_input(
                "בתפקיד", value=(month_first, month_last),
                min_value=month_first, max_value=month_last,
                format="DD/MM/YYYY", key=f"bd_{agent['id']}",
                help="שנה רק אם הנציג נכנס או עזב באמצע החודש.")
            # date_input hands back a single date while a new range is being picked
            start, end = (period if isinstance(period, (tuple, list)) and len(period) == 2
                          else (period[0] if isinstance(period, (tuple, list)) else period,
                                month_last))
            manual[agent["id"]] = {
                "meetings":   st.number_input("תיאומים",   min_value=0, key=f"bm_{agent['id']}"),
                "phoenix":    st.number_input("פניקס",     min_value=0, key=f"bp_{agent['id']}"),
                "idle_calls": st.number_input("שיחות סרק", min_value=0, key=f"bi_{agent['id']}"),
                # a full month means "untouched" — keep it out of the reports
                "role_start": None if start == month_first else start,
                "role_end":   None if end == month_last else end,
            }
            seen_first, seen_last = hints.get(agent["employee_id"], (None, None))
            if seen_first is not None:
                st.caption(f"נראה בקובץ הנוכחות מ-{seen_first.strftime('%d/%m')} "
                           f"עד {seen_last.strftime('%d/%m')}")

    # ── Compute / Save buttons ───────────────────────────────────────────────
    if att_file and vc_file:
        col_calc, col_save = st.columns(2)
        calc_clicked        = col_calc.button("חשב בונוסים")
        save_direct_clicked = col_save.button("💾 חשב ושמור להיסטוריה", type="primary")

        if calc_clicked or save_direct_clicked:
            try:
                res = compute_month(att_file, vc_file, fb_file, manual, agents,
                                    settings, month_label)
            except Exception as e:
                st.error(f"שגיאה בקריאת קבצים: {e}")
                return

            st.session_state[_SS_KEY] = res

            if save_direct_clicked:
                _do_save_and_navigate(res, month_label)

    elif _SS_KEY not in st.session_state:
        st.info("נא להעלות לפחות קבצי נוכחות ו-Voicenter")
        return

    if _SS_KEY not in st.session_state:
        return

    # ── Restore computed results from session_state ──────────────────────────
    res           = st.session_state[_SS_KEY]
    kpi_data      = res["kpi_data"]
    bonus_data    = res["bonus_data"]
    center_rate   = res["center_rate"]
    center_meets  = res["center_meets"]
    manager_bonus = res["manager_bonus"]
    billing       = res["billing"]
    month_label   = res["month_label"]

    # ── Step 3: results ──────────────────────────────────────────────────────
    missing = agents_missing_data(kpi_data)
    if missing:
        rows = [f"- **{name}** — חסר בדוח {', '.join(src)}" for name, src in missing]
        st.warning(
            "לנציגים הבאים לא נמצאו נתונים בדוחות, והמדדים שלהם מוצגים כאפס — "
            "מה שלא מבדיל בין ביצועים חלשים לנתון חסר:\n\n"
            + "\n".join(rows)
            + "\n\nבדוק שהשם ב**ניהול נציגים** תואם בדיוק לשם בדוח. הבונוסים לא שונו."
        )

    ui.section_header("תוצאות", step=3)
    c_a, c_b = st.columns(2)
    c_a.metric("קצב מוקד", f"{center_rate:.2f}/שעה",
               delta="עמד ביעד" if center_meets else "לא עמד")
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

    if st.button("שמור חודש להיסטוריה"):
        _do_save_and_navigate(res, month_label)

    # ── Per-agent cards ──────────────────────────────────────────────────────
    st.markdown("---")
    ui.section_header("פירוט לנציגים")
    for k, b in zip(kpi_data, bonus_data):
        _f = k.get("role_factor", 1.0)
        _pro = "—" if _f >= 1.0 else f"×{_f:.2f}"
        with st.expander(f"{k['name']}  —  סה\"כ ₪{b['total']:,}", key=f"exp_{k['agent_id']}"):
            c1, c2, c3, c4, c5, c6, c7, c8 = st.columns(8)
            c1.metric("שעות",         f"{k['hours']:.1f}")
            c2.metric("תיאומים",      k["meetings"])
            c3.metric("תיאומים/שעה",  f"{k['meetings_per_hour']:.2f}")
            c4.metric("תעסוקה",       f"{k['occupancy_pct']*100:.1f}%")
            c5.metric("סרק",          f"{k['idle_pct']*100:.2f}%")
            c6.metric('סה"כ שיחות',   k.get("total_calls", k.get("answered_calls", 0)))
            c7.metric("% מענה",       f"{k.get('answer_rate', 0)*100:.1f}%")
            c8.metric("ימים בתפקיד",   f"{k.get('role_days', '—')}")
            st.dataframe(
                [
                    {"רכיב": "עמלת תיאומים",    "₪": b["meetings_bonus"] - b.get("center_bonus", 0),
                     "יחסי": "—"},
                    {"רכיב": "בונוס ליעד צוותי", "₪": b.get("center_bonus", 0),
                     "יחסי": "—"},
                    {"רכיב": "בונוס פניקס",      "₪": b["phoenix_bonus"], "יחסי": "—"},
                    {"רכיב": "בונוס תעסוקה",    "₪": b["occupancy_bonus"], "יחסי": _pro},
                    {"רכיב": "בונוס סרק",        "₪": b["idle_bonus"],      "יחסי": _pro},
                    {"רכיב": "בונוס משוב",       "₪": b["feedback_bonus"],  "יחסי": _pro},
                    {"רכיב": 'סה"כ',             "₪": b["total"], "יחסי": ""},
                ],
                use_container_width=True, hide_index=True,
            )
            with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as af:
                af_path = af.name
            export_agent_bonus(k, b, month_label, af_path, center_meets=center_meets)
            with open(af_path, "rb") as af:
                st.download_button(
                    f"הורד Excel אישי — {k['name']}",
                    af.read(),
                    file_name=f"bonus_{k['name']}_{month_label}.xlsx",
                    key=f"dl_{k['agent_id']}",
                )
            os.unlink(af_path)

    # ── Center Excel download ────────────────────────────────────────────────
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
    st.download_button("הורד Excel מוקד מלא", xl_bytes, file_name=f"bonuses_{month_label}.xlsx")
    os.unlink(xl_path)

    # ── Step 4: email ────────────────────────────────────────────────────────
    ui.section_header("שליחת מיילים", step=4)
    client_html = build_monthly_client_email(billing, month_label)
    with st.expander("תצוגה מקדימה — מייל ללקוח", key="exp_client_preview"):
        st.components.v1.html(client_html, height=300, scrolling=True)

    confirmed = st.checkbox("בדקתי ואישרתי את כל המיילים")
    if not confirmed:
        return

    smtp     = settings["smtp"]
    password = st.secrets.get("SMTP_PASSWORD", "")
    c1, c2   = st.columns(2)
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
