import pandas as pd

from src.lineups import (
    enrich_events_with_lineups,
    is_normalized_lineups_df,
    load_lineups,
    load_lineups_from_json_dir,
    normalize_lineups_df,
)


def test_normalize_lineups_df_returns_expected_columns():
    source_df = pd.DataFrame(
        [
            {
                "match_id": "1",
                "team_name": "Blue",
                "lineup": [
                    {
                        "player_id": 10,
                        "player_name": "Keeper",
                        "player_nickname": "GK",
                        "jersey_number": 1,
                        "positions": [{"position": "Goalkeeper"}],
                    }
                ],
            }
        ]
    )

    normalized_df = normalize_lineups_df(source_df)

    assert {"match_id", "team", "player", "position_group"}.issubset(normalized_df.columns)
    assert normalized_df.loc[0, "player"] == "Keeper"


def test_position_group_is_assigned_correctly():
    source_df = pd.DataFrame(
        [
            {"match_id": "1", "team": "Blue", "player": "A", "position": "Goalkeeper"},
            {"match_id": "1", "team": "Blue", "player": "B", "position": "Center Back"},
            {"match_id": "1", "team": "Blue", "player": "C", "position": "Central Midfield"},
            {"match_id": "1", "team": "Blue", "player": "D", "position": "Right Wing"},
        ]
    )

    normalized_df = normalize_lineups_df(source_df)

    assert normalized_df.loc[0, "position_group"] == "Portero"
    assert normalized_df.loc[1, "position_group"] == "Defensa"
    assert normalized_df.loc[2, "position_group"] == "Mediocentro"
    assert normalized_df.loc[3, "position_group"] == "Atacante"


def test_enrich_events_with_lineups_adds_position_group_without_duplication():
    events_df = pd.DataFrame(
        [
            {"match_id": "1", "team": "Blue", "player": "Rodri", "event_type": "Pass", "position_group": None},
            {"match_id": "1", "team": "Blue", "player": "Rodri", "event_type": "Shot", "position_group": None},
        ]
    )
    lineups_df = pd.DataFrame(
        [
            {
                "match_id": "1",
                "team": "Blue",
                "player_id": 100,
                "player": "Rodri",
                "player_nickname": "Rodri",
                "jersey_number": 16,
                "position": "Central Midfield",
                "position_group": "Mediocentro",
                "raw_position": "Central Midfield",
            }
        ]
    )

    enriched_df = enrich_events_with_lineups(events_df, lineups_df)

    assert len(enriched_df) == len(events_df)
    assert enriched_df["position_group"].eq("Mediocentro").all()


def test_is_normalized_lineups_df_checks_minimum_columns():
    valid_df = pd.DataFrame([{"match_id": "1", "team": "Blue", "player": "A", "position_group": "Defensa"}])
    invalid_df = pd.DataFrame([{"match_id": "1", "team": "Blue", "player": "A"}])

    assert is_normalized_lineups_df(valid_df) is True
    assert is_normalized_lineups_df(invalid_df) is False


def test_normalize_lineups_df_handles_empty_and_flat_schema_variants():
    empty_result = normalize_lineups_df(pd.DataFrame())
    flat_df = pd.DataFrame(
        [
            {
                "match_id": 1,
                "team_name": " Blue ",
                "player.id": "10",
                "player.name": " Rodri ",
                "player.nickname": " R ",
                "jersey_number": "16",
                "position.name": "Defensive Midfield",
            }
        ]
    )

    flat_result = normalize_lineups_df(flat_df)

    assert empty_result.columns.tolist() == [
        "match_id",
        "team",
        "player_id",
        "player",
        "player_nickname",
        "jersey_number",
        "position",
        "position_group",
        "raw_position",
    ]
    assert flat_result.loc[0, "team"] == "Blue"
    assert flat_result.loc[0, "player"] == "Rodri"
    assert flat_result.loc[0, "position_group"] == "Mediocentro"


def test_load_lineups_handles_missing_invalid_and_csv_inputs(tmp_path):
    missing = load_lineups(tmp_path / "missing.csv")
    broken_path = tmp_path / "broken.csv"
    broken_path.write_text('"unterminated', encoding="utf-8")
    broken = load_lineups(broken_path)

    csv_path = tmp_path / "lineups.csv"
    pd.DataFrame(
        [
            {"match_id": "1", "team": "Blue", "player": "Rodri", "position_group": "Mediocentro"},
        ]
    ).to_csv(csv_path, index=False)
    loaded = load_lineups(csv_path)

    assert missing.empty
    assert broken.empty
    assert loaded.loc[0, "player"] == "Rodri"


def test_load_lineups_from_json_dir_handles_missing_invalid_and_valid_files(tmp_path):
    missing = load_lineups_from_json_dir(tmp_path / "missing")

    raw_dir = tmp_path / "lineups"
    raw_dir.mkdir()
    (raw_dir / "bad.json").write_text("{not-json}", encoding="utf-8")
    pd.DataFrame(
        [
            {
                "team_name": "Blue",
                "lineup": [
                    {
                        "player_id": 1,
                        "player_name": "Keeper",
                        "player_nickname": None,
                        "jersey_number": 1,
                        "positions": [{"position": "Goalkeeper"}],
                    }
                ],
            }
        ]
    ).to_json(raw_dir / "123.json")

    loaded = load_lineups_from_json_dir(raw_dir)

    assert missing.empty
    assert loaded.loc[0, "match_id"] == "123"
    assert loaded.loc[0, "position_group"] == "Portero"


def test_enrich_events_with_lineups_handles_missing_team_and_player_id_merge():
    events_df = pd.DataFrame(
        [
            {"match_id": "1", "player": "Rodri", "player_id": 10, "position_group": None, "position": None, "player_nickname": None},
        ]
    )
    lineups_df = pd.DataFrame(
        [
            {
                "match_id": "1",
                "team": "Blue",
                "player_id": 10,
                "player": "Rodri",
                "player_nickname": "R",
                "jersey_number": 16,
                "position": "Central Midfield",
                "position_group": "Mediocentro",
                "raw_position": "Central Midfield",
            }
        ]
    )

    enriched = enrich_events_with_lineups(events_df, lineups_df)

    assert enriched.loc[0, "position_group"] == "Mediocentro"
    assert enriched.loc[0, "player_nickname"] == "R"
    assert enriched.loc[0, "position"] == "Central Midfield"
