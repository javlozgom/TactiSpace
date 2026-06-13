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


def test_ranking_helpers_cover_defaults_empty_and_ascending_cases():
    assert get_rankable_metrics_for_event("Unknown Event") == ["total_events", "successful_events", "success_rate"]
    assert get_default_ranking_metric("Unknown Event") == "total_events"

    empty_result = build_player_ranking(pd.DataFrame(), "Pass", "progressive_passes")
    assert empty_result.empty

    missing_event_df = pd.DataFrame([{"player": "A", "event_type": "Carry"}])
    assert build_player_ranking(missing_event_df, "Pass", "progressive_passes").empty

    filtered_df = pd.DataFrame(
        [
            {"player": "A", "event_type": "Pass", "outcome": "Successful", "x": 10, "end_x": 30, "end_y": 30},
            {"player": "B", "event_type": "Pass", "outcome": "Successful", "x": 10, "end_x": 15, "end_y": 30},
        ]
    )
    ascending_ranking = build_player_ranking(filtered_df, "Pass", "progressive_passes", ascending=True)
    assert ascending_ranking.iloc[0]["player"] == "B"


def test_build_player_ranking_skips_non_numeric_metrics_and_min_events():
    df = pd.DataFrame(
        [
            {"player": "A", "event_type": "Pass", "outcome": "Successful", "x": 10, "end_x": 15, "end_y": 30},
            {"player": "B", "event_type": "Pass", "outcome": "Successful", "x": 10, "end_x": 15, "end_y": 30},
        ]
    )

    assert build_player_ranking(df, "Pass", "interpretation").empty
    assert build_player_ranking(df, "Pass", "progressive_passes", min_events=2).empty
