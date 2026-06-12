from __future__ import annotations

import pandas as pd

from src.ui.views.spatial_formatters import normalize_coordinate_key, safe_display, spatial_reference_sort_key
from src.ui.views.spatial_utils import visible_freeze_frame_df


def build_delaunay_neighbors_df(
    freeze_frame_df: pd.DataFrame,
    delaunay_edges_df: pd.DataFrame,
) -> pd.DataFrame:
    """Build one per-player same-team Delaunay adjacency summary using local ids."""
    visible_players_df = visible_freeze_frame_df(freeze_frame_df)
    required_columns = {"x", "y", "spatial_reference_id"}
    if visible_players_df.empty or not required_columns.issubset(visible_players_df.columns) or delaunay_edges_df.empty:
        return pd.DataFrame()

    reference_df = visible_players_df.copy()
    reference_df["_coords_key"] = reference_df.apply(
        lambda row: normalize_coordinate_key(row.get("x"), row.get("y")),
        axis=1,
    )
    reference_df = reference_df.dropna(subset=["_coords_key"]).drop_duplicates(subset=["_coords_key"], keep="first")
    if reference_df.empty:
        return pd.DataFrame()

    id_by_coords = dict(zip(reference_df["_coords_key"], reference_df["spatial_reference_id"], strict=False))
    team_by_id = {
        str(row["spatial_reference_id"]): safe_display(row.get("team"))
        for _, row in reference_df.iterrows()
        if pd.notna(row.get("spatial_reference_id"))
    }
    neighbor_map = {str(ref_id): set() for ref_id in reference_df["spatial_reference_id"].dropna().astype(str).tolist()}

    for _, edge in delaunay_edges_df.iterrows():
        a_id = id_by_coords.get(normalize_coordinate_key(edge.get("a_x"), edge.get("a_y")))
        b_id = id_by_coords.get(normalize_coordinate_key(edge.get("b_x"), edge.get("b_y")))
        if a_id in {None, ""} or b_id in {None, ""}:
            continue
        a_id = str(a_id)
        b_id = str(b_id)
        if a_id == b_id or team_by_id.get(a_id) != team_by_id.get(b_id):
            continue
        neighbor_map.setdefault(a_id, set()).add(b_id)
        neighbor_map.setdefault(b_id, set()).add(a_id)

    rows: list[dict[str, object]] = []
    for _, player_row in reference_df.iterrows():
        player_id = player_row.get("spatial_reference_id")
        if pd.isna(player_id):
            continue
        player_id = str(player_id)
        neighbors = sorted(neighbor_map.get(player_id, set()), key=spatial_reference_sort_key)
        rows.append(
            {
                "Jugador visible": player_id,
                "Equipo": safe_display(player_row.get("team")),
                "Vecinos del mismo equipo": ", ".join(neighbors) if neighbors else "—",
                "Nº vecinos": len(neighbors),
            }
        )

    result_df = pd.DataFrame(rows)
    if result_df.empty:
        return result_df
    result_df["_sort_key"] = result_df["Jugador visible"].map(spatial_reference_sort_key)
    result_df = result_df.sort_values("_sort_key").drop(columns="_sort_key").reset_index(drop=True)
    return result_df


def build_delaunay_edge_distances_df(
    freeze_frame_df: pd.DataFrame,
    delaunay_edges_df: pd.DataFrame,
) -> pd.DataFrame:
    """Build one readable edge-distance table using local case identifiers."""
    visible_players_df = visible_freeze_frame_df(freeze_frame_df)
    required_columns = {"x", "y", "spatial_reference_id"}
    if visible_players_df.empty or not required_columns.issubset(visible_players_df.columns) or delaunay_edges_df.empty:
        return pd.DataFrame()

    reference_df = visible_players_df.copy()
    reference_df["_coords_key"] = reference_df.apply(
        lambda row: normalize_coordinate_key(row.get("x"), row.get("y")),
        axis=1,
    )
    reference_df = reference_df.dropna(subset=["_coords_key"]).drop_duplicates(subset=["_coords_key"], keep="first")
    if reference_df.empty:
        return pd.DataFrame()

    id_by_coords = dict(zip(reference_df["_coords_key"], reference_df["spatial_reference_id"], strict=False))
    team_by_id = {
        str(row["spatial_reference_id"]): safe_display(row.get("team"))
        for _, row in reference_df.iterrows()
        if pd.notna(row.get("spatial_reference_id"))
    }

    rows: list[dict[str, object]] = []
    for _, edge in delaunay_edges_df.iterrows():
        a_id = id_by_coords.get(normalize_coordinate_key(edge.get("a_x"), edge.get("a_y")))
        b_id = id_by_coords.get(normalize_coordinate_key(edge.get("b_x"), edge.get("b_y")))
        if a_id in {None, ""} or b_id in {None, ""}:
            continue

        a_id = str(a_id)
        b_id = str(b_id)
        first_id, second_id = sorted((a_id, b_id), key=spatial_reference_sort_key)
        first_team = team_by_id.get(first_id, "—")
        second_team = team_by_id.get(second_id, "—")
        relation = "Mismo equipo" if first_team == second_team else "Equipos distintos"

        rows.append(
            {
                "Punto A": first_id,
                "Punto B": second_id,
                "Relación": relation,
                "Distancia": round(pd.to_numeric(edge.get("length"), errors="coerce"), 3),
            }
        )

    result_df = pd.DataFrame(rows).dropna(subset=["Distancia"])
    if result_df.empty:
        return result_df
    result_df["_sort_a"] = result_df["Punto A"].map(spatial_reference_sort_key)
    result_df["_sort_b"] = result_df["Punto B"].map(spatial_reference_sort_key)
    result_df = result_df.sort_values(["_sort_a", "_sort_b", "Distancia"]).drop(columns=["_sort_a", "_sort_b"]).reset_index(drop=True)
    return result_df
