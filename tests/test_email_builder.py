# tests/test_email_builder.py
from modules.email_builder import (
    build_weekly_management_email,
    build_weekly_agent_email,
    build_monthly_client_email,
    build_monthly_agent_email,
)

def _kpi():
    return [{"name": "טום", "hours": 80.0, "meetings": 80, "meetings_per_hour": 1.0,
             "occupancy_pct": 0.35, "idle_pct": 0.01, "phoenix": 3}]

def test_weekly_mgmt_is_html_with_table():
    html = build_weekly_management_email(_kpi(), "שבוע 1 יוני 2026")
    assert '<table' in html and 'טום' in html

def test_weekly_agent_email_contains_name():
    html = build_weekly_agent_email(_kpi()[0], "טום", "שבוע 1 יוני 2026")
    assert 'טום' in html and '<table' in html

def test_monthly_client_shows_billing():
    html = build_monthly_client_email(
        {"total_hours": 80.0, "phoenix_count": 3, "phoenix_billing": 300}, "יוני 2026")
    assert '300' in html and '<table' in html

def test_monthly_agent_shows_total():
    bonus = {"meetings_bonus": 480, "occupancy_bonus": 300, "idle_bonus": 150,
             "feedback_bonus": 150, "phoenix_bonus": 150, "total": 1230}
    html = build_monthly_agent_email(_kpi()[0], bonus, "טום", "יוני 2026")
    assert '1230' in html and 'טום' in html
