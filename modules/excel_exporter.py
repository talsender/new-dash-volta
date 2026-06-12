# modules/excel_exporter.py
import openpyxl
from openpyxl.styles import (Font, PatternFill, Alignment, Border, Side,
                              GradientFill)
from openpyxl.utils import get_column_letter
from modules.config_manager import load_settings

# ── Palette ────────────────────────────────────────────────────────────────
_C_HEADER_BG  = "1F4E79"   # dark navy
_C_HEADER_FG  = "FFFFFF"
_C_TITLE_BG   = "F5A800"   # Volta orange
_C_TITLE_FG   = "1F1F1F"
_C_ROW_ALT    = "EBF3FB"   # light blue stripe
_C_ROW_MAIN   = "FFFFFF"
_C_GOOD_BG    = "C6EFCE"   # green
_C_GOOD_FG    = "276221"
_C_WARN_BG    = "FFEB9C"   # yellow
_C_WARN_FG    = "7D5A00"
_C_BAD_BG     = "FFC7CE"   # red
_C_BAD_FG     = "9C0006"
_C_TOTAL_BG   = "D9E1F2"   # summary row
_C_TOTAL_FG   = "1F4E79"
_C_BORDER     = "BFBFBF"

_THIN = Side(style='thin', color=_C_BORDER)
_BORDER = Border(left=_THIN, right=_THIN, top=_THIN, bottom=_THIN)
_THICK_BOTTOM = Border(left=_THIN, right=_THIN, top=_THIN,
                       bottom=Side(style='medium', color=_C_HEADER_BG))

_CENTER = Alignment(horizontal='center', vertical='center',
                    wrap_text=False, readingOrder=2)
_RIGHT  = Alignment(horizontal='right',  vertical='center', readingOrder=2)
_LEFT   = Alignment(horizontal='left',   vertical='center', readingOrder=2)

RTL_SHEET_VIEW = {"rightToLeft": True}


def _fill(hex_color):
    return PatternFill("solid", fgColor=hex_color)


def _font(hex_color, bold=False, size=11):
    return Font(color=hex_color, bold=bold, size=size, name="Calibri")


def _apply_title(ws, text, ncols):
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=ncols)
    c = ws.cell(1, 1, text)
    c.fill = _fill(_C_TITLE_BG)
    c.font = _font(_C_TITLE_FG, bold=True, size=14)
    c.alignment = _CENTER
    c.border = _BORDER
    ws.row_dimensions[1].height = 28


def _apply_header(ws, row, cols):
    for ci, val in enumerate(cols, 1):
        c = ws.cell(row, ci, val)
        c.fill   = _fill(_C_HEADER_BG)
        c.font   = _font(_C_HEADER_FG, bold=True)
        c.alignment = _CENTER
        c.border = _THICK_BOTTOM
    ws.row_dimensions[row].height = 22


def _status_fill(value, good_threshold, warn_threshold, higher_is_better=True):
    """Return (bg, fg) hex based on whether higher/lower is better."""
    if higher_is_better:
        if value >= good_threshold:
            return _C_GOOD_BG, _C_GOOD_FG
        if value >= warn_threshold:
            return _C_WARN_BG, _C_WARN_FG
        return _C_BAD_BG, _C_BAD_FG
    else:
        if value <= good_threshold:
            return _C_GOOD_BG, _C_GOOD_FG
        if value <= warn_threshold:
            return _C_WARN_BG, _C_WARN_FG
        return _C_BAD_BG, _C_BAD_FG


def _data_cell(ws, row, col, value, bg=None, fg=None, fmt=None,
               bold=False, align=_CENTER):
    c = ws.cell(row, col, value)
    c.fill   = _fill(bg) if bg else _fill(_C_ROW_MAIN if row % 2 == 0 else _C_ROW_ALT)
    c.font   = _font(fg or _C_HEADER_BG, bold=bold)
    c.alignment = align
    c.border = _BORDER
    if fmt:
        c.number_format = fmt
    return c


def _autofit(ws, min_w=10, max_w=35):
    for col_cells in ws.columns:
        length = max(len(str(c.value or "")) for c in col_cells)
        ws.column_dimensions[get_column_letter(col_cells[0].column)].width = \
            min(max(length + 4, min_w), max_w)


def _rtl(ws):
    ws.sheet_view.rightToLeft = True


# ── Weekly KPI ─────────────────────────────────────────────────────────────

def export_weekly_kpi(kpi_data: list, filepath: str) -> None:
    settings  = load_settings()
    t         = settings["bonus_thresholds"]
    mph_good  = t["meetings_per_hour_tier_a"]          # 1.0
    mph_warn  = t.get("meetings_per_hour_tier_a", 1.0) * 0.75
    occ_good  = t["occupancy_tier_a_pct"] / 100        # 0.35
    occ_warn  = t["occupancy_tier_b_pct"] / 100        # 0.30
    idle_good = t["idle_tier_a_pct"] / 100             # 0.02
    idle_warn = t["idle_tier_b_pct"] / 100             # 0.03

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "KPI שבועי"
    _rtl(ws)

    COLS = ["נציג", "שעות עבודה", "תיאומים", "פגישות/שעה",
            "תעסוקה %", "סרק %", "פניקס", "שיחות נענו"]
    _apply_title(ws, "דוח KPI שבועי — וולטה סולאר", len(COLS))
    _apply_header(ws, 2, COLS)
    ws.freeze_panes = "A3"

    for ri, a in enumerate(kpi_data, 3):
        row_bg = _C_ROW_ALT if ri % 2 == 0 else _C_ROW_MAIN

        _data_cell(ws, ri, 1, a["name"],    bg=row_bg, align=_RIGHT, bold=True)
        _data_cell(ws, ri, 2, round(a["hours"], 1), bg=row_bg, fmt='0.0')

        # meetings
        _data_cell(ws, ri, 3, a["meetings"], bg=row_bg)

        # meetings/hour — colored by threshold
        mph = round(a["meetings_per_hour"], 2)
        bg, fg = _status_fill(mph, mph_good, mph_warn, higher_is_better=True)
        _data_cell(ws, ri, 4, mph, bg=bg, fg=fg, bold=True, fmt='0.00')

        # occupancy — colored
        occ_val = a["occupancy_pct"]
        bg, fg = _status_fill(occ_val, occ_good, occ_warn, higher_is_better=True)
        _data_cell(ws, ri, 5, occ_val, bg=bg, fg=fg, fmt='0.0%')

        # idle — colored (lower is better)
        idle_val = a["idle_pct"]
        bg, fg = _status_fill(idle_val, idle_good, idle_warn, higher_is_better=False)
        _data_cell(ws, ri, 6, idle_val, bg=bg, fg=fg, fmt='0.00%')

        _data_cell(ws, ri, 7, a["phoenix"],        bg=row_bg)
        _data_cell(ws, ri, 8, a.get("answered_calls", 0), bg=row_bg)

    # summary row
    sr = len(kpi_data) + 3
    ws.row_dimensions[sr].height = 20
    total_meetings = sum(a["meetings"] for a in kpi_data)
    total_hours    = sum(a["hours"]    for a in kpi_data)
    center_mph     = round(total_meetings / total_hours, 2) if total_hours else 0
    bg_s, fg_s = _status_fill(center_mph, mph_good, mph_warn, higher_is_better=True)

    for ci in range(1, len(COLS) + 1):
        c = ws.cell(sr, ci)
        c.fill   = _fill(_C_TOTAL_BG)
        c.font   = _font(_C_TOTAL_FG, bold=True)
        c.border = _BORDER
        c.alignment = _CENTER
    ws.cell(sr, 1, "סיכום").alignment = _RIGHT
    ws.cell(sr, 2, round(total_hours, 1)).number_format = '0.0'
    ws.cell(sr, 3, total_meetings)
    c = ws.cell(sr, 4, center_mph)
    c.fill = _fill(bg_s); c.font = _font(fg_s, bold=True)
    c.number_format = '0.00'

    _autofit(ws)
    wb.save(filepath)


# ── Monthly Bonus ───────────────────────────────────────────────────────────

def export_monthly_bonus(bonus_data: list, billing: dict,
                         month_label: str, filepath: str) -> None:
    wb = openpyxl.Workbook()
    wb.remove(wb.active)

    # ── Sheet 1: לתשלום ──────────────────────────────────────────────────
    ws1 = wb.create_sheet("לתשלום")
    _rtl(ws1)
    COLS1 = ["שם נציג", "מספר עובד", "בונוס לתשלום (₪)"]
    _apply_title(ws1, f"בונוסים לתשלום — {month_label}", len(COLS1))
    _apply_header(ws1, 2, COLS1)
    ws1.freeze_panes = "A3"

    for ri, b in enumerate(bonus_data, 3):
        row_bg = _C_ROW_ALT if ri % 2 == 0 else _C_ROW_MAIN
        _data_cell(ws1, ri, 1, b["name"],        bg=row_bg, align=_RIGHT, bold=True)
        _data_cell(ws1, ri, 2, b["employee_id"], bg=row_bg)
        total = b["total"]
        if total >= 1500:
            bg, fg = _C_GOOD_BG, _C_GOOD_FG
        elif total >= 800:
            bg, fg = _C_WARN_BG, _C_WARN_FG
        else:
            bg, fg = _C_BAD_BG,  _C_BAD_FG
        _data_cell(ws1, ri, 3, total, bg=bg, fg=fg, bold=True, fmt='#,##0 ₪')

    # total row
    sr1 = len(bonus_data) + 3
    grand = sum(b["total"] for b in bonus_data)
    for ci in range(1, 4):
        c = ws1.cell(sr1, ci)
        c.fill = _fill(_C_TOTAL_BG); c.font = _font(_C_TOTAL_FG, bold=True)
        c.border = _BORDER; c.alignment = _CENTER
    ws1.cell(sr1, 1, "סה\"כ").alignment = _RIGHT
    ws1.cell(sr1, 3, grand).number_format = '#,##0 ₪'
    _autofit(ws1)

    # ── Sheet 2: פירוט ───────────────────────────────────────────────────
    ws2 = wb.create_sheet("מפרוט")
    _rtl(ws2)
    COLS2 = ["שם", "תיאומים", "תעסוקה", "סרק", "משוב", "פניקס", 'סה"כ']
    _apply_title(ws2, f"מפרוט בונוסים — {month_label}", len(COLS2))
    _apply_header(ws2, 2, COLS2)
    ws2.freeze_panes = "A3"

    BONUS_COLS = ["meetings_bonus", "occupancy_bonus", "idle_bonus",
                  "feedback_bonus", "phoenix_bonus", "total"]
    for ri, b in enumerate(bonus_data, 3):
        row_bg = _C_ROW_ALT if ri % 2 == 0 else _C_ROW_MAIN
        _data_cell(ws2, ri, 1, b["name"], bg=row_bg, align=_RIGHT, bold=True)
        for ci, key in enumerate(BONUS_COLS, 2):
            val = b[key]
            bg = row_bg
            fg = None
            if val > 0 and key != "total":
                bg, fg = _C_GOOD_BG, _C_GOOD_FG
            elif val == 0 and key != "total":
                bg, fg = _C_BAD_BG, _C_BAD_FG
            if key == "total":
                bold = True
                if val >= 1500:
                    bg, fg = _C_GOOD_BG, _C_GOOD_FG
                elif val >= 800:
                    bg, fg = _C_WARN_BG, _C_WARN_FG
                else:
                    bg, fg = _C_BAD_BG, _C_BAD_FG
            else:
                bold = False
            _data_cell(ws2, ri, ci, val, bg=bg, fg=fg, bold=bold, fmt='#,##0 ₪')
    _autofit(ws2)

    # ── Sheet 3: חיוב ללקוח ─────────────────────────────────────────────
    ws3 = wb.create_sheet("חיוב ללקוח")
    _rtl(ws3)
    COLS3 = ["נציג", "שעות"]
    _apply_title(ws3, f"חיוב ללקוח — {month_label}", len(COLS3))
    _apply_header(ws3, 2, COLS3)
    ws3.freeze_panes = "A3"

    for ri, (name, hours) in enumerate(billing["hours_by_agent"].items(), 3):
        row_bg = _C_ROW_ALT if ri % 2 == 0 else _C_ROW_MAIN
        _data_cell(ws3, ri, 1, name,          bg=row_bg, align=_RIGHT, bold=True)
        _data_cell(ws3, ri, 2, round(hours,1), bg=row_bg, fmt='0.0')

    sr3 = len(billing["hours_by_agent"]) + 3
    for row_offset, (label, val, fmt) in enumerate([
        ('סה"כ שעות',   round(billing["total_hours"], 1), '0.0'),
        (f'פניקס ({billing["phoenix_count"]} עסקאות)',
         billing["phoenix_billing"], '#,##0 ₪'),
    ]):
        r = sr3 + row_offset
        for ci in range(1, 3):
            c = ws3.cell(r, ci)
            c.fill = _fill(_C_TOTAL_BG); c.font = _font(_C_TOTAL_FG, bold=True)
            c.border = _BORDER; c.alignment = _CENTER
        ws3.cell(r, 1, label).alignment = _RIGHT
        ws3.cell(r, 2, val).number_format = fmt
    _autofit(ws3)

    wb.save(filepath)
