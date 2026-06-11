import json, os

_DIR = os.path.join(os.path.dirname(__file__), '..', 'config')
_AGENTS_PATH = os.path.join(_DIR, 'agents.json')
_SETTINGS_PATH = os.path.join(_DIR, 'settings.json')


def load_agents(path: str = _AGENTS_PATH) -> list:
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def save_agents(agents: list, path: str = _AGENTS_PATH) -> None:
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(agents, f, ensure_ascii=False, indent=2)


def load_settings(path: str = _SETTINGS_PATH) -> dict:
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def save_settings(settings: dict, path: str = _SETTINGS_PATH) -> None:
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)
