import pandas as pd
import datetime, re


def _parse_hours(val) -> float:
    if isinstance(val, datetime.time):
        return val.hour + val.minute / 60 + val.second / 3600
    if isinstance(val, datetime.timedelta):
        return val.total_seconds() / 3600
    if isinstance(val, (int, float)):
        if pd.isna(val):
            return 0.0
        if 0 < val < 1:
            return val * 24  # Excel fraction of day
        return float(val)
    s = str(val).strip()
    if ':' in s:
        parts = s.split(':')
        try:
            return int(parts[0]) + int(parts[1]) / 60
        except (ValueError, IndexError):
            return 0.0
    try:
        v = float(s)
        return v * 24 if 0 < v < 1 else v
    except (ValueError, TypeError):
        return 0.0


def parse_attendance(filepath: str) -> pd.DataFrame:
    with pd.ExcelFile(filepath, engine='openpyxl') as xl:
        sheet = next((s for s in xl.sheet_names if 'וולטה' in s), xl.sheet_names[0])
        raw = xl.parse(sheet, header=None)
        header_row = next(
            (i for i, row in raw.iterrows()
             if any('מספר' in str(v) and 'עובד' in str(v) for v in row.values)),
            None
        )
        if header_row is None:
            raise KeyError("לא נמצאה שורת כותרות עם 'מספר עובד'")
        df = xl.parse(sheet, header=header_row)
    df.columns = [str(c).strip() for c in df.columns]
    df = df[pd.to_numeric(df['מספר עובד'], errors='coerce').notna()].copy()
    df['מספר עובד'] = pd.to_numeric(df['מספר עובד'], errors='coerce').astype('Int64')
    # sum per-shift columns (סה"כ 1, סה"כ 2, ...) — more reliable than סה"כ כללי
    shift_cols = [c for c in df.columns if re.match(r'סה"כ\s*\d+', c)]
    if shift_cols:
        df['סה"כ כללי'] = sum(df[c].apply(_parse_hours) for c in shift_cols)
    else:
        hours_col = next((c for c in df.columns if 'סה"כ' in c or 'כללי' in c), None)
        if hours_col is None:
            raise KeyError(f"לא נמצאה עמודת שעות. עמודות: {list(df.columns)}")
        df['סה"כ כללי'] = df[hours_col].apply(_parse_hours)
    return df


def _describe_file(filepath: str) -> str:
    """Name the uploaded format, so a failure says what arrived instead of 'cannot read'."""
    with open(filepath, 'rb') as f:
        head = f.read(8)
    if head[:4] == b'%PDF':
        return "PDF"
    if head[:2] == b'PK':
        return "xlsx פגום או ארכיון ZIP"
    if head[:4] == b'\xd0\xcf\x11\xe0':
        return 'xls בינארי ישן'
    if head[:2] in (b'\xff\xfe', b'\xfe\xff') or head[:1] == b'<':
        return "HTML"
    return "טקסט או פורמט לא מזוהה"


def _read_voicenter_table(filepath: str):
    """Voicenter exports an HTML table named .xls. Opening that in Excel and saving
    turns it into a real workbook, and some exports arrive delimited — read all three.
    """
    for enc in ('utf-16', 'utf-8', 'windows-1255'):
        try:
            tables = pd.read_html(filepath, encoding=enc, header=None)
            if tables:
                return tables[0]
        except Exception:
            continue
    try:
        return pd.read_excel(filepath, header=None)
    except Exception:
        pass
    for enc in ('utf-8-sig', 'utf-16', 'windows-1255'):
        for sep in ('\t', ','):
            try:
                df = pd.read_csv(filepath, sep=sep, header=None,
                                 encoding=enc, engine='python')
                if df.shape[1] > 1:
                    return df
            except Exception:
                continue
    return None


def parse_voicenter(filepath: str) -> pd.DataFrame:
    raw = _read_voicenter_table(filepath)
    if raw is None:
        raise KeyError(
            f"לא ניתן לקרוא את קובץ Voicenter — הקובץ נראה כמו {_describe_file(filepath)}. "
            "ייצא מחדש מ-Voicenter, או שמור אותו כ-Excel Workbook (.xlsx)."
        )

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

    # Total incoming calls (כניסות) — distinct from answered (נענו)
    _total_candidates = ['כניסות', 'שיחות נכנסות', 'שיחות']
    total_col = next(
        (c for c in df.columns
         if str(c).strip() in _total_candidates
         or any(t in str(c) for t in _total_candidates)),
        None,
    )
    if total_col and total_col != answered_col:
        df = df.rename(columns={total_col: 'כניסות'})
        df['כניסות'] = pd.to_numeric(df['כניסות'], errors='coerce').fillna(0).astype(int)
    else:
        df['כניסות'] = df['נענו']  # fallback: same as answered

    return df.reset_index(drop=True)


def parse_feedback(filepath: str) -> dict:
    """Returns {agent_name: {'score': float, 'criteria': [...], 'strengths': [...], 'improvements': [...]}}"""
    import openpyxl
    result = {}
    _SKIP = {'.', 'מדדים', 'מדדים '}
    wb = openpyxl.load_workbook(filepath, data_only=True)
    for sname in wb.sheetnames:
        if sname.strip() in _SKIP:
            continue
        ws   = wb[sname]
        agent = sname.strip()
        score = None
        criteria, strengths, improvements = [], [], []
        mode = None  # 'strengths' | 'improvements' | None

        for row in ws.iter_rows(values_only=True):
            if not any(v is not None for v in row):
                continue
            label = str(row[0]).strip() if row[0] is not None else ""

            # Section transitions
            if 'לשימור' in label:
                mode = 'strengths';    continue
            if 'לשיפור' in label:
                mode = 'improvements'; continue
            if any(m in label for m in ('הערות כלליות', 'סיכום שיחה', 'פרטי פניה')):
                mode = None;           continue

            # Overall score (first occurrence only)
            if score is None and 'ציון' in label:
                for v in row[1:6]:
                    try:
                        s = float(v)
                        if 1 <= s <= 10:
                            score = s; break
                        if 10 < s <= 100:
                            score = round(s / 10, 2); break
                    except (TypeError, ValueError):
                        pass
                continue

            # Strength / improvement bullets
            if mode == 'strengths' and label:
                strengths.append(label); continue
            if mode == 'improvements' and label:
                improvements.append(label); continue

            # Criterion row: has numeric scores in cols C-F in range 1-10,
            # and has a description in col B
            if mode is None and label and row[1] is not None:
                call_scores = []
                for v in row[2:6]:
                    try:
                        s = float(v)
                        if 1 <= s <= 10:
                            call_scores.append(round(s, 2))
                    except (TypeError, ValueError):
                        pass
                if call_scores:
                    criteria.append({
                        'label':  label,
                        'scores': call_scores,
                        'avg':    round(sum(call_scores) / len(call_scores), 2),
                    })

        if score is not None or criteria:
            result[agent] = {
                'score':        score,
                'criteria':     criteria,
                'strengths':    strengths[:6],
                'improvements': improvements[:6],
            }
    return result
