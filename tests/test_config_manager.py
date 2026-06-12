import json, tempfile, os
from modules.config_manager import load_agents, save_agents, load_settings, save_settings

def test_load_agents():
    data = [{"id": "a1", "name": "טום", "employee_id": 123, "email": "", "active": True}]
    f = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8')
    json.dump(data, f, ensure_ascii=False)
    f.close()
    try:
        result = load_agents(f.name)
        assert result[0]["name"] == "טום"
    finally:
        os.unlink(f.name)

def test_save_and_reload_agents():
    agents = [{"id": "a1", "name": "אלינור", "employee_id": 456, "email": "", "active": True}]
    f = tempfile.NamedTemporaryFile(suffix='.json', delete=False)
    f.close()
    try:
        save_agents(agents, f.name)
        loaded = load_agents(f.name)
        assert loaded[0]["name"] == "אלינור"
    finally:
        os.unlink(f.name)

def test_load_settings_returns_dict():
    data = {"bonus_thresholds": {"meetings_per_hour_tier_a": 1.0}}
    f = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8')
    json.dump(data, f)
    f.close()
    try:
        result = load_settings(f.name)
        assert result["bonus_thresholds"]["meetings_per_hour_tier_a"] == 1.0
    finally:
        os.unlink(f.name)

def test_load_agents_missing_file_returns_empty():
    result = load_agents('/nonexistent/path/agents.json')
    assert result == []

def test_load_settings_missing_file_raises_with_message():
    import pytest
    with pytest.raises(FileNotFoundError, match="settings.json"):
        load_settings('/nonexistent/path/settings.json')
