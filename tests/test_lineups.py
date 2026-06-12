import pandas as pd

from src.lineups import (
    enrich_events_with_lineups,
    is_normalized_lineups_df,
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
