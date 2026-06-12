from __future__ import annotations

import pandas as pd

from src.services.data_service import get_freeze_frames, get_match_labels, get_normalized_events


def get_normalized_events_cached(
    default_path: str,
    normalized_path: str,
    lineups_path: str,
    uploaded_file_bytes: bytes | None,
    schema_version: str,
) -> pd.DataFrame:
    """Compatibility wrapper with pure repository semantics."""
    return get_normalized_events(
        default_path,
        normalized_path,
        lineups_path,
        uploaded_file_bytes,
        schema_version,
    )


def get_match_labels_cached(version: str) -> dict[str, str]:
    """Compatibility wrapper with pure repository semantics."""
    return get_match_labels(version)


def get_freeze_frames_cached(
    default_path: str,
    match_ids: tuple[str, ...] | None = None,
) -> pd.DataFrame:
    """Compatibility wrapper with pure repository semantics."""
    return get_freeze_frames(default_path, match_ids=match_ids)
