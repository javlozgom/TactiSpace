from __future__ import annotations

import pandas as pd
import streamlit as st

from src.config.settings import MATCH_LABELS_VERSION, MAX_PLOT_EVENTS
from src.ui.cache import get_match_labels_cached
from src.ui.components.insight_card import render_insight_card
from src.ui.layout_kit.navigation import render_button_group
from src.ui.layout_kit.page import render_page_shell
from src.ui.layout_kit.section import render_section_divider
from src.ui.navigation_config import EVENT_ANALYSIS_SECTIONS
from src.ui.views.comparative import render_comparative_analysis
from src.ui.views.events import render_events_view
from src.ui.views.heatmap import render_heatmap_view
from src.ui.views.losses import render_losses_view
from src.ui.views.spatial import render_spatial_analysis_view
from src.ui.views.specific_metrics import render_specific_metrics as render_specific_metrics_view


def _render_section_control(label: str, options: list[str], key: str) -> str:
    """Render one compact section control with a stable active-button state."""
    return render_button_group(label, options, key, columns_per_row=4)


def event_analysis_requires_spatial_data() -> bool:
    """Return whether the current event-analysis subsection needs freeze-frame data."""
    return st.session_state.get("event_analysis_section", EVENT_ANALYSIS_SECTIONS[0]) == EVENT_ANALYSIS_SECTIONS[4]


def render_event_analysis_view(
    *,
    filtered_df: pd.DataFrame,
    events_df: pd.DataFrame,
    freeze_frames_df: pd.DataFrame | None,
    selected_player: object,
    comparative_context_df: pd.DataFrame,
) -> None:
    """Render the grouped event-analysis experience."""
    render_page_shell(
        "🎯 Sistema de análisis",
        "Vista principal de trabajo: reúne análisis de eventos, heatmap, comparativa, pérdidas y análisis espacial.",
        eyebrow="Análisis",
        tone="blue",
    )
    render_insight_card(
        "Qué encontrarás aquí",
        (
            "Esta vista concentra el núcleo analítico de la app. Usa `📏 Métricas específicas` para estudiar un tipo de evento, "
            "`📋 Eventos` para exploración visual, `🌡️ Mapa de calor` para densidad espacial, `⚖️ Comparativa` para contraste "
            "entre contextos, `🗺️ Voronoi/Delaunay` para freeze-frame, Voronoi y Delaunay y `⚠️ Pérdidas` para el bloque integrado de pérdidas y pases fallidos."
        ),
    )
    current_section = _render_section_control(
        "Secciones de Sistema de análisis",
        EVENT_ANALYSIS_SECTIONS,
        key="event_analysis_section",
    )
    render_section_divider()

    if current_section == EVENT_ANALYSIS_SECTIONS[0]:
        render_specific_metrics_view(
            filtered_df,
            selected_player=selected_player,
            context_df=comparative_context_df,
        )
    elif current_section == EVENT_ANALYSIS_SECTIONS[1]:
        render_events_view(filtered_df)
    elif current_section == EVENT_ANALYSIS_SECTIONS[2]:
        render_heatmap_view(filtered_df, max_plot_events=MAX_PLOT_EVENTS)
    elif current_section == EVENT_ANALYSIS_SECTIONS[3]:
        render_comparative_analysis(
            comparative_context_df,
            events_df,
            selected_player,
            match_labels=get_match_labels_cached(MATCH_LABELS_VERSION),
        )
    elif current_section == EVENT_ANALYSIS_SECTIONS[4]:
        render_spatial_analysis_view(events_df, filtered_df, freeze_frames_df)
    else:
        render_losses_view(filtered_df)
