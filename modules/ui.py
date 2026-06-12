# modules/ui.py
import streamlit as st


def page_header(title: str, icon: str = "", subtitle: str = ""):
    icon_html = f'<span class="ph-icon">{icon}</span>' if icon else ""
    sub_html  = f'<div class="ph-sub">{subtitle}</div>' if subtitle else ""
    st.markdown(
        f'<div class="kpi-page-header" style="text-align:center;">'
        f'<div style="text-align:center;">{icon_html}<h1 style="display:inline;">{title}</h1></div>'
        f'{sub_html}'
        f'</div>',
        unsafe_allow_html=True,
    )


def section_header(text: str, step: int = None):
    step_html = f'<span class="sh-step">שלב {step}</span>' if step is not None else ""
    st.markdown(
        f'<div class="kpi-section-header">'
        f'{step_html}'
        f'<span class="sh-title">{text}</span>'
        f'<span class="sh-line"></span>'
        f'</div>',
        unsafe_allow_html=True,
    )


def agent_cards(agents: list):
    if not agents:
        return
    cols = st.columns(min(len(agents), 4))
    for col, a in zip(cols, agents):
        with col:
            st.markdown(
                f'<div class="kpi-agent-card" style="text-align:center;">'
                f'<div class="ac-id">מ. עובד {a["employee_id"]}</div>'
                f'<div class="ac-name">{a["name"]}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )


def agent_label(name: str):
    st.markdown(
        f'<div class="kpi-agent-label">{name}</div>',
        unsafe_allow_html=True,
    )
