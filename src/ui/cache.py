from __future__ import annotations

import pandas as pd
import streamlit as st

from src.repositories.cache_repository import (
    get_freeze_frames_cached as _get_freeze_frames,
    get_match_labels_cached as _get_match_labels,
    get_normalized_events_cached as _get_normalized_events,
)


@st.cache_data(show_spinner=False)
def get_normalized_events_cached(
    default_path: str,
    normalized_path: str,
    lineups_path: str,
    uploaded_file_bytes: bytes | None,
    schema_version: str,
) -> pd.DataFrame:
    """UI-level cached access to normalized events."""
    return _get_normalized_events(
        default_path,
        normalized_path,
        lineups_path,
        uploaded_file_bytes,
        schema_version,
    )


@st.cache_data(show_spinner=False)
def get_match_labels_cached(version: str) -> dict[str, str]:
    """UI-level cached access to readable match labels."""
    return _get_match_labels(version)


@st.cache_data(show_spinner=False)
def get_freeze_frames_cached(
    default_path: str,
    match_ids: tuple[str, ...] | None = None,
) -> pd.DataFrame:
    """UI-level cached access to freeze-frame data."""
    return _get_freeze_frames(default_path, match_ids=match_ids)
