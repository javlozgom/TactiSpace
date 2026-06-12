import pandas as pd

from src.core.rules.position_priorities import _normalize_position_name
from src.position_priorities import (
    DEFAULT_POSITION,
    get_specific_position_for_player,
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


def test_position_priority_helpers_cover_empty_group_and_event_inference():
    empty_df = pd.DataFrame()
    event_df = pd.DataFrame(
        [
            {"player": "Defensor", "event_type": "Clearance"},
            {"player": "Defensor", "event_type": "Block"},
            {"player": "Mediocentro", "event_type": "Pass"},
            {"player": "Mediocentro", "event_type": "Pressure"},
            {"player": "Portero", "event_type": "Goal Keeper"},
            {"player": "Portero", "event_type": "Pass"},
        ]
    )

    assert get_position_for_player(empty_df, "A") == DEFAULT_POSITION
    assert get_position_for_player(event_df, "Defensor") == "Defensa"
    assert get_position_for_player(event_df, "Mediocentro") == "Mediocentro"
    assert get_position_for_player(event_df, "Portero") == "Portero"


def test_position_priority_helpers_normalize_variants_and_specific_position():
    df = pd.DataFrame(
        [
            {"player": "Jugador", "position": "Wing Back", "event_type": "Pass"},
            {"player": "Jugador", "position": "Wing Back", "event_type": "Carry"},
            {"player": "Delantero", "position": "Striker", "event_type": "Shot"},
        ]
    )

    assert get_position_for_player(df, "Jugador") == "Defensa"
    assert get_position_for_player(df, "Delantero") == "Atacante"
    assert get_specific_position_for_player(df, "Jugador") == "Wing Back"
    assert get_specific_position_for_player(df, "Todos") is None
    assert get_specific_position_for_player(pd.DataFrame([{"player": "A"}]), "A") is None


def test_position_priority_private_normalization_and_default_branches():
    assert _normalize_position_name("Goal Keeper Sweeper") == "Portero"
    assert _normalize_position_name("Central Midfielder") == "Mediocentro"
    assert _normalize_position_name("Second Striker") == "Atacante"
    assert _normalize_position_name("") is None
    assert _normalize_position_name("Unknown") is None

    fallback_df = pd.DataFrame([{"player": "SinDatos", "position_group": "Otro", "position": None, "event_type": "Unknown"}])
    assert get_position_for_player(fallback_df, "SinDatos") == "Mediocentro"
    assert get_position_for_player(pd.DataFrame([{"player": "A"}]), "B") == DEFAULT_POSITION
    assert get_priority_events_for_position(None) == get_priority_events_for_position(DEFAULT_POSITION)
