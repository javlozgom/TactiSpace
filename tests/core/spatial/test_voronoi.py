import pandas as pd
import pytest

from src.voronoi import (
    build_voronoi_regions,
    calculate_space_metrics,
    compute_voronoi,
    get_pitch_polygon,
)


def _build_players_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"player": "A", "player_id": 1, "team": "Blue", "teammate": True, "x": 20, "y": 20},
            {"player": "B", "player_id": 2, "team": "Blue", "teammate": True, "x": 40, "y": 40},
            {"player": "C", "player_id": 3, "team": "Red", "teammate": False, "x": 70, "y": 30},
            {"player": "D", "player_id": 4, "team": "Red", "teammate": False, "x": 90, "y": 55},
        ]
    )


def test_get_pitch_polygon_returns_valid_polygon():
    polygon = get_pitch_polygon()
    assert polygon.is_valid
    assert round(polygon.area, 2) == 9600.0


def test_compute_voronoi_with_less_than_three_points_does_not_break():
    result = compute_voronoi(pd.DataFrame([{"x": 10, "y": 20}, {"x": 15, "y": 25}]))
    assert result["valid"] is False
    assert result["voronoi"] is None


def test_build_voronoi_regions_returns_areas_for_valid_points():
    regions_df = build_voronoi_regions(_build_players_df())
    assert not regions_df.empty
    assert "area" in regions_df.columns
    assert (regions_df["area"] > 0).any()


def test_build_voronoi_regions_covers_pitch_without_internal_gaps():
    regions_df = build_voronoi_regions(_build_players_df())

    _assert_regions_cover_pitch(regions_df)


def test_calculate_space_metrics_adds_expected_columns():
    players_df = _build_players_df()
    regions_df = build_voronoi_regions(players_df)
    metrics_df = calculate_space_metrics(players_df, regions_df)
    assert {"voronoi_area", "normalized_area", "nearest_opponent_distance"}.issubset(metrics_df.columns)


def test_build_voronoi_regions_clips_out_of_bounds_points():
    players_df = pd.DataFrame(
        [
            {"player": "A", "player_id": 1, "team": "Blue", "teammate": True, "x": 42.8, "y": 9.0},
            {"player": "B", "player_id": 2, "team": "Blue", "teammate": True, "x": 53.1, "y": -2.8},
            {"player": "C", "player_id": 3, "team": "Blue", "teammate": True, "x": 61.0, "y": 65.0},
            {"player": "D", "player_id": 4, "team": "Red", "teammate": False, "x": 46.1, "y": 6.0},
            {"player": "E", "player_id": 5, "team": "Red", "teammate": False, "x": 61.3, "y": 19.6},
            {"player": "F", "player_id": 6, "team": "Red", "teammate": False, "x": 27.3, "y": 28.8},
        ]
    )

    regions_df = build_voronoi_regions(players_df)

    assert not regions_df.empty
    assert regions_df["area"].gt(0).any()
    _assert_regions_cover_pitch(regions_df)


def test_build_voronoi_regions_handles_duplicate_points_without_gaps():
    players_df = pd.concat(
        [
            _build_players_df(),
            pd.DataFrame(
                [
                    {"player": "Duplicate A", "player_id": 10, "team": "Blue", "teammate": True, "x": 20, "y": 20},
                ]
            ),
        ],
        ignore_index=True,
    )

    regions_df = build_voronoi_regions(players_df)

    assert len(regions_df) == 4
    _assert_regions_cover_pitch(regions_df)


def _assert_regions_cover_pitch(regions_df: pd.DataFrame) -> None:
    shapely_ops = pytest.importorskip("shapely.ops")
    pitch_polygon = get_pitch_polygon()
    union_geometry = shapely_ops.unary_union(list(regions_df["polygon"]))

    assert pitch_polygon.difference(union_geometry).area < 1e-6
    assert abs(union_geometry.area - pitch_polygon.area) < 1e-6
