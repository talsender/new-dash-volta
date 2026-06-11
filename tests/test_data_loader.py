import pytest, pandas as pd, tempfile, os
from modules.data_loader import parse_attendance
from modules.data_loader import parse_voicenter


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
