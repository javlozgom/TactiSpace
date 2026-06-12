from __future__ import annotations

import pandas as pd

from src.core.spatial.pass_decision import resolve_scoring_profile


def safe_display(value: object) -> str:
    """Render a safe user-facing display value."""
    if value is None or pd.isna(value):
        return "-"
    return str(value)


def safe_int_like(value: object) -> int:
    """Cast one minute/second-like value safely."""
    numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    if pd.isna(numeric):
        return 0
    return int(numeric)


def format_ratio(numerator: int, denominator: int) -> str:
    """Format one count ratio including percentage safely."""
    if denominator <= 0:
        return f"{numerator} / {denominator} (0.0%)"
    return f"{numerator} / {denominator} ({(numerator / denominator) * 100:.1f}%)"


def format_coordinate_pair(x_value: object, y_value: object) -> str:
    """Format a coordinate pair safely."""
    x_num = pd.to_numeric(pd.Series([x_value]), errors="coerce").iloc[0]
    y_num = pd.to_numeric(pd.Series([y_value]), errors="coerce").iloc[0]
    if pd.isna(x_num) or pd.isna(y_num):
        return "-"
    return f"({x_num:.2f}, {y_num:.2f})"


def format_location(location: object) -> str:
    """Format one recommended location."""
    if location is None:
        return "-"
    if isinstance(location, (list, tuple)) and len(location) >= 2:
        x_val = pd.to_numeric(pd.Series([location[0]]), errors="coerce").iloc[0]
        y_val = pd.to_numeric(pd.Series([location[1]]), errors="coerce").iloc[0]
        if pd.notna(x_val) and pd.notna(y_val):
            return f"({x_val:.2f}, {y_val:.2f})"
    return str(location)


def format_score(score: object) -> str:
    """Format numeric scores consistently."""
    if score is None:
        return "-"
    if isinstance(score, (int, float)):
        return f"{float(score):.3f}"
    return str(score)


def normalize_merge_key(value: object) -> str | None:
    """Normalize one merge key so mixed pandas dtypes do not break local joins."""
    if value is None or pd.isna(value):
        return None
    return str(value).strip()


def normalize_coordinate_key(x_value: object, y_value: object) -> str | None:
    """Normalize one x,y pair for tolerant local table enrichment."""
    x_num = pd.to_numeric(pd.Series([x_value]), errors="coerce").iloc[0]
    y_num = pd.to_numeric(pd.Series([y_value]), errors="coerce").iloc[0]
    if pd.isna(x_num) or pd.isna(y_num):
        return None
    return f"{float(x_num):.6f}|{float(y_num):.6f}"


def spatial_reference_sort_key(reference_id: object) -> tuple[int, int, str]:
    """Sort local ids such as T1, T2, R1 in one stable readable order."""
    text = str(reference_id or "")
    if not text:
        return (9, 0, "")
    prefix = text[0]
    numeric_part = text[1:]
    try:
        number = int(numeric_part)
    except Exception:
        number = 0
    prefix_order = {"T": 0, "R": 1}.get(prefix, 9)
    return (prefix_order, number, text)


def describe_scoring_profile_compact(scoring_profile: object) -> str:
    """Return one short comparison-friendly summary of the active scoring profile."""
    resolved_profile = resolve_scoring_profile(scoring_profile)
    descriptions = {
        "Conservador": "Seguridad, menor presión rival y coste de pase controlado.",
        "Intermedio": "Equilibrio entre progresión, espacio, presión y distancia.",
        "Arriesgado": "Más progresión y espacio, aceptando mayor coste de pase.",
    }
    return descriptions[resolved_profile]


def normalize_recommendation_text(recommendation: dict) -> None:
    """Replace missing player placeholders in recommendation text with spatial ids when available."""
    if not isinstance(recommendation, dict):
        return

    recommended_player = recommendation.get("recommended_player")
    recommended_reference_id = recommendation.get("spatial_reference_id")
    fallback_label = recommended_player or recommended_reference_id or "el receptor sugerido"

    if not recommended_player and recommended_reference_id:
        recommendation["recommended_player"] = recommended_reference_id

    reason = recommendation.get("reason")
    if isinstance(reason, str) and "None" in reason:
        recommendation["reason"] = reason.replace("None", str(fallback_label))
