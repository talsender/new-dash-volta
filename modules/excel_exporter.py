# modules/excel_exporter.py
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from modules.config_manager import load_settings
from datetime import datetime

# ── Palette ──────────────────────────────────────────────────────────────────
_C_BRAND_DARK = "0B1E35"   # deep navy  — brand bar, header row, summary row
_C_BRAND_MED  = "1A3A60"   # medium navy — title row
_C_GOLD       = "F5A800"   # Volta gold
_C_WHITE      = "FFFFFF"
_C_ROW_EVEN   = "EDF4FD"   # very light blue stripe
_C_ROW_ODD    = "FFFFFF"   # white
_C_META_BG    = "F4F8FD"   # near-white metadata row
_C_META_FG    = "7090A8"   # muted blue-gray metadata text
_C_GOOD_BG    = "D4EDDA"
_C_GOOD_FG    = "0E5C23"
_C_WARN_BG    = "FFF3CD"
_C_WARN_FG    = "7C5C00"
_C_BAD_BG     = "FAD7DA"
_C_BAD_FG     = "7C1422"
_C_BORDER_CLR = "C8D8E8"   # light blue-gray border

# ── Shared style objects ──────────────────────────────────────────────────────
_THIN      = Side(style='thin',   color=_C_BORDER_CLR)
_GOLD_THIN = Side(style='thin',   color=_C_GOLD)
_GOLD_MED  = Side(style='medium', color=_C_GOLD)

_BORDER     = Border(left=_THIN, right=_THIN, top=_THIN, bottom=_THIN)
_BORDER_HDR = Border(left=_THIN, right=_THIN, top=_GOLD_THIN, bottom=_GOLD_MED)
_BORDER_SUM = Border(left=_THIN, right=_THIN, top=_GOLD_MED,  bottom=_THIN)

_CENTER = Alignment(horizontal='center', vertical='center', readingOrder=2)
_RIGHT  = Alignment(horizontal='right',  vertical='center', readingOrder=2)


def _fill(hex_color):
    return PatternFill("solid", fgColor=hex_color)


def _font(hex_color, bold=False, size=11):
    return Font(color=hex_color, bold=bold, size=size, name="Calibri")


def _status_fill(value, good_thr, warn_thr, higher_is_better=True):
    if higher_is_better:
        if value >= good_thr:  return _C_GOOD_BG, _C_GOOD_FG
        if value >= warn_thr:  return _C_WARN_BG, _C_WARN_FG
    else:
        if value <= good_thr:  return _C_GOOD_BG, _C_GOOD_FG
        if value <= warn_thr:  return _C_WARN_BG, _C_WARN_FG
    return _C_BAD_BG, _C_BAD_FG


def _data_cell(ws, row, col, value, bg=None, fg=None, fmt=None,
               bold=False, align=None):
    if align is None:
        align = _CENTER
    row_bg = _C_ROW_EVEN if row % 2 == 0 else _C_ROW_ODD
    c = ws.cell(row, col, value)
    c.fill      = _fill(bg if bg is not None else row_bg)
    c.font      = _font(fg or _C_BRAND_DARK, bold=bold)
    c.alignment = align
    c.border    = _BORDER
    if fmt:
        c.number_format = fmt
    return c


def _apply_brand_header(ws, title, ncols, meta=""):
    """Write brand bar (row 1), title (row 2), metadata (row 3)."""
    # Row 1 — brand bar
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=ncols)
    c = ws.cell(1, 1, "⚡  Volta Solar  |  מוקד תיאומים")
    c.fill      = _fill(_C_BRAND_DARK)
    c.font      = Font(name="Calibri", bold=True, size=13, color=_C_GOLD)
    c.alignment = _CENTER
    ws.row_dimensions[1].height = 36

    # Row 2 — sheet title
    ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=ncols)
    c2 = ws.cell(2, 1, title)
    c2.fill      = _fill(_C_BRAND_MED)
    c2.font      = Font(name="Calibri", bold=True, size=16, color=_C_WHITE)
    c2.alignment = _CENTER
    ws.row_dimensions[2].height = 32

    # Row 3 — metadata
    ws.merge_cells(start_row=3, start_column=1, end_row=3, end_column=ncols)
    c3 = ws.cell(3, 1, meta)
    c3.fill      = _fill(_C_META_BG)
    c3.font      = Font(name="Calibri", size=9, color=_C_META_FG)
    c3.alignment = _CENTER
    ws.row_dimensions[3].height = 18


def _apply_header(ws, cols):
    """Write column headers to row 4."""
    for ci, val in enumerate(cols, 1):
        c = ws.cell(4, ci, val)
        c.fill      = _fill(_C_BRAND_DARK)
        c.font      = Font(name="Calibri", bold=True, size=11, color=_C_GOLD)
        c.alignment = _CENTER
        c.border    = _BORDER_HDR
    ws.row_dimensions[4].height = 26


def _apply_summary(ws, row, ncols, cells):
    """Gold-on-navy summary row. cells: list of (col, value) or (col, value, fmt)."""
    for ci in range(1, ncols + 1):
        c = ws.cell(row, ci)
        c.fill      = _fill(_C_BRAND_DARK)
        c.font      = _font(_C_GOLD, bold=True)
        c.border    = _BORDER_SUM
        c.alignment = _CENTER
    for entry in cells:
        col, value = entry[0], entry[1]
        fmt = entry[2] if len(entry) > 2 else None
        c = ws.cell(row, col, value)
        c.fill      = _fill(_C_BRAND_DARK)
        c.font      = _font(_C_GOLD, bold=True)
        c.border    = _BORDER_SUM
        c.alignment = _RIGHT if col == 1 else _CENTER
        if fmt:
            c.number_format = fmt
    ws.row_dimensions[row].height = 26


def _setup_print(ws):
    ws.page_setup.orientation = 'landscape'
    ws.page_setup.paperSize   = 9      # A4
    ws.page_setup.fitToPage   = True
    ws.page_setup.fitToWidth  = 1
    ws.page_setup.fitToHeight = 0
    ws.print_options.horizontalCentered = True


def _autofit(ws, overrides=None, min_w=10, max_w=40):
    overrides = overrides or {}
    for col_cells in ws.columns:
        letter = get_column_letter(col_cells[0].column)
        if letter in overrides:
            ws.column_dimensions[letter].width = overrides[letter]
        else:
            length = max(len(str(c.value or "")) for c in col_cells)
            ws.column_dimensions[letter].width = min(max(length + 4, min_w), max_w)


def _init_sheet(ws, title, ncols, meta="", tab_color=None):
    """Configure RTL/gridlines, apply brand header. Returns data start row (5)."""
    ws.sheet_view.rightToLeft   = True
    ws.sheet_view.showGridLines = False
    if tab_color:
        ws.sheet_properties.tabColor = tab_color
    _apply_brand_header(ws, title, ncols, meta)
    return 5  # data rows start here (brand + title + meta + header = rows 1–4)


# ── Weekly KPI ───────────────────────────────────────────────────────────────

def export_weekly_kpi(kpi_data: list, filepath: str) -> None:
    settings  = load_settings()
    t         = settings["bonus_thresholds"]
    mph_good  = t["meetings_per_hour_tier_a"]
    mph_warn  = mph_good * 0.75
    occ_good  = t["occupancy_tier_a_pct"] / 100
    occ_warn  = t["occupancy_tier_b_pct"] / 100
    idle_good = t["idle_tier_a_pct"] / 100
    idle_warn = t["idle_tier_b_pct"] / 100

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "KPI שבועי"

    COLS  = ["נציג", "שעות עבודה", "תיאומים", "פגישות/שעה",
             "תעסוקה %", "סרק %", "פניקס", "שיחות נענו"]
    ncols = len(COLS)
    now   = datetime.now().strftime("%d/%m/%Y %H:%M")

    ds = _init_sheet(ws, "דוח KPI שבועי",
                     ncols=ncols,
                     meta=f"הופק: {now}  |  מספר נציגים: {len(kpi_data)}",
                     tab_color=_C_GOLD)
    _apply_header(ws, COLS)
    ws.freeze_panes = "A5"

    for ri, a in enumerate(kpi_data, ds):
        ws.row_dimensions[ri].height = 22
        row_bg = _C_ROW_EVEN if ri % 2 == 0 else _C_ROW_ODD

        _data_cell(ws, ri, 1, a["name"],            bg=row_bg, align=_RIGHT, bold=True)
        _data_cell(ws, ri, 2, round(a["hours"], 1), bg=row_bg, fmt='0.0')
        _data_cell(ws, ri, 3, a["meetings"],         bg=row_bg)

        mph = round(a["meetings_per_hour"], 2)
        bg, fg = _status_fill(mph, mph_good, mph_warn, higher_is_better=True)
        _data_cell(ws, ri, 4, mph, bg=bg, fg=fg, bold=True, fmt='0.00')

        occ_val = a["occupancy_pct"]
        bg, fg = _status_fill(occ_val, occ_good, occ_warn, higher_is_better=True)
        _data_cell(ws, ri, 5, occ_val, bg=bg, fg=fg, fmt='0.0%')

        idle_val = a["idle_pct"]
        bg, fg = _status_fill(idle_val, idle_good, idle_warn, higher_is_better=False)
        _data_cell(ws, ri, 6, idle_val, bg=bg, fg=fg, fmt='0.00%')

        _data_cell(ws, ri, 7, a["phoenix"],                bg=row_bg)
        _data_cell(ws, ri, 8, a.get("answered_calls", 0),  bg=row_bg)

    # summary row
    n              = len(kpi_data)
    total_meetings = sum(a["meetings"]               for a in kpi_data)
    total_hours    = sum(a["hours"]                  for a in kpi_data)
    total_answered = sum(a.get("answered_calls", 0)  for a in kpi_data)
    total_phoenix  = sum(a["phoenix"]                for a in kpi_data)
    center_mph     = round(total_meetings / total_hours, 2) if total_hours else 0
    avg_occ        = sum(a["occupancy_pct"] for a in kpi_data) / n if n else 0
    avg_idle       = sum(a["idle_pct"]      for a in kpi_data) / n if n else 0

    occ_bg, occ_fg   = _status_fill(avg_occ,  occ_good,  occ_warn,  higher_is_better=True)
    idle_bg, idle_fg = _status_fill(avg_idle, idle_good, idle_warn, higher_is_better=False)
    mph_bg,  mph_fg  = _status_fill(center_mph, mph_good, mph_warn, higher_is_better=True)

    sr = len(kpi_data) + ds
    _apply_summary(ws, sr, ncols, [
        (1, "סיכום מוקד"),
        (2, round(total_hours, 1),  "0.0"),
        (3, total_meetings),
        (4, center_mph,             "0.00"),
        (7, total_phoenix),
        (8, total_answered),
    ])
    # occupancy and idle get their own colors in the summary
    for col, val, fmt, bg, fg in [
        (5, avg_occ,  '0.0%',  occ_bg,  occ_fg),
        (6, avg_idle, '0.00%', idle_bg, idle_fg),
    ]:
        c = ws.cell(sr, col, val)
        c.fill = _fill(bg); c.font = _font(fg, bold=True)
        c.border = _BORDER_SUM; c.alignment = _CENTER
        c.number_format = fmt

    _autofit(ws, overrides={"A": 22, "B": 16, "C": 14, "D": 16,
                             "E": 14, "F": 14, "G": 12, "H": 16})
    _setup_print(ws)
    wb.save(filepath)


# ── Monthly Bonus ─────────────────────────────────────────────────────────────

def export_monthly_bonus(bonus_data: list, billing: dict,
                         month_label: str, filepath: str) -> None:
    now = datetime.now().strftime("%d/%m/%Y %H:%M")

    wb = openpyxl.Workbook()
    wb.remove(wb.active)

    # ── Sheet 1: לתשלום ─────────────────────────────────────────────────────
    ws1   = wb.create_sheet("לתשלום")
    COLS1 = ["שם נציג", "מספר עובד", "בונוס לתשלום (₪)"]
    n1    = len(COLS1)
    ds1   = _init_sheet(
        ws1,
        title=f"בונוסים לתשלום  |  {month_label}",
        ncols=n1,
        meta=f"הופק: {now}  |  מספר נציגים: {len(bonus_data)}",
        tab_color=_C_BRAND_DARK,
    )
    _apply_header(ws1, COLS1)
    ws1.freeze_panes = "A5"

    for ri, b in enumerate(bonus_data, ds1):
        row_bg = _C_ROW_EVEN if ri % 2 == 0 else _C_ROW_ODD
        ws1.row_dimensions[ri].height = 22
        _data_cell(ws1, ri, 1, b["name"],        bg=row_bg, align=_RIGHT, bold=True)
        _data_cell(ws1, ri, 2, b["employee_id"], bg=row_bg)
        total = b["total"]
        bg, fg = ((_C_GOOD_BG, _C_GOOD_FG) if total >= 1500
                  else (_C_WARN_BG, _C_WARN_FG) if total >= 800
                  else (_C_BAD_BG, _C_BAD_FG))
        _data_cell(ws1, ri, 3, total, bg=bg, fg=fg, bold=True, fmt='#,##0 ₪')

    _apply_summary(ws1, len(bonus_data) + ds1, n1, [
        (1, 'סה"כ לתשלום'),
        (3, sum(b["total"] for b in bonus_data), '#,##0 ₪'),
    ])
    _autofit(ws1, overrides={"A": 24, "B": 14, "C": 22})
    _setup_print(ws1)

    # ── Sheet 2: פירוט בונוסים ───────────────────────────────────────────────
    ws2   = wb.create_sheet("פירוט בונוסים")
    COLS2 = ["שם נציג", "תיאומים", "תעסוקה", "סרק",
             "משוב", "פניקס", 'סה"כ']
    n2    = len(COLS2)
    ds2   = _init_sheet(
        ws2,
        title=f"פירוט בונוסים  |  {month_label}",
        ncols=n2,
        meta=f"הופק: {now}  |  מספר נציגים: {len(bonus_data)}",
        tab_color="1B5FAA",
    )
    _apply_header(ws2, COLS2)
    ws2.freeze_panes = "A5"

    BONUS_KEYS = ["meetings_bonus", "occupancy_bonus", "idle_bonus",
                  "feedback_bonus", "phoenix_bonus", "total"]
    for ri, b in enumerate(bonus_data, ds2):
        row_bg = _C_ROW_EVEN if ri % 2 == 0 else _C_ROW_ODD
        ws2.row_dimensions[ri].height = 22
        _data_cell(ws2, ri, 1, b["name"], bg=row_bg, align=_RIGHT, bold=True)
        for ci, key in enumerate(BONUS_KEYS, 2):
            val  = b[key]
            bold = (key == "total")
            if key == "total":
                bg, fg = ((_C_GOOD_BG, _C_GOOD_FG) if val >= 1500
                          else (_C_WARN_BG, _C_WARN_FG) if val >= 800
                          else (_C_BAD_BG, _C_BAD_FG))
            elif val > 0:
                bg, fg = _C_GOOD_BG, _C_GOOD_FG
            else:
                bg, fg = row_bg, _C_META_FG
            _data_cell(ws2, ri, ci, val, bg=bg, fg=fg, bold=bold, fmt='#,##0 ₪')

    _apply_summary(ws2, len(bonus_data) + ds2, n2, [
        (1, 'סה"כ'),
        (7, sum(b["total"] for b in bonus_data), '#,##0 ₪'),
    ])
    _autofit(ws2, overrides={"A": 24})
    _setup_print(ws2)

    # ── Sheet 3: חיוב ללקוח ─────────────────────────────────────────────────
    ws3   = wb.create_sheet("חיוב ללקוח")
    COLS3 = ["נציג", "שעות עבודה"]
    n3    = len(COLS3)
    ds3   = _init_sheet(
        ws3,
        title=f"חיוב ללקוח  |  {month_label}",
        ncols=n3,
        meta=f"הופק: {now}  |  פניקס: {billing.get('phoenix_count', 0)} עסקאות",
        tab_color=_C_GOLD,
    )
    _apply_header(ws3, COLS3)
    ws3.freeze_panes = "A5"

    for ri, (name, hours) in enumerate(billing["hours_by_agent"].items(), ds3):
        row_bg = _C_ROW_EVEN if ri % 2 == 0 else _C_ROW_ODD
        ws3.row_dimensions[ri].height = 22
        _data_cell(ws3, ri, 1, name,            bg=row_bg, align=_RIGHT, bold=True)
        _data_cell(ws3, ri, 2, round(hours, 1), bg=row_bg, fmt='0.0')

    sr3 = len(billing["hours_by_agent"]) + ds3
    _apply_summary(ws3, sr3, n3, [
        (1, 'סה"כ שעות'),
        (2, round(billing["total_hours"], 1), '0.0'),
    ])
    _apply_summary(ws3, sr3 + 1, n3, [
        (1, f'פניקס ({billing.get("phoenix_count", 0)} עסקאות)'),
        (2, billing.get("phoenix_billing", 0), '#,##0 ₪'),
    ])
    _autofit(ws3, overrides={"A": 28, "B": 18})
    _setup_print(ws3)

    wb.save(filepath)
