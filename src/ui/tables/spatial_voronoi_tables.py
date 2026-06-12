from __future__ import annotations

import pandas as pd

from src.ui.tables.spatial_common_tables import drop_empty_display_columns, merge_spatial_reference_ids
from src.ui.views.spatial_formatters import safe_display
from src.ui.views.spatial_utils import visible_freeze_frame_df


def build_display_space_metrics_df(
    space_metrics_df: pd.DataFrame,
    freeze_frame_df: pd.DataFrame,
) -> pd.DataFrame:
    """Prepare one readable table of per-player space metrics without changing calculations."""
    if space_metrics_df.empty:
        return pd.DataFrame()

    display_space_metrics = merge_spatial_reference_ids(space_metrics_df.copy(), freeze_frame_df)
    for numeric_col in [
        "x",
        "y",
        "area",
        "voronoi_area",
        "nearest_opponent_distance",
        "distance_to_passer",
        "forward_progress",
        "pass_score",
    ]:
        if numeric_col in display_space_metrics.columns:
            display_space_metrics[numeric_col] = pd.to_numeric(display_space_metrics[numeric_col], errors="coerce").round(3)

    preferred_columns = [
        col
        for col in [
            "spatial_reference_id",
            "player",
            "teammate",
            "x",
            "y",
            "voronoi_area",
            "nearest_opponent_distance",
            "distance_to_passer",
            "forward_progress",
            "pass_score",
        ]
        if col in display_space_metrics.columns
    ]
    return drop_empty_display_columns(display_space_metrics[preferred_columns] if preferred_columns else display_space_metrics)


def build_voronoi_team_summary_df(
    voronoi_regions_df: pd.DataFrame,
    freeze_frame_df: pd.DataFrame,
) -> pd.DataFrame:
    """Aggregate visible Voronoi influence by team for one case."""
    if voronoi_regions_df.empty:
        return pd.DataFrame()

    working_df = voronoi_regions_df.copy()
    area_column = "voronoi_area" if "voronoi_area" in working_df.columns else "area"
    if area_column not in working_df.columns:
        return pd.DataFrame()

    working_df[area_column] = pd.to_numeric(working_df[area_column], errors="coerce")
    working_df = working_df.dropna(subset=[area_column])
    working_df = working_df[working_df[area_column] > 0].copy()
    if working_df.empty:
        return pd.DataFrame()

    if "team" not in working_df.columns:
        working_df["team"] = pd.NA

    visible_players_df = visible_freeze_frame_df(freeze_frame_df)
    visible_counts_df = pd.DataFrame(columns=["team", "Jugadores visibles"])
    if not visible_players_df.empty and "team" in visible_players_df.columns:
        visible_counts_df = (
            visible_players_df.assign(team=visible_players_df["team"].map(safe_display))
            .groupby("team", dropna=False)
            .size()
            .reset_index(name="Jugadores visibles")
        )

    working_df["team"] = working_df["team"].map(safe_display)
    summary_df = working_df.groupby("team", dropna=False)[area_column].sum().reset_index(name="Área Voronoi")
    total_area = float(summary_df["Área Voronoi"].sum()) if not summary_df.empty else 0.0
    summary_df["% ocupación del campo"] = (summary_df["Área Voronoi"] / total_area) * 100 if total_area > 0 else 0.0
    if not visible_counts_df.empty:
        summary_df = summary_df.merge(visible_counts_df, on="team", how="left")
    else:
        summary_df["Jugadores visibles"] = pd.NA
    summary_df = summary_df.rename(columns={"team": "Equipo"})
    summary_df["Área Voronoi"] = pd.to_numeric(summary_df["Área Voronoi"], errors="coerce").round(3)
    summary_df["% ocupación del campo"] = pd.to_numeric(summary_df["% ocupación del campo"], errors="coerce").round(3)
    return summary_df.sort_values("Área Voronoi", ascending=False).reset_index(drop=True)
