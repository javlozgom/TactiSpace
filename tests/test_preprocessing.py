import pandas as pd
import pytest

from src.preprocessing import add_derived_event_columns, infer_duel_outcomes, normalize_events


def test_normalize_events_creates_timestamp():
    df = pd.DataFrame(
        [
            {
                "match_id": 1,
                "team": "A",
                "player": "P1",
                "minute": "1",
                "second": "30",
                "event_type": "Pass",
                "outcome": "Successful",
                "x": "10",
                "y": "20",
                "end_x": "30",
                "end_y": "40",
                "possession_id": 1,
            }
        ]
    )

    result = normalize_events(df)

    assert "timestamp" in result.columns
    assert "inferred_outcome" in result.columns
    assert result.loc[0, "timestamp"] == 90


def test_normalize_events_preserves_events_without_coordinates_or_player():
    df = pd.DataFrame(
        [
            {
                "match_id": 3930172,
                "team": "Italy",
                "player": "Riccardo Calafiori",
                "minute": 54,
                "second": 4,
                "event_type": "Own Goal Against",
                "outcome": "Own Goal Against",
                "x": None,
                "y": None,
                "end_x": None,
                "end_y": None,
                "possession_id": None,
            },
            {
                "match_id": 3930172,
                "team": "Spain",
                "player": None,
                "minute": 54,
                "second": 4,
                "event_type": "Own Goal For",
                "outcome": "Own Goal For",
                "x": None,
                "y": None,
                "end_x": None,
                "end_y": None,
                "possession_id": None,
            },
        ]
    )

    result = normalize_events(df)

    assert len(result) == 2
    assert set(result["event_type"]) == {"Own Goal Against", "Own Goal For"}
    assert result.loc[result["event_type"] == "Own Goal For", "player"].iloc[0] == "Unknown"
    assert result["timestamp"].tolist() == [3244, 3244]


def test_normalize_events_raises_when_columns_are_missing():
    df = pd.DataFrame([{"match_id": 1, "team": "A"}])

    with pytest.raises(ValueError, match="Faltan columnas obligatorias"):
        normalize_events(df)


def test_infer_duel_outcomes_marks_won_and_lost():
    df = pd.DataFrame(
        [
            {
                "match_id": 1,
                "team": "Spain",
                "player": "Rodri",
                "minute": 1,
                "second": 0,
                "timestamp": 60,
                "event_type": "Duel",
                "outcome": "Unknown",
                "x": 10,
                "y": 20,
                "end_x": 10,
                "end_y": 20,
                "possession_id": 1,
            },
            {
                "match_id": 1,
                "team": "Spain",
                "player": "Pedri",
                "minute": 1,
                "second": 2,
                "timestamp": 62,
                "event_type": "Pass",
                "outcome": "Successful",
                "x": 15,
                "y": 25,
                "end_x": 20,
                "end_y": 30,
                "possession_id": 1,
            },
            {
                "match_id": 1,
                "team": "Italy",
                "player": "Barella",
                "minute": 2,
                "second": 0,
                "timestamp": 120,
                "event_type": "Duel",
                "outcome": "Unknown",
                "x": 40,
                "y": 50,
                "end_x": 40,
                "end_y": 50,
                "possession_id": 2,
            },
            {
                "match_id": 1,
                "team": "Spain",
                "player": "Le Normand",
                "minute": 2,
                "second": 1,
                "timestamp": 121,
                "event_type": "Recovery",
                "outcome": "Won",
                "x": 42,
                "y": 48,
                "end_x": 42,
                "end_y": 48,
                "possession_id": 3,
            },
        ]
    )

    result = infer_duel_outcomes(df)

    assert result.loc[0, "inferred_outcome"] == "Won"
    assert result.loc[2, "inferred_outcome"] == "Lost"


def test_add_derived_event_columns_creates_expected_flags():
    df = pd.DataFrame(
        [
            {
                "event_type": "Pass",
                "outcome": "Successful",
                "x": 30,
                "y": 20,
                "end_x": 85,
                "end_y": 30,
            },
            {
                "event_type": "Dribble",
                "outcome": "Incomplete",
                "x": 90,
                "y": 40,
                "end_x": 105,
                "end_y": 40,
            },
            {
                "event_type": "Miscontrol",
                "outcome": "Lost",
                "x": 10,
                "y": 15,
                "end_x": 10,
                "end_y": 15,
            },
        ]
    )

    result = add_derived_event_columns(df)

    assert {"is_successful", "is_failed", "action_length", "is_progressive", "to_final_third", "box_entry", "field_zone", "loss_type"}.issubset(result.columns)
    assert bool(result.loc[0, "is_successful"]) is True
    assert bool(result.loc[1, "is_failed"]) is True
    assert round(float(result.loc[0, "action_length"]), 2) > 0
    assert bool(result.loc[0, "is_progressive"]) is True
    assert bool(result.loc[0, "to_final_third"]) is True
    assert bool(result.loc[1, "box_entry"]) is True
    assert result.loc[0, "field_zone"] == "Tercio defensivo"
    assert result.loc[1, "field_zone"] == "Tercio ofensivo"
    assert result.loc[1, "loss_type"] == "Failed Dribble"
    assert result.loc[2, "loss_type"] == "Miscontrol"
