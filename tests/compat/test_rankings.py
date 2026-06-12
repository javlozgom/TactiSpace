import pandas as pd

from src.rankings import (
    build_player_ranking,
    get_default_ranking_metric,
    get_rankable_metrics_for_event,
)


def test_get_rankable_metrics_for_event_pass():
    metrics = get_rankable_metrics_for_event("Pass")

    assert "progressive_passes" in metrics
    assert "completion_rate" in metrics


def test_get_default_ranking_metric_pass():
    assert get_default_ranking_metric("Pass") == "progressive_passes"


def test_build_player_ranking_with_two_players():
    df = pd.DataFrame(
        [
            {"player": "A", "event_type": "Pass", "outcome": "Successful", "x": 10, "end_x": 30, "end_y": 30},
            {"player": "A", "event_type": "Pass", "outcome": "Successful", "x": 20, "end_x": 35, "end_y": 30},
            {"player": "B", "event_type": "Pass", "outcome": "Successful", "x": 10, "end_x": 15, "end_y": 30},
        ]
    )

    ranking = build_player_ranking(df, "Pass", "progressive_passes")

    assert len(ranking) == 2
    assert ranking.iloc[0]["player"] == "A"
    assert ranking.iloc[0]["rank"] == 1
