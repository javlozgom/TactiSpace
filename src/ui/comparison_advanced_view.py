from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from src.services.comparative_service import (
    advanced_comparison_to_dataframe,
    compare_player_contexts,
    get_available_matches,
    get_players_for_match_team,
    get_teams_for_match,
    metrics_dict_to_dataframe,
)
from src.services.events_service import (
    calculate_specific_event_metrics,
    get_event_analysis_description,
    get_metric_definitions,
    get_metric_display_name,
)
from src.core.rules.metric_filters import apply_specific_metric_focus_filters, get_focus_filter_options
from src.core.models.player_labels import get_player_display_name
from src.ui.comparison_utils import (
    ensure_distinct_labels,
    format_comparison_table,
    format_match_label,
    format_metric_value,
    format_metrics_table,
)
from src.ui.components import render_context_bar, render_empty_state, render_pill_selector, render_section_header
from src.ui.views.specific_metrics import (
    MAX_SPECIFIC_EVENT_ROWS,
    SPECIFIC_EVENT_KPI_KEYS,
    SUCCESS_NOTE,
    build_specific_metrics_table,
)
from src.ui.components.visualizations import plot_single_event_map


def render_advanced_comparison(
    full_df: pd.DataFrame,
    supported_events: list[str],
    full_name_map: dict[str, str],
    match_labels: dict[str, str],
) -> None:
    """Render the advanced comparison block using the full dataframe."""
    with st.container():
        render_section_header("Comparativa avanzada", "Compara jugadores entre partidos, equipos o contextos distintos.")
        st.caption(
            "Compara jugadores entre distintos equipos o partidos, incluyendo la evolución de un mismo jugador en diferentes encuentros."
        )
        available_matches = get_available_matches(full_df)
        if not available_matches:
            render_empty_state(
                "No hay partidos disponibles para construir la comparativa avanzada.",
                "Revisa que el dataset cargado incluya más de un contexto de partido.",
            )
            return

        left_col, right_col = st.columns(2, vertical_alignment="top")
        with left_col:
            st.markdown("**Jugador A**")
            match_a = st.selectbox(
                "Partido A",
                available_matches,
                key="advanced_compare_match_a",
                format_func=lambda match_id: format_match_label(match_id, match_labels),
            )
            teams_a = get_teams_for_match(full_df, match_a)
            if not teams_a:
                render_empty_state(
                    "No hay equipos disponibles para el partido A.",
                    "Selecciona otro partido para continuar.",
                )
                return
            if st.session_state.get("advanced_compare_team_a") not in teams_a:
                st.session_state["advanced_compare_team_a"] = teams_a[0]
            team_a = st.selectbox("Equipo A", teams_a, key="advanced_compare_team_a")
            players_a = get_players_for_match_team(full_df, match_a, team_a)
            if not players_a:
                render_empty_state(
                    "No hay jugadores disponibles para el contexto A.",
                    "Selecciona otro equipo o partido para continuar.",
                )
                return
            if st.session_state.get("advanced_compare_player_a") not in players_a:
                st.session_state["advanced_compare_player_a"] = players_a[0]
            player_a = st.selectbox(
                "Jugador A",
                players_a,
                key="advanced_compare_player_a",
                format_func=lambda player_name: get_player_display_name(player_name, full_name_map),
            )

        with right_col:
            st.markdown("**Jugador B**")
            match_b = st.selectbox(
                "Partido B",
                available_matches,
                key="advanced_compare_match_b",
                format_func=lambda match_id: format_match_label(match_id, match_labels),
            )
            teams_b = get_teams_for_match(full_df, match_b)
            if not teams_b:
                render_empty_state(
                    "No hay equipos disponibles para el partido B.",
                    "Selecciona otro partido para continuar.",
                )
                return
            if st.session_state.get("advanced_compare_team_b") not in teams_b:
                st.session_state["advanced_compare_team_b"] = teams_b[0]
            team_b = st.selectbox("Equipo B", teams_b, key="advanced_compare_team_b")
            players_b = get_players_for_match_team(full_df, match_b, team_b)
            if not players_b:
                render_empty_state(
                    "No hay jugadores disponibles para el contexto B.",
                    "Selecciona otro equipo o partido para continuar.",
                )
                return
            if st.session_state.get("advanced_compare_player_b") not in players_b:
                st.session_state["advanced_compare_player_b"] = players_b[0]
            player_b = st.selectbox(
                "Jugador B",
                players_b,
                key="advanced_compare_player_b",
                format_func=lambda player_name: get_player_display_name(player_name, full_name_map),
            )

        selected_event = st.selectbox(
            "Evento a comparar",
            supported_events,
            key="advanced_compare_event_selector",
        )
        draft_config = {
            "match_a": match_a,
            "team_a": team_a,
            "player_a": player_a,
            "match_b": match_b,
            "team_b": team_b,
            "player_b": player_b,
            "selected_event": selected_event,
        }

        st.session_state["advanced_compare_last_config"] = dict(draft_config)
        config = draft_config

        with st.container():
            match_a = config["match_a"]
            team_a = config["team_a"]
            player_a = config["player_a"]
            match_b = config["match_b"]
            team_b = config["team_b"]
            player_b = config["player_b"]
            selected_event = config["selected_event"]

            context_a = {"match_id": match_a, "team": team_a, "player": player_a}
            context_b = {"match_id": match_b, "team": team_b, "player": player_b}
            if context_a == context_b:
                st.info("Selecciona dos contextos distintos para comparar.")
                return

            comparison = compare_player_contexts(full_df, context_a, context_b, selected_event)
            if not comparison:
                st.warning("No hay datos suficientes para uno de los contextos seleccionados.")
                return

            if player_a == player_b and match_a != match_b:
                st.info("Comparando el rendimiento del mismo jugador en dos partidos distintos.")
            elif team_a != team_b:
                st.info("Comparando jugadores de equipos diferentes.")

            render_section_header("Resumen de la comparación")
            summary_cols = st.columns(2, vertical_alignment="top")
            with summary_cols[0]:
                st.markdown(
                    "\n".join(
                        [
                            "**Contexto A**",
                            f"Partido: `{format_match_label(match_a, match_labels)}`",
                            f"Equipo: `{team_a}`",
                            f"Jugador: `{get_player_display_name(player_a, full_name_map)}`",
                        ]
                    )
                )
            with summary_cols[1]:
                st.markdown(
                    "\n".join(
                        [
                            "**Contexto B**",
                            f"Partido: `{format_match_label(match_b, match_labels)}`",
                            f"Equipo: `{team_b}`",
                            f"Jugador: `{get_player_display_name(player_b, full_name_map)}`",
                        ]
                    )
                )
            st.markdown(f"**Evento comparado:** `{selected_event}`")
            st.info(get_event_analysis_description(selected_event))
            render_context_bar(
                [
                    {"label": "Contexto A", "value": f"{team_a} · {get_player_display_name(player_a, full_name_map)}"},
                    {"label": "Contexto B", "value": f"{team_b} · {get_player_display_name(player_b, full_name_map)}"},
                    {"label": "Evento", "value": selected_event},
                ]
            )
            st.divider()

            focus_options = get_focus_filter_options(selected_event)
            selected_filters = _render_advanced_filter_groups(selected_event, focus_options)
            if focus_options and st.button(
                "Restablecer filtros de esta comparativa",
                key=f"advanced_specific_metric_reset::{selected_event}",
                icon=":material/refresh:",
            ):
                _reset_advanced_filter_group_state(selected_event, focus_options)
                st.rerun()

            st.caption(SUCCESS_NOTE)
            with st.expander("Definiciones de métricas"):
                for label, definition in get_metric_definitions().items():
                    st.markdown(f"**{label}:** {definition}")
                st.caption(SUCCESS_NOTE)
            st.divider()

            filtered_context_a_df = _filter_context_df(
                full_df=full_df,
                match_id=match_a,
                team=team_a,
                player=player_a,
                event_type=selected_event,
                selected_filters=selected_filters,
            )
            filtered_context_b_df = _filter_context_df(
                full_df=full_df,
                match_id=match_b,
                team=team_b,
                player=player_b,
                event_type=selected_event,
                selected_filters=selected_filters,
            )

            comparison_df = advanced_comparison_to_dataframe(comparison)
            left_label, right_label = ensure_distinct_labels(
                get_player_display_name(player_a, full_name_map),
                get_player_display_name(player_b, full_name_map),
                left_suffix=f"A · {team_a}",
                right_suffix=f"B · {team_b}",
            )
            if comparison_df.empty:
                st.info("No hay métricas numéricas comparables para esos dos contextos.")
            else:
                comparison_df = format_comparison_table(
                    comparison_df,
                    left_label=left_label,
                    right_label=right_label,
                )
                st.dataframe(comparison_df, width="stretch", hide_index=True)
            st.divider()

            detail_cols = st.columns(2, vertical_alignment="top")
            with detail_cols[0]:
                _render_advanced_context_panel(
                    filtered_context_a_df,
                    selected_event,
                    left_label,
                    full_name_map,
                    "a",
                )
            with detail_cols[1]:
                _render_advanced_context_panel(
                    filtered_context_b_df,
                    selected_event,
                    right_label,
                    full_name_map,
                    "b",
                )

            with st.expander("Ver métricas completas de cada contexto"):
                metrics_cols = st.columns(2, vertical_alignment="top")
                with metrics_cols[0]:
                    st.markdown(f"**{left_label}**")
                    metrics_a_df = metrics_dict_to_dataframe(comparison.get("metrics_a", {}))
                    metrics_a_df = format_metrics_table(metrics_a_df)
                    st.dataframe(metrics_a_df, width="stretch", hide_index=True)
                with metrics_cols[1]:
                    st.markdown(f"**{right_label}**")
                    metrics_b_df = metrics_dict_to_dataframe(comparison.get("metrics_b", {}))
                    metrics_b_df = format_metrics_table(metrics_b_df)
                    st.dataframe(metrics_b_df, width="stretch", hide_index=True)


def _filter_context_df(
    full_df: pd.DataFrame,
    match_id: object,
    team: str,
    player: str,
    event_type: str,
    selected_filters: dict[str, str],
) -> pd.DataFrame:
    """Apply quick filters and return one fully filtered player context."""
    context_df = full_df[(full_df["match_id"] == match_id) & (full_df["team"] == team)].copy()
    context_df = apply_specific_metric_focus_filters(
        context_df,
        event_type=event_type,
        selected_filters=selected_filters,
        context_df=context_df.copy(),
    )
    return context_df[
        (context_df["match_id"] == match_id)
        & (context_df["team"] == team)
        & (context_df["player"] == player)
    ].copy()


def _render_advanced_filter_groups(event_type: str, focus_options: dict[str, list[str]]) -> dict[str, str]:
    """Render specific-metrics quick filters inside the advanced comparison block."""
    selections: dict[str, str] = {}
    if not focus_options:
        return selections

    st.markdown("**Filtros rápidos comunes**")
    group_items = list(focus_options.items())
    groups_per_row = 1 if len(group_items) <= 1 else 2
    for row_start in range(0, len(group_items), groups_per_row):
        row_items = group_items[row_start : row_start + groups_per_row]
        row_columns = st.columns(len(row_items), gap="large", vertical_alignment="top")
        for column, (group_name, options) in zip(row_columns, row_items):
            state_key = _advanced_filter_state_key(event_type, group_name)
            if st.session_state.get(state_key) not in options:
                st.session_state[state_key] = options[0]
            with column:
                st.markdown(f"**{group_name}**")
                selections[group_name] = _render_single_group_control(
                    label=f"{group_name} - comparativa avanzada - {event_type}",
                    options=options,
                    key=state_key,
                )
    return selections


def _render_single_group_control(label: str, options: list[str], key: str) -> str:
    """Render one quick-filter control with a stable active-button state."""
    return render_pill_selector(label, options, key, columns_per_row=3)


def _render_advanced_context_panel(
    context_df: pd.DataFrame,
    event_type: str,
    label: str,
    full_name_map: dict[str, str],
    suffix: str,
) -> None:
    """Render the specific-metrics style detail view for one comparison context."""
    st.markdown(f"**{label}**")
    if context_df.empty:
        st.warning("No hay eventos para esta combinación de filtros.")
        return

    metrics = calculate_specific_event_metrics(context_df, event_type)
    _render_context_kpis(event_type, metrics, suffix)

    fig = plot_single_event_map(
        context_df,
        event_type=event_type,
        title=f"{event_type} - {label}",
        show_legend=True,
    )
    st.pyplot(fig, width="stretch")
    plt.close(fig)

    summary_df = build_specific_metrics_table(metrics)
    st.dataframe(summary_df, width="stretch", hide_index=True)

    display_df = context_df.copy().head(MAX_SPECIFIC_EVENT_ROWS)
    if "player" in display_df.columns:
        display_df["player"] = display_df["player"].map(
            lambda value: get_player_display_name(str(value), full_name_map)
        )
    st.dataframe(display_df, width="stretch", hide_index=True)
    if len(context_df) > MAX_SPECIFIC_EVENT_ROWS:
        st.caption(f"Se muestran los primeros {MAX_SPECIFIC_EVENT_ROWS} eventos filtrados.")


def _render_context_kpis(event_type: str, metrics: dict[str, object], suffix: str) -> None:
    """Render a compact KPI strip for one advanced comparison context."""
    preferred_keys = [
        metric_key
        for metric_key in SPECIFIC_EVENT_KPI_KEYS.get(event_type, ["total_events", "successful_events", "success_rate"])
        if metric_key in metrics
    ]
    if not preferred_keys:
        return

    kpi_cols = st.columns(len(preferred_keys))
    for column, metric_key in zip(kpi_cols, preferred_keys):
        column.metric(
            get_metric_display_name(metric_key),
            format_metric_value(metrics[metric_key]),
        )


def _advanced_filter_state_key(event_type: str, group_name: str) -> str:
    """Build a session-state key for advanced specific-metrics filters."""
    return f"advanced_specific_metric_filter::{event_type}::{group_name}"


def _reset_advanced_filter_group_state(event_type: str, focus_options: dict[str, list[str]]) -> None:
    """Reset advanced comparison quick filters for one event to their default option."""
    for group_name, options in focus_options.items():
        st.session_state[_advanced_filter_state_key(event_type, group_name)] = options[0]
