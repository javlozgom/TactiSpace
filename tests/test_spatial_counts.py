from __future__ import annotations

import pandas as pd

from src.services.spatial_service import count_visible_spatial_events
from src.ui.views.home import _count_events_with_360
from src.ui.views.spatial import _count_freeze_frame_events_in_context


def _build_events_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"event_id": "evt-1", "match_id": 1},
            {"event_id": "evt-2", "match_id": 1},
            {"event_id": "evt-3", "match_id": 1},
        ]
    )


def _build_freeze_frames_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"event_id": "evt-1", "player": "A"},
            {"event_id": "evt-1", "player": "B"},
            {"event_id": "evt-2", "player": "C"},
            {"event_id": "evt-2", "player": "D"},
            {"event_id": "evt-2", "player": "E"},
        ]
    )


def test_count_visible_spatial_events_counts_unique_events_only() -> None:
    events_df = _build_events_df()
    freeze_frames_df = _build_freeze_frames_df()

    assert count_visible_spatial_events(events_df, freeze_frames_df) == 2


def test_count_events_with_360_uses_unique_event_ids() -> None:
    events_df = _build_events_df()
    freeze_frames_df = _build_freeze_frames_df()

    assert _count_events_with_360(events_df, freeze_frames_df) == 2


def test_count_freeze_frame_events_in_context_counts_unique_events_only() -> None:
    filtered_df = _build_events_df()
    freeze_frames_df = _build_freeze_frames_df()

    assert _count_freeze_frame_events_in_context(filtered_df, freeze_frames_df) == 2
