from __future__ import annotations

import streamlit as st

from src.ui.components import render_empty_state, render_plot_card
from src.ui.components.spatial_visualizations import (
    plot_delaunay_freeze_frame,
    plot_freeze_frame,
    plot_voronoi_delaunay_freeze_frame,
)
from src.ui.config.spatial_labels import SPATIAL_PLOT_RENDER_WIDTH


def render_delaunay_network(*, context: dict[str, object]) -> None:
    """Render Delaunay-centered network plots for the selected case."""
    selected_event = context["selected_event"]
    freeze_frame_df = context["freeze_frame_df"]
    delaunay_edges_df = context["delaunay_edges_df"]
    voronoi_regions_df = context.get("voronoi_regions_df")
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

    if "delaunay" in selected_plots:
        if not is_first_block:
            st.divider()
        render_plot_card(
            "Freeze-frame + Delaunay + pase fallido",
            plot_delaunay_freeze_frame(selected_event, freeze_frame_df, delaunay_edges_df),
            "Las aristas Delaunay muestran conectividad local entre jugadores visibles.",
            badges=[("DELAUNAY", "purple"), ("REAL", "red")],
            figure_width=SPATIAL_PLOT_RENDER_WIDTH,
            border=False,
        )
        shown_any_plot = True
        is_first_block = False

    if "combined" in selected_plots and voronoi_regions_df is not None and not voronoi_regions_df.empty:
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
            "Se integran las regiones Voronoi, la red Delaunay y los identificadores visibles del caso dentro del mismo freeze-frame.",
            badges=[("VORONOI", "blue"), ("DELAUNAY", "purple"), ("REAL", "red")],
            figure_width=SPATIAL_PLOT_RENDER_WIDTH,
            border=False,
        )
        shown_any_plot = True

    if not shown_any_plot:
        render_empty_state(
            "No hay visualizaciones Delaunay activas en los controles superiores.",
            "Activa `Delaunay + pase fallido`, `Freeze-frame + pase fallido` o la vista combinada para ver esta subvista.",
        )
