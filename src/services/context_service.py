from __future__ import annotations

import pandas as pd

from src.core.metrics.basic import calculate_basic_metrics
from src.services.filter_service import filter_events
from src.services.spatial_service import count_visible_spatial_events, get_spatial_match_ids


def build_view_contexts(
    events_df: pd.DataFrame,
    *,
    selected_match: object,
    selected_team: object,
    selected_player: object,
    selected_minutes: tuple[int, int] | list[int] | None,
    freeze_frames_df: pd.DataFrame | None,
) -> dict[str, object]:
    """Build the filtered dataframes and metrics shared by top-level views."""
    position_context_df = filter_events(
        events_df,
        match_id=selected_match,
        team=selected_team,
        player=selected_player,
    )
    filtered_df = filter_events(
        events_df,
        match_id=selected_match,
        team=selected_team,
        player=selected_player,
        minute_range=selected_minutes,
    )
    comparative_context_df = filter_events(
        events_df,
        match_id=selected_match,
        team=selected_team,
        minute_range=selected_minutes,
    )
    spatial_match_ids = get_spatial_match_ids(selected_match, filtered_df)
    return {
        "position_context_df": position_context_df,
        "filtered_df": filtered_df,
        "comparative_context_df": comparative_context_df,
        "metrics": calculate_basic_metrics(filtered_df),
        "spatial_match_ids": spatial_match_ids,
        "visible_spatial_events": count_visible_spatial_events(filtered_df, freeze_frames_df),
    }
