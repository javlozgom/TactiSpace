from __future__ import annotations

import streamlit as st

from src.ui.components import render_empty_state, render_plot_card
from src.ui.components.spatial_visualizations import (
    plot_freeze_frame,
    plot_voronoi_delaunay_freeze_frame,
    plot_voronoi_freeze_frame,
)
from src.ui.config.spatial_labels import SPATIAL_PLOT_RENDER_WIDTH


def render_voronoi_view(*, context: dict[str, object]) -> None:
    """Render Voronoi-centered visual plots for the selected case."""
    selected_event = context["selected_event"]
    freeze_frame_df = context["freeze_frame_df"]
    voronoi_regions_df = context["voronoi_regions_df"]
    delaunay_edges_df = context["delaunay_edges_df"]
    selected_plots = context["selected_plots"]

    shown_any_plot = False
    is_first_block = True
    if "original" in selected_plots:
        render_plot_card(
            "Freeze-frame del pase fallido",
            plot_freeze_frame(selected_event, freeze_frame_df),
            "Se muestran compañeros, rivales, actor y trayectoria del pase fallido.",
            badges=[("REAL", "red")],
            figure_width=SPATIAL_PLOT_RENDER_WIDTH,
            border=False,
        )
        shown_any_plot = True
        is_first_block = False

    if "voronoi" in selected_plots:
        if not is_first_block:
            st.divider()
        render_plot_card(
            "Freeze-frame + Voronoi + pase fallido",
            plot_voronoi_freeze_frame(selected_event, freeze_frame_df, voronoi_regions_df),
            "Las regiones aproximan el espacio de influencia de cada jugador visible.",
            badges=[("VORONOI", "blue"), ("REAL", "red")],
            figure_width=SPATIAL_PLOT_RENDER_WIDTH,
            border=False,
        )
        shown_any_plot = True
        is_first_block = False

    if "combined" in selected_plots:
        if not is_first_block:
            st.divider()
        render_plot_card(
            "Vista combinada Voronoi + Delaunay",
            plot_voronoi_delaunay_freeze_frame(
                selected_event,
                freeze_frame_df,
                voronoi_regions_df,
                delaunay_edges_df,
            ),
            "Vista combinada entre zonas de influencia y conectividad local del snapshot.",
            badges=[("VORONOI", "blue"), ("DELAUNAY", "purple"), ("REAL", "red")],
            figure_width=SPATIAL_PLOT_RENDER_WIDTH,
            border=False,
        )
        shown_any_plot = True

    if not shown_any_plot:
        render_empty_state(
            "No hay visualizaciones Voronoi activas en los controles superiores.",
            "Activa `Voronoi + pase fallido`, `Freeze-frame + pase fallido` o la vista combinada para ver esta subvista.",
        )
