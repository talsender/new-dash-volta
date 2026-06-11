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
