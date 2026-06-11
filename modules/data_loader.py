import pandas as pd


def parse_attendance(filepath: str) -> pd.DataFrame:
    df = pd.read_excel(filepath, sheet_name='וולטה סולאר', engine='openpyxl')
    df['מספר עובד'] = pd.to_numeric(df['מספר עובד'], errors='coerce').astype('Int64')
    df['סה"כ כללי'] = pd.to_numeric(df['סה"כ כללי'], errors='coerce').fillna(0.0)
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
