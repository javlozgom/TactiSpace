from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.repositories.data_repository import (
    _load_player_nicknames,
    load_events,
    load_match_labels,
)


def test_load_player_nicknames_returns_empty_df_for_missing_directory(tmp_path: Path):
    result = _load_player_nicknames(tmp_path / "missing")

    assert result.empty
    assert result.columns.tolist() == ["match_id", "team", "player", "player_nickname"]


def test_load_player_nicknames_extracts_unique_rows_and_skips_invalid_files(tmp_path: Path):
    valid_payload = [
        {
            "team_name": "Spain",
            "lineup": [
                {"player_name": "Rodri", "player_nickname": "Rodri"},
                {"player_name": "Rodri", "player_nickname": "Duplicate should be ignored"},
                {"player_name": "Lamine Yamal", "player_nickname": "Lamine"},
                "not-a-dict",
            ],
        }
    ]
    (tmp_path / "123.json").write_text(json.dumps(valid_payload), encoding="utf-8")
    (tmp_path / "broken.json").write_text("{not-json}", encoding="utf-8")

    result = _load_player_nicknames(tmp_path)

    assert len(result) == 2
    assert result["match_id"].tolist() == [123, 123]
    assert result["player"].tolist() == ["Rodri", "Lamine Yamal"]
    assert result["player_nickname"].tolist() == ["Rodri", "Lamine"]


def test_load_events_raises_file_not_found_for_missing_default_path(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        load_events(default_path=tmp_path / "missing.csv")


def test_load_match_labels_returns_empty_dict_for_missing_file(tmp_path: Path):
    assert load_match_labels(tmp_path / "missing.json") == {}


def test_load_match_labels_raises_for_missing_required_columns(tmp_path: Path):
    matches_path = tmp_path / "matches.json"
    matches_path.write_text(
        json.dumps([{"match_id": 1, "match_date": "2024-06-15"}]),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Faltan columnas"):
        load_match_labels(matches_path)


def test_load_match_labels_formats_date_and_stage(tmp_path: Path):
    matches_path = tmp_path / "matches.json"
    matches_path.write_text(
        json.dumps(
            [
                {
                    "match_id": 1,
                    "match_date": "2024-06-15",
                    "home_team": {"home_team_name": "Spain"},
                    "away_team": {"away_team_name": "Croatia"},
                    "competition_stage": {"name": "Group Stage"},
                },
                {
                    "match_id": 2,
                    "match_date": "invalid-date",
                    "home_team": {},
                    "away_team": {},
                },
            ]
        ),
        encoding="utf-8",
    )

    result = load_match_labels(matches_path)

    assert result["1"] == "Spain vs Croatia | 15/06/2024 | Group Stage"
    assert result["2"] == "Local vs Visitante | invalid-date"
