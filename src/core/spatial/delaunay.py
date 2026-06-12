from __future__ import annotations

import math

import pandas as pd
from scipy.spatial import Delaunay


PITCH_X_MIN = 0.0
PITCH_X_MAX = 120.0
PITCH_Y_MIN = 0.0
PITCH_Y_MAX = 80.0


def compute_delaunay_edges(freeze_frame_df: pd.DataFrame) -> pd.DataFrame:
    """Compute one edge table from a freeze-frame using Delaunay triangulation."""
    if freeze_frame_df is None or freeze_frame_df.empty:
        return pd.DataFrame()

    if not {"x", "y"}.issubset(freeze_frame_df.columns):
        return pd.DataFrame()

    points_df = freeze_frame_df.copy()
    points_df["x"] = pd.to_numeric(points_df["x"], errors="coerce")
    points_df["y"] = pd.to_numeric(points_df["y"], errors="coerce")
    points_df = points_df.dropna(subset=["x", "y"])
    points_df = points_df[
        points_df["x"].between(PITCH_X_MIN, PITCH_X_MAX)
        & points_df["y"].between(PITCH_Y_MIN, PITCH_Y_MAX)
    ].reset_index(drop=True)

    if len(points_df) < 3:
        return pd.DataFrame()

    try:
        triangulation = Delaunay(points_df[["x", "y"]].to_numpy())
    except Exception:
        return pd.DataFrame()

    edge_indexes: set[tuple[int, int]] = set()
    for simplex in triangulation.simplices:
        simplex_points = [int(point_idx) for point_idx in simplex]
        for i, j in (
            (simplex_points[0], simplex_points[1]),
            (simplex_points[1], simplex_points[2]),
            (simplex_points[2], simplex_points[0]),
        ):
            edge_indexes.add(tuple(sorted((i, j))))

    rows: list[dict] = []
    for i, j in sorted(edge_indexes):
        player_a = points_df.iloc[i]
        player_b = points_df.iloc[j]
        rows.append(
            {
                "a_index": i,
                "b_index": j,
                "a_x": float(player_a["x"]),
                "a_y": float(player_a["y"]),
                "b_x": float(player_b["x"]),
                "b_y": float(player_b["y"]),
                "a_teammate": bool(player_a.get("teammate", False)),
                "b_teammate": bool(player_b.get("teammate", False)),
                "a_actor": bool(player_a.get("actor", False)),
                "b_actor": bool(player_b.get("actor", False)),
                "a_player": player_a.get("player", player_a.get("player_name")),
                "b_player": player_b.get("player", player_b.get("player_name")),
                "length": _distance(
                    player_a["x"],
                    player_a["y"],
                    player_b["x"],
                    player_b["y"],
                ),
            }
        )

    return pd.DataFrame(rows)


def recommend_pass_by_delaunay(
    event_row: pd.Series,
    freeze_frame_df: pd.DataFrame,
    delaunay_edges_df: pd.DataFrame,
) -> dict:
    """Recommend a teammate connected to the actor by one Delaunay edge."""
    empty_candidates = pd.DataFrame(
        columns=["player", "x", "y", "edge_length", "progression", "distance", "delaunay_score"]
    )
    empty_result = {
        "recommended_player": None,
        "recommended_location": None,
        "delaunay_score": None,
        "progression": None,
        "distance": None,
        "edge_length": None,
        "reason": "No hay suficientes datos para una recomendación Delaunay.",
        "score_breakdown": [],
        "candidates": empty_candidates,
    }

    if freeze_frame_df is None or freeze_frame_df.empty:
        return empty_result | {"reason": "El freeze-frame está vacío para este evento."}

    actor_mask = (
        freeze_frame_df["actor"].fillna(False).astype(bool)
        if "actor" in freeze_frame_df.columns
        else pd.Series(False, index=freeze_frame_df.index)
    )
    actor_df = freeze_frame_df[actor_mask].copy()
    if actor_df.empty:
        return empty_result | {"reason": "No se encontró un actor marcado en el freeze-frame."}

    if delaunay_edges_df is None or delaunay_edges_df.empty:
        return empty_result | {"reason": "No hay aristas Delaunay disponibles para este freeze-frame."}

    actor = actor_df.iloc[0]
    actor_x = _to_float(actor.get("x"), None)
    actor_y = _to_float(actor.get("y"), None)
    if actor_x is None or actor_y is None:
        return empty_result | {"reason": "El actor no tiene coordenadas válidas."}

    start_x = _to_float(event_row.get("x"), actor_x)
    start_y = _to_float(event_row.get("y"), actor_y)

    candidate_rows: list[dict] = []
    for _, edge in delaunay_edges_df.iterrows():
        candidate = None

        if bool(edge.get("a_actor", False)) and bool(edge.get("b_teammate", False)):
            candidate = {
                "player": edge.get("b_player"),
                "x": _to_float(edge.get("b_x"), None),
                "y": _to_float(edge.get("b_y"), None),
                "edge_length": _to_float(edge.get("length"), None),
            }
        elif bool(edge.get("b_actor", False)) and bool(edge.get("a_teammate", False)):
            candidate = {
                "player": edge.get("a_player"),
                "x": _to_float(edge.get("a_x"), None),
                "y": _to_float(edge.get("a_y"), None),
                "edge_length": _to_float(edge.get("length"), None),
            }

        if candidate is None or candidate["x"] is None or candidate["y"] is None:
            continue

        progression = candidate["x"] - start_x
        distance = _distance(start_x, start_y, candidate["x"], candidate["y"])
        edge_length = candidate["edge_length"] if candidate["edge_length"] is not None else distance

        progression_score = max(progression, 0.0) / 120.0
        compactness_score = max(0.0, 1.0 - (edge_length / 80.0))
        distance_penalty = distance / 120.0
        delaunay_score = (0.6 * progression_score) + (0.35 * compactness_score) - (0.1 * distance_penalty)

        candidate_rows.append(
            {
                **candidate,
                "progression": progression,
                "distance": distance,
                "progression_score": progression_score,
                "compactness_score": compactness_score,
                "distance_penalty": distance_penalty,
                "delaunay_score": delaunay_score,
            }
        )

    if not candidate_rows:
        return empty_result | {"reason": "El actor no tiene compañeros conectados por una arista Delaunay."}

    candidates_df = (
        pd.DataFrame(candidate_rows)
        .sort_values(["delaunay_score", "progression", "player"], ascending=[False, False, True])
        .reset_index(drop=True)
    )
    best = candidates_df.iloc[0]

    return {
        "recommended_player": best.get("player"),
        "recommended_location": (float(best["x"]), float(best["y"])),
        "delaunay_score": float(best["delaunay_score"]),
        "progression": float(best["progression"]),
        "distance": float(best["distance"]),
        "edge_length": float(best["edge_length"]),
        "reason": (
            "Se prioriza un compañero conectado al actor por Delaunay, con progresión positiva, "
            "arista compacta y distancia moderada al pasador."
        ),
        "score_breakdown": _build_delaunay_score_breakdown(best),
        "candidates": candidates_df,
    }


def _distance(x1: object, y1: object, x2: object, y2: object) -> float:
    return math.dist((float(x1), float(y1)), (float(x2), float(y2)))


def _to_float(value: object, default: float | None) -> float | None:
    if value is None or pd.isna(value):
        return default
    try:
        return float(value)
    except Exception:
        return default


def _build_delaunay_score_breakdown(best_option: pd.Series) -> list[dict[str, float | str | None]]:
    """Return one explicit breakdown of the current Delaunay heuristic."""
    progression_weight = 0.6
    compactness_weight = 0.35
    distance_penalty_weight = -0.1

    progression_score = _to_float(best_option.get("progression_score"), 0.0) or 0.0
    compactness_score = _to_float(best_option.get("compactness_score"), 0.0) or 0.0
    distance_penalty = _to_float(best_option.get("distance_penalty"), 0.0) or 0.0
    final_score = _to_float(best_option.get("delaunay_score"), 0.0) or 0.0

    return [
        {
            "factor": "progression_score",
            "value": progression_score,
            "weight": progression_weight,
            "contribution": progression_score * progression_weight,
        },
        {
            "factor": "compactness_score",
            "value": compactness_score,
            "weight": compactness_weight,
            "contribution": compactness_score * compactness_weight,
        },
        {
            "factor": "distance_penalty",
            "value": distance_penalty,
            "weight": distance_penalty_weight,
            "contribution": distance_penalty * distance_penalty_weight,
        },
        {
            "factor": "final_score",
            "value": final_score,
            "weight": None,
            "contribution": final_score,
        },
    ]
