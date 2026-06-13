import pandas as pd

from src.pass_decision import (
    DEFAULT_SCORING_PROFILE,
    SCORING_PROFILE_WEIGHTS,
    describe_pass_recommendation,
    describe_voronoi_recommendation,
    build_pass_options,
    get_failed_pass_candidates,
    resolve_scoring_profile,
    score_pass_options,
    suggest_alternative_pass,
    suggest_alternative_pass_by_voronoi_area,
)
from src.core.spatial.pass_decision import (
    _build_score_breakdown,
    _build_voronoi_breakdown,
    _compute_box_entry_mask,
    _compute_final_third_mask,
    _compute_pass_length_series,
    _compute_progressive_mask,
    _lookup_voronoi_area,
    _nearest_opponent_distance,
    _normalize_series,
    _to_float,
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


def test_get_failed_pass_candidates_handles_empty_non_pass_and_success_only_inputs():
    assert get_failed_pass_candidates(pd.DataFrame()).empty
    assert get_failed_pass_candidates(pd.DataFrame([{"event_type": "Carry"}])).empty
    assert get_failed_pass_candidates(
        pd.DataFrame([{"event_type": "Pass", "outcome": "Successful", "x": 1, "y": 1, "end_x": 2, "end_y": 2}])
    ).empty


def test_build_pass_options_returns_empty_schema_when_no_teammates_exist():
    event_row = pd.Series({"player": "Passer", "x": 30, "y": 40})
    freeze_frame_df = pd.DataFrame([{"player": "Opponent", "teammate": False, "x": 40, "y": 50}])

    options_df = build_pass_options(event_row, freeze_frame_df)

    assert options_df.empty
    assert "distance_to_passer" in options_df.columns


def test_build_pass_options_excludes_passer_by_name_when_actor_column_is_absent():
    event_row = pd.Series({"player": "Passer", "x": 30, "y": 40})
    freeze_frame_df = pd.DataFrame(
        [
            {"player": "Passer", "teammate": True, "x": 30, "y": 40},
            {"player": "Receiver", "teammate": True, "x": 50, "y": 42},
            {"player": "Opponent", "teammate": False, "x": 55, "y": 42},
        ]
    )

    options_df = build_pass_options(event_row, freeze_frame_df)

    assert options_df["player"].tolist() == ["Receiver"]


def test_build_pass_options_skips_candidates_with_invalid_coordinates():
    event_row = pd.Series({"player": "Passer", "x": 30, "y": 40})
    freeze_frame_df = pd.DataFrame(
        [
            {"player": "Receiver A", "teammate": True, "x": "bad", "y": 42},
            {"player": "Receiver B", "teammate": True, "x": 50, "y": 55},
            {"player": "Opponent", "teammate": False, "x": 60, "y": 50},
        ]
    )

    options_df = build_pass_options(event_row, freeze_frame_df)

    assert options_df["player"].tolist() == ["Receiver B"]


def test_suggest_alternative_pass_and_voronoi_return_empty_recommendation_without_candidates():
    event_row = pd.Series({"player": "Passer", "x": 30, "y": 40})
    freeze_frame_df = pd.DataFrame()

    scoring_result = suggest_alternative_pass(event_row, freeze_frame_df)
    voronoi_result = suggest_alternative_pass_by_voronoi_area(event_row, freeze_frame_df)

    assert scoring_result["recommended_player"] is None
    assert "falta de candidatos" in describe_pass_recommendation({}).lower()
    assert voronoi_result["recommended_player"] is None
    assert "falta de candidatos" in describe_voronoi_recommendation({}).lower()


def test_suggest_alternative_pass_by_voronoi_area_returns_ranked_breakdown():
    event_row = pd.Series({"player": "Passer", "x": 30, "y": 40})
    freeze_frame_df = _build_freeze_frame_df()
    voronoi_regions_df = build_voronoi_regions(freeze_frame_df)

    result = suggest_alternative_pass_by_voronoi_area(event_row, freeze_frame_df, voronoi_regions_df)

    assert result["recommended_player"] is not None
    assert result["options"].iloc[0]["rank"] == 1
    assert {item["factor"] for item in result["score_breakdown"]} == {
        "voronoi_area",
        "nearest_opponent_distance",
        "forward_progress",
        "distance_to_passer",
        "final_score",
    }


def test_low_level_pass_decision_helpers_cover_missing_branches():
    df = pd.DataFrame([{"x": 0, "y": 0, "end_x": 3, "end_y": 4}])
    assert _compute_pass_length_series(df).tolist() == [5.0]
    assert _compute_pass_length_series(pd.DataFrame([{"x": 0}])).tolist() == [0.0]
    assert _compute_progressive_mask(pd.DataFrame([{"x": 0, "end_x": 12}])).tolist() == [True]
    assert _compute_progressive_mask(pd.DataFrame([{"x": 0}])).tolist() == [False]
    assert _compute_final_third_mask(pd.DataFrame([{"end_x": 80}])).tolist() == [True]
    assert _compute_final_third_mask(pd.DataFrame([{"x": 1}])).tolist() == [False]
    assert _compute_box_entry_mask(pd.DataFrame([{"end_x": 102, "end_y": 40}])).tolist() == [True]
    assert _compute_box_entry_mask(pd.DataFrame([{"end_x": 102}])).tolist() == [False]
    assert _nearest_opponent_distance(10, 10, pd.DataFrame()) == 0.0
    assert _nearest_opponent_distance(10, 10, pd.DataFrame([{"x": "bad", "y": 3}])) == 0.0
    assert _normalize_series([5, 5]).tolist() == [0.0, 0.0]
    assert _to_float("bad", 7.0) == 7.0
    assert _to_float(None, 3.0) == 3.0


def test_lookup_voronoi_area_supports_player_id_name_and_coordinate_matching():
    by_id_df = pd.DataFrame([{"player_id": 7, "voronoi_area": 12.5}])
    by_name_df = pd.DataFrame([{"player": "Receiver", "area": 8.5}])
    by_coords_df = pd.DataFrame([{"x": 50.0, "y": 42.0, "voronoi_area": 9.5}])

    assert _lookup_voronoi_area(pd.Series({"player_id": 7}), by_id_df) == 12.5
    assert _lookup_voronoi_area(pd.Series({"player": "Receiver"}), by_name_df) == 8.5
    assert _lookup_voronoi_area(pd.Series({"x": 50.0, "y": 42.0}), by_coords_df) == 9.5
    assert _lookup_voronoi_area(pd.Series({"player": "Missing"}), pd.DataFrame()) == 0.0


def test_score_and_voronoi_breakdown_helpers_are_explicit():
    option = pd.Series(
        {
            "forward_progress_norm": 0.6,
            "nearest_opponent_distance_norm": 0.8,
            "voronoi_area_norm": 0.5,
            "distance_to_passer_norm": 0.2,
            "pass_score": 1.23,
            "voronoi_area": 9.0,
            "nearest_opponent_distance": 6.0,
            "forward_progress": 12.0,
            "distance_to_passer": 18.0,
        }
    )

    score_breakdown = _build_score_breakdown(option, scoring_profile="Arriesgado")
    voronoi_breakdown = _build_voronoi_breakdown(option)

    assert score_breakdown[-1]["contribution"] == 1.23
    assert score_breakdown[0]["weight"] == SCORING_PROFILE_WEIGHTS["Arriesgado"]["forward_progress"]
    assert voronoi_breakdown[-1]["direction"] == "Resultado"
