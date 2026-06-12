from pathlib import Path

import pandas as pd

from src.data_loader import is_normalized_events_df, load_events


def test_is_normalized_events_df_returns_true_with_minimum_columns():
    df = pd.DataFrame(
        [
            {
                "timestamp": 90,
                "match_id": 1,
                "team": "A",
                "player": "P1",
                "minute": 1,
                "second": 30,
                "event_type": "Pass",
                "x": 10.0,
                "y": 20.0,
            }
        ]
    )

    assert is_normalized_events_df(df) is True


def test_is_normalized_events_df_returns_false_without_timestamp():
    df = pd.DataFrame(
        [
            {
                "match_id": 1,
                "team": "A",
                "player": "P1",
                "minute": 1,
                "second": 30,
                "event_type": "Pass",
                "x": 10.0,
                "y": 20.0,
            }
        ]
    )

    assert is_normalized_events_df(df) is False


def test_load_events_returns_normalized_parquet_as_is(tmp_path: Path):
    parquet_path = tmp_path / "events_normalized.parquet"
    source_df = pd.DataFrame(
        [
            {
                "timestamp": 90,
                "match_id": 1,
                "team": "A",
                "player": "P1",
                "minute": 1,
                "second": 30,
                "event_type": "Pass",
                "outcome": "Successful",
                "x": 10.0,
                "y": 20.0,
                "end_x": 20.0,
                "end_y": 25.0,
                "possession_id": 1,
            }
        ]
    )
    source_df.to_parquet(parquet_path, index=False)

    loaded_df = load_events(default_path=parquet_path)

    assert is_normalized_events_df(loaded_df) is True
    assert loaded_df.loc[0, "timestamp"] == 90


def test_load_events_keeps_uncommon_event_types_in_default_dataset(tmp_path: Path):
    parquet_path = tmp_path / "events.parquet"
    source_df = pd.DataFrame(
        [
            {
                "match_id": 3930172,
                "event_id": "evt-1",
                "team": "Italy",
                "player": "Riccardo Calafiori",
                "player_nickname": None,
                "position": "Center Back",
                "minute": 54,
                "second": 4,
                "type": "Own Goal Against",
                "pass_outcome": None,
                "dribble_outcome": None,
                "shot_outcome": None,
                "x": None,
                "y": None,
                "end_x": None,
                "end_y": None,
                "possession": 12,
            }
        ]
    )
    source_df.to_parquet(parquet_path, index=False)

    loaded_df = load_events(default_path=parquet_path)

    assert len(loaded_df) == 1
    assert loaded_df.loc[0, "event_type"] == "Own Goal Against"
    assert loaded_df.loc[0, "outcome"] == "Own Goal Against"
