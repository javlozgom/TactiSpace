import pandas as pd

from src.failed_passes import (
    get_failed_passes,
    summarize_failed_passes_by_player,
)


def test_get_failed_passes_detects_failed_pass_and_derives_columns():
    df = pd.DataFrame(
        [
            {"player": "A", "event_type": "Pass", "outcome": "Unsuccessful", "x": 20, "y": 20, "end_x": 40, "end_y": 30},
            {"player": "A", "event_type": "Pass", "outcome": "Successful", "x": 20, "y": 20, "end_x": 40, "end_y": 30},
        ]
    )

    failed_passes = get_failed_passes(df)

    assert len(failed_passes) == 1
    assert "pass_length" in failed_passes.columns
    assert "progressive" in failed_passes.columns
    assert "to_final_third" in failed_passes.columns
    assert "box_entry" in failed_passes.columns


def test_summarize_failed_passes_by_player_works():
    df = pd.DataFrame(
        [
            {"player": "A", "event_type": "Pass", "outcome": "Unsuccessful", "x": 20, "y": 20, "end_x": 40, "end_y": 30},
            {"player": "A", "event_type": "Pass", "outcome": "Unsuccessful", "x": 70, "y": 20, "end_x": 103, "end_y": 30},
            {"player": "B", "event_type": "Pass", "outcome": "Unsuccessful", "x": 20, "y": 20, "end_x": 25, "end_y": 30},
        ]
    )

    summary = summarize_failed_passes_by_player(df)

    assert len(summary) == 2
    assert "total_failed_passes" in summary.columns
    assert summary.iloc[0]["total_failed_passes"] >= summary.iloc[1]["total_failed_passes"]
