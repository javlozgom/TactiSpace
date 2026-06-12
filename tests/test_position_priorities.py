import pandas as pd

from src.position_priorities import (
    DEFAULT_POSITION,
    get_position_for_player,
    get_priority_events_for_player,
    get_priority_events_for_position,
)


def test_todos_returns_default_position():
    df = pd.DataFrame([{"player": "Rodri", "position": "Midfielder", "event_type": "Pass"}])
    assert get_position_for_player(df, "Todos") == DEFAULT_POSITION


def test_gk_returns_portero():
    df = pd.DataFrame([{"player": "Unai Simon", "position": "GK", "event_type": "Goal Keeper"}])
    assert get_position_for_player(df, "Unai Simon") == "Portero"


def test_defender_returns_defensa():
    df = pd.DataFrame([{"player": "Laporte", "position": "Defender", "event_type": "Pass"}])
    assert get_position_for_player(df, "Laporte") == "Defensa"


def test_midfielder_returns_mediocentro():
    df = pd.DataFrame([{"player": "Rodri", "position": "Midfielder", "event_type": "Pass"}])
    assert get_position_for_player(df, "Rodri") == "Mediocentro"


def test_forward_returns_atacante():
    df = pd.DataFrame([{"player": "Morata", "position": "Forward", "event_type": "Shot"}])
    assert get_position_for_player(df, "Morata") == "Atacante"


def test_position_group_has_priority_over_position():
    df = pd.DataFrame(
        [{"player": "Rodri", "position": "Forward", "position_group": "Mediocentro", "event_type": "Pass"}]
    )
    assert get_position_for_player(df, "Rodri") == "Mediocentro"


def test_atacante_priorities_have_six_events():
    events = get_priority_events_for_position("Atacante")
    assert len(events) == 6


def test_unknown_position_falls_back_to_default():
    df = pd.DataFrame([{"player": "Jugador X", "position": "Mystery Role", "event_type": "Shot"}])
    detected_position, priority_events = get_priority_events_for_player(df, "Jugador X")

    assert detected_position == DEFAULT_POSITION
    assert priority_events == get_priority_events_for_position(DEFAULT_POSITION)
