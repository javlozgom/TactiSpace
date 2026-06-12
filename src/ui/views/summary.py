from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from src.repositories.data_repository import load_match_labels
from src.core.metrics.basic import SUCCESS_OUTCOMES, calculate_player_summary, get_effective_outcome_series
from src.core.rules.position_priorities import (
    DEFAULT_POSITION,
    EVENT_DESCRIPTIONS,
    get_priority_events_for_player,
    get_specific_position_for_player,
)
from src.ui.components import (
    render_context_bar,
    render_empty_state,
    render_info_box,
    render_kpi_grid,
    render_limited_dataframe,
    render_page_header,
    render_plot_card,
    render_section_header,
)
from src.ui.components.visualizations import plot_single_event_map


SPECIAL_SUMMARY_EVENTS = {
    "Own Goal For": "Gol en propia a favor",
    "Own Goal Against": "Gol en propia en contra",
    "Offside": "Fuera de juego",
}

SPECIAL_PLOT_EVENT_TYPES = ["Own Goal For", "Own Goal Against"]


def _safe_metric(metrics: dict[str, object], key: str, default: object = 0) -> object:
    """Return a metric safely from the metrics dictionary."""
    if not isinstance(metrics, dict):
        return default
    return metrics.get(key, default)


def _get_event_type_column(df: pd.DataFrame) -> str | None:
    """Return the first available event type column."""
    for column in ("event_type", "type", "type_name"):
        if column in df.columns:
            return column
    return None


def _event_success_rate(df: pd.DataFrame, event_type: str, event_type_column: str) -> str:
    """Calculate a success rate for one event type."""
    event_df = df[df[event_type_column].astype(str) == event_type].copy()
    if event_df.empty:
        return "0.0%"
    try:
        success_rate = get_effective_outcome_series(event_df).isin(SUCCESS_OUTCOMES).mean() * 100
        return f"{success_rate:.1f}%"
    except Exception:
        return "0.0%"


def _build_action_success_df(filtered_df: pd.DataFrame, event_type_column: str) -> pd.DataFrame:
    """Build a compact success-rate table."""
    relevant_events = ["Pass", "Shot", "Dribble", "Duel", "Interception", "Pressure", "Carry"]
    rows = []

    for event_type in relevant_events:
        event_df = filtered_df[filtered_df[event_type_column].astype(str) == event_type].copy()
        if event_df.empty:
            continue

        rows.append(
            {
                "Evento": event_type,
                "Total": len(event_df),
                "Acierto": _event_success_rate(filtered_df, event_type, event_type_column),
            }
        )

    return pd.DataFrame(rows)


def _build_special_event_summary_items(filtered_df: pd.DataFrame) -> list[tuple[str, str, str]]:
    """Build compact summary items for special event cards."""
    event_type_column = _get_event_type_column(filtered_df)
    if event_type_column is None or filtered_df.empty:
        return []

    items: list[tuple[str, str, str]] = []
    for event_type, label in SPECIAL_SUMMARY_EVENTS.items():
        event_df = filtered_df[filtered_df[event_type_column].astype(str) == event_type].copy()
        if event_df.empty:
            continue

        references = []
        if {"minute", "second"}.issubset(event_df.columns):
            for _, row in event_df.loc[:, ["minute", "second"]].dropna().head(3).iterrows():
                minute = pd.to_numeric(row.get("minute"), errors="coerce")
                second = pd.to_numeric(row.get("second"), errors="coerce")
                if pd.notna(minute) and pd.notna(second):
                    references.append(f"{int(minute)}:{int(second):02d}")

        help_text = f"Aparece en {', '.join(references)}" if references else "Aparece en el contexto filtrado"
        items.append((label, str(len(event_df)), help_text))

    return items


def _get_special_plot_event_types(filtered_df: pd.DataFrame) -> list[str]:
    """Return special event types with a useful dedicated pitch marker."""
    event_type_column = _get_event_type_column(filtered_df)
    if event_type_column is None or filtered_df.empty:
        return []

    available = set(filtered_df[event_type_column].dropna().astype(str).unique().tolist())
    return [event_type for event_type in SPECIAL_PLOT_EVENT_TYPES if event_type in available]


@st.cache_data(show_spinner=False)
def _get_match_labels() -> dict[str, str]:
    """Cache readable match labels for summary helpers."""
    return load_match_labels()


def _format_special_event_reference(row: pd.Series, match_labels: dict[str, str]) -> str:
    """Format one compact special-event reference with match, stage and time."""
    match_id = row.get("match_id")
    match_label = match_labels.get(str(match_id), f"Partido {match_id}") if pd.notna(match_id) else "Partido"

    label_parts = [part.strip() for part in str(match_label).split("|") if str(part).strip()]
    if len(label_parts) >= 3:
        match_context = f"{label_parts[0]} | {label_parts[-1]}"
    else:
        match_context = label_parts[0] if label_parts else str(match_label)

    minute = pd.to_numeric(row.get("minute"), errors="coerce")
    second = pd.to_numeric(row.get("second"), errors="coerce")
    if pd.notna(minute) and pd.notna(second):
        return f"{match_context} ({int(minute)}:{int(second):02d})"
    return match_context


def _render_special_events(filtered_df: pd.DataFrame, event_type_column: str) -> None:
    """Render special event cards if present."""
    rows = []
    match_labels = _get_match_labels()

    for event_type, label in SPECIAL_SUMMARY_EVENTS.items():
        event_df = filtered_df[filtered_df[event_type_column].astype(str) == event_type].copy()
        if event_df.empty:
            continue

        minute_text = "Contexto filtrado"
        sample_columns = [column for column in ["match_id", "minute", "second"] if column in event_df.columns]
        if {"minute", "second"}.issubset(event_df.columns):
            sample_times = (
                event_df.loc[:, sample_columns]
                .dropna()
                .drop_duplicates()
                .sort_values([column for column in ["match_id", "minute", "second"] if column in sample_columns])
                .head(3)
            )
            if not sample_times.empty:
                minute_text = ", ".join(
                    _format_special_event_reference(row, match_labels)
                    for _, row in sample_times.iterrows()
                )

        rows.append(
            {
                "label": label,
                "value": len(event_df),
                "help": f"Aparece en {minute_text}",
                "tone": "orange" if event_type == "Offside" else "red",
                "icon": "flag" if event_type == "Offside" else "circle-x",
            }
        )

    if not rows:
        return

    render_section_header(
        "Eventos especiales del contexto",
        "Eventos poco frecuentes que conviene revisar de forma explícita.",
    )
    render_kpi_grid(rows)


def _render_priority_maps(
    filtered_df: pd.DataFrame,
    selected_player: str,
    position_source_df: pd.DataFrame,
    event_type_column: str,
) -> None:
    """Render priority maps based on player position."""
    player_for_priority = selected_player if selected_player and selected_player != "Todos" else "Todos"

    try:
        detected_position, priority_events = get_priority_events_for_player(
            position_source_df,
            player_for_priority,
        )
    except Exception:
        detected_position = DEFAULT_POSITION
        priority_events = ["Pass", "Carry", "Shot", "Pressure", "Ball Recovery", "Duel"]

    if not detected_position:
        detected_position = DEFAULT_POSITION

    try:
        specific_position = get_specific_position_for_player(position_source_df, player_for_priority)
    except Exception:
        specific_position = None

    render_section_header(
        "Mapas prioritarios del jugador",
        "La app prioriza tipos de evento según el perfil posicional cuando es posible.",
    )

    render_context_bar(
        [
            {"label": "Jugador", "value": player_for_priority},
            {"label": "Grupo de posición", "value": detected_position},
            {"label": "Posición específica", "value": specific_position or "No disponible"},
        ]
    )

    priority_events = [
        event_type
        for event_type in priority_events
        if event_type in set(filtered_df[event_type_column].dropna().astype(str).unique())
    ]

    if not priority_events:
        render_empty_state(
            "No hay eventos prioritarios disponibles en este contexto.",
            "Prueba con otro jugador, equipo o rango temporal.",
        )
        return

    for row_start in range(0, min(len(priority_events), 6), 2):
        columns = st.columns(2)
        for column, event_type in zip(columns, priority_events[row_start : row_start + 2]):
            with column:
                event_scope_df = filtered_df[
                    filtered_df[event_type_column].astype(str) == event_type
                ].copy()

                if player_for_priority != "Todos" and "player" in event_scope_df.columns:
                    event_scope_df = event_scope_df[
                        event_scope_df["player"].astype(str) == str(player_for_priority)
                    ].copy()

                description = EVENT_DESCRIPTIONS.get(
                    event_type,
                    "Mapa contextual del tipo de evento seleccionado.",
                )

                if event_scope_df.empty:
                    with st.container(border=True):
                        st.markdown(f"**{event_type}**")
                        st.caption("No hay eventos para este mapa.")
                    continue

                fig = plot_single_event_map(
                    filtered_df,
                    event_type=event_type,
                    player_name=None if player_for_priority == "Todos" else player_for_priority,
                    title=event_type,
                    show_legend=True,
                )

                render_plot_card(
                    event_type,
                    fig,
                    description,
                )


def render_summary_view(
    filtered_df: pd.DataFrame,
    metrics: dict[str, object],
    selected_player: str,
    position_source_df: pd.DataFrame,
) -> None:
    """Render the summary dashboard."""
    render_page_header(
        "Resumen",
        "Vista general del contexto activo con volumen, acierto por acción y mapas prioritarios del jugador.",
        badge="Visión general",
    )

    if filtered_df.empty:
        render_empty_state(
            "No hay eventos para los filtros seleccionados.",
            "Prueba con otro partido, equipo, jugador o rango de minutos.",
        )
        return

    event_type_column = _get_event_type_column(filtered_df)
    if event_type_column is None:
        render_empty_state(
            "No se ha encontrado una columna de tipo de evento.",
            "Revisa que el dataset incluya event_type, type o type_name.",
        )
        return

    selected_player_label = selected_player or "Todos"

    render_kpi_grid(
        [
            {
                "label": "Eventos",
                "value": f"{int(_safe_metric(metrics, 'total_events', len(filtered_df))):,}",
                "help": "Volumen del contexto",
                "tone": "blue",
                "icon": "list",
            },
            {
                "label": "Pases",
                "value": f"{int(_safe_metric(metrics, 'total_passes', 0)):,}",
                "help": "Acciones de pase",
                "tone": "green",
                "icon": "send",
            },
            {
                "label": "Conducciones",
                "value": f"{int(_safe_metric(metrics, 'total_carries', 0)):,}",
                "help": "Carries detectados",
                "tone": "purple",
                "icon": "route",
            },
            {
                "label": "Tiros",
                "value": f"{int(_safe_metric(metrics, 'total_shots', 0)):,}",
                "help": "Finalizaciones",
                "tone": "orange",
                "icon": "target",
            },
        ]
    )
    st.divider()

    render_section_header(
        "Contexto activo",
        "Resumen del subconjunto que se está analizando.",
    )

    render_context_bar(
        [
            {"label": "Jugador", "value": selected_player_label},
            {"label": "Equipos", "value": filtered_df["team"].nunique() if "team" in filtered_df.columns else 0},
            {"label": "Partidos", "value": filtered_df["match_id"].nunique() if "match_id" in filtered_df.columns else 0},
            {"label": "Tipos de evento", "value": filtered_df[event_type_column].nunique()},
        ]
    )
    st.divider()

    render_section_header(
        "Acierto por acción",
        "Lectura rápida del comportamiento de las acciones más relevantes.",
    )

    action_success_df = _build_action_success_df(filtered_df, event_type_column)
    if action_success_df.empty:
        render_empty_state(
            "No hay eventos suficientes para calcular acierto por acción.",
            "Prueba con un contexto más amplio.",
        )
    else:
        with st.container(border=True):
            st.dataframe(action_success_df, width="stretch", hide_index=True)
    st.divider()

    _render_special_events(filtered_df, event_type_column)
    st.divider()

    render_section_header(
        "Resumen por jugador",
        "Métricas agregadas por jugador dentro del contexto filtrado.",
    )

    try:
        summary_df = calculate_player_summary(filtered_df)
    except Exception:
        summary_df = pd.DataFrame()

    if summary_df.empty:
        render_empty_state(
            "No hay datos suficientes para construir el resumen por jugador.",
            "Prueba a ampliar el rango de minutos o quitar el filtro de jugador.",
        )
    else:
        with st.container(border=True):
            render_limited_dataframe(summary_df, max_rows=1000)
    st.divider()

    _render_priority_maps(
        filtered_df=filtered_df,
        selected_player=selected_player_label,
        position_source_df=position_source_df,
        event_type_column=event_type_column,
    )
    st.divider()

    render_section_header(
        "Cómo interpretar este resumen",
        "Los indicadores son descriptivos y dependen directamente de los filtros globales.",
    )

    render_info_box(
        "Lectura recomendada",
        (
            "Usa esta pestaña como punto de partida. Los KPIs ofrecen una visión rápida, "
            "mientras que los mapas prioritarios ayudan a enfocar el análisis según el perfil "
            "del jugador o el contexto seleccionado. Para conclusiones más detalladas, combina "
            "esta lectura con Comparativa y Voronoi, Delaunay y sugerencia de pase."
        ),
        tone="info",
    )
