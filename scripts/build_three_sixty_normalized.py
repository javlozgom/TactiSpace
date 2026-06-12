from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.data_paths import (
    DEFAULT_THREE_SIXTY_NORMALIZED_PATH,
    DEFAULT_THREE_SIXTY_RAW_PATH,
    RAW_THREE_SIXTY_DIR,
)
from src.freeze_frame import load_freeze_frames, normalize_freeze_frame_df


def optimize_three_sixty_df(df: pd.DataFrame) -> pd.DataFrame:
    """Apply safe dtype optimizations to one normalized 360 dataframe."""
    optimized_df = df.copy()
    for column in ["player", "team"]:
        if column in optimized_df.columns:
            optimized_df[column] = optimized_df[column].astype("category")
    for column in ["x", "y"]:
        if column in optimized_df.columns:
            optimized_df[column] = pd.to_numeric(optimized_df[column], errors="coerce").astype("float32")
    for column in ["match_id", "player_id"]:
        if column in optimized_df.columns:
            optimized_df[column] = pd.to_numeric(optimized_df[column], errors="coerce").astype("Int32")
    return optimized_df


def main() -> None:
    """Build the normalized three_sixty parquet from processed or raw sources."""
    source_path = DEFAULT_THREE_SIXTY_RAW_PATH if DEFAULT_THREE_SIXTY_RAW_PATH.exists() else RAW_THREE_SIXTY_DIR
    print(f"Cargando datos 360 desde {source_path}...")
    raw_df = load_freeze_frames(source_path)
    normalized_df = normalize_freeze_frame_df(raw_df)
    optimized_df = optimize_three_sixty_df(normalized_df)

    DEFAULT_THREE_SIXTY_NORMALIZED_PATH.parent.mkdir(parents=True, exist_ok=True)
    optimized_df.to_parquet(DEFAULT_THREE_SIXTY_NORMALIZED_PATH, index=False)

    print(f"Filas cargadas: {len(optimized_df):,}")
    print(f"Eventos únicos: {optimized_df['event_id'].nunique(dropna=True):,}" if "event_id" in optimized_df.columns else "Eventos únicos: 0")
    print(f"Partidos únicos: {optimized_df['match_id'].nunique(dropna=True):,}" if "match_id" in optimized_df.columns else "Partidos únicos: 0")
    print(f"Guardado en {DEFAULT_THREE_SIXTY_NORMALIZED_PATH}")


if __name__ == "__main__":
    main()
