from __future__ import annotations

import math
from typing import Any

import pandas as pd

from src.core.spatial.freeze_frame import split_freeze_frame_players
from src.core.losses.analysis import is_failed_outcome
from src.core.metrics.basic import get_effective_outcome_series

DEFAULT_SCORING_PROFILE = "Intermedio"
SCORING_PROFILE_WEIGHTS: dict[str, dict[str, float]] = {
    "Conservador": {
        "forward_progress": 0.5,
        "nearest_opponent_distance": 1.3,
        "voronoi_area": 0.8,
        "distance_to_passer_penalty": -0.7,
    },
    "Intermedio": {
        "forward_progress": 1.0,
        "nearest_opponent_distance": 1.0,
        "voronoi_area": 1.0,
        "distance_to_passer_penalty": -0.3,
    },
    "Arriesgado": {
        "forward_progress": 1.5,
        "nearest_opponent_distance": 0.7,
        "voronoi_area": 1.2,
        "distance_to_passer_penalty": -0.15,
    },
}


def get_failed_pass_candidates(events_df: pd.DataFrame) -> pd.DataFrame:
    """Return failed pass events enriched with simple contextual flags."""
    if events_df.empty or "event_type" not in events_df.columns:
        return pd.DataFrame()

    pass_df = events_df[events_df["event_type"] == "Pass"].copy()
    if pass_df.empty:
        return pass_df

    outcome_series = get_effective_outcome_series(pass_df)
    failed_mask = outcome_series.map(is_failed_outcome)
    failed_pass_df = pass_df[failed_mask].copy()
    if failed_pass_df.empty:
        return failed_pass_df

    failed_pass_df["pass_length"] = _compute_pass_length_series(failed_pass_df)
    failed_pass_df["progressive"] = _compute_progressive_mask(failed_pass_df)
    failed_pass_df["to_final_third"] = _compute_final_third_mask(failed_pass_df)
    failed_pass_df["box_entry"] = _compute_box_entry_mask(failed_pass_df)
    return failed_pass_df.reset_index(drop=True)


def build_pass_options(
    failed_pass_event: pd.Series,
    freeze_frame_df: pd.DataFrame,
    voronoi_regions_df: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Build one candidate-receiver table from a failed pass freeze-frame."""
    teammates_df, opponents_df = split_freeze_frame_players(freeze_frame_df)
    if teammates_df.empty:
        return pd.DataFrame(
            columns=[
                "player",
                "player_id",
                "x",
                "y",
                "distance_to_passer",
                "forward_progress",
                "nearest_opponent_distance",
                "voronoi_area",
                "is_visible",
            ]
        )

    passer_name = failed_pass_event.get("player")
    passer_x = _to_float(failed_pass_event.get("x"), 0.0)
    passer_y = _to_float(failed_pass_event.get("y"), 0.0)
    candidates_df = teammates_df.copy()

    if "actor" in candidates_df.columns and candidates_df["actor"].fillna(False).astype(bool).any():
        candidates_df = candidates_df[~candidates_df["actor"].fillna(False).astype(bool)].copy()
    elif passer_name is not None and "player" in candidates_df.columns:
        candidates_df = candidates_df[candidates_df["player"].astype(str) != str(passer_name)].copy()

    if candidates_df.empty:
        return pd.DataFrame()

    rows: list[dict[str, Any]] = []
    for _, candidate in candidates_df.iterrows():
        candidate_x = _to_float(candidate.get("x"), None)
        candidate_y = _to_float(candidate.get("y"), None)
        if candidate_x is None or candidate_y is None:
            continue

        rows.append(
            {
                "player": candidate.get("player"),
                "player_id": candidate.get("player_id"),
                "x": candidate_x,
                "y": candidate_y,
                "distance_to_passer": math.dist((passer_x, passer_y), (candidate_x, candidate_y)),
                "forward_progress": candidate_x - passer_x,
                "nearest_opponent_distance": _nearest_opponent_distance(candidate_x, candidate_y, opponents_df),
                "voronoi_area": _lookup_voronoi_area(candidate, voronoi_regions_df),
                "is_visible": bool(candidate.get("visible", True)),
            }
        )

    return pd.DataFrame(rows)


def score_pass_options(
    options_df: pd.DataFrame,
    scoring_profile: str = DEFAULT_SCORING_PROFILE,
) -> pd.DataFrame:
    """Score candidate pass options with a simple interpretable heuristic."""
    if options_df.empty:
        return options_df.copy()

    resolved_profile = resolve_scoring_profile(scoring_profile)
    weights = SCORING_PROFILE_WEIGHTS[resolved_profile]
    scored_df = options_df.copy()
    scored_df["forward_progress_norm"] = _normalize_series(scored_df.get("forward_progress", 0))
    scored_df["nearest_opponent_distance_norm"] = _normalize_series(scored_df.get("nearest_opponent_distance", 0))
    scored_df["voronoi_area_norm"] = _normalize_series(scored_df.get("voronoi_area", 0))
    scored_df["distance_to_passer_norm"] = _normalize_series(scored_df.get("distance_to_passer", 0))

    scored_df["pass_score"] = (
        (scored_df["forward_progress_norm"] * weights["forward_progress"])
        + (scored_df["nearest_opponent_distance_norm"] * weights["nearest_opponent_distance"])
        + (scored_df["voronoi_area_norm"] * weights["voronoi_area"])
        + (scored_df["distance_to_passer_norm"] * weights["distance_to_passer_penalty"])
    ).round(3)
    scored_df["scoring_profile"] = resolved_profile
    scored_df = scored_df.sort_values(["pass_score", "player"], ascending=[False, True]).reset_index(drop=True)
    scored_df["rank"] = range(1, len(scored_df) + 1)
    return scored_df


def suggest_alternative_pass(
    failed_pass_event: pd.Series,
    freeze_frame_df: pd.DataFrame,
    voronoi_regions_df: pd.DataFrame | None = None,
    scoring_profile: str = DEFAULT_SCORING_PROFILE,
) -> dict[str, Any]:
    """Suggest one spatially favorable alternative for a failed pass."""
    resolved_profile = resolve_scoring_profile(scoring_profile)
    options_df = build_pass_options(
        failed_pass_event=failed_pass_event,
        freeze_frame_df=freeze_frame_df,
        voronoi_regions_df=voronoi_regions_df,
    )
    scored_options_df = score_pass_options(options_df, scoring_profile=resolved_profile)
    if scored_options_df.empty:
        return {
            "recommended_player": None,
            "recommended_location": None,
            "score": 0,
            "reason": "No hay candidatos suficientes en el freeze-frame.",
            "score_breakdown": [],
            "scoring_profile": resolved_profile,
            "options": scored_options_df,
        }

    best_option = scored_options_df.iloc[0]
    recommendation = {
        "recommended_player": best_option.get("player"),
        "recommended_location": (best_option.get("x"), best_option.get("y")),
        "score": float(best_option.get("pass_score", 0)),
        "reason": describe_pass_recommendation(
            {"options": scored_options_df, "best_option": best_option},
            scoring_profile=resolved_profile,
        ),
        "score_breakdown": _build_score_breakdown(best_option, scoring_profile=resolved_profile),
        "scoring_profile": resolved_profile,
        "options": scored_options_df,
    }
    return recommendation


def suggest_alternative_pass_by_voronoi_area(
    failed_pass_event: pd.Series,
    freeze_frame_df: pd.DataFrame,
    voronoi_regions_df: pd.DataFrame | None = None,
) -> dict[str, Any]:
    """Suggest one alternative prioritizing Voronoi area and local free space."""
    options_df = build_pass_options(
        failed_pass_event=failed_pass_event,
        freeze_frame_df=freeze_frame_df,
        voronoi_regions_df=voronoi_regions_df,
    )
    if options_df.empty:
        return {
            "recommended_player": None,
            "recommended_location": None,
            "score": 0,
            "reason": "No hay candidatos suficientes en el freeze-frame.",
            "score_breakdown": [],
            "options": options_df,
        }

    ranked_options_df = options_df.copy()
    for column in [
        "voronoi_area",
        "nearest_opponent_distance",
        "forward_progress",
        "distance_to_passer",
    ]:
        if column in ranked_options_df.columns:
            ranked_options_df[column] = pd.to_numeric(ranked_options_df[column], errors="coerce").fillna(0.0)

    ranked_options_df = ranked_options_df.sort_values(
        ["voronoi_area", "nearest_opponent_distance", "forward_progress", "distance_to_passer", "player"],
        ascending=[False, False, False, True, True],
    ).reset_index(drop=True)
    ranked_options_df["rank"] = range(1, len(ranked_options_df) + 1)
    ranked_options_df["voronoi_result"] = ranked_options_df["voronoi_area"]

    best_option = ranked_options_df.iloc[0]
    return {
        "recommended_player": best_option.get("player"),
        "recommended_location": (best_option.get("x"), best_option.get("y")),
        "score": float(best_option.get("voronoi_area", 0)),
        "reason": describe_voronoi_recommendation(
            {"options": ranked_options_df, "best_option": best_option}
        ),
        "score_breakdown": _build_voronoi_breakdown(best_option),
        "options": ranked_options_df,
    }


def describe_pass_recommendation(
    recommendation: dict,
    scoring_profile: str = DEFAULT_SCORING_PROFILE,
) -> str:
    """Return one readable explanation for the suggested alternative."""
    best_option = recommendation.get("best_option")
    if best_option is None and isinstance(recommendation.get("options"), pd.DataFrame) and not recommendation["options"].empty:
        best_option = recommendation["options"].iloc[0]
    if best_option is None:
        return "No hay una alternativa sugerida por falta de candidatos espaciales."

    player_name = best_option.get("player") or "el receptor sugerido"
    resolved_profile = resolve_scoring_profile(scoring_profile)
    profile_messages = {
        "Conservador": (
            f"Se sugiere buscar a {player_name} como alternativa conservadora, "
            "priorizando seguridad, menor presión rival cercana y un coste de pase más controlado."
        ),
        "Intermedio": (
            f"Se sugiere buscar a {player_name} como alternativa espacialmente favorable, "
            "porque equilibra espacio disponible, presión rival cercana, progresión y distancia de pase."
        ),
        "Arriesgado": (
            f"Se sugiere buscar a {player_name} como alternativa arriesgada, "
            "priorizando progresión y ganancia espacial aunque el coste del pase pueda ser mayor."
        ),
    }
    return profile_messages[resolved_profile]


def describe_voronoi_recommendation(recommendation: dict) -> str:
    """Return one readable explanation for the Voronoi-first alternative."""
    best_option = recommendation.get("best_option")
    if best_option is None and isinstance(recommendation.get("options"), pd.DataFrame) and not recommendation["options"].empty:
        best_option = recommendation["options"].iloc[0]
    if best_option is None:
        return "No hay una alternativa sugerida por Voronoi por falta de candidatos espaciales."

    player_name = best_option.get("player") or "el receptor sugerido"
    return (
        f"Se sugiere buscar a {player_name} como alternativa Voronoi, "
        "priorizando la mayor área de influencia disponible y usando el espacio libre cercano como criterio de apoyo."
    )


def resolve_scoring_profile(scoring_profile: object) -> str:
    """Return one supported scoring profile with safe fallback."""
    if not isinstance(scoring_profile, str):
        return DEFAULT_SCORING_PROFILE
    return scoring_profile if scoring_profile in SCORING_PROFILE_WEIGHTS else DEFAULT_SCORING_PROFILE


def _compute_pass_length_series(df: pd.DataFrame) -> pd.Series:
    """Compute pass length from origin and destination coordinates."""
    required_columns = {"x", "y", "end_x", "end_y"}
    if not required_columns.issubset(df.columns):
        return pd.Series(0.0, index=df.index)
    coords = df[["x", "y", "end_x", "end_y"]].apply(pd.to_numeric, errors="coerce")
    return (((coords["end_x"] - coords["x"]) ** 2 + (coords["end_y"] - coords["y"]) ** 2) ** 0.5).fillna(0).round(2)


def _compute_progressive_mask(df: pd.DataFrame) -> pd.Series:
    """Flag whether each pass progresses at least 10 meters in x."""
    if not {"x", "end_x"}.issubset(df.columns):
        return pd.Series(False, index=df.index)
    coords = df[["x", "end_x"]].apply(pd.to_numeric, errors="coerce")
    return (coords["end_x"] - coords["x"] >= 10).fillna(False)


def _compute_final_third_mask(df: pd.DataFrame) -> pd.Series:
    """Flag whether the pass reaches the final third."""
    if "end_x" not in df.columns:
        return pd.Series(False, index=df.index)
    end_x = pd.to_numeric(df["end_x"], errors="coerce")
    return (end_x >= 80).fillna(False)


def _compute_box_entry_mask(df: pd.DataFrame) -> pd.Series:
    """Flag whether the pass reaches the box."""
    if not {"end_x", "end_y"}.issubset(df.columns):
        return pd.Series(False, index=df.index)
    coords = df[["end_x", "end_y"]].apply(pd.to_numeric, errors="coerce")
    return ((coords["end_x"] >= 102) & coords["end_y"].between(18, 62)).fillna(False)


def _nearest_opponent_distance(x_value: float, y_value: float, opponents_df: pd.DataFrame) -> float:
    """Return nearest opponent distance for one candidate."""
    if opponents_df.empty:
        return 0.0
    coords_df = opponents_df[["x", "y"]].apply(pd.to_numeric, errors="coerce").dropna()
    if coords_df.empty:
        return 0.0
    distances = ((coords_df["x"] - x_value) ** 2 + (coords_df["y"] - y_value) ** 2) ** 0.5
    return float(distances.min()) if not distances.empty else 0.0


def _lookup_voronoi_area(candidate_row: pd.Series, voronoi_regions_df: pd.DataFrame | None) -> float:
    """Look up Voronoi area for one candidate."""
    if voronoi_regions_df is None or voronoi_regions_df.empty:
        return 0.0

    def _extract_area(match_df: pd.DataFrame) -> float:
        if match_df.empty:
            return 0.0
        area_value = match_df.iloc[0].get("voronoi_area", match_df.iloc[0].get("area", 0))
        numeric_area = pd.to_numeric(pd.Series([area_value]), errors="coerce").iloc[0]
        return float(numeric_area) if pd.notna(numeric_area) else 0.0

    if pd.notna(candidate_row.get("player_id")) and "player_id" in voronoi_regions_df.columns:
        match_df = voronoi_regions_df[voronoi_regions_df["player_id"] == candidate_row.get("player_id")]
        if not match_df.empty:
            return _extract_area(match_df)
    if pd.notna(candidate_row.get("player")) and "player" in voronoi_regions_df.columns:
        match_df = voronoi_regions_df[voronoi_regions_df["player"].astype(str) == str(candidate_row.get("player"))]
        if not match_df.empty:
            return _extract_area(match_df)
    if {"x", "y"}.issubset(candidate_row.index) and {"x", "y"}.issubset(voronoi_regions_df.columns):
        candidate_x = _to_float(candidate_row.get("x"), None)
        candidate_y = _to_float(candidate_row.get("y"), None)
        if candidate_x is not None and candidate_y is not None:
            coords_df = voronoi_regions_df[["x", "y"]].apply(pd.to_numeric, errors="coerce")
            match_mask = (
                coords_df["x"].sub(candidate_x).abs().lt(1e-6)
                & coords_df["y"].sub(candidate_y).abs().lt(1e-6)
            )
            match_df = voronoi_regions_df.loc[match_mask]
            if not match_df.empty:
                return _extract_area(match_df)
    return 0.0


def _normalize_series(series_like: object) -> pd.Series:
    """Normalize one numeric series safely to the [0, 1] range."""
    series = pd.to_numeric(pd.Series(series_like), errors="coerce").fillna(0)
    min_value = float(series.min()) if not series.empty else 0.0
    max_value = float(series.max()) if not series.empty else 0.0
    if max_value == min_value:
        return pd.Series(0.0, index=series.index)
    return (series - min_value) / (max_value - min_value)


def _build_score_breakdown(
    best_option: pd.Series,
    scoring_profile: str = DEFAULT_SCORING_PROFILE,
) -> list[dict[str, float | str | None]]:
    """Return one explicit breakdown of the current pass scoring heuristic."""
    resolved_profile = resolve_scoring_profile(scoring_profile)
    weights = SCORING_PROFILE_WEIGHTS[resolved_profile]
    progression_weight = weights["forward_progress"]
    nearest_opponent_weight = weights["nearest_opponent_distance"]
    voronoi_weight = weights["voronoi_area"]
    distance_penalty_weight = weights["distance_to_passer_penalty"]

    progression_norm = _to_float(best_option.get("forward_progress_norm"), 0.0) or 0.0
    nearest_opponent_norm = _to_float(best_option.get("nearest_opponent_distance_norm"), 0.0) or 0.0
    voronoi_norm = _to_float(best_option.get("voronoi_area_norm"), 0.0) or 0.0
    distance_norm = _to_float(best_option.get("distance_to_passer_norm"), 0.0) or 0.0
    final_score = _to_float(best_option.get("pass_score"), 0.0) or 0.0

    return [
        {
            "factor": "progression",
            "value": progression_norm,
            "weight": progression_weight,
            "contribution": progression_norm * progression_weight,
        },
        {
            "factor": "nearest_opponent_distance",
            "value": nearest_opponent_norm,
            "weight": nearest_opponent_weight,
            "contribution": nearest_opponent_norm * nearest_opponent_weight,
        },
        {
            "factor": "voronoi_area",
            "value": voronoi_norm,
            "weight": voronoi_weight,
            "contribution": voronoi_norm * voronoi_weight,
        },
        {
            "factor": "distance_penalty",
            "value": distance_norm,
            "weight": distance_penalty_weight,
            "contribution": distance_norm * distance_penalty_weight,
        },
        {
            "factor": "final_score",
            "value": final_score,
            "weight": None,
            "contribution": final_score,
        },
    ]


def _build_voronoi_breakdown(best_option: pd.Series) -> list[dict[str, float | str | None]]:
    """Return one explicit breakdown for the Voronoi-first recommendation."""
    return [
        {
            "factor": "voronoi_area",
            "value": _to_float(best_option.get("voronoi_area"), 0.0) or 0.0,
            "math_weight": "No aplica",
            "priority": 1,
            "direction": "Maximizar",
            "contribution": _to_float(best_option.get("voronoi_area"), 0.0) or 0.0,
        },
        {
            "factor": "nearest_opponent_distance",
            "value": _to_float(best_option.get("nearest_opponent_distance"), 0.0) or 0.0,
            "math_weight": "No aplica",
            "priority": 2,
            "direction": "Maximizar",
            "contribution": _to_float(best_option.get("nearest_opponent_distance"), 0.0) or 0.0,
        },
        {
            "factor": "forward_progress",
            "value": _to_float(best_option.get("forward_progress"), 0.0) or 0.0,
            "math_weight": "No aplica",
            "priority": 3,
            "direction": "Maximizar",
            "contribution": _to_float(best_option.get("forward_progress"), 0.0) or 0.0,
        },
        {
            "factor": "distance_to_passer",
            "value": _to_float(best_option.get("distance_to_passer"), 0.0) or 0.0,
            "math_weight": "No aplica",
            "priority": 4,
            "direction": "Minimizar",
            "contribution": _to_float(best_option.get("distance_to_passer"), 0.0) or 0.0,
        },
        {
            "factor": "final_score",
            "value": _to_float(best_option.get("voronoi_area"), 0.0) or 0.0,
            "math_weight": "No aplica",
            "priority": None,
            "direction": "Resultado",
            "contribution": _to_float(best_option.get("voronoi_area"), 0.0) or 0.0,
        },
    ]


def _to_float(value: object, default: float | None) -> float | None:
    """Convert a scalar to float with default fallback."""
    if value is None or pd.isna(value):
        return default
    try:
        return float(value)
    except Exception:
        return default
