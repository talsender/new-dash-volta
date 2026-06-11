# modules/excel_exporter.py
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment

_FILL = PatternFill("solid", fgColor="1F4E79")
_FONT = Font(color="FFFFFF", bold=True)
_CENTER = Alignment(horizontal='center')


def _header(ws, row, cols):
    for c, val in enumerate(cols, 1):
        cell = ws.cell(row, c, val)
        cell.fill = _FILL; cell.font = _FONT; cell.alignment = _CENTER


def export_weekly_kpi(kpi_data: list, filepath: str) -> None:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'KPI שבועי'
    _header(ws, 1, ['נציג', 'שעות', 'תיאומים', 'פגישות/שעה', 'תעסוקה %', 'סרק %', 'פניקס'])
    for i, a in enumerate(kpi_data, 2):
        ws.cell(i, 1, a['name'])
        ws.cell(i, 2, round(a['hours'], 1))
        ws.cell(i, 3, a['meetings'])
        ws.cell(i, 4, round(a['meetings_per_hour'], 2))
        ws.cell(i, 5, f"{a['occupancy_pct']*100:.1f}%")
        ws.cell(i, 6, f"{a['idle_pct']*100:.2f}%")
        ws.cell(i, 7, a['phoenix'])
    wb.save(filepath)


def export_monthly_bonus(bonus_data: list, billing: dict, month_label: str, filepath: str) -> None:
    wb = openpyxl.Workbook()
    wb.remove(wb.active)

    ws1 = wb.create_sheet('לתשלום')
    _header(ws1, 1, ['שם', 'מספר עובד', 'בונוס לתשלום'])
    for i, b in enumerate(bonus_data, 2):
        ws1.cell(i, 1, b['name']); ws1.cell(i, 2, b['employee_id']); ws1.cell(i, 3, b['total'])

    ws2 = wb.create_sheet('מפרוט')
    _header(ws2, 1, ['שם', 'תיאומים', 'תעסוקה', 'סרק', 'משוב', 'פניקס', 'סה"כ'])
    for i, b in enumerate(bonus_data, 2):
        for c, k in enumerate(['name','meetings_bonus','occupancy_bonus','idle_bonus',
                                'feedback_bonus','phoenix_bonus','total'], 1):
            ws2.cell(i, c, b[k])

    ws3 = wb.create_sheet('חיוב ללקוח')
    ws3.cell(1, 1, f'חיוב חודש {month_label}')
    _header(ws3, 2, ['נציג', 'שעות'])
    for i, (name, hours) in enumerate(billing['hours_by_agent'].items(), 3):
        ws3.cell(i, 1, name); ws3.cell(i, 2, round(hours, 1))
    r = len(billing['hours_by_agent']) + 3
    ws3.cell(r, 1, 'סה"כ שעות'); ws3.cell(r, 2, round(billing['total_hours'], 1))
    ws3.cell(r+1, 1, f'פניקס ({billing["phoenix_count"]} עסקאות)')
    ws3.cell(r+1, 2, billing['phoenix_billing'])

    wb.save(filepath)
