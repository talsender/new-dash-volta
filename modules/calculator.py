import pandas as pd


def calculate_work_hours(attendance_df: pd.DataFrame, employee_id: int) -> float:
    emp = attendance_df[attendance_df['מספר עובד'] == employee_id]
    working = emp[emp['סה"כ כללי'] > 0]
    return max(0.0, float(working['סה"כ כללי'].sum()) - len(working))


def calculate_meetings_per_hour(meetings: int, hours: float) -> float:
    return 0.0 if hours == 0 else meetings / hours


def calculate_idle_pct(idle_calls: int, answered_calls: int) -> float:
    return 0.0 if answered_calls == 0 else idle_calls / answered_calls


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


def calculate_agent_bonus(kpi: dict, center_meets: bool, settings: dict) -> dict:
    t = settings["bonus_thresholds"]
    m = calculate_meetings_bonus(kpi["meetings"], kpi["individual_rate"], center_meets)
    o = calculate_occupancy_bonus(kpi["occupancy_pct"])
    i = calculate_idle_bonus(kpi["idle_pct"])
    fb = calculate_feedback_bonus(kpi.get("feedback_score"))
    ph = kpi["phoenix"] * t["phoenix_employee_rate"]
    return {"meetings_bonus": m, "occupancy_bonus": o, "idle_bonus": i,
            "feedback_bonus": fb, "phoenix_bonus": ph, "total": m + o + i + fb + ph}


def calculate_manager_bonus(center_rate: float, settings: dict) -> float:
    t = settings["bonus_thresholds"]
    if center_rate >= t["manager_bonus_a_rate"]:
        return t["manager_bonus_a"]
    if center_rate >= t["manager_bonus_b_rate"]:
        return t["manager_bonus_b"]
    return t["manager_bonus_c"]
