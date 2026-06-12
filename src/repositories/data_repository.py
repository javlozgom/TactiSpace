from __future__ import annotations

from pathlib import Path
from typing import IO, Any

import pandas as pd

from src.config.constants import (
    DEFAULT_EVENTS_NORMALIZED_PATH,
    DEFAULT_EVENTS_RAW_PATH,
    DEFAULT_MATCHES_PATH,
    RAW_LINEUPS_DIR,
)
from src.core.models.lineups import load_lineups
from src.core.spatial.freeze_frame import load_freeze_frames

DEFAULT_PARQUET_PATH = DEFAULT_EVENTS_RAW_PATH
DEFAULT_NORMALIZED_PARQUET_PATH = DEFAULT_EVENTS_NORMALIZED_PATH
DEFAULT_LINEUPS_DIR = RAW_LINEUPS_DIR
NORMALIZED_REQUIRED_COLUMNS = {
    "timestamp",
    "match_id",
    "team",
    "player",
    "minute",
    "second",
    "event_type",
    "x",
    "y",
}


def is_normalized_events_df(df: pd.DataFrame) -> bool:
    """Return whether one dataframe already matches the normalized event schema."""
    return not df.empty and NORMALIZED_REQUIRED_COLUMNS.issubset(df.columns)


def _load_player_nicknames(lineups_dir: str | Path = DEFAULT_LINEUPS_DIR) -> pd.DataFrame:
    """Load player nicknames from raw lineup JSON files when available."""
    directory = Path(lineups_dir)
    if not directory.exists():
        return pd.DataFrame(columns=["match_id", "team", "player", "player_nickname"])

    rows: list[dict[str, object]] = []
    for lineup_file in sorted(directory.glob("*.json")):
        try:
            match_id = int(lineup_file.stem)
            lineup_data = pd.read_json(lineup_file)
        except Exception:
            continue

        if lineup_data.empty:
            continue
        for _, team_row in lineup_data.iterrows():
            team_name = team_row.get("team_name")
            for player in team_row.get("lineup", []) or []:
                if not isinstance(player, dict):
                    continue
                rows.append(
                    {
                        "match_id": match_id,
                        "team": team_name,
                        "player": player.get("player_name"),
                        "player_nickname": player.get("player_nickname"),
                    }
                )
    if not rows:
        return pd.DataFrame(columns=["match_id", "team", "player", "player_nickname"])
    return pd.DataFrame(rows).drop_duplicates(subset=["match_id", "team", "player"])


def _normalize_default_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """Adapt the processed Euro dataset to the prototype schema."""
    event_df = df.copy()

    event_df["event_type"] = event_df["type"]

    event_df["outcome"] = "Unknown"
    event_df.loc[event_df["event_type"] == "Pass", "outcome"] = event_df["pass_outcome"].apply(
        lambda value: "Successful" if pd.isna(value) else "Unsuccessful"
    )
    event_df.loc[event_df["event_type"] == "Carry", "outcome"] = "Successful"
    event_df.loc[event_df["event_type"] == "Dribble", "outcome"] = event_df[
        "dribble_outcome"
    ].map({"Complete": "Successful", "Incomplete": "Unsuccessful"}).fillna("Successful")
    event_df.loc[event_df["event_type"] == "Duel", "outcome"] = "Unknown"
    event_df.loc[event_df["event_type"] == "Ball Recovery", "outcome"] = "Won"
    event_df.loc[event_df["event_type"].isin(["Dispossessed", "Miscontrol", "Error"]), "outcome"] = (
        "Lost"
    )
    event_df.loc[event_df["event_type"].isin(["Interception", "Block", "Foul Won"]), "outcome"] = "Won"
    event_df.loc[event_df["event_type"] == "Shot", "outcome"] = event_df["shot_outcome"].replace(
        {
            "Off T": "Off Target",
            "Wayward": "Off Target",
            "Post": "Off Target",
            "Blocked": "Saved",
            "Saved Off Target": "Saved",
            "Saved to Post": "Saved",
        }
    ).fillna("Saved")
    event_df.loc[event_df["event_type"] == "Ball Receipt*", "outcome"] = "Successful"
    event_df.loc[event_df["event_type"] == "Pressure", "outcome"] = "Successful"
    event_df.loc[event_df["event_type"] == "Clearance", "outcome"] = "Successful"
    event_df.loc[event_df["event_type"] == "Goal Keeper", "outcome"] = "Successful"
    event_df.loc[event_df["event_type"] == "Own Goal Against", "outcome"] = "Own Goal Against"
    event_df.loc[event_df["event_type"] == "Own Goal For", "outcome"] = "Own Goal For"

    event_df["player"] = event_df["player"].fillna("Unknown")
    event_df["end_x"] = event_df["end_x"].fillna(event_df["x"])
    event_df["end_y"] = event_df["end_y"].fillna(event_df["y"])
    if "player_nickname" not in event_df.columns:
        event_df = event_df.merge(
            _load_player_nicknames(),
            on=["match_id", "team", "player"],
            how="left",
        )

    return event_df[
        [
            "match_id",
            "event_id",
            "team",
            "player",
            "player_nickname",
            "position",
            "minute",
            "second",
            "event_type",
            "outcome",
            "x",
            "y",
            "end_x",
            "end_y",
            "possession",
        ]
    ].rename(columns={"possession": "possession_id"})


def load_events(
    uploaded_file: IO[str] | IO[bytes] | Any | None = None,
    default_path: str | Path = DEFAULT_PARQUET_PATH,
) -> pd.DataFrame:
    """Load football events from an uploaded CSV or the processed parquet dataset."""
    try:
        if uploaded_file is not None:
            return pd.read_csv(uploaded_file)

        path = Path(default_path)
        if not path.exists():
            raise FileNotFoundError(f"El archivo por defecto no existe: {path}")
        if path.suffix == ".parquet":
            loaded_df = pd.read_parquet(path)
            if is_normalized_events_df(loaded_df):
                return loaded_df
            return _normalize_default_dataset(loaded_df)
        loaded_df = pd.read_csv(path)
        if is_normalized_events_df(loaded_df):
            return loaded_df
        return loaded_df
    except FileNotFoundError:
        raise
    except Exception as exc:
        raise ValueError(f"No se pudo leer el archivo de eventos: {exc}") from exc


def load_match_labels(
    matches_path: str | Path = DEFAULT_MATCHES_PATH,
) -> dict[str, str]:
    """Load readable match labels keyed by match_id."""
    path = Path(matches_path)
    if not path.exists():
        return {}

    try:
        matches_df = pd.read_json(path)
    except Exception as exc:
        raise ValueError(f"No se pudo leer la metadata de partidos: {exc}") from exc

    required_columns = ["match_id", "match_date", "home_team", "away_team"]
    missing_columns = [column for column in required_columns if column not in matches_df.columns]
    if missing_columns:
        raise ValueError(
            "Faltan columnas en la metadata de partidos: " + ", ".join(missing_columns)
        )

    labels: dict[str, str] = {}
    for _, row in matches_df.iterrows():
        home_team = row["home_team"].get("home_team_name", "Local")
        away_team = row["away_team"].get("away_team_name", "Visitante")
        stage = row.get("competition_stage", {})
        stage_name = stage.get("name") if isinstance(stage, dict) else None
        match_date = pd.to_datetime(row["match_date"], errors="coerce")
        formatted_date = (
            match_date.strftime("%d/%m/%Y") if pd.notna(match_date) else str(row["match_date"])
        )
        label_parts = [f"{home_team} vs {away_team}", formatted_date]
        if stage_name:
            label_parts.append(str(stage_name))
        labels[str(row["match_id"])] = " | ".join(label_parts)

    return labels
