from __future__ import annotations

import importlib
from pathlib import Path

import pandas as pd
import pytest


build_all_normalized = importlib.import_module("scripts.build_all_normalized")
build_events_normalized = importlib.import_module("scripts.build_events_normalized")
build_lineups_normalized = importlib.import_module("scripts.build_lineups_normalized")
build_normalized_dataset = importlib.import_module("scripts.build_normalized_dataset")
build_three_sixty_normalized = importlib.import_module("scripts.build_three_sixty_normalized")


def test_build_all_normalized_runs_full_pipeline_and_handles_three_sixty_error(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    calls: list[str] = []

    monkeypatch.setattr(build_all_normalized, "build_lineups_normalized", lambda: calls.append("lineups"))
    monkeypatch.setattr(build_all_normalized, "build_events_normalized", lambda: calls.append("events"))

    def _raise_three_sixty():
        calls.append("three_sixty")
        raise RuntimeError("boom")

    monkeypatch.setattr(build_all_normalized, "build_three_sixty_normalized", _raise_three_sixty)

    build_all_normalized.main()

    output = capsys.readouterr().out
    assert calls == ["lineups", "events", "three_sixty"]
    assert "Pipeline completado." in output
    assert "No se pudo generar three_sixty_normalized.parquet" in output


def test_optimize_events_df_casts_supported_columns():
    df = pd.DataFrame(
        [
            {
                "team": "Spain",
                "player": "A",
                "event_type": "Pass",
                "outcome": "Successful",
                "position": "CM",
                "position_group": "Midfielder",
                "player_nickname": "AA",
                "x": "10",
                "y": "20",
                "end_x": "30",
                "end_y": "40",
                "action_length": "50",
                "minute": "12",
                "second": "8",
                "match_id": "100",
                "possession_id": "9",
                "timestamp": "123",
                "player_id": "7",
            }
        ]
    )

    result = build_events_normalized.optimize_events_df(df)

    assert str(result["team"].dtype) == "category"
    assert str(result["x"].dtype) == "float32"
    assert str(result["minute"].dtype) == "Int16"
    assert str(result["match_id"].dtype) == "Int32"


def test_build_events_normalized_main_enriches_and_writes_parquet(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    input_df = pd.DataFrame([{"match_id": 1, "player": "A"}])
    normalized_df = pd.DataFrame([{"match_id": 1, "player": "A", "position": "CM", "position_group": "Mid"}])
    lineups_df = pd.DataFrame([{"match_id": 1, "player": "A"}])
    output_path = tmp_path / "events_normalized.parquet"
    lineups_path = tmp_path / "lineups_normalized.parquet"
    lineups_path.write_text("x", encoding="utf-8")
    written: dict[str, object] = {}

    monkeypatch.setattr(build_events_normalized, "DEFAULT_EVENTS_RAW_PATH", tmp_path / "events.parquet")
    monkeypatch.setattr(build_events_normalized, "DEFAULT_EVENTS_NORMALIZED_PATH", output_path)
    monkeypatch.setattr(build_events_normalized, "DEFAULT_LINEUPS_NORMALIZED_PATH", lineups_path)
    monkeypatch.setattr(build_events_normalized, "load_events", lambda default_path: input_df)
    monkeypatch.setattr(build_events_normalized, "normalize_events", lambda df: normalized_df.copy())
    monkeypatch.setattr(build_events_normalized, "add_derived_event_columns", lambda df: df.assign(action_length=1))
    monkeypatch.setattr(build_events_normalized, "load_lineups", lambda path: lineups_df)
    monkeypatch.setattr(build_events_normalized, "is_normalized_lineups_df", lambda df: True)
    monkeypatch.setattr(
        build_events_normalized,
        "enrich_events_with_lineups",
        lambda events_df, loaded_lineups_df: events_df.assign(player_nickname="Alpha"),
    )

    def _fake_to_parquet(self, path, index=False):
        written["path"] = path
        written["index"] = index
        written["df"] = self.copy()

    monkeypatch.setattr(pd.DataFrame, "to_parquet", _fake_to_parquet, raising=False)

    build_events_normalized.main()

    output = capsys.readouterr().out
    assert written["path"] == output_path
    assert written["index"] is False
    assert "Lineups usados para enriquecer" in output
    assert written["df"].loc[0, "player_nickname"] == "Alpha"


def test_build_lineups_normalized_main_reads_processed_or_raw_and_writes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    raw_processed_path = tmp_path / "lineups.parquet"
    raw_processed_path.write_text("x", encoding="utf-8")
    normalized_path = tmp_path / "lineups_normalized.parquet"
    lineups_df = pd.DataFrame([{"match_id": 1, "player": "A"}])
    written: dict[str, object] = {}

    monkeypatch.setattr(build_lineups_normalized, "DEFAULT_LINEUPS_RAW_PATH", raw_processed_path)
    monkeypatch.setattr(build_lineups_normalized, "DEFAULT_LINEUPS_NORMALIZED_PATH", normalized_path)
    monkeypatch.setattr(build_lineups_normalized, "RAW_LINEUPS_DIR", tmp_path / "raw_lineups")
    monkeypatch.setattr(build_lineups_normalized, "load_lineups", lambda path: lineups_df)
    monkeypatch.setattr(build_lineups_normalized, "load_lineups_from_json_dir", lambda path: pd.DataFrame())
    monkeypatch.setattr(build_lineups_normalized, "normalize_lineups_df", lambda df: df.assign(player="A"))

    def _fake_to_parquet(self, path, index=False):
        written["path"] = path
        written["df"] = self.copy()

    monkeypatch.setattr(pd.DataFrame, "to_parquet", _fake_to_parquet, raising=False)

    build_lineups_normalized.main()

    output = capsys.readouterr().out
    assert written["path"] == normalized_path
    assert "Jugadores" in output
    assert written["df"].loc[0, "player"] == "A"


def test_build_lineups_normalized_main_falls_back_to_raw_json_dir(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    normalized_path = tmp_path / "lineups_normalized.parquet"
    called: list[str] = []

    monkeypatch.setattr(build_lineups_normalized, "DEFAULT_LINEUPS_RAW_PATH", tmp_path / "missing.parquet")
    monkeypatch.setattr(build_lineups_normalized, "DEFAULT_LINEUPS_NORMALIZED_PATH", normalized_path)
    monkeypatch.setattr(build_lineups_normalized, "RAW_LINEUPS_DIR", tmp_path / "raw_lineups")
    monkeypatch.setattr(build_lineups_normalized, "load_lineups", lambda path: pd.DataFrame())
    monkeypatch.setattr(
        build_lineups_normalized,
        "load_lineups_from_json_dir",
        lambda path: called.append("raw") or pd.DataFrame([{"match_id": 1}]),
    )
    monkeypatch.setattr(build_lineups_normalized, "normalize_lineups_df", lambda df: df.assign(player="A"))
    monkeypatch.setattr(pd.DataFrame, "to_parquet", lambda self, path, index=False: None, raising=False)

    build_lineups_normalized.main()

    assert called == ["raw"]


def test_optimize_three_sixty_df_casts_supported_columns():
    df = pd.DataFrame([{"player": "A", "team": "Spain", "x": "1", "y": "2", "match_id": "3", "player_id": "4"}])

    result = build_three_sixty_normalized.optimize_three_sixty_df(df)

    assert str(result["player"].dtype) == "category"
    assert str(result["x"].dtype) == "float32"
    assert str(result["match_id"].dtype) == "Int32"


def test_build_three_sixty_normalized_main_uses_available_source_and_writes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    raw_path = tmp_path / "three_sixty.parquet"
    raw_path.write_text("x", encoding="utf-8")
    normalized_path = tmp_path / "three_sixty_normalized.parquet"
    raw_df = pd.DataFrame([{"event_id": "e1", "match_id": 1, "player_id": 2, "player": "A", "team": "Spain", "x": 1, "y": 2}])
    written: dict[str, object] = {}

    monkeypatch.setattr(build_three_sixty_normalized, "DEFAULT_THREE_SIXTY_RAW_PATH", raw_path)
    monkeypatch.setattr(build_three_sixty_normalized, "RAW_THREE_SIXTY_DIR", tmp_path / "raw_three_sixty")
    monkeypatch.setattr(build_three_sixty_normalized, "DEFAULT_THREE_SIXTY_NORMALIZED_PATH", normalized_path)
    monkeypatch.setattr(build_three_sixty_normalized, "load_freeze_frames", lambda source_path: raw_df)
    monkeypatch.setattr(build_three_sixty_normalized, "normalize_freeze_frame_df", lambda df: df.copy())

    def _fake_to_parquet(self, path, index=False):
        written["path"] = path
        written["df"] = self.copy()

    monkeypatch.setattr(pd.DataFrame, "to_parquet", _fake_to_parquet, raising=False)

    build_three_sixty_normalized.main()

    output = capsys.readouterr().out
    assert written["path"] == normalized_path
    assert "Eventos" in output
    assert written["df"].loc[0, "event_id"] == "e1"


def test_build_normalized_dataset_module_reexports_main():
    assert build_normalized_dataset.main is build_events_normalized.main
