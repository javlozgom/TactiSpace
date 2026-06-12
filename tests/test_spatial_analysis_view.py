from __future__ import annotations

import pandas as pd

from src.ui.tables import build_delaunay_edge_distances_df
from src.ui.spatial_analysis_view import (
    _assign_spatial_reference_ids,
    _build_delaunay_neighbors_df,
    _build_event_diagnostics,
    _build_voronoi_team_summary_df,
    _enrich_freeze_frame_team_labels,
    _format_ratio,
    _merge_spatial_reference_ids,
)


def test_format_ratio_handles_non_zero_denominator():
    assert _format_ratio(3, 4) == "3 / 4 (75.0%)"


def test_format_ratio_handles_zero_denominator():
    assert _format_ratio(0, 0) == "0 / 0 (0.0%)"


def test_build_event_diagnostics_is_robust_and_counts_visible_players():
    event_row = pd.Series(
        {
            "match_id": 123,
            "minute": 10,
            "second": 25,
            "player": "Passer",
            "team": "Blue",
            "event_type": "Pass",
            "x": 30,
            "y": 40,
            "end_x": 55,
            "end_y": 45,
        }
    )
    freeze_frame_df = pd.DataFrame(
        [
            {"player": "Passer", "teammate": True, "actor": True, "visible": True, "x": 30, "y": 40},
            {"player": "Mate", "teammate": True, "actor": False, "visible": True, "x": 50, "y": 42},
            {"player": "Rival", "teammate": False, "actor": False, "visible": True, "x": 60, "y": 42},
            {"player": "Hidden", "teammate": False, "actor": False, "visible": False, "x": 80, "y": 42},
        ]
    )

    diagnostics = _build_event_diagnostics(event_row, freeze_frame_df)
    values = {row["Campo"]: row["Valor"] for row in diagnostics}

    assert values["freeze-frame disponible"] == "Sí"
    assert values["jugadores visibles"] == 3
    assert values["compañeros visibles"] == 2
    assert values["rivales visibles"] == 1
    assert values["actor detectado"] == "Sí"


def test_assign_spatial_reference_ids_resets_per_case_and_skips_non_visible_rows():
    first_case_df = pd.DataFrame(
        [
            {"player": "Actor", "teammate": True, "actor": True, "visible": True},
            {"player": "Mate", "teammate": True, "actor": False, "visible": True},
            {"player": "Rival", "teammate": False, "actor": False, "visible": True},
            {"player": "Hidden", "teammate": False, "actor": False, "visible": False},
        ]
    )
    second_case_df = pd.DataFrame(
        [
            {"player": "Mate 2", "teammate": True, "actor": False, "visible": True},
            {"player": "Rival 2", "teammate": False, "actor": False, "visible": True},
        ]
    )

    first_result = _assign_spatial_reference_ids(first_case_df)
    second_result = _assign_spatial_reference_ids(second_case_df)

    assert first_result["spatial_reference_id"].iloc[:3].tolist() == ["T1", "T2", "R1"]
    assert pd.isna(first_result["spatial_reference_id"].iloc[3])
    assert second_result["spatial_reference_id"].tolist() == ["T1", "R1"]


def test_merge_spatial_reference_ids_preserves_option_rows_and_assigns_teammate_ids():
    freeze_frame_df = pd.DataFrame(
        [
            {"player": "Passer", "player_id": 10, "teammate": True, "visible": True, "x": 30.0, "y": 40.0, "spatial_reference_id": "T1"},
            {"player": "Mate A", "player_id": 11, "teammate": True, "visible": True, "x": 50.0, "y": 42.0, "spatial_reference_id": "T2"},
            {"player": "Mate B", "player_id": 12, "teammate": True, "visible": True, "x": 55.0, "y": 45.0, "spatial_reference_id": "T3"},
        ]
    )
    options_df = pd.DataFrame(
        [
            {"player": "Mate A", "player_id": 11, "x": 50.0, "y": 42.0, "pass_score": 1.2},
            {"player": "Mate B", "player_id": 12, "x": 55.0, "y": 45.0, "pass_score": 0.8},
        ]
    )

    result_df = _merge_spatial_reference_ids(options_df, freeze_frame_df)

    assert len(result_df) == 2
    assert result_df["spatial_reference_id"].tolist() == ["T2", "T3"]


def test_build_voronoi_team_summary_df_aggregates_area_and_visible_counts():
    freeze_frame_df = pd.DataFrame(
        [
            {"player": "Actor", "team": "Spain", "teammate": True, "visible": True},
            {"player": "Mate", "team": "Spain", "teammate": True, "visible": True},
            {"player": "Rival A", "team": "Croatia", "teammate": False, "visible": True},
            {"player": "Rival B", "team": "Croatia", "teammate": False, "visible": True},
            {"player": "Hidden", "team": "Croatia", "teammate": False, "visible": False},
        ]
    )
    voronoi_regions_df = pd.DataFrame(
        [
            {"player": "Actor", "team": "Spain", "area": 60.0},
            {"player": "Mate", "team": "Spain", "area": 40.0},
            {"player": "Rival A", "team": "Croatia", "area": 30.0},
            {"player": "Rival B", "team": "Croatia", "area": 20.0},
        ]
    )

    summary_df = _build_voronoi_team_summary_df(voronoi_regions_df, freeze_frame_df)

    assert summary_df["Equipo"].tolist() == ["Spain", "Croatia"]
    assert summary_df["Área Voronoi"].tolist() == [100.0, 50.0]
    assert summary_df["Jugadores visibles"].tolist() == [2, 2]
    assert summary_df["% ocupación del campo"].tolist() == [66.667, 33.333]


def test_build_delaunay_neighbors_df_uses_local_ids_and_same_team_neighbors_only():
    freeze_frame_df = pd.DataFrame(
        [
            {"player": "Actor", "team": "Spain", "teammate": True, "visible": True, "x": 10.0, "y": 10.0, "spatial_reference_id": "T1"},
            {"player": "Mate A", "team": "Spain", "teammate": True, "visible": True, "x": 20.0, "y": 10.0, "spatial_reference_id": "T2"},
            {"player": "Mate B", "team": "Spain", "teammate": True, "visible": True, "x": 30.0, "y": 10.0, "spatial_reference_id": "T3"},
            {"player": "Rival A", "team": "Croatia", "teammate": False, "visible": True, "x": 40.0, "y": 10.0, "spatial_reference_id": "R1"},
        ]
    )
    delaunay_edges_df = pd.DataFrame(
        [
            {"a_x": 10.0, "a_y": 10.0, "b_x": 20.0, "b_y": 10.0},
            {"a_x": 20.0, "a_y": 10.0, "b_x": 30.0, "b_y": 10.0},
            {"a_x": 30.0, "a_y": 10.0, "b_x": 40.0, "b_y": 10.0},
        ]
    )

    neighbors_df = _build_delaunay_neighbors_df(freeze_frame_df, delaunay_edges_df)

    assert neighbors_df["Jugador visible"].tolist() == ["T1", "T2", "T3", "R1"]
    assert neighbors_df["Vecinos del mismo equipo"].tolist() == ["T2", "T1, T3", "T2", "—"]
    assert neighbors_df["Nº vecinos"].tolist() == [1, 2, 1, 0]


def test_enrich_freeze_frame_team_labels_assigns_event_team_and_opponent_team():
    event_row = pd.Series({"match_id": 1, "team": "Spain", "possession_team": "Spain"})
    freeze_frame_df = pd.DataFrame(
        [
            {"player": "Actor", "teammate": True, "team": None},
            {"player": "Mate", "teammate": True, "team": ""},
            {"player": "Rival A", "teammate": False, "team": None},
            {"player": "Rival B", "teammate": False, "team": "Spain"},
        ]
    )

    from src.ui.views import spatial as spatial_view

    original_get_match_labels = spatial_view._get_match_labels
    spatial_view._get_match_labels = lambda: {"1": "Spain vs Croatia | 15/06/2024 | Group Stage"}
    try:
        result_df = _enrich_freeze_frame_team_labels(event_row, freeze_frame_df)
    finally:
        spatial_view._get_match_labels = original_get_match_labels

    assert result_df["team"].tolist() == ["Spain", "Spain", "Croatia", "Croatia"]


def test_build_delaunay_edge_distances_df_uses_local_ids_and_edge_lengths():
    freeze_frame_df = pd.DataFrame(
        [
            {"player": "Actor", "team": "Spain", "teammate": True, "visible": True, "x": 10.0, "y": 10.0, "spatial_reference_id": "T1"},
            {"player": "Mate A", "team": "Spain", "teammate": True, "visible": True, "x": 20.0, "y": 10.0, "spatial_reference_id": "T2"},
            {"player": "Rival A", "team": "Croatia", "teammate": False, "visible": True, "x": 20.0, "y": 20.0, "spatial_reference_id": "R1"},
        ]
    )
    delaunay_edges_df = pd.DataFrame(
        [
            {"a_x": 10.0, "a_y": 10.0, "b_x": 20.0, "b_y": 10.0, "length": 10.0},
            {"a_x": 20.0, "a_y": 10.0, "b_x": 20.0, "b_y": 20.0, "length": 10.0},
        ]
    )

    edge_distances_df = build_delaunay_edge_distances_df(freeze_frame_df, delaunay_edges_df)

    assert edge_distances_df["Punto A"].tolist() == ["T1", "T2"]
    assert edge_distances_df["Punto B"].tolist() == ["T2", "R1"]
    assert edge_distances_df["Relación"].tolist() == ["Mismo equipo", "Equipos distintos"]
    assert edge_distances_df["Distancia"].tolist() == [10.0, 10.0]
