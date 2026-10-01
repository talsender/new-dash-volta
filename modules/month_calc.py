# modules/month_calc.py
"""Shared monthly KPI/bonus computation used by monthly_bonus and history screens."""
import tempfile, os, calendar, datetime as dt
from modules.data_loader import parse_attendance, parse_voicenter, parse_feedback
from modules.calculator import (calculate_work_hours, calculate_meetings_per_hour,
                                 calculate_idle_pct, calculate_answer_rate,
                                 calculate_role_factor,
                                 calculate_center_rate,
                                 calculate_agent_bonus, calculate_manager_bonus)

_HEB_MONTHS = {
    "ינואר": "01", "פברואר": "02", "מרץ": "03", "אפריל": "04",
    "מאי": "05", "יוני": "06", "יולי": "07", "אוגוסט": "08",
    "ספטמבר": "09", "אוקטובר": "10", "נובמבר": "11", "דצמבר": "12",
}


def _label_to_month_key(label: str) -> str:
    """'יוני 2026' → '2026-06'. Falls back to the label itself."""
    parts = label.strip().split()
    if len(parts) == 2:
        month_num = _HEB_MONTHS.get(parts[0])
        if month_num and parts[1].isdigit() and len(parts[1]) == 4:
            return f"{parts[1]}-{month_num}"
    return label.strip()


def _save_upload(uploaded, suffix):
    f = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    f.write(uploaded.read()); f.close()
    return f.name


def _find_feedback_entry(scores: dict, agent_name: str, feedback_name: str = None):
    """Return the raw entry (dict or float) for an agent, or None."""
    if not scores:
        return None
    for name in ([feedback_name.strip()] if feedback_name else []) + [agent_name.strip()]:
        if name in scores:
            return scores[name]
        nl = name.lower()
        fl = name.split()[0].lower()
        for key, val in scores.items():
            kl = key.strip().lower()
            if kl == nl or kl in nl or nl in kl:
                return val
            if fl == kl or kl.startswith(fl) or fl.startswith(kl):
                return val
    return None


def _get_feedback(scores: dict, agent_name: str, feedback_name: str = None):
    entry = _find_feedback_entry(scores, agent_name, feedback_name)
    if entry is None:
        return None
    return entry.get('score') if isinstance(entry, dict) else entry


def days_in_month(month_label: str) -> int:
    """Calendar days in the month the label names, falling back to 30."""
    try:
        year, month = (int(v) for v in _label_to_month_key(month_label).split("-"))
        return calendar.monthrange(year, month)[1]
    except (ValueError, TypeError):
        return 30


def _month_bounds(month_label: str):
    """(first, last) dates of the month, or None when the label is unreadable."""
    try:
        year, month = (int(v) for v in _label_to_month_key(month_label).split("-"))
    except (ValueError, TypeError):
        return None, None
    return dt.date(year, month, 1), dt.date(year, month, days_in_month(month_label))


def count_role_days(month_label: str, start=None, end=None) -> int:
    """Calendar days the agent held the role inside this month, both ends included.

    A range reaching outside the month is clipped to it, so someone employed
    since last year is in the role for the whole month and no more. An empty
    or inverted range is zero.
    """
    first, last = _month_bounds(month_label)
    if first is None:
        return days_in_month(month_label)
    begin = max(start, first) if start else first
    finish = min(end, last) if end else last
    return max(0, (finish - begin).days + 1)


def agents_missing_data(kpi_data: list) -> list:
    """[(name, ["Voicenter", ...]), ...] for agents whose source reports held nothing.

    Their metrics read as zeros, which is indistinguishable from genuinely bad
    performance — and a zero idle rate even earns the top idle bonus. Surfacing
    it is the point; the numbers themselves are left alone.
    """
    out = []
    for k in kpi_data:
        missing = []
        if not k.get("has_vc_data", True):
            missing.append("Voicenter")
        if not k.get("has_attendance", True):
            missing.append("נוכחות")
        if missing:
            out.append((k.get("name", "?"), missing))
    return out


def compute_month(att_file, vc_file, fb_file, manual, agents, settings, month_label,
                  month_key=None):
    """Parse uploaded files and compute all KPI/bonus data.

    Raises on parse failure — caller should catch and display the error.
    Returns a results dict.
    """
    t = settings["bonus_thresholds"]
    month_days = days_in_month(month_label)

    att_path = _save_upload(att_file, '.xlsx')
    vc_path  = _save_upload(vc_file, '.xls')
    fb_path  = _save_upload(fb_file, '.xlsx') if fb_file else None
    try:
        att_df          = parse_attendance(att_path)
        vc_df           = parse_voicenter(vc_path)
        feedback_scores = parse_feedback(fb_path) if fb_path else {}
    finally:
        for p in [att_path, vc_path, fb_path]:
            if p:
                try:
                    os.unlink(p)
                except OSError:
                    pass

    kpi_data = []
    for agent in agents:
        hours   = calculate_work_hours(att_df, agent["employee_id"])
        inp     = manual[agent["id"]]
        vc_name = agent.get('voicenter_name') or agent['name']
        vc_row  = vc_df[vc_df['משתמש'].str.lower().str.contains(vc_name.lower(), na=False, regex=False)]
        if not len(vc_row):
            first_name = agent['name'].split()[0]
            vc_row = vc_df[vc_df['משתמש'].str.contains(first_name, na=False, regex=False)]
        answered    = int(vc_row['נענו'].iloc[0])              if len(vc_row) else 0
        total_calls = int(vc_row['כניסות'].iloc[0])           if len(vc_row) else 0
        occ_pct     = float(vc_row['אחוז תעסוקה נטו'].iloc[0]) if len(vc_row) else 0.0
        has_vc      = bool(len(vc_row))
        # untouched dates mean the whole month — never prorate what was not asked for
        role_start  = inp.get("role_start")
        role_end    = inp.get("role_end")
        role_days   = count_role_days(month_label, role_start, role_end)
        role_factor = calculate_role_factor(role_days, month_days)
        kpi_data.append({
            "agent_id": agent["id"], "name": agent["name"],
            "employee_id": agent["employee_id"], "email": agent.get("email", ""),
            "role_days": role_days, "role_factor": role_factor,
            "role_start": role_start, "role_end": role_end,
            "has_vc_data": has_vc, "has_attendance": hours > 0,
            "hours": hours, "meetings": inp["meetings"],
            "meetings_per_hour": calculate_meetings_per_hour(inp["meetings"], hours),
            "occupancy_pct": occ_pct, "idle_calls": inp["idle_calls"],
            "answered_calls": answered,
            "total_calls":    total_calls,
            "answer_rate": calculate_answer_rate(answered, total_calls),
            "idle_pct": calculate_idle_pct(inp["idle_calls"], answered),
            "phoenix": inp["phoenix"],
            "feedback_score": _get_feedback(feedback_scores, agent["name"],
                                            feedback_name=agent.get("feedback_name")),
            "feedback_details": _find_feedback_entry(feedback_scores, agent["name"],
                                                     feedback_name=agent.get("feedback_name")),
        })

    center_rate  = calculate_center_rate([{"hours": k["hours"], "meetings": k["meetings"]} for k in kpi_data])
    center_meets = center_rate >= t["meetings_per_hour_tier_a"]

    bonus_data = []
    for k in kpi_data:
        kpi_in = {"meetings": k["meetings"], "individual_rate": k["meetings_per_hour"],
                  "occupancy_pct": k["occupancy_pct"], "idle_pct": k["idle_pct"],
                  "feedback_score": k["feedback_score"], "phoenix": k["phoenix"]}
        b = calculate_agent_bonus(kpi_in, center_meets, settings,
                                  work_days_factor=k.get("role_factor", 1.0))
        bonus_data.append({"name": k["name"], "employee_id": k["employee_id"],
                           "role_days": k.get("role_days", month_days), **b})

    manager_bonus = calculate_manager_bonus(center_rate, settings)
    total_phoenix = sum(k["phoenix"] for k in kpi_data)
    billing = {
        "hours_by_agent":  {k["name"]: k["hours"] for k in kpi_data},
        "total_hours":     sum(k["hours"] for k in kpi_data),
        "phoenix_count":   total_phoenix,
        "phoenix_billing": total_phoenix * t["phoenix_client_rate"],
    }

    return {
        "kpi_data":      kpi_data,
        "bonus_data":    bonus_data,
        "center_rate":   center_rate,
        "center_meets":  center_meets,
        "manager_bonus": manager_bonus,
        "billing":       billing,
        "days_in_month": month_days,
        "month_label": month_label,
        "month_key":   (month_key or month_label).strip(),
    }


def build_snapshot(res, month_label):
    """Build history snapshot dict from computed results."""
    kpi_data   = res["kpi_data"]
    bonus_data = res["bonus_data"]
    billing    = res["billing"]
    n = len(kpi_data) or 1
    month_days = res.get("days_in_month", res.get("full_month_days", 30))
    total_answered = sum(k.get("answered_calls", 0) for k in kpi_data)
    total_calls    = sum(k.get("total_calls", k.get("answered_calls", 0)) for k in kpi_data)
    return {
        "month":             res.get("month_key") or _label_to_month_key(month_label),
        "label":             month_label,
        # Center-level metrics
        "center_rate":       res["center_rate"],
        "center_met_target": res["center_meets"],
        "manager_bonus":     res["manager_bonus"],
        "total_billing":     billing["phoenix_billing"],
        "total_meetings":       sum(k["meetings"] for k in kpi_data),
        "total_hours":          billing["total_hours"],
        "total_phoenix":        billing["phoenix_count"],
        "total_idle_calls":     sum(k.get("idle_calls", 0) for k in kpi_data),
        "total_answered_calls": total_answered,
        "total_calls":          total_calls,
        "answer_rate":          calculate_answer_rate(total_answered, total_calls),
        "avg_occupancy_pct":    sum(k["occupancy_pct"] for k in kpi_data) / n,
        "avg_idle_pct":         sum(k["idle_pct"] for k in kpi_data) / n,
        "total_agent_bonus":    sum(b["total"] for b in bonus_data),
        "days_in_month":        month_days,
        # Per-agent breakdown
        "agents": [{
            "name":              k["name"],
            "hours":             k["hours"],
            "meetings":          k["meetings"],
            "meetings_per_hour": k["meetings_per_hour"],
            "occupancy_pct":     k["occupancy_pct"],
            "idle_pct":          k["idle_pct"],
            "role_days":         k.get("role_days", k.get("work_days", month_days)),
            "role_factor":       k.get("role_factor", k.get("work_days_factor", 1.0)),
            "answer_rate":       calculate_answer_rate(
                k.get("answered_calls", 0),
                k.get("total_calls", k.get("answered_calls", 0))),
            "feedback_score":    k["feedback_score"],
            "phoenix":           k["phoenix"],
            "bonus_total":       b["total"],
        } for k, b in zip(kpi_data, bonus_data)]
    }
