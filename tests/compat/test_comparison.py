import pandas as pd

from src.comparison import (
    advanced_comparison_to_dataframe,
    compare_player_contexts,
    compare_player_to_team,
    compare_two_players,
    comparison_dict_to_dataframe,
    filter_player_context,
    get_available_matches,
    get_players_for_match_team,
    get_teams_for_match,
)


def _build_comparison_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "match_id": 1,
                "team": "Blue",
                "player": "A",
                "event_type": "Pass",
                "outcome": "Successful",
                "x": 10,
                "y": 20,
                "end_x": 25,
                "end_y": 20,
            },
            {
                "match_id": 1,
                "team": "Blue",
                "player": "A",
                "event_type": "Pass",
                "outcome": "Unsuccessful",
                "x": 20,
                "y": 20,
                "end_x": 24,
                "end_y": 20,
            },
            {
                "match_id": 1,
                "team": "Blue",
                "player": "B",
                "event_type": "Pass",
                "outcome": "Successful",
                "x": 30,
                "y": 20,
                "end_x": 50,
                "end_y": 20,
            },
            {
                "match_id": 1,
                "team": "Red",
                "player": "C",
                "event_type": "Pass",
                "outcome": "Successful",
                "x": 40,
                "y": 20,
                "end_x": 70,
                "end_y": 20,
            },
            {
                "match_id": 2,
                "team": "Blue",
                "player": "A",
                "event_type": "Pass",
                "outcome": "Successful",
                "x": 15,
                "y": 20,
                "end_x": 35,
                "end_y": 20,
            },
            {
                "match_id": 2,
                "team": "Green",
                "player": "D",
                "event_type": "Pass",
                "outcome": "Unsuccessful",
                "x": 25,
                "y": 20,
                "end_x": 33,
                "end_y": 20,
            },
            {
                "match_id": 2,
                "team": "Green",
                "player": "D",
                "event_type": "Pass",
                "outcome": "Successful",
                "x": 35,
                "y": 20,
                "end_x": 55,
                "end_y": 20,
            },
        ]
    )


def test_compare_player_to_team_returns_expected_keys():
    df = _build_comparison_df()

    comparison = compare_player_to_team(df, "A", "Pass")

    assert comparison["player"] == "A"
    assert comparison["team"] == "Blue"
    assert comparison["event_type"] == "Pass"
    assert "player_metrics" in comparison
    assert "team_metrics" in comparison
    assert "completion_rate" in comparison["differences"]
    assert comparison["team_metrics"]["total_passes"] == 4


def test_compare_two_players_returns_expected_keys():
    df = pd.DataFrame(
        [
            {"player": "A", "event_type": "Carry", "x": 10, "y": 10, "end_x": 30, "end_y": 10},
            {"player": "B", "event_type": "Carry", "x": 20, "y": 10, "end_x": 25, "end_y": 10},
        ]
    )

    comparison = compare_two_players(df, "A", "B", "Carry")

    assert comparison["player_a"] == "A"
    assert comparison["player_b"] == "B"
    assert comparison["event_type"] == "Carry"
    assert "total_carries" in comparison["differences"]


def test_get_available_matches_returns_sorted_values():
    df = _build_comparison_df()

    assert get_available_matches(df) == [1, 2]


def test_get_teams_for_match_returns_match_teams():
    df = _build_comparison_df()

    assert get_teams_for_match(df, 1) == ["Blue", "Red"]


def test_get_players_for_match_team_returns_match_team_players():
    df = _build_comparison_df()

    assert get_players_for_match_team(df, 2, "Green") == ["D"]


def test_get_players_for_match_team_excludes_unknown_placeholder():
    df = pd.DataFrame(
        [
            {"match_id": 3, "team": "Blue", "player": "Unknown"},
            {"match_id": 3, "team": "Blue", "player": " Player A "},
            {"match_id": 3, "team": "Blue", "player": "Player B"},
        ]
    )

    assert get_players_for_match_team(df, 3, "Blue") == [" Player A ", "Player B"]


def test_get_players_for_match_team_returns_empty_when_only_unknown_is_available():
    df = pd.DataFrame(
        [
            {"match_id": 4, "team": "Blue", "player": "Unknown"},
            {"match_id": 4, "team": "Blue", "player": " unknown "},
        ]
    )

    assert get_players_for_match_team(df, 4, "Blue") == []


def test_filter_player_context_filters_correctly():
    df = _build_comparison_df()

    result = filter_player_context(df, 1, "Blue", "A")

    assert len(result) == 2
    assert result["match_id"].eq(1).all()
    assert result["team"].eq("Blue").all()
    assert result["player"].eq("A").all()


def test_compare_player_contexts_compares_players_from_different_teams():
    df = _build_comparison_df()

    comparison = compare_player_contexts(
        df,
        {"match_id": 1, "team": "Blue", "player": "A"},
        {"match_id": 2, "team": "Green", "player": "D"},
        "Pass",
    )

    assert comparison["context_a"]["team"] == "Blue"
    assert comparison["context_b"]["team"] == "Green"
    assert comparison["event_type"] == "Pass"
    assert "total_passes" in comparison["differences"]


def test_compare_player_contexts_allows_same_player_in_different_matches():
    df = _build_comparison_df()

    comparison = compare_player_contexts(
        df,
        {"match_id": 1, "team": "Blue", "player": "A"},
        {"match_id": 2, "team": "Blue", "player": "A"},
        "Pass",
    )

    assert comparison["context_a"]["match_id"] == 1
    assert comparison["context_b"]["match_id"] == 2
    assert comparison["metrics_a"]["total_passes"] == 2
    assert comparison["metrics_b"]["total_passes"] == 1


def test_comparison_dict_to_dataframe_returns_expected_columns():
    comparison = {
        "differences": {
            "total_passes": {
                "value_player": 5,
                "value_team": 10,
                "difference": -5,
                "relative_difference_pct": -50.0,
            }
        }
    }

    result = comparison_dict_to_dataframe(comparison)

    assert list(result.columns) == [
        "metric",
        "value_a",
        "value_b",
        "difference",
        "relative_difference_pct",
    ]


def test_advanced_comparison_to_dataframe_returns_expected_columns():
    comparison = {
        "differences": {
            "total_passes": {
                "value_a": 5,
                "value_b": 10,
                "difference": -5,
                "relative_difference_pct": -50.0,
            }
        }
    }

    result = advanced_comparison_to_dataframe(comparison)

    assert list(result.columns) == [
        "metric",
        "value_a",
        "value_b",
        "difference",
        "relative_difference_pct",
    ]


def test_comparison_helpers_handle_empty_dataframe():
    df = pd.DataFrame()

    assert get_available_matches(df) == []
    assert get_teams_for_match(df, 1) == []
    assert get_players_for_match_team(df, 1, "Blue") == []
    assert filter_player_context(df, 1, "Blue", "A").empty
    assert compare_player_contexts(
        df,
        {"match_id": 1, "team": "Blue", "player": "A"},
        {"match_id": 2, "team": "Green", "player": "D"},
        "Pass",
    ) == {}
