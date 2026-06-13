import pandas as pd

from src.percentiles import (
    PERCENTILE_METRIC_METADATA,
    add_interpreted_percentiles,
    add_percentiles,
    build_percentile_scatter_data,
    build_player_metric_dataset,
    flatten_metric_options,
    flatten_percentile_presets,
    get_metric_metadata,
    get_percentile_interpretation_text,
    get_percentile_metric_options,
    get_percentile_presets,
    get_top_highlighted_players,
    is_efficiency_metric,
    is_risk_metric,
)
from src.core.percentiles.calculations import (
    _build_percentile_mode_label,
    _find_metric_event_source,
    _interpret_percentile_series,
    _is_unknown_player,
    _is_unknown_position,
    _looks_like_preset_definition,
    _safe_metric_value,
)


def _build_percentile_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "match_id": 1,
                "team": "Blue",
                "player": "A",
                "position": "Forward",
                "event_type": "Shot",
                "outcome": "Goal",
                "x": 104,
                "y": 40,
            },
            {
                "match_id": 1,
                "team": "Blue",
                "player": "A",
                "position": "Forward",
                "event_type": "Pass",
                "outcome": "Successful",
                "x": 20,
                "y": 20,
                "end_x": 50,
                "end_y": 20,
            },
            {
                "match_id": 1,
                "team": "Blue",
                "player": "B",
                "position": "Midfielder",
                "event_type": "Shot",
                "outcome": "Saved",
                "x": 105,
                "y": 39,
            },
            {
                "match_id": 1,
                "team": "Blue",
                "player": "B",
                "position": "Midfielder",
                "event_type": "Shot",
                "outcome": "Goal",
                "x": 102,
                "y": 37,
            },
            {
                "match_id": 1,
                "team": "Blue",
                "player": "B",
                "position": "Midfielder",
                "event_type": "Shot",
                "outcome": "Off Target",
                "x": 99,
                "y": 44,
            },
            {
                "match_id": 1,
                "team": "Blue",
                "player": "B",
                "position": "Midfielder",
                "event_type": "Shot",
                "outcome": "Blocked",
                "x": 98,
                "y": 41,
            },
            {
                "match_id": 1,
                "team": "Blue",
                "player": "B",
                "position": "Midfielder",
                "event_type": "Shot",
                "outcome": "Saved",
                "x": 100,
                "y": 42,
            },
            {
                "match_id": 1,
                "team": "Red",
                "player": "C",
                "position": "Defender",
                "event_type": "Pass",
                "outcome": "Unsuccessful",
                "x": 25,
                "y": 30,
                "end_x": 30,
                "end_y": 32,
            },
            {
                "match_id": 1,
                "team": "Red",
                "player": "C",
                "position": "Defender",
                "event_type": "Dispossessed",
                "outcome": "",
                "x": 30,
                "y": 30,
            },
        ]
    )


def test_metric_metadata_contains_key_metrics():
    assert "total_shots" in PERCENTILE_METRIC_METADATA
    assert "conversion_rate" in PERCENTILE_METRIC_METADATA
    assert "failed_passes" in PERCENTILE_METRIC_METADATA


def test_get_percentile_metric_options_returns_non_empty_dict():
    options = get_percentile_metric_options()
    assert isinstance(options, dict)
    assert options
    assert "Pase" in options


def test_flatten_metric_options_returns_flat_dict():
    flat = flatten_metric_options(get_percentile_metric_options())
    assert isinstance(flat, dict)
    assert "total_passes" in flat
    assert "goals" in flat


def test_get_metric_metadata_returns_label_and_direction():
    metadata = get_metric_metadata("conversion_rate")
    assert metadata["label"] == "% conversión"
    assert metadata["direction"] == "efficiency"


def test_risk_and_efficiency_helpers():
    assert is_risk_metric("failed_passes") is True
    assert is_efficiency_metric("conversion_rate") is True


def test_build_player_metric_dataset_creates_one_row_per_player():
    dataset = build_player_metric_dataset(
        _build_percentile_df(),
        metrics=["total_passes", "goals", "total_losses"],
    )
    assert len(dataset) == 3
    assert "player" in dataset.columns
    assert "total_events" in dataset.columns
    assert dataset["player"].nunique() == 3


def test_build_player_metric_dataset_computes_box_entries_from_passes_and_carries():
    df = pd.DataFrame(
        [
            {
                "match_id": 1,
                "team": "Blue",
                "player": "A",
                "position": "Forward",
                "event_type": "Pass",
                "x": 70,
                "y": 30,
                "end_x": 104,
                "end_y": 40,
                "outcome": "Successful",
            },
            {
                "match_id": 1,
                "team": "Blue",
                "player": "A",
                "position": "Forward",
                "event_type": "Carry",
                "x": 80,
                "y": 32,
                "end_x": 103,
                "end_y": 39,
            },
        ]
    )

    dataset = build_player_metric_dataset(df, metrics=["box_entries"])
    assert dataset.loc[0, "box_entries"] == 2


def test_add_interpreted_percentiles_keeps_higher_is_better_direction():
    dataset = pd.DataFrame(
        {
            "player": ["A", "B"],
            "goals": [1, 3],
            "total_shots": [2, 4],
        }
    )
    result = add_interpreted_percentiles(dataset, "goals", "total_shots")
    player_b = result[result["player"] == "B"].iloc[0]
    player_a = result[result["player"] == "A"].iloc[0]
    assert player_b["x_interpreted_percentile"] > player_a["x_interpreted_percentile"]


def test_add_interpreted_percentiles_inverts_lower_is_better_metrics():
    dataset = pd.DataFrame(
        {
            "player": ["A", "B"],
            "average_distance_to_goal": [8.0, 20.0],
            "goals": [1, 2],
        }
    )
    result = add_interpreted_percentiles(dataset, "average_distance_to_goal", "goals")
    player_a = result[result["player"] == "A"].iloc[0]
    player_b = result[result["player"] == "B"].iloc[0]
    assert player_a["x_interpreted_percentile"] > player_b["x_interpreted_percentile"]


def test_add_interpreted_percentiles_does_not_invert_risk_metrics():
    dataset = pd.DataFrame(
        {
            "player": ["A", "B"],
            "failed_passes": [1, 4],
            "goals": [0, 0],
        }
    )
    result = add_interpreted_percentiles(dataset, "failed_passes", "goals")
    player_b = result[result["player"] == "B"].iloc[0]
    player_a = result[result["player"] == "A"].iloc[0]
    assert player_b["x_interpreted_percentile"] > player_a["x_interpreted_percentile"]


def test_add_percentiles_adds_backward_compatible_columns():
    dataset = build_player_metric_dataset(_build_percentile_df(), metrics=["total_passes", "goals"])
    result = add_percentiles(dataset, "total_passes", "goals")
    assert {
        "x_percentile",
        "y_percentile",
        "combined_percentile_score",
        "x_raw_percentile",
        "y_raw_percentile",
    }.issubset(result.columns)


def test_get_top_highlighted_players_returns_top_n():
    dataset = build_player_metric_dataset(_build_percentile_df(), metrics=["total_passes", "goals"])
    result = add_percentiles(dataset, "total_passes", "goals")
    top_df = get_top_highlighted_players(result, top_n=2)
    assert len(top_df) == 2


def test_percentile_interpretation_texts_cover_risk_efficiency_and_production():
    assert "riesgo" in get_percentile_interpretation_text("failed_passes", "goals").lower()
    assert "eficiencia" in get_percentile_interpretation_text("total_shots", "conversion_rate").lower()
    assert "producción ofensiva" in get_percentile_interpretation_text("total_shots", "goals").lower()


def test_get_percentile_presets_returns_non_empty_dict():
    presets = get_percentile_presets()
    assert isinstance(presets, dict)
    assert presets
    assert "Finalización" in presets


def test_build_percentile_scatter_data_respects_specific_minimum():
    full_df, highlighted_df = build_percentile_scatter_data(
        _build_percentile_df(),
        x_metric="total_shots",
        y_metric="conversion_rate",
        min_events=1,
        top_n=5,
        min_metric="total_shots",
        min_metric_value=5,
    )
    assert not full_df.empty
    assert full_df["player"].tolist() == ["B"]
    assert len(highlighted_df) == 1


def test_percentile_functions_handle_empty_dataframe():
    empty_df = pd.DataFrame()
    dataset = build_player_metric_dataset(empty_df, metrics=["total_passes"])
    assert dataset.empty
    percentiles_df = add_percentiles(dataset, "total_passes", "goals")
    assert {"x_percentile", "y_percentile", "combined_percentile_score"}.issubset(percentiles_df.columns)
    full_df, highlighted_df = build_percentile_scatter_data(
        empty_df,
        x_metric="total_passes",
        y_metric="goals",
    )
    assert full_df.empty
    assert highlighted_df.empty


def test_flatten_percentile_presets_returns_at_least_twenty_eight_presets():
    flattened = flatten_percentile_presets(get_percentile_presets())
    assert len(flattened) >= 28


def test_expected_percentile_preset_names_exist():
    flattened = flatten_percentile_presets(get_percentile_presets())
    expected_names = {
        "Producción goleadora",
        "Eficiencia finalizadora",
        "Precisión de tiro",
        "Atacantes desequilibrantes",
        "Extremos desequilibrantes",
        "Creadores progresivos",
        "Mediocentros seguros y progresivos",
        "Generadores de peligro",
        "Distribuidores principales",
        "Centrales constructores",
        "Jugadores más participativos",
        "Conductores progresivos",
        "Progresión mixta",
        "Laterales profundos",
        "Box-to-box",
        "Amenaza al área",
        "Progresión hacia zona peligrosa",
        "Defensas activos",
        "Anticipación defensiva",
        "Dominio en duelos",
        "Mediocentros completos",
        "Laterales equilibrados",
        "Presión alta",
        "Presionantes intensos",
        "Recuperadores adelantados",
        "Alertas de pérdida",
        "Riesgo en pase",
        "Riesgo técnico",
    }
    assert expected_names.issubset(flattened.keys())


def test_each_expected_preset_has_required_fields():
    flattened = flatten_percentile_presets(get_percentile_presets())
    for preset_definition in flattened.values():
        assert "description" in preset_definition
        assert "x_metric" in preset_definition
        assert "y_metric" in preset_definition
        assert "position" in preset_definition
        assert "min_events" in preset_definition


def test_risk_presets_are_flagged():
    flattened = flatten_percentile_presets(get_percentile_presets())
    assert flattened["Alertas de pérdida"]["risk_preset"] is True
    assert flattened["Riesgo en pase"]["risk_preset"] is True
    assert flattened["Riesgo técnico"]["risk_preset"] is True


def test_presets_with_specific_minimum_define_threshold_fields():
    flattened = flatten_percentile_presets(get_percentile_presets())
    for preset_name in [
        "Eficiencia finalizadora",
        "Precisión de tiro",
        "Dominio en duelos",
    ]:
        assert "min_metric" in flattened[preset_name]
        assert "min_metric_value" in flattened[preset_name]


def test_all_preset_metrics_exist_in_metadata():
    flattened = flatten_percentile_presets(get_percentile_presets())
    preset_metrics = {
        preset_definition["x_metric"] for preset_definition in flattened.values()
    } | {
        preset_definition["y_metric"] for preset_definition in flattened.values()
    }
    assert preset_metrics.issubset(PERCENTILE_METRIC_METADATA.keys())


def test_presets_do_not_repeat_same_metric_pair_and_position():
    flattened = flatten_percentile_presets(get_percentile_presets())
    signatures = [
        (
            preset_definition["x_metric"],
            preset_definition["y_metric"],
            preset_definition["position"],
        )
        for preset_definition in flattened.values()
    ]
    assert len(signatures) == len(set(signatures))


def test_metric_metadata_and_interpretation_fallbacks_cover_unknown_cases():
    metadata = get_metric_metadata("unknown_metric")

    assert metadata["family"] == "Otras"
    assert "rendimiento relativo" in get_percentile_interpretation_text("unknown_metric", "other_metric").lower()
    assert "volumen" in get_percentile_interpretation_text("total_passes", "goals").lower()


def test_flatten_percentile_presets_accepts_mixed_structures():
    presets = {
        "directo": {
            "description": "x",
            "x_metric": "goals",
            "y_metric": "total_shots",
            "position": "Atacante",
            "min_events": 5,
        },
        "grupo": {
            "preset": {
                "description": "y",
                "x_metric": "goals",
                "y_metric": "total_shots",
                "position": "Atacante",
                "min_events": 5,
            }
        },
        "ruido": "ignorar",
    }

    flattened = flatten_percentile_presets(presets)

    assert set(flattened) == {"directo", "preset"}


def test_build_player_metric_dataset_filters_unknowns_and_position_thresholds():
    df = pd.DataFrame(
        [
            {"player": "Unknown", "team": "Blue", "position": "Forward", "event_type": "Shot", "outcome": "Goal", "x": 100, "y": 40},
            {"player": "A", "team": "Blue", "position": "Goalkeeper", "event_type": "Shot", "outcome": "Goal", "x": 100, "y": 40},
            {"player": "B", "team": "Blue", "position": "Forward", "event_type": "Shot", "outcome": "Goal", "x": 100, "y": 40},
        ]
    )

    dataset = build_player_metric_dataset(
        df,
        metrics=["goals"],
        position_filter="Atacante",
        min_events=1,
        min_metric="goals",
        min_metric_value=1,
    )

    assert dataset["player"].tolist() == ["B"]


def test_add_interpreted_percentiles_handles_empty_input_and_mode_labels():
    empty_result = add_interpreted_percentiles(pd.DataFrame(), "goals", "failed_passes")

    assert empty_result.empty
    assert _build_percentile_mode_label("higher_is_risk", "efficiency") == "Riesgo"
    assert _build_percentile_mode_label("efficiency", "higher_is_better") == "Eficiencia"
    assert _build_percentile_mode_label("volume", "higher_is_better") == "Volumen"
    assert _build_percentile_mode_label("higher_is_better", "higher_is_better") == "Rendimiento relativo"


def test_percentile_internal_helpers_cover_remaining_branches():
    assert _is_unknown_player(" unknown ") is True
    assert _is_unknown_player("Rodri") is False
    assert _is_unknown_position(" Unknown ") is True
    assert _is_unknown_position("Defensa") is False
    assert _find_metric_event_source("successful_dribbles") == "Dribble"
    assert _find_metric_event_source("metrica_inexistente") is None
    assert _safe_metric_value(True) == 1
    assert _safe_metric_value("4.0") == 4
    assert _safe_metric_value("4.5") == 4.5
    assert _safe_metric_value("x") == 0
    assert _interpret_percentile_series(pd.Series([20.0, 80.0]), "lower_is_better").tolist() == [80.0, 20.0]
    assert _looks_like_preset_definition(
        {"description": "x", "x_metric": "a", "y_metric": "b", "position": "Todas", "min_events": 1}
    ) is True
