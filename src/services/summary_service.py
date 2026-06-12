from __future__ import annotations

import pandas as pd

from src.core.metrics.basic import calculate_basic_metrics, calculate_player_summary


def get_summary_metrics(filtered_df: pd.DataFrame) -> dict[str, float]:
    """Prepare the basic metrics used by summary-level views."""
    return calculate_basic_metrics(filtered_df)


def get_player_summary(filtered_df: pd.DataFrame) -> pd.DataFrame:
    """Prepare per-player summary data."""
    return calculate_player_summary(filtered_df)
