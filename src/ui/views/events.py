from __future__ import annotations

import pandas as pd
import streamlit as st

from src.ui.components import (
    render_context_bar,
    render_empty_state,
    render_info_box,
    render_limited_dataframe,
    render_page_header,
    render_plot_card,
    render_section_header,
)
from src.ui.components.visualizations import plot_events_on_pitch


EVENT_EXPLANATIONS = {
    "Pass": "Pase realizado por un jugador. Puede incluir destino, altura, longitud, presión recibida y resultado.",
    "Carry": "Conducción del balón por parte de un jugador entre dos puntos del campo.",
    "Shot": "Remate o intento de finalización hacia portería.",
    "Pressure": "Acción defensiva en la que un jugador presiona al rival con balón o cercano a recibir.",
    "Ball Recovery": "Recuperación de balón por parte del equipo.",
    "Duel": "Disputa individual entre jugadores por el balón o la posición.",
    "Dribble": "Intento de regate para superar a un rival.",
    "Ball Receipt*": "Recepción de balón por parte de un jugador.",
    "Miscontrol": "Control defectuoso del balón que puede provocar pérdida.",
    "Dispossessed": "Pérdida de balón por entrada o presión de un rival.",
    "Interception": "Intercepción de un pase o acción rival.",
    "Clearance": "Despeje defensivo para alejar el balón de zona peligrosa.",
    "Block": "Bloqueo de tiro, pase o acción rival.",
    "Goal Keeper": "Acción específica del portero.",
    "Own Goal For": "Gol en propia puerta a favor del equipo analizado.",
    "Own Goal Against": "Gol en propia puerta en contra del equipo analizado.",
    "Offside": "Acción señalada como fuera de juego.",
}


NON_PLOTTED_EVENT_TYPES = {
    "Injury Stoppage",
    "Half End",
    "Half Start",
    "Player On",
    "Player Off",
    "Starting XI",
    "Substitution",
    "Tactical Shift",
    "Bad Behaviour",
}


def _get_event_type_column(df: pd.DataFrame) -> str | None:
    """Return the first available event type column."""
    for column in ("event_type", "type", "type_name"):
        if column in df.columns:
            return column
    return None


def _format_event_count(visible_count: int, total_count: int) -> str:
    """Format visible events over total events."""
    if total_count <= 0:
        return "0 / 0"
    return f"{visible_count:,} / {total_count:,}"


def get_plottable_event_types(event_types: list[str]) -> list[str]:
    """Return event types that have useful pitch-map representation."""
    return [event_type for event_type in event_types if str(event_type) not in NON_PLOTTED_EVENT_TYPES]


def prepare_events_map_df(df: pd.DataFrame) -> tuple[pd.DataFrame, bool, list[str]]:
    """Prepare the event dataframe used by the map while preserving table data."""
    if df.empty:
        return df.copy(), True, []

    event_type_column = _get_event_type_column(df)
    if event_type_column is None:
        return df.copy(), True, []

    plottable_types = get_plottable_event_types(
        sorted(df[event_type_column].dropna().astype(str).unique().tolist())
    )
    plot_df = df[df[event_type_column].astype(str).isin(plottable_types)].copy()
    return plot_df, True, plottable_types


def _render_event_glossary(selected_events: list[str]) -> None:
    """Render an accessible glossary for selected event types."""
    if not selected_events:
        return

    render_section_header(
        "Guía de lectura de eventos",
        "Definiciones breves para interpretar los eventos seleccionados en el mapa y la tabla.",
    )

    for event_type in selected_events:
        explanation = EVENT_EXPLANATIONS.get(
            event_type,
            "Evento StatsBomb disponible en el dataset. Su interpretación depende del contexto de la jugada.",
        )
        render_info_box(event_type, explanation, tone="neutral")


def _prepare_plot_df(df: pd.DataFrame, event_type_column: str) -> pd.DataFrame:
    """Remove administrative events that are not useful on the pitch map."""
    if df.empty:
        return df.copy()
    return df[~df[event_type_column].astype(str).isin(NON_PLOTTED_EVENT_TYPES)].copy()


def render_events_view(filtered_df: pd.DataFrame) -> None:
    """Render the event explorer view."""
    render_page_header(
        "Eventos",
        "Exploración visual de eventos filtrados sobre el terreno de juego.",
        badge="Exploración",
    )

    if filtered_df.empty:
        render_empty_state(
            "No hay eventos para los filtros seleccionados.",
            "Amplía el rango de minutos o cambia partido, equipo o jugador.",
        )
        return

    event_type_column = _get_event_type_column(filtered_df)
    if event_type_column is None:
        render_empty_state(
            "No se ha encontrado una columna de tipo de evento.",
            "Revisa que el dataset incluya event_type, type o type_name.",
        )
        return

    available_event_types = sorted(
        filtered_df[event_type_column].dropna().astype(str).unique().tolist()
    )

    render_section_header(
        "Selección de eventos",
        "Elige uno o varios tipos de evento para mostrarlos en el mapa y en la tabla.",
    )

    with st.container(border=True):
        default_events = available_event_types[: min(5, len(available_event_types))]
        selected_event_types = st.multiselect(
            "Tipos de evento",
            options=available_event_types,
            default=default_events,
            help="Puedes combinar varios eventos para comparar su distribución espacial.",
        )
    st.divider()

    if not selected_event_types:
        render_empty_state(
            "Selecciona al menos un tipo de evento.",
            "El mapa y la tabla se actualizarán automáticamente.",
        )
        return

    selected_df = filtered_df[
        filtered_df[event_type_column].astype(str).isin(selected_event_types)
    ].copy()

    render_section_header(
        "Resumen de selección",
        "Volumen de eventos visibles respecto al contexto filtrado.",
    )

    render_context_bar(
        [
            {"label": "Eventos mostrados", "value": _format_event_count(len(selected_df), len(filtered_df))},
            {"label": "Tipos seleccionados", "value": len(selected_event_types)},
        ]
    )
    st.divider()

    if selected_df.empty:
        render_empty_state(
            "No hay eventos de los tipos seleccionados.",
            "Prueba con otros tipos de evento.",
        )
        return

    plot_df, draw_movements, _ = prepare_events_map_df(selected_df)

    if plot_df.empty:
        render_empty_state(
            "Los eventos seleccionados no tienen representación espacial útil.",
            "Algunos eventos administrativos se muestran solo en tabla.",
        )
    else:
        fig = plot_events_on_pitch(
            plot_df,
            title="Mapa de eventos seleccionados",
            draw_movements=draw_movements,
            show_legend=True,
        )
        render_plot_card(
            "Mapa de eventos",
            fig,
            "Distribución espacial de los eventos seleccionados en el contexto filtrado.",
        )
    st.divider()

    render_section_header(
        "Tabla de eventos",
        "Detalle de los eventos visibles. La tabla se limita para mantener rendimiento.",
    )

    display_columns = [
        column
        for column in [
            "match_id",
            "period",
            "minute",
            "second",
            "team",
            "player",
            event_type_column,
            "outcome",
            "x",
            "y",
            "end_x",
            "end_y",
        ]
        if column in selected_df.columns
    ]

    table_df = selected_df[display_columns].copy() if display_columns else selected_df.copy()

    with st.container(border=True):
        render_limited_dataframe(table_df, max_rows=1000)

    st.divider()
    _render_event_glossary(selected_event_types)
