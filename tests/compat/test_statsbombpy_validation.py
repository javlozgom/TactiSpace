from __future__ import annotations

import pandas as pd

from src.statsbombpy_validation import (
    build_match_validation_row,
    count_coordinate_events,
    count_events_by_type,
    get_event_type_series,
)


def test_get_event_type_series_uses_event_type_column():
    df = pd.DataFrame({"event_type": ["Pass", "Shot"]})

    result = get_event_type_series(df)

    assert result.tolist() == ["Pass", "Shot"]


def test_get_event_type_series_extracts_name_from_type_dict():
    df = pd.DataFrame({"type": [{"name": "Pass"}, {"name": "Shot"}, None]})

    result = get_event_type_series(df)

    assert result.tolist() == ["Pass", "Shot", None]


def test_count_events_by_type_counts_matches():
    df = pd.DataFrame({"event_type": ["Pass", "Shot", "Pass", "Carry"]})

    result = count_events_by_type(df, "Pass")

    assert result == 2


def test_count_coordinate_events_with_xy_columns():
    df = pd.DataFrame({"x": [10, None, 30], "y": [5, 20, None]})

    result = count_coordinate_events(df)

    assert result == 1


def test_count_coordinate_events_with_location_column():
    df = pd.DataFrame({"location": [[10, 5], None, [30], [40, 12], ["a", 1]]})

    result = count_coordinate_events(df)

    assert result == 2


def test_build_match_validation_row_with_small_dataframes():
    events_norm = pd.DataFrame(
        {
            "event_type": ["Pass", "Shot", "Pass"],
            "x": [10, 20, None],
            "y": [15, 30, 40],
        }
    )
    lineups_norm = pd.DataFrame({"player": ["A", "B"]})
    frames_norm = pd.DataFrame({"event_id": ["e1", "e1", "e2"]})
    sb_events = pd.DataFrame(
        {
            "type": [{"name": "Pass"}, {"name": "Shot"}],
            "location": [[1, 2], [3, 4]],
        }
    )
    sb_lineups = {
        "Team A": pd.DataFrame({"player_name": ["P1", "P2"]}),
        "Team B": pd.DataFrame({"player_name": ["P3"]}),
    }
    sb_frames = pd.DataFrame({"id": ["e1", "e2", "e2"]})

    row = build_match_validation_row(
        match_id=123,
        events_norm=events_norm,
        lineups_norm=lineups_norm,
        frames_norm=frames_norm,
        sb_events=sb_events,
        sb_lineups=sb_lineups,
        sb_frames=sb_frames,
    )

    assert row == {
        "match_id": 123,
        "events_parquet": 3,
        "events_sb": 2,
        "diff_events": 1,
        "passes_parquet": 2,
        "passes_sb": 1,
        "shots_parquet": 1,
        "shots_sb": 1,
        "lineups_parquet": 2,
        "lineups_sb": 3,
        "freeze_frames_parquet": 2,
        "freeze_frames_sb": 2,
        "coordinate_events_parquet": 2,
        "coordinate_events_sb": 2,
        "status": "ok",
        "warning": "",
    }
