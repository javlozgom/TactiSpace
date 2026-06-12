from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from src.config.constants import (
    DEFAULT_THREE_SIXTY_NORMALIZED_PATH,
    DEFAULT_THREE_SIXTY_RAW_PATH,
    RAW_THREE_SIXTY_DIR,
)

DEFAULT_RAW_FREEZE_FRAME_DIR = RAW_THREE_SIXTY_DIR

EXPECTED_FREEZE_FRAME_COLUMNS = [
    "event_id",
    "match_id",
    "teammate",
    "actor",
    "keeper",
    "player",
    "player_id",
    "team",
    "x",
    "y",
    "visible",
    "raw_freeze_frame",
]


def is_normalized_freeze_frame_df(df: pd.DataFrame) -> bool:
    """Return whether one dataframe already matches the normalized freeze-frame schema."""
    return not df.empty and set(EXPECTED_FREEZE_FRAME_COLUMNS).issubset(df.columns)


def detect_freeze_frame_columns(df: pd.DataFrame) -> dict[str, str | bool | None]:
    """Detect freeze-frame related columns in one dataframe."""
    columns = set(df.columns)
    freeze_frame_column = next(
        (column for column in ["freeze_frame", "freeze_frames", "three_sixty", "360_freeze_frame"] if column in columns),
        None,
    )
    visible_area_column = next(
        (column for column in ["visible_area", "visibility_area"] if column in columns),
        None,
    )
    event_id_column = next(
        (column for column in ["event_id", "event_uuid", "id", "freeze_frame_id"] if column in columns),
        None,
    )
    return {
        "has_freeze_frame": freeze_frame_column is not None or visible_area_column is not None,
        "freeze_frame_column": freeze_frame_column,
        "visible_area_column": visible_area_column,
        "event_id_column": event_id_column,
    }


def load_freeze_frames(
    default_path: str | Path = DEFAULT_THREE_SIXTY_NORMALIZED_PATH,
    match_ids: tuple[str, ...] | None = None,
) -> pd.DataFrame:
    """Load freeze-frame data from processed files or raw StatsBomb 360 JSON files."""
    file_path = Path(default_path)
    normalized_match_ids = _normalize_match_ids(match_ids)
    if file_path.exists():
        try:
            if file_path.is_dir():
                return _load_freeze_frames_from_directory(file_path, normalized_match_ids)
            if file_path.suffix.lower() == ".csv":
                loaded_df = pd.read_csv(file_path)
                return _filter_freeze_frames_by_match_ids(loaded_df, normalized_match_ids)
            if file_path.suffix.lower() == ".parquet":
                loaded_df = pd.read_parquet(file_path)
                return _filter_freeze_frames_by_match_ids(loaded_df, normalized_match_ids)
            if file_path.suffix.lower() == ".json":
                return _load_freeze_frames_from_json_file(file_path)
        except Exception:
            return pd.DataFrame()

    raw_dir_candidates = []
    if file_path.suffix:
        raw_dir_candidates.append(file_path.with_suffix(""))
    raw_processed_path = Path(DEFAULT_THREE_SIXTY_RAW_PATH)
    if raw_processed_path != file_path and raw_processed_path.exists():
        try:
            if raw_processed_path.suffix.lower() == ".csv":
                loaded_df = pd.read_csv(raw_processed_path)
                return _filter_freeze_frames_by_match_ids(loaded_df, normalized_match_ids)
            if raw_processed_path.suffix.lower() == ".parquet":
                loaded_df = pd.read_parquet(raw_processed_path)
                return _filter_freeze_frames_by_match_ids(loaded_df, normalized_match_ids)
        except Exception:
            pass
    raw_dir_candidates.append(DEFAULT_RAW_FREEZE_FRAME_DIR)
    raw_dir_candidates.append(file_path.parent.parent / "raw" / "statsbomb" / "euro_2024" / "three_sixty")

    for raw_dir in raw_dir_candidates:
        if raw_dir.exists() and raw_dir.is_dir():
            try:
                return _load_freeze_frames_from_directory(raw_dir, normalized_match_ids)
            except Exception:
                return pd.DataFrame()
    return pd.DataFrame()


def normalize_freeze_frame_df(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize freeze-frame data to one row per player in one common schema."""
    if df.empty:
        return pd.DataFrame(columns=EXPECTED_FREEZE_FRAME_COLUMNS)
    if is_normalized_freeze_frame_df(df):
        return _finalize_freeze_frame_df(df)

    detected = detect_freeze_frame_columns(df)
    freeze_frame_column = detected["freeze_frame_column"]
    if freeze_frame_column:
        expanded_rows = _expand_nested_freeze_frames(df, str(freeze_frame_column))
        if expanded_rows:
            normalized_df = pd.DataFrame(expanded_rows)
            return _finalize_freeze_frame_df(normalized_df)

    normalized_df = _normalize_flat_freeze_frame_df(df)
    return _finalize_freeze_frame_df(normalized_df)


def get_freeze_frame_for_event(
    event_row: pd.Series,
    freeze_frames_df: pd.DataFrame,
) -> pd.DataFrame:
    """Return the normalized freeze-frame associated with one event."""
    direct_freeze_frame = event_row.get("freeze_frame")
    if isinstance(direct_freeze_frame, list):
        expanded_rows = _expand_freeze_frame_list(
            direct_freeze_frame,
            event_id=_extract_event_identifier(event_row),
            base_event=event_row.to_dict(),
        )
        return _finalize_freeze_frame_df(pd.DataFrame(expanded_rows))

    if freeze_frames_df.empty:
        return pd.DataFrame(columns=EXPECTED_FREEZE_FRAME_COLUMNS)

    event_identifiers = [
        event_row.get(column)
        for column in ["event_id", "event_uuid", "id", "freeze_frame_id"]
        if column in event_row.index
    ]
    event_identifiers = [identifier for identifier in event_identifiers if pd.notna(identifier)]
    if not event_identifiers:
        return pd.DataFrame(columns=EXPECTED_FREEZE_FRAME_COLUMNS)

    working_df = freeze_frames_df if is_normalized_freeze_frame_df(freeze_frames_df) else normalize_freeze_frame_df(freeze_frames_df)
    if working_df.empty or "event_id" not in working_df.columns:
        return pd.DataFrame(columns=EXPECTED_FREEZE_FRAME_COLUMNS)

    for identifier in event_identifiers:
        match_df = working_df[working_df["event_id"].astype(str) == str(identifier)].copy()
        if not match_df.empty:
            return match_df.reset_index(drop=True)
    return pd.DataFrame(columns=EXPECTED_FREEZE_FRAME_COLUMNS)


def split_freeze_frame_players(freeze_frame_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split normalized freeze-frame players into teammates and opponents."""
    if freeze_frame_df.empty or "teammate" not in freeze_frame_df.columns:
        empty_df = pd.DataFrame(columns=EXPECTED_FREEZE_FRAME_COLUMNS)
        return empty_df.copy(), empty_df.copy()

    teammate_mask = freeze_frame_df["teammate"].fillna(False).astype(bool)
    teammates_df = freeze_frame_df[teammate_mask].copy().reset_index(drop=True)
    opponents_df = freeze_frame_df[~teammate_mask].copy().reset_index(drop=True)
    return teammates_df, opponents_df


def has_freeze_frame_data(freeze_frames_df: pd.DataFrame) -> bool:
    """Return whether the provided dataframe contains useful freeze-frame data."""
    normalized_df = freeze_frames_df if is_normalized_freeze_frame_df(freeze_frames_df) else normalize_freeze_frame_df(freeze_frames_df)
    return not normalized_df.empty and {"x", "y"}.issubset(normalized_df.columns)


def _expand_nested_freeze_frames(df: pd.DataFrame, freeze_frame_column: str) -> list[dict[str, Any]]:
    """Expand nested freeze-frame lists into one row per player."""
    rows: list[dict[str, Any]] = []
    for _, event_row in df.iterrows():
        freeze_frame_value = event_row.get(freeze_frame_column)
        if not isinstance(freeze_frame_value, list):
            continue
        rows.extend(
            _expand_freeze_frame_list(
                freeze_frame_value,
                event_id=_extract_event_identifier(event_row),
                base_event=event_row.to_dict(),
            )
        )
    return rows


def _load_freeze_frames_from_directory(directory: Path, match_ids: tuple[str, ...] | None = None) -> pd.DataFrame:
    """Load and combine raw freeze-frame JSON files from one directory."""
    if match_ids:
        json_files = [directory / f"{match_id}.json" for match_id in match_ids]
        json_files = [json_file for json_file in json_files if json_file.exists()]
    else:
        json_files = sorted(directory.glob("*.json"))
    if not json_files:
        return pd.DataFrame()

    frames: list[pd.DataFrame] = []
    for json_file in json_files:
        loaded_df = _load_freeze_frames_from_json_file(json_file)
        if not loaded_df.empty:
            frames.append(loaded_df)

    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def _load_freeze_frames_from_json_file(file_path: Path) -> pd.DataFrame:
    """Load one raw StatsBomb 360 JSON file into a dataframe."""
    try:
        loaded_df = pd.read_json(file_path)
    except ValueError:
        return pd.DataFrame()
    if loaded_df.empty:
        return pd.DataFrame()
    loaded_df = loaded_df.copy()
    loaded_df["match_id"] = file_path.stem
    return loaded_df


def _normalize_match_ids(match_ids: tuple[str, ...] | None) -> tuple[str, ...] | None:
    """Return one clean tuple of match ids for file filtering."""
    if not match_ids:
        return None
    normalized_ids = []
    for match_id in match_ids:
        if match_id is None or pd.isna(match_id):
            continue
        match_id_str = str(match_id).strip()
        if not match_id_str or match_id_str.lower() == "todos":
            continue
        normalized_ids.append(match_id_str)
    if not normalized_ids:
        return None
    return tuple(dict.fromkeys(normalized_ids))


def _filter_freeze_frames_by_match_ids(
    df: pd.DataFrame,
    match_ids: tuple[str, ...] | None,
) -> pd.DataFrame:
    """Filter one processed freeze-frame dataframe by match ids when possible."""
    if df.empty or not match_ids or "match_id" not in df.columns:
        return df
    return df[df["match_id"].astype(str).isin(match_ids)].reset_index(drop=True)


def _expand_freeze_frame_list(
    freeze_frame_list: list[Any],
    event_id: object,
    base_event: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Expand one freeze-frame player list into normalized rows."""
    base_event = base_event or {}
    rows: list[dict[str, Any]] = []
    for player_row in freeze_frame_list:
        if not isinstance(player_row, dict):
            continue

        location = player_row.get("location")
        x_value, y_value = _parse_location(location)
        rows.append(
            {
                "event_id": event_id,
                "match_id": base_event.get("match_id"),
                "teammate": _safe_bool(player_row.get("teammate")),
                "actor": _safe_bool(player_row.get("actor")),
                "keeper": _safe_bool(player_row.get("keeper")),
                "player": _extract_player_name(player_row),
                "player_id": _extract_player_id(player_row),
                "team": _extract_team_name(player_row) or base_event.get("team"),
                "x": x_value,
                "y": y_value,
                "visible": _safe_bool(player_row.get("visible", True)),
                "raw_freeze_frame": player_row,
            }
        )
    return rows


def _normalize_flat_freeze_frame_df(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize one flat freeze-frame dataframe."""
    if df.empty:
        return pd.DataFrame(columns=EXPECTED_FREEZE_FRAME_COLUMNS)

    working_df = df.copy()
    if "location" in working_df.columns and {"x", "y"}.difference(working_df.columns):
        coords = working_df["location"].apply(_parse_location).tolist()
        working_df["x"] = [coord[0] for coord in coords]
        working_df["y"] = [coord[1] for coord in coords]

    normalized_df = pd.DataFrame(
        {
            "event_id": _coalesce_columns(working_df, ["event_id", "event_uuid", "id", "freeze_frame_id"]),
            "match_id": _coalesce_columns(working_df, ["match_id"]),
            "teammate": _coalesce_columns(working_df, ["teammate"], default=False),
            "actor": _coalesce_columns(working_df, ["actor"], default=False),
            "keeper": _coalesce_columns(working_df, ["keeper"], default=False),
            "player": _coalesce_columns(working_df, ["player", "player_name"]),
            "player_id": _coalesce_columns(working_df, ["player_id"]),
            "team": _coalesce_columns(working_df, ["team", "team_name"]),
            "x": _coalesce_columns(working_df, ["x"]),
            "y": _coalesce_columns(working_df, ["y"]),
            "visible": _coalesce_columns(working_df, ["visible"], default=True),
            "raw_freeze_frame": [None] * len(working_df),
        }
    )
    return normalized_df


def _finalize_freeze_frame_df(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure one normalized freeze-frame dataframe has the expected schema."""
    if df.empty:
        return pd.DataFrame(columns=EXPECTED_FREEZE_FRAME_COLUMNS)

    working_df = df.copy()
    for column in EXPECTED_FREEZE_FRAME_COLUMNS:
        if column not in working_df.columns:
            working_df[column] = None

    for bool_column in ["teammate", "actor", "keeper", "visible"]:
        working_df[bool_column] = working_df[bool_column].map(_safe_bool)

    for coord_column in ["x", "y"]:
        working_df[coord_column] = pd.to_numeric(working_df[coord_column], errors="coerce")
    if "match_id" in working_df.columns:
        working_df["match_id"] = working_df["match_id"].astype(str)

    return working_df.loc[:, EXPECTED_FREEZE_FRAME_COLUMNS].dropna(subset=["x", "y"], how="all").reset_index(drop=True)


def _extract_event_identifier(event_row: pd.Series) -> object:
    """Extract one best-effort event identifier from an event row."""
    for column in ["event_id", "event_uuid", "id", "freeze_frame_id"]:
        if column in event_row.index and pd.notna(event_row.get(column)):
            return event_row.get(column)
    return None


def _coalesce_columns(df: pd.DataFrame, columns: list[str], default: object = None) -> pd.Series:
    """Return the first available column from a list, or a default series."""
    for column in columns:
        if column in df.columns:
            return df[column]
    return pd.Series([default] * len(df), index=df.index)


def _parse_location(value: object) -> tuple[float | None, float | None]:
    """Parse one location structure into x and y coordinates."""
    if isinstance(value, (list, tuple)) and len(value) >= 2:
        return _to_float(value[0]), _to_float(value[1])
    if isinstance(value, dict):
        return _to_float(value.get("x")), _to_float(value.get("y"))
    return None, None


def _extract_player_name(player_row: dict[str, Any]) -> object:
    """Extract one player name from one freeze-frame player row."""
    player_value = player_row.get("player")
    if isinstance(player_value, dict):
        return player_value.get("name")
    return player_row.get("player_name", player_value)


def _extract_player_id(player_row: dict[str, Any]) -> object:
    """Extract one player id from one freeze-frame player row."""
    player_value = player_row.get("player")
    if isinstance(player_value, dict):
        return player_value.get("id")
    return player_row.get("player_id")


def _extract_team_name(player_row: dict[str, Any]) -> object:
    """Extract one team name from one freeze-frame player row."""
    team_value = player_row.get("team")
    if isinstance(team_value, dict):
        return team_value.get("name")
    return player_row.get("team_name", team_value)


def _safe_bool(value: object) -> bool:
    """Convert one value to bool without crashing on null-like values."""
    if pd.isna(value):
        return False
    return bool(value)


def _to_float(value: object) -> float | None:
    """Convert one scalar to float when possible."""
    if value is None or pd.isna(value):
        return None
    try:
        return float(value)
    except Exception:
        return None
