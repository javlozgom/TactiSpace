from __future__ import annotations

import pandas as pd
import streamlit as st

from src.ui.components.data_panel import render_data_panel
from src.ui.components.empty_state import render_empty_state
from src.ui.tables import build_delaunay_edge_distances_df, build_delaunay_neighbors_df


def render_delaunay_connections(*, context: dict[str, object]) -> None:
    """Render readable Delaunay connectivity tables for the selected case."""
    neighbors_df = context["neighbors_df"]
    edge_distances_df = context.get("edge_distances_df", pd.DataFrame())

    if neighbors_df.empty and edge_distances_df.empty:
        render_empty_state(
            "No hay conectividad Delaunay suficiente para resumir conexiones del caso.",
            "La vista requiere aristas válidas y jugadores visibles con identificador local en este caso.",
        )
        return

    if not neighbors_df.empty:
        render_data_panel(neighbors_df, title="Vecinos del mismo equipo por jugador visible", border=False)

    if not edge_distances_df.empty:
        if not neighbors_df.empty:
            st.divider()
        render_data_panel(edge_distances_df, title="Distancias entre puntos conectados por Delaunay", border=False)


def render_delaunay_neighbors_table(
    freeze_frame_df: pd.DataFrame,
    delaunay_edges_df: pd.DataFrame,
) -> None:
    """Compatibility wrapper preserved for external imports."""
    neighbors_df = build_delaunay_neighbors_df(freeze_frame_df, delaunay_edges_df)
    if neighbors_df.empty:
        render_empty_state(
            "No hay conectividad Delaunay suficiente para resumir vecinos del mismo equipo.",
            "La tabla requiere aristas válidas y jugadores visibles con identificador local en este caso.",
        )
        return
    render_data_panel(neighbors_df, title="Vecinos del mismo equipo por jugador visible", border=False)


def render_delaunay_edge_distances_table(
    freeze_frame_df: pd.DataFrame,
    delaunay_edges_df: pd.DataFrame,
) -> None:
    """Compatibility wrapper for the readable Delaunay edge-distance table."""
    edge_distances_df = build_delaunay_edge_distances_df(freeze_frame_df, delaunay_edges_df)
    if edge_distances_df.empty:
        render_empty_state(
            "No hay aristas Delaunay suficientes para mostrar distancias.",
            "La tabla aparece cuando el caso tiene conexiones válidas entre jugadores visibles.",
        )
        return
    render_data_panel(edge_distances_df, title="Distancias entre puntos conectados por Delaunay", border=False)
