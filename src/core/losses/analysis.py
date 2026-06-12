from __future__ import annotations

import math

import pandas as pd

from src.core.rules.metric_filters import FINAL_THIRD_THRESHOLD, OWN_HALF_THRESHOLD
from src.core.metrics.basic import get_effective_outcome_series


DIRECT_LOSS_EVENTS = {"Dispossessed", "Miscontrol", "Error"}


def is_failed_outcome(outcome: object) -> bool:
    """Return whether an outcome should be considered a possession loss."""
    if outcome is None or (isinstance(outcome, float) and math.isnan(outcome)):
        return False
    normalized = str(outcome).strip().lower()
    if "off target" in normalized:
        return False
    return any(keyword in normalized for keyword in ("unsuccessful", "incomplete", "lost", "fail", "failed"))


def get_loss_events(df: pd.DataFrame) -> pd.DataFrame:
    """Return direct and action-based possession losses with a normalized loss type."""
    if df.empty or "event_type" not in df.columns:
        return pd.DataFrame(columns=list(df.columns) + ["loss_type"])

    event_type_series = df["event_type"].astype("string").fillna("")
    outcome_series = (
        get_effective_outcome_series(df).astype("string").fillna("")
        if {"outcome", "inferred_outcome"}.intersection(df.columns)
        else pd.Series("", index=df.index, dtype="object")
    )

    direct_loss_mask = event_type_series.isin(DIRECT_LOSS_EVENTS)
    failed_pass_mask = event_type_series.eq("Pass") & outcome_series.map(is_failed_outcome)
    failed_dribble_mask = event_type_series.eq("Dribble") & outcome_series.map(is_failed_outcome)

    loss_df = df[direct_loss_mask | failed_pass_mask | failed_dribble_mask].copy()
    if loss_df.empty:
        return pd.DataFrame(columns=list(df.columns) + ["loss_type"])

    loss_df["loss_type"] = loss_df["event_type"].astype("string")
    loss_df.loc[loss_df["event_type"] == "Pass", "loss_type"] = "Failed Pass"
    loss_df.loc[loss_df["event_type"] == "Dribble", "loss_type"] = "Failed Dribble"
    return loss_df


def calculate_loss_metrics(df: pd.DataFrame) -> dict[str, int]:
    """Calculate compact metrics for loss events."""
    loss_df = get_loss_events(df)
    if loss_df.empty:
        return {
            "total_losses": 0,
            "losses_own_half": 0,
            "losses_opponent_half": 0,
            "losses_final_third": 0,
            "failed_passes": 0,
            "failed_dribbles": 0,
            "miscontrols": 0,
            "dispossessed": 0,
            "errors": 0,
        }

    x_series = pd.to_numeric(loss_df["x"], errors="coerce") if "x" in loss_df.columns else pd.Series(float("nan"), index=loss_df.index)
    return {
        "total_losses": int(len(loss_df)),
        "losses_own_half": int((x_series < OWN_HALF_THRESHOLD).fillna(False).sum()),
        "losses_opponent_half": int((x_series >= OWN_HALF_THRESHOLD).fillna(False).sum()),
        "losses_final_third": int((x_series >= FINAL_THIRD_THRESHOLD).fillna(False).sum()),
        "failed_passes": int(loss_df["loss_type"].eq("Failed Pass").sum()),
        "failed_dribbles": int(loss_df["loss_type"].eq("Failed Dribble").sum()),
        "miscontrols": int(loss_df["loss_type"].eq("Miscontrol").sum()),
        "dispossessed": int(loss_df["loss_type"].eq("Dispossessed").sum()),
        "errors": int(loss_df["loss_type"].eq("Error").sum()),
    }


def get_dangerous_losses(df: pd.DataFrame) -> pd.DataFrame:
    """Return losses in own half or losses followed quickly by a rival action."""
    loss_df = get_loss_events(df)
    if loss_df.empty:
        return loss_df

    x_series = pd.to_numeric(loss_df["x"], errors="coerce") if "x" in loss_df.columns else pd.Series(float("nan"), index=loss_df.index)
    own_half_mask = (x_series < OWN_HALF_THRESHOLD).fillna(False)
    dangerous_mask = own_half_mask.copy()

    required_columns = {"match_id", "possession_id", "timestamp", "team"}
    if required_columns.issubset(df.columns):
        ordered_df = df.sort_values(["match_id", "possession_id", "timestamp"]).copy()
        quick_rival_action_indices: set[int] = set()
        for _, possession_df in ordered_df.groupby(["match_id", "possession_id"], sort=False):
            possession_df = possession_df.sort_values("timestamp")
            indices = possession_df.index.to_list()
            teams = possession_df["team"].tolist()
            timestamps = pd.to_numeric(possession_df["timestamp"], errors="coerce").tolist()
            for pos, row_index in enumerate(indices):
                if row_index not in loss_df.index:
                    continue
                current_team = teams[pos]
                current_timestamp = timestamps[pos]
                if pd.isna(current_timestamp):
                    continue
                for next_pos in range(pos + 1, len(indices)):
                    next_timestamp = timestamps[next_pos]
                    if pd.isna(next_timestamp):
                        continue
                    if next_timestamp - current_timestamp > 10:
                        break
                    if teams[next_pos] != current_team:
                        quick_rival_action_indices.add(row_index)
                        break
        dangerous_mask = dangerous_mask | loss_df.index.to_series().isin(quick_rival_action_indices)

    return loss_df[dangerous_mask].copy()


def summarize_losses_by_player(df: pd.DataFrame) -> pd.DataFrame:
    """Summarize loss events by player."""
    loss_df = get_loss_events(df)
    if loss_df.empty or "player" not in loss_df.columns:
        return pd.DataFrame(
            columns=[
                "player",
                "total_losses",
                "failed_passes",
                "failed_dribbles",
                "miscontrols",
                "dispossessed",
                "errors",
            ]
        )

    summary_df = (
        loss_df.assign(
            failed_pass=loss_df["loss_type"].eq("Failed Pass"),
            failed_dribble=loss_df["loss_type"].eq("Failed Dribble"),
            miscontrol=loss_df["loss_type"].eq("Miscontrol"),
            dispossessed=loss_df["loss_type"].eq("Dispossessed"),
            error=loss_df["loss_type"].eq("Error"),
        )
        .groupby("player", as_index=False)
        .agg(
            total_losses=("loss_type", "size"),
            failed_passes=("failed_pass", "sum"),
            failed_dribbles=("failed_dribble", "sum"),
            miscontrols=("miscontrol", "sum"),
            dispossessed=("dispossessed", "sum"),
            errors=("error", "sum"),
        )
        .sort_values(["total_losses", "player"], ascending=[False, True])
        .reset_index(drop=True)
    )
    return summary_df
