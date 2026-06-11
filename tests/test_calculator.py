import pytest, pandas as pd
from modules.calculator import (
    calculate_work_hours,
    calculate_meetings_per_hour,
    calculate_idle_pct,
    calculate_center_rate,
)

def _df(rows):
    return pd.DataFrame(rows)

# ── Work hours ────────────────────────────────────────────
def test_work_hours_single_day():
    df = _df([{'מספר עובד': 96186, 'סה"כ כללי': 8.0}])
    assert calculate_work_hours(df, 96186) == pytest.approx(7.0)

def test_work_hours_multiple_days():
    df = _df([
        {'מספר עובד': 96186, 'סה"כ כללי': 8.0},
        {'מספר עובד': 96186, 'סה"כ כללי': 7.0},
        {'מספר עובד': 96186, 'סה"כ כללי': 6.0},
    ])
    assert calculate_work_hours(df, 96186) == pytest.approx(18.0)  # (8+7+6) - 3

def test_work_hours_ignores_absent_days():
    # Zero-hour rows are absent days — no 1h deduction
    df = _df([
        {'מספר עובד': 96186, 'סה"כ כללי': 0.0},
        {'מספר עובד': 96186, 'סה"כ כללי': 8.0},
    ])
    assert calculate_work_hours(df, 96186) == pytest.approx(7.0)  # 8 - 1

def test_work_hours_unknown_employee():
    df = _df([{'מספר עובד': 96186, 'סה"כ כללי': 8.0}])
    assert calculate_work_hours(df, 99999) == pytest.approx(0.0)

# ── Meetings per hour ─────────────────────────────────────
def test_meetings_per_hour_normal():
    assert calculate_meetings_per_hour(80, 70.0) == pytest.approx(80 / 70, rel=0.01)

def test_meetings_per_hour_zero_hours():
    assert calculate_meetings_per_hour(10, 0.0) == 0.0

# ── Idle % ────────────────────────────────────────────────
def test_idle_pct_normal():
    assert calculate_idle_pct(2, 190) == pytest.approx(2 / 190, rel=0.01)

def test_idle_pct_zero_answered():
    assert calculate_idle_pct(0, 0) == 0.0

# ── Center rate ───────────────────────────────────────────
def test_center_rate_combines_agents():
    agents = [{"hours": 80.0, "meetings": 80}, {"hours": 90.0, "meetings": 90}]
    assert calculate_center_rate(agents) == pytest.approx(1.0)

def test_center_rate_excludes_zero_hour_agents():
    agents = [{"hours": 0.0, "meetings": 10}, {"hours": 100.0, "meetings": 80}]
    assert calculate_center_rate(agents) == pytest.approx(0.8)
