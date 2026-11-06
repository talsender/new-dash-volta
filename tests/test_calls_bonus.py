# tests/test_calls_bonus.py
"""Calls per hour replaces occupancy as what the agent is paid on.

The target is 60 calls in a nine-hour day. Occupancy keeps being measured and
shown — it just stops paying, and it stays the client's metric.
"""
import pytest

from modules.calculator import (calculate_calls_per_hour, calls_per_standard_day,
                                calculate_calls_bonus, calculate_agent_bonus,
                                calculate_gross_work_hours)


def _settings():
    return {"bonus_thresholds": {
        "standard_day_hours": 9,
        "calls_per_hour_tier_a": 6.5, "calls_per_hour_tier_a_bonus": 300,
        "calls_per_hour_tier_b": 6.0, "calls_per_hour_tier_b_bonus": 200,
        "calls_per_hour_tier_c": 5.5, "calls_per_hour_tier_c_bonus": 100,
        "phoenix_employee_rate": 50,
    }}


# ── the rate ───────────────────────────────────────────────────────────────

def test_calls_per_hour():
    assert calculate_calls_per_hour(733, 128.5) == pytest.approx(5.704, rel=1e-3)


def test_calls_per_hour_without_hours_is_zero_not_infinity():
    """No attendance means no rate — never a division that explodes."""
    assert calculate_calls_per_hour(500, 0) == 0.0


def test_calls_per_standard_day_normalises_to_a_nine_hour_day():
    assert calls_per_standard_day(6.667, 9) == pytest.approx(60.0, rel=1e-3)


# ── the tiers ──────────────────────────────────────────────────────────────

@pytest.mark.parametrize("per_hour,expected", [
    (6.5, 300), (7.1, 300),            # target met — 58.5 a day over nine hours
    (6.49, 200), (6.0, 200),           # middle rung
    (5.99, 100), (5.5, 100),           # bottom rung
    (5.49, 0), (0, 0),                 # below the floor
])
def test_calls_bonus_tiers(per_hour, expected):
    assert calculate_calls_bonus(per_hour, _settings()) == expected


def test_calls_bonus_never_pays_above_the_occupancy_ceiling():
    """The ceiling stays ₪300 — the whole point of the change was no extra cost."""
    assert calculate_calls_bonus(50, _settings()) == 300


# ── inside the agent bonus ─────────────────────────────────────────────────

def _kpi(calls_per_hour=6.5, occupancy=0.80):
    return {"meetings": 80, "individual_rate": 1.1, "occupancy_pct": occupancy,
            "idle_pct": 0.015, "feedback_score": 8.52, "phoenix": 3,
            "calls_per_hour": calls_per_hour}


def test_agent_bonus_pays_on_calls_not_occupancy():
    """High occupancy with weak dialling must no longer pay."""
    result = calculate_agent_bonus(_kpi(calls_per_hour=5.0, occupancy=0.95),
                                   True, _settings())
    assert result["calls_bonus"] == 0
    assert "occupancy_bonus" not in result


def test_agent_bonus_calls_tier_is_paid():
    result = calculate_agent_bonus(_kpi(calls_per_hour=6.1), True, _settings())
    assert result["calls_bonus"] == 200


def test_agent_bonus_calls_is_prorated_by_time_in_role():
    """A fixed monthly sum, so it shrinks with the role period like the others."""
    result = calculate_agent_bonus(_kpi(calls_per_hour=6.5), True, _settings(),
                                   role_factor=0.5)
    assert result["calls_bonus"] == 150


def test_agent_bonus_total_includes_the_calls_bonus():
    r = calculate_agent_bonus(_kpi(calls_per_hour=6.5), True, _settings())
    assert r["total"] == (r["meetings_bonus"] + r["calls_bonus"] + r["idle_bonus"]
                          + r["feedback_bonus"] + r["phoenix_bonus"])


# ── hours including breaks ────────────────────────────────

def test_gross_hours_do_not_deduct_the_break():
    """calculate_work_hours nets off an hour a day for lunch; the call rate is
    measured against the clock, so 6.5 an hour means 58.5 in a nine-hour day."""
    import pandas as pd
    df = pd.DataFrame([
        {'מספר עובד': 96186, 'סה"כ כללי': 9.0},
        {'מספר עובד': 96186, 'סה"כ כללי': 8.5},
        {'מספר עובד': 98752, 'סה"כ כללי': 9.0},
    ])
    assert calculate_gross_work_hours(df, 96186) == pytest.approx(17.5)


def test_gross_hours_unknown_employee_is_zero():
    import pandas as pd
    df = pd.DataFrame([{'מספר עובד': 96186, 'סה"כ כללי': 9.0}])
    assert calculate_gross_work_hours(df, 99999) == 0.0


def test_the_target_in_both_units():
    """6.5 an hour is the target; a nine-hour day makes it 58.5."""
    assert calls_per_standard_day(6.5, 9) == pytest.approx(58.5)
