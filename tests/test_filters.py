import pandas as pd

from src.filters import filter_events


def build_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"match_id": 1, "team": "Spain", "player": "Rodri", "minute": 10, "event_type": "Pass"},
            {"match_id": 1, "team": "Spain", "player": "Pedri", "minute": 12, "event_type": "Shot"},
            {"match_id": 2, "team": "Italy", "player": "Barella", "minute": 15, "event_type": "Carry"},
        ]
    )


def test_filter_by_match():
    result = filter_events(build_df(), match_id="1")
    assert len(result) == 2
    assert set(result["match_id"]) == {1}


def test_filter_by_team():
    result = filter_events(build_df(), team="Spain")
    assert len(result) == 2
    assert set(result["team"]) == {"Spain"}


def test_filter_by_player():
    result = filter_events(build_df(), player="Barella")
    assert len(result) == 1
    assert result.iloc[0]["player"] == "Barella"


def test_filter_by_event_type():
    result = filter_events(build_df(), event_type="Shot")
    assert len(result) == 1
    assert result.iloc[0]["event_type"] == "Shot"
