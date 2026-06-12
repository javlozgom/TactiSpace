import pandas as pd

from src.ui.events_view import NON_PLOTTED_EVENT_TYPES, get_plottable_event_types, prepare_events_map_df


def test_prepare_events_map_df_excludes_non_plotted_event_types():
    df = pd.DataFrame(
        [
            {"event_type": "Pass", "x": 10, "y": 10},
            {"event_type": "Half Start", "x": 60, "y": 40},
            {"event_type": "Substitution", "x": 60, "y": 40},
            {"event_type": "Offside", "x": 90, "y": 35},
        ]
    )

    plot_df, draw_movements, _ = prepare_events_map_df(df)

    assert draw_movements is True
    assert set(plot_df["event_type"]) == {"Pass", "Offside"}


def test_get_plottable_event_types_filters_administrative_events():
    event_types = ["Pass", "Half End", "Own Goal Against", "Player Off", "Offside"]

    plotted = get_plottable_event_types(event_types)

    assert plotted == ["Pass", "Own Goal Against", "Offside"]
    assert "Half End" in NON_PLOTTED_EVENT_TYPES
