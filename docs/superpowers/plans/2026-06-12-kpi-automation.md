# KPI Automation System — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a browser-based Streamlit app that automates weekly KPI reports and monthly bonus calculations for a meeting-coordination call center (Volta Solar client).

**Architecture:** Single Streamlit app with 6 screens. Business logic lives in pure Python modules (testable with pytest). Screens call modules and handle file upload / manual input / email approval flow. Config (agents, thresholds) stored in JSON files on disk. Monthly snapshots stored in `data/history.json` for trend analysis.

**Tech Stack:** Python 3.12, Streamlit 1.58, pandas 3.0, openpyxl 3.1, lxml 6.1, pytest 9.0, smtplib (stdlib). Deployed to Streamlit Cloud (free, browser-only, zero local install).

---

## File Structure

```
c:\Users\Sinaymer\KPIs Volta\
├── app.py
├── requirements.txt
├── config/
│   ├── agents.json
│   └── settings.json
├── modules/
│   ├── __init__.py
│   ├── config_manager.py
│   ├── data_loader.py
│   ├── calculator.py
│   ├── email_builder.py
│   ├── email_sender.py
│   └── excel_exporter.py
├── screens/
│   ├── __init__.py
│   ├── dashboard.py
│   ├── weekly_kpi.py
│   ├── monthly_bonus.py
│   ├── agent_management.py
│   ├── settings_screen.py
│   └── history.py
├── data/
│   └── history.json          ← created at runtime
├── tests/
│   ├── __init__.py
│   ├── test_data_loader.py
│   ├── test_calculator.py
│   ├── test_config_manager.py
│   ├── test_email_builder.py
│   ├── test_excel_exporter.py
│   └── test_history_manager.py
└── .streamlit/
    └── secrets.toml   ← NOT committed to git
```

---

## Task 1: Project Scaffold

**Files:**
- Create: `requirements.txt`
- Create: `config/agents.json`
- Create: `config/settings.json`
- Create: `modules/__init__.py`, `screens/__init__.py`, `tests/__init__.py`
- Create: `.streamlit/secrets.toml` (template)
- Create: `.gitignore`

- [ ] **Step 1: Create directories**

```powershell
mkdir config, modules, screens, tests, .streamlit
```

- [ ] **Step 2: Create requirements.txt**

```
streamlit>=1.35
pandas>=2.0
openpyxl>=3.1
lxml>=5.0
pytest>=9.0
```

- [ ] **Step 3: Create config/agents.json**

```json
[
  {"id": "david_ziv",      "name": "דיוד זיו",    "employee_id": 96186, "email": "", "active": true},
  {"id": "elinor",         "name": "אלינור",       "employee_id": 98752, "email": "", "active": true},
  {"id": "tom_sorski",     "name": "טום סורסקי",   "employee_id": 98804, "email": "", "active": true},
  {"id": "perry_yavdayev", "name": "פרי יבדייב",   "employee_id": 99133, "email": "", "active": true}
]
```

- [ ] **Step 4: Create config/settings.json**

```json
{
  "bonus_thresholds": {
    "meetings_per_hour_tier_a": 1.0,
    "meetings_per_hour_tier_a_rate": 5,
    "meetings_per_hour_tier_b_rate": 4,
    "center_target_bonus_per_meeting": 1,
    "occupancy_tier_a_pct": 35,
    "occupancy_tier_a_bonus": 300,
    "occupancy_tier_b_pct": 30,
    "occupancy_tier_b_bonus": 200,
    "idle_tier_a_pct": 2,
    "idle_tier_a_bonus": 150,
    "idle_tier_b_pct": 3,
    "idle_tier_b_bonus": 100,
    "feedback_tier_a_score": 8.5,
    "feedback_tier_a_bonus": 150,
    "feedback_tier_b_score": 8.0,
    "feedback_tier_b_bonus": 100,
    "phoenix_employee_rate": 50,
    "phoenix_client_rate": 100,
    "manager_bonus_a_rate": 1.0,
    "manager_bonus_a": 2000,
    "manager_bonus_b_rate": 0.8,
    "manager_bonus_b": 1600,
    "manager_bonus_c": 1200
  },
  "smtp": {
    "host": "",
    "port": 587,
    "username": "",
    "from_email": ""
  },
  "recipients": {
    "management": [],
    "client": []
  }
}
```

- [ ] **Step 5: Create .streamlit/secrets.toml (template — do not commit real values)**

```toml
# Fill in real value in Streamlit Cloud → App Settings → Secrets
SMTP_PASSWORD = ""
```

- [ ] **Step 6: Create .gitignore**

```
.streamlit/secrets.toml
__pycache__/
*.pyc
.pytest_cache/
```

- [ ] **Step 7: Create empty __init__.py files**

Create empty files: `modules/__init__.py`, `screens/__init__.py`, `tests/__init__.py`

- [ ] **Step 8: Verify structure**

```bash
python -c "import os; print([f for f in os.listdir('.')])"
```
Expected: config, modules, screens, tests, .streamlit, requirements.txt, .gitignore visible.

- [ ] **Step 9: Commit**

```bash
git init
git add requirements.txt config/ modules/__init__.py screens/__init__.py tests/__init__.py .gitignore .streamlit/
git commit -m "feat: project scaffold for KPI automation app"
```

---

## Task 2: Config Manager

**Files:**
- Create: `modules/config_manager.py`
- Create: `tests/test_config_manager.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_config_manager.py
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
```

- [ ] **Step 2: Run to verify failure**

```bash
python -m pytest tests/test_config_manager.py -v
```
Expected: ImportError (module not found)

- [ ] **Step 3: Implement config_manager.py**

```python
# modules/config_manager.py
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
```

- [ ] **Step 4: Run tests**

```bash
python -m pytest tests/test_config_manager.py -v
```
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add modules/config_manager.py tests/test_config_manager.py
git commit -m "feat: config manager for agents and settings JSON"
```

---

## Task 3: Data Loader — Attendance File

The file (נוכחות לפי מחלקה.xlsx) has a sheet "וולטה סולאר" with one row per employee per day. Key columns: `מספר עובד`, `סה"כ כללי`.

**Files:**
- Create: `modules/data_loader.py`
- Create: `tests/test_data_loader.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_data_loader.py
import pytest, pandas as pd, tempfile, os
from modules.data_loader import parse_attendance

def _make_attendance(rows):
    df = pd.DataFrame(rows)
    f = tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False)
    with pd.ExcelWriter(f.name, engine='openpyxl') as w:
        df.to_excel(w, sheet_name='וולטה סולאר', index=False)
    return f.name

def test_parse_attendance_returns_dataframe():
    path = _make_attendance([
        {'תאריך': '01/06/2026', 'מספר עובד': 96186, 'שם עובד': 'דיוד זיו', 'סה"כ כללי': 8.0}
    ])
    try:
        df = parse_attendance(path)
        assert isinstance(df, pd.DataFrame)
        assert 'מספר עובד' in df.columns
        assert len(df) == 1
    finally:
        os.unlink(path)

def test_parse_attendance_multiple_employees():
    path = _make_attendance([
        {'תאריך': '01/06/2026', 'מספר עובד': 96186, 'שם עובד': 'דיוד', 'סה"כ כללי': 8.0},
        {'תאריך': '01/06/2026', 'מספר עובד': 98752, 'שם עובד': 'אלינור', 'סה"כ כללי': 7.0},
    ])
    try:
        df = parse_attendance(path)
        assert len(df) == 2
        assert set(df['מספר עובד'].tolist()) == {96186, 98752}
    finally:
        os.unlink(path)
```

- [ ] **Step 2: Run to verify failure**

```bash
python -m pytest tests/test_data_loader.py -v
```
Expected: ImportError

- [ ] **Step 3: Implement parse_attendance**

```python
# modules/data_loader.py
import pandas as pd


def parse_attendance(filepath: str) -> pd.DataFrame:
    df = pd.read_excel(filepath, sheet_name='וולטה סולאר', engine='openpyxl')
    df['מספר עובד'] = pd.to_numeric(df['מספר עובד'], errors='coerce').astype('Int64')
    df['סה"כ כללי'] = pd.to_numeric(df['סה"כ כללי'], errors='coerce').fillna(0.0)
    return df
```

- [ ] **Step 4: Run tests**

```bash
python -m pytest tests/test_data_loader.py -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add modules/data_loader.py tests/test_data_loader.py
git commit -m "feat: attendance file parser"
```

---

## Task 4: Data Loader — Voicenter File

The Voicenter .xls is a UTF-16 HTML table disguised as XLS. Must use `pd.read_html(filepath, encoding='utf-16')`.

Key columns: `משתמש`, `נענו`, `אחוז תעסוקה נטו`.

**Files:**
- Modify: `modules/data_loader.py`
- Modify: `tests/test_data_loader.py`

- [ ] **Step 1: Write failing tests**

Add to `tests/test_data_loader.py`:

```python
from modules.data_loader import parse_voicenter

def _make_voicenter(rows):
    headers = ['משתמש', 'סה"כ שיחות', 'נענו', 'שיחות שלא נענו', 'אחוז תעסוקה נטו']
    html = '<table><tr>' + ''.join(f'<th>{h}</th>' for h in headers) + '</tr>'
    for r in rows:
        html += '<tr>' + ''.join(f'<td>{r.get(h,"")}</td>' for h in headers) + '</tr>'
    html += '</table>'
    f = tempfile.NamedTemporaryFile(suffix='.xls', delete=False, mode='w', encoding='utf-16')
    f.write(html); f.close()
    return f.name

def test_parse_voicenter_returns_dataframe():
    path = _make_voicenter([
        {'משתמש': 'טום', 'סה"כ שיחות': 200, 'נענו': 190,
         'שיחות שלא נענו': 10, 'אחוז תעסוקה נטו': '35%'}
    ])
    try:
        df = parse_voicenter(path)
        assert isinstance(df, pd.DataFrame)
        assert 'משתמש' in df.columns
        assert len(df) == 1
    finally:
        os.unlink(path)

def test_parse_voicenter_occupancy_as_float():
    path = _make_voicenter([
        {'משתמש': 'טום', 'סה"כ שיחות': 200, 'נענו': 190,
         'שיחות שלא נענו': 10, 'אחוז תעסוקה נטו': '35%'}
    ])
    try:
        df = parse_voicenter(path)
        assert df.iloc[0]['אחוז תעסוקה נטו'] == pytest.approx(0.35)
    finally:
        os.unlink(path)
```

- [ ] **Step 2: Run to verify failure**

```bash
python -m pytest tests/test_data_loader.py::test_parse_voicenter_returns_dataframe -v
```
Expected: FAIL (function not defined)

- [ ] **Step 3: Add parse_voicenter to data_loader.py**

```python
def parse_voicenter(filepath: str) -> pd.DataFrame:
    tables = pd.read_html(filepath, encoding='utf-16')
    df = tables[0]
    # Drop summary rows (totals have no user name or are labeled סה"כ)
    df = df[df['משתמש'].notna() & ~df['משתמש'].astype(str).str.startswith('סה"כ')]
    occ = 'אחוז תעסוקה נטו'
    if df[occ].dtype == object:
        df[occ] = (df[occ].str.replace('%', '', regex=False)
                          .str.strip()
                          .pipe(pd.to_numeric, errors='coerce') / 100)
    df['נענו'] = pd.to_numeric(df['נענו'], errors='coerce').fillna(0).astype(int)
    return df.reset_index(drop=True)
```

- [ ] **Step 4: Run tests**

```bash
python -m pytest tests/test_data_loader.py -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add modules/data_loader.py tests/test_data_loader.py
git commit -m "feat: Voicenter HTML-disguised-XLS parser"
```

---

## Task 5: Data Loader — Feedback File

Each agent has a separate sheet. The row with "ציון משוב" in column A holds the score in column B.

**Files:**
- Modify: `modules/data_loader.py`
- Modify: `tests/test_data_loader.py`

- [ ] **Step 1: Write failing tests**

```python
from modules.data_loader import parse_feedback

def _make_feedback(agent_scores: dict):
    f = tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False)
    with pd.ExcelWriter(f.name, engine='openpyxl') as w:
        for name, score in agent_scores.items():
            pd.DataFrame([['ציון משוב', score], ['פרמטר 2', 7.0]]).to_excel(
                w, sheet_name=name, index=False, header=False)
    return f.name

def test_parse_feedback_returns_scores():
    path = _make_feedback({"טום סורסקי": 8.52, "אלינור": 8.5})
    try:
        result = parse_feedback(path)
        assert result["טום סורסקי"] == pytest.approx(8.52)
        assert result["אלינור"] == pytest.approx(8.5)
    finally:
        os.unlink(path)

def test_parse_feedback_missing_agent_is_absent():
    path = _make_feedback({"טום סורסקי": 8.52})
    try:
        result = parse_feedback(path)
        assert result.get("אלינור") is None
    finally:
        os.unlink(path)
```

- [ ] **Step 2: Run to verify failure**

```bash
python -m pytest tests/test_data_loader.py::test_parse_feedback_returns_scores -v
```

- [ ] **Step 3: Add parse_feedback to data_loader.py**

```python
def parse_feedback(filepath: str) -> dict:
    xl = pd.ExcelFile(filepath, engine='openpyxl')
    scores = {}
    for sheet in xl.sheet_names:
        df = xl.parse(sheet, header=None)
        mask = df.iloc[:, 0].astype(str).str.contains('ציון משוב', na=False)
        if mask.any():
            score = pd.to_numeric(df.iloc[mask.idxmax(), 1], errors='coerce')
            if not pd.isna(score):
                scores[sheet] = float(score)
    return scores
```

- [ ] **Step 4: Run all data loader tests**

```bash
python -m pytest tests/test_data_loader.py -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add modules/data_loader.py tests/test_data_loader.py
git commit -m "feat: feedback file parser"
```

---

## Task 6: Calculator — Work Hours & Rates

**Files:**
- Create: `modules/calculator.py`
- Create: `tests/test_calculator.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_calculator.py
import pytest, pandas as pd
from modules.calculator import (
    calculate_work_hours,
    calculate_meetings_per_hour,
    calculate_idle_pct,
    calculate_center_rate,
)

def _df(rows):
    return pd.DataFrame(rows)

# ── Work hours ────────────────────────────────────────────
def test_work_hours_single_day():
    df = _df([{'מספר עובד': 96186, 'סה"כ כללי': 8.0}])
    assert calculate_work_hours(df, 96186) == pytest.approx(7.0)

def test_work_hours_multiple_days():
    df = _df([
        {'מספר עובד': 96186, 'סה"כ כללי': 8.0},
        {'מספר עובד': 96186, 'סה"כ כללי': 7.0},
        {'מספר עובד': 96186, 'סה"כ כללי': 6.0},
    ])
    assert calculate_work_hours(df, 96186) == pytest.approx(18.0)  # (8+7+6) - 3

def test_work_hours_ignores_absent_days():
    # Zero-hour rows are absent days — no 1h deduction
    df = _df([
        {'מספר עובד': 96186, 'סה"כ כללי': 0.0},
        {'מספר עובד': 96186, 'סה"כ כללי': 8.0},
    ])
    assert calculate_work_hours(df, 96186) == pytest.approx(7.0)  # 8 - 1

def test_work_hours_unknown_employee():
    df = _df([{'מספר עובד': 96186, 'סה"כ כללי': 8.0}])
    assert calculate_work_hours(df, 99999) == pytest.approx(0.0)

# ── Meetings per hour ─────────────────────────────────────
def test_meetings_per_hour_normal():
    assert calculate_meetings_per_hour(80, 70.0) == pytest.approx(80 / 70, rel=0.01)

def test_meetings_per_hour_zero_hours():
    assert calculate_meetings_per_hour(10, 0.0) == 0.0

# ── Idle % ────────────────────────────────────────────────
def test_idle_pct_normal():
    assert calculate_idle_pct(2, 190) == pytest.approx(2 / 190, rel=0.01)

def test_idle_pct_zero_answered():
    assert calculate_idle_pct(0, 0) == 0.0

# ── Center rate ───────────────────────────────────────────
def test_center_rate_combines_agents():
    agents = [{"hours": 80.0, "meetings": 80}, {"hours": 90.0, "meetings": 90}]
    assert calculate_center_rate(agents) == pytest.approx(1.0)

def test_center_rate_excludes_zero_hour_agents():
    agents = [{"hours": 0.0, "meetings": 10}, {"hours": 100.0, "meetings": 80}]
    assert calculate_center_rate(agents) == pytest.approx(0.8)
```

- [ ] **Step 2: Run to verify failure**

```bash
python -m pytest tests/test_calculator.py -v
```
Expected: ImportError

- [ ] **Step 3: Implement calculator.py**

```python
# modules/calculator.py
import pandas as pd


def calculate_work_hours(attendance_df: pd.DataFrame, employee_id: int) -> float:
    emp = attendance_df[attendance_df['מספר עובד'] == employee_id]
    working = emp[emp['סה"כ כללי'] > 0]
    return max(0.0, float(working['סה"כ כללי'].sum()) - len(working))


def calculate_meetings_per_hour(meetings: int, hours: float) -> float:
    return 0.0 if hours == 0 else meetings / hours


def calculate_idle_pct(idle_calls: int, answered_calls: int) -> float:
    return 0.0 if answered_calls == 0 else idle_calls / answered_calls


def calculate_center_rate(agents: list) -> float:
    active = [a for a in agents if a["hours"] > 0]
    if not active:
        return 0.0
    return sum(a["meetings"] for a in active) / sum(a["hours"] for a in active)
```

- [ ] **Step 4: Run tests**

```bash
python -m pytest tests/test_calculator.py -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add modules/calculator.py tests/test_calculator.py
git commit -m "feat: work hours, meetings/hr, idle%, center rate calculators"
```

---

## Task 7: Calculator — Bonus Components

**Files:**
- Modify: `modules/calculator.py`
- Modify: `tests/test_calculator.py`

- [ ] **Step 1: Write failing tests**

Add to `tests/test_calculator.py`:

```python
from modules.calculator import (
    calculate_meetings_bonus,
    calculate_occupancy_bonus,
    calculate_idle_bonus,
    calculate_feedback_bonus,
)

def test_meetings_bonus_above_target_center_meets():
    assert calculate_meetings_bonus(80, 1.1, True) == 480   # (5+1)×80

def test_meetings_bonus_above_target_center_misses():
    assert calculate_meetings_bonus(80, 1.1, False) == 400  # 5×80

def test_meetings_bonus_below_target_center_meets():
    assert calculate_meetings_bonus(80, 0.9, True) == 400   # (4+1)×80

def test_meetings_bonus_below_target_center_misses():
    assert calculate_meetings_bonus(80, 0.9, False) == 320  # 4×80

def test_occupancy_tier_a():
    assert calculate_occupancy_bonus(0.36) == 300
def test_occupancy_tier_a_boundary():
    assert calculate_occupancy_bonus(0.35) == 300
def test_occupancy_tier_b():
    assert calculate_occupancy_bonus(0.31) == 200
def test_occupancy_tier_b_boundary():
    assert calculate_occupancy_bonus(0.30) == 200
def test_occupancy_none():
    assert calculate_occupancy_bonus(0.29) == 0

def test_idle_tier_a():
    assert calculate_idle_bonus(0.01) == 150
def test_idle_tier_a_boundary():
    assert calculate_idle_bonus(0.02) == 150
def test_idle_tier_b():
    assert calculate_idle_bonus(0.025) == 100
def test_idle_tier_b_boundary():
    assert calculate_idle_bonus(0.03) == 100
def test_idle_none():
    assert calculate_idle_bonus(0.04) == 0

def test_feedback_tier_a():
    assert calculate_feedback_bonus(8.52) == 150
def test_feedback_tier_a_boundary():
    assert calculate_feedback_bonus(8.5) == 150
def test_feedback_tier_b():
    assert calculate_feedback_bonus(8.1) == 100
def test_feedback_tier_b_boundary():
    assert calculate_feedback_bonus(8.0) == 100
def test_feedback_none_score():
    assert calculate_feedback_bonus(None) == 0
def test_feedback_below():
    assert calculate_feedback_bonus(7.9) == 0
```

- [ ] **Step 2: Run to verify failures**

```bash
python -m pytest tests/test_calculator.py -k "bonus" -v
```

- [ ] **Step 3: Add bonus functions to calculator.py**

```python
def calculate_meetings_bonus(meetings: int, individual_rate: float, center_meets: bool) -> float:
    base = 5 if individual_rate >= 1.0 else 4
    extra = 1 if center_meets else 0
    return meetings * (base + extra)


def calculate_occupancy_bonus(occupancy_pct: float) -> float:
    if occupancy_pct >= 0.35:
        return 300
    if occupancy_pct >= 0.30:
        return 200
    return 0


def calculate_idle_bonus(idle_pct: float) -> float:
    if idle_pct <= 0.02:
        return 150
    if idle_pct <= 0.03:
        return 100
    return 0


def calculate_feedback_bonus(score) -> float:
    if score is None:
        return 0
    if score >= 8.5:
        return 150
    if score >= 8.0:
        return 100
    return 0
```

- [ ] **Step 4: Run all calculator tests**

```bash
python -m pytest tests/test_calculator.py -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add modules/calculator.py tests/test_calculator.py
git commit -m "feat: individual bonus component calculators with full boundary coverage"
```

---

## Task 8: Calculator — Full Bonus Report

Combines all components into complete bonus dict per agent plus manager bonus.

**Files:**
- Modify: `modules/calculator.py`
- Modify: `tests/test_calculator.py`

- [ ] **Step 1: Write failing tests**

Add to `tests/test_calculator.py`:

```python
from modules.calculator import calculate_agent_bonus, calculate_manager_bonus

def _settings():
    return {"bonus_thresholds": {
        "phoenix_employee_rate": 50, "phoenix_client_rate": 100,
        "manager_bonus_a_rate": 1.0, "manager_bonus_a": 2000,
        "manager_bonus_b_rate": 0.8, "manager_bonus_b": 1600,
        "manager_bonus_c": 1200,
    }}

def test_calculate_agent_bonus_full():
    kpi = {"meetings": 80, "individual_rate": 1.1, "occupancy_pct": 0.36,
           "idle_pct": 0.015, "feedback_score": 8.52, "phoenix": 3}
    result = calculate_agent_bonus(kpi, center_meets=True, settings=_settings())
    assert result["meetings_bonus"] == 480    # (5+1)×80
    assert result["occupancy_bonus"] == 300
    assert result["idle_bonus"] == 150
    assert result["feedback_bonus"] == 150
    assert result["phoenix_bonus"] == 150    # 3×50
    assert result["total"] == 1230

def test_calculate_manager_bonus_tier_a():
    assert calculate_manager_bonus(1.05, _settings()) == 2000

def test_calculate_manager_bonus_tier_b():
    assert calculate_manager_bonus(0.85, _settings()) == 1600

def test_calculate_manager_bonus_tier_c():
    assert calculate_manager_bonus(0.75, _settings()) == 1200
```

- [ ] **Step 2: Run to verify failures**

```bash
python -m pytest tests/test_calculator.py::test_calculate_agent_bonus_full tests/test_calculator.py::test_calculate_manager_bonus_tier_a -v
```

- [ ] **Step 3: Add to calculator.py**

```python
def calculate_agent_bonus(kpi: dict, center_meets: bool, settings: dict) -> dict:
    t = settings["bonus_thresholds"]
    m = calculate_meetings_bonus(kpi["meetings"], kpi["individual_rate"], center_meets)
    o = calculate_occupancy_bonus(kpi["occupancy_pct"])
    i = calculate_idle_bonus(kpi["idle_pct"])
    fb = calculate_feedback_bonus(kpi.get("feedback_score"))
    ph = kpi["phoenix"] * t["phoenix_employee_rate"]
    return {"meetings_bonus": m, "occupancy_bonus": o, "idle_bonus": i,
            "feedback_bonus": fb, "phoenix_bonus": ph, "total": m + o + i + fb + ph}


def calculate_manager_bonus(center_rate: float, settings: dict) -> float:
    t = settings["bonus_thresholds"]
    if center_rate >= t["manager_bonus_a_rate"]:
        return t["manager_bonus_a"]
    if center_rate >= t["manager_bonus_b_rate"]:
        return t["manager_bonus_b"]
    return t["manager_bonus_c"]
```

- [ ] **Step 4: Run all tests**

```bash
python -m pytest tests/ -v
```
Expected: PASS (all)

- [ ] **Step 5: Commit**

```bash
git add modules/calculator.py tests/test_calculator.py
git commit -m "feat: full agent bonus and manager bonus calculators"
```

---

## Task 9: Excel Exporter

**Files:**
- Create: `modules/excel_exporter.py`
- Create: `tests/test_excel_exporter.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_excel_exporter.py
import tempfile, os
import openpyxl
from modules.excel_exporter import export_weekly_kpi, export_monthly_bonus

def _kpi():
    return [{"name": "טום", "hours": 80.0, "meetings": 80, "meetings_per_hour": 1.0,
             "occupancy_pct": 0.35, "idle_pct": 0.01, "phoenix": 3}]

def _bonus():
    return [{"name": "טום", "employee_id": 98804, "meetings_bonus": 480,
             "occupancy_bonus": 300, "idle_bonus": 150,
             "feedback_bonus": 150, "phoenix_bonus": 150, "total": 1230}]

def _billing():
    return {"hours_by_agent": {"טום": 80.0}, "total_hours": 80.0,
            "phoenix_count": 3, "phoenix_billing": 300}

def test_export_weekly_creates_sheet():
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
        path = f.name
    try:
        export_weekly_kpi(_kpi(), path)
        wb = openpyxl.load_workbook(path)
        assert 'KPI שבועי' in wb.sheetnames
    finally:
        os.unlink(path)

def test_export_weekly_has_agent_name():
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
        path = f.name
    try:
        export_weekly_kpi(_kpi(), path)
        wb = openpyxl.load_workbook(path)
        ws = wb['KPI שבועי']
        names = [ws.cell(r, 1).value for r in range(2, ws.max_row + 1)]
        assert 'טום' in names
    finally:
        os.unlink(path)

def test_export_monthly_has_three_sheets():
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
        path = f.name
    try:
        export_monthly_bonus(_bonus(), _billing(), "יוני 2026", path)
        wb = openpyxl.load_workbook(path)
        assert {'לתשלום', 'מפרוט', 'חיוב ללקוח'}.issubset(set(wb.sheetnames))
    finally:
        os.unlink(path)
```

- [ ] **Step 2: Run to verify failure**

```bash
python -m pytest tests/test_excel_exporter.py -v
```

- [ ] **Step 3: Implement excel_exporter.py**

```python
# modules/excel_exporter.py
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment

_FILL = PatternFill("solid", fgColor="1F4E79")
_FONT = Font(color="FFFFFF", bold=True)
_CENTER = Alignment(horizontal='center')


def _header(ws, row, cols):
    for c, val in enumerate(cols, 1):
        cell = ws.cell(row, c, val)
        cell.fill = _FILL; cell.font = _FONT; cell.alignment = _CENTER


def export_weekly_kpi(kpi_data: list, filepath: str) -> None:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'KPI שבועי'
    _header(ws, 1, ['נציג', 'שעות', 'תיאומים', 'פגישות/שעה', 'תעסוקה %', 'סרק %', 'פניקס'])
    for i, a in enumerate(kpi_data, 2):
        ws.cell(i, 1, a['name'])
        ws.cell(i, 2, round(a['hours'], 1))
        ws.cell(i, 3, a['meetings'])
        ws.cell(i, 4, round(a['meetings_per_hour'], 2))
        ws.cell(i, 5, f"{a['occupancy_pct']*100:.1f}%")
        ws.cell(i, 6, f"{a['idle_pct']*100:.2f}%")
        ws.cell(i, 7, a['phoenix'])
    wb.save(filepath)


def export_monthly_bonus(bonus_data: list, billing: dict, month_label: str, filepath: str) -> None:
    wb = openpyxl.Workbook()
    wb.remove(wb.active)

    ws1 = wb.create_sheet('לתשלום')
    _header(ws1, 1, ['שם', 'מספר עובד', 'בונוס לתשלום'])
    for i, b in enumerate(bonus_data, 2):
        ws1.cell(i, 1, b['name']); ws1.cell(i, 2, b['employee_id']); ws1.cell(i, 3, b['total'])

    ws2 = wb.create_sheet('מפרוט')
    _header(ws2, 1, ['שם', 'תיאומים', 'תעסוקה', 'סרק', 'משוב', 'פניקס', 'סה"כ'])
    for i, b in enumerate(bonus_data, 2):
        for c, k in enumerate(['name','meetings_bonus','occupancy_bonus','idle_bonus',
                                'feedback_bonus','phoenix_bonus','total'], 1):
            ws2.cell(i, c, b[k])

    ws3 = wb.create_sheet('חיוב ללקוח')
    ws3.cell(1, 1, f'חיוב חודש {month_label}')
    _header(ws3, 2, ['נציג', 'שעות'])
    for i, (name, hours) in enumerate(billing['hours_by_agent'].items(), 3):
        ws3.cell(i, 1, name); ws3.cell(i, 2, round(hours, 1))
    r = len(billing['hours_by_agent']) + 3
    ws3.cell(r, 1, 'סה"כ שעות'); ws3.cell(r, 2, round(billing['total_hours'], 1))
    ws3.cell(r+1, 1, f'פניקס ({billing["phoenix_count"]} עסקאות)')
    ws3.cell(r+1, 2, billing['phoenix_billing'])

    wb.save(filepath)
```

- [ ] **Step 4: Run tests**

```bash
python -m pytest tests/test_excel_exporter.py -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add modules/excel_exporter.py tests/test_excel_exporter.py
git commit -m "feat: Excel exporter — weekly KPI and monthly bonus (3 sheets)"
```

---

## Task 10: Email Builder

**Files:**
- Create: `modules/email_builder.py`
- Create: `tests/test_email_builder.py`

- [ ] **Step 1: Write failing tests**

```python
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
```

- [ ] **Step 2: Run to verify failures**

```bash
python -m pytest tests/test_email_builder.py -v
```

- [ ] **Step 3: Implement email_builder.py**

```python
# modules/email_builder.py
_TH = 'background:#1F4E79;color:#fff;padding:8px 12px;border:1px solid #ccc;text-align:center'
_TD = 'padding:8px 12px;border:1px solid #ccc;text-align:center'
_TABLE = 'border-collapse:collapse;width:100%;direction:rtl;font-family:Arial,sans-serif'
_WRAP = '<div style="direction:rtl;font-family:Arial,sans-serif;padding:20px">{}</div>'


def _table(headers, rows):
    ths = ''.join(f'<th style="{_TH}">{h}</th>' for h in headers)
    trs = ''.join(
        '<tr>' + ''.join(f'<td style="{_TD}">{v}</td>' for v in row) + '</tr>'
        for row in rows
    )
    return f'<table style="{_TABLE}"><thead><tr>{ths}</tr></thead><tbody>{trs}</tbody></table>'


def build_weekly_management_email(kpi_data: list, week_label: str) -> str:
    rows = [[a['name'], f"{a['hours']:.1f}", a['meetings'],
             f"{a['meetings_per_hour']:.2f}", f"{a['occupancy_pct']*100:.1f}%",
             f"{a['idle_pct']*100:.2f}%", a['phoenix']] for a in kpi_data]
    table = _table(['נציג','שעות','תיאומים','פגישות/שעה','תעסוקה','סרק','פניקס'], rows)
    return _WRAP.format(f'<h2>דוח KPI שבועי — {week_label}</h2>{table}')


def build_weekly_agent_email(agent_kpi: dict, agent_name: str, week_label: str) -> str:
    a = agent_kpi
    rows = [['שעות', f"{a['hours']:.1f}"], ['תיאומים', a['meetings']],
            ['פגישות/שעה', f"{a['meetings_per_hour']:.2f}"],
            ['תעסוקה', f"{a['occupancy_pct']*100:.1f}%"],
            ['סרק', f"{a['idle_pct']*100:.2f}%"], ['פניקס', a['phoenix']]]
    table = _table(['מדד', 'ערך'], rows)
    return _WRAP.format(f'<h2>שלום {agent_name},</h2><p>דוח ביצועים — {week_label}</p>{table}')


def build_monthly_client_email(billing: dict, month_label: str) -> str:
    rows = [['שעות עבודה', f"{billing['total_hours']:.1f}", '—'],
            ['פניקס', billing['phoenix_count'], f"₪{billing['phoenix_billing']:,}"]]
    table = _table(['פריט', 'כמות', 'עלות'], rows)
    return _WRAP.format(f'<h2>חיוב חודשי — {month_label}</h2>{table}<p>מצורף Excel מפורט.</p>')


def build_monthly_agent_email(agent_kpi: dict, agent_bonus: dict,
                               agent_name: str, month_label: str) -> str:
    b = agent_bonus
    rows = [['תיאומים', f"₪{b['meetings_bonus']:,}"],
            ['תעסוקה', f"₪{b['occupancy_bonus']:,}"],
            ['סרק', f"₪{b['idle_bonus']:,}"],
            ['משוב', f"₪{b['feedback_bonus']:,}"],
            ['פניקס', f"₪{b['phoenix_bonus']:,}"],
            ['<b>סה"כ</b>', f"<b>₪{b['total']:,}</b>"]]
    table = _table(['רכיב', 'סכום'], rows)
    return _WRAP.format(f'<h2>שלום {agent_name},</h2><p>פירוט בונוס — {month_label}</p>{table}')
```

- [ ] **Step 4: Run tests**

```bash
python -m pytest tests/test_email_builder.py -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add modules/email_builder.py tests/test_email_builder.py
git commit -m "feat: HTML email builder for all 4 email types"
```

---

## Task 11: Email Sender

**Files:**
- Create: `modules/email_sender.py`
- Create: `tests/test_email_sender.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_email_sender.py
from unittest.mock import patch, MagicMock
from modules.email_sender import send_email, SendResult

_SMTP_CFG = {"host": "smtp.gmail.com", "port": 587,
             "username": "a@b.com", "from_email": "a@b.com"}

def test_send_returns_success():
    with patch('smtplib.SMTP') as mock_smtp:
        ctx = MagicMock()
        mock_smtp.return_value.__enter__.return_value = ctx
        result = send_email(_SMTP_CFG, "pw", ["r@t.com"], "Subject", "<p>Hi</p>")
        assert result.success is True
        assert ctx.sendmail.called

def test_send_returns_failure_on_exception():
    with patch('smtplib.SMTP') as mock_smtp:
        mock_smtp.return_value.__enter__.side_effect = Exception("refused")
        result = send_email(_SMTP_CFG, "bad", ["r@t.com"], "Subject", "<p>Hi</p>")
        assert result.success is False
        assert "refused" in result.error
```

- [ ] **Step 2: Run to verify failure**

```bash
python -m pytest tests/test_email_sender.py -v
```

- [ ] **Step 3: Implement email_sender.py**

```python
# modules/email_sender.py
import smtplib, os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from dataclasses import dataclass
from typing import Optional


@dataclass
class SendResult:
    success: bool
    error: Optional[str] = None


def send_email(smtp_config: dict, smtp_password: str, to: list,
               subject: str, html_body: str,
               attachment_path: Optional[str] = None) -> SendResult:
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = smtp_config['from_email']
    msg['To'] = ', '.join(to)
    msg.attach(MIMEText(html_body, 'html', 'utf-8'))
    if attachment_path:
        with open(attachment_path, 'rb') as f:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition',
                        f'attachment; filename="{os.path.basename(attachment_path)}"')
        msg.attach(part)
    try:
        with smtplib.SMTP(smtp_config['host'], smtp_config['port']) as srv:
            srv.starttls()
            srv.login(smtp_config['username'], smtp_password)
            srv.sendmail(smtp_config['from_email'], to, msg.as_string())
        return SendResult(success=True)
    except Exception as e:
        return SendResult(success=False, error=str(e))
```

- [ ] **Step 4: Run all tests**

```bash
python -m pytest tests/ -v
```
Expected: PASS (all)

- [ ] **Step 5: Commit**

```bash
git add modules/email_sender.py tests/test_email_sender.py
git commit -m "feat: SMTP email sender with attachment support"
```

---

## Task 12: Screen — Agent Management

No automated tests for Streamlit screens. Verify via `python -c` import check.

**Files:**
- Create: `screens/agent_management.py`

- [ ] **Step 1: Implement agent_management.py**

```python
# screens/agent_management.py
import streamlit as st
from modules.config_manager import load_agents, save_agents


def render():
    st.header("ניהול נציגים")
    agents = load_agents()

    st.subheader("נציגים קיימים")
    for i, agent in enumerate(agents):
        c1, c2, c3, c4, c5 = st.columns([3, 2, 3, 2, 1])
        with c1:
            agents[i]["name"] = st.text_input("שם", agent["name"], key=f"n_{i}")
        with c2:
            agents[i]["employee_id"] = int(st.number_input(
                "מ. עובד", value=agent["employee_id"], step=1, key=f"e_{i}"))
        with c3:
            agents[i]["email"] = st.text_input("מייל", agent.get("email", ""), key=f"m_{i}")
        with c4:
            agents[i]["active"] = st.checkbox("פעיל", agent["active"], key=f"a_{i}")
        with c5:
            if st.button("🗑", key=f"d_{i}"):
                agents.pop(i)
                save_agents(agents)
                st.rerun()

    if st.button("שמור שינויים"):
        save_agents(agents)
        st.success("נשמר בהצלחה")

    st.divider()
    st.subheader("הוספת נציג חדש")
    with st.form("add"):
        name = st.text_input("שם")
        emp_id = st.number_input("מספר עובד", step=1, value=0)
        email = st.text_input("מייל")
        if st.form_submit_button("הוסף") and name:
            agents.append({"id": name.replace(" ", "_"),
                           "name": name, "employee_id": int(emp_id),
                           "email": email, "active": True})
            save_agents(agents)
            st.success(f"נציג {name} נוסף")
            st.rerun()
```

- [ ] **Step 2: Verify import**

```bash
python -c "from screens.agent_management import render; print('OK')"
```
Expected: OK

- [ ] **Step 3: Commit**

```bash
git add screens/agent_management.py
git commit -m "feat: agent management screen"
```

---

## Task 13: Screen — Settings

**Files:**
- Create: `screens/settings_screen.py`

- [ ] **Step 1: Implement settings_screen.py**

```python
# screens/settings_screen.py
import streamlit as st
from modules.config_manager import load_settings, save_settings


def render():
    st.header("הגדרות מערכת")
    s = load_settings()
    t = s["bonus_thresholds"]

    st.subheader("ספי בונוס")
    c1, c2 = st.columns(2)
    with c1:
        t["meetings_per_hour_tier_a"] = st.number_input("פגישות/שעה (סף תעריף 5₪)", value=float(t["meetings_per_hour_tier_a"]), step=0.1)
        t["occupancy_tier_a_pct"] = st.number_input("תעסוקה A %", value=int(t["occupancy_tier_a_pct"]))
        t["occupancy_tier_b_pct"] = st.number_input("תעסוקה B %", value=int(t["occupancy_tier_b_pct"]))
        t["idle_tier_a_pct"] = st.number_input("סרק A % (מקסימום)", value=int(t["idle_tier_a_pct"]))
        t["idle_tier_b_pct"] = st.number_input("סרק B % (מקסימום)", value=int(t["idle_tier_b_pct"]))
    with c2:
        t["feedback_tier_a_score"] = st.number_input("ציון משוב A", value=float(t["feedback_tier_a_score"]), step=0.1)
        t["feedback_tier_b_score"] = st.number_input("ציון משוב B", value=float(t["feedback_tier_b_score"]), step=0.1)
        t["phoenix_employee_rate"] = st.number_input("פניקס לנציג ₪", value=int(t["phoenix_employee_rate"]))
        t["phoenix_client_rate"] = st.number_input("פניקס ללקוח ₪", value=int(t["phoenix_client_rate"]))
        t["manager_bonus_a"] = st.number_input("בונוס מנהל A ₪", value=int(t["manager_bonus_a"]))
        t["manager_bonus_b"] = st.number_input("בונוס מנהל B ₪", value=int(t["manager_bonus_b"]))
        t["manager_bonus_c"] = st.number_input("בונוס מנהל C ₪", value=int(t["manager_bonus_c"]))

    st.subheader("SMTP")
    smtp = s["smtp"]
    smtp["host"] = st.text_input("שרת", smtp.get("host", ""))
    smtp["port"] = int(st.number_input("פורט", value=int(smtp.get("port", 587))))
    smtp["username"] = st.text_input("שם משתמש", smtp.get("username", ""))
    smtp["from_email"] = st.text_input("כתובת שולח", smtp.get("from_email", ""))
    st.info("סיסמת SMTP מוגדרת ב-Streamlit Cloud Secrets (SMTP_PASSWORD)")

    st.subheader("נמענים")
    r = s["recipients"]
    r["management"] = [x.strip() for x in st.text_area(
        "הנהלה (שורה לכל כתובת)", "\n".join(r.get("management", []))).splitlines() if x.strip()]
    r["client"] = [x.strip() for x in st.text_area(
        "לקוח — וולטה (שורה לכל כתובת)", "\n".join(r.get("client", []))).splitlines() if x.strip()]

    if st.button("שמור הגדרות"):
        save_settings(s)
        st.success("הגדרות נשמרו")
```

- [ ] **Step 2: Verify import**

```bash
python -c "from screens.settings_screen import render; print('OK')"
```

- [ ] **Step 3: Commit**

```bash
git add screens/settings_screen.py
git commit -m "feat: settings screen for bonus thresholds, SMTP, recipients"
```

---

## Task 14: Screen — Weekly KPI

**Files:**
- Create: `screens/weekly_kpi.py`

- [ ] **Step 1: Implement weekly_kpi.py**

```python
# screens/weekly_kpi.py
import streamlit as st
import tempfile, os
from modules.data_loader import parse_attendance, parse_voicenter
from modules.calculator import (calculate_work_hours, calculate_meetings_per_hour,
                                 calculate_idle_pct, calculate_center_rate)
from modules.config_manager import load_agents, load_settings
from modules.email_builder import build_weekly_management_email, build_weekly_agent_email
from modules.email_sender import send_email
from modules.excel_exporter import export_weekly_kpi


def _save_upload(uploaded, suffix):
    f = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    f.write(uploaded.read()); f.close()
    return f.name


def render():
    st.header("דוח KPI שבועי")
    agents = [a for a in load_agents() if a["active"]]
    settings = load_settings()

    st.subheader("1. העלאת קבצים")
    c1, c2 = st.columns(2)
    att_file = c1.file_uploader("נוכחות (.xlsx)", type=['xlsx'], key="w_att")
    vc_file  = c2.file_uploader("Voicenter (.xls)", type=['xls','xlsx'], key="w_vc")
    if not att_file or not vc_file:
        st.info("נא להעלות את שני הקבצים")
        return

    att_path = _save_upload(att_file, '.xlsx')
    vc_path  = _save_upload(vc_file, '.xls')
    try:
        att_df = parse_attendance(att_path)
        vc_df  = parse_voicenter(vc_path)
    except Exception as e:
        st.error(f"שגיאה בקריאת קבצים: {e}")
        return
    finally:
        os.unlink(att_path); os.unlink(vc_path)

    st.subheader("2. הזנה ידנית")
    week_label = st.text_input("תיאור שבוע", "שבוע X — יוני 2026")
    manual = {}
    cols = st.columns(len(agents))
    for col, agent in zip(cols, agents):
        with col:
            st.markdown(f"**{agent['name']}**")
            manual[agent["id"]] = {
                "meetings":   st.number_input("תיאומים",  min_value=0, key=f"wm_{agent['id']}"),
                "phoenix":    st.number_input("פניקס",    min_value=0, key=f"wp_{agent['id']}"),
                "idle_calls": st.number_input("שיחות סרק", min_value=0, key=f"wi_{agent['id']}"),
            }

    if not st.button("חשב KPI"):
        return

    kpi_data = []
    for agent in agents:
        hours = calculate_work_hours(att_df, agent["employee_id"])
        inp = manual[agent["id"]]
        vc_row = vc_df[vc_df['משתמש'].str.contains(agent['name'].split()[0], na=False)]
        answered = int(vc_row['נענו'].iloc[0]) if len(vc_row) else 0
        occ_pct  = float(vc_row['אחוז תעסוקה נטו'].iloc[0]) if len(vc_row) else 0.0
        kpi_data.append({
            "agent_id": agent["id"], "name": agent["name"],
            "email": agent.get("email", ""), "hours": hours,
            "meetings": inp["meetings"],
            "meetings_per_hour": calculate_meetings_per_hour(inp["meetings"], hours),
            "occupancy_pct": occ_pct, "idle_calls": inp["idle_calls"],
            "idle_pct": calculate_idle_pct(inp["idle_calls"], answered),
            "answered_calls": answered, "phoenix": inp["phoenix"],
        })

    center_rate = calculate_center_rate([{"hours": k["hours"], "meetings": k["meetings"]} for k in kpi_data])

    st.subheader("3. תוצאות")
    center_ok = center_rate >= settings["bonus_thresholds"]["meetings_per_hour_tier_a"]
    st.metric("קצב מוקד", f"{center_rate:.2f} פגישות/שעה",
              delta="✅ עמד ביעד" if center_ok else "❌ לא עמד")
    st.dataframe([{
        "נציג": k["name"], "שעות": f"{k['hours']:.1f}", "תיאומים": k["meetings"],
        "פגישות/שעה": f"{k['meetings_per_hour']:.2f}",
        "תעסוקה": f"{k['occupancy_pct']*100:.1f}%",
        "סרק": f"{k['idle_pct']*100:.2f}%", "פניקס": k["phoenix"],
    } for k in kpi_data], use_container_width=True)

    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
        xl_path = f.name
    export_weekly_kpi(kpi_data, xl_path)
    with open(xl_path, 'rb') as f:
        st.download_button("📥 הורד Excel", f.read(), file_name=f"kpi_{week_label}.xlsx")
    os.unlink(xl_path)

    st.subheader("4. שליחת מיילים")
    mgmt_html = build_weekly_management_email(kpi_data, week_label)
    with st.expander("תצוגה מקדימה — מייל הנהלה"):
        st.components.v1.html(mgmt_html, height=400, scrolling=True)

    confirmed = st.checkbox("בדקתי ואישרתי את התצוגה המקדימה")
    if not confirmed:
        return

    smtp = settings["smtp"]
    password = st.secrets.get("SMTP_PASSWORD", "")
    c_mgmt, c_agents = st.columns(2)
    with c_mgmt:
        if st.button("שלח להנהלה"):
            r = send_email(smtp, password, settings["recipients"]["management"],
                           f"KPI שבועי — {week_label}", mgmt_html)
            st.success("נשלח") if r.success else st.error(r.error)
    with c_agents:
        if st.button("שלח לנציגים"):
            for k in kpi_data:
                if not k.get("email"):
                    st.warning(f"חסר מייל: {k['name']}"); continue
                html = build_weekly_agent_email(k, k["name"], week_label)
                r = send_email(smtp, password, [k["email"]],
                               f"ביצועים שבועיים — {week_label}", html)
                st.success(f"נשלח ל-{k['name']}") if r.success else st.error(f"{k['name']}: {r.error}")
```

- [ ] **Step 2: Verify import**

```bash
python -c "from screens.weekly_kpi import render; print('OK')"
```

- [ ] **Step 3: Commit**

```bash
git add screens/weekly_kpi.py
git commit -m "feat: weekly KPI screen with file upload, calculation, email send"
```

---

## Task 15: Screen — Monthly Bonus

**Files:**
- Create: `screens/monthly_bonus.py`

- [ ] **Step 1: Implement monthly_bonus.py**

```python
# screens/monthly_bonus.py
import streamlit as st
import tempfile, os
from modules.data_loader import parse_attendance, parse_voicenter, parse_feedback
from modules.calculator import (calculate_work_hours, calculate_meetings_per_hour,
                                 calculate_idle_pct, calculate_center_rate,
                                 calculate_agent_bonus, calculate_manager_bonus)
from modules.config_manager import load_agents, load_settings
from modules.email_builder import (build_monthly_client_email, build_monthly_agent_email)
from modules.email_sender import send_email
from modules.excel_exporter import export_monthly_bonus


def _save_upload(uploaded, suffix):
    f = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    f.write(uploaded.read()); f.close()
    return f.name


def render():
    st.header("בונוסים חודשיים")
    agents = [a for a in load_agents() if a["active"]]
    settings = load_settings()
    t = settings["bonus_thresholds"]

    st.subheader("1. העלאת קבצים")
    c1, c2, c3 = st.columns(3)
    att_file = c1.file_uploader("נוכחות (.xlsx)", type=['xlsx'], key="b_att")
    vc_file  = c2.file_uploader("Voicenter (.xls)", type=['xls','xlsx'], key="b_vc")
    fb_file  = c3.file_uploader("משובים (.xlsx) — אופציונלי", type=['xlsx'], key="b_fb")
    if not att_file or not vc_file:
        st.info("נא להעלות לפחות קבצי נוכחות ו-Voicenter")
        return

    att_path = _save_upload(att_file, '.xlsx')
    vc_path  = _save_upload(vc_file, '.xls')
    fb_path  = _save_upload(fb_file, '.xlsx') if fb_file else None
    try:
        att_df = parse_attendance(att_path)
        vc_df  = parse_voicenter(vc_path)
        feedback_scores = parse_feedback(fb_path) if fb_path else {}
    except Exception as e:
        st.error(f"שגיאה בקריאת קבצים: {e}")
        return
    finally:
        for p in [att_path, vc_path, fb_path]:
            if p: os.unlink(p)

    st.subheader("2. הזנה ידנית")
    month_label = st.text_input("חודש", "יוני 2026")
    manual = {}
    cols = st.columns(len(agents))
    for col, agent in zip(cols, agents):
        with col:
            st.markdown(f"**{agent['name']}**")
            manual[agent["id"]] = {
                "meetings":   st.number_input("תיאומים",  min_value=0, key=f"bm_{agent['id']}"),
                "phoenix":    st.number_input("פניקס",    min_value=0, key=f"bp_{agent['id']}"),
                "idle_calls": st.number_input("שיחות סרק", min_value=0, key=f"bi_{agent['id']}"),
            }

    if not st.button("חשב בונוסים"):
        return

    kpi_data = []
    for agent in agents:
        hours = calculate_work_hours(att_df, agent["employee_id"])
        inp = manual[agent["id"]]
        vc_row = vc_df[vc_df['משתמש'].str.contains(agent['name'].split()[0], na=False)]
        answered = int(vc_row['נענו'].iloc[0]) if len(vc_row) else 0
        occ_pct  = float(vc_row['אחוז תעסוקה נטו'].iloc[0]) if len(vc_row) else 0.0
        kpi_data.append({
            "agent_id": agent["id"], "name": agent["name"],
            "employee_id": agent["employee_id"], "email": agent.get("email", ""),
            "hours": hours, "meetings": inp["meetings"],
            "meetings_per_hour": calculate_meetings_per_hour(inp["meetings"], hours),
            "occupancy_pct": occ_pct, "idle_calls": inp["idle_calls"],
            "idle_pct": calculate_idle_pct(inp["idle_calls"], answered),
            "phoenix": inp["phoenix"],
            "feedback_score": feedback_scores.get(agent["name"]),
        })

    center_rate  = calculate_center_rate([{"hours": k["hours"], "meetings": k["meetings"]} for k in kpi_data])
    center_meets = center_rate >= t["meetings_per_hour_tier_a"]

    bonus_data = []
    for k in kpi_data:
        kpi_in = {"meetings": k["meetings"], "individual_rate": k["meetings_per_hour"],
                  "occupancy_pct": k["occupancy_pct"], "idle_pct": k["idle_pct"],
                  "feedback_score": k["feedback_score"], "phoenix": k["phoenix"]}
        b = calculate_agent_bonus(kpi_in, center_meets, settings)
        bonus_data.append({"name": k["name"], "employee_id": k["employee_id"], **b})

    manager_bonus = calculate_manager_bonus(center_rate, settings)
    total_phoenix = sum(k["phoenix"] for k in kpi_data)
    billing = {"hours_by_agent": {k["name"]: k["hours"] for k in kpi_data},
               "total_hours": sum(k["hours"] for k in kpi_data),
               "phoenix_count": total_phoenix,
               "phoenix_billing": total_phoenix * t["phoenix_client_rate"]}

    st.subheader("3. תוצאות")
    c_a, c_b = st.columns(2)
    c_a.metric("קצב מוקד", f"{center_rate:.2f}/שעה",
               delta="✅ עמד ביעד" if center_meets else "❌ לא עמד")
    c_b.metric("בונוס מנהל", f"₪{manager_bonus:,}")
    st.dataframe([{
        "נציג": b["name"], "תיאומים ₪": b["meetings_bonus"],
        "תעסוקה ₪": b["occupancy_bonus"], "סרק ₪": b["idle_bonus"],
        "משוב ₪": b["feedback_bonus"], "פניקס ₪": b["phoenix_bonus"],
        "סה\"כ ₪": b["total"],
    } for b in bonus_data], use_container_width=True)

    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
        xl_path = f.name
    export_monthly_bonus(bonus_data, billing, month_label, xl_path)
    with open(xl_path, 'rb') as f:
        xl_bytes = f.read()
    st.download_button("📥 הורד Excel", xl_bytes, file_name=f"bonuses_{month_label}.xlsx")
    os.unlink(xl_path)

    st.subheader("4. שליחת מיילים")
    client_html = build_monthly_client_email(billing, month_label)
    with st.expander("תצוגה מקדימה — מייל ללקוח"):
        st.components.v1.html(client_html, height=300, scrolling=True)

    confirmed = st.checkbox("בדקתי ואישרתי את כל המיילים")
    if not confirmed:
        return

    smtp = settings["smtp"]
    password = st.secrets.get("SMTP_PASSWORD", "")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("שלח ללקוח (וולטה) + Excel"):
            with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
                xl2 = f.name
            export_monthly_bonus(bonus_data, billing, month_label, xl2)
            r = send_email(smtp, password, settings["recipients"]["client"],
                           f"חיוב חודש {month_label}", client_html, attachment_path=xl2)
            os.unlink(xl2)
            st.success("נשלח ללקוח") if r.success else st.error(r.error)
    with c2:
        if st.button("שלח בונוסים לכל נציג"):
            for k, b in zip(kpi_data, bonus_data):
                if not k.get("email"):
                    st.warning(f"חסר מייל: {k['name']}"); continue
                html = build_monthly_agent_email(k, b, k["name"], month_label)
                r = send_email(smtp, password, [k["email"]],
                               f"בונוס חודש {month_label}", html)
                st.success(f"נשלח ל-{k['name']}") if r.success else st.error(f"{k['name']}: {r.error}")
```

- [ ] **Step 2: Verify import**

```bash
python -c "from screens.monthly_bonus import render; print('OK')"
```

- [ ] **Step 3: Commit**

```bash
git add screens/monthly_bonus.py
git commit -m "feat: monthly bonus screen with bonus calculation, Excel export, email send"
```

---

## Task 16: History Manager

Saves and loads monthly snapshots. One JSON file (`data/history.json`) holds all past months as a list.

**Files:**
- Create: `modules/history_manager.py`
- Create: `tests/test_history_manager.py`

- [ ] **Step 1: Write failing tests**

```python
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
```

- [ ] **Step 2: Run to verify failure**

```bash
python -m pytest tests/test_history_manager.py -v
```
Expected: ImportError

- [ ] **Step 3: Implement history_manager.py**

```python
# modules/history_manager.py
import json, os
from datetime import datetime

_DEFAULT_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'history.json')


def load_history(path: str = _DEFAULT_PATH) -> list:
    if not os.path.exists(path):
        return []
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def save_month(snapshot: dict, path: str = _DEFAULT_PATH) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    history = load_history(path)
    # Overwrite if same month already exists
    history = [h for h in history if h.get("month") != snapshot["month"]]
    snapshot["saved_at"] = datetime.now().isoformat()
    history.append(snapshot)
    history.sort(key=lambda h: h["month"])
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def get_month(month: str, path: str = _DEFAULT_PATH):
    return next((h for h in load_history(path) if h["month"] == month), None)
```

- [ ] **Step 4: Run all tests**

```bash
python -m pytest tests/ -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add modules/history_manager.py tests/test_history_manager.py
git commit -m "feat: monthly history manager — save/load/overwrite snapshots"
```

---

## Task 17: Screen — History & Analytics

Displays trend charts and monthly comparisons from saved history.

**Files:**
- Create: `screens/history.py`

- [ ] **Step 1: Implement history.py**

```python
# screens/history.py
import streamlit as st
import json
from modules.history_manager import load_history, save_month

try:
    import plotly.express as px
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False


def render():
    st.header("היסטוריה וניתוח נתונים")
    history = load_history()

    if not history:
        st.info("אין נתונים היסטוריים עדיין. לאחר חישוב חודשי, לחץ 'שמור חודש להיסטוריה'.")
        _upload_section()
        return

    labels = [h["label"] for h in history]
    months = [h["month"] for h in history]

    st.subheader("סיכום חודשים")
    summary_rows = [{
        "חודש": h["label"],
        "קצב מוקד": f"{h['center_rate']:.2f}",
        "עמד ביעד": "✅" if h["center_met_target"] else "❌",
        "בונוס מנהל ₪": f"{h['manager_bonus']:,}",
        "חיוב ללקוח ₪": f"{h['total_billing']:,}",
    } for h in history]
    st.dataframe(summary_rows, use_container_width=True)

    if HAS_PLOTLY:
        st.subheader("קצב מוקד לאורך זמן")
        fig = px.line(x=labels, y=[h["center_rate"] for h in history],
                      labels={"x": "חודש", "y": "פגישות/שעה"},
                      markers=True)
        fig.add_hline(y=1.0, line_dash="dash", line_color="green",
                      annotation_text="יעד 1.0")
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("פניקס לפי חודש")
        phoenix_by_month = [sum(a["phoenix"] for a in h["agents"]) for h in history]
        fig2 = px.bar(x=labels, y=phoenix_by_month,
                      labels={"x": "חודש", "y": "עסקאות פניקס"})
        st.plotly_chart(fig2, use_container_width=True)

        # Per-agent meetings/hour trend
        st.subheader("פגישות/שעה לפי נציג")
        agent_names = list({a["name"] for h in history for a in h["agents"]})
        for name in agent_names:
            rates = []
            month_labels = []
            for h in history:
                agent = next((a for a in h["agents"] if a["name"] == name), None)
                if agent:
                    rates.append(agent["meetings_per_hour"])
                    month_labels.append(h["label"])
            if rates:
                fig3 = px.line(x=month_labels, y=rates,
                               title=name, labels={"x": "חודש", "y": "פגישות/שעה"},
                               markers=True)
                fig3.add_hline(y=1.0, line_dash="dash", line_color="green")
                st.plotly_chart(fig3, use_container_width=True)

        st.subheader("מגמת בונוסים")
        for name in agent_names:
            bonuses = []
            month_labels = []
            for h in history:
                agent = next((a for a in h["agents"] if a["name"] == name), None)
                if agent:
                    bonuses.append(agent["bonus_total"])
                    month_labels.append(h["label"])
            if bonuses:
                fig4 = px.bar(x=month_labels, y=bonuses,
                              title=f"בונוס — {name}",
                              labels={"x": "חודש", "y": "בונוס ₪"})
                st.plotly_chart(fig4, use_container_width=True)
    else:
        st.warning("התקן את plotly לגרפים: `pip install plotly`")
        for h in history:
            with st.expander(h["label"]):
                st.json(h)

    st.divider()
    # Download / upload
    col1, col2 = st.columns(2)
    with col1:
        st.download_button("📥 הורד היסטוריה (JSON)",
                           json.dumps(history, ensure_ascii=False, indent=2).encode('utf-8'),
                           file_name="kpi_history.json", mime="application/json")
    with col2:
        _upload_section()


def _upload_section():
    uploaded = st.file_uploader("📤 העלה היסטוריה (JSON)", type=['json'], key="hist_upload")
    if uploaded:
        data = json.loads(uploaded.read().decode('utf-8'))
        for month_data in data:
            save_month(month_data)
        st.success(f"שוחזרו {len(data)} חודשים")
        st.rerun()
```

- [ ] **Step 2: Install plotly**

```bash
pip install plotly
```
Add `plotly>=5.0` to `requirements.txt`.

- [ ] **Step 3: Verify import**

```bash
python -c "from screens.history import render; print('OK')"
```
Expected: OK

- [ ] **Step 4: Commit**

```bash
git add screens/history.py requirements.txt
git commit -m "feat: history screen with trend charts (plotly)"
```

---

## Task 18: Update Monthly Bonus Screen — Save to History

Add a "שמור חודש להיסטוריה" button to the monthly bonus screen after calculation.

**Files:**
- Modify: `screens/monthly_bonus.py`

- [ ] **Step 1: Add import and save button**

At the top of `screens/monthly_bonus.py`, add:
```python
from modules.history_manager import save_month
```

After the bonus results table (after the `st.dataframe(...)` call in the results section), add:

```python
    if st.button("💾 שמור חודש להיסטוריה"):
        snapshot = {
            "month": month_label[:7] if len(month_label) >= 7 else month_label,
            "label": month_label,
            "center_rate": center_rate,
            "center_met_target": center_meets,
            "manager_bonus": manager_bonus,
            "total_billing": billing["phoenix_billing"],
            "agents": [{
                "name": k["name"],
                "hours": k["hours"],
                "meetings": k["meetings"],
                "meetings_per_hour": k["meetings_per_hour"],
                "occupancy_pct": k["occupancy_pct"],
                "idle_pct": k["idle_pct"],
                "feedback_score": k["feedback_score"],
                "phoenix": k["phoenix"],
                "bonus_total": b["total"],
            } for k, b in zip(kpi_data, bonus_data)]
        }
        save_month(snapshot)
        st.success(f"חודש {month_label} נשמר להיסטוריה ✅")
```

- [ ] **Step 2: Verify import still works**

```bash
python -c "from screens.monthly_bonus import render; print('OK')"
```

- [ ] **Step 3: Commit**

```bash
git add screens/monthly_bonus.py
git commit -m "feat: save monthly snapshot to history from bonus screen"
```

---

## Task 19: Screen — Dashboard

Shows active agents and the last saved month's highlights from history.

**Files:**
- Create: `screens/dashboard.py`

- [ ] **Step 1: Implement dashboard.py**

```python
# screens/dashboard.py
import streamlit as st
from modules.config_manager import load_agents
from modules.history_manager import load_history


def render():
    st.header("לוח בקרה — מוקד וולטה סולאר")
    agents = load_agents()
    active = [a for a in agents if a["active"]]

    history = load_history()
    last = history[-1] if history else None

    col1, col2, col3 = st.columns(3)
    col1.metric("נציגים פעילים", len(active))
    if last:
        col2.metric(f"קצב מוקד — {last['label']}", f"{last['center_rate']:.2f}",
                    delta="✅ עמד ביעד" if last["center_met_target"] else "❌ לא עמד")
        col3.metric(f"בונוס מנהל — {last['label']}", f"₪{last['manager_bonus']:,}")

    st.markdown("---")
    st.subheader("נציגים פעילים")
    for a in active:
        st.markdown(f"- **{a['name']}** (מ. עובד: {a['employee_id']})")

    if last:
        st.markdown("---")
        st.subheader(f"ביצועים אחרון — {last['label']}")
        st.dataframe([{
            "נציג": a["name"],
            "פגישות/שעה": f"{a['meetings_per_hour']:.2f}",
            "בונוס ₪": f"{a['bonus_total']:,}",
        } for a in last["agents"]], use_container_width=True)
```

- [ ] **Step 2: Verify import**

```bash
python -c "from screens.dashboard import render; print('OK')"
```

- [ ] **Step 3: Commit**

```bash
git add screens/dashboard.py
git commit -m "feat: dashboard screen"
```

---

## Task 20: Main App + Deployment

**Files:**
- Create: `app.py`

- [ ] **Step 1: Implement app.py**

```python
# app.py
import sys
sys.stdout.reconfigure(encoding='utf-8')

import streamlit as st

st.set_page_config(
    page_title="KPI — וולטה סולאר",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

from screens import (dashboard, weekly_kpi, monthly_bonus,
                     agent_management, settings_screen, history)

PAGES = {
    "📊 לוח בקרה":        dashboard,
    "📅 KPI שבועי":       weekly_kpi,
    "💰 בונוסים חודשיים": monthly_bonus,
    "📈 היסטוריה":        history,
    "👥 ניהול נציגים":    agent_management,
    "⚙️ הגדרות":          settings_screen,
}

with st.sidebar:
    st.title("מוקד וולטה סולאר")
    st.markdown("---")
    selection = st.radio("ניווט", list(PAGES.keys()), label_visibility="collapsed")

PAGES[selection].render()
```

- [ ] **Step 2: Run full test suite**

```bash
python -m pytest tests/ -v
```
Expected: PASS (all tests)

- [ ] **Step 3: Run app locally**

```bash
streamlit run app.py
```
Open `http://localhost:8501`. Verify all 5 screens load without errors. Test the golden path:
- Dashboard shows 4 agents
- Agent Management: add a test agent, verify it appears, delete it
- Settings: change one threshold, save, reload — verify it persisted
- Weekly KPI: upload the real files from `c:\Users\Sinaymer\KPIs Volta\`, enter sample numbers, click "חשב KPI", verify table appears and Excel download works
- Monthly Bonus: same files + feedback file, calculate — verify bonus table and Excel

- [ ] **Step 4: Commit**

```bash
git add app.py
git commit -m "feat: main app with sidebar navigation"
```

- [ ] **Step 5: Push to GitHub and deploy to Streamlit Cloud**

1. Create a new GitHub repo at github.com (name: `kpi-volta` or similar)
2. Push:
   ```bash
   git remote add origin https://github.com/<your-username>/kpi-volta.git
   git push -u origin main
   ```
3. Go to [share.streamlit.io](https://share.streamlit.io) → Sign in with GitHub → "New app"
4. Select repo `kpi-volta`, branch `main`, main file `app.py` → Deploy
5. After deploy: App Settings → Secrets → add:
   ```toml
   SMTP_PASSWORD = "your-smtp-app-password"
   ```
6. Open the deployed URL — verify the app works identically in browser without any local software

---

## Self-Review Notes

- All 5 screens, all 3 email types, all bonus components, and both Excel exports are covered.
- Voicenter name matching uses `str.contains(first_name)` — if agent names differ significantly between Voicenter and config, the user can update agent names in Settings to match exactly what Voicenter reports.
- Feedback file is optional (monthly bonus screen accepts 2 files minimum) — agents without a feedback score get 0₪ for that component with no error.
- Streamlit Cloud file persistence: config changes (agents, settings) write to disk. On redeployment, files reset to the committed defaults. For permanent agent/settings changes, commit the updated JSON files to GitHub before redeploying.
- The "backup before export" spec item doesn't apply to Streamlit's browser download model (no server-side file to overwrite).
