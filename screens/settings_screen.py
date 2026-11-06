# screens/settings_screen.py
import streamlit as st
from modules.config_manager import load_settings, save_settings
from modules import ui


def render():
    ui.page_header("הגדרות מערכת", icon="⚙️", subtitle="ספי בונוס, SMTP ונמענים")

    s = load_settings()
    t = s["bonus_thresholds"]

    ui.section_header("ספי בונוס")
    c1, c2 = st.columns(2)
    with c1:
        t["meetings_per_hour_tier_a"] = st.number_input(
            "פגישות/שעה — סף תעריף 5₪", value=float(t["meetings_per_hour_tier_a"]), step=0.1)
        st.caption("יעד השיחות — מה שהנציג מתוגמל עליו")
        t["standard_day_hours"] = int(st.number_input(
            "שעות ביום עבודה מלא", value=int(t.get("standard_day_hours", 9)), step=1,
            help="לפיו מחושב 'שיחות ליום' מתוך שיחות לשעה"))
        _std = int(t.get("standard_day_hours", 9))
        for tier, default_rate, default_bonus in (("a", 6.5, 300), ("b", 6.0, 200), ("c", 5.5, 100)):
            cc1, cc2 = st.columns(2)
            rate = float(cc1.number_input(
                f"שיחות לשעה — סף {tier.upper()}",
                value=float(t.get(f"calls_per_hour_tier_{tier}", default_rate)), step=0.1,
                help="נמדד מול שעות על השעון, כולל הפסקות"))
            t[f"calls_per_hour_tier_{tier}"] = rate
            t[f"calls_per_hour_tier_{tier}_bonus"] = int(cc2.number_input(
                f"בונוס {tier.upper()} ₪",
                value=int(t.get(f"calls_per_hour_tier_{tier}_bonus", default_bonus)), step=10))
            st.caption(f"= {rate * _std:.1f} שיחות ביום של {_std} שעות")
        st.caption("ספי תעסוקה — לתצוגה ולצביעה בדוחות בלבד, לא משלמים")
        t["occupancy_tier_a_pct"] = st.number_input("תעסוקה A %", value=int(t["occupancy_tier_a_pct"]))
        t["occupancy_tier_b_pct"] = st.number_input("תעסוקה B %", value=int(t["occupancy_tier_b_pct"]))
        t["idle_tier_a_pct"] = st.number_input("סרק A % (מקסימום)", value=int(t["idle_tier_a_pct"]))
        t["idle_tier_b_pct"] = st.number_input("סרק B % (מקסימום)", value=int(t["idle_tier_b_pct"]))
    with c2:
        t["feedback_tier_a_score"] = st.number_input("ציון משוב A", value=float(t["feedback_tier_a_score"]), step=0.1)
        t["feedback_tier_b_score"] = st.number_input("ציון משוב B", value=float(t["feedback_tier_b_score"]), step=0.1)
        t["phoenix_employee_rate"] = st.number_input("פניקס לנציג ₪", value=int(t["phoenix_employee_rate"]))
        t["phoenix_client_rate"]   = st.number_input("פניקס ללקוח ₪", value=int(t["phoenix_client_rate"]))
        t["manager_bonus_a"]       = st.number_input("בונוס מנהל A ₪", value=int(t["manager_bonus_a"]))
        t["manager_bonus_b"]       = st.number_input("בונוס מנהל B ₪", value=int(t["manager_bonus_b"]))
        t["manager_bonus_c"]       = st.number_input("בונוס מנהל C ₪", value=int(t["manager_bonus_c"]))

    st.markdown("<hr/>", unsafe_allow_html=True)
    ui.section_header("הגדרות SMTP")
    smtp = s["smtp"]
    smtp["host"]       = st.text_input("שרת",         smtp.get("host", ""))
    smtp["port"]       = int(st.number_input("פורט",  value=int(smtp.get("port", 587))))
    smtp["username"]   = st.text_input("שם משתמש",    smtp.get("username", ""))
    smtp["from_email"] = st.text_input("כתובת שולח",  smtp.get("from_email", ""))
    st.info("סיסמת SMTP מוגדרת ב-Streamlit Secrets (SMTP_PASSWORD)")

    st.markdown("<hr/>", unsafe_allow_html=True)
    ui.section_header("נמענים")
    r = s["recipients"]
    r["management"] = [x.strip() for x in st.text_area(
        "הנהלה (שורה לכל כתובת)", "\n".join(r.get("management", []))).splitlines() if x.strip()]
    r["client"] = [x.strip() for x in st.text_area(
        "לקוח — וולטה (שורה לכל כתובת)", "\n".join(r.get("client", []))).splitlines() if x.strip()]

    st.markdown("<br/>", unsafe_allow_html=True)
    if st.button("שמור הגדרות"):
        save_settings(s)
        st.success("הגדרות נשמרו ✅")
