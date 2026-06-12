from __future__ import annotations

from numbers import Number

import pandas as pd

from src.core.metrics.events import calculate_specific_event_metrics


def compare_player_to_team(
    df: pd.DataFrame,
    player: str,
    event_type: str,
) -> dict[str, object]:
    """Compare one player's event metrics against the selected dataframe context."""
    if df.empty or not player or player == "Todos" or "player" not in df.columns:
        return {}

    player_df = df[df["player"] == player].copy()
    if player_df.empty:
        return {}

    team_df = _get_player_team_context(df, player_df)
    if team_df.empty:
        return {}

    player_metrics = calculate_specific_event_metrics(player_df, event_type)
    team_metrics = calculate_specific_event_metrics(team_df, event_type)
    return {
        "player": player,
        "team": team_df["team"].mode().iloc[0] if "team" in team_df.columns and not team_df["team"].mode().empty else None,
        "event_type": event_type,
        "player_metrics": player_metrics,
        "team_metrics": team_metrics,
        "differences": _build_differences(player_metrics, team_metrics, "player", "team"),
    }


def compare_two_players(
    df: pd.DataFrame,
    player_a: str,
    player_b: str,
    event_type: str,
) -> dict[str, object]:
    """Compare specific-event metrics between two players inside one context dataframe."""
    if df.empty or not player_a or not player_b or "player" not in df.columns:
        return {}

    player_a_df = df[df["player"] == player_a].copy()
    player_b_df = df[df["player"] == player_b].copy()
    if player_a_df.empty or player_b_df.empty:
        return {}

    player_a_metrics = calculate_specific_event_metrics(player_a_df, event_type)
    player_b_metrics = calculate_specific_event_metrics(player_b_df, event_type)
    return {
        "player_a": player_a,
        "player_b": player_b,
        "event_type": event_type,
        "player_a_metrics": player_a_metrics,
        "player_b_metrics": player_b_metrics,
        "differences": _build_differences(player_a_metrics, player_b_metrics, "a", "b"),
    }


def get_available_matches(df: pd.DataFrame) -> list:
    """Return sorted match identifiers available in the dataframe."""
    if df.empty or "match_id" not in df.columns:
        return []
    match_ids = df["match_id"].dropna().unique().tolist()
    try:
        return sorted(match_ids)
    except TypeError:
        return sorted(match_ids, key=lambda value: str(value))


def get_teams_for_match(df: pd.DataFrame, match_id) -> list[str]:
    """Return sorted team names available for one match."""
    if df.empty or "match_id" not in df.columns or "team" not in df.columns:
        return []
    match_df = df[df["match_id"] == match_id]
    if match_df.empty:
        return []
    return sorted(match_df["team"].dropna().astype(str).unique().tolist())


def get_players_for_match_team(
    df: pd.DataFrame,
    match_id,
    team: str,
) -> list[str]:
    """Return sorted player names for one match-team context."""
    if (
        df.empty
        or not team
        or "match_id" not in df.columns
        or "team" not in df.columns
        or "player" not in df.columns
    ):
        return []
    player_df = df[(df["match_id"] == match_id) & (df["team"] == team)]
    if player_df.empty:
        return []
    return sorted(player_df["player"].dropna().astype(str).unique().tolist())


def filter_player_context(
    df: pd.DataFrame,
    match_id,
    team: str,
    player: str,
) -> pd.DataFrame:
    """Return the dataframe filtered to one match, team and player context."""
    required_columns = {"match_id", "team", "player"}
    if df.empty or not required_columns.issubset(df.columns):
        return pd.DataFrame(columns=df.columns)
    return df[
        (df["match_id"] == match_id)
        & (df["team"] == team)
        & (df["player"] == player)
    ].copy()


def compare_player_contexts(
    df: pd.DataFrame,
    context_a: dict,
    context_b: dict,
    event_type: str,
) -> dict[str, object]:
    """Compare specific-event metrics between two arbitrary match-team-player contexts."""
    if df.empty:
        return {}

    df_a = filter_player_context(
        df,
        context_a.get("match_id"),
        context_a.get("team"),
        context_a.get("player"),
    )
    df_b = filter_player_context(
        df,
        context_b.get("match_id"),
        context_b.get("team"),
        context_b.get("player"),
    )
    if df_a.empty or df_b.empty:
        return {}

    metrics_a = calculate_specific_event_metrics(df_a, event_type)
    metrics_b = calculate_specific_event_metrics(df_b, event_type)
    return {
        "context_a": dict(context_a),
        "context_b": dict(context_b),
        "event_type": event_type,
        "metrics_a": metrics_a,
        "metrics_b": metrics_b,
        "differences": _build_differences(metrics_a, metrics_b, "a", "b"),
    }


def metrics_dict_to_dataframe(metrics: dict[str, object]) -> pd.DataFrame:
    """Convert a metrics dictionary into a simple two-column dataframe."""
    if not metrics:
        return pd.DataFrame(columns=["metric", "value"])

    rows = [
        {"metric": metric_key, "value": metric_value}
        for metric_key, metric_value in metrics.items()
        if metric_key != "interpretation"
    ]
    return pd.DataFrame(rows)


def comparison_dict_to_dataframe(comparison: dict[str, object]) -> pd.DataFrame:
    """Convert a comparison differences dict into a dataframe."""
    return _differences_to_dataframe(comparison.get("differences", {}) if comparison else {})


def advanced_comparison_to_dataframe(comparison: dict[str, object]) -> pd.DataFrame:
    """Convert an advanced comparison result into a dataframe."""
    return _differences_to_dataframe(comparison.get("differences", {}) if comparison else {})


def _differences_to_dataframe(differences: dict[str, object]) -> pd.DataFrame:
    """Convert a numeric differences dictionary into a normalized dataframe."""
    if not differences:
        return pd.DataFrame(
            columns=["metric", "value_a", "value_b", "difference", "relative_difference_pct"]
        )

    rows: list[dict[str, object]] = []
    for metric, values in differences.items():
        rows.append(
            {
                "metric": metric,
                "value_a": values.get("value_a", values.get("value_player")),
                "value_b": values.get("value_b", values.get("value_team")),
                "difference": values.get("difference"),
                "relative_difference_pct": values.get("relative_difference_pct"),
            }
        )
    return pd.DataFrame(rows)


def _build_differences(
    metrics_a: dict[str, object],
    metrics_b: dict[str, object],
    left_label: str,
    right_label: str,
) -> dict[str, dict[str, float | int | None]]:
    """Build numeric metric differences between two metric dictionaries."""
    differences: dict[str, dict[str, float | int | None]] = {}
    common_keys = set(metrics_a).intersection(metrics_b)
    for metric_key in common_keys:
        value_a = metrics_a.get(metric_key)
        value_b = metrics_b.get(metric_key)
        if not _is_numeric(value_a) or not _is_numeric(value_b):
            continue

        numeric_a = float(value_a)
        numeric_b = float(value_b)
        difference = numeric_a - numeric_b
        relative_difference_pct = None if numeric_b == 0 else round((difference / numeric_b) * 100, 2)
        differences[metric_key] = {
            f"value_{left_label}": value_a,
            f"value_{right_label}": value_b,
            "difference": round(difference, 2) if isinstance(difference, float) else difference,
            "relative_difference_pct": relative_difference_pct,
        }
    return differences


def _is_numeric(value: object) -> bool:
    """Return whether a value should be compared numerically."""
    return isinstance(value, Number) and not isinstance(value, bool)


def _get_player_team_context(df: pd.DataFrame, player_df: pd.DataFrame) -> pd.DataFrame:
    """Return the dataframe subset corresponding to the player's team context."""
    if "team" not in df.columns or "team" not in player_df.columns:
        return df.copy()

    team_mode = player_df["team"].dropna().mode()
    if team_mode.empty:
        return df.copy()

    player_team = team_mode.iloc[0]
    return df[df["team"] == player_team].copy()
