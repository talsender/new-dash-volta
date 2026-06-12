import pandas as pd


def parse_attendance(filepath: str) -> pd.DataFrame:
    xl = pd.ExcelFile(filepath, engine='openpyxl')
    sheet = next((s for s in xl.sheet_names if 'וולטה' in s), xl.sheet_names[0])
    # read without headers to find the real header row
    raw = xl.parse(sheet, header=None)
    header_row = None
    for i, row in raw.iterrows():
        if any('מספר' in str(v) and 'עובד' in str(v) for v in row.values):
            header_row = i
            break
    if header_row is None:
        raise KeyError(f"לא נמצאה שורת כותרות עם 'מספר עובד'. שורה ראשונה: {list(raw.iloc[0])}")
    df = xl.parse(sheet, header=header_row)
    df.columns = [str(c).strip() for c in df.columns]
    emp_col = next((c for c in df.columns if 'מספר' in c and 'עובד' in c), None)
    hours_col = next((c for c in df.columns if 'סה"כ' in c or 'סהכ' in c or 'כללי' in c), None)
    if hours_col is None:
        raise KeyError(f"לא נמצאה עמודת סה\"כ שעות. עמודות: {list(df.columns)}")
    df['מספר עובד'] = pd.to_numeric(df[emp_col], errors='coerce').astype('Int64')
    df['סה"כ כללי'] = pd.to_numeric(df[hours_col], errors='coerce').fillna(0.0)
    return df


def parse_voicenter(filepath: str) -> pd.DataFrame:
    for enc in ('utf-16', 'utf-8', 'windows-1255'):
        try:
            tables = pd.read_html(filepath, encoding=enc)
            break
        except Exception:
            continue
    else:
        tables = pd.read_html(filepath)
    # find the table that contains a 'משתמש'-like column
    df = None
    for t in tables:
        t.columns = [str(c).strip() for c in t.columns]
        if any('משתמש' in c for c in t.columns):
            df = t
            break
    if df is None:
        all_cols = [list(t.columns) for t in tables]
        raise KeyError(f"לא נמצאה עמודת 'משתמש'. עמודות בטבלאות: {all_cols}")
    user_col = next(c for c in df.columns if 'משתמש' in c)
    df = df.rename(columns={user_col: 'משתמש'})
    df = df[df['משתמש'].notna() & ~df['משתמש'].astype(str).str.startswith('סה"כ')]
    occ_col = next((c for c in df.columns if 'תעסוקה' in c), None)
    if occ_col is None:
        raise KeyError(f"לא נמצאה עמודת תעסוקה. עמודות: {list(df.columns)}")
    df = df.rename(columns={occ_col: 'אחוז תעסוקה נטו'})
    occ = 'אחוז תעסוקה נטו'
    if not pd.api.types.is_float_dtype(df[occ]) and not pd.api.types.is_integer_dtype(df[occ]):
        df[occ] = (df[occ].astype(str)
                          .str.replace('%', '', regex=False)
                          .str.strip()
                          .pipe(pd.to_numeric, errors='coerce') / 100)
    answered_col = next((c for c in df.columns if 'נענו' in c), None)
    if answered_col:
        df = df.rename(columns={answered_col: 'נענו'})
    df['נענו'] = pd.to_numeric(df.get('נענו', 0), errors='coerce').fillna(0).astype(int)
    return df.reset_index(drop=True)


def parse_feedback(filepath: str) -> dict:
    scores = {}
    with pd.ExcelFile(filepath, engine='openpyxl') as xl:
        for sheet in xl.sheet_names:
            df = xl.parse(sheet, header=None)
            mask = df.iloc[:, 0].astype(str).str.contains('ציון משוב', na=False)
            if mask.any():
                score = pd.to_numeric(df.iloc[mask.idxmax(), 1], errors='coerce')
                if not pd.isna(score):
                    scores[sheet] = float(score)
    return scores
