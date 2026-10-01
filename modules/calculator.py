import pandas as pd


def calculate_work_hours(attendance_df: pd.DataFrame, employee_id: int) -> float:
    emp = attendance_df[attendance_df['מספר עובד'] == employee_id]
    working = emp[emp['סה"כ כללי'] > 0]
    full_days = working[working['סה"כ כללי'] >= 1]
    return max(0.0, float(working['סה"כ כללי'].sum()) - len(full_days))


def employee_attendance_range(attendance_df: pd.DataFrame, employee_id: int):
    """(first, last) dates the employee clocked in — evidence of when they
    entered or left the role, for the hint beside the role-period input.

    Returns (None, None) when the employee is absent from the report or the
    file carries no date column.
    """
    if 'תאריך' not in attendance_df.columns:
        return None, None
    emp = attendance_df[(attendance_df['מספר עובד'] == employee_id)
                        & (attendance_df['סה"כ כללי'] > 0)]
    dates = pd.to_datetime(emp['תאריך'], errors='coerce').dropna()
    if dates.empty:
        return None, None
    return dates.min(), dates.max()


def attendance_coverage(attendance_df: pd.DataFrame):
    """(first_date, last_date, distinct_days) of the report, for the role-period hint.

    Returns (None, None, 0) when the file carries no date column, so callers
    can tell "no coverage known" from a genuine one-day report.
    """
    if 'תאריך' not in attendance_df.columns:
        return None, None, 0
    worked = attendance_df[attendance_df['סה"כ כללי'] > 0]
    dates = pd.to_datetime(worked['תאריך'], errors='coerce').dropna()
    if dates.empty:
        return None, None, 0
    return dates.min(), dates.max(), int(dates.dt.normalize().nunique())


def calculate_meetings_per_hour(meetings: int, hours: float) -> float:
    return 0.0 if hours == 0 else meetings / hours


def calculate_idle_pct(idle_calls: int, answered_calls: int) -> float:
    return 0.0 if answered_calls == 0 else idle_calls / answered_calls


def calculate_answer_rate(answered_calls: int, total_calls: int) -> float:
    return 0.0 if total_calls == 0 else answered_calls / total_calls


def calculate_role_factor(days_in_role: float, days_in_month: float) -> float:
    """Share of the month the agent held the role, capped at 1.0.

    Time in the role, not days attended — someone there all month keeps the
    full bonus after a sick day. A days_in_month of 0 means we were not told
    the month length, so assume a full month rather than silently zeroing
    someone's bonus.
    """
    if days_in_month <= 0:
        return 1.0
    return min(1.0, days_in_role / days_in_month)


def calculate_center_rate(agents: list) -> float:
    active = [a for a in agents if a["hours"] > 0]
    if not active:
        return 0.0
    return sum(a["meetings"] for a in active) / sum(a["hours"] for a in active)


def calculate_meetings_bonus(meetings: int, individual_rate: float, center_meets: bool) -> float:
    base = 5 if individual_rate >= 1.0 else 4
    extra = 1 if center_meets else 0
    return meetings * (base + extra)


def calculate_occupancy_bonus(occupancy_pct: float) -> float:
    if occupancy_pct >= 0.35:
        return 300
    if occupancy_pct >= 0.30:
        return 200
    return 0


def calculate_idle_bonus(idle_pct: float) -> float:
    if idle_pct <= 0.02:
        return 150
    if idle_pct <= 0.03:
        return 100
    return 0


def calculate_feedback_bonus(score) -> float:
    if score is None:
        return 0
    if score >= 8.5:
        return 150
    if score >= 8.0:
        return 100
    return 0


def calculate_agent_bonus(kpi: dict, center_meets: bool, settings: dict,
                          work_days_factor: float = 1.0) -> dict:
    """Bonus breakdown for one agent.

    work_days_factor prorates only the fixed monthly sums (occupancy, idle,
    feedback). The per-unit components — the meetings commission, the team
    target bonus folded into it, and phoenix — already scale with what the
    agent produced, so cutting them again would penalise the same absence
    twice. A factor of 1.0 reproduces the untouched calculation exactly.

    meetings_bonus keeps its original meaning and still includes the team
    target bonus; center_bonus reports that part on its own, for display.
    """
    t = settings["bonus_thresholds"]
    m = calculate_meetings_bonus(kpi["meetings"], kpi["individual_rate"], center_meets)
    ctr = kpi["meetings"] if center_meets else 0
    o = round(calculate_occupancy_bonus(kpi["occupancy_pct"]) * work_days_factor)
    i = round(calculate_idle_bonus(kpi["idle_pct"]) * work_days_factor)
    fb = round(calculate_feedback_bonus(kpi.get("feedback_score")) * work_days_factor)
    ph = kpi["phoenix"] * t["phoenix_employee_rate"]
    return {"meetings_bonus": m, "center_bonus": ctr,
            "occupancy_bonus": o, "idle_bonus": i,
            "feedback_bonus": fb, "phoenix_bonus": ph, "total": m + o + i + fb + ph}


def calculate_manager_bonus(center_rate: float, settings: dict) -> float:
    t = settings["bonus_thresholds"]
    if center_rate >= t["manager_bonus_a_rate"]:
        return t["manager_bonus_a"]
    if center_rate >= t["manager_bonus_b_rate"]:
        return t["manager_bonus_b"]
    return t["manager_bonus_c"]
