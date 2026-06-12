from __future__ import annotations

import argparse
import sys
from collections.abc import Mapping
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.data_paths import (
    DEFAULT_EVENTS_NORMALIZED_PATH,
    DEFAULT_LINEUPS_NORMALIZED_PATH,
    DEFAULT_THREE_SIXTY_NORMALIZED_PATH,
)
from src.statsbombpy_validation import (
    build_match_validation_row,
    count_coordinate_events,
    count_events_by_type,
    count_unique_frames,
)

REPORT_PATH = Path("data/processed/validation_statsbombpy_report.csv")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate normalized parquet data against statsbombpy.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--limit", type=int, help="Number of matches to validate.")
    group.add_argument("--all", action="store_true", help="Validate all available matches.")
    group.add_argument("--match-id", action="append", dest="match_ids", type=int, help="Specific match_id to validate. Can be repeated.")
    return parser.parse_args()


def read_optional_parquet(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_parquet(path)


def require_match_id_column(df: pd.DataFrame, label: str) -> None:
    if "match_id" not in df.columns:
        raise ValueError(f"Error: {label} no contiene la columna 'match_id'.")


def select_match_ids(events_df: pd.DataFrame, args: argparse.Namespace) -> list[int]:
    available_ids = pd.to_numeric(events_df["match_id"], errors="coerce").dropna().astype(int).drop_duplicates().tolist()
    if not available_ids:
        raise ValueError("Error: events_normalized.parquet no contiene match_id validos.")

    if args.match_ids:
        requested = list(dict.fromkeys(args.match_ids))
        missing = sorted(set(requested) - set(available_ids))
        if missing:
            raise ValueError(f"Error: match_id no encontrado(s) en events_normalized.parquet: {missing}")
        return requested

    if args.all:
        return available_ids

    limit = args.limit if args.limit is not None else 3
    if limit <= 0:
        raise ValueError("Error: --limit debe ser un entero positivo.")
    return available_ids[:limit]


def filter_match_df(df: pd.DataFrame, match_id: int) -> pd.DataFrame:
    if df.empty or "match_id" not in df.columns:
        return pd.DataFrame(columns=df.columns)
    return df.loc[pd.to_numeric(df["match_id"], errors="coerce") == match_id].copy()


def frames_dict_to_df(frames_data: object, match_id: int) -> pd.DataFrame:
    rows: list[dict] = []

    if not isinstance(frames_data, list):
        return pd.DataFrame()

    for event in frames_data:
        if not isinstance(event, Mapping):
            continue

        event_uuid = event.get("event_uuid")
        event_match_id = event.get("match_id", match_id)
        visible_area = event.get("visible_area")
        freeze_frame = event.get("freeze_frame") or []

        for frame in freeze_frame:
            if not isinstance(frame, Mapping):
                continue

            rows.append(
                {
                    "event_uuid": event_uuid,
                    "match_id": event_match_id,
                    "visible_area": visible_area,
                    "teammate": frame.get("teammate"),
                    "actor": frame.get("actor"),
                    "keeper": frame.get("keeper"),
                    "location": frame.get("location"),
                }
            )

    return pd.DataFrame(rows)


def fetch_statsbomb_data(match_id: int) -> tuple[pd.DataFrame, object, pd.DataFrame, str]:
    from statsbombpy import sb

    warning = ""
    sb_events = sb.events(match_id=match_id)
    sb_lineups = sb.lineups(match_id=match_id)
    try:
        frames_dict = sb.frames(match_id=match_id, fmt="dict")
        sb_frames = frames_dict_to_df(frames_dict, match_id)
    except Exception as exc:  # pragma: no cover - depends on remote availability
        sb_frames = pd.DataFrame()
        warning = f"frames unavailable: {exc}"

    return sb_events, sb_lineups, sb_frames, warning


def main() -> int:
    args = parse_args()

    if not DEFAULT_EVENTS_NORMALIZED_PATH.exists():
        print(f"Error: no existe {DEFAULT_EVENTS_NORMALIZED_PATH}", file=sys.stderr)
        return 1

    try:
        events_df = pd.read_parquet(DEFAULT_EVENTS_NORMALIZED_PATH)
        require_match_id_column(events_df, str(DEFAULT_EVENTS_NORMALIZED_PATH))
        lineups_df = read_optional_parquet(DEFAULT_LINEUPS_NORMALIZED_PATH)
        frames_df = read_optional_parquet(DEFAULT_THREE_SIXTY_NORMALIZED_PATH)
        match_ids = select_match_ids(events_df, args)
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1

    rows: list[dict] = []
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

    for match_id in match_ids:
        print(f"Validando match_id={match_id}...")
        events_match = filter_match_df(events_df, match_id)
        lineups_match = filter_match_df(lineups_df, match_id)
        frames_match = filter_match_df(frames_df, match_id)

        try:
            sb_events, sb_lineups, sb_frames, warning = fetch_statsbomb_data(match_id)
            row = build_match_validation_row(
                match_id=match_id,
                events_norm=events_match,
                lineups_norm=lineups_match,
                frames_norm=frames_match,
                sb_events=sb_events,
                sb_lineups=sb_lineups,
                sb_frames=sb_frames,
            )
            if warning:
                row["warning"] = warning
            print(
                f"  status={row['status']} events={row['events_parquet']}/{row['events_sb']} "
                f"passes={row['passes_parquet']}/{row['passes_sb']} shots={row['shots_parquet']}/{row['shots_sb']}"
            )
        except Exception as exc:
            row = {
                "match_id": match_id,
                "events_parquet": int(len(events_match)),
                "events_sb": 0,
                "diff_events": int(len(events_match)),
                "passes_parquet": count_events_by_type(events_match, "Pass"),
                "passes_sb": 0,
                "shots_parquet": count_events_by_type(events_match, "Shot"),
                "shots_sb": 0,
                "lineups_parquet": int(len(lineups_match)),
                "lineups_sb": 0,
                "freeze_frames_parquet": count_unique_frames(frames_match),
                "freeze_frames_sb": 0,
                "coordinate_events_parquet": count_coordinate_events(events_match),
                "coordinate_events_sb": 0,
                "status": "error",
                "warning": str(exc),
            }
            print(f"  status=error warning={exc}")

        rows.append(row)

    report_df = pd.DataFrame(rows)
    report_df.to_csv(REPORT_PATH, index=False)
    print(f"Reporte guardado en {REPORT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
