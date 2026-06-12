from __future__ import annotations

from pathlib import Path


DEFAULT_EVENTS_RAW_PATH = Path("data/processed/events.parquet")
DEFAULT_EVENTS_NORMALIZED_PATH = Path("data/processed/events_normalized.parquet")

DEFAULT_THREE_SIXTY_RAW_PATH = Path("data/processed/three_sixty.parquet")
DEFAULT_THREE_SIXTY_NORMALIZED_PATH = Path("data/processed/three_sixty_normalized.parquet")

DEFAULT_LINEUPS_RAW_PATH = Path("data/processed/lineups.parquet")
DEFAULT_LINEUPS_NORMALIZED_PATH = Path("data/processed/lineups_normalized.parquet")

RAW_THREE_SIXTY_DIR = Path("data/raw/statsbomb/euro_2024/three_sixty")
RAW_LINEUPS_DIR = Path("data/raw/statsbomb/euro_2024/lineups")
DEFAULT_MATCHES_PATH = Path("data/raw/statsbomb/euro_2024/matches.json")
