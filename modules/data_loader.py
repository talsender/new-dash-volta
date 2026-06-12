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
    raw = None
    for enc in ('utf-16', 'utf-8', 'windows-1255'):
        try:
            tables = pd.read_html(filepath, encoding=enc, header=None)
            if tables:
                raw = tables[0]
                break
        except Exception:
            continue
    if raw is None:
        raise KeyError("לא ניתן לקרוא את קובץ Voicenter")

    raw = raw.astype(str).apply(lambda col: col.str.strip())
    # find the row that contains 'משתמש'
    header_row = None
    for i, row in raw.iterrows():
        if any('משתמש' in str(v) for v in row.values):
            header_row = i
            break
    if header_row is None:
        sample = raw.head(5).to_dict()
        raise KeyError(f"לא נמצאה שורת כותרות עם 'משתמש'. דוגמה: {sample}")

    raw.columns = raw.iloc[header_row].tolist()
    df = raw.iloc[header_row + 1:].reset_index(drop=True)
    df.columns = [str(c).strip() for c in df.columns]

    user_col = next((c for c in df.columns if 'משתמש' in c), None)
    if not user_col:
        raise KeyError(f"עמודות לאחר הגדרת כותרת: {list(df.columns)}")
    df = df.rename(columns={user_col: 'משתמש'})
    df = df[df['משתמש'].notna() & ~df['משתמש'].astype(str).str.startswith('סה"כ') & (df['משתמש'] != 'nan')]

    occ_col = next((c for c in df.columns if 'תעסוקה' in c), None)
    if occ_col is None:
        raise KeyError(f"לא נמצאה עמודת תעסוקה. עמודות: {list(df.columns)}")
    df = df.rename(columns={occ_col: 'אחוז תעסוקה נטו'})
    occ = 'אחוז תעסוקה נטו'
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
