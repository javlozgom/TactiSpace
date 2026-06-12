from __future__ import annotations

import pandas as pd
import streamlit as st

from src.core.metrics.basic import get_effective_outcome_series
from src.core.models.player_labels import apply_player_display_names, build_player_label_maps
from src.core.models.preprocessing import infer_duel_outcomes
from src.ui.components.page_header import render_section_header


def limit_dataframe_rows(df: pd.DataFrame, max_rows: int = 1000) -> tuple[pd.DataFrame, int, bool]:
    """Return one bounded dataframe preview plus metadata about truncation."""
    if df.empty:
        return df.copy(), 0, False

    total_rows = len(df)
    was_limited = total_rows > max_rows
    preview_df = df.head(max_rows).copy() if was_limited else df.copy()
    return preview_df, total_rows, was_limited


def render_limited_dataframe(
    df: pd.DataFrame,
    max_rows: int = 1000,
    caption_prefix: str = "Mostrando",
) -> None:
    """Render one dataframe with a bounded row preview."""
    preview_df, total_rows, was_limited = limit_dataframe_rows(df, max_rows=max_rows)
    st.dataframe(preview_df, width="stretch", hide_index=True)
    if was_limited:
        st.caption(f"{caption_prefix} {len(preview_df):,} de {total_rows:,} filas.")


def render_metric_table(df: pd.DataFrame, title: str | None = None, border: bool = True) -> None:
    """Render one metric dataframe with optional section title."""
    if title:
        render_section_header(title)
    if border:
        with st.container(border=True):
            render_limited_dataframe(df, max_rows=1000)
        return
    render_limited_dataframe(df, max_rows=1000)


def render_method_comparison_table(rows: list[dict[str, object]]) -> None:
    """Render one comparison table for recommendation methods."""
    if not rows:
        return
    comparison_df = pd.DataFrame(rows)
    render_metric_table(comparison_df, title="Comparativa de mÃ©todos")


def build_display_df(df: pd.DataFrame) -> pd.DataFrame:
    """Prepare one dataframe for user-facing display."""
    display_df = df.copy()
    duel_inference_columns = {"event_type", "outcome", "match_id", "team", "timestamp", "possession_id"}
    can_infer_duels = duel_inference_columns.issubset(display_df.columns)

    if "inferred_outcome" not in display_df.columns and can_infer_duels:
        if (display_df["event_type"] == "Duel").any():
            display_df = infer_duel_outcomes(display_df)

    if "inferred_outcome" in display_df.columns:
        display_df["outcome"] = get_effective_outcome_series(display_df)

    full_to_display, _ = build_player_label_maps(display_df)
    return apply_player_display_names(display_df, full_to_display)


def dataframe_preview(df: pd.DataFrame, label: str, max_rows: int = 1000) -> None:
    """Render one bounded dataframe preview."""
    preview_df = build_display_df(df)
    render_limited_dataframe(preview_df, max_rows=max_rows, caption_prefix=f"{label}: mostrando")
