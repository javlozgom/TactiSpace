from __future__ import annotations

import sys
from pathlib import Path
from time import perf_counter

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.data_loader import load_events
from src.data_paths import (
    DEFAULT_EVENTS_NORMALIZED_PATH,
    DEFAULT_EVENTS_RAW_PATH,
    DEFAULT_LINEUPS_NORMALIZED_PATH,
)
from src.lineups import enrich_events_with_lineups, is_normalized_lineups_df, load_lineups
from src.preprocessing import add_derived_event_columns, normalize_events


def optimize_events_df(df: pd.DataFrame) -> pd.DataFrame:
    """Apply safe dtype optimizations to one normalized events dataframe."""
    optimized_df = df.copy()

    for column in ["team", "player", "event_type", "outcome", "position", "position_group", "player_nickname"]:
        if column in optimized_df.columns:
            optimized_df[column] = optimized_df[column].astype("category")

    for column in ["x", "y", "end_x", "end_y", "action_length"]:
        if column in optimized_df.columns:
            optimized_df[column] = pd.to_numeric(optimized_df[column], errors="coerce").astype("float32")

    for column in ["minute", "second"]:
        if column in optimized_df.columns:
            optimized_df[column] = pd.to_numeric(optimized_df[column], errors="coerce").astype("Int16")

    for column in ["match_id", "possession_id", "timestamp", "player_id"]:
        if column in optimized_df.columns:
            optimized_df[column] = pd.to_numeric(optimized_df[column], errors="coerce").astype("Int32")

    return optimized_df


def main() -> None:
    """Build the normalized events parquet, enriching it with lineups when available."""
    start_time = perf_counter()
    print(f"Cargando eventos base desde {DEFAULT_EVENTS_RAW_PATH}...")
    input_df = load_events(default_path=DEFAULT_EVENTS_RAW_PATH)
    print(f"Filas de entrada: {len(input_df):,}")

    print("Normalizando eventos...")
    normalized_df = normalize_events(input_df)
    normalized_df = add_derived_event_columns(normalized_df)

    used_lineups = False
    if DEFAULT_LINEUPS_NORMALIZED_PATH.exists():
        lineups_df = load_lineups(DEFAULT_LINEUPS_NORMALIZED_PATH)
        if is_normalized_lineups_df(lineups_df):
            normalized_df = enrich_events_with_lineups(normalized_df, lineups_df)
            used_lineups = True

    print("Optimizando tipos...")
    optimized_df = optimize_events_df(normalized_df)

    DEFAULT_EVENTS_NORMALIZED_PATH.parent.mkdir(parents=True, exist_ok=True)
    optimized_df.to_parquet(DEFAULT_EVENTS_NORMALIZED_PATH, index=False)

    elapsed = perf_counter() - start_time
    position_columns = [column for column in ["position", "position_group"] if column in optimized_df.columns]
    print(f"Filas de salida: {len(optimized_df):,}")
    print(f"Lineups usados para enriquecer: {'sí' if used_lineups else 'no'}")
    print(f"Columnas de posición disponibles: {', '.join(position_columns) if position_columns else 'ninguna'}")
    print(f"Dataset guardado en {DEFAULT_EVENTS_NORMALIZED_PATH}")
    print(f"Tiempo total: {elapsed:.2f}s")


if __name__ == "__main__":
    main()
