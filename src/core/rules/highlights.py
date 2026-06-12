from __future__ import annotations

import pandas as pd

from src.core.losses.failed_passes import get_failed_passes
from src.core.rules.metric_filters import FINAL_THIRD_THRESHOLD, OWN_HALF_THRESHOLD, PROGRESSIVE_DELTA_X
from src.core.losses.analysis import get_loss_events


def detect_highlight_actions(df: pd.DataFrame) -> pd.DataFrame:
    """Detect highlight actions useful for later storytelling and review."""
    if df.empty:
        return pd.DataFrame(
            columns=[
                "minute",
                "second",
                "team",
                "player",
                "event_type",
                "highlight_type",
                "description",
                "x",
                "y",
                "end_x",
                "end_y",
            ]
        )

    highlights: list[dict[str, object]] = []
    if "event_type" not in df.columns:
        return pd.DataFrame(highlights)

    working_df = df.copy()
    if {"x", "end_x"}.issubset(working_df.columns):
        working_df["x"] = pd.to_numeric(working_df["x"], errors="coerce")
        working_df["end_x"] = pd.to_numeric(working_df["end_x"], errors="coerce")
    if "y" in working_df.columns:
        working_df["y"] = pd.to_numeric(working_df["y"], errors="coerce")
    if "end_y" in working_df.columns:
        working_df["end_y"] = pd.to_numeric(working_df["end_y"], errors="coerce")

    for _, row in working_df.iterrows():
        event_type = row.get("event_type")
        if event_type == "Pass":
            progressive = _is_progressive(row)
            box_entry = _is_box_entry(row)
            if box_entry:
                highlights.append(_build_highlight_row(row, "box_entries", "Pase al área"))
            elif progressive:
                highlights.append(_build_highlight_row(row, "progressive_passes", "Pase progresivo"))
        elif event_type == "Carry" and _is_progressive(row):
            highlights.append(_build_highlight_row(row, "progressive_carries", "Conducción progresiva"))
        elif event_type == "Shot":
            highlights.append(_build_highlight_row(row, "shots", "Finalización"))
        elif event_type == "Ball Recovery" and _coord_value(row, "x") >= OWN_HALF_THRESHOLD:
            highlights.append(_build_highlight_row(row, "high_recoveries", "Recuperación en campo rival"))
        elif event_type == "Pressure" and _coord_value(row, "x") >= FINAL_THIRD_THRESHOLD:
            highlights.append(_build_highlight_row(row, "final_third_pressures", "Presión en último tercio"))

    dangerous_losses = get_loss_events(working_df)
    if not dangerous_losses.empty and "x" in dangerous_losses.columns:
        own_half_losses = dangerous_losses[pd.to_numeric(dangerous_losses["x"], errors="coerce") < OWN_HALF_THRESHOLD]
        for _, row in own_half_losses.iterrows():
            highlights.append(_build_highlight_row(row, "dangerous_losses", "Pérdida en campo propio"))

    return pd.DataFrame(highlights)


def summarize_highlights(df: pd.DataFrame) -> dict[str, int]:
    """Return compact counts for detected highlight actions."""
    highlights_df = detect_highlight_actions(df)
    if highlights_df.empty:
        return {
            "total_highlights": 0,
            "progressive_passes": 0,
            "box_entries": 0,
            "progressive_carries": 0,
            "shots": 0,
            "high_recoveries": 0,
            "final_third_pressures": 0,
            "dangerous_losses": 0,
        }

    return {
        "total_highlights": int(len(highlights_df)),
        "progressive_passes": int(highlights_df["highlight_type"].eq("progressive_passes").sum()),
        "box_entries": int(highlights_df["highlight_type"].eq("box_entries").sum()),
        "progressive_carries": int(highlights_df["highlight_type"].eq("progressive_carries").sum()),
        "shots": int(highlights_df["highlight_type"].eq("shots").sum()),
        "high_recoveries": int(highlights_df["highlight_type"].eq("high_recoveries").sum()),
        "final_third_pressures": int(highlights_df["highlight_type"].eq("final_third_pressures").sum()),
        "dangerous_losses": int(highlights_df["highlight_type"].eq("dangerous_losses").sum()),
    }


def _is_progressive(row: pd.Series) -> bool:
    """Return whether the row advances the ball at least 10 meters on X."""
    x = _coord_value(row, "x")
    end_x = _coord_value(row, "end_x")
    return pd.notna(x) and pd.notna(end_x) and (end_x - x >= PROGRESSIVE_DELTA_X)


def _is_box_entry(row: pd.Series) -> bool:
    """Return whether the row ends in the penalty area."""
    end_x = _coord_value(row, "end_x")
    end_y = _coord_value(row, "end_y")
    return pd.notna(end_x) and pd.notna(end_y) and end_x >= 102 and 18 <= end_y <= 62


def _build_highlight_row(row: pd.Series, highlight_type: str, description: str) -> dict[str, object]:
    """Build a standardized highlight row."""
    return {
        "minute": row.get("minute"),
        "second": row.get("second"),
        "team": row.get("team"),
        "player": row.get("player"),
        "event_type": row.get("event_type"),
        "highlight_type": highlight_type,
        "description": description,
        "x": row.get("x"),
        "y": row.get("y"),
        "end_x": row.get("end_x"),
        "end_y": row.get("end_y"),
    }


def _coord_value(row: pd.Series, column: str) -> float:
    """Return a numeric coordinate value or NaN."""
    return pd.to_numeric(pd.Series([row.get(column)]), errors="coerce").iloc[0]
