from __future__ import annotations

import pandas as pd
import streamlit as st

from src.core.metrics.basic import get_effective_outcome_series
from src.core.models.player_labels import apply_player_display_names, build_player_label_maps
from src.core.models.preprocessing import infer_duel_outcomes
from src.core.rules.metric_filters import apply_specific_metric_focus_filters, get_focus_filter_options
from src.services.events_service import (
    calculate_specific_event_metrics,
    get_event_analysis_description,
    get_metric_definitions,
    get_metric_display_name,
    get_supported_specific_metric_events,
)
from src.ui.components import render_context_bar, render_empty_state, render_info_box, render_plot_card
from src.ui.components.data_panel import render_data_panel
from src.ui.components.metric_card import render_metric_cards
from src.ui.components.visualizations import plot_single_event_map
from src.ui.layout_kit.navigation import render_button_group
from src.ui.layout_kit.page import render_page_shell
from src.ui.layout_kit.section import render_section_title


MAX_SPECIFIC_EVENT_ROWS = 250
SUCCESS_NOTE = (
    "El porcentaje de éxito se calcula a partir del campo outcome cuando está disponible. "
    "En algunos eventos, como Pressure, Clearance o Ball Receipt*, la interpretación del éxito "
    "puede depender del proveedor de datos y se considera una aproximación inicial."
)

SPECIFIC_EVENT_KPI_KEYS = {
    "Pass": ["total_passes", "completed_passes", "incomplete_passes", "completion_rate"],
    "Carry": ["total_carries", "progressive_carries", "final_third_carries", "box_entries"],
    "Shot": ["total_shots", "goals", "saved", "blocked"],
    "Pressure": ["total_pressures", "pressures_in_opponent_half", "pressures_in_final_third", "average_x"],
    "Duel": ["total_duels", "duels_won", "duels_lost", "win_rate"],
    "Dribble": ["total_dribbles", "successful_dribbles", "unsuccessful_dribbles", "success_rate"],
    "Ball Recovery": [
        "total_recoveries",
        "recoveries_in_own_half",
        "recoveries_in_opponent_half",
        "recoveries_in_final_third",
    ],
}


def render_specific_metrics(
    filtered_df: pd.DataFrame,
    selected_player: str = "Todos",
    context_df: pd.DataFrame | None = None,
) -> None:
    """Render the specific metrics tab focused on event analysis."""
    render_page_shell(
        "Métricas específicas",
        "Análisis detallado por tipo de evento.",
        eyebrow="Métricas",
        tone="teal",
    )
    render_context_bar(
        [
            {"label": "Jugador", "value": selected_player or "Todos"},
            {"label": "Eventos filtrados", "value": f"{len(filtered_df):,}"},
            {
                "label": "Partidos",
                "value": f"{filtered_df['match_id'].nunique():,}" if "match_id" in filtered_df.columns else "-",
            },
        ]
    )
    st.divider()

    supported_events = get_supported_specific_metric_events()
    full_to_display, _ = build_player_label_maps(filtered_df)

    render_section_title("Selector de evento", "Escoge el tipo de acción y revisa su definición.")
    with st.container(border=True):
        selected_event = st.selectbox(
            "Tipo de evento",
            supported_events,
            key="specific_metrics_event_selector",
        )
    render_info_box(
        "Descripción de la métrica",
        get_event_analysis_description(selected_event),
        tone="neutral",
    )
    st.divider()

    focus_options = get_focus_filter_options(selected_event)
    selected_filters = _render_filter_groups(selected_event, focus_options)
    if focus_options and st.button(
        "Restablecer filtros de esta métrica",
        key=f"specific_metric_reset::{selected_event}",
        icon=":material/refresh:",
    ):
        _reset_filter_group_state(selected_event, focus_options)
        st.rerun()
    if focus_options:
        st.divider()

    filtered_event_df = apply_specific_metric_focus_filters(
        filtered_df,
        event_type=selected_event,
        selected_filters=selected_filters,
        context_df=context_df if context_df is not None else filtered_df,
    )
    metrics = calculate_specific_event_metrics(filtered_event_df, selected_event)

    render_info_box("Nota metodológica", SUCCESS_NOTE, tone="neutral")
    with st.expander("Definiciones de métricas"):
        for label, definition in get_metric_definitions().items():
            st.markdown(f"**{label}:** {definition}")
        st.caption(SUCCESS_NOTE)
    st.divider()

    _render_kpis(selected_event, metrics)

    content_cols = st.columns([1.35, 1], vertical_alignment="top")
    with content_cols[0]:
        if filtered_event_df.empty:
            render_empty_state(
                "No hay eventos para esta combinación de filtros.",
                "Prueba otra combinación de filtros rápidos o amplía el contexto global.",
            )
        else:
            fig = plot_single_event_map(
                filtered_event_df,
                event_type=selected_event,
                title=selected_event,
                show_legend=True,
            )
            render_plot_card(
                f"Mapa del evento: {selected_event}",
                fig,
                "Distribución espacial de las acciones filtradas.",
            )

    with content_cols[1]:
        summary_df = build_specific_metrics_table(metrics)
        render_data_panel(
            summary_df,
            title="Resumen de métricas",
            description="Desglose tabular del evento seleccionado.",
        )

    st.divider()
    display_df = apply_player_display_names(_build_display_df(filtered_event_df), full_to_display).head(
        MAX_SPECIFIC_EVENT_ROWS
    )
    render_data_panel(
        display_df,
        title="Eventos filtrados",
        description="Vista tabular de la selección activa.",
    )
    if len(filtered_event_df) > MAX_SPECIFIC_EVENT_ROWS:
        st.caption(f"Se muestran los primeros {MAX_SPECIFIC_EVENT_ROWS} eventos filtrados.")


def build_specific_metrics_table(metrics: dict[str, object]) -> pd.DataFrame:
    """Convert metric dicts into a user-facing two-column table."""
    rows = [
        {
            "Métrica": get_metric_display_name(key),
            "Valor": _format_metric_value(value),
        }
        for key, value in metrics.items()
        if key != "interpretation"
    ]
    return pd.DataFrame(rows)


def _render_filter_groups(event_type: str, focus_options: dict[str, list[str]]) -> dict[str, str]:
    """Render grouped quick filters and return the current selection."""
    selections: dict[str, str] = {}
    if not focus_options:
        return selections

    render_section_title("Filtros internos", "Ajustes rápidos específicos para este tipo de evento.")
    with st.container(border=True):
        group_items = list(focus_options.items())
        groups_per_row = 1 if len(group_items) <= 1 else 2
        for row_start in range(0, len(group_items), groups_per_row):
            row_items = group_items[row_start : row_start + groups_per_row]
            row_columns = st.columns(len(row_items), gap="large", vertical_alignment="top")
            for column, (group_name, options) in zip(row_columns, row_items):
                state_key = _filter_state_key(event_type, group_name)
                if st.session_state.get(state_key) not in options:
                    st.session_state[state_key] = options[0]
                with column:
                    st.markdown(f"**{group_name}**")
                    selections[group_name] = _render_single_group_control(
                        label=f"{group_name} - {event_type}",
                        options=options,
                        key=state_key,
                    )
    return selections


def _render_single_group_control(label: str, options: list[str], key: str) -> str:
    """Render one quick-filter control with a stable active-button state."""
    return render_button_group(label, options, key, columns_per_row=3)


def _render_kpis(event_type: str, metrics: dict[str, object]) -> None:
    """Render a compact KPI strip using user-facing metric names."""
    default_keys = (
        ["total_events", "average_x", "average_y"]
        if not metrics.get("show_success_rate", True)
        else ["total_events", "successful_events", "success_rate"]
    )
    preferred_keys = [
        metric_key
        for metric_key in SPECIFIC_EVENT_KPI_KEYS.get(event_type, default_keys)
        if metric_key in metrics
    ]
    if not preferred_keys:
        return

    render_metric_cards(
        [
            {
                "label": get_metric_display_name(metric_key),
                "value": _format_metric_value(metrics[metric_key]),
            }
            for metric_key in preferred_keys
        ]
    )


def _format_metric_value(value: object) -> str:
    """Format metric values consistently for display widgets."""
    if isinstance(value, float):
        if value.is_integer():
            return str(int(value))
        return f"{value:.2f}"
    return str(value)


def _build_display_df(df: pd.DataFrame) -> pd.DataFrame:
    """Prepare a user-facing event table with inferred duel outcomes when needed."""
    display_df = df.copy()
    duel_inference_columns = {"event_type", "outcome", "match_id", "team", "timestamp", "possession_id"}
    if "inferred_outcome" not in display_df.columns and duel_inference_columns.issubset(display_df.columns):
        if (display_df["event_type"] == "Duel").any():
            display_df = infer_duel_outcomes(display_df)
    if "inferred_outcome" in display_df.columns:
        display_df["outcome"] = get_effective_outcome_series(display_df)
    return display_df


def _filter_state_key(event_type: str, group_name: str) -> str:
    """Build a session-state key for one grouped quick filter."""
    return f"specific_metric_filter::{event_type}::{group_name}"


def _reset_filter_group_state(event_type: str, focus_options: dict[str, list[str]]) -> None:
    """Reset quick filters for one event to their default option."""
    for group_name, options in focus_options.items():
        if not options:
            continue
        st.session_state[_filter_state_key(event_type, group_name)] = options[0]
