from __future__ import annotations

import io
from pathlib import Path

import pandas as pd

from src.core.models.lineups import enrich_events_with_lineups, is_normalized_lineups_df
from src.core.models.preprocessing import add_derived_event_columns, normalize_events
from src.core.spatial.freeze_frame import normalize_freeze_frame_df
from src.repositories.data_repository import (
    is_normalized_events_df,
    load_events,
    load_freeze_frames,
    load_lineups,
    load_match_labels,
)


def get_normalized_events(
    default_path: str,
    normalized_path: str,
    lineups_path: str,
    uploaded_file_bytes: bytes | None,
    schema_version: str,
) -> pd.DataFrame:
    """Load and normalize event data from the active source."""
    _ = schema_version

    if uploaded_file_bytes is not None:
        raw_df = load_events(uploaded_file=io.BytesIO(uploaded_file_bytes))
        return normalize_events(raw_df)

    normalized_file = Path(normalized_path)
    if normalized_file.exists():
        normalized_df = load_events(default_path=normalized_file)
        if is_normalized_events_df(normalized_df):
            return add_derived_event_columns(normalized_df)

    raw_df = load_events(default_path=default_path)
    if is_normalized_events_df(raw_df):
        return add_derived_event_columns(raw_df)

    normalized_df = normalize_events(raw_df)
    lineups_file = Path(lineups_path)
    if lineups_file.exists():
        lineups_df = load_lineups(lineups_file)
        if is_normalized_lineups_df(lineups_df):
            normalized_df = enrich_events_with_lineups(normalized_df, lineups_df)

    return add_derived_event_columns(normalized_df)


def get_match_labels(version: str) -> dict[str, str]:
    """Load readable labels for match selection."""
    _ = version
    return load_match_labels()


def get_freeze_frames(
    default_path: str,
    match_ids: tuple[str, ...] | None = None,
) -> pd.DataFrame:
    """Load and normalize freeze-frame data for the requested match scope."""
    raw_ff_df = load_freeze_frames(default_path, match_ids=match_ids)
    return normalize_freeze_frame_df(raw_ff_df)
