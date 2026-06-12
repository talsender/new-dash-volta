# modules/history_manager.py
import json, os, base64
from datetime import datetime

_DEFAULT_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'history.json')
_REPO_FILE_PATH = "data/history.json"


def _github_cfg():
    try:
        import streamlit as st
        token  = st.secrets.get("GITHUB_TOKEN", "")
        repo   = st.secrets.get("GITHUB_REPO",  "")
        branch = st.secrets.get("GITHUB_BRANCH", "master")
        if token and repo:
            return token, repo, branch
    except Exception:
        pass
    return None


def _gh_read(token, repo, branch):
    import requests
    url  = f"https://api.github.com/repos/{repo}/contents/{_REPO_FILE_PATH}"
    hdrs = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
    r = requests.get(url, headers=hdrs, params={"ref": branch}, timeout=10)
    if r.status_code == 200:
        d = r.json()
        return json.loads(base64.b64decode(d["content"]).decode("utf-8")), d["sha"]
    return [], None


def _gh_write(token, repo, branch, history, sha):
    import requests
    url  = f"https://api.github.com/repos/{repo}/contents/{_REPO_FILE_PATH}"
    hdrs = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
    body = {
        "message": f"history: update {datetime.now().strftime('%Y-%m-%d')}",
        "content": base64.b64encode(
            json.dumps(history, ensure_ascii=False, indent=2).encode("utf-8")
        ).decode("ascii"),
        "branch": branch,
    }
    if sha:
        body["sha"] = sha
    r = requests.put(url, headers=hdrs, json=body, timeout=10)
    return r.status_code in (200, 201)


def _load_local(path: str) -> list:
    if not os.path.exists(path):
        return []
    with open(path, encoding='utf-8') as f:
        content = f.read().strip()
    return json.loads(content) if content else []


def load_history(path: str = _DEFAULT_PATH) -> list:
    cfg = _github_cfg()
    if cfg:
        try:
            history, _ = _gh_read(*cfg)
            return history
        except Exception:
            pass
    return _load_local(path)


def save_month(snapshot: dict, path: str = _DEFAULT_PATH) -> None:
    snapshot = dict(snapshot)
    snapshot.setdefault("saved_at", datetime.now().isoformat())

    cfg = _github_cfg()
    if cfg:
        try:
            token, repo, branch = cfg
            history, sha = _gh_read(token, repo, branch)
            history = [h for h in history if h.get("month") != snapshot["month"]]
            history.append(snapshot)
            history.sort(key=lambda h: h["month"])
            if _gh_write(token, repo, branch, history, sha):
                return
        except Exception:
            pass

    # local fallback
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    history = _load_local(path)
    history = [h for h in history if h.get("month") != snapshot["month"]]
    history.append(snapshot)
    history.sort(key=lambda h: h["month"])
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def get_month(month: str, path: str = _DEFAULT_PATH):
    return next((h for h in load_history(path) if h["month"] == month), None)
