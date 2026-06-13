# screens/history.py
import streamlit as st
import json
import io
import tempfile
import os
from modules.history_manager import load_history, save_month, delete_month
from modules.month_calc import compute_month, build_snapshot
from modules.config_manager import load_agents, load_settings
from modules.excel_exporter import export_history_summary
from modules import ui

try:
    import plotly.express as px
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

_SAVE_LABELS = {"github": "GitHub — קבוע", "local": "מקומי", "session": "זיכרון"}

_PLOT_LAYOUT = dict(
    paper_bgcolor="rgba(8,20,34,0.9)",
    plot_bgcolor="rgba(4,8,15,0.6)",
    font=dict(color="#7A9CBE", family="Heebo"),
    xaxis=dict(gridcolor="rgba(255,255,255,0.06)", color="#7A9CBE"),
    yaxis=dict(gridcolor="rgba(255,255,255,0.06)", color="#7A9CBE", side="right"),
    title_font=dict(color="#EDF2F7", size=14),
    margin=dict(l=20, r=60, t=40, b=20),
)


def _rtl_table(rows: list) -> str:
    """Render a dark-themed RTL HTML table (direction: rtl, first column on right)."""
    if not rows:
        return ""
    cols = list(rows[0].keys())
    th = "".join(
        f'<th style="padding:10px 14px;background:rgba(27,95,170,0.25);'
        f'color:#F5A800;font-weight:600;white-space:nowrap;'
        f'border-bottom:2px solid rgba(245,168,0,0.25);">{c}</th>'
        for c in cols
    )
    body = ""
    for i, row in enumerate(rows):
        bg = "rgba(255,255,255,0.03)" if i % 2 else "transparent"
        tds = "".join(
            f'<td style="padding:8px 14px;color:#EDF2F7;background:{bg};'
            f'border-bottom:1px solid rgba(255,255,255,0.06);white-space:nowrap;">'
            f'{row[c]}</td>'
            for c in cols
        )
        body += f"<tr>{tds}</tr>"
    return (
        '<div style="overflow-x:auto;direction:rtl;margin-bottom:8px;">'
        '<table style="width:100%;border-collapse:collapse;direction:rtl;'
        'text-align:right;font-family:Heebo,sans-serif;font-size:14px;">'
        f"<thead><tr>{th}</tr></thead>"
        f"<tbody>{body}</tbody>"
        "</table></div>"
    )


def _add_month_from_excel():
    with st.expander("➕ הוסף חודש מקובצי Excel"):
        agents   = [a for a in load_agents() if a["active"]]
        settings = load_settings()

        c1, c2, c3 = st.columns(3)
        att_file = c1.file_uploader("נוכחות (.xlsx)",              type=['xlsx'],       key="h_att")
        vc_file  = c2.file_uploader("Voicenter (.xls)",            type=['xls','xlsx'], key="h_vc")
        fb_file  = c3.file_uploader("משובים (.xlsx) — אופציונלי", type=['xlsx'],       key="h_fb")

        month_label = st.text_input("חודש", "יוני 2026", key="h_month")

        manual = {}
        cols = st.columns(len(agents))
        for col, agent in zip(cols, agents):
            with col:
                st.markdown(
                    f'<div style="color:#F5A800;font-weight:700;font-size:14px;'
                    f'text-align:right;margin-bottom:6px;">{agent["name"]}</div>',
                    unsafe_allow_html=True,
                )
                manual[agent["id"]] = {
                    "meetings":   st.number_input("תיאומים",   min_value=0, key=f"hm_{agent['id']}"),
                    "phoenix":    st.number_input("פניקס",     min_value=0, key=f"hp_{agent['id']}"),
                    "idle_calls": st.number_input("שיחות סרק", min_value=0, key=f"hi_{agent['id']}"),
                }

        if st.button("חשב ושמור להיסטוריה", type="primary", key="h_save_btn",
                     disabled=not (att_file and vc_file)):
            try:
                res = compute_month(att_file, vc_file, fb_file, manual, agents, settings, month_label)
            except Exception as e:
                st.error(f"שגיאה בקריאת קבצים: {e}")
                return

            snapshot = build_snapshot(res, month_label)
            save_src = save_month(snapshot)
            st.toast(f"✅ חודש {month_label} נשמר ({_SAVE_LABELS.get(save_src, 'נשמר')})")
            st.rerun()


def _upload_json_section():
    uploaded = st.file_uploader("📤 העלה היסטוריה (JSON)", type=["json"], key="hist_upload")
    if uploaded:
        data = json.loads(uploaded.read().decode("utf-8"))
        for m in data:
            save_month(m)
        st.success(f"שוחזרו {len(data)} חודשים ✅")
        st.rerun()


def render():
    ui.page_header("היסטוריה וניתוח", icon="📈", subtitle="מגמות ביצועים לאורך זמן")

    # GitHub persistence status
    try:
        token    = st.secrets.get("GITHUB_TOKEN", "")
        repo     = st.secrets.get("GITHUB_REPO",  "")
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
        if "kpi_history" in st.session_state:
            del st.session_state["kpi_history"]
        st.rerun()

    history = load_history()
    if not history:
        st.info("אין נתונים היסטוריים עדיין. לאחר חישוב חודשי לחץ 'שמור חודש להיסטוריה'.")
        _add_month_from_excel()
        _upload_json_section()
        return

    labels = [h["label"] for h in history]

    # ── RTL summary table ────────────────────────────────────────────────────
    ui.section_header("סיכום חודשים — ביצועי מוקד")
    table_rows = [{
        "חודש":          h["label"],
        "שעות":          f"{h.get('total_hours', 0):.1f}",
        "תיאומים":       h.get("total_meetings", "—"),
        "תיאומים/שעה":   f"{h.get('center_rate', 0):.2f}",
        "שיחות סרק":     h.get("total_idle_calls", "—"),
        'סה"כ שיחות':    h.get("total_calls", h.get("total_answered_calls", "—")),
        "פניקס":         h.get("total_phoenix", "—"),
    } for h in history]
    st.markdown(_rtl_table(table_rows), unsafe_allow_html=True)

    # ── Excel export ─────────────────────────────────────────────────────────
    try:
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as _f:
            _xl_path = _f.name
        export_history_summary(history, _xl_path)
        with open(_xl_path, "rb") as _f:
            _xl_bytes = _f.read()
        os.unlink(_xl_path)
        st.download_button(
            "📊 ייצא לאקסל",
            _xl_bytes,
            file_name="kpi_history_summary.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    except Exception as _e:
        st.warning(f"שגיאה בייצוא Excel: {_e}")

    # ── History management (delete) ──────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    ui.section_header("ניהול היסטוריה")
    for h in history:
        col_del, col_lbl = st.columns([1, 5])
        col_lbl.markdown(
            f'<div style="text-align:right;padding-top:6px;">'
            f'<b>{h["label"]}</b> — {h.get("total_meetings", "—")} תיאומים, '
            f'{h.get("total_hours", 0):.1f} שעות</div>',
            unsafe_allow_html=True,
        )
        if col_del.button("🗑️ מחק", key=f"del_{h['month']}"):
            delete_month(h["month"])
            st.toast(f"🗑️ {h['label']} נמחק")
            st.rerun()

    if HAS_PLOTLY:
        # ── Total calls chart ────────────────────────────────────────────────
        call_data = [
            (h["label"], v)
            for h in history
            for v in [h.get("total_calls", h.get("total_answered_calls"))]
            if isinstance(v, (int, float))
        ]
        if call_data:
            ui.section_header('סה"כ שיחות לפי חודש')
            clabels, cvals = zip(*call_data)
            fig_calls = px.bar(
                x=list(clabels), y=list(cvals),
                labels={"x": "חודש", "y": 'סה"כ שיחות'},
                color_discrete_sequence=["#3DD68C"],
            )
            fig_calls.update_layout(**_PLOT_LAYOUT)
            st.plotly_chart(fig_calls, use_container_width=True)

        # ── Center rate over time ────────────────────────────────────────────
        ui.section_header("קצב מוקד לאורך זמן")
        fig = px.line(x=labels, y=[h["center_rate"] for h in history],
                      labels={"x": "חודש", "y": "פגישות/שעה"},
                      markers=True, color_discrete_sequence=["#F5A800"])
        fig.add_hline(y=1.0, line_dash="dash", line_color="#3DD68C", annotation_text="יעד")
        fig.update_layout(**_PLOT_LAYOUT)
        st.plotly_chart(fig, use_container_width=True)

        # ── Phoenix ──────────────────────────────────────────────────────────
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
        _upload_json_section()

    st.markdown("<hr/>", unsafe_allow_html=True)
    _add_month_from_excel()
