from __future__ import annotations

import pandas as pd
import streamlit as st

from src.ui.components.data_panel import render_data_panel
from src.ui.components.empty_state import render_empty_state
from src.ui.tables import build_voronoi_team_summary_df


def render_voronoi_metrics(*, context: dict[str, object]) -> None:
    """Render numeric Voronoi outputs and space-related tables."""
    team_summary_df = context["team_summary_df"]
    if team_summary_df.empty:
        render_empty_state(
            "No hay áreas Voronoi suficientes para resumir la influencia espacial por equipo.",
            "La lectura agregada depende de las regiones Voronoi válidas del freeze-frame visible.",
        )
    else:
        render_data_panel(team_summary_df, title="Influencia espacial aproximada por equipo", border=False)

    display_space_metrics = context["display_space_metrics_df"]
    if display_space_metrics.empty:
        render_empty_state(
            "No hay métricas espaciales Voronoi disponibles para este caso.",
            "La tabla aparece cuando el cálculo Voronoi genera áreas y métricas válidas por jugador visible.",
        )
        return

    st.divider()
    render_data_panel(
        context["display_space_metrics_display_df"],
        title="Métricas espaciales por jugador visible",
        border=False,
    )


def render_voronoi_team_summary_table(
    voronoi_regions_df: pd.DataFrame,
    freeze_frame_df: pd.DataFrame,
) -> None:
    """Compatibility wrapper preserved for tests and external imports."""
    summary_df = build_voronoi_team_summary_df(voronoi_regions_df, freeze_frame_df)
    if summary_df.empty:
        render_empty_state(
            "No hay áreas Voronoi suficientes para resumir la influencia espacial por equipo.",
            "La lectura agregada depende de las regiones Voronoi válidas del freeze-frame visible.",
        )
        return
    render_data_panel(summary_df, title="Influencia espacial aproximada por equipo", border=False)
