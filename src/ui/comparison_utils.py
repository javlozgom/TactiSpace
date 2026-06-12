from __future__ import annotations

import pandas as pd

from src.services.events_service import get_metric_display_name


def format_match_label(match_id: object, match_labels: dict[str, str]) -> str:
    """Return a readable label for one match identifier."""
    return match_labels.get(str(match_id), f"Partido {match_id}")


def ensure_distinct_labels(
    left_label: str,
    right_label: str,
    left_suffix: str = "A",
    right_suffix: str = "B",
) -> tuple[str, str]:
    """Ensure visible table labels are unique for Streamlit dataframe rendering."""
    if left_label != right_label:
        return left_label, right_label
    return f"{left_label} [{left_suffix}]", f"{right_label} [{right_suffix}]"


def format_metric_value(value: object) -> str:
    """Format metric values as display-safe strings."""
    if isinstance(value, float):
        if value.is_integer():
            return str(int(value))
        return f"{value:.2f}"
    return str(value)


def format_comparison_table(
    comparison_df: pd.DataFrame,
    left_label: str,
    right_label: str,
) -> pd.DataFrame:
    """Rename and format one comparison table for display."""
    formatted_df = comparison_df.rename(
        columns={
            "metric": "Métrica",
            "value_a": left_label,
            "value_b": right_label,
            "difference": "Diferencia",
            "relative_difference_pct": "Dif. relativa %",
        }
    )
    formatted_df["Métrica"] = formatted_df["Métrica"].map(get_metric_display_name)
    return formatted_df


def format_player_team_comparison_table(
    comparison_df: pd.DataFrame,
    left_label: str,
    right_label: str,
) -> pd.DataFrame:
    """Format the player-vs-team table using team-share readings for volume metrics."""
    formatted_df = comparison_df.copy()
    if formatted_df.empty:
        return formatted_df

    formatted_df["team_share_pct"] = formatted_df.apply(
        lambda row: calculate_team_share_pct(
            metric_key=str(row.get("metric", "")),
            player_value=row.get("value_a"),
            team_value=row.get("value_b"),
        ),
        axis=1,
    )
    formatted_df["reading"] = formatted_df.apply(
        lambda row: build_player_team_reading(
            metric_key=str(row.get("metric", "")),
            team_share_pct=row.get("team_share_pct"),
            relative_difference_pct=row.get("relative_difference_pct"),
        ),
        axis=1,
    )

    formatted_df = formatted_df.rename(
        columns={
            "metric": "Métrica",
            "value_a": left_label,
            "value_b": right_label,
            "team_share_pct": "% del equipo",
            "reading": "Lectura",
        }
    )
    formatted_df["Métrica"] = formatted_df["Métrica"].map(get_metric_display_name)
    formatted_df[left_label] = formatted_df[left_label].map(format_metric_value)
    formatted_df[right_label] = formatted_df[right_label].map(format_metric_value)
    formatted_df["% del equipo"] = formatted_df["% del equipo"].map(
        lambda value: "-" if pd.isna(value) else f"{float(value):.1f}%"
    )
    return formatted_df.loc[:, ["Métrica", left_label, right_label, "% del equipo", "Lectura"]]


def format_metrics_table(metrics_df: pd.DataFrame) -> pd.DataFrame:
    """Rename and format one metrics dataframe for display."""
    formatted_df = metrics_df.rename(columns={"metric": "Métrica", "value": "Valor"})
    if "Métrica" in formatted_df.columns:
        formatted_df["Métrica"] = formatted_df["Métrica"].map(get_metric_display_name)
    if "Valor" in formatted_df.columns:
        formatted_df["Valor"] = formatted_df["Valor"].map(format_metric_value)
    return formatted_df


def calculate_team_share_pct(metric_key: str, player_value: object, team_value: object) -> float | None:
    """Return player contribution as a percentage of the team for volume-like metrics."""
    if not is_team_share_metric(metric_key):
        return None
    if not isinstance(player_value, (int, float)) or not isinstance(team_value, (int, float)):
        return None
    if float(team_value) == 0:
        return None
    return round((float(player_value) / float(team_value)) * 100, 1)


def build_player_team_reading(
    metric_key: str,
    team_share_pct: object,
    relative_difference_pct: object,
) -> str:
    """Build the user-facing interpretation for one player-vs-team row."""
    if team_share_pct is not None and not pd.isna(team_share_pct):
        return f"Aporta el {float(team_share_pct):.1f}% del total del equipo"
    if isinstance(relative_difference_pct, (int, float)):
        sign = "+" if float(relative_difference_pct) > 0 else ""
        return f"{sign}{float(relative_difference_pct):.1f}% vs contexto equipo"
    return "-"


def is_team_share_metric(metric_key: str) -> bool:
    """Return whether a metric is better understood as contribution to team volume."""
    share_metric_keys = {
        "total_events",
        "successful_events",
        "total_passes",
        "completed_passes",
        "incomplete_passes",
        "progressive_passes",
        "final_third_passes",
        "box_entries",
        "pass_box_entries",
        "total_carries",
        "progressive_carries",
        "final_third_carries",
        "carry_box_entries",
        "carries_with_end_location",
        "total_shots",
        "goals",
        "saved",
        "off_target",
        "blocked",
        "total_pressures",
        "pressures_in_opponent_half",
        "pressures_in_final_third",
        "total_duels",
        "duels_won",
        "duels_lost",
        "total_dribbles",
        "successful_dribbles",
        "unsuccessful_dribbles",
        "dribbles_in_final_third",
        "total_recoveries",
        "recoveries_in_own_half",
        "recoveries_in_opponent_half",
        "recoveries_in_final_third",
    }
    return metric_key in share_metric_keys
