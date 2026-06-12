from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.data_paths import DEFAULT_LINEUPS_NORMALIZED_PATH, DEFAULT_LINEUPS_RAW_PATH, RAW_LINEUPS_DIR
from src.lineups import load_lineups, load_lineups_from_json_dir, normalize_lineups_df


def main() -> None:
    """Build the normalized lineups parquet from processed or raw sources."""
    print(f"Buscando lineups procesados en {DEFAULT_LINEUPS_RAW_PATH}...")
    if DEFAULT_LINEUPS_RAW_PATH.exists():
        lineups_df = load_lineups(DEFAULT_LINEUPS_RAW_PATH)
    else:
        print(f"No existe {DEFAULT_LINEUPS_RAW_PATH}. Probando JSONs raw en {RAW_LINEUPS_DIR}...")
        lineups_df = load_lineups_from_json_dir(RAW_LINEUPS_DIR)

    normalized_df = normalize_lineups_df(lineups_df)
    DEFAULT_LINEUPS_NORMALIZED_PATH.parent.mkdir(parents=True, exist_ok=True)
    normalized_df.to_parquet(DEFAULT_LINEUPS_NORMALIZED_PATH, index=False)

    print(f"Filas cargadas: {len(normalized_df):,}")
    print(f"Jugadores únicos: {normalized_df['player'].nunique(dropna=True):,}" if "player" in normalized_df.columns else "Jugadores únicos: 0")
    print(f"Partidos únicos: {normalized_df['match_id'].nunique(dropna=True):,}" if "match_id" in normalized_df.columns else "Partidos únicos: 0")
    print(f"Guardado en {DEFAULT_LINEUPS_NORMALIZED_PATH}")


if __name__ == "__main__":
    main()
