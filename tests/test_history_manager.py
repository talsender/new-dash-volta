# tests/test_history_manager.py
import json, tempfile, os, pytest
from modules.history_manager import save_month, load_history, get_month

def _snapshot():
    return {
        "month": "2026-06",
        "label": "יוני 2026",
        "center_rate": 1.02,
        "center_met_target": True,
        "manager_bonus": 2000,
        "total_billing": 45600,
        "agents": [
            {"name": "טום", "hours": 113.0, "meetings": 142,
             "meetings_per_hour": 1.257, "occupancy_pct": 0.36,
             "idle_pct": 0.005, "feedback_score": 8.52,
             "phoenix": 5, "bonus_total": 1380}
        ]
    }

def test_save_and_load():
    f = tempfile.NamedTemporaryFile(suffix='.json', delete=False)
    f.close()
    try:
        save_month(_snapshot(), f.name)
        history = load_history(f.name)
        assert len(history) == 1
        assert history[0]["month"] == "2026-06"
    finally:
        os.unlink(f.name)

def test_save_twice_appends():
    f = tempfile.NamedTemporaryFile(suffix='.json', delete=False)
    f.close()
    try:
        s1 = {**_snapshot(), "month": "2026-05", "label": "מאי 2026"}
        s2 = {**_snapshot(), "month": "2026-06", "label": "יוני 2026"}
        save_month(s1, f.name)
        save_month(s2, f.name)
        history = load_history(f.name)
        assert len(history) == 2
    finally:
        os.unlink(f.name)

def test_save_same_month_overwrites():
    f = tempfile.NamedTemporaryFile(suffix='.json', delete=False)
    f.close()
    try:
        s1 = {**_snapshot(), "center_rate": 0.9}
        s2 = {**_snapshot(), "center_rate": 1.1}
        save_month(s1, f.name)
        save_month(s2, f.name)
        history = load_history(f.name)
        assert len(history) == 1
        assert history[0]["center_rate"] == 1.1
    finally:
        os.unlink(f.name)

def test_get_month_returns_snapshot():
    f = tempfile.NamedTemporaryFile(suffix='.json', delete=False)
    f.close()
    try:
        save_month(_snapshot(), f.name)
        result = get_month("2026-06", f.name)
        assert result is not None
        assert result["label"] == "יוני 2026"
    finally:
        os.unlink(f.name)

def test_get_month_missing_returns_none():
    f = tempfile.NamedTemporaryFile(suffix='.json', delete=False)
    f.close()
    try:
        result = get_month("2026-01", f.name)
        assert result is None
    finally:
        os.unlink(f.name)
