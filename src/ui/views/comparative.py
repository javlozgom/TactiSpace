from __future__ import annotations

import pandas as pd
import streamlit as st

from src.services.events_service import get_supported_specific_metric_events
from src.core.models.player_labels import build_player_label_maps
from src.ui.comparison_advanced_view import render_advanced_comparison
from src.ui.comparison_basic_view import render_basic_comparisons
from src.ui.components import render_context_bar, render_page_header
from src.ui.views.percentiles import render_percentiles_section


def render_comparative_analysis(
    filtered_df: pd.DataFrame,
    full_df: pd.DataFrame,
    selected_player: str | None,
    match_labels: dict[str, str] | None = None,
) -> None:
    """Render the comparative analysis tab."""
    render_page_header(
        "Comparativa",
        "Compara el rendimiento de un jugador frente al contexto del equipo, entre jugadores o entre partidos y equipos distintos.",
        eyebrow="Comparativa",
    )
    render_context_bar(
        [
            {"label": "Eventos", "value": len(filtered_df)},
            {"label": "Jugador activo", "value": selected_player or "Todos"},
            {"label": "Partidos", "value": filtered_df["match_id"].nunique() if not filtered_df.empty else 0},
        ]
    )

    supported_events = _get_event_options(filtered_df, full_df)
    filtered_name_map, _ = build_player_label_maps(filtered_df)
    full_name_map, _ = build_player_label_maps(full_df)

    render_basic_comparisons(
        filtered_df=filtered_df,
        selected_player=selected_player,
        supported_events=supported_events,
        filtered_name_map=filtered_name_map,
    )

    st.divider()
    render_advanced_comparison(
        full_df=full_df,
        supported_events=supported_events,
        full_name_map=full_name_map,
        match_labels=match_labels or {},
    )

    st.divider()
    render_percentiles_section(filtered_df=filtered_df, full_df=full_df)


def _get_event_options(filtered_df: pd.DataFrame, full_df: pd.DataFrame) -> list[str]:
    """Return supported event options for the comparative view."""
    source_df = filtered_df if not filtered_df.empty else full_df
    dataset_events = (
        sorted(source_df["event_type"].dropna().astype(str).unique().tolist())
        if not source_df.empty and "event_type" in source_df.columns
        else []
    )
    supported_events = get_supported_specific_metric_events()
    if not supported_events:
        return dataset_events

    ordered_events: list[str] = []
    seen: set[str] = set()
    for event_type in [*supported_events, *dataset_events]:
        if event_type not in seen:
            ordered_events.append(event_type)
            seen.add(event_type)
    return ordered_events
