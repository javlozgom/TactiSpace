from __future__ import annotations

import pandas as pd

from src.spatial import (
    PASS_OPTION_COLUMNS,
    evaluate_pass_options,
    extract_freeze_frame,
    suggest_alternative_pass,
)


def test_extract_freeze_frame_returns_dataframe():
    event_row = pd.Series({"id": "event-1", "freeze_frame": None})
    result = extract_freeze_frame(event_row)
    assert isinstance(result, pd.DataFrame)


def test_evaluate_pass_options_returns_expected_columns():
    teammates_df = pd.DataFrame(
        [
            {"player": "A", "x": 30.0, "y": 40.0},
            {"player": "B", "x": 45.0, "y": 28.0},
        ]
    )
    opponents_df = pd.DataFrame([{"player": "R1", "x": 35.0, "y": 39.0}])

    result = evaluate_pass_options((20.0, 30.0), teammates_df, opponents_df)

    assert isinstance(result, pd.DataFrame)
    assert list(result.columns) == PASS_OPTION_COLUMNS


def test_suggest_alternative_pass_returns_expected_keys():
    failed_pass_event = pd.Series({"player": "A", "x": 20.0, "y": 30.0})
    freeze_frame_df = pd.DataFrame()

    result = suggest_alternative_pass(failed_pass_event, freeze_frame_df)

    assert set(result) == {
        "recommended_player",
        "recommended_location",
        "score",
        "reason",
        "implemented",
    }
    assert result["implemented"] is False
