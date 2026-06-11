import pandas as pd


def parse_attendance(filepath: str) -> pd.DataFrame:
    df = pd.read_excel(filepath, sheet_name='וולטה סולאר', engine='openpyxl')
    df['מספר עובד'] = pd.to_numeric(df['מספר עובד'], errors='coerce').astype('Int64')
    df['סה"כ כללי'] = pd.to_numeric(df['סה"כ כללי'], errors='coerce').fillna(0.0)
    return df
