import pandas as pd

from src.pass_decision import (
    DEFAULT_SCORING_PROFILE,
    SCORING_PROFILE_WEIGHTS,
    build_pass_options,
    get_failed_pass_candidates,
    resolve_scoring_profile,
    score_pass_options,
    suggest_alternative_pass,
)
from src.voronoi import build_voronoi_regions


def _build_failed_pass_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "event_type": "Pass",
                "player": "Passer",
                "team": "Blue",
                "outcome": "Unsuccessful",
                "x": 30,
                "y": 40,
                "end_x": 55,
                "end_y": 45,
            },
            {
                "event_type": "Pass",
                "player": "Other",
                "team": "Blue",
                "outcome": "Successful",
                "x": 20,
                "y": 30,
                "end_x": 30,
                "end_y": 35,
            },
        ]
    )


def _build_freeze_frame_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"event_id": "evt-1", "player": "Passer", "player_id": 1, "team": "Blue", "teammate": True, "actor": True, "x": 30, "y": 40, "visible": True},
            {"event_id": "evt-1", "player": "Receiver A", "player_id": 2, "team": "Blue", "teammate": True, "actor": False, "x": 60, "y": 42, "visible": True},
            {"event_id": "evt-1", "player": "Receiver B", "player_id": 3, "team": "Blue", "teammate": True, "actor": False, "x": 50, "y": 55, "visible": True},
            {"event_id": "evt-1", "player": "Opponent A", "player_id": 4, "team": "Red", "teammate": False, "actor": False, "x": 62, "y": 42, "visible": True},
            {"event_id": "evt-1", "player": "Opponent B", "player_id": 5, "team": "Red", "teammate": False, "actor": False, "x": 75, "y": 50, "visible": True},
        ]
    )


def test_get_failed_pass_candidates_detects_failed_pass():
    result = get_failed_pass_candidates(_build_failed_pass_df())
    assert len(result) == 1
    assert result.iloc[0]["progressive"] in {True, False}


def test_build_pass_options_returns_candidates():
    event_row = pd.Series({"player": "Passer", "x": 30, "y": 40})
    freeze_frame_df = _build_freeze_frame_df()
    voronoi_regions_df = build_voronoi_regions(freeze_frame_df)
    options_df = build_pass_options(event_row, freeze_frame_df, voronoi_regions_df)
    assert not options_df.empty
    assert "distance_to_passer" in options_df.columns


def test_score_pass_options_orders_by_pass_score():
    options_df = pd.DataFrame(
        [
            {"player": "A", "distance_to_passer": 10, "forward_progress": 20, "nearest_opponent_distance": 8, "voronoi_area": 15},
            {"player": "B", "distance_to_passer": 18, "forward_progress": 8, "nearest_opponent_distance": 4, "voronoi_area": 5},
        ]
    )
    scored_df = score_pass_options(options_df)
    assert scored_df.iloc[0]["pass_score"] >= scored_df.iloc[1]["pass_score"]
    assert "rank" in scored_df.columns


def test_score_pass_options_uses_intermedio_by_default():
    options_df = pd.DataFrame(
        [
            {"player": "A", "distance_to_passer": 10, "forward_progress": 20, "nearest_opponent_distance": 8, "voronoi_area": 15},
            {"player": "B", "distance_to_passer": 18, "forward_progress": 8, "nearest_opponent_distance": 4, "voronoi_area": 5},
        ]
    )

    default_df = score_pass_options(options_df)
    explicit_df = score_pass_options(options_df, scoring_profile="Intermedio")

    assert default_df["pass_score"].tolist() == explicit_df["pass_score"].tolist()
    assert default_df["scoring_profile"].tolist() == ["Intermedio", "Intermedio"]


def test_score_pass_options_changes_ranking_across_profiles():
    options_df = pd.DataFrame(
        [
            {"player": "Safe", "distance_to_passer": 5, "forward_progress": 5, "nearest_opponent_distance": 12, "voronoi_area": 6},
            {"player": "Risky", "distance_to_passer": 20, "forward_progress": 25, "nearest_opponent_distance": 2, "voronoi_area": 20},
        ]
    )

    conservative_df = score_pass_options(options_df, scoring_profile="Conservador")
    risky_df = score_pass_options(options_df, scoring_profile="Arriesgado")

    assert conservative_df.iloc[0]["player"] == "Safe"
    assert risky_df.iloc[0]["player"] == "Risky"


def test_resolve_scoring_profile_falls_back_to_intermedio():
    assert resolve_scoring_profile("Desconocido") == DEFAULT_SCORING_PROFILE
    assert resolve_scoring_profile(None) == DEFAULT_SCORING_PROFILE
    assert SCORING_PROFILE_WEIGHTS[DEFAULT_SCORING_PROFILE]["distance_to_passer_penalty"] == -0.3


def test_suggest_alternative_pass_returns_expected_keys():
    event_row = pd.Series({"player": "Passer", "x": 30, "y": 40})
    freeze_frame_df = _build_freeze_frame_df()
    voronoi_regions_df = build_voronoi_regions(freeze_frame_df)
    result = suggest_alternative_pass(event_row, freeze_frame_df, voronoi_regions_df)
    assert {"recommended_player", "recommended_location", "score", "reason", "options", "score_breakdown", "scoring_profile"}.issubset(result.keys())


def test_suggest_alternative_pass_exposes_score_breakdown():
    event_row = pd.Series({"player": "Passer", "x": 30, "y": 40})
    freeze_frame_df = _build_freeze_frame_df()
    voronoi_regions_df = build_voronoi_regions(freeze_frame_df)

    result = suggest_alternative_pass(event_row, freeze_frame_df, voronoi_regions_df)

    factor_names = {row["factor"] for row in result["score_breakdown"]}
    assert {"progression", "nearest_opponent_distance", "voronoi_area", "distance_penalty", "final_score"}.issubset(factor_names)


def test_suggest_alternative_pass_uses_requested_profile_in_breakdown():
    event_row = pd.Series({"player": "Passer", "x": 30, "y": 40})
    freeze_frame_df = _build_freeze_frame_df()
    voronoi_regions_df = build_voronoi_regions(freeze_frame_df)

    result = suggest_alternative_pass(event_row, freeze_frame_df, voronoi_regions_df, scoring_profile="Conservador")

    weights = {row["factor"]: row["weight"] for row in result["score_breakdown"] if row["weight"] is not None}
    assert result["scoring_profile"] == "Conservador"
    assert weights["progression"] == 0.5
    assert weights["nearest_opponent_distance"] == 1.3
    assert weights["voronoi_area"] == 0.8
    assert weights["distance_penalty"] == -0.7
