import pandas as pd

from src.metrics import calculate_basic_metrics, calculate_player_summary


def build_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"player": "Rodri", "event_type": "Pass", "outcome": "Successful"},
            {"player": "Rodri", "event_type": "Pass", "outcome": "Unsuccessful"},
            {"player": "Morata", "event_type": "Shot", "outcome": "Goal"},
            {"player": "Pedri", "event_type": "Carry", "outcome": "Successful"},
            {"player": "Le Normand", "event_type": "Duel", "outcome": "Unknown"},
        ]
    )


def test_calculate_basic_metrics_total_events():
    metrics = calculate_basic_metrics(build_df())
    assert metrics["total_events"] == 5
    assert metrics["total_passes"] == 2
    assert metrics["total_duels"] == 1


def test_calculate_basic_metrics_success_rate():
    metrics = calculate_basic_metrics(build_df())
    assert metrics["successful_events"] == 3
    assert metrics["success_rate"] == 60.0


def test_calculate_player_summary():
    summary = calculate_player_summary(build_df())
    rodri_passes = summary[
        (summary["player"] == "Rodri") & (summary["event_type"] == "Pass")
    ].iloc[0]

    assert rodri_passes["event_count"] == 2
    assert rodri_passes["successful_actions"] == 1
    assert rodri_passes["success_pct"] == 50.0


def test_calculate_player_summary_with_categorical_columns():
    df = build_df().copy()
    df["player"] = df["player"].astype("category")
    df["event_type"] = df["event_type"].astype("category")
    df["outcome"] = df["outcome"].astype("category")

    summary = calculate_player_summary(df)

    rodri_passes = summary[
        (summary["player"].astype(str) == "Rodri") & (summary["event_type"].astype(str) == "Pass")
    ].iloc[0]
    assert rodri_passes["event_count"] == 2
