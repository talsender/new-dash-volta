# tests/test_bad_cells.py
"""One unreadable cell must not take the whole month down.

A blank or junk value in a report used to reach float() bare and raise
"could not convert string to float: ''", which the screen showed as a file
error with no hint of which file, agent or column was at fault.
"""
import pytest

from modules.month_calc import _to_float, _to_int


@pytest.mark.parametrize("value", ["", "   ", None, "n/a", "—", float("nan"), "abc"])
def test_to_float_falls_back_on_anything_unreadable(value):
    assert _to_float(value) == 0.0


@pytest.mark.parametrize("value", ["", "   ", None, "n/a", "—", float("nan"), "abc"])
def test_to_int_falls_back_on_anything_unreadable(value):
    assert _to_int(value) == 0


def test_to_float_reads_real_values():
    assert _to_float(0.58) == pytest.approx(0.58)
    assert _to_float("0.58") == pytest.approx(0.58)
    assert _to_float(" 1,234.5 ") == pytest.approx(1234.5)


def test_to_int_reads_real_values():
    assert _to_int(733) == 733
    assert _to_int("733") == 733
    assert _to_int("1,263") == 1263
    assert _to_int(733.8) == 733


def test_to_float_reports_whether_the_value_was_usable():
    """compute_month needs to know, so it can flag the agent rather than pay on a guess."""
    assert _to_float("", with_status=True) == (0.0, False)
    assert _to_float("0.58", with_status=True) == (0.58, True)
