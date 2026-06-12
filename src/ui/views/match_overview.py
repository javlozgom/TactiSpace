from __future__ import annotations

import pandas as pd

from src.ui.components.insight_card import render_insight_card
from src.ui.layout_kit.navigation import render_button_group
from src.ui.layout_kit.page import render_page_shell
from src.ui.layout_kit.section import render_section_divider
from src.ui.navigation_config import MATCH_OVERVIEW_SECTIONS
from src.ui.views.guide import render_guide_view
from src.ui.views.home import render_home_view
from src.ui.views.summary import render_summary_view


def _render_section_control(label: str, options: list[str], key: str) -> str:
    """Render one compact section control with a stable active-button state."""
    return render_button_group(label, options, key, columns_per_row=3)


def render_match_overview_view(
    filtered_df: pd.DataFrame,
    events_df: pd.DataFrame,
    freeze_frames_df: pd.DataFrame | None,
    metrics: dict[str, object],
    selected_match: object,
    selected_team: object,
    selected_player: object,
    position_context_df: pd.DataFrame,
    spatial_events_count: int,
) -> None:
    """Render the grouped match-overview experience."""
    render_page_shell(
        "🏟️ Vista general",
        "Vista principal de contexto: reúne dashboard general, resumen descriptivo y guía de uso para interpretar la app.",
        eyebrow="Contexto",
        tone="blue",
    )
    render_insight_card(
        "Qué encontrarás aquí",
        (
            "Esta vista agrupa la entrada general a la app. Usa `🏠 Inicio` para orientación rápida, "
            "`📊 Resumen` para lectura descriptiva del contexto y `📘 Guía` para documentación e interpretación."
        ),
    )
    current_section = _render_section_control(
        "Secciones de Vista general",
        MATCH_OVERVIEW_SECTIONS,
        key="match_overview_section",
    )
    render_section_divider()

    if current_section == MATCH_OVERVIEW_SECTIONS[0]:
        render_home_view(
            filtered_df,
            events_df,
            freeze_frames_df,
            metrics,
            selected_match,
            selected_team,
            selected_player,
            spatial_events_count=spatial_events_count,
        )
    elif current_section == MATCH_OVERVIEW_SECTIONS[1]:
        render_summary_view(filtered_df, metrics, selected_player, position_context_df)
    else:
        render_guide_view()
