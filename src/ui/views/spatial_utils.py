from __future__ import annotations

import pandas as pd


def extract_event_id(event_row: pd.Series) -> str | None:
    """Extract one best-effort event identifier from an event row."""
    for column in ["event_id", "id"]:
        if column in event_row.index and pd.notna(event_row.get(column)):
            return str(event_row.get(column))
    return None


def coalesce_event_value(event_row: pd.Series, columns: list[str]) -> object:
    """Return the first non-null value from a list of possible columns."""
    for column in columns:
        if column in event_row.index and pd.notna(event_row.get(column)):
            return event_row.get(column)
    return "-"


def visible_freeze_frame_df(freeze_frame_df: pd.DataFrame) -> pd.DataFrame:
    """Return only visible freeze-frame rows when the visibility column exists."""
    if freeze_frame_df.empty or "visible" not in freeze_frame_df.columns:
        return freeze_frame_df
    return freeze_frame_df[freeze_frame_df["visible"].fillna(True).astype(bool)].copy()


def freeze_frame_has_actor(freeze_frame_df: pd.DataFrame) -> bool:
    """Return whether the freeze-frame contains an actor flag."""
    if freeze_frame_df.empty or "actor" not in freeze_frame_df.columns:
        return False
    working_df = visible_freeze_frame_df(freeze_frame_df)
    return bool(working_df["actor"].fillna(False).astype(bool).any())


def count_teammates(freeze_frame_df: pd.DataFrame) -> int:
    """Count visible teammates."""
    if freeze_frame_df.empty or "teammate" not in freeze_frame_df.columns:
        return 0
    working_df = visible_freeze_frame_df(freeze_frame_df)
    return int(working_df["teammate"].fillna(False).astype(bool).sum())


def count_opponents(freeze_frame_df: pd.DataFrame) -> int:
    """Count visible opponents."""
    if freeze_frame_df.empty or "teammate" not in freeze_frame_df.columns:
        return 0
    working_df = visible_freeze_frame_df(freeze_frame_df)
    teammate_mask = working_df["teammate"].fillna(False).astype(bool)
    return int((~teammate_mask).sum())


def count_visible_players(freeze_frame_df: pd.DataFrame) -> int:
    """Count visible players robustly across normalized and legacy freeze-frame data."""
    if freeze_frame_df.empty:
        return 0
    return int(len(visible_freeze_frame_df(freeze_frame_df)))


def assign_spatial_reference_ids(freeze_frame_df: pd.DataFrame) -> pd.DataFrame:
    """Assign local per-case ids to visible teammates and rivals."""
    if freeze_frame_df.empty:
        return freeze_frame_df.copy()

    working_df = freeze_frame_df.copy().reset_index(drop=True)
    working_df["spatial_reference_id"] = pd.Series(pd.NA, index=working_df.index, dtype="object")
    visible_mask = working_df.get("visible", True)
    if not isinstance(visible_mask, pd.Series):
        visible_mask = pd.Series([bool(visible_mask)] * len(working_df), index=working_df.index)
    visible_mask = visible_mask.fillna(True).astype(bool)

    teammate_mask = pd.Series(False, index=working_df.index)
    if "teammate" in working_df.columns:
        teammate_mask = working_df["teammate"].fillna(False).astype(bool)

    teammate_index = 1
    opponent_index = 1
    for row_index in working_df.index:
        if not bool(visible_mask.loc[row_index]):
            continue
        if bool(teammate_mask.loc[row_index]):
            working_df.at[row_index, "spatial_reference_id"] = f"T{teammate_index}"
            teammate_index += 1
        else:
            working_df.at[row_index, "spatial_reference_id"] = f"R{opponent_index}"
            opponent_index += 1

    return working_df
