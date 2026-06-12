from __future__ import annotations

import pandas as pd


def get_spatial_match_ids(
    selected_match: object,
    filtered_df: pd.DataFrame,
) -> tuple[str, ...] | None:
    """Return the smallest match-id scope needed for spatial analysis loading."""
    if selected_match not in {None, "", "Todos"}:
        return (str(selected_match),)

    if filtered_df.empty or "match_id" not in filtered_df.columns:
        return None

    match_ids = []
    for match_id in filtered_df["match_id"].dropna().astype(str).unique().tolist():
        match_id_str = str(match_id).strip()
        if match_id_str:
            match_ids.append(match_id_str)

    return tuple(match_ids) if match_ids else None


def count_visible_spatial_events(
    filtered_df: pd.DataFrame,
    freeze_frames_df: pd.DataFrame | None,
) -> int:
    """Count unique events with freeze-frame visible in the current filtered context."""
    if filtered_df.empty:
        return 0

    if (
        freeze_frames_df is not None
        and not freeze_frames_df.empty
        and "event_id" in filtered_df.columns
        and "event_id" in freeze_frames_df.columns
    ):
        visible_event_ids = set(filtered_df["event_id"].dropna().astype(str).tolist())
        if not visible_event_ids:
            return 0
        return int(
            freeze_frames_df["event_id"]
            .dropna()
            .astype(str)
            .loc[lambda series: series.isin(visible_event_ids)]
            .nunique()
        )

    candidate_columns = [
        "has_freeze_frame",
        "freeze_frame_available",
        "has_360",
        "has_three_sixty",
        "visible_area_available",
        "three_sixty_event_id",
    ]
    for column in candidate_columns:
        if column not in filtered_df.columns:
            continue
        if column == "three_sixty_event_id":
            return int(filtered_df[column].notna().sum())
        try:
            return int(filtered_df[column].fillna(False).astype(bool).sum())
        except Exception:
            continue
    return 0
