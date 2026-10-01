import pytest, pandas as pd
from modules.calculator import (
    calculate_work_hours,
    calculate_meetings_per_hour,
    calculate_idle_pct,
    calculate_answer_rate,
    attendance_coverage,
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

def test_work_hours_partial_day_no_lunch_deduction():
    # A day under 1h should not trigger the 1h lunch deduction
    df = _df([{'מספר עובד': 96186, 'סה"כ כללי': 0.5}])
    assert calculate_work_hours(df, 96186) == pytest.approx(0.5)

def test_work_hours_mixed_full_and_partial_days():
    # 8h full day → deduct 1h; 0.5h partial day → no deduction
    df = _df([
        {'מספר עובד': 96186, 'סה"כ כללי': 8.0},
        {'מספר עובד': 96186, 'סה"כ כללי': 0.5},
    ])
    assert calculate_work_hours(df, 96186) == pytest.approx(7.5)  # (8+0.5) - 1

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

# ── Answer rate ──────────────────────────────────
def test_answer_rate_normal():
    assert calculate_answer_rate(1066, 1240) == pytest.approx(1066 / 1240, rel=0.01)

def test_answer_rate_zero_total_calls():
    assert calculate_answer_rate(0, 0) == 0.0

def test_answer_rate_all_answered():
    assert calculate_answer_rate(940, 940) == 1.0

# ── Center rate ───────────────────────────────────────────
def test_center_rate_combines_agents():
    agents = [{"hours": 80.0, "meetings": 80}, {"hours": 90.0, "meetings": 90}]
    assert calculate_center_rate(agents) == pytest.approx(1.0)

def test_center_rate_excludes_zero_hour_agents():
    agents = [{"hours": 0.0, "meetings": 10}, {"hours": 100.0, "meetings": 80}]
    assert calculate_center_rate(agents) == pytest.approx(0.8)


# ── Task 7: Bonus components ──────────────────────────────
from modules.calculator import (
    calculate_meetings_bonus,
    calculate_occupancy_bonus,
    calculate_idle_bonus,
    calculate_feedback_bonus,
)

def test_meetings_bonus_above_target_center_meets():
    assert calculate_meetings_bonus(80, 1.1, True) == 480   # (5+1)×80

def test_meetings_bonus_above_target_center_misses():
    assert calculate_meetings_bonus(80, 1.1, False) == 400  # 5×80

def test_meetings_bonus_below_target_center_meets():
    assert calculate_meetings_bonus(80, 0.9, True) == 400   # (4+1)×80

def test_meetings_bonus_below_target_center_misses():
    assert calculate_meetings_bonus(80, 0.9, False) == 320  # 4×80

def test_occupancy_tier_a():
    assert calculate_occupancy_bonus(0.36) == 300
def test_occupancy_tier_a_boundary():
    assert calculate_occupancy_bonus(0.35) == 300
def test_occupancy_tier_b():
    assert calculate_occupancy_bonus(0.31) == 200
def test_occupancy_tier_b_boundary():
    assert calculate_occupancy_bonus(0.30) == 200
def test_occupancy_none():
    assert calculate_occupancy_bonus(0.29) == 0

def test_idle_tier_a():
    assert calculate_idle_bonus(0.01) == 150
def test_idle_tier_a_boundary():
    assert calculate_idle_bonus(0.02) == 150
def test_idle_tier_b():
    assert calculate_idle_bonus(0.025) == 100
def test_idle_tier_b_boundary():
    assert calculate_idle_bonus(0.03) == 100
def test_idle_none():
    assert calculate_idle_bonus(0.04) == 0

def test_feedback_tier_a():
    assert calculate_feedback_bonus(8.52) == 150
def test_feedback_tier_a_boundary():
    assert calculate_feedback_bonus(8.5) == 150
def test_feedback_tier_b():
    assert calculate_feedback_bonus(8.1) == 100
def test_feedback_tier_b_boundary():
    assert calculate_feedback_bonus(8.0) == 100
def test_feedback_none_score():
    assert calculate_feedback_bonus(None) == 0
def test_feedback_below():
    assert calculate_feedback_bonus(7.9) == 0


# ── Task 8: Full bonus report ─────────────────────────────
from modules.calculator import calculate_agent_bonus, calculate_manager_bonus

def _settings():
    return {"bonus_thresholds": {
        "phoenix_employee_rate": 50, "phoenix_client_rate": 100,
        "manager_bonus_a_rate": 1.0, "manager_bonus_a": 2000,
        "manager_bonus_b_rate": 0.8, "manager_bonus_b": 1600,
        "manager_bonus_c": 1200,
    }}

def test_calculate_agent_bonus_full():
    kpi = {"meetings": 80, "individual_rate": 1.1, "occupancy_pct": 0.36,
           "idle_pct": 0.015, "feedback_score": 8.52, "phoenix": 3}
    result = calculate_agent_bonus(kpi, center_meets=True, settings=_settings())
    assert result["meetings_bonus"] == 480    # (5+1)×80
    assert result["occupancy_bonus"] == 300
    assert result["idle_bonus"] == 150
    assert result["feedback_bonus"] == 150
    assert result["phoenix_bonus"] == 150    # 3×50
    assert result["total"] == 1230

def test_calculate_manager_bonus_tier_a():
    assert calculate_manager_bonus(1.05, _settings()) == 2000

def test_calculate_manager_bonus_tier_b():
    assert calculate_manager_bonus(0.85, _settings()) == 1600

def test_calculate_manager_bonus_tier_c():
    assert calculate_manager_bonus(0.75, _settings()) == 1200


# ── Work-days proration of the bonus ────────────────────────

def _bonus_kpi():
    return {"meetings": 80, "individual_rate": 1.1, "occupancy_pct": 0.36,
            "idle_pct": 0.015, "feedback_score": 8.52, "phoenix": 3}


def test_agent_bonus_default_factor_reproduces_todays_numbers():
    """Safety property: an untouched call must be identical to passing factor 1.0."""
    plain    = calculate_agent_bonus(_bonus_kpi(), True, _settings())
    explicit = calculate_agent_bonus(_bonus_kpi(), True, _settings(), work_days_factor=1.0)
    assert plain == explicit
    assert plain["total"] == 1230


def test_agent_bonus_prorates_only_the_fixed_sum_components():
    r = calculate_agent_bonus(_bonus_kpi(), True, _settings(), work_days_factor=0.5)
    # per-unit components already scale with output — must not be cut twice
    assert r["meetings_bonus"] == 480
    assert r["phoenix_bonus"]  == 150
    # fixed monthly sums — halved
    assert r["occupancy_bonus"] == 150
    assert r["idle_bonus"]      == 75
    assert r["feedback_bonus"]  == 75
    assert r["total"] == 480 + 150 + 150 + 75 + 75


def test_agent_bonus_rounds_prorated_amounts_to_whole_shekels():
    """7/22 of the 300 ₪ tier is 95.45 → 95; of the 150 ₪ tier 47.7 → 48."""
    r = calculate_agent_bonus(_bonus_kpi(), True, _settings(), work_days_factor=7 / 22)
    assert r["occupancy_bonus"] == 95
    assert r["idle_bonus"]      == 48
    assert r["feedback_bonus"]  == 48


def test_agent_bonus_zero_days_pays_no_fixed_bonuses():
    r = calculate_agent_bonus(_bonus_kpi(), True, _settings(), work_days_factor=0.0)
    assert (r["occupancy_bonus"], r["idle_bonus"], r["feedback_bonus"]) == (0, 0, 0)
    assert r["meetings_bonus"] == 480


def test_agent_bonus_exposes_center_target_bonus_separately():
    """The team bonus stays folded into meetings_bonus, and is also reported on its own."""
    r = calculate_agent_bonus(_bonus_kpi(), True, _settings())
    assert r["center_bonus"]   == 80     # 80 meetings × 1 ₪
    assert r["meetings_bonus"] == 480    # unchanged — includes it


def test_agent_bonus_center_target_bonus_zero_when_center_misses():
    r = calculate_agent_bonus(_bonus_kpi(), False, _settings())
    assert r["center_bonus"]   == 0
    assert r["meetings_bonus"] == 400


# ── Work days detected from the attendance file ────────────────

def test_attendance_coverage_reports_distinct_dates_and_range():
    df = _df([
        {'מספר עובד': 1, 'סה"כ כללי': 8.0, 'תאריך': pd.Timestamp('2026-09-01')},
        {'מספר עובד': 2, 'סה"כ כללי': 8.0, 'תאריך': pd.Timestamp('2026-09-01')},
        {'מספר עובד': 1, 'סה"כ כללי': 7.0, 'תאריך': pd.Timestamp('2026-09-03')},
    ])
    first, last, days = attendance_coverage(df)
    assert days == 2
    assert (first.day, first.month) == (1, 9)
    assert (last.day, last.month) == (3, 9)


def test_attendance_coverage_without_date_column():
    """The parser does not guarantee a date column — the hint must degrade, not crash."""
    df = _df([{'מספר עובד': 1, 'סה"כ כללי': 8.0}])
    assert attendance_coverage(df) == (None, None, 0)
