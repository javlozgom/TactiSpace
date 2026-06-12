from __future__ import annotations

import math

import pandas as pd

from src.core.losses.analysis import is_failed_outcome
from src.core.rules.metric_filters import (
    BOX_ENTRY_X_THRESHOLD,
    BOX_ENTRY_Y_MAX,
    BOX_ENTRY_Y_MIN,
    FINAL_THIRD_THRESHOLD,
    OWN_HALF_THRESHOLD,
    PROGRESSIVE_DELTA_X,
)
from src.core.metrics.basic import get_effective_outcome_series


def get_failed_passes(df: pd.DataFrame) -> pd.DataFrame:
    """Return failed passes with derived spatial descriptors."""
    if df.empty or "event_type" not in df.columns:
        return pd.DataFrame(columns=list(df.columns))

    outcome_series = (
        get_effective_outcome_series(df).fillna("").astype(str)
        if {"outcome", "inferred_outcome"}.intersection(df.columns)
        else pd.Series("", index=df.index, dtype="object")
    )
    failed_pass_df = df[df["event_type"].eq("Pass") & outcome_series.map(is_failed_outcome)].copy()
    if failed_pass_df.empty:
        return failed_pass_df

    coords = failed_pass_df.loc[:, [column for column in ["x", "y", "end_x", "end_y"] if column in failed_pass_df.columns]]
    for column in ["x", "y", "end_x", "end_y"]:
        if column in coords.columns:
            failed_pass_df[column] = pd.to_numeric(failed_pass_df[column], errors="coerce")

    failed_pass_df["pass_length"] = _pass_length_series(failed_pass_df)
    failed_pass_df["progressive"] = _progressive_mask(failed_pass_df)
    failed_pass_df["to_final_third"] = (failed_pass_df.get("end_x", pd.Series(float("nan"), index=failed_pass_df.index)) >= FINAL_THIRD_THRESHOLD).fillna(False)
    failed_pass_df["box_entry"] = _box_entry_mask(failed_pass_df)
    failed_pass_df["origin_zone"] = _zone_label_series(failed_pass_df.get("x", pd.Series(float("nan"), index=failed_pass_df.index)))
    failed_pass_df["destination_zone"] = _zone_label_series(failed_pass_df.get("end_x", pd.Series(float("nan"), index=failed_pass_df.index)))
    return failed_pass_df


def calculate_failed_pass_metrics(df: pd.DataFrame) -> dict[str, float | int]:
    """Calculate compact failed-pass metrics."""
    failed_pass_df = get_failed_passes(df)
    if failed_pass_df.empty:
        return {
            "total_failed_passes": 0,
            "average_length": 0.0,
            "progressive_failed_passes": 0,
            "failed_passes_to_final_third": 0,
            "failed_box_entries": 0,
            "failed_passes_own_half": 0,
            "failed_passes_opponent_half": 0,
        }

    x_series = pd.to_numeric(failed_pass_df["x"], errors="coerce") if "x" in failed_pass_df.columns else pd.Series(float("nan"), index=failed_pass_df.index)
    pass_length = pd.to_numeric(failed_pass_df["pass_length"], errors="coerce").dropna()
    return {
        "total_failed_passes": int(len(failed_pass_df)),
        "average_length": round(float(pass_length.mean()), 2) if not pass_length.empty else 0.0,
        "progressive_failed_passes": int(failed_pass_df["progressive"].fillna(False).sum()),
        "failed_passes_to_final_third": int(failed_pass_df["to_final_third"].fillna(False).sum()),
        "failed_box_entries": int(failed_pass_df["box_entry"].fillna(False).sum()),
        "failed_passes_own_half": int((x_series < OWN_HALF_THRESHOLD).fillna(False).sum()),
        "failed_passes_opponent_half": int((x_series >= OWN_HALF_THRESHOLD).fillna(False).sum()),
    }


def summarize_failed_passes_by_player(df: pd.DataFrame) -> pd.DataFrame:
    """Summarize failed-pass patterns by player."""
    failed_pass_df = get_failed_passes(df)
    if failed_pass_df.empty or "player" not in failed_pass_df.columns:
        return pd.DataFrame(
            columns=[
                "player",
                "total_failed_passes",
                "progressive_failed_passes",
                "failed_passes_to_final_third",
                "failed_box_entries",
                "average_length",
            ]
        )

    summary_df = (
        failed_pass_df.groupby("player", as_index=False)
        .agg(
            total_failed_passes=("event_type", "size"),
            progressive_failed_passes=("progressive", "sum"),
            failed_passes_to_final_third=("to_final_third", "sum"),
            failed_box_entries=("box_entry", "sum"),
            average_length=("pass_length", "mean"),
        )
        .sort_values(["total_failed_passes", "player"], ascending=[False, True])
        .reset_index(drop=True)
    )
    summary_df["average_length"] = summary_df["average_length"].round(2)
    return summary_df


def get_failed_pass_context(
    df: pd.DataFrame,
    max_seconds_after: int = 10,
) -> pd.DataFrame:
    """Return event context after each failed pass in the same possession."""
    failed_pass_df = get_failed_passes(df)
    if failed_pass_df.empty:
        return pd.DataFrame(
            columns=[
                "passer",
                "minute",
                "second",
                "x",
                "y",
                "end_x",
                "end_y",
                "pass_length",
                "progressive",
                "next_event_type",
                "next_player",
                "next_outcome",
                "seconds_after",
                "possession_id",
            ]
        )
    required_columns = {"match_id", "possession_id", "timestamp"}
    if not required_columns.issubset(df.columns):
        return pd.DataFrame(
            columns=[
                "passer",
                "minute",
                "second",
                "x",
                "y",
                "end_x",
                "end_y",
                "pass_length",
                "progressive",
                "next_event_type",
                "next_player",
                "next_outcome",
                "seconds_after",
                "possession_id",
            ]
        )

    ordered_df = df.sort_values(["match_id", "possession_id", "timestamp"]).copy()
    outcome_column = "inferred_outcome" if "inferred_outcome" in ordered_df.columns else "outcome"
    results: list[dict[str, object]] = []
    for _, possession_df in ordered_df.groupby(["match_id", "possession_id"], sort=False):
        possession_df = possession_df.sort_values("timestamp")
        possession_indices = possession_df.index.to_list()
        timestamps = pd.to_numeric(possession_df["timestamp"], errors="coerce").tolist()
        for pos, current_index in enumerate(possession_indices):
            if current_index not in failed_pass_df.index:
                continue
            current_row = failed_pass_df.loc[current_index]
            current_timestamp = timestamps[pos]
            if pd.isna(current_timestamp):
                continue
            for next_pos in range(pos + 1, len(possession_indices)):
                next_timestamp = timestamps[next_pos]
                if pd.isna(next_timestamp):
                    continue
                delta = next_timestamp - current_timestamp
                if delta <= 0:
                    continue
                if delta > max_seconds_after:
                    break
                next_row = possession_df.iloc[next_pos]
                results.append(
                    {
                        "passer": current_row.get("player"),
                        "minute": current_row.get("minute"),
                        "second": current_row.get("second"),
                        "x": current_row.get("x"),
                        "y": current_row.get("y"),
                        "end_x": current_row.get("end_x"),
                        "end_y": current_row.get("end_y"),
                        "pass_length": current_row.get("pass_length"),
                        "progressive": current_row.get("progressive"),
                        "next_event_type": next_row.get("event_type"),
                        "next_player": next_row.get("player"),
                        "next_outcome": next_row.get(outcome_column),
                        "seconds_after": int(delta),
                        "possession_id": current_row.get("possession_id"),
                    }
                )
    return pd.DataFrame(results)


def _pass_length_series(df: pd.DataFrame) -> pd.Series:
    """Compute euclidean pass length."""
    required_columns = {"x", "y", "end_x", "end_y"}
    if not required_columns.issubset(df.columns):
        return pd.Series(float("nan"), index=df.index)
    coords = df.loc[:, ["x", "y", "end_x", "end_y"]].apply(pd.to_numeric, errors="coerce")
    return ((coords["end_x"] - coords["x"]) ** 2 + (coords["end_y"] - coords["y"]) ** 2).pow(0.5)


def _progressive_mask(df: pd.DataFrame) -> pd.Series:
    """Return whether each failed pass is progressive."""
    if not {"x", "end_x"}.issubset(df.columns):
        return pd.Series(False, index=df.index)
    coords = df.loc[:, ["x", "end_x"]].apply(pd.to_numeric, errors="coerce")
    return (coords["end_x"] - coords["x"] >= PROGRESSIVE_DELTA_X).fillna(False)


def _box_entry_mask(df: pd.DataFrame) -> pd.Series:
    """Return whether each failed pass ends in the penalty area."""
    if not {"end_x", "end_y"}.issubset(df.columns):
        return pd.Series(False, index=df.index)
    coords = df.loc[:, ["end_x", "end_y"]].apply(pd.to_numeric, errors="coerce")
    return (
        (coords["end_x"] >= BOX_ENTRY_X_THRESHOLD)
        & coords["end_y"].between(BOX_ENTRY_Y_MIN, BOX_ENTRY_Y_MAX)
    ).fillna(False)


def _zone_label_series(series: pd.Series) -> pd.Series:
    """Return the field-third label for a coordinate series."""
    numeric_series = pd.to_numeric(series, errors="coerce")
    zone_series = pd.Series("Sin dato", index=numeric_series.index, dtype="object")
    zone_series.loc[numeric_series < 40] = "Tercio defensivo"
    zone_series.loc[(numeric_series >= 40) & (numeric_series < 80)] = "Tercio medio"
    zone_series.loc[numeric_series >= 80] = "Tercio ofensivo"
    return zone_series
