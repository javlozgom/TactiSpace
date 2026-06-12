from __future__ import annotations

from collections import Counter

import pandas as pd


DEFAULT_POSITION = "Atacante"

POSITION_EVENT_PRIORITIES = {
    "Portero": [
        "Goal Keeper",
        "Pass",
        "Ball Receipt*",
        "Clearance",
        "Ball Recovery",
        "Error",
    ],
    "Defensa": [
        "Pass",
        "Ball Recovery",
        "Duel",
        "Interception",
        "Clearance",
        "Block",
    ],
    "Mediocentro": [
        "Ball Receipt*",
        "Pass",
        "Carry",
        "Pressure",
        "Ball Recovery",
        "Duel",
    ],
    "Atacante": [
        "Shot",
        "Ball Receipt*",
        "Dribble",
        "Carry",
        "Pass",
        "Dispossessed",
    ],
}

EVENT_DESCRIPTIONS = {
    "Goal Keeper": "Acciones específicas del portero: paradas, salidas y gestión del área.",
    "Pass": "Distribución del balón y dirección de los pases.",
    "Ball Receipt*": "Zonas donde el jugador recibe el balón.",
    "Clearance": "Despejes y acciones defensivas para alejar el peligro.",
    "Ball Recovery": "Recuperaciones de balón y zonas de reconquista.",
    "Error": "Errores que pueden generar situaciones de peligro.",
    "Duel": "Disputas individuales por la posesión.",
    "Interception": "Anticipaciones y cortes de líneas de pase.",
    "Block": "Bloqueos de tiros, pases o acciones rivales.",
    "Carry": "Conducciones y progresiones con balón.",
    "Pressure": "Acciones de presión sobre el rival.",
    "Shot": "Finalizaciones y zonas de remate.",
    "Dribble": "Regates e intentos de superar rivales.",
    "Dispossessed": "Pérdidas de balón por entrada o presión rival.",
}

POSITION_NORMALIZATION = {
    "gk": "Portero",
    "goalkeeper": "Portero",
    "goal keeper": "Portero",
    "portero": "Portero",
    "df": "Defensa",
    "defender": "Defensa",
    "centre back": "Defensa",
    "center back": "Defensa",
    "left back": "Defensa",
    "right back": "Defensa",
    "defensa": "Defensa",
    "mf": "Mediocentro",
    "midfielder": "Mediocentro",
    "defensive midfield": "Mediocentro",
    "central midfield": "Mediocentro",
    "attacking midfield": "Mediocentro",
    "mediocentro": "Mediocentro",
    "centrocampista": "Mediocentro",
    "fw": "Atacante",
    "forward": "Atacante",
    "striker": "Atacante",
    "winger": "Atacante",
    "left wing": "Atacante",
    "right wing": "Atacante",
    "atacante": "Atacante",
    "delantero": "Atacante",
    "extremo": "Atacante",
}


def _normalize_position_name(position_value: object) -> str | None:
    """Map raw position labels to one of the supported app positions."""
    if position_value is None or pd.isna(position_value):
        return None

    raw_value = str(position_value).strip()
    if not raw_value:
        return None

    normalized_key = raw_value.lower()
    if normalized_key in POSITION_NORMALIZATION:
        return POSITION_NORMALIZATION[normalized_key]

    if "goalkeeper" in normalized_key or "goal keeper" in normalized_key:
        return "Portero"
    if "wing back" in normalized_key or "back" in normalized_key:
        return "Defensa"
    if "midfield" in normalized_key or "midfielder" in normalized_key:
        return "Mediocentro"
    if "forward" in normalized_key or "wing" in normalized_key or "striker" in normalized_key:
        return "Atacante"

    return None


def _infer_position_from_events(player_df: pd.DataFrame) -> str:
    """Infer a broad position bucket from the player's event profile."""
    event_counts = player_df["event_type"].astype(str).value_counts()

    goalkeeper_score = int(event_counts.get("Goal Keeper", 0))
    defensive_score = sum(
        int(event_counts.get(event_type, 0))
        for event_type in ["Clearance", "Block", "Interception", "Duel", "Ball Recovery"]
    )
    midfield_score = sum(
        int(event_counts.get(event_type, 0))
        for event_type in ["Pass", "Ball Receipt*", "Carry", "Pressure"]
    )
    attacking_score = sum(
        int(event_counts.get(event_type, 0))
        for event_type in ["Shot", "Dribble", "Dispossessed", "Foul Won"]
    )

    if goalkeeper_score >= max(defensive_score, midfield_score, attacking_score, 1):
        return "Portero"
    if defensive_score > attacking_score and defensive_score >= midfield_score:
        return "Defensa"
    if midfield_score >= attacking_score and midfield_score >= defensive_score:
        return "Mediocentro"
    if attacking_score > 0:
        return "Atacante"

    return DEFAULT_POSITION


def get_position_for_player(df: pd.DataFrame, player_name: str | None) -> str:
    """Detect the broad position for a selected player."""
    if player_name is None or not str(player_name).strip() or player_name == "Todos":
        return DEFAULT_POSITION
    if df.empty or "player" not in df.columns:
        return DEFAULT_POSITION

    player_df = df[df["player"] == player_name].copy()
    if player_df.empty:
        return DEFAULT_POSITION

    if "position_group" in player_df.columns:
        normalized_groups = [
            str(value).strip()
            for value in player_df["position_group"].dropna().tolist()
            if str(value).strip() in POSITION_EVENT_PRIORITIES
        ]
        if normalized_groups:
            return Counter(normalized_groups).most_common(1)[0][0]

    if "position" in player_df.columns:
        normalized_positions = [
            normalized
            for normalized in (
                _normalize_position_name(value) for value in player_df["position"].dropna().tolist()
            )
            if normalized is not None
        ]
        if normalized_positions:
            return Counter(normalized_positions).most_common(1)[0][0]

    return _infer_position_from_events(player_df)


def get_priority_events_for_position(position: str | None) -> list[str]:
    """Return the six priority event types for a given broad position."""
    if position not in POSITION_EVENT_PRIORITIES:
        return POSITION_EVENT_PRIORITIES[DEFAULT_POSITION]
    return POSITION_EVENT_PRIORITIES[position]


def get_priority_events_for_player(df: pd.DataFrame, player_name: str | None) -> tuple[str, list[str]]:
    """Return detected position plus the event priorities for that player."""
    detected_position = get_position_for_player(df, player_name)
    return detected_position, get_priority_events_for_position(detected_position)


def get_specific_position_for_player(df: pd.DataFrame, player_name: str | None) -> str | None:
    """Return the most frequent raw position label for a player when available."""
    if player_name is None or not str(player_name).strip() or player_name == "Todos":
        return None
    if df.empty or "player" not in df.columns or "position" not in df.columns:
        return None

    player_df = df[df["player"] == player_name].copy()
    if player_df.empty:
        return None

    raw_positions = [
        str(value).strip()
        for value in player_df["position"].dropna().tolist()
        if str(value).strip()
    ]
    if not raw_positions:
        return None

    return Counter(raw_positions).most_common(1)[0][0]
