from __future__ import annotations

from collections.abc import Mapping

import pandas as pd


EVENT_TYPE_COLUMNS = ("event_type", "type", "type_name", "type.name")
FRAME_ID_COLUMNS = ("event_id", "id", "event_uuid")


def _empty_aligned_series(df: pd.DataFrame) -> pd.Series:
    return pd.Series(index=df.index, dtype="object")


def _extract_type_name(value: object) -> object:
    if isinstance(value, Mapping):
        return value.get("name")
    return value


def _is_valid_coordinate_pair(value: object) -> bool:
    if not isinstance(value, (list, tuple)) or len(value) < 2:
        return False

    x = pd.to_numeric(pd.Series([value[0]]), errors="coerce").iloc[0]
    y = pd.to_numeric(pd.Series([value[1]]), errors="coerce").iloc[0]
    return pd.notna(x) and pd.notna(y)


def _count_lineup_rows(df_or_dict: object) -> int:
    if isinstance(df_or_dict, pd.DataFrame):
        return len(df_or_dict)

    if isinstance(df_or_dict, Mapping):
        total = 0
        for value in df_or_dict.values():
            if isinstance(value, pd.DataFrame):
                total += len(value)
        return total

    return 0


def get_event_type_series(df: pd.DataFrame) -> pd.Series:
    """Return a best-effort event type series aligned to the dataframe index."""
    if df.empty:
        return _empty_aligned_series(df)

    for column in EVENT_TYPE_COLUMNS:
        if column not in df.columns:
            continue

        series = df[column]
        if column == "type":
            extracted = series.map(_extract_type_name).astype(object)
            return extracted.where(extracted.notna(), None)
        return series

    return _empty_aligned_series(df)


def count_events_by_type(df: pd.DataFrame, event_type: str) -> int:
    """Count events matching one event type name."""
    if df.empty:
        return 0

    event_types = get_event_type_series(df)
    if event_types.empty:
        return 0

    normalized = event_types.astype("string").str.strip()
    return int((normalized == event_type).sum())


def count_coordinate_events(df: pd.DataFrame) -> int:
    """Count rows with valid x/y coordinates or a valid [x, y] location pair."""
    if df.empty:
        return 0

    if {"x", "y"}.issubset(df.columns):
        x = pd.to_numeric(df["x"], errors="coerce")
        y = pd.to_numeric(df["y"], errors="coerce")
        return int((x.notna() & y.notna()).sum())

    if "location" in df.columns:
        return int(df["location"].map(_is_valid_coordinate_pair).sum())

    return 0


def count_unique_frames(df: pd.DataFrame) -> int:
    """Count freeze frames by unique event identifier."""
    if df.empty:
        return 0

    for column in FRAME_ID_COLUMNS:
        if column in df.columns:
            return int(df[column].nunique(dropna=True))

    return int(len(df))


def build_match_validation_row(
    match_id: int,
    events_norm: pd.DataFrame,
    lineups_norm: pd.DataFrame,
    frames_norm: pd.DataFrame,
    sb_events: pd.DataFrame,
    sb_lineups: object,
    sb_frames: pd.DataFrame,
) -> dict:
    """Build one validation row comparing parquet data against statsbombpy data."""
    events_parquet = int(len(events_norm))
    events_sb = int(len(sb_events))

    return {
        "match_id": match_id,
        "events_parquet": events_parquet,
        "events_sb": events_sb,
        "diff_events": events_parquet - events_sb,
        "passes_parquet": count_events_by_type(events_norm, "Pass"),
        "passes_sb": count_events_by_type(sb_events, "Pass"),
        "shots_parquet": count_events_by_type(events_norm, "Shot"),
        "shots_sb": count_events_by_type(sb_events, "Shot"),
        "lineups_parquet": int(len(lineups_norm)),
        "lineups_sb": _count_lineup_rows(sb_lineups),
        "freeze_frames_parquet": count_unique_frames(frames_norm),
        "freeze_frames_sb": count_unique_frames(sb_frames),
        "coordinate_events_parquet": count_coordinate_events(events_norm),
        "coordinate_events_sb": count_coordinate_events(sb_events),
        "status": "ok",
        "warning": "",
    }
