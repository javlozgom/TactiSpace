import pandas as pd

from src.delaunay import compute_delaunay_edges, recommend_pass_by_delaunay


def _build_event_row() -> pd.Series:
    return pd.Series({"player": "Passer", "x": 30, "y": 40, "end_x": 55, "end_y": 45, "event_type": "Pass"})


def _build_freeze_frame_df(with_actor: bool = True) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"event_id": "evt-1", "player": "Passer", "player_id": 1, "team": "Blue", "teammate": True, "actor": with_actor, "x": 30, "y": 40, "visible": True},
            {"event_id": "evt-1", "player": "Receiver A", "player_id": 2, "team": "Blue", "teammate": True, "actor": False, "x": 45, "y": 38, "visible": True},
            {"event_id": "evt-1", "player": "Receiver B", "player_id": 3, "team": "Blue", "teammate": True, "actor": False, "x": 48, "y": 52, "visible": True},
            {"event_id": "evt-1", "player": "Opponent A", "player_id": 4, "team": "Red", "teammate": False, "actor": False, "x": 60, "y": 44, "visible": True},
        ]
    )


def test_compute_delaunay_edges_returns_edges_for_valid_points():
    result = compute_delaunay_edges(_build_freeze_frame_df())
    assert not result.empty
    assert {"a_index", "b_index", "a_x", "a_y", "b_x", "b_y", "length"}.issubset(result.columns)


def test_compute_delaunay_edges_returns_empty_with_less_than_three_points():
    freeze_frame_df = pd.DataFrame(
        [
            {"player": "A", "x": 10, "y": 20},
            {"player": "B", "x": 30, "y": 40},
        ]
    )
    result = compute_delaunay_edges(freeze_frame_df)
    assert result.empty


def test_recommend_pass_by_delaunay_returns_dict_with_location():
    freeze_frame_df = _build_freeze_frame_df()
    delaunay_edges_df = compute_delaunay_edges(freeze_frame_df)
    result = recommend_pass_by_delaunay(_build_event_row(), freeze_frame_df, delaunay_edges_df)
    assert isinstance(result, dict)
    assert "recommended_location" in result


def test_recommend_pass_by_delaunay_without_actor_returns_none_player():
    freeze_frame_df = _build_freeze_frame_df(with_actor=False)
    delaunay_edges_df = compute_delaunay_edges(freeze_frame_df)
    result = recommend_pass_by_delaunay(_build_event_row(), freeze_frame_df, delaunay_edges_df)
    assert result["recommended_player"] is None
    assert "actor" in result["reason"].lower()


def test_recommend_pass_by_delaunay_without_edges_does_not_break():
    freeze_frame_df = _build_freeze_frame_df()
    result = recommend_pass_by_delaunay(_build_event_row(), freeze_frame_df, pd.DataFrame())
    assert result["recommended_player"] is None
    assert "reason" in result
