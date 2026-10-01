# tests/test_excel_exporter.py
import tempfile, os
import pytest
import openpyxl
from modules.excel_exporter import (export_weekly_kpi, export_monthly_bonus,
                                    export_agent_bonus, export_history_summary)

def _kpi():
    return [{"name": "טום", "hours": 80.0, "meetings": 80, "meetings_per_hour": 1.0,
             "occupancy_pct": 0.35, "idle_pct": 0.01, "phoenix": 3,
             "answered_calls": 1066, "total_calls": 1240,
             "answer_rate": 1066 / 1240}]

def _bonus():
    return [{"name": "טום", "employee_id": 98804, "meetings_bonus": 480,
             "occupancy_bonus": 300, "idle_bonus": 150,
             "feedback_bonus": 150, "phoenix_bonus": 150, "total": 1230}]

def _billing():
    return {"hours_by_agent": {"טום": 80.0}, "total_hours": 80.0,
            "phoenix_count": 3, "phoenix_billing": 300}

def test_export_weekly_creates_sheet():
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
        path = f.name
    try:
        export_weekly_kpi(_kpi(), path)
        wb = openpyxl.load_workbook(path)
        assert 'KPI שבועי' in wb.sheetnames
    finally:
        os.unlink(path)

def test_export_weekly_has_agent_name():
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
        path = f.name
    try:
        export_weekly_kpi(_kpi(), path)
        wb = openpyxl.load_workbook(path)
        ws = wb['KPI שבועי']
        names = [ws.cell(r, 1).value for r in range(2, ws.max_row + 1)]
        assert 'טום' in names
    finally:
        os.unlink(path)

def test_export_monthly_has_three_sheets():
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
        path = f.name
    try:
        export_monthly_bonus(_bonus(), _billing(), "יוני 2026", path)
        wb = openpyxl.load_workbook(path)
        assert {'לתשלום', 'פירוט בונוסים', 'סיכום מוקד'}.issubset(set(wb.sheetnames))
    finally:
        os.unlink(path)


# ── Answer rate column ─────────────────────────────────────

def _headers(ws):
    """Header labels of a sheet, wherever the header row happens to be."""
    return [ws.cell(r, c).value
            for r in range(1, min(ws.max_row, 6) + 1)
            for c in range(1, ws.max_column + 1)]


def _col_of(ws, label):
    for r in range(1, min(ws.max_row, 6) + 1):
        for c in range(1, ws.max_column + 1):
            if ws.cell(r, c).value == label:
                return r, c
    raise AssertionError(f"header {label!r} not found")


def test_weekly_sheet_has_answer_rate_column():
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
        path = f.name
    try:
        export_weekly_kpi(_kpi(), path)
        ws = openpyxl.load_workbook(path)['KPI שבועי']
        hdr_row, col = _col_of(ws, '% מענה')
        assert ws.cell(hdr_row + 1, col).value == pytest.approx(1066 / 1240)
        assert ws.cell(hdr_row + 1, col).number_format == "0.0%"
    finally:
        os.unlink(path)


def test_weekly_summary_row_answer_rate_is_volume_weighted():
    two = _kpi() + [{**_kpi()[0], "name": "אלינור",
                     "answered_calls": 668, "total_calls": 940,
                     "answer_rate": 668 / 940}]
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
        path = f.name
    try:
        export_weekly_kpi(two, path)
        ws = openpyxl.load_workbook(path)['KPI שבועי']
        hdr_row, col = _col_of(ws, '% מענה')
        summary = ws.cell(hdr_row + 3, col).value
        assert summary == pytest.approx((1066 + 668) / (1240 + 940))
    finally:
        os.unlink(path)


def test_monthly_bonus_sheet_has_answer_rate_column():
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
        path = f.name
    try:
        export_monthly_bonus(_bonus(), _billing(), "יוני 2026", path,
                             kpi_data=_kpi())
        ws = openpyxl.load_workbook(path)['פירוט בונוסים']
        assert '% מענה' in _headers(ws)
    finally:
        os.unlink(path)


def test_agent_sheet_has_answered_calls_and_answer_rate_formula():
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
        path = f.name
    try:
        export_agent_bonus(_kpi()[0], _bonus()[0], "יוני 2026", path)
        ws = openpyxl.load_workbook(path)['בונוס אישי']
        labels = {ws.cell(r, 1).value: r for r in range(1, ws.max_row + 1)}
        assert 'שיחות שנענו' in labels
        assert 'אחוז מענה' in labels
        assert ws.cell(labels['שיחות שנענו'], 2).value == 1066
        rate = ws.cell(labels['אחוז מענה'], 2)
        assert str(rate.value).startswith("="), "answer rate must be a live Excel formula"
        assert rate.number_format == "0.0%"
    finally:
        os.unlink(path)


def test_history_summary_has_answer_rate_column():
    history = [{"label": "יוני 2026", "total_hours": 80.0,
                "total_meetings": 80, "center_rate": 1.0,
                "total_idle_calls": 12, "total_calls": 1240,
                "answer_rate": 1066 / 1240, "total_phoenix": 3}]
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
        path = f.name
    try:
        export_history_summary(history, path)
        ws = openpyxl.load_workbook(path)['סיכום חודשי']
        hdr_row, col = _col_of(ws, '% מענה')
        assert ws.cell(hdr_row + 1, col).value == pytest.approx(1066 / 1240)
    finally:
        os.unlink(path)


def _hist_row(label, calls, rate=None):
    row = {"label": label, "total_hours": 300.0, "total_meetings": 300,
           "center_rate": 1.0, "total_idle_calls": 70,
           "total_calls": calls, "total_phoenix": 4}
    if rate is not None:
        row["answer_rate"] = rate
    return row


def test_history_summary_legacy_month_shows_dash():
    """A month saved before the metric existed must render —, never 0.0%."""
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
        path = f.name
    try:
        export_history_summary([_hist_row("יוני 2026", 4000)], path)
        ws = openpyxl.load_workbook(path)['סיכום חודשי']
        hdr_row, col = _col_of(ws, '% מענה')
        assert ws.cell(hdr_row + 1, col).value == "—"
    finally:
        os.unlink(path)


def test_history_summary_total_ignores_months_without_answer_rate():
    """Legacy months must not dilute the total — only rated months count."""
    history = [_hist_row("אוגוסט 2026", 4830, 3869 / 4830),
               _hist_row("יוני 2026", 4000)]
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
        path = f.name
    try:
        export_history_summary(history, path)
        ws = openpyxl.load_workbook(path)['סיכום חודשי']
        hdr_row, col = _col_of(ws, '% מענה')
        assert ws.cell(hdr_row + 3, col).value == pytest.approx(3869 / 4830)
    finally:
        os.unlink(path)


# ── Work-days proration ────────────────────────────────

def test_monthly_bonus_sheet_has_role_days_column():
    kpi = [{**_kpi()[0], "role_days": 15, "role_factor": 0.5}]
    bonus = [{**_bonus()[0], "role_days": 15}]
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
        path = f.name
    try:
        export_monthly_bonus(bonus, _billing(), "ספטמבר 2026", path, kpi_data=kpi)
        ws = openpyxl.load_workbook(path)['פירוט בונוסים']
        hdr_row, col = _col_of(ws, "ימים בתפקיד")
        assert ws.cell(hdr_row + 1, col).value == 15
    finally:
        os.unlink(path)


def test_agent_sheet_has_role_days_row():
    kpi = {**_kpi()[0], "role_days": 7, "role_factor": 7 / 30}
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
        path = f.name
    try:
        export_agent_bonus(kpi, _bonus()[0], "ספטמבר 2026", path)
        ws = openpyxl.load_workbook(path)['בונוס אישי']
        labels = {ws.cell(r, 1).value: r for r in range(1, ws.max_row + 1)}
        assert "ימים בתפקיד" in labels
        assert ws.cell(labels["ימים בתפקיד"], 2).value == 7
    finally:
        os.unlink(path)


def test_agent_sheet_fixed_bonus_formulas_reference_the_role_days_cell():
    """Editing the days cell in Excel must move the three fixed bonuses with it."""
    kpi = {**_kpi()[0], "role_days": 7, "role_factor": 7 / 30}
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
        path = f.name
    try:
        export_agent_bonus(kpi, _bonus()[0], "ספטמבר 2026", path)
        ws = openpyxl.load_workbook(path)['בונוס אישי']
        labels = {ws.cell(r, 1).value: r for r in range(1, ws.max_row + 1)}
        wd_row = labels["ימים בתפקיד"]
        for metric in ("אחוז תעסוקה", "אחוז סרק", "ציון משוב"):
            formula = str(ws.cell(labels[metric], 4).value)
            assert f"B{wd_row}" in formula, f"{metric} bonus ignores the work-days cell"
            assert formula.startswith("=ROUND(")
    finally:
        os.unlink(path)


def test_agent_sheet_per_unit_bonus_formulas_are_not_prorated():
    """The commission, team bonus and phoenix must not reference the days cell."""
    kpi = {**_kpi()[0], "role_days": 7, "role_factor": 7 / 30}
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
        path = f.name
    try:
        export_agent_bonus(kpi, _bonus()[0], "ספטמבר 2026", path)
        ws = openpyxl.load_workbook(path)['בונוס אישי']
        labels = {ws.cell(r, 1).value: r for r in range(1, ws.max_row + 1)}
        wd_row = labels["ימים בתפקיד"]
        for metric in ("עמלת תיאומים", "בונוס ליעד צוותי", "עסקת פניקס"):
            formula = str(ws.cell(labels[metric], 4).value)
            assert f"B{wd_row}" not in formula, f"{metric} must not be prorated"
    finally:
        os.unlink(path)
