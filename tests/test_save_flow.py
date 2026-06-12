# tests/test_save_flow.py
"""End-to-end tests for the save-to-history flow:
  save_month sets session cache → load_history reads it → build_snapshot has all fields.
"""
import pytest
from unittest.mock import MagicMock, patch


# ── helpers ────────────────────────────────────────────────────────────────

class _FakeSessionState:
    """Dict-backed session_state substitute with no MagicMock ambiguity."""
    def __init__(self, initial=None):
        self._d = dict(initial or {})

    def get(self, key, default=None):
        return self._d.get(key, default)

    def __getitem__(self, key):
        return self._d[key]

    def __setitem__(self, key, value):
        self._d[key] = value

    def __contains__(self, key):
        return key in self._d

    def __delitem__(self, key):
        del self._d[key]

    @property
    def data(self):
        return self._d


def _mock_streamlit(initial_cache=None):
    """Return (mock_st, fake_session_state).

    initial_cache: if provided, pre-populates 'kpi_history' so that
    _cache_get() returns it rather than falling through to _load_local().
    Pass [] to start with an empty (but non-None) cache.
    """
    from modules.history_manager import _SS_CACHE_KEY
    init = {}
    if initial_cache is not None:
        init[_SS_CACHE_KEY] = initial_cache

    ss = _FakeSessionState(init)

    mock_st = MagicMock()
    mock_st.session_state = ss
    mock_st.secrets = MagicMock()
    mock_st.secrets.get = lambda k, default="": default
    return mock_st, ss


def _full_snapshot():
    return {
        "month": "2026-06",
        "label": "יוני 2026",
        "center_rate": 1.12,
        "center_met_target": True,
        "manager_bonus": 2500,
        "total_billing": 50000,
        "total_meetings": 295,
        "total_hours": 230.5,
        "total_phoenix": 12,
        "avg_occupancy_pct": 0.42,
        "avg_idle_pct": 0.008,
        "total_agent_bonus": 3200,
        "agents": [{
            "name": "טום",
            "hours": 115.0,
            "meetings": 148,
            "meetings_per_hour": 1.287,
            "occupancy_pct": 0.42,
            "idle_pct": 0.008,
            "feedback_score": 8.5,
            "phoenix": 6,
            "bonus_total": 1600,
        }],
    }


# ── build_snapshot field coverage ─────────────────────────────────────────

def test_build_snapshot_required_fields():
    """build_snapshot must include all center-level and per-agent fields."""
    from modules.month_calc import build_snapshot

    res = {
        "kpi_data": [{
            "name": "טום", "hours": 115.0, "meetings": 148,
            "meetings_per_hour": 1.287, "occupancy_pct": 0.42,
            "idle_pct": 0.008, "feedback_score": 8.5, "phoenix": 6,
        }],
        "bonus_data": [{"name": "טום", "total": 1600}],
        "center_rate": 1.12,
        "center_meets": True,
        "manager_bonus": 2500,
        "billing": {
            "phoenix_billing": 50000,
            "total_hours": 115.0,
            "phoenix_count": 6,
        },
    }
    snap = build_snapshot(res, "יוני 2026")

    for field in [
        "month", "label", "center_rate", "center_met_target", "manager_bonus",
        "total_billing", "total_meetings", "total_hours", "total_phoenix",
        "avg_occupancy_pct", "avg_idle_pct", "total_agent_bonus", "agents",
    ]:
        assert field in snap, f"build_snapshot missing field: {field}"

    assert snap["month"] == "יוני 2026"
    assert snap["total_meetings"] == 148
    assert snap["total_phoenix"] == 6
    assert snap["avg_occupancy_pct"] == pytest.approx(0.42)
    assert snap["total_agent_bonus"] == 1600

    agent = snap["agents"][0]
    for field in ["name", "hours", "meetings", "meetings_per_hour",
                  "occupancy_pct", "idle_pct", "feedback_score", "phoenix", "bonus_total"]:
        assert field in agent, f"agent snapshot missing field: {field}"


def test_build_snapshot_averages_multiple_agents():
    """avg_occupancy_pct and avg_idle_pct must be averaged across all agents."""
    from modules.month_calc import build_snapshot

    res = {
        "kpi_data": [
            {"name": "א", "hours": 100, "meetings": 120, "meetings_per_hour": 1.2,
             "occupancy_pct": 0.40, "idle_pct": 0.010, "feedback_score": 8.0, "phoenix": 3},
            {"name": "ב", "hours": 100, "meetings": 110, "meetings_per_hour": 1.1,
             "occupancy_pct": 0.60, "idle_pct": 0.006, "feedback_score": 9.0, "phoenix": 5},
        ],
        "bonus_data": [{"name": "א", "total": 1000}, {"name": "ב", "total": 1200}],
        "center_rate": 1.15,
        "center_meets": True,
        "manager_bonus": 2000,
        "billing": {"phoenix_billing": 40000, "total_hours": 200.0, "phoenix_count": 8},
    }
    snap = build_snapshot(res, "יולי 2026")

    assert snap["total_meetings"] == 230
    assert snap["avg_occupancy_pct"] == pytest.approx(0.50)
    assert snap["avg_idle_pct"] == pytest.approx(0.008)
    assert snap["total_agent_bonus"] == 2200


# ── session cache tests ────────────────────────────────────────────────────

def test_save_month_sets_session_cache():
    """save_month with _DEFAULT_PATH must write the snapshot to session_state['kpi_history']."""
    from modules.history_manager import save_month, _DEFAULT_PATH, _SS_CACHE_KEY

    # Start with empty cache ([] not None) so _load_local is never called
    mock_st, ss = _mock_streamlit(initial_cache=[])

    with patch.dict('sys.modules', {'streamlit': mock_st}):
        save_month(_full_snapshot(), _DEFAULT_PATH)

    assert _SS_CACHE_KEY in ss.data, \
        f"session_state['{_SS_CACHE_KEY}'] was not set — save_month did not cache data"
    saved = ss.data[_SS_CACHE_KEY]
    assert len(saved) == 1
    assert saved[0]["month"] == "2026-06"
    assert saved[0]["total_meetings"] == 295


def test_save_month_never_raises():
    """save_month must return a string and never raise, even on I/O failure."""
    from modules.history_manager import save_month, _DEFAULT_PATH

    mock_st, _ = _mock_streamlit(initial_cache=[])

    with patch.dict('sys.modules', {'streamlit': mock_st}):
        result = save_month(_full_snapshot(), _DEFAULT_PATH)

    assert isinstance(result, str)
    assert result in ("github", "local", "session")


def test_load_history_reads_from_session_cache():
    """load_history must return data from session_state['kpi_history'] without hitting disk."""
    from modules.history_manager import load_history, _SS_CACHE_KEY

    mock_st, _ = _mock_streamlit(initial_cache=[_full_snapshot()])

    with patch.dict('sys.modules', {'streamlit': mock_st}):
        history = load_history()

    assert len(history) == 1
    assert history[0]["month"] == "2026-06"
    assert history[0]["total_meetings"] == 295
    assert history[0]["center_rate"] == pytest.approx(1.12)


def test_save_then_load_session_roundtrip():
    """Full roundtrip: save_month populates cache, then load_history returns same data."""
    from modules.history_manager import save_month, load_history, _DEFAULT_PATH

    mock_st, _ = _mock_streamlit(initial_cache=[])

    with patch.dict('sys.modules', {'streamlit': mock_st}):
        src = save_month(_full_snapshot(), _DEFAULT_PATH)
        history = load_history(_DEFAULT_PATH)

    assert src in ("github", "local", "session")
    assert len(history) == 1
    assert history[0]["month"] == "2026-06"
    assert history[0]["total_meetings"] == 295
    assert history[0]["total_agent_bonus"] == 3200
    assert history[0]["avg_occupancy_pct"] == pytest.approx(0.42)


def test_save_two_months_both_visible_in_load():
    """Saving two different months must make both visible in load_history."""
    from modules.history_manager import save_month, load_history, _DEFAULT_PATH

    mock_st, _ = _mock_streamlit(initial_cache=[])

    snap_may = {**_full_snapshot(), "month": "2026-05", "label": "מאי 2026", "total_meetings": 280}
    snap_jun = _full_snapshot()

    with patch.dict('sys.modules', {'streamlit': mock_st}):
        save_month(snap_may, _DEFAULT_PATH)
        save_month(snap_jun, _DEFAULT_PATH)
        history = load_history(_DEFAULT_PATH)

    assert len(history) == 2
    months = [h["month"] for h in history]
    assert "2026-05" in months
    assert "2026-06" in months


def test_save_same_month_overwrites_in_cache():
    """Saving the same month twice must overwrite, not duplicate, in the cache."""
    from modules.history_manager import save_month, load_history, _DEFAULT_PATH

    # Empty cache (not None) ensures no disk read on first save
    mock_st, _ = _mock_streamlit(initial_cache=[])

    snap_v1 = {**_full_snapshot(), "total_meetings": 280}
    snap_v2 = {**_full_snapshot(), "total_meetings": 295}

    with patch.dict('sys.modules', {'streamlit': mock_st}):
        save_month(snap_v1, _DEFAULT_PATH)
        save_month(snap_v2, _DEFAULT_PATH)
        history = load_history(_DEFAULT_PATH)

    assert len(history) == 1, f"expected 1 entry but got {len(history)}"
    assert history[0]["total_meetings"] == 295


# ── nav_goto key test ──────────────────────────────────────────────────────

def test_do_save_and_navigate_sets_nav_goto():
    """_do_save_and_navigate must set session_state['nav_goto'] before calling st.rerun()."""
    mock_st, ss = _mock_streamlit(initial_cache=[])

    class _FakeRerun(BaseException):
        pass

    mock_st.rerun = MagicMock(side_effect=_FakeRerun)
    mock_st.toast = MagicMock()

    with patch.dict('sys.modules', {'streamlit': mock_st}):
        with patch('modules.history_manager.save_month', return_value='session'):
            import importlib, screens.monthly_bonus
            importlib.reload(screens.monthly_bonus)
            try:
                screens.monthly_bonus._do_save_and_navigate(
                    {
                        "kpi_data": [], "bonus_data": [],
                        "center_rate": 1.0, "center_meets": True,
                        "manager_bonus": 0,
                        "billing": {"phoenix_billing": 0, "total_hours": 0, "phoenix_count": 0},
                    },
                    "יוני 2026",
                )
            except _FakeRerun:
                pass

    assert ss.data.get("nav_goto") == "📈 היסטוריה", \
        f"nav_goto not set correctly — got: {ss.data.get('nav_goto')}"
