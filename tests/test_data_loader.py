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
