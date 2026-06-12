import pandas as pd

from src.core.metrics.events import (
    _contains_any,
    _distance_series,
    _filter_event_df,
    _get_outcome_series,
    _round_distance,
    _round_pct,
    _safe_mean,
    calculate_carry_metrics,
    calculate_dribble_metrics,
    calculate_duel_metrics,
    calculate_event_card_stats,
    calculate_pass_metrics,
    calculate_pressure_metrics,
    calculate_recovery_metrics,
    calculate_shot_metrics,
    calculate_specific_event_metrics,
    get_event_analysis_description,
    get_metric_definitions,
    get_metric_display_name,
    get_supported_specific_metric_events,
)


def test_calculate_event_card_stats_success_event():
    df = pd.DataFrame(
        [
            {"event_type": "Pass", "outcome": "Successful"},
            {"event_type": "Pass", "outcome": "Complete"},
            {"event_type": "Pass", "outcome": "Unsuccessful"},
        ]
    )

    stats = calculate_event_card_stats(df, "Pass")

    assert stats["total_events"] == 3
    assert stats["successful_events"] == 2
    assert stats["success_rate"] == 66.7
    assert stats["show_success_rate"] is True


def test_calculate_event_card_stats_negative_event():
    df = pd.DataFrame(
        [
            {"event_type": "Dispossessed", "outcome": ""},
            {"event_type": "Dispossessed", "outcome": ""},
        ]
    )

    stats = calculate_event_card_stats(df, "Dispossessed")

    assert stats["total_events"] == 2
    assert stats["successful_events"] == 0
    assert stats["show_success_rate"] is False
    assert stats["info_label"] == "Evento de riesgo"


def test_calculate_pass_metrics_simple():
    df = pd.DataFrame(
        [
            {"event_type": "Pass", "x": 30, "y": 40, "end_x": 45, "end_y": 40, "outcome": ""},
            {"event_type": "Pass", "x": 70, "y": 20, "end_x": 105, "end_y": 30, "outcome": "Successful"},
            {"event_type": "Pass", "x": 50, "y": 30, "end_x": 55, "end_y": 30, "outcome": "Unsuccessful"},
        ]
    )

    metrics = calculate_pass_metrics(df)

    assert metrics["total_passes"] == 3
    assert metrics["completed_passes"] == 2
    assert metrics["incomplete_passes"] == 1
    assert metrics["completion_rate"] == 66.7
    assert metrics["progressive_passes"] == 2
    assert metrics["final_third_passes"] == 1
    assert metrics["box_entries"] == 1


def test_calculate_carry_metrics_simple():
    df = pd.DataFrame(
        [
            {"event_type": "Carry", "x": 20, "y": 30, "end_x": 35, "end_y": 30},
            {"event_type": "Carry", "x": 75, "y": 25, "end_x": 103, "end_y": 40},
        ]
    )

    metrics = calculate_carry_metrics(df)

    assert metrics["total_carries"] == 2
    assert metrics["progressive_carries"] == 2
    assert metrics["final_third_carries"] == 1
    assert metrics["box_entries"] == 1
    assert metrics["carries_with_end_location"] == 2


def test_calculate_shot_metrics_simple():
    df = pd.DataFrame(
        [
            {"event_type": "Shot", "x": 100, "y": 40, "outcome": "Goal"},
            {"event_type": "Shot", "x": 102, "y": 41, "outcome": "Goal"},
            {"event_type": "Shot", "x": 110, "y": 35, "outcome": "Saved"},
            {"event_type": "Shot", "x": 90, "y": 50, "outcome": "Off Target"},
        ]
    )

    metrics = calculate_shot_metrics(df)

    assert metrics["total_shots"] == 4
    assert metrics["goals"] == 2
    assert metrics["saved"] == 1
    assert metrics["off_target"] == 1
    assert metrics["blocked"] == 0
    assert metrics["average_distance_to_goal"] > 0
    assert metrics["conversion_rate"] == 50.0
    assert metrics["shot_on_target_rate"] == 75.0
    assert metrics["goals_per_shot"] == 0.5


def test_calculate_specific_event_metrics_falls_back_to_generic():
    df = pd.DataFrame(
        [
            {"event_type": "Block", "x": 70, "y": 30, "outcome": "Successful"},
            {"event_type": "Block", "x": 72, "y": 31, "outcome": "Unsuccessful"},
        ]
    )

    metrics = calculate_specific_event_metrics(df, "Block")

    assert metrics["event_type"] == "Block"
    assert metrics["total_events"] == 2
    assert metrics["successful_events"] == 1
    assert metrics["success_rate"] == 50.0


def test_calculate_specific_event_metrics_includes_shot_efficiency_metrics():
    df = pd.DataFrame(
        [
            {"event_type": "Shot", "x": 100, "y": 40, "outcome": "Goal"},
            {"event_type": "Shot", "x": 102, "y": 41, "outcome": "Goal"},
            {"event_type": "Shot", "x": 110, "y": 35, "outcome": "Saved"},
            {"event_type": "Shot", "x": 90, "y": 50, "outcome": "Off Target"},
        ]
    )

    metrics = calculate_specific_event_metrics(df, "Shot")

    assert metrics["conversion_rate"] == 50.0
    assert metrics["shot_on_target_rate"] == 75.0
    assert metrics["goals_per_shot"] == 0.5


def test_get_supported_specific_metric_events_not_empty():
    events = get_supported_specific_metric_events()

    assert isinstance(events, list)
    assert len(events) > 0
    assert "Pass" in events


def test_get_event_analysis_description_known_event():
    description = get_event_analysis_description("Pass")

    assert "pases" in description.lower()


def test_get_metric_definitions_contains_expected_keys():
    definitions = get_metric_definitions()

    assert "% acierto" in definitions
    assert "Último tercio" in definitions


def test_get_metric_display_name_returns_spanish_label():
    assert get_metric_display_name("completion_rate") == "% acierto"
    assert get_metric_display_name("unknown_metric") == "Unknown metric"


def test_event_metric_helpers_handle_empty_and_numeric_fallbacks():
    empty_df = pd.DataFrame(columns=["event_type", "outcome"])

    filtered = _filter_event_df(empty_df, "Pass")
    outcomes = _get_outcome_series(empty_df)
    contains = _contains_any(pd.Series(dtype="object"), ("goal",))
    distances = _distance_series(pd.DataFrame([{"x": 1, "y": 2}]))

    assert filtered.empty
    assert outcomes.tolist() == []
    assert contains.tolist() == []
    assert len(distances) == 1 and pd.isna(distances.iloc[0])
    assert _round_pct(66.66) == 66.7
    assert _round_distance(12.3456) == 12.35
    assert _safe_mean(pd.DataFrame([{"x": "10"}, {"x": "bad"}]), "x") == 10.0
    assert _safe_mean(pd.DataFrame(), "x") == 0.0


def test_get_outcome_series_prefers_inferred_outcome_when_needed():
    df = pd.DataFrame([{"event_type": "Pass", "inferred_outcome": " Successful "}])

    outcomes = _get_outcome_series(df)

    assert outcomes.tolist() == ["successful"]


def test_calculate_pressure_duel_dribble_and_recovery_metrics_cover_zero_branches():
    df = pd.DataFrame(
        [
            {"event_type": "Pressure", "x": 30, "y": 20},
            {"event_type": "Pressure", "x": 85, "y": 40},
            {"event_type": "Duel", "outcome": "Won"},
            {"event_type": "Duel", "outcome": "Lost"},
            {"event_type": "Dribble", "outcome": "Complete", "x": 90},
            {"event_type": "Dribble", "outcome": "Incomplete", "x": 50},
            {"event_type": "Ball Recovery", "x": 35},
            {"event_type": "Ball Recovery", "x": 70},
            {"event_type": "Ball Recovery", "x": 90},
        ]
    )

    pressure_metrics = calculate_pressure_metrics(df)
    duel_metrics = calculate_duel_metrics(df)
    dribble_metrics = calculate_dribble_metrics(df)
    recovery_metrics = calculate_recovery_metrics(df)

    assert pressure_metrics["total_pressures"] == 2
    assert pressure_metrics["pressures_in_opponent_half"] == 1
    assert pressure_metrics["pressures_in_final_third"] == 1
    assert duel_metrics["duels_won"] == 1
    assert duel_metrics["duels_lost"] == 1
    assert duel_metrics["win_rate"] == 50.0
    assert dribble_metrics["successful_dribbles"] == 1
    assert dribble_metrics["unsuccessful_dribbles"] == 1
    assert dribble_metrics["dribbles_in_final_third"] == 1
    assert recovery_metrics["recoveries_in_own_half"] == 1
    assert recovery_metrics["recoveries_in_opponent_half"] == 2
    assert recovery_metrics["recoveries_in_final_third"] == 1


def test_specific_event_metrics_fallbacks_for_missing_coordinates_and_unknown_events():
    df = pd.DataFrame(
        [
            {"event_type": "Pass", "outcome": "Complete"},
            {"event_type": "Carry"},
            {"event_type": "Shot", "outcome": "Blocked"},
            {"event_type": "Offside"},
        ]
    )

    pass_metrics = calculate_pass_metrics(df)
    carry_metrics = calculate_carry_metrics(df)
    shot_metrics = calculate_shot_metrics(df)
    generic_metrics = calculate_specific_event_metrics(df, "Offside")

    assert pass_metrics["progressive_passes"] == 0
    assert pass_metrics["box_entries"] == 0
    assert carry_metrics["carries_with_end_location"] == 0
    assert carry_metrics["progressive_carries"] == 0
    assert shot_metrics["blocked"] == 1
    assert shot_metrics["average_distance_to_goal"] == 0.0
    assert generic_metrics["show_success_rate"] is False
    assert generic_metrics["success_rate"] == 0.0


def test_get_event_analysis_description_returns_default_for_unknown_event():
    assert "resume la actividad" in get_event_analysis_description("Unknown Event").lower()
