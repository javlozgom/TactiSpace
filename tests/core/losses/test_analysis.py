import pandas as pd

from src.loss_analysis import (
    calculate_loss_metrics,
    get_loss_events,
    summarize_losses_by_player,
)


def test_get_loss_events_detects_expected_loss_types():
    df = pd.DataFrame(
        [
            {"player": "A", "event_type": "Dispossessed", "outcome": "", "x": 30},
            {"player": "A", "event_type": "Miscontrol", "outcome": "", "x": 40},
            {"player": "A", "event_type": "Error", "outcome": "", "x": 50},
            {"player": "A", "event_type": "Pass", "outcome": "Unsuccessful", "x": 60},
            {"player": "A", "event_type": "Dribble", "outcome": "Failed", "x": 70},
        ]
    )

    losses = get_loss_events(df)

    assert set(losses["loss_type"]) == {
        "Dispossessed",
        "Miscontrol",
        "Error",
        "Failed Pass",
        "Failed Dribble",
    }


def test_calculate_loss_metrics_returns_expected_counts():
    df = pd.DataFrame(
        [
            {"player": "A", "event_type": "Dispossessed", "outcome": "", "x": 30},
            {"player": "A", "event_type": "Pass", "outcome": "Unsuccessful", "x": 70},
            {"player": "A", "event_type": "Dribble", "outcome": "Failed", "x": 85},
        ]
    )

    metrics = calculate_loss_metrics(df)

    assert metrics["total_losses"] == 3
    assert metrics["losses_own_half"] == 1
    assert metrics["losses_opponent_half"] == 2
    assert metrics["losses_final_third"] == 1


def test_summarize_losses_by_player_works():
    df = pd.DataFrame(
        [
            {"player": "A", "event_type": "Dispossessed", "outcome": "", "x": 30},
            {"player": "A", "event_type": "Pass", "outcome": "Unsuccessful", "x": 70},
            {"player": "B", "event_type": "Miscontrol", "outcome": "", "x": 40},
        ]
    )

    summary = summarize_losses_by_player(df)

    assert len(summary) == 2
    assert "total_losses" in summary.columns


def test_get_loss_events_supports_categorical_event_and_outcome_columns():
    df = pd.DataFrame(
        [
            {"player": "A", "event_type": "Dispossessed", "outcome": "", "x": 30},
            {"player": "A", "event_type": "Pass", "outcome": "Unsuccessful", "x": 70},
            {"player": "B", "event_type": "Offside", "outcome": "Offside", "x": 90},
        ]
    )
    df["event_type"] = df["event_type"].astype("category")
    df["outcome"] = df["outcome"].astype("category")

    losses = get_loss_events(df)

    assert len(losses) == 2
    assert set(losses["loss_type"]) == {"Dispossessed", "Failed Pass"}
