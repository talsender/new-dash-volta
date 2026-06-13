# modules/history_manager.py
import json, os, base64
from datetime import datetime

_DEFAULT_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'history.json')
_REPO_FILE_PATH = "data/history.json"

# Session-state cache key — used instead of module-level _mem so the cache is
# guaranteed to be shared between save_month() and load_history() within the
# same user session, even across screen navigations on Streamlit Cloud.
_SS_CACHE_KEY = "kpi_history"


def _cache_get():
    try:
        import streamlit as st
        return st.session_state.get(_SS_CACHE_KEY)
    except Exception:
        return None


def _cache_set(data):
    try:
        import streamlit as st
        st.session_state[_SS_CACHE_KEY] = data
    except Exception:
        pass


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
    with open(path, encoding="utf-8") as f:
        content = f.read().strip()
    return json.loads(content) if content else []


def _use_cache(path: str) -> bool:
    """Only cache when using the production default path — not in tests."""
    return os.path.abspath(path) == os.path.abspath(_DEFAULT_PATH)


def load_history(path: str = _DEFAULT_PATH) -> list:
    if _use_cache(path):
        # Serve from session_state cache if available (avoids disk/network on every rerun)
        cached = _cache_get()
        if cached is not None:
            return list(cached)

        cfg = _github_cfg()
        if cfg:
            try:
                data, _ = _gh_read(*cfg)
                _cache_set(data)
                return list(data)
            except Exception:
                pass

        data = _load_local(path)
        _cache_set(data)
        return list(data)

    return _load_local(path)


def save_month(snapshot: dict, path: str = _DEFAULT_PATH) -> str:
    """Persist snapshot and return storage source: 'github' | 'local' | 'session'.

    Never raises — all failures fall back to 'session' (in-memory cache).
    """
    try:
        snapshot = dict(snapshot)
        snapshot.setdefault("saved_at", datetime.now().isoformat())

        use_cache = _use_cache(path)

        # Build the current list, falling back gracefully at every step
        if use_cache:
            cached = _cache_get()
            if cached is not None:
                base = list(cached)
            else:
                try:
                    base = _load_local(path)
                except Exception:
                    base = []
        else:
            try:
                base = _load_local(path)
            except Exception:
                base = []

        base = [h for h in base if h.get("month") != snapshot["month"]]
        base.append(snapshot)
        base.sort(key=lambda h: h.get("month", ""))

        if use_cache:
            # Write to session_state cache first — history page reads from here immediately
            _cache_set(base)

            cfg = _github_cfg()
            if cfg:
                try:
                    token, repo, branch = cfg
                    _, sha = _gh_read(token, repo, branch)
                    if _gh_write(token, repo, branch, base, sha):
                        return "github"
                except Exception:
                    pass

        # Local file write — non-fatal on Streamlit Cloud (read-only source dir)
        try:
            os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(base, f, ensure_ascii=False, indent=2)
            return "local"
        except Exception:
            return "session"

    except Exception:
        # Last-resort: try to at least update the cache so history isn't empty
        try:
            _cache_set([snapshot])
        except Exception:
            pass
        return "session"


def delete_month(month_key: str, path: str = _DEFAULT_PATH) -> str:
    """Remove a month entry from history. Never raises. Returns storage source."""
    try:
        use_cache = _use_cache(path)
        if use_cache:
            cached = _cache_get()
            base = list(cached) if cached is not None else _load_local(path)
        else:
            base = _load_local(path)

        base = [h for h in base if h.get("month") != month_key]

        if use_cache:
            _cache_set(base)
            cfg = _github_cfg()
            if cfg:
                try:
                    token, repo, branch = cfg
                    _, sha = _gh_read(token, repo, branch)
                    if _gh_write(token, repo, branch, base, sha):
                        return "github"
                except Exception:
                    pass

        try:
            os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(base, f, ensure_ascii=False, indent=2)
            return "local"
        except Exception:
            return "session"
    except Exception:
        return "session"


def get_month(month: str, path: str = _DEFAULT_PATH):
    return next((h for h in load_history(path) if h["month"] == month), None)
