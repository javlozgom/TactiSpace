from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.build_events_normalized import main as build_events_normalized
from scripts.build_lineups_normalized import main as build_lineups_normalized
from scripts.build_three_sixty_normalized import main as build_three_sixty_normalized


def main() -> None:
    """Run the full normalized data pipeline."""
    print("1. Generando lineups_normalized.parquet...")
    build_lineups_normalized()
    print("\n2. Generando events_normalized.parquet...")
    build_events_normalized()
    print("\n3. Generando three_sixty_normalized.parquet...")
    try:
        build_three_sixty_normalized()
    except Exception as exc:
        print(f"No se pudo generar three_sixty_normalized.parquet: {exc}")
    print("\nPipeline completado.")


if __name__ == "__main__":
    main()
