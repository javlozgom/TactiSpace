from __future__ import annotations

import pandas as pd

from src.ui.tables.spatial_common_tables import drop_empty_display_columns


def build_voronoi_debug_df(voronoi_regions_df: pd.DataFrame) -> pd.DataFrame:
    """Prepare one technical Voronoi table with readable columns only."""
    if voronoi_regions_df.empty:
        return pd.DataFrame()

    debug_df = voronoi_regions_df.copy()
    preferred_columns = [col for col in ["player", "team", "teammate", "x", "y", "area", "voronoi_area"] if col in debug_df.columns]
    if preferred_columns:
        debug_df = debug_df[preferred_columns]
    for numeric_col in ["x", "y", "area", "voronoi_area"]:
        if numeric_col in debug_df.columns:
            debug_df[numeric_col] = pd.to_numeric(debug_df[numeric_col], errors="coerce").round(3)
    return drop_empty_display_columns(debug_df)


def build_delaunay_edges_debug_df(delaunay_edges_df: pd.DataFrame) -> pd.DataFrame:
    """Prepare one technical Delaunay edge table without altering the source data."""
    if delaunay_edges_df.empty:
        return pd.DataFrame()

    debug_df = delaunay_edges_df.copy()
    preferred_columns = [
        col
        for col in ["a_x", "a_y", "b_x", "b_y", "a_teammate", "b_teammate", "edge_length", "distance", "progression"]
        if col in debug_df.columns
    ]
    if preferred_columns:
        debug_df = debug_df[preferred_columns]
    for numeric_col in ["a_x", "a_y", "b_x", "b_y", "edge_length", "distance", "progression"]:
        if numeric_col in debug_df.columns:
            debug_df[numeric_col] = pd.to_numeric(debug_df[numeric_col], errors="coerce").round(3)
    return drop_empty_display_columns(debug_df)
