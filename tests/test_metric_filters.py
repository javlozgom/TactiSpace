import pandas as pd

from src.metric_filters import (
    apply_specific_metric_focus_filters,
    get_focus_filter_options,
)


def test_get_focus_filter_options_pass_has_result_and_progression():
    options = get_focus_filter_options("Pass")

    assert "Resultado" in options
    assert "Progresión" in options
    assert options["Progresión"] == ["Todos", "Progresivos", "Al área"]
    assert options["Zona de origen"] == ["Todas", "1er tercio", "2o tercio", "3er tercio"]
    assert options["Zona de destino"] == ["Todas", "1er tercio", "2o tercio", "3er tercio"]
    assert "Continuación" in options


def test_apply_specific_metric_focus_filters_filters_completed_passes():
    df = pd.DataFrame(
        [
            {"event_type": "Pass", "outcome": "Successful", "x": 30, "end_x": 45, "end_y": 40},
            {"event_type": "Pass", "outcome": "Unsuccessful", "x": 30, "end_x": 45, "end_y": 40},
        ]
    )

    result = apply_specific_metric_focus_filters(
        df,
        "Pass",
        {"Resultado": "Completados"},
    )

    assert len(result) == 1
    assert result.iloc[0]["outcome"] == "Successful"


def test_apply_specific_metric_focus_filters_filters_progressive_passes():
    df = pd.DataFrame(
        [
            {"event_type": "Pass", "x": 20, "end_x": 35},
            {"event_type": "Pass", "x": 20, "end_x": 25},
        ]
    )

    result = apply_specific_metric_focus_filters(
        df,
        "Pass",
        {"Progresión": "Progresivos"},
    )

    assert len(result) == 1
    assert result.iloc[0]["end_x"] == 35


def test_apply_specific_metric_focus_filters_filters_actions_to_final_third():
    df = pd.DataFrame(
        [
            {"event_type": "Pass", "x": 40, "end_x": 82},
            {"event_type": "Pass", "x": 40, "end_x": 70},
        ]
    )

    result = apply_specific_metric_focus_filters(
        df,
        "Pass",
        {"Zona de destino": "3er tercio"},
    )

    assert len(result) == 1
    assert result.iloc[0]["end_x"] == 82


def test_apply_specific_metric_focus_filters_filters_actions_to_box():
    df = pd.DataFrame(
        [
            {"event_type": "Carry", "x": 70, "end_x": 103, "end_y": 40},
            {"event_type": "Carry", "x": 70, "end_x": 90, "end_y": 50},
        ]
    )

    result = apply_specific_metric_focus_filters(
        df,
        "Carry",
        {"Progresión": "Al área"},
    )

    assert len(result) == 1
    assert result.iloc[0]["end_x"] == 103


def test_apply_specific_metric_focus_filters_filters_field_thirds():
    df = pd.DataFrame(
        [
            {"event_type": "Pressure", "x": 20},
            {"event_type": "Pressure", "x": 55},
            {"event_type": "Pressure", "x": 85},
        ]
    )

    first_third = apply_specific_metric_focus_filters(df, "Pressure", {"Zona": "1er tercio"})
    second_third = apply_specific_metric_focus_filters(df, "Pressure", {"Zona": "2o tercio"})
    third_third = apply_specific_metric_focus_filters(df, "Pressure", {"Zona": "3er tercio"})

    assert len(first_third) == 1
    assert first_third.iloc[0]["x"] == 20
    assert len(second_third) == 1
    assert second_third.iloc[0]["x"] == 55
    assert len(third_third) == 1
    assert third_third.iloc[0]["x"] == 85


def test_apply_specific_metric_focus_filters_filters_destination_thirds():
    df = pd.DataFrame(
        [
            {"event_type": "Pass", "x": 20, "end_x": 30},
            {"event_type": "Pass", "x": 20, "end_x": 55},
            {"event_type": "Pass", "x": 20, "end_x": 90},
        ]
    )

    first_third = apply_specific_metric_focus_filters(df, "Pass", {"Zona de destino": "1er tercio"})
    second_third = apply_specific_metric_focus_filters(df, "Pass", {"Zona de destino": "2o tercio"})
    third_third = apply_specific_metric_focus_filters(df, "Pass", {"Zona de destino": "3er tercio"})

    assert len(first_third) == 1
    assert first_third.iloc[0]["end_x"] == 30
    assert len(second_third) == 1
    assert second_third.iloc[0]["end_x"] == 55
    assert len(third_third) == 1
    assert third_third.iloc[0]["end_x"] == 90


def test_apply_specific_metric_focus_filters_filters_carry_by_continuation():
    df = pd.DataFrame(
        [
            {"match_id": 1, "possession_id": 1, "timestamp": 1, "team": "Spain", "event_type": "Carry"},
            {"match_id": 1, "possession_id": 1, "timestamp": 2, "team": "Spain", "event_type": "Shot"},
            {"match_id": 1, "possession_id": 2, "timestamp": 1, "team": "Spain", "event_type": "Carry"},
            {"match_id": 1, "possession_id": 2, "timestamp": 2, "team": "Spain", "event_type": "Pass"},
        ]
    )

    result = apply_specific_metric_focus_filters(
        df,
        "Carry",
        {"Continuación": "Acaban en tiro"},
    )

    assert len(result) == 1
    assert result.iloc[0]["possession_id"] == 1


def test_apply_specific_metric_focus_filters_filters_pass_by_continuation():
    df = pd.DataFrame(
        [
            {"match_id": 1, "possession_id": 1, "timestamp": 1, "team": "Spain", "event_type": "Pass"},
            {"match_id": 1, "possession_id": 1, "timestamp": 2, "team": "Spain", "event_type": "Ball Receipt*"},
            {"match_id": 1, "possession_id": 1, "timestamp": 3, "team": "Spain", "event_type": "Carry"},
            {"match_id": 1, "possession_id": 2, "timestamp": 1, "team": "Spain", "event_type": "Pass"},
            {"match_id": 1, "possession_id": 2, "timestamp": 2, "team": "Spain", "event_type": "Ball Receipt*"},
            {"match_id": 1, "possession_id": 2, "timestamp": 3, "team": "Spain", "event_type": "Dribble"},
        ]
    )

    result = apply_specific_metric_focus_filters(
        df,
        "Pass",
        {"Continuación": "Acaban en conducción"},
    )

    assert len(result) == 1
    assert result.iloc[0]["possession_id"] == 1


def test_apply_specific_metric_focus_filters_uses_broader_context_for_continuation():
    full_df = pd.DataFrame(
        [
            {"match_id": 1, "possession_id": 1, "timestamp": 1, "team": "Spain", "player": "A", "event_type": "Carry"},
            {"match_id": 1, "possession_id": 1, "timestamp": 2, "team": "Spain", "player": "B", "event_type": "Shot"},
            {"match_id": 1, "possession_id": 2, "timestamp": 1, "team": "Spain", "player": "A", "event_type": "Carry"},
            {"match_id": 1, "possession_id": 2, "timestamp": 2, "team": "Spain", "player": "B", "event_type": "Pass"},
        ]
    )
    player_df = full_df[full_df["player"] == "A"].copy()

    result = apply_specific_metric_focus_filters(
        player_df,
        "Carry",
        {"Continuación": "Acaban en tiro"},
        context_df=full_df,
    )

    assert len(result) == 1
    assert result.iloc[0]["possession_id"] == 1


def test_apply_specific_metric_focus_filters_handles_empty_dataframe():
    df = pd.DataFrame(columns=["event_type", "x", "end_x", "outcome"])

    result = apply_specific_metric_focus_filters(df, "Pass", {"Resultado": "Completados"})

    assert result.empty


def test_apply_specific_metric_focus_filters_handles_missing_columns():
    df = pd.DataFrame(
        [
            {"event_type": "Pass", "x": 30},
            {"event_type": "Pass", "x": 40},
        ]
    )

    result = apply_specific_metric_focus_filters(df, "Pass", {"Progresión": "Al área"})

    assert result.empty
