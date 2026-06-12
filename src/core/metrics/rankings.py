from __future__ import annotations

from numbers import Number

import pandas as pd

from src.core.metrics.events import calculate_specific_event_metrics


RANKABLE_METRICS_BY_EVENT = {
    "Pass": [
        "total_passes",
        "completed_passes",
        "completion_rate",
        "progressive_passes",
        "final_third_passes",
        "box_entries",
    ],
    "Carry": [
        "total_carries",
        "average_length",
        "progressive_carries",
        "final_third_carries",
        "box_entries",
    ],
    "Shot": [
        "total_shots",
        "goals",
        "saved",
        "off_target",
        "blocked",
        "average_distance_to_goal",
    ],
    "Pressure": [
        "total_pressures",
        "pressures_in_opponent_half",
        "pressures_in_final_third",
    ],
    "Duel": [
        "total_duels",
        "duels_won",
        "win_rate",
    ],
    "Dribble": [
        "total_dribbles",
        "successful_dribbles",
        "success_rate",
        "dribbles_in_final_third",
    ],
    "Ball Recovery": [
        "total_recoveries",
        "recoveries_in_own_half",
        "recoveries_in_opponent_half",
        "recoveries_in_final_third",
    ],
}

DEFAULT_RANKING_METRICS = {
    "Pass": "progressive_passes",
    "Carry": "progressive_carries",
    "Shot": "total_shots",
    "Pressure": "total_pressures",
    "Duel": "duels_won",
    "Dribble": "successful_dribbles",
    "Ball Recovery": "total_recoveries",
}


def get_rankable_metrics_for_event(event_type: str) -> list[str]:
    """Return metrics that make sense for ranking players in one event type."""
    return list(
        RANKABLE_METRICS_BY_EVENT.get(
            event_type,
            ["total_events", "successful_events", "success_rate"],
        )
    )


def build_player_ranking(
    df: pd.DataFrame,
    event_type: str,
    metric: str,
    min_events: int = 1,
    ascending: bool = False,
) -> pd.DataFrame:
    """Build a player ranking table for one event and metric."""
    if df.empty or "player" not in df.columns or "event_type" not in df.columns:
        return pd.DataFrame(columns=["rank", "player", "metric", "value", "total_events_for_event"])

    event_df = df[df["event_type"] == event_type].copy()
    if event_df.empty:
        return pd.DataFrame(columns=["rank", "player", "metric", "value", "total_events_for_event"])

    ranking_rows: list[dict[str, object]] = []
    for player_name, player_df in event_df.groupby("player", sort=True):
        total_events_for_event = int(len(player_df))
        if total_events_for_event < min_events:
            continue

        player_metrics = calculate_specific_event_metrics(player_df, event_type)
        value = player_metrics.get(metric)
        if not _is_numeric(value):
            continue

        ranking_rows.append(
            {
                "player": player_name,
                "metric": metric,
                "value": value,
                "total_events_for_event": total_events_for_event,
            }
        )

    if not ranking_rows:
        return pd.DataFrame(columns=["rank", "player", "metric", "value", "total_events_for_event"])

    ranking_df = pd.DataFrame(ranking_rows).sort_values(
        by=["value", "player"],
        ascending=[ascending, True],
    ).reset_index(drop=True)
    ranking_df.insert(0, "rank", ranking_df.index + 1)
    return ranking_df


def get_default_ranking_metric(event_type: str) -> str:
    """Return the default ranking metric for one event type."""
    return DEFAULT_RANKING_METRICS.get(event_type, "total_events")


def _is_numeric(value: object) -> bool:
    """Return whether a metric value can be ranked numerically."""
    return isinstance(value, Number) and not isinstance(value, bool)
