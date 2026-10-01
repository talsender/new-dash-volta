# tests/test_role_period.py
"""Proration by time in the role — not by days attended.

Someone present all month earns the full fixed bonuses even after three sick
days; someone who joined on the 16th earns half. These cover the boundary.
"""
import datetime as dt
import pytest

from modules.month_calc import days_in_month, count_role_days
from modules.calculator import calculate_role_factor, employee_attendance_range


# ── length of the month, derived from the label the user already types ──────

def test_days_in_month_september():
    assert days_in_month("ספטמבר 2026") == 30


def test_days_in_month_february():
    assert days_in_month("פברואר 2026") == 28


def test_days_in_month_unparsable_label_falls_back_to_30():
    assert days_in_month("חודש כלשהו") == 30


# ── days in the role, clipped to the month ─────────────────────────────────

def test_count_role_days_defaults_to_the_whole_month():
    assert count_role_days("ספטמבר 2026") == 30


def test_count_role_days_joined_mid_month_is_inclusive_of_the_start():
    # 16/09 through 30/09 is 15 days, the 16th included
    assert count_role_days("ספטמבר 2026", start=dt.date(2026, 9, 16)) == 15


def test_count_role_days_left_mid_month_is_inclusive_of_the_last_day():
    assert count_role_days("ספטמבר 2026", end=dt.date(2026, 9, 10)) == 10


def test_count_role_days_joined_and_left_within_the_month():
    assert count_role_days("ספטמבר 2026",
                           start=dt.date(2026, 9, 12),
                           end=dt.date(2026, 9, 21)) == 10


def test_count_role_days_clips_a_range_that_starts_before_the_month():
    """Someone employed since last year is in the role for the whole month, not more."""
    assert count_role_days("ספטמבר 2026", start=dt.date(2025, 3, 1)) == 30


def test_count_role_days_clips_a_range_that_ends_after_the_month():
    assert count_role_days("ספטמבר 2026", end=dt.date(2027, 1, 1)) == 30


def test_count_role_days_range_entirely_outside_the_month_is_zero():
    assert count_role_days("ספטמבר 2026",
                           start=dt.date(2026, 10, 1),
                           end=dt.date(2026, 10, 20)) == 0


def test_count_role_days_end_before_start_is_zero():
    assert count_role_days("ספטמבר 2026",
                           start=dt.date(2026, 9, 20),
                           end=dt.date(2026, 9, 10)) == 0


# ── the factor itself ──────────────────────────────────────────────────────

def test_role_factor_half_a_month():
    assert calculate_role_factor(15, 30) == pytest.approx(0.5)


def test_role_factor_full_month_is_one():
    assert calculate_role_factor(30, 30) == 1.0


def test_role_factor_caps_at_one():
    assert calculate_role_factor(35, 30) == 1.0


def test_role_factor_no_days_in_role():
    assert calculate_role_factor(0, 30) == 0.0


def test_role_factor_unknown_month_length_assumes_full():
    assert calculate_role_factor(15, 0) == 1.0


# ── the hint: when the attendance file first and last sees the agent ───

def _att(rows):
    import pandas as pd
    return pd.DataFrame(rows)


def test_employee_attendance_range_spans_first_to_last_day_seen():
    """A new hire's first clock-in is the best evidence of their start date."""
    import pandas as pd
    df = _att([
        {'מספר עובד': 99495, 'סה"כ כללי': 8.0, 'תאריך': pd.Timestamp('2026-09-12')},
        {'מספר עובד': 99495, 'סה"כ כללי': 7.0, 'תאריך': pd.Timestamp('2026-09-28')},
        {'מספר עובד': 96186, 'סה"כ כללי': 8.0, 'תאריך': pd.Timestamp('2026-09-01')},
    ])
    first, last = employee_attendance_range(df, 99495)
    assert (first.day, first.month) == (12, 9)
    assert (last.day, last.month) == (28, 9)


def test_employee_attendance_range_ignores_days_with_no_hours():
    import pandas as pd
    df = _att([
        {'מספר עובד': 99495, 'סה"כ כללי': 0.0, 'תאריך': pd.Timestamp('2026-09-01')},
        {'מספר עובד': 99495, 'סה"כ כללי': 8.0, 'תאריך': pd.Timestamp('2026-09-12')},
    ])
    first, _ = employee_attendance_range(df, 99495)
    assert (first.day, first.month) == (12, 9)


def test_employee_attendance_range_unknown_employee():
    import pandas as pd
    df = _att([{'מספר עובד': 96186, 'סה"כ כללי': 8.0,
                'תאריך': pd.Timestamp('2026-09-01')}])
    assert employee_attendance_range(df, 99999) == (None, None)


def test_employee_attendance_range_without_a_date_column():
    df = _att([{'מספר עובד': 99495, 'סה"כ כללי': 8.0}])
    assert employee_attendance_range(df, 99495) == (None, None)
