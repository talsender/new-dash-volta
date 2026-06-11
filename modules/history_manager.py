# modules/history_manager.py
import json, os
from datetime import datetime

_DEFAULT_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'history.json')


def load_history(path: str = _DEFAULT_PATH) -> list:
    if not os.path.exists(path):
        return []
    with open(path, encoding='utf-8') as f:
        content = f.read().strip()
    if not content:
        return []
    return json.loads(content)


def save_month(snapshot: dict, path: str = _DEFAULT_PATH) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    history = load_history(path)
    history = [h for h in history if h.get("month") != snapshot["month"]]
    snapshot["saved_at"] = datetime.now().isoformat()
    history.append(snapshot)
    history.sort(key=lambda h: h["month"])
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def get_month(month: str, path: str = _DEFAULT_PATH):
    return next((h for h in load_history(path) if h["month"] == month), None)
