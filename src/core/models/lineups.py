from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from src.config.constants import DEFAULT_LINEUPS_RAW_PATH, RAW_LINEUPS_DIR


LINEUPS_REQUIRED_COLUMNS = [
    "match_id",
    "team",
    "player_id",
    "player",
    "player_nickname",
    "jersey_number",
    "position",
    "position_group",
    "raw_position",
]

POSITION_GROUP_PATTERNS = {
    "Portero": ["goalkeeper", "goal keeper", "gk", "portero"],
    "Defensa": [
        "center back",
        "centre back",
        "left back",
        "right back",
        "fullback",
        "full back",
        "wing back",
        "defender",
        "defensa",
        "df",
    ],
    "Mediocentro": [
        "defensive midfield",
        "central midfield",
        "attacking midfield",
        "midfielder",
        "midfield",
        "centrocampista",
        "mediocentro",
        "mf",
    ],
    "Atacante": [
        "forward",
        "striker",
        "winger",
        "left wing",
        "right wing",
        "center forward",
        "centre forward",
        "delantero",
        "extremo",
        "atacante",
        "fw",
    ],
}


def is_normalized_lineups_df(df: pd.DataFrame) -> bool:
    """Return whether one dataframe already matches the normalized lineup schema."""
    required_columns = {"match_id", "team", "player", "position_group"}
    return not df.empty and required_columns.issubset(df.columns)


def normalize_lineups_df(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize one lineup dataframe to the common tabular schema."""
    if df.empty:
        return pd.DataFrame(columns=LINEUPS_REQUIRED_COLUMNS)

    if "lineup" in df.columns:
        normalized_df = _expand_statsbomb_lineups(df)
    else:
        normalized_df = _normalize_flat_lineups(df)

    for column in LINEUPS_REQUIRED_COLUMNS:
        if column not in normalized_df.columns:
            normalized_df[column] = None

    normalized_df["match_id"] = normalized_df["match_id"].astype(str)
    normalized_df["team"] = normalized_df["team"].map(_clean_text)
    normalized_df["player"] = normalized_df["player"].map(_clean_text)
    normalized_df["player_nickname"] = normalized_df["player_nickname"].map(_clean_text)
    normalized_df["position"] = normalized_df["position"].map(_clean_text)
    normalized_df["raw_position"] = normalized_df["raw_position"].map(_clean_text)
    normalized_df["position_group"] = normalized_df.apply(
        lambda row: _map_position_group(row.get("position_group")) or _map_position_group(row.get("position")) or _map_position_group(row.get("raw_position")),
        axis=1,
    )
    normalized_df["player_id"] = pd.to_numeric(normalized_df["player_id"], errors="coerce").astype("Int64")
    normalized_df["jersey_number"] = pd.to_numeric(normalized_df["jersey_number"], errors="coerce").astype("Int64")

    normalized_df = normalized_df.loc[:, LINEUPS_REQUIRED_COLUMNS]
    normalized_df = normalized_df.drop_duplicates(subset=["match_id", "team", "player_id", "player"], keep="first")
    return normalized_df.reset_index(drop=True)


def load_lineups(default_path: str | Path = DEFAULT_LINEUPS_RAW_PATH) -> pd.DataFrame:
    """Load lineups from a processed parquet/csv file when available."""
    path = Path(default_path)
    if not path.exists():
        return pd.DataFrame(columns=LINEUPS_REQUIRED_COLUMNS)

    try:
        if path.suffix.lower() == ".parquet":
            loaded_df = pd.read_parquet(path)
        else:
            loaded_df = pd.read_csv(path)
    except Exception:
        return pd.DataFrame(columns=LINEUPS_REQUIRED_COLUMNS)

    if is_normalized_lineups_df(loaded_df):
        return normalize_lineups_df(loaded_df)
    return normalize_lineups_df(loaded_df)


def load_lineups_from_json_dir(raw_dir: str | Path = RAW_LINEUPS_DIR) -> pd.DataFrame:
    """Load raw StatsBomb lineup JSON files and normalize them."""
    directory = Path(raw_dir)
    if not directory.exists() or not directory.is_dir():
        return pd.DataFrame(columns=LINEUPS_REQUIRED_COLUMNS)

    frames: list[pd.DataFrame] = []
    for lineup_file in sorted(directory.glob("*.json")):
        try:
            loaded_df = pd.read_json(lineup_file)
        except Exception:
            continue
        if loaded_df.empty:
            continue
        loaded_df = loaded_df.copy()
        loaded_df["match_id"] = lineup_file.stem
        frames.append(loaded_df)

    if not frames:
        return pd.DataFrame(columns=LINEUPS_REQUIRED_COLUMNS)
    return normalize_lineups_df(pd.concat(frames, ignore_index=True))


def enrich_events_with_lineups(events_df: pd.DataFrame, lineups_df: pd.DataFrame) -> pd.DataFrame:
    """Merge lightweight lineup metadata into the events dataframe without duplicating rows."""
    if events_df.empty or lineups_df.empty:
        return events_df.copy()

    enriched_df = events_df.copy()
    normalized_lineups_df = normalize_lineups_df(lineups_df)
    if normalized_lineups_df.empty or "match_id" not in enriched_df.columns:
        return enriched_df

    normalized_lineups_df["match_id"] = normalized_lineups_df["match_id"].astype(str)
    enriched_df["match_id"] = enriched_df["match_id"].astype(str)

    if "team" in enriched_df.columns and "team" in normalized_lineups_df.columns:
        team_player_lookup = (
            normalized_lineups_df
            .dropna(subset=["player"])
            .drop_duplicates(subset=["match_id", "team", "player"])
            .loc[:, ["match_id", "team", "player", "player_id", "player_nickname", "position", "position_group"]]
        )
        enriched_df = _merge_lineup_metadata(enriched_df, team_player_lookup, on=["match_id", "team", "player"])
    else:
        player_lookup = (
            normalized_lineups_df
            .dropna(subset=["player"])
            .drop_duplicates(subset=["match_id", "player"])
            .loc[:, ["match_id", "player", "player_id", "player_nickname", "position", "position_group"]]
        )
        enriched_df = _merge_lineup_metadata(enriched_df, player_lookup, on=["match_id", "player"])

    if "player_id" in enriched_df.columns and enriched_df["player_id"].notna().any():
        player_id_lookup = (
            normalized_lineups_df
            .dropna(subset=["player_id"])
            .drop_duplicates(subset=["match_id", "player_id"])
            .loc[:, ["match_id", "player_id", "player_nickname", "position", "position_group", "player"]]
        )
        enriched_df = _merge_lineup_metadata(enriched_df, player_id_lookup, on=["match_id", "player_id"])

    return enriched_df


def _expand_statsbomb_lineups(df: pd.DataFrame) -> pd.DataFrame:
    """Expand raw StatsBomb lineup rows to one row per player."""
    rows: list[dict[str, Any]] = []
    for _, team_row in df.iterrows():
        match_id = team_row.get("match_id")
        team_name = team_row.get("team_name") or team_row.get("team")
        for player_row in team_row.get("lineup", []) or []:
            if not isinstance(player_row, dict):
                continue
            raw_position = _extract_primary_position(player_row.get("positions"))
            rows.append(
                {
                    "match_id": match_id,
                    "team": team_name,
                    "player_id": player_row.get("player_id"),
                    "player": player_row.get("player_name"),
                    "player_nickname": player_row.get("player_nickname"),
                    "jersey_number": player_row.get("jersey_number"),
                    "position": raw_position,
                    "raw_position": raw_position,
                }
            )
    return pd.DataFrame(rows)


def _normalize_flat_lineups(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize one already-tabular lineup dataframe."""
    working_df = df.copy()
    column_candidates = {
        "match_id": ["match_id"],
        "team": ["team", "team_name"],
        "player_id": ["player_id", "player.id"],
        "player": ["player", "player_name", "player.name"],
        "player_nickname": ["player_nickname", "player.nickname"],
        "jersey_number": ["jersey_number"],
        "position": ["position", "position.name"],
        "raw_position": ["raw_position", "position", "position.name"],
        "position_group": ["position_group"],
    }

    normalized_df = pd.DataFrame(index=working_df.index)
    for normalized_column, candidates in column_candidates.items():
        normalized_df[normalized_column] = _coalesce_columns(working_df, candidates)
    return normalized_df


def _merge_lineup_metadata(events_df: pd.DataFrame, lookup_df: pd.DataFrame, on: list[str]) -> pd.DataFrame:
    """Merge lineup metadata and only fill empty event values."""
    if lookup_df.empty:
        return events_df

    merged_df = events_df.merge(lookup_df, on=on, how="left", suffixes=("", "__lineup"))
    fill_columns = ["player_id", "player_nickname", "position", "position_group", "player"]
    for column in fill_columns:
        lineup_column = f"{column}__lineup"
        if lineup_column not in merged_df.columns:
            continue
        if column not in merged_df.columns:
            merged_df[column] = merged_df[lineup_column]
        else:
            merged_df[column] = merged_df[column].where(~merged_df[column].isna(), merged_df[lineup_column])
        merged_df = merged_df.drop(columns=[lineup_column])
    return merged_df


def _extract_primary_position(positions: object) -> str | None:
    """Return the primary position label from a StatsBomb positions list."""
    if not isinstance(positions, list) or not positions:
        return None
    for position_row in positions:
        if not isinstance(position_row, dict):
            continue
        position_name = _clean_text(position_row.get("position"))
        if position_name:
            return position_name
    return None


def _coalesce_columns(df: pd.DataFrame, candidates: list[str]) -> pd.Series:
    """Return the first available candidate column or an empty series."""
    for column in candidates:
        if column in df.columns:
            return df[column]
    return pd.Series([None] * len(df), index=df.index, dtype="object")


def _map_position_group(value: object) -> str | None:
    """Map one raw position label to the app position buckets."""
    cleaned_value = _clean_text(value)
    if cleaned_value is None:
        return None
    normalized_value = cleaned_value.lower()
    if normalized_value in {"gk", "goalkeeper", "goal keeper", "portero"}:
        return "Portero"
    if normalized_value in {"df", "defender", "defensa"}:
        return "Defensa"
    if normalized_value in {"mf", "midfielder", "mediocentro", "centrocampista"}:
        return "Mediocentro"
    if normalized_value in {"fw", "forward", "delantero", "extremo", "atacante"}:
        return "Atacante"
    for position_group, patterns in POSITION_GROUP_PATTERNS.items():
        if any(pattern in normalized_value for pattern in patterns if len(pattern) > 2):
            return position_group
    return None


def _clean_text(value: object) -> str | None:
    """Return one stripped string or None."""
    if value is None or pd.isna(value):
        return None
    cleaned_value = str(value).strip()
    return cleaned_value or None
