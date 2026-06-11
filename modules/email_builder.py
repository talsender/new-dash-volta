# modules/email_builder.py
_TH = 'background:#1F4E79;color:#fff;padding:8px 12px;border:1px solid #ccc;text-align:center'
_TD = 'padding:8px 12px;border:1px solid #ccc;text-align:center'
_TABLE = 'border-collapse:collapse;width:100%;direction:rtl;font-family:Arial,sans-serif'
_WRAP = '<div style="direction:rtl;font-family:Arial,sans-serif;padding:20px">{}</div>'


def _table(headers, rows):
    ths = ''.join(f'<th style="{_TH}">{h}</th>' for h in headers)
    trs = ''.join(
        '<tr>' + ''.join(f'<td style="{_TD}">{v}</td>' for v in row) + '</tr>'
        for row in rows
    )
    return f'<table style="{_TABLE}"><thead><tr>{ths}</tr></thead><tbody>{trs}</tbody></table>'


def build_weekly_management_email(kpi_data: list, week_label: str) -> str:
    rows = [[a['name'], f"{a['hours']:.1f}", a['meetings'],
             f"{a['meetings_per_hour']:.2f}", f"{a['occupancy_pct']*100:.1f}%",
             f"{a['idle_pct']*100:.2f}%", a['phoenix']] for a in kpi_data]
    table = _table(['נציג','שעות','תיאומים','פגישות/שעה','תעסוקה','סרק','פניקס'], rows)
    return _WRAP.format(f'<h2>דוח KPI שבועי — {week_label}</h2>{table}')


def build_weekly_agent_email(agent_kpi: dict, agent_name: str, week_label: str) -> str:
    a = agent_kpi
    rows = [['שעות', f"{a['hours']:.1f}"], ['תיאומים', a['meetings']],
            ['פגישות/שעה', f"{a['meetings_per_hour']:.2f}"],
            ['תעסוקה', f"{a['occupancy_pct']*100:.1f}%"],
            ['סרק', f"{a['idle_pct']*100:.2f}%"], ['פניקס', a['phoenix']]]
    table = _table(['מדד', 'ערך'], rows)
    return _WRAP.format(f'<h2>שלום {agent_name},</h2><p>דוח ביצועים — {week_label}</p>{table}')


def build_monthly_client_email(billing: dict, month_label: str) -> str:
    rows = [['שעות עבודה', f"{billing['total_hours']:.1f}", '—'],
            ['פניקס', billing['phoenix_count'], f"₪{billing['phoenix_billing']:,}"]]
    table = _table(['פריט', 'כמות', 'עלות'], rows)
    return _WRAP.format(f'<h2>חיוב חודשי — {month_label}</h2>{table}<p>מצורף Excel מפורט.</p>')


def build_monthly_agent_email(agent_kpi: dict, agent_bonus: dict,
                               agent_name: str, month_label: str) -> str:
    b = agent_bonus
    rows = [['תיאומים', f"₪{b['meetings_bonus']:,}"],
            ['תעסוקה', f"₪{b['occupancy_bonus']:,}"],
            ['סרק', f"₪{b['idle_bonus']:,}"],
            ['משוב', f"₪{b['feedback_bonus']:,}"],
            ['פניקס', f"₪{b['phoenix_bonus']:,}"],
            ['<b>סה"כ</b>', f"<b>₪{b['total']}</b>"]]
    table = _table(['רכיב', 'סכום'], rows)
    return _WRAP.format(f'<h2>שלום {agent_name},</h2><p>פירוט בונוס — {month_label}</p>{table}')
