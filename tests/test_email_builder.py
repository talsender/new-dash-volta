# tests/test_email_builder.py
from modules.email_builder import (
    build_weekly_management_email,
    build_weekly_agent_email,
    build_monthly_client_email,
    build_monthly_agent_email,
)

def _kpi():
    return [{"name": "טום", "hours": 80.0, "meetings": 80, "meetings_per_hour": 1.0,
             "occupancy_pct": 0.35, "idle_pct": 0.01, "phoenix": 3,
             "calls_per_day": 58.4}]

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
    bonus = {"meetings_bonus": 480, "calls_bonus": 200, "idle_bonus": 150,
             "feedback_bonus": 150, "phoenix_bonus": 150, "total": 1130}
    html = build_monthly_agent_email(_kpi()[0], bonus, "טום", "יוני 2026")
    assert ('1,130' in html or '1130' in html) and 'טום' in html


def test_agent_name_with_html_chars_is_escaped():
    # Agent names come from user-editable JSON and must be escaped before HTML insertion
    kpi = [{"name": "<script>alert(1)</script>", "hours": 80.0, "meetings": 80,
             "meetings_per_hour": 1.0, "occupancy_pct": 0.35,
             "idle_pct": 0.01, "phoenix": 3}]
    html = build_weekly_management_email(kpi, "שבוע 1")
    assert '<script>' not in html, "Raw <script> tag must not appear in email HTML"
    assert '&lt;script&gt;' in html or 'alert' not in html


def test_agent_name_with_quote_does_not_break_html():
    kpi = [{"name": 'דוד "הגדול" כהן', "hours": 80.0, "meetings": 80,
             "meetings_per_hour": 1.0, "occupancy_pct": 0.35,
             "idle_pct": 0.01, "phoenix": 3}]
    html = build_weekly_management_email(kpi, "שבוע 1")
    # The name should appear escaped (as &quot; or &#34;) or safely as text
    assert 'דוד' in html


# ── one report for the client, one for the agents ─────────────────

_CALLS_WORDS = ["שיחות ליום", "שיחות/שעה", "בונוס שיחות", "יעד שיחות"]


def test_client_email_never_carries_the_calls_target():
    """The client is billed on occupancy and must not learn the agents' target."""
    html = build_monthly_client_email(
        {"total_hours": 80.0, "phoenix_count": 3, "phoenix_billing": 300}, "יוני 2026")
    for word in _CALLS_WORDS:
        assert word not in html, f"the client email leaks {word!r}"


def test_agent_email_reports_the_calls_bonus():
    bonus = {"meetings_bonus": 480, "calls_bonus": 200, "idle_bonus": 150,
             "feedback_bonus": 150, "phoenix_bonus": 150, "total": 1130}
    html = build_monthly_agent_email(_kpi()[0], bonus, "טום", "יוני 2026")
    assert "שיחות" in html
    assert "תעסוקה" not in html, "occupancy no longer pays the agent"


def test_weekly_agent_email_shows_calls_per_day():
    html = build_weekly_agent_email(_kpi()[0], "טום", "שבוע 1")
    assert "שיחות ליום" in html and "58.4" in html


def test_weekly_management_email_shows_calls_per_day():
    html = build_weekly_management_email(_kpi(), "שבוע 1")
    assert "שיחות ליום" in html
