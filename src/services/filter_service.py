from __future__ import annotations

from typing import Any

import pandas as pd


def get_filter_options(df: pd.DataFrame) -> dict[str, Any]:
    """Build options for the Streamlit sidebar filters."""
    matches = ["Todos", *sorted(df["match_id"].dropna().astype(str).unique().tolist())]
    teams = ["Todos", *sorted(df["team"].dropna().astype(str).unique().tolist())]
    players = ["Todos", *sorted(df["player"].dropna().astype(str).unique().tolist())]
    event_types = [
        "Todos",
        *sorted(df["event_type"].dropna().astype(str).unique().tolist()),
    ]

    min_minute = int(df["minute"].min()) if not df.empty else 0
    max_minute = int(df["minute"].max()) if not df.empty else 0

    return {
        "matches": matches,
        "teams": teams,
        "players": players,
        "event_types": event_types,
        "min_minute": min_minute,
        "max_minute": max_minute,
    }


def filter_events(
    df: pd.DataFrame,
    match_id: str = "Todos",
    team: str = "Todos",
    player: str = "Todos",
    event_type: str = "Todos",
    minute_range: tuple[int, int] | None = None,
) -> pd.DataFrame:
    """Filter events by team, player, event type and minute range."""
    filtered_df = df.copy()

    if match_id != "Todos":
        filtered_df = filtered_df[filtered_df["match_id"].astype(str) == str(match_id)]
    if team != "Todos":
        filtered_df = filtered_df[filtered_df["team"] == team]
    if player != "Todos":
        filtered_df = filtered_df[filtered_df["player"] == player]
    if event_type != "Todos":
        filtered_df = filtered_df[filtered_df["event_type"] == event_type]
    if minute_range is not None:
        start_minute, end_minute = minute_range
        filtered_df = filtered_df[
            filtered_df["minute"].between(start_minute, end_minute, inclusive="both")
        ]

    return filtered_df.copy()
