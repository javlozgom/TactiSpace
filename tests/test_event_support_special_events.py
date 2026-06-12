import matplotlib.pyplot as plt
import pandas as pd

from src.event_metrics import (
    calculate_event_card_stats,
    calculate_generic_event_metrics,
    get_supported_specific_metric_events,
)
from src.preprocessing import normalize_events
from src.ui.comparative_view import _get_event_options
from src.ui.summary_view import _build_special_event_summary_items, _get_special_plot_event_types
from src.visualizations import EVENT_MARKERS, draw_offside_flag, plot_single_event_map


def test_normalize_events_keeps_special_events():
    df = pd.DataFrame(
        [
            {
                "match_id": 1,
                "team": "Spain",
                "player": None,
                "minute": 10,
                "second": 5,
                "event_type": "Own Goal For",
                "outcome": "Own Goal For",
                "x": None,
                "y": None,
                "end_x": None,
                "end_y": None,
                "possession_id": None,
            },
            {
                "match_id": 1,
                "team": "Italy",
                "player": "Calafiori",
                "minute": 10,
                "second": 5,
                "event_type": "Own Goal Against",
                "outcome": "Own Goal Against",
                "x": None,
                "y": None,
                "end_x": None,
                "end_y": None,
                "possession_id": None,
            },
            {
                "match_id": 1,
                "team": "Spain",
                "player": "Morata",
                "minute": 22,
                "second": 15,
                "event_type": "Offside",
                "outcome": "Offside",
                "x": 95,
                "y": 35,
                "end_x": 95,
                "end_y": 35,
                "possession_id": 3,
            },
        ]
    )

    result = normalize_events(df)

    assert set(result["event_type"]) == {"Own Goal For", "Own Goal Against", "Offside"}


def test_calculate_generic_event_metrics_supports_offside():
    df = pd.DataFrame(
        [
            {"event_type": "Offside", "outcome": "Offside", "x": 92, "y": 38},
            {"event_type": "Offside", "outcome": "Offside", "x": 98, "y": 42},
        ]
    )

    metrics = calculate_generic_event_metrics(df, "Offside")

    assert metrics["event_type"] == "Offside"
    assert metrics["total_events"] == 2
    assert metrics["show_success_rate"] is False
    assert metrics["average_x"] == 95.0


def test_event_card_stats_hide_success_rate_for_special_events():
    df = pd.DataFrame(
        [
            {"event_type": "Own Goal For", "outcome": "Own Goal For"},
            {"event_type": "Own Goal Against", "outcome": "Own Goal Against"},
            {"event_type": "Offside", "outcome": "Offside"},
        ]
    )

    for event_type in ["Own Goal For", "Own Goal Against", "Offside"]:
        stats = calculate_event_card_stats(df, event_type)
        assert stats["show_success_rate"] is False


def test_supported_specific_metric_events_include_special_events():
    supported_events = get_supported_specific_metric_events()

    assert "Own Goal For" in supported_events
    assert "Own Goal Against" in supported_events
    assert "Offside" in supported_events


def test_draw_offside_flag_handles_valid_coordinates():
    fig, ax = plt.subplots()
    try:
        draw_offside_flag(ax, 90, 40, size=1.5)
    finally:
        plt.close(fig)


def test_plot_single_event_map_supports_offside():
    df = pd.DataFrame(
        [
            {"event_type": "Offside", "outcome": "Offside", "x": 96, "y": 37},
            {"event_type": "Offside", "outcome": "Offside", "x": 101, "y": 43},
        ]
    )

    fig = plot_single_event_map(df, "Offside", show_legend=True)
    try:
        assert fig is not None
    finally:
        plt.close(fig)


def test_comparative_event_options_include_special_events():
    df = pd.DataFrame(
        [
            {"event_type": "Pass"},
            {"event_type": "Offside"},
            {"event_type": "Own Goal For"},
            {"event_type": "Own Goal Against"},
        ]
    )

    options = _get_event_options(df, df)

    assert "Offside" in options
    assert "Own Goal For" in options
    assert "Own Goal Against" in options


def test_summary_special_event_items_make_own_goals_visible():
    df = pd.DataFrame(
        [
            {"event_type": "Own Goal Against", "minute": 54, "second": 4},
            {"event_type": "Pass", "minute": 10, "second": 0},
        ]
    )

    items = _build_special_event_summary_items(df)

    assert items[0][0] == "Gol en propia en contra"
    assert items[0][1] == "1"
    assert "54:04" in items[0][2]


def test_summary_special_plot_event_types_only_include_own_goals():
    df = pd.DataFrame(
        [
            {"event_type": "Own Goal Against"},
            {"event_type": "Offside"},
            {"event_type": "Pass"},
        ]
    )

    event_types = _get_special_plot_event_types(df)

    assert event_types == ["Own Goal Against"]


def test_pass_marker_remains_a_point():
    assert EVENT_MARKERS["Pass"] == "o"


def test_event_markers_are_unique():
    assert len(set(EVENT_MARKERS.values())) == len(EVENT_MARKERS)
