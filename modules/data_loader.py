import pandas as pd


def parse_attendance(filepath: str) -> pd.DataFrame:
    xl = pd.ExcelFile(filepath, engine='openpyxl')
    sheet = next((s for s in xl.sheet_names if 'וולטה' in s), xl.sheet_names[0])
    df = xl.parse(sheet)
    df.columns = [str(c).strip() for c in df.columns]
    # find employee-id column flexibly
    emp_col = next((c for c in df.columns if 'מספר' in c and 'עובד' in c), None)
    if emp_col is None:
        raise KeyError(f"לא נמצאה עמודת 'מספר עובד'. עמודות קיימות: {list(df.columns)}")
    df['מספר עובד'] = pd.to_numeric(df[emp_col], errors='coerce').astype('Int64')
    # find total-hours column flexibly
    hours_col = next((c for c in df.columns if 'סה"כ' in c or 'סהכ' in c or 'כללי' in c), None)
    if hours_col is None:
        raise KeyError(f"לא נמצאה עמודת סה\"כ שעות. עמודות קיימות: {list(df.columns)}")
    df['סה"כ כללי'] = pd.to_numeric(df[hours_col], errors='coerce').fillna(0.0)
    return df


def parse_voicenter(filepath: str) -> pd.DataFrame:
    tables = pd.read_html(filepath, encoding='utf-16')
    df = tables[0]
    # Drop summary rows (totals have no user name or are labeled סה"כ)
    df = df[df['משתמש'].notna() & ~df['משתמש'].astype(str).str.startswith('סה"כ')]
    occ = 'אחוז תעסוקה נטו'
    # pandas 3.x returns StringDtype ('str') for string columns, not object
    if not pd.api.types.is_float_dtype(df[occ]) and not pd.api.types.is_integer_dtype(df[occ]):
        df[occ] = (df[occ].astype(str)
                          .str.replace('%', '', regex=False)
                          .str.strip()
                          .pipe(pd.to_numeric, errors='coerce') / 100)
    df['נענו'] = pd.to_numeric(df['נענו'], errors='coerce').fillna(0).astype(int)
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
