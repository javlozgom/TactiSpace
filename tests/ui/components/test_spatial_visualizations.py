import matplotlib.pyplot as plt
import pandas as pd
import pytest

shapely_geometry = pytest.importorskip("shapely.geometry")
GeometryCollection = shapely_geometry.GeometryCollection
LineString = shapely_geometry.LineString
MultiPolygon = shapely_geometry.MultiPolygon
Polygon = shapely_geometry.Polygon

from src.ui.components.spatial_visualizations import _fill_polygon
from src.spatial_visualizations import (
    plot_delaunay_freeze_frame,
    plot_freeze_frame,
    plot_pass_recommendation,
    plot_voronoi_freeze_frame,
)


def _build_event_row() -> pd.Series:
    return pd.Series({"player": "Passer", "x": 30, "y": 40, "end_x": 55, "end_y": 45, "event_type": "Pass"})


def _build_freeze_frame_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"event_id": "evt-1", "player": "Passer", "player_id": 1, "team": "Blue", "teammate": True, "actor": True, "x": 30, "y": 40, "visible": True, "spatial_reference_id": "T1"},
            {"event_id": "evt-1", "player": "Receiver A", "player_id": 2, "team": "Blue", "teammate": True, "actor": False, "x": 60, "y": 42, "visible": True, "spatial_reference_id": "T2"},
            {"event_id": "evt-1", "player": "Opponent A", "player_id": 3, "team": "Red", "teammate": False, "actor": False, "x": 62, "y": 42, "visible": True, "spatial_reference_id": "R1"},
            {"event_id": "evt-1", "player": "Opponent B", "player_id": 4, "team": "Red", "teammate": False, "actor": False, "x": 75, "y": 50, "visible": True, "spatial_reference_id": "R2"},
        ]
    )


def _build_regions_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"player": "Passer", "player_id": 1, "team": "Blue", "teammate": True, "polygon": Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])},
            {"player": "Opponent A", "player_id": 3, "team": "Red", "teammate": False, "polygon": Polygon([(10, 0), (20, 0), (20, 10), (10, 10)])},
        ]
    )


def _build_delaunay_edges_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"a_x": 30, "a_y": 40, "b_x": 60, "b_y": 42, "a_teammate": True, "b_teammate": True},
            {"a_x": 30, "a_y": 40, "b_x": 62, "b_y": 42, "a_teammate": True, "b_teammate": False},
        ]
    )


def test_fill_polygon_handles_common_geometry_types():
    fig, ax = plt.subplots()
    try:
        cases = [
            (None, 0),
            ([(0, 0), (1, 0), (1, 1), (0, 1)], 1),
            (Polygon([(0, 0), (1, 0), (1, 1), (0, 1)]), 1),
            (MultiPolygon([Polygon([(0, 0), (1, 0), (1, 1), (0, 1)]), Polygon([(2, 0), (3, 0), (3, 1), (2, 1)])]), 2),
            (GeometryCollection([Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])]), 1),
            (GeometryCollection([LineString([(0, 0), (1, 1)])]), 0),
            (LineString([(0, 0), (1, 1)]), 0),
        ]

        for geometry, expected_additions in cases:
            before = len(ax.patches)
            _fill_polygon(ax, geometry, "#2f855a")
            assert len(ax.patches) - before == expected_additions
    finally:
        plt.close(fig)


def test_plot_freeze_frame_returns_figure():
    fig = plot_freeze_frame(_build_event_row(), _build_freeze_frame_df())
    assert fig is not None
    plot_labels = {text.get_text() for text in fig.axes[0].texts}
    assert {"T1", "T2", "R1", "R2"}.issubset(plot_labels)


def test_plot_voronoi_freeze_frame_returns_figure():
    freeze_frame_df = _build_freeze_frame_df()
    regions_df = _build_regions_df()
    fig = plot_voronoi_freeze_frame(_build_event_row(), freeze_frame_df, regions_df)
    assert fig is not None


def test_plot_delaunay_freeze_frame_returns_figure():
    freeze_frame_df = _build_freeze_frame_df()
    edges_df = _build_delaunay_edges_df()
    fig = plot_delaunay_freeze_frame(_build_event_row(), freeze_frame_df, edges_df)
    assert fig is not None


def test_plot_pass_recommendation_returns_figure():
    freeze_frame_df = _build_freeze_frame_df()
    regions_df = _build_regions_df()
    recommendation = {
        "recommended_player": "Receiver A",
        "recommended_location": (60, 42),
        "score": 1.2,
        "reason": "Test",
    }
    fig = plot_pass_recommendation(_build_event_row(), freeze_frame_df, regions_df, recommendation)
    assert fig is not None
