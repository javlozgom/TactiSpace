from __future__ import annotations

import pandas as pd


SUCCESS_OUTCOMES = {"Successful", "Goal", "Won"}


def get_effective_outcome_series(df: pd.DataFrame) -> pd.Series:
    """Return the outcome series used for analysis, preferring inferred values."""
    if "inferred_outcome" in df.columns:
        return df["inferred_outcome"]
    return df["outcome"]


def calculate_basic_metrics(df: pd.DataFrame) -> dict[str, float]:
    """Calculate basic counts and success rate for a set of events."""
    total_events = int(len(df))
    effective_outcomes = get_effective_outcome_series(df)
    successful_events = int(effective_outcomes.isin(SUCCESS_OUTCOMES).sum()) if not df.empty else 0
    success_rate = (successful_events / total_events * 100) if total_events else 0.0

    return {
        "total_events": total_events,
        "total_passes": int((df["event_type"] == "Pass").sum()) if not df.empty else 0,
        "total_carries": int((df["event_type"] == "Carry").sum()) if not df.empty else 0,
        "total_shots": int((df["event_type"] == "Shot").sum()) if not df.empty else 0,
        "total_dribbles": int((df["event_type"] == "Dribble").sum()) if not df.empty else 0,
        "total_duels": int((df["event_type"] == "Duel").sum()) if not df.empty else 0,
        "total_recoveries": int((df["event_type"] == "Ball Recovery").sum()) if not df.empty else 0,
        "total_turnovers": int(
            df["event_type"].isin(["Dispossessed", "Miscontrol"]).sum()
        )
        if not df.empty
        else 0,
        "successful_events": successful_events,
        "success_rate": success_rate,
    }


def calculate_player_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Return a player and event type summary table."""
    if df.empty:
        return pd.DataFrame(
            columns=["player", "event_type", "event_count", "successful_actions", "success_pct"]
        )

    summary_df = (
        df.assign(is_success=get_effective_outcome_series(df).isin(SUCCESS_OUTCOMES))
        .groupby(["player", "event_type"], as_index=False, observed=True)
        .agg(
            event_count=("event_type", "size"),
            successful_actions=("is_success", "sum"),
        )
    )
    summary_df["success_pct"] = (
        summary_df["successful_actions"] / summary_df["event_count"] * 100
    ).round(2)

    return summary_df.sort_values(
        by=["event_count", "player", "event_type"],
        ascending=[False, True, True],
    ).reset_index(drop=True)
