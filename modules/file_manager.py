# modules/file_manager.py
"""Storage + management for saved monthly bonus XLSX files.

Each call to save_export_file() writes a NEW timestamped .xlsx under
data/exports/ — months are never overwritten, so every save is kept.
"""
import os, re
from datetime import datetime

_EXPORTS_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'exports')


def _safe(text: str) -> str:
    """Make a string safe for a filename (keep Hebrew, drop separators)."""
    text = (text or "").strip()
    text = re.sub(r'[\\/:*?"<>|]+', '', text)
    text = re.sub(r'\s+', '_', text)
    return text or "month"


def exports_dir(path: str = _EXPORTS_DIR) -> str:
    os.makedirs(os.path.abspath(path), exist_ok=True)
    return os.path.abspath(path)


def save_export_file(month_label: str, data: bytes,
                     path: str = _EXPORTS_DIR) -> str:
    """Write `data` as a new XLSX file for `month_label`. Returns the file path."""
    d = exports_dir(path)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"bonuses_{_safe(month_label)}_{stamp}.xlsx"
    full = os.path.join(d, filename)
    with open(full, 'wb') as f:
        f.write(data)
    return full


def list_export_files(path: str = _EXPORTS_DIR) -> list:
    """Return saved files, newest first, with metadata."""
    d = exports_dir(path)
    files = []
    for name in os.listdir(d):
        if not name.lower().endswith('.xlsx'):
            continue
        full = os.path.join(d, name)
        stat = os.stat(full)
        files.append({
            "name": name,
            "path": full,
            "size_kb": round(stat.st_size / 1024, 1),
            "modified": datetime.fromtimestamp(stat.st_mtime),
        })
    files.sort(key=lambda f: f["modified"], reverse=True)
    return files


def read_export_file(name: str, path: str = _EXPORTS_DIR) -> bytes:
    full = os.path.join(exports_dir(path), os.path.basename(name))
    with open(full, 'rb') as f:
        return f.read()


def delete_export_file(name: str, path: str = _EXPORTS_DIR) -> bool:
    """Delete a saved file by name. Returns True if a file was removed."""
    full = os.path.join(exports_dir(path), os.path.basename(name))
    if os.path.exists(full):
        os.remove(full)
        return True
    return False
