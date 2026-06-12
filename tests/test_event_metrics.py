import pandas as pd

from src.event_metrics import (
    calculate_carry_metrics,
    calculate_event_card_stats,
    calculate_pass_metrics,
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
