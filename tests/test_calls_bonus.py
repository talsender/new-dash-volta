# tests/test_calls_bonus.py
"""Calls per hour replaces occupancy as what the agent is paid on.

The target is 60 calls in a nine-hour day. Occupancy keeps being measured and
shown — it just stops paying, and it stays the client's metric.
"""
import pytest

from modules.calculator import (calculate_calls_per_hour, calls_per_standard_day,
                                calculate_calls_bonus, calculate_agent_bonus)


def _settings():
    return {"bonus_thresholds": {
        "standard_day_hours": 9,
        "calls_per_day_tier_a": 60, "calls_per_day_tier_a_bonus": 300,
        "calls_per_day_tier_b": 55, "calls_per_day_tier_b_bonus": 200,
        "calls_per_day_tier_c": 50, "calls_per_day_tier_c_bonus": 100,
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

@pytest.mark.parametrize("per_day,expected", [
    (60, 300), (61.4, 300),            # target met
    (59.9, 200), (55, 200),            # middle rung
    (54.9, 100), (50, 100),            # bottom rung
    (49.9, 0), (0, 0),                 # below the floor
])
def test_calls_bonus_tiers(per_day, expected):
    assert calculate_calls_bonus(per_day, _settings()) == expected


def test_calls_bonus_never_pays_above_the_occupancy_ceiling():
    """The ceiling stays ₪300 — the whole point of the change was no extra cost."""
    assert calculate_calls_bonus(500, _settings()) == 300


# ── inside the agent bonus ─────────────────────────────────────────────────

def _kpi(calls_per_day=60.0, occupancy=0.80):
    return {"meetings": 80, "individual_rate": 1.1, "occupancy_pct": occupancy,
            "idle_pct": 0.015, "feedback_score": 8.52, "phoenix": 3,
            "calls_per_day": calls_per_day}


def test_agent_bonus_pays_on_calls_not_occupancy():
    """High occupancy with weak dialling must no longer pay."""
    result = calculate_agent_bonus(_kpi(calls_per_day=48, occupancy=0.95),
                                   True, _settings())
    assert result["calls_bonus"] == 0
    assert "occupancy_bonus" not in result


def test_agent_bonus_calls_tier_is_paid():
    result = calculate_agent_bonus(_kpi(calls_per_day=56), True, _settings())
    assert result["calls_bonus"] == 200


def test_agent_bonus_calls_is_prorated_by_time_in_role():
    """A fixed monthly sum, so it shrinks with the role period like the others."""
    result = calculate_agent_bonus(_kpi(calls_per_day=60), True, _settings(),
                                   role_factor=0.5)
    assert result["calls_bonus"] == 150


def test_agent_bonus_total_includes_the_calls_bonus():
    r = calculate_agent_bonus(_kpi(calls_per_day=60), True, _settings())
    assert r["total"] == (r["meetings_bonus"] + r["calls_bonus"] + r["idle_bonus"]
                          + r["feedback_bonus"] + r["phoenix_bonus"])
