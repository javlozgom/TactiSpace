from __future__ import annotations

import pandas as pd
import streamlit as st

from src.services.comparative_service import compare_player_to_team, comparison_dict_to_dataframe
from src.core.models.player_labels import get_player_display_name
from src.ui.comparison_utils import ensure_distinct_labels, format_player_team_comparison_table
from src.ui.components import render_section_header


def render_basic_comparisons(
    filtered_df: pd.DataFrame,
    selected_player: str | None,
    supported_events: list[str],
    filtered_name_map: dict[str, str],
) -> None:
    """Render the basic comparison blocks inside the comparative tab."""
    _render_player_vs_team(filtered_df, selected_player, supported_events, filtered_name_map)


def _render_player_vs_team(
    filtered_df: pd.DataFrame,
    selected_player: str | None,
    supported_events: list[str],
    filtered_name_map: dict[str, str],
) -> None:
    """Render the player-vs-team comparison block."""
    with st.container():
        render_section_header("Jugador vs equipo", "Mide cómo se posiciona un jugador frente al promedio de su contexto.")
        if not selected_player or selected_player == "Todos":
            st.info("Selecciona un jugador concreto en el panel lateral para comparar contra el equipo.")
            return

        st.markdown(f"**Jugador seleccionado:** {get_player_display_name(selected_player, filtered_name_map)}")
        selected_event = st.selectbox(
            "Evento para comparación con el equipo",
            supported_events,
            key="comparative_event_selector_team",
        )
        st.divider()
        comparison = compare_player_to_team(filtered_df, selected_player, selected_event)
        if not comparison:
            st.info("No hay datos suficientes para comparar al jugador con el equipo.")
            return

        comparison_df = comparison_dict_to_dataframe(comparison)
        if comparison_df.empty:
            st.info("No hay métricas numéricas comparables para esta selección.")
            return

        left_label, right_label = ensure_distinct_labels(
            get_player_display_name(selected_player, filtered_name_map),
            "Equipo",
        )
        comparison_df = format_player_team_comparison_table(
            comparison_df,
            left_label=left_label,
            right_label=right_label,
        )
        st.dataframe(comparison_df, width="stretch", hide_index=True)
