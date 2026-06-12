# scripts/01_build_dataset.py
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import pandas as pd


# -----------------------------
# Repo / paths helpers
# -----------------------------
def find_repo_root(start: Path | None = None) -> Path:
    """Walk upwards to find repo root (pyproject.toml or .git)."""
    if start is None:
        start = Path(__file__).resolve()
    for parent in [start, *start.parents]:
        if (parent / "pyproject.toml").exists() or (parent / ".git").exists():
            return parent
    # fallback: repo/scripts/01_build_dataset.py
    return Path(__file__).resolve().parents[1]


def ensure_dirs(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


# -----------------------------
# StatsBomb parsing helpers
# -----------------------------
def safe_get(d: Dict[str, Any], *keys: str, default=None):
    cur: Any = d
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return cur


def parse_location(loc: Any) -> Tuple[Optional[float], Optional[float]]:
    """StatsBomb location is [x, y]. Return (x, y) or (None, None)."""
    if isinstance(loc, list) and len(loc) >= 2:
        try:
            return float(loc[0]), float(loc[1])
        except (TypeError, ValueError):
            return None, None
    return None, None


def pick_end_location(event: Dict[str, Any]) -> Tuple[Optional[float], Optional[float]]:
    """
    StatsBomb: end location depends on event type.
    - pass.end_location
    - carry.end_location
    - shot.end_location
    - clearance.end_location (sometimes)
    Add more later if you need.
    """
    et = safe_get(event, "type", "name", default=None)

    if et == "Pass":
        end_loc = safe_get(event, "pass", "end_location", default=None)
        return parse_location(end_loc)

    if et == "Carry":
        end_loc = safe_get(event, "carry", "end_location", default=None)
        return parse_location(end_loc)

    if et == "Shot":
        end_loc = safe_get(event, "shot", "end_location", default=None)
        return parse_location(end_loc)

    if et == "Clearance":
        end_loc = safe_get(event, "clearance", "end_location", default=None)
        return parse_location(end_loc)

    return None, None


def extract_common_fields(event: Dict[str, Any], match_id: int) -> Dict[str, Any]:
    x, y = parse_location(event.get("location"))
    end_x, end_y = pick_end_location(event)

    out: Dict[str, Any] = {
        "match_id": match_id,
        "event_id": event.get("id"),
        "index": event.get("index"),
        "period": event.get("period"),
        "timestamp": event.get("timestamp"),
        "minute": event.get("minute"),
        "second": event.get("second"),
        "type": safe_get(event, "type", "name"),
        "possession": event.get("possession"),
        "possession_team": safe_get(event, "possession_team", "name"),
        "team": safe_get(event, "team", "name"),
        "player": safe_get(event, "player", "name"),
        "position": safe_get(event, "position", "name"),
        "play_pattern": safe_get(event, "play_pattern", "name"),
        "x": x,
        "y": y,
        "end_x": end_x,
        "end_y": end_y,
        # Some generic flags
        "under_pressure": bool(event.get("under_pressure")) if "under_pressure" in event else None,
        "out": bool(event.get("out")) if "out" in event else None,
        "off_camera": bool(event.get("off_camera")) if "off_camera" in event else None,
    }
    return out


def extract_pass_fields(event: Dict[str, Any]) -> Dict[str, Any]:
    p = event.get("pass", {}) if isinstance(event.get("pass"), dict) else {}
    return {
        "pass_recipient": safe_get(p, "recipient", "name"),
        "pass_length": p.get("length"),
        "pass_angle": p.get("angle"),
        "pass_height": safe_get(p, "height", "name"),
        "pass_type": safe_get(p, "type", "name"),
        "pass_body_part": safe_get(p, "body_part", "name"),
        "pass_outcome": safe_get(p, "outcome", "name"),
        "pass_assisted_shot_id": p.get("assisted_shot_id"),
        "pass_switch": bool(p.get("switch")) if "switch" in p else None,
        "pass_cross": bool(p.get("cross")) if "cross" in p else None,
        "pass_cut_back": bool(p.get("cut_back")) if "cut_back" in p else None,
        "pass_through_ball": bool(p.get("through_ball")) if "through_ball" in p else None,
    }


def extract_shot_fields(event: Dict[str, Any]) -> Dict[str, Any]:
    s = event.get("shot", {}) if isinstance(event.get("shot"), dict) else {}
    return {
        "shot_outcome": safe_get(s, "outcome", "name"),
        "shot_statsbomb_xg": s.get("statsbomb_xg"),
        "shot_body_part": safe_get(s, "body_part", "name"),
        "shot_type": safe_get(s, "type", "name"),
        "shot_technique": safe_get(s, "technique", "name"),
        "shot_first_time": bool(s.get("first_time")) if "first_time" in s else None,
        "shot_one_on_one": bool(s.get("one_on_one")) if "one_on_one" in s else None,
        "shot_open_goal": bool(s.get("open_goal")) if "open_goal" in s else None,
        "shot_aerial_won": bool(s.get("aerial_won")) if "aerial_won" in s else None,
    }


def extract_carry_fields(event: Dict[str, Any]) -> Dict[str, Any]:
    c = event.get("carry", {}) if isinstance(event.get("carry"), dict) else {}
    return {
        "carry_length": c.get("length"),
        "carry_end_location": c.get("end_location"),  # keep raw too if you want
    }


# ✅ NUEVO: DRIBBLE
def extract_dribble_fields(event: Dict[str, Any]) -> Dict[str, Any]:
    d = event.get("dribble", {}) if isinstance(event.get("dribble"), dict) else {}
    return {
        # En tu raw viene como dribble.outcome.name = "Complete"/"Incomplete"
        "dribble_outcome": safe_get(d, "outcome", "name"),
        # Flags típicos (si existen en el JSON)
        "dribble_nutmeg": bool(d.get("nutmeg")) if "nutmeg" in d else None,
        "dribble_overrun": bool(d.get("overrun")) if "overrun" in d else None,
        "dribble_no_touch": bool(d.get("no_touch")) if "no_touch" in d else None,
    }


def event_to_row(event: Dict[str, Any], match_id: int) -> Dict[str, Any]:
    row = extract_common_fields(event, match_id)

    et = row["type"]
    if et == "Pass":
        row.update(extract_pass_fields(event))
    elif et == "Shot":
        row.update(extract_shot_fields(event))
    elif et == "Carry":
        row.update(extract_carry_fields(event))
    elif et == "Dribble":
        row.update(extract_dribble_fields(event))

    return row


def read_events_file(path: Path) -> List[Dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(f"Events JSON is not a list: {path}")
    return data


def infer_match_id_from_filename(path: Path) -> int:
    # StatsBomb open-data typically uses events/<match_id>.json
    stem = path.stem
    try:
        return int(stem)
    except ValueError as e:
        raise ValueError(f"Cannot infer match_id from filename: {path.name}") from e


def iter_event_files(raw_dir: Path) -> Iterable[Path]:
    """
    Look for event JSON files under:
      data/raw/**/events/*.json
    """
    patterns = [
        "**/events/*.json",
        "**/event/*.json",  # just in case
    ]
    seen = set()
    for pat in patterns:
        for p in raw_dir.glob(pat):
            if p.is_file() and p.suffix.lower() == ".json":
                if p not in seen:
                    seen.add(p)
                    yield p


# -----------------------------
# Main dataset builder
# -----------------------------
def build_events_dataset(
    raw_dir: Path,
    limit_files: Optional[int] = None,
    verbose: bool = False,
) -> pd.DataFrame:
    files = sorted(iter_event_files(raw_dir))
    if limit_files is not None:
        files = files[:limit_files]

    if not files:
        raise FileNotFoundError(
            f"No event JSON files found under {raw_dir}. "
            "Expected something like data/raw/**/events/<match_id>.json"
        )

    rows: List[Dict[str, Any]] = []
    for i, fp in enumerate(files, start=1):
        match_id = infer_match_id_from_filename(fp)
        events = read_events_file(fp)
        for ev in events:
            if isinstance(ev, dict):
                rows.append(event_to_row(ev, match_id))

        if verbose:
            print(f"[{i}/{len(files)}] parsed {fp} (match_id={match_id}, events={len(events)})")

    df = pd.DataFrame(rows)

    # Basic dtype cleanup (optional but nice)
    numeric_cols = [
        "minute", "second", "period", "index",
        "x", "y", "end_x", "end_y",
        "pass_length", "pass_angle",
        "shot_statsbomb_xg",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


def main() -> None:
    parser = argparse.ArgumentParser(description="Build processed dataset from raw StatsBomb event JSONs.")
    parser.add_argument(
        "--raw-dir",
        type=str,
        default=None,
        help="Path to data/raw. Default: <repo_root>/data/raw",
    )
    parser.add_argument(
        "--out",
        type=str,
        default=None,
        help="Output file path. Default: <repo_root>/data/processed/events.parquet",
    )
    parser.add_argument(
        "--format",
        type=str,
        choices=["parquet", "csv"],
        default="parquet",
        help="Output format (default: parquet).",
    )
    parser.add_argument(
        "--limit-files",
        type=int,
        default=None,
        help="Limit number of event files for quick runs.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print progress while parsing files.",
    )

    args = parser.parse_args()

    repo_root = find_repo_root()
    raw_dir = Path(args.raw_dir) if args.raw_dir else (repo_root / "data" / "raw")
    out_path = Path(args.out) if args.out else (repo_root / "data" / "processed" / f"events.{args.format}")

    df = build_events_dataset(raw_dir=raw_dir, limit_files=args.limit_files, verbose=args.verbose)

    ensure_dirs(out_path.parent)

    if args.format == "csv":
        df.to_csv(out_path, index=False)
    else:
        df.to_parquet(out_path, index=False)

    # Mini-check para que veas al vuelo si ya hay dribbles con outcome
    if "type" in df.columns and "dribble_outcome" in df.columns:
        d = df[df["type"] == "Dribble"]
        print(f"Saved: {out_path} | rows={len(df)} | dribbles={len(d)}")
        if len(d) > 0:
            print("dribble_outcome counts:")
            print(d["dribble_outcome"].value_counts(dropna=False).head(10))
    else:
        print(f"Saved: {out_path} | rows={len(df)}")


if __name__ == "__main__":
    main()
