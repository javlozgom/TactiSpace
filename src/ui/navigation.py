from __future__ import annotations

import pandas as pd

from src.ui.navigation_config import (
    EVENT_ANALYSIS_VIEW,
    MATCH_OVERVIEW_VIEW,
    RAW_DEBUG_VIEW,
    canonicalize_view_name,
)
from src.ui.views.event_analysis import render_event_analysis_view
from src.ui.views.match_overview import render_match_overview_view
from src.ui.views.raw_debug import render_raw_debug_view


def render_active_view(
    active_view: str,
    *,
    filtered_df: pd.DataFrame,
    events_df: pd.DataFrame,
    freeze_frames_df: pd.DataFrame | None,
    metrics: dict[str, object],
    selected_match: object,
    selected_team: object,
    selected_player: object,
    position_context_df: pd.DataFrame,
    comparative_context_df: pd.DataFrame,
    spatial_match_ids: tuple[str, ...] | None,
    visible_spatial_events: int,
) -> None:
    """Route the selected top-level view inside the main content column."""
    _ = spatial_match_ids
    active_view = canonicalize_view_name(active_view)

    if active_view == MATCH_OVERVIEW_VIEW:
        render_match_overview_view(
            filtered_df,
            events_df,
            freeze_frames_df,
            metrics,
            selected_match,
            selected_team,
            selected_player,
            position_context_df,
            spatial_events_count=visible_spatial_events,
        )
    elif active_view == EVENT_ANALYSIS_VIEW:
        render_event_analysis_view(
            filtered_df=filtered_df,
            events_df=events_df,
            freeze_frames_df=freeze_frames_df,
            selected_player=selected_player,
            comparative_context_df=comparative_context_df,
        )
    elif active_view == RAW_DEBUG_VIEW:
        render_raw_debug_view(filtered_df)
