from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pandas as pd
import pytest


def _load_dataset_builder_module():
    script_path = Path(__file__).resolve().parents[2] / "scripts" / "01_build_dataset.py"
    spec = importlib.util.spec_from_file_location("build_dataset_script", script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_safe_get_and_location_helpers():
    module = _load_dataset_builder_module()

    assert module.safe_get({"a": {"b": 3}}, "a", "b") == 3
    assert module.safe_get({"a": {}}, "a", "b", default="x") == "x"
    assert module.parse_location([1, 2]) == (1.0, 2.0)
    assert module.parse_location(["3", "4"]) == (3.0, 4.0)
    assert module.parse_location(["x", 2]) == (None, None)
    assert module.parse_location(None) == (None, None)


def test_pick_end_location_supports_multiple_event_types():
    module = _load_dataset_builder_module()

    assert module.pick_end_location({"type": {"name": "Pass"}, "pass": {"end_location": [10, 20]}}) == (10.0, 20.0)
    assert module.pick_end_location({"type": {"name": "Carry"}, "carry": {"end_location": [11, 21]}}) == (11.0, 21.0)
    assert module.pick_end_location({"type": {"name": "Shot"}, "shot": {"end_location": [12, 22]}}) == (12.0, 22.0)
    assert module.pick_end_location({"type": {"name": "Clearance"}, "clearance": {"end_location": [13, 23]}}) == (
        13.0,
        23.0,
    )
    assert module.pick_end_location({"type": {"name": "Duel"}}) == (None, None)


def test_event_field_extractors_cover_specific_payloads():
    module = _load_dataset_builder_module()
    event = {
        "id": "evt-1",
        "index": 8,
        "period": 1,
        "timestamp": "00:10:00.000",
        "minute": 10,
        "second": 3,
        "type": {"name": "Pass"},
        "possession": 7,
        "possession_team": {"name": "Spain"},
        "team": {"name": "Spain"},
        "player": {"name": "Player A"},
        "position": {"name": "CM"},
        "play_pattern": {"name": "Regular Play"},
        "location": [30, 40],
        "under_pressure": True,
        "out": False,
        "off_camera": False,
        "pass": {
            "recipient": {"name": "Player B"},
            "length": 15,
            "angle": 0.5,
            "height": {"name": "Ground Pass"},
            "type": {"name": "Simple Pass"},
            "body_part": {"name": "Right Foot"},
            "outcome": {"name": "Complete"},
            "assisted_shot_id": "shot-1",
            "switch": True,
            "cross": False,
            "cut_back": False,
            "through_ball": True,
            "end_location": [45, 50],
        },
    }

    row = module.event_to_row(event, 123)

    assert row["match_id"] == 123
    assert row["event_id"] == "evt-1"
    assert row["team"] == "Spain"
    assert row["player"] == "Player A"
    assert row["x"] == 30.0
    assert row["end_x"] == 45.0
    assert row["pass_recipient"] == "Player B"
    assert row["pass_outcome"] == "Complete"
    assert row["pass_switch"] is True


def test_event_to_row_supports_shot_carry_and_dribble():
    module = _load_dataset_builder_module()

    shot_row = module.event_to_row(
        {
            "type": {"name": "Shot"},
            "shot": {
                "outcome": {"name": "Goal"},
                "statsbomb_xg": 0.5,
                "body_part": {"name": "Right Foot"},
                "type": {"name": "Open Play"},
                "technique": {"name": "Volley"},
                "first_time": True,
            },
        },
        1,
    )
    carry_row = module.event_to_row(
        {"type": {"name": "Carry"}, "carry": {"length": 7, "end_location": [20, 25]}},
        1,
    )
    dribble_row = module.event_to_row(
        {"type": {"name": "Dribble"}, "dribble": {"outcome": {"name": "Complete"}, "nutmeg": True}},
        1,
    )

    assert shot_row["shot_outcome"] == "Goal"
    assert shot_row["shot_first_time"] is True
    assert carry_row["carry_length"] == 7
    assert carry_row["carry_end_location"] == [20, 25]
    assert dribble_row["dribble_outcome"] == "Complete"
    assert dribble_row["dribble_nutmeg"] is True


def test_read_and_discover_event_files(tmp_path: Path):
    module = _load_dataset_builder_module()
    events_dir = tmp_path / "competition" / "events"
    events_dir.mkdir(parents=True)
    first = events_dir / "123.json"
    first.write_text(json.dumps([{"id": "1"}]), encoding="utf-8")
    second = events_dir / "456.json"
    second.write_text(json.dumps([{"id": "2"}]), encoding="utf-8")

    found = list(module.iter_event_files(tmp_path))

    assert found == [first, second]
    assert module.read_events_file(first) == [{"id": "1"}]
    assert module.infer_match_id_from_filename(first) == 123


def test_infer_match_id_from_filename_raises_for_invalid_name():
    module = _load_dataset_builder_module()

    with pytest.raises(ValueError):
        module.infer_match_id_from_filename(Path("abc.json"))


def test_build_events_dataset_parses_files_and_applies_numeric_cleanup(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    module = _load_dataset_builder_module()
    events_dir = tmp_path / "open-data" / "events"
    events_dir.mkdir(parents=True)
    event_file = events_dir / "999.json"
    event_file.write_text(
        json.dumps(
            [
                {
                    "id": "evt-1",
                    "index": "1",
                    "period": "1",
                    "minute": "10",
                    "second": "5",
                    "type": {"name": "Pass"},
                    "team": {"name": "Spain"},
                    "player": {"name": "Player A"},
                    "location": [1, 2],
                    "pass": {"end_location": [3, 4], "length": "12.5", "angle": "0.4"},
                }
            ]
        ),
        encoding="utf-8",
    )

    df = module.build_events_dataset(tmp_path, verbose=True)

    output = capsys.readouterr().out
    assert len(df) == 1
    assert df.loc[0, "match_id"] == 999
    assert df.loc[0, "minute"] == 10
    assert df.loc[0, "pass_length"] == 12.5
    assert "parsed" in output


def test_build_events_dataset_raises_when_no_files_exist(tmp_path: Path):
    module = _load_dataset_builder_module()

    with pytest.raises(FileNotFoundError):
        module.build_events_dataset(tmp_path)


def test_find_repo_root_and_ensure_dirs(tmp_path: Path):
    module = _load_dataset_builder_module()
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / ".git").mkdir()
    nested = repo_root / "a" / "b"
    nested.mkdir(parents=True)

    assert module.find_repo_root(nested) == repo_root

    output_dir = tmp_path / "new" / "tree"
    module.ensure_dirs(output_dir)
    assert output_dir.exists()


def test_main_writes_csv_output(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    module = _load_dataset_builder_module()
    raw_dir = tmp_path / "raw"
    out_path = tmp_path / "processed" / "events.csv"

    monkeypatch.setattr(
        module,
        "build_events_dataset",
        lambda raw_dir, limit_files=None, verbose=False: pd.DataFrame(
            [{"type": "Dribble", "dribble_outcome": "Complete"}]
        ),
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "01_build_dataset.py",
            "--raw-dir",
            str(raw_dir),
            "--out",
            str(out_path),
            "--format",
            "csv",
        ],
    )

    module.main()

    assert out_path.exists()
    result = pd.read_csv(out_path)
    assert result.loc[0, "dribble_outcome"] == "Complete"
