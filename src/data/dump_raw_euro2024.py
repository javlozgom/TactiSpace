import json
import time
from pathlib import Path
from typing import Any, Optional, Dict

import requests

# =========================
# CONFIG
# =========================
BASE_URL = "https://raw.githubusercontent.com/statsbomb/open-data/master/data"

# Euro 2024 (StatsBomb Open Data)
COMPETITION_ID = 55
SEASON_ID = 282

# Tu carpeta data (la que has indicado)
DATA_DIR = Path(r"C:\Users\javie\Escritorio\Curso 25-26\TFG\ws-TFG\data")

RAW_ROOT = DATA_DIR / "raw" / "statsbomb" / "euro_2024"
EVENTS_DIR = RAW_ROOT / "events"
LINEUPS_DIR = RAW_ROOT / "lineups"
THREE_SIXTY_DIR = RAW_ROOT / "three_sixty"  # (en GitHub es "three-sixty")

TIMEOUT = 30
RETRIES = 5
SLEEP_SECONDS = 0.15  # evita rate limit / carga excesiva

# Si True, no vuelve a descargar archivos que ya existen
SKIP_IF_EXISTS = True


# =========================
# HELPERS
# =========================
def fetch_json(url: str) -> Any:
    last_err: Optional[Exception] = None
    for attempt in range(1, RETRIES + 1):
        try:
            r = requests.get(url, timeout=TIMEOUT)
            if r.status_code == 200:
                return r.json()
            if r.status_code == 404:
                return None
            r.raise_for_status()
        except Exception as e:
            last_err = e
            time.sleep(0.7 * attempt)
    raise RuntimeError(f"Fallo descargando {url}. Último error: {last_err}")


def dump_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)


def ok_existing(path: Path) -> bool:
    return path.exists() and path.stat().st_size > 20


def maybe_download(url: str, out_path: Path, manifest: Dict, key_ok: str, key_404: Optional[str] = None) -> None:
    if SKIP_IF_EXISTS and ok_existing(out_path):
        return

    data = fetch_json(url)
    if data is None:
        if key_404:
            manifest[key_404] += 1
        return

    dump_json(out_path, data)
    manifest[key_ok] += 1


# =========================
# MAIN
# =========================
def main() -> None:
    RAW_ROOT.mkdir(parents=True, exist_ok=True)
    EVENTS_DIR.mkdir(parents=True, exist_ok=True)
    LINEUPS_DIR.mkdir(parents=True, exist_ok=True)
    THREE_SIXTY_DIR.mkdir(parents=True, exist_ok=True)

    manifest = {
        "competition_id": COMPETITION_ID,
        "season_id": SEASON_ID,
        "export_root": str(RAW_ROOT),
        "downloaded": {
            "competitions": 0,
            "matches": 0,
            "events": 0,
            "lineups": 0,
            "three_sixty": 0,
            "three_sixty_missing": 0,
        },
        "matches_count": 0,
        "notes": [
            "Los archivos en data/raw son crudos (sin transformar).",
            "three_sixty se descarga del endpoint 'three-sixty' y se guarda en carpeta 'three_sixty'."
        ],
    }

    # 1) competitions.json (útil para contexto)
    comps_path = RAW_ROOT / "competitions.json"
    comps_url = f"{BASE_URL}/competitions.json"
    maybe_download(
        comps_url, comps_path,
        manifest["downloaded"], "competitions"
    )
    time.sleep(SLEEP_SECONDS)

    # 2) matches del torneo
    matches_path = RAW_ROOT / "matches.json"
    matches_url = f"{BASE_URL}/matches/{COMPETITION_ID}/{SEASON_ID}.json"

    if not (SKIP_IF_EXISTS and ok_existing(matches_path)):
        matches = fetch_json(matches_url)
        if matches is None:
            raise RuntimeError("No se pudo descargar matches.json. Revisa COMPETITION_ID/SEASON_ID.")
        dump_json(matches_path, matches)
        manifest["downloaded"]["matches"] += 1
    else:
        matches = json.loads(matches_path.read_text(encoding="utf-8"))

    manifest["matches_count"] = len(matches)
    print(f"📦 Partidos: {len(matches)}")

    # 3) por partido: events / lineups / three-sixty
    for i, m in enumerate(matches, start=1):
        match_id = m["match_id"]
        print(f"[{i}/{len(matches)}] match_id={match_id}")

        # events
        maybe_download(
            f"{BASE_URL}/events/{match_id}.json",
            EVENTS_DIR / f"{match_id}.json",
            manifest["downloaded"], "events"
        )
        time.sleep(SLEEP_SECONDS)

        # lineups
        maybe_download(
            f"{BASE_URL}/lineups/{match_id}.json",
            LINEUPS_DIR / f"{match_id}.json",
            manifest["downloaded"], "lineups"
        )
        time.sleep(SLEEP_SECONDS)

        # three-sixty (ojo al guion en el endpoint)
        maybe_download(
            f"{BASE_URL}/three-sixty/{match_id}.json",
            THREE_SIXTY_DIR / f"{match_id}.json",
            manifest["downloaded"], "three_sixty", "three_sixty_missing"
        )
        time.sleep(SLEEP_SECONDS)

    dump_json(RAW_ROOT / "manifest.json", manifest)

    print("\n🏁 Dump crudo terminado")
    print(f"📁 {RAW_ROOT}")
    print("✅ Resumen:", manifest["downloaded"])


if __name__ == "__main__":
    main()
