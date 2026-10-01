import pytest, pandas as pd, tempfile, os
from modules.data_loader import parse_attendance
from modules.data_loader import parse_voicenter
from modules.data_loader import parse_feedback


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


def test_parse_voicenter_occupancy_integer_column():
    # Voicenter sometimes exports occupancy as plain integer (35) not string "35%"
    # The parser must still divide by 100 to produce 0.35
    path = _make_voicenter([
        {'משתמש': 'טום', 'סה"כ שיחות': 200, 'נענו': 190,
         'שיחות שלא נענו': 10, 'אחוז תעסוקה נטו': 35}
    ])
    try:
        df = parse_voicenter(path)
        assert df.iloc[0]['אחוז תעסוקה נטו'] == pytest.approx(0.35), \
            "Integer occupancy (35) must be divided by 100 to yield 0.35"
    finally:
        os.unlink(path)


def test_parse_voicenter_filters_total_rows():
    path = _make_voicenter([
        {'משתמש': 'טום', 'סה"כ שיחות': 200, 'נענו': 190,
         'שיחות שלא נענו': 10, 'אחוז תעסוקה נטו': '35%'},
        {'משתמש': 'סה"כ', 'סה"כ שיחות': 200, 'נענו': 190,
         'שיחות שלא נענו': 10, 'אחוז תעסוקה נטו': '35%'},
    ])
    try:
        df = parse_voicenter(path)
        assert len(df) == 1, "Total/summary row labeled סה\"כ must be dropped"
        assert df.iloc[0]['משתמש'] == 'טום'
    finally:
        os.unlink(path)


# ── Voicenter exports that are not the native HTML table ──────────

_VC_HEADERS = ['משתמש', 'סה"כ שיחות', 'נענו',
               'שיחות שלא נענו', 'אחוז תעסוקה נטו']
_VC_ROW = ['דיוד זיו', 200, 190, 10, '35%']


def test_parse_voicenter_reads_a_real_excel_workbook():
    """Opening the export in Excel and saving turns it into a real workbook."""
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["דוח שיחות"])        # Voicenter puts a title row above the headers
    ws.append(_VC_HEADERS)
    ws.append(_VC_ROW)
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
        path = f.name
    wb.save(path)
    try:
        df = parse_voicenter(path)
        assert df.iloc[0]['משתמש'] == 'דיוד זיו'
        assert df.iloc[0]['נענו'] == 190
        assert df.iloc[0]['אחוז תעסוקה נטו'] == pytest.approx(0.35)
    finally:
        os.unlink(path)


def test_parse_voicenter_reads_a_csv_export():
    with tempfile.NamedTemporaryFile(suffix='.csv', delete=False, mode='w',
                                     encoding='utf-8-sig', newline='') as f:
        f.write(",".join(_VC_HEADERS) + "\n")
        f.write(",".join(str(v) for v in _VC_ROW) + "\n")
        path = f.name
    try:
        df = parse_voicenter(path)
        assert df.iloc[0]['משתמש'] == 'דיוד זיו'
        assert df.iloc[0]['כניסות'] == 200
    finally:
        os.unlink(path)


def test_parse_voicenter_unreadable_file_says_what_it_got():
    """A generic 'cannot read' sends you hunting — name the format instead."""
    with tempfile.NamedTemporaryFile(suffix='.xls', delete=False) as f:
        f.write(b"%PDF-1.4 this is not a report at all")
        path = f.name
    try:
        with pytest.raises(KeyError) as err:
            parse_voicenter(path)
        assert "PDF" in str(err.value)
    finally:
        os.unlink(path)


# ── occupancy arrives in three different shapes ──────────────────

def _vc_xlsx(occupancy):
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(_VC_HEADERS)
    ws.append(['דיוד זיו', 1263, 733, 530, occupancy])
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
        path = f.name
    wb.save(path)
    return path


def test_occupancy_from_excel_percent_cell_is_not_divided_twice():
    """Excel stores a percent-formatted cell as the fraction 0.58, not '58%'."""
    path = _vc_xlsx(0.58)
    try:
        assert parse_voicenter(path).iloc[0]['אחוז תעסוקה נטו'] == pytest.approx(0.58)
    finally:
        os.unlink(path)


def test_occupancy_from_a_plain_number_is_read_as_percent():
    path = _vc_xlsx(58)
    try:
        assert parse_voicenter(path).iloc[0]['אחוז תעסוקה נטו'] == pytest.approx(0.58)
    finally:
        os.unlink(path)


def test_occupancy_written_as_text_with_a_percent_sign():
    path = _vc_xlsx("58%")
    try:
        assert parse_voicenter(path).iloc[0]['אחוז תעסוקה נטו'] == pytest.approx(0.58)
    finally:
        os.unlink(path)


def test_occupancy_above_100_percent_survives_the_excel_round_trip():
    """Real data has an agent at 102%. As an Excel fraction that is 1.02 —
    it must not be mistaken for 1%, which a per-cell 'is it above 1' rule would do."""
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(_VC_HEADERS)
    for name, occ in [("א", 0.33), ("ב", 0.49), ("ג", 1.02)]:
        ws.append([name, 1263, 733, 530, occ])
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
        path = f.name
    wb.save(path)
    try:
        got = list(parse_voicenter(path)['אחוז תעסוקה נטו'])
        assert got == pytest.approx([0.33, 0.49, 1.02])
    finally:
        os.unlink(path)
