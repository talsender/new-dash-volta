import pandas as pd


def parse_attendance(filepath: str) -> pd.DataFrame:
    with pd.ExcelFile(filepath, engine='openpyxl') as xl:
        sheet = next((s for s in xl.sheet_names if 'וולטה' in s), xl.sheet_names[0])
        raw = xl.parse(sheet, header=None)
    raw = raw.astype(str).apply(lambda col: col.str.strip())
    header_row = next(
        (i for i, row in raw.iterrows()
         if any('מספר' in str(v) and 'עובד' in str(v) for v in row.values)),
        None
    )
    if header_row is None:
        raise KeyError(f"לא נמצאה שורת כותרות עם 'מספר עובד'. שורות: {raw.head(3).values.tolist()}")
    raw.columns = [str(v).strip() for v in raw.iloc[header_row]]
    df = raw.iloc[header_row + 1:].reset_index(drop=True)
    df = df[pd.to_numeric(df['מספר עובד'], errors='coerce').notna()].copy()
    df['מספר עובד'] = pd.to_numeric(df['מספר עובד'], errors='coerce').astype('Int64')
    hours_col = next((c for c in df.columns if 'סה"כ' in c or 'סהכ' in c or 'כללי' in c), None)
    if hours_col is None:
        raise KeyError(f"לא נמצאה עמודת שעות. עמודות: {list(df.columns)}")
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
    col_names = [str(c).strip() for c in raw.columns]

    # case 1: pandas already detected headers (e.g. <th> tags)
    if any('משתמש' in c for c in col_names):
        raw.columns = col_names
        df = raw
    else:
        # case 2: all columns are numeric — find header row in values
        header_row = next(
            (i for i, row in raw.iterrows() if any('משתמש' in str(v) for v in row.values)),
            None
        )
        if header_row is None:
            raise KeyError(f"לא נמצאה שורת כותרות עם 'משתמש'. עמודות: {col_names}")
        raw.columns = [str(v).strip() for v in raw.iloc[header_row]]
        df = raw.iloc[header_row + 1:].reset_index(drop=True)

    user_col = next((c for c in df.columns if 'משתמש' in c), None)
    df = df.rename(columns={user_col: 'משתמש'})
    df = df[df['משתמש'].notna() & ~df['משתמש'].astype(str).str.startswith('סה"כ') & (df['משתמש'] != 'nan')]

    occ_col = next((c for c in df.columns if 'תעסוקה' in c), None)
    if occ_col is None:
        raise KeyError(f"לא נמצאה עמודת תעסוקה. עמודות: {list(df.columns)}")
    df = df.rename(columns={occ_col: 'אחוז תעסוקה נטו'})
    df['אחוז תעסוקה נטו'] = (df['אחוז תעסוקה נטו'].astype(str)
                              .str.replace('%', '', regex=False).str.strip()
                              .pipe(pd.to_numeric, errors='coerce') / 100)

    answered_col = next((c for c in df.columns if c == 'נענו' or ('נענו' in c and 'לא' not in c)), None)
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
