from __future__ import annotations

import importlib
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest


validation_script = importlib.import_module("scripts.validate_statsbombpy_data")


def test_parse_args_supports_limit_all_and_match_ids(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr("sys.argv", ["validate_statsbombpy_data.py", "--limit", "5"])
    args = validation_script.parse_args()
    assert args.limit == 5
    assert args.all is False

    monkeypatch.setattr("sys.argv", ["validate_statsbombpy_data.py", "--all"])
    args = validation_script.parse_args()
    assert args.all is True

    monkeypatch.setattr("sys.argv", ["validate_statsbombpy_data.py", "--match-id", "1", "--match-id", "2"])
    args = validation_script.parse_args()
    assert args.match_ids == [1, 2]


def test_read_optional_parquet_returns_empty_when_missing(tmp_path: Path):
    result = validation_script.read_optional_parquet(tmp_path / "missing.parquet")
    assert result.empty


def test_require_match_id_column_validates_input():
    validation_script.require_match_id_column(pd.DataFrame([{"match_id": 1}]), "events")

    with pytest.raises(ValueError):
        validation_script.require_match_id_column(pd.DataFrame([{"x": 1}]), "events")


def test_select_match_ids_handles_default_limit_all_and_explicit_requests():
    events_df = pd.DataFrame({"match_id": [1, 2, 3, None]})

    assert validation_script.select_match_ids(events_df, SimpleNamespace(match_ids=None, all=False, limit=None)) == [1, 2, 3]
    assert validation_script.select_match_ids(events_df, SimpleNamespace(match_ids=None, all=False, limit=2)) == [1, 2]
    assert validation_script.select_match_ids(events_df, SimpleNamespace(match_ids=None, all=True, limit=None)) == [1, 2, 3]
    assert validation_script.select_match_ids(events_df, SimpleNamespace(match_ids=[3, 1, 3], all=False, limit=None)) == [3, 1]


def test_select_match_ids_raises_for_invalid_cases():
    empty_events_df = pd.DataFrame({"match_id": [None]})

    with pytest.raises(ValueError):
        validation_script.select_match_ids(empty_events_df, SimpleNamespace(match_ids=None, all=False, limit=None))

    with pytest.raises(ValueError):
        validation_script.select_match_ids(
            pd.DataFrame({"match_id": [1, 2]}),
            SimpleNamespace(match_ids=[4], all=False, limit=None),
        )

    with pytest.raises(ValueError):
        validation_script.select_match_ids(
            pd.DataFrame({"match_id": [1, 2]}),
            SimpleNamespace(match_ids=None, all=False, limit=0),
        )


def test_filter_match_df_and_frames_dict_to_df():
    df = pd.DataFrame({"match_id": [1, 2], "value": [10, 20]})
    filtered = validation_script.filter_match_df(df, 2)

    assert filtered["value"].tolist() == [20]
    assert validation_script.filter_match_df(pd.DataFrame(), 1).empty

    frames_df = validation_script.frames_dict_to_df(
        [
            {
                "event_uuid": "evt-1",
                "match_id": 8,
                "visible_area": [1, 2, 3],
                "freeze_frame": [
                    {"teammate": True, "actor": False, "keeper": False, "location": [10, 20]},
                    "invalid",
                ],
            },
            "skip",
        ],
        8,
    )

    assert len(frames_df) == 1
    assert frames_df.loc[0, "event_uuid"] == "evt-1"
    assert validation_script.frames_dict_to_df("invalid", 8).empty


def test_fetch_statsbomb_data_uses_frames_dict_and_handles_success(monkeypatch: pytest.MonkeyPatch):
    class _SB:
        @staticmethod
        def events(match_id: int):
            return pd.DataFrame([{"match_id": match_id}])

        @staticmethod
        def lineups(match_id: int):
            return pd.DataFrame([{"match_id": match_id}])

        @staticmethod
        def frames(match_id: int, fmt: str):
            assert fmt == "dict"
            return [{"event_uuid": "evt-1", "freeze_frame": [{"teammate": True}]}]

    monkeypatch.setitem(__import__("sys").modules, "statsbombpy", SimpleNamespace(sb=_SB))

    sb_events, sb_lineups, sb_frames, warning = validation_script.fetch_statsbomb_data(9)

    assert not sb_events.empty
    assert not sb_lineups.empty
    assert not sb_frames.empty
    assert warning == ""


def test_fetch_statsbomb_data_handles_frames_failure(monkeypatch: pytest.MonkeyPatch):
    class _SB:
        @staticmethod
        def events(match_id: int):
            return pd.DataFrame([{"match_id": match_id}])

        @staticmethod
        def lineups(match_id: int):
            return pd.DataFrame([{"match_id": match_id}])

        @staticmethod
        def frames(match_id: int, fmt: str):
            raise RuntimeError("frames down")

    monkeypatch.setitem(__import__("sys").modules, "statsbombpy", SimpleNamespace(sb=_SB))

    _, _, sb_frames, warning = validation_script.fetch_statsbomb_data(9)

    assert sb_frames.empty
    assert "frames unavailable" in warning


def test_main_returns_error_when_events_parquet_is_missing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    monkeypatch.setattr(validation_script, "DEFAULT_EVENTS_NORMALIZED_PATH", tmp_path / "missing.parquet")
    monkeypatch.setattr(
        validation_script,
        "parse_args",
        lambda: SimpleNamespace(match_ids=None, all=False, limit=None),
    )

    result = validation_script.main()

    err = capsys.readouterr().err
    assert result == 1
    assert "no existe" in err


def test_main_builds_report_and_handles_fetch_errors(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    events_path = tmp_path / "events_normalized.parquet"
    report_path = tmp_path / "validation_report.csv"
    lineups_path = tmp_path / "lineups_normalized.parquet"
    frames_path = tmp_path / "three_sixty_normalized.parquet"
    events_path.write_text("x", encoding="utf-8")
    lineups_path.write_text("x", encoding="utf-8")
    frames_path.write_text("x", encoding="utf-8")
    events_df = pd.DataFrame({"match_id": [1, 2], "event_type": ["Pass", "Shot"], "x": [1, 2], "y": [3, 4]})
    lineups_df = pd.DataFrame({"match_id": [1, 2], "player": ["A", "B"]})
    frames_df = pd.DataFrame({"match_id": [1], "event_uuid": ["evt-1"]})

    monkeypatch.setattr(validation_script, "DEFAULT_EVENTS_NORMALIZED_PATH", events_path)
    monkeypatch.setattr(validation_script, "DEFAULT_LINEUPS_NORMALIZED_PATH", lineups_path)
    monkeypatch.setattr(validation_script, "DEFAULT_THREE_SIXTY_NORMALIZED_PATH", frames_path)
    monkeypatch.setattr(validation_script, "REPORT_PATH", report_path)
    monkeypatch.setattr(
        validation_script,
        "parse_args",
        lambda: SimpleNamespace(match_ids=None, all=False, limit=2),
    )

    def _fake_read_parquet(path: Path):
        if path == events_path:
            return events_df
        if path == lineups_path:
            return lineups_df
        if path == frames_path:
            return frames_df
        raise AssertionError(f"Unexpected path: {path}")

    monkeypatch.setattr(pd, "read_parquet", _fake_read_parquet)
    monkeypatch.setattr(validation_script, "build_match_validation_row", lambda **kwargs: {"match_id": kwargs["match_id"], "status": "ok", "events_parquet": 1, "events_sb": 1, "passes_parquet": 1, "passes_sb": 1, "shots_parquet": 0, "shots_sb": 0})

    def _fake_fetch(match_id: int):
        if match_id == 1:
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), "frames warning"
        raise RuntimeError("remote failed")

    monkeypatch.setattr(validation_script, "fetch_statsbomb_data", _fake_fetch)

    result = validation_script.main()

    output = capsys.readouterr().out
    assert result == 0
    assert report_path.exists()
    report_df = pd.read_csv(report_path)
    assert report_df["match_id"].tolist() == [1, 2]
    assert "Reporte guardado" in output
