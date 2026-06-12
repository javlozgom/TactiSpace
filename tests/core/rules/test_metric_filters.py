import pandas as pd

from src.core.rules.metric_filters import (
    _contains_keywords,
    _continuation_mask,
    _normalized_outcome_series,
    _normalize_label,
    _progression_mask,
    _result_mask,
    _zone_mask,
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


def test_get_focus_filter_options_for_other_supported_events():
    assert get_focus_filter_options("Shot")["Resultado"] == ["Todos", "Goles", "Parados", "Fuera", "Bloqueados"]
    assert get_focus_filter_options("Pressure")["Zona"] == ["Todas", "1er tercio", "2o tercio", "3er tercio"]
    assert "Progresión" in get_focus_filter_options("Carry")
    assert get_focus_filter_options("Duel")["Resultado"] == ["Todos", "Ganados", "Perdidos"]
    assert get_focus_filter_options("Dribble")["Zona"] == ["Todas", "1er tercio", "2o tercio", "3er tercio"]
    assert get_focus_filter_options("Ball Recovery")["Zona"] == ["Todas", "1er tercio", "2o tercio", "3er tercio"]
    assert get_focus_filter_options("Interception")["Zona"] == ["Todas", "1er tercio", "2o tercio", "3er tercio"]
    assert get_focus_filter_options("Unknown") == {}


def test_apply_specific_metric_focus_filters_supports_result_variants():
    df = pd.DataFrame(
        [
            {"event_type": "Shot", "outcome": "Goal"},
            {"event_type": "Shot", "outcome": "Saved"},
            {"event_type": "Shot", "outcome": "Off Target"},
            {"event_type": "Shot", "outcome": "Blocked"},
            {"event_type": "Duel", "outcome": "Won"},
            {"event_type": "Duel", "outcome": "Lost"},
            {"event_type": "Dribble", "outcome": "Successful"},
            {"event_type": "Dribble", "outcome": "Unsuccessful"},
        ]
    )

    assert len(apply_specific_metric_focus_filters(df, "Shot", {"Resultado": "Goles"})) == 1
    assert len(apply_specific_metric_focus_filters(df, "Shot", {"Resultado": "Parados"})) == 1
    assert len(apply_specific_metric_focus_filters(df, "Shot", {"Resultado": "Fuera"})) == 1
    assert len(apply_specific_metric_focus_filters(df, "Shot", {"Resultado": "Bloqueados"})) == 1
    assert len(apply_specific_metric_focus_filters(df, "Duel", {"Resultado": "Ganados"})) == 1
    assert len(apply_specific_metric_focus_filters(df, "Duel", {"Resultado": "Perdidos"})) == 1
    assert len(apply_specific_metric_focus_filters(df, "Dribble", {"Resultado": "Exitosos"})) == 1
    assert len(apply_specific_metric_focus_filters(df, "Dribble", {"Resultado": "Fallidos"})) == 1


def test_apply_specific_metric_focus_filters_supports_zone_aliases_and_passthrough():
    df = pd.DataFrame(
        [
            {"event_type": "Pressure", "x": 30, "end_x": 20},
            {"event_type": "Pressure", "x": 65, "end_x": 60},
            {"event_type": "Pressure", "x": 85, "end_x": 90},
        ]
    )

    own_half = apply_specific_metric_focus_filters(df, "Pressure", {"Zona": "Campo propio"})
    opponent_half = apply_specific_metric_focus_filters(df, "Pressure", {"Zona": "Campo rival"})
    final_third = apply_specific_metric_focus_filters(df, "Pressure", {"Zona": "Ultimo tercio"})
    passthrough = apply_specific_metric_focus_filters(df, "Pressure", {"Grupo desconocido": "Valor"})

    assert own_half["x"].tolist() == [30]
    assert opponent_half["x"].tolist() == [65, 85]
    assert final_third["x"].tolist() == [85]
    assert len(passthrough) == 3


def test_apply_specific_metric_focus_filters_handles_missing_required_columns_for_continuation():
    df = pd.DataFrame([{"event_type": "Carry", "team": "Spain"}])

    result = apply_specific_metric_focus_filters(df, "Carry", {"Continuación": "Acaban en tiro"})

    assert result.empty


def test_apply_specific_metric_focus_filters_returns_all_rows_for_unknown_continuation_option():
    df = pd.DataFrame(
        [
            {"match_id": 1, "possession_id": 1, "timestamp": 1, "team": "Spain", "event_type": "Carry"},
            {"match_id": 1, "possession_id": 1, "timestamp": 2, "team": "Spain", "event_type": "Shot"},
        ]
    )

    result = apply_specific_metric_focus_filters(df, "Carry", {"Continuación": "Algo no soportado"})

    assert len(result) == 1


def test_apply_specific_metric_focus_filters_handles_missing_event_type_and_todos_passthrough():
    no_event_type = pd.DataFrame([{"x": 30}])
    df = pd.DataFrame([{"event_type": "Pass", "x": 20}])

    result_missing = apply_specific_metric_focus_filters(no_event_type, "Pass", {"Resultado": "Completados"})
    result_todos = apply_specific_metric_focus_filters(df, "Pass", {"Resultado": "Todos"})
    result_no_matches = apply_specific_metric_focus_filters(df, "Shot", {"Resultado": "Goles"})

    assert result_missing.empty
    assert len(result_todos) == 1
    assert result_no_matches.empty


def test_metric_filter_private_helpers_cover_remaining_branches():
    df = pd.DataFrame(
        [
            {"outcome": "Successful"},
            {"inferred_outcome": "Lost"},
        ]
    )
    empty_outcomes = _normalized_outcome_series(pd.DataFrame())
    normalized = _normalize_label(" Conducción ")
    contains_empty = _contains_keywords(pd.Series(dtype="object"), ("goal",))
    result_default = _result_mask(pd.DataFrame([{"outcome": "Other"}]), "Shot", "Otra")
    progressive_missing = _progression_mask(pd.DataFrame([{"x": 1}]), "Progresivos")
    destination_final_third = _progression_mask(pd.DataFrame([{"end_x": 79}, {"end_x": 80}]), "Al ultimo tercio")
    progression_default = _progression_mask(pd.DataFrame([{"x": 1, "end_x": 2}]), "Otra")
    zone_missing = _zone_mask(pd.DataFrame([{"y": 1}]), "1er tercio", column="x")
    continuation_missing = _continuation_mask(
        pd.DataFrame([{"event_type": "Carry"}]),
        pd.DataFrame([{"event_type": "Carry"}]),
        "Carry",
        "Acaban en tiro",
    )

    assert _normalized_outcome_series(df).tolist() == ["", "lost"]
    assert empty_outcomes.tolist() == []
    assert normalized == "conduccion"
    assert contains_empty.tolist() == []
    assert result_default.tolist() == [True]
    assert progressive_missing.tolist() == [False]
    assert destination_final_third.tolist() == [False, True]
    assert progression_default.tolist() == [True]
    assert zone_missing.tolist() == [False]
    assert continuation_missing.tolist() == [False]
