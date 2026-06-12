from __future__ import annotations

import pandas as pd
import streamlit as st

from src.ui.components import (
    render_context_bar,
    render_empty_state,
    render_info_box,
    render_page_header,
    render_plot_card,
    render_section_header,
)
from src.ui.components.visualizations import plot_event_heatmap


def get_selected_event_types_for_heatmap(filtered_df: pd.DataFrame) -> str | None:
    """Render a local single-event control for the Heatmap view."""
    available_event_types = sorted(filtered_df["event_type"].dropna().unique().tolist())
    if not available_event_types:
        return None

    working_selection = st.session_state.get("heatmap_view_event_types_working")
    if working_selection is None or working_selection not in available_event_types:
        st.session_state["heatmap_view_event_types_working"] = available_event_types[0]

    with st.container(border=True):
        st.pills(
            "Evento del mapa de calor",
            options=available_event_types,
            selection_mode="single",
            help="Selecciona el tipo de evento que quieres usar para construir el mapa de calor.",
            key="heatmap_view_event_types_working",
        )
    return st.session_state.get("heatmap_view_event_types_working")


def render_heatmap_view(filtered_df: pd.DataFrame, max_plot_events: int = 600) -> None:
    """Render the heatmap view."""
    render_page_header(
        "Mapa de calor",
        "Concentración espacial de eventos.",
        eyebrow="Heatmap",
    )
    if filtered_df.empty:
        render_empty_state(
            "No hay eventos para construir el mapa de calor.",
            "Prueba a ampliar el rango de minutos o revisar partido, equipo y jugador.",
        )
        return

    render_section_header("Selector de evento", "Escoge el tipo de acción que alimenta el mapa de calor.")
    selected_event_type = get_selected_event_types_for_heatmap(filtered_df)
    if not selected_event_type:
        render_empty_state(
            "No hay tipos de evento disponibles para el mapa de calor.",
            "Selecciona un contexto con eventos registrados.",
        )
        return

    heatmap_df = filtered_df[filtered_df["event_type"] == selected_event_type].copy()
    if heatmap_df.empty:
        render_empty_state(
            "No hay eventos de este tipo para el contexto seleccionado.",
            "Prueba con otro tipo de evento o amplia el contexto.",
        )
        return

    render_context_bar(
        [
            {"label": "Evento", "value": selected_event_type},
            {"label": "Eventos usados", "value": f"{len(heatmap_df):,}"},
            {"label": "Límite visual", "value": max_plot_events},
        ]
    )
    st.divider()
    fig = plot_event_heatmap(heatmap_df.head(max_plot_events))
    render_plot_card(
        "Heatmap de eventos",
        fig,
        "Mapa construido a partir del contexto filtrado y limitado para mantener el rendimiento.",
    )
    st.divider()
    render_info_box(
        "Interpretación",
        "Las zonas más densas indican dónde se repite con mayor frecuencia el tipo de evento seleccionado.",
        tone="neutral",
    )
