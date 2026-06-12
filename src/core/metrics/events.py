from __future__ import annotations

import re

import pandas as pd

from src.core.metrics.basic import get_effective_outcome_series


SUCCESS_RATE_EVENTS = {
    "Pass",
    "Dribble",
    "Duel",
    "Goal Keeper",
    "Ball Receipt*",
    "Carry",
    "Pressure",
    "Ball Recovery",
    "Interception",
    "Block",
    "Clearance",
    "Foul Won",
}

SUCCESS_KEYWORDS = (
    "successful",
    "complete",
    "won",
    "goal",
    "saved",
    "success",
)
PASS_SUCCESS_KEYWORDS = ("successful", "complete")
DUEL_WIN_KEYWORDS = ("won", "success")
DUEL_LOSS_KEYWORDS = ("lost", "unsuccessful")
SUPPORTED_SPECIFIC_EVENTS = [
    "Pass",
    "Carry",
    "Shot",
    "Pressure",
    "Ball Recovery",
    "Duel",
    "Dribble",
    "Ball Receipt*",
    "Miscontrol",
    "Dispossessed",
    "Interception",
    "Clearance",
    "Block",
    "Goal Keeper",
    "Own Goal For",
    "Own Goal Against",
    "Offside",
]

INTERPRETATION_BY_EVENT = {
    "Pass": "Este bloque resume volumen, precision y progresion de los pases.",
    "Carry": "Este bloque mide la capacidad de progresar con balon mediante conducciones.",
    "Shot": "Este bloque resume la produccion de tiro y la localizacion de las finalizaciones.",
    "Pressure": "Este bloque describe la actividad sin balon y las zonas de presion.",
    "Duel": "Este bloque analiza disputas individuales y porcentaje de exito.",
    "Dribble": "Este bloque resume volumen de regates, exito y presencia en zonas avanzadas.",
    "Ball Recovery": "Este bloque resume donde recupera el jugador y con que frecuencia aparece en campo rival.",
}

EVENT_ANALYSIS_DESCRIPTIONS = {
    "Pass": "Analiza volumen, precisión, dirección y progresión de los pases.",
    "Carry": "Mide la capacidad de progresar con balón mediante conducciones.",
    "Shot": "Resume la producción de tiro y la localización de las finalizaciones.",
    "Pressure": "Describe la actividad sin balón y las zonas donde se presiona al rival.",
    "Ball Recovery": "Muestra dónde se recupera la posesión del balón.",
    "Duel": "Analiza disputas individuales y porcentaje de éxito.",
    "Dribble": "Evalúa intentos de superar rivales mediante regate.",
    "Ball Receipt*": "Muestra las zonas donde el jugador recibe el balón.",
    "Miscontrol": "Identifica controles defectuosos o errores técnicos en recepción.",
    "Dispossessed": "Localiza pérdidas de balón provocadas por la presión o entrada rival.",
    "Interception": "Mide anticipaciones y cortes de líneas de pase.",
    "Clearance": "Muestra despejes y acciones para alejar el peligro.",
    "Block": "Analiza bloqueos de tiros, pases o acciones rivales.",
    "Goal Keeper": "Agrupa acciones específicas del portero.",
    "Own Goal For": "Goles en propia a favor del equipo: acciones en las que el rival introduce el balón en su propia portería.",
    "Own Goal Against": "Goles en propia en contra: acciones en las que el propio equipo introduce el balón en su portería.",
    "Offside": "Fueras de juego señalados durante acciones ofensivas.",
}

METRIC_DEFINITIONS = {
    "% acierto": "Proporción de acciones exitosas sobre el total de acciones evaluables.",
    "Pase progresivo": "Pase cuyo destino avanza al menos 10 metros en el eje X.",
    "Carry progresivo": "Conducción cuyo destino avanza al menos 10 metros en el eje X.",
    "Último tercio": "Zona del campo con x >= 80.",
    "Entrada al área": "Acción cuyo destino termina en x >= 102 e y entre 18 y 62.",
    "Campo propio": "Eventos con x < 60.",
    "Campo rival": "Eventos con x >= 60.",
    "Distancia media": "Distancia euclídea entre punto inicial y punto final de la acción.",
    "Tasa de tiro": "Proporción de secuencias que terminan en un tiro.",
    "Tasa de pérdida": "Proporción de secuencias que terminan en pérdida.",
    "Tasa de recuperación": "Proporción de secuencias que terminan en recuperación.",
}

METRIC_DISPLAY_NAMES = {
    "total_events": "Eventos totales",
    "successful_events": "Acciones exitosas",
    "success_rate": "% acierto",
    "average_x": "Posición media X",
    "average_y": "Posición media Y",
    "total_passes": "Pases totales",
    "completed_passes": "Pases completados",
    "incomplete_passes": "Pases fallidos",
    "completion_rate": "% acierto",
    "average_length": "Distancia media",
    "progressive_passes": "Pases progresivos",
    "final_third_passes": "Pases al último tercio",
    "box_entries": "Entradas al área",
    "total_carries": "Conducciones totales",
    "progressive_carries": "Conducciones progresivas",
    "final_third_carries": "Conducciones al último tercio",
    "carries_with_end_location": "Conducciones con destino válido",
    "total_shots": "Tiros totales",
    "goals": "Goles",
    "saved": "Parados",
    "off_target": "Fuera",
    "blocked": "Bloqueados",
    "average_distance_to_goal": "Distancia media a portería",
    "conversion_rate": "% conversión",
    "shot_on_target_rate": "% tiros a portería",
    "goals_per_shot": "Goles por tiro",
    "total_pressures": "Presiones totales",
    "pressures_in_opponent_half": "Presiones en campo rival",
    "pressures_in_final_third": "Presiones en último tercio",
    "total_duels": "Duelos totales",
    "duels_won": "Duelos ganados",
    "duels_lost": "Duelos perdidos",
    "win_rate": "% ganados",
    "total_dribbles": "Regates totales",
    "successful_dribbles": "Regates exitosos",
    "unsuccessful_dribbles": "Regates fallidos",
    "dribbles_in_final_third": "Regates en último tercio",
    "total_recoveries": "Recuperaciones totales",
    "recoveries_in_own_half": "Recuperaciones en campo propio",
    "recoveries_in_opponent_half": "Recuperaciones en campo rival",
    "recoveries_in_final_third": "Recuperaciones en último tercio",
    "show_success_rate": "Muestra % acierto",
    "info_label": "Lectura",
}


def _filter_event_df(df: pd.DataFrame, event_type: str) -> pd.DataFrame:
    """Return only rows matching the target event type."""
    if df.empty or "event_type" not in df.columns:
        return pd.DataFrame(columns=df.columns)
    return df[df["event_type"] == event_type].copy()


def _get_outcome_series(df: pd.DataFrame) -> pd.Series:
    """Return a normalized lower-case outcome series for matching."""
    if df.empty or not {"outcome", "inferred_outcome"}.intersection(df.columns):
        return pd.Series("", index=df.index, dtype="object")
    return get_effective_outcome_series(df).fillna("").astype(str).str.strip().str.lower()


def _contains_any(series: pd.Series, keywords: tuple[str, ...] | list[str]) -> pd.Series:
    """Check whether each string contains any keyword."""
    if series.empty:
        return pd.Series(dtype=bool, index=series.index)
    patterns = [re.compile(rf"\b{re.escape(keyword)}\b", flags=re.IGNORECASE) for keyword in keywords]
    return series.apply(lambda value: any(pattern.search(value) for pattern in patterns))


def _round_pct(value: float) -> float:
    """Round a percentage to one decimal place."""
    return round(float(value), 1)


def _round_distance(value: float) -> float:
    """Round a distance metric to two decimals."""
    return round(float(value), 2)


def _safe_mean(df: pd.DataFrame, column: str, decimals: int = 2) -> float:
    """Return a safe numeric mean for a dataframe column."""
    if df.empty or column not in df.columns:
        return 0.0
    numeric_series = pd.to_numeric(df[column], errors="coerce").dropna()
    if numeric_series.empty:
        return 0.0
    return round(float(numeric_series.mean()), decimals)


def _distance_series(df: pd.DataFrame) -> pd.Series:
    """Compute euclidean distances between start and end coordinates."""
    required_columns = {"x", "y", "end_x", "end_y"}
    if df.empty or not required_columns.issubset(df.columns):
        return pd.Series(dtype="float64", index=df.index)

    coords = df.loc[:, ["x", "y", "end_x", "end_y"]].apply(pd.to_numeric, errors="coerce")
    return ((coords["end_x"] - coords["x"]) ** 2 + (coords["end_y"] - coords["y"]) ** 2).pow(0.5)


def _build_interpretation(event_type: str) -> str:
    """Return a short interpretation string for the UI."""
    return INTERPRETATION_BY_EVENT.get(
        event_type,
        "Este bloque resume la actividad del evento seleccionado.",
    )


def calculate_event_card_stats(df: pd.DataFrame, event_type: str) -> dict[str, object]:
    """Calculate compact stats for summary event cards."""
    event_df = _filter_event_df(df, event_type)
    total_events = int(len(event_df))
    show_success_rate = event_type in SUCCESS_RATE_EVENTS
    info_label = "Evento descriptivo"
    if event_type in {"Dispossessed", "Miscontrol", "Error", "Foul Committed", "Dribbled Past"}:
        info_label = "Evento de riesgo"

    successful_events = 0
    success_rate = 0.0
    if show_success_rate and total_events > 0:
        outcome_series = _get_outcome_series(event_df)
        successful_events = int(_contains_any(outcome_series, SUCCESS_KEYWORDS).sum())
        success_rate = _round_pct((successful_events / total_events) * 100)

    return {
        "event_type": event_type,
        "total_events": total_events,
        "successful_events": successful_events,
        "success_rate": success_rate,
        "show_success_rate": show_success_rate,
        "success_label": "Aciertos",
        "info_label": info_label,
    }


def calculate_pass_metrics(df: pd.DataFrame) -> dict[str, object]:
    """Calculate pass-specific KPIs."""
    pass_df = _filter_event_df(df, "Pass")
    total_passes = int(len(pass_df))
    outcome_series = _get_outcome_series(pass_df)
    completed_mask = outcome_series.eq("") | _contains_any(outcome_series, PASS_SUCCESS_KEYWORDS)
    completed_passes = int(completed_mask.fillna(False).sum())
    incomplete_passes = max(total_passes - completed_passes, 0)
    completion_rate = _round_pct((completed_passes / total_passes) * 100) if total_passes else 0.0

    distances = _distance_series(pass_df).dropna()
    average_length = _round_distance(distances.mean()) if not distances.empty else 0.0

    if {"x", "end_x"}.issubset(pass_df.columns):
        coords = pass_df.loc[:, ["x", "end_x"]].apply(pd.to_numeric, errors="coerce")
        progressive_passes = int((coords["end_x"] - coords["x"] >= 10).fillna(False).sum())
        final_third_passes = int((coords["end_x"] >= 80).fillna(False).sum())
    else:
        progressive_passes = 0
        final_third_passes = 0

    if {"end_x", "end_y"}.issubset(pass_df.columns):
        end_coords = pass_df.loc[:, ["end_x", "end_y"]].apply(pd.to_numeric, errors="coerce")
        box_entries = int(
            ((end_coords["end_x"] >= 102) & end_coords["end_y"].between(18, 62)).fillna(False).sum()
        )
    else:
        box_entries = 0

    return {
        "event_type": "Pass",
        "total_passes": total_passes,
        "completed_passes": completed_passes,
        "incomplete_passes": incomplete_passes,
        "completion_rate": completion_rate,
        "average_length": average_length,
        "progressive_passes": progressive_passes,
        "final_third_passes": final_third_passes,
        "box_entries": box_entries,
        "interpretation": _build_interpretation("Pass"),
    }


def calculate_carry_metrics(df: pd.DataFrame) -> dict[str, object]:
    """Calculate carry-specific KPIs."""
    carry_df = _filter_event_df(df, "Carry")
    total_carries = int(len(carry_df))
    distances = _distance_series(carry_df).dropna()
    average_length = _round_distance(distances.mean()) if not distances.empty else 0.0
    carries_with_end_location = int(distances.notna().sum())

    if {"x", "end_x"}.issubset(carry_df.columns):
        coords = carry_df.loc[:, ["x", "end_x"]].apply(pd.to_numeric, errors="coerce")
        progressive_carries = int((coords["end_x"] - coords["x"] >= 10).fillna(False).sum())
        final_third_carries = int((coords["end_x"] >= 80).fillna(False).sum())
    else:
        progressive_carries = 0
        final_third_carries = 0

    if {"end_x", "end_y"}.issubset(carry_df.columns):
        end_coords = carry_df.loc[:, ["end_x", "end_y"]].apply(pd.to_numeric, errors="coerce")
        box_entries = int(
            ((end_coords["end_x"] >= 102) & end_coords["end_y"].between(18, 62)).fillna(False).sum()
        )
    else:
        box_entries = 0

    return {
        "event_type": "Carry",
        "total_carries": total_carries,
        "average_length": average_length,
        "progressive_carries": progressive_carries,
        "final_third_carries": final_third_carries,
        "box_entries": box_entries,
        "carries_with_end_location": carries_with_end_location,
        "interpretation": _build_interpretation("Carry"),
    }


def calculate_shot_metrics(df: pd.DataFrame) -> dict[str, object]:
    """Calculate shot-specific KPIs."""
    shot_df = _filter_event_df(df, "Shot")
    total_shots = int(len(shot_df))
    outcome_series = _get_outcome_series(shot_df)

    goals = int(outcome_series.str.contains("goal", case=False, na=False).sum())
    saved = int(outcome_series.str.contains("saved", case=False, na=False).sum())
    off_target = int(outcome_series.str.contains("off target", case=False, na=False).sum())
    blocked = int(outcome_series.str.contains("blocked", case=False, na=False).sum())

    if {"x", "y"}.issubset(shot_df.columns):
        coords = shot_df.loc[:, ["x", "y"]].apply(pd.to_numeric, errors="coerce")
        distances = ((120 - coords["x"]) ** 2 + (40 - coords["y"]) ** 2).pow(0.5).dropna()
        average_distance_to_goal = _round_distance(distances.mean()) if not distances.empty else 0.0
    else:
        average_distance_to_goal = 0.0

    conversion_rate = _round_pct((goals / total_shots) * 100) if total_shots else 0.0
    shot_on_target_rate = _round_pct(((goals + saved) / total_shots) * 100) if total_shots else 0.0
    goals_per_shot = round(goals / total_shots, 3) if total_shots else 0.0

    return {
        "event_type": "Shot",
        "total_shots": total_shots,
        "goals": goals,
        "saved": saved,
        "off_target": off_target,
        "blocked": blocked,
        "average_distance_to_goal": average_distance_to_goal,
        "conversion_rate": conversion_rate,
        "shot_on_target_rate": shot_on_target_rate,
        "goals_per_shot": goals_per_shot,
        "interpretation": _build_interpretation("Shot"),
    }


def calculate_pressure_metrics(df: pd.DataFrame) -> dict[str, object]:
    """Calculate pressure-specific KPIs."""
    pressure_df = _filter_event_df(df, "Pressure")
    total_pressures = int(len(pressure_df))

    if "x" in pressure_df.columns:
        x_series = pd.to_numeric(pressure_df["x"], errors="coerce")
        pressures_in_opponent_half = int((x_series >= 60).fillna(False).sum())
        pressures_in_final_third = int((x_series >= 80).fillna(False).sum())
    else:
        pressures_in_opponent_half = 0
        pressures_in_final_third = 0

    return {
        "event_type": "Pressure",
        "total_pressures": total_pressures,
        "pressures_in_opponent_half": pressures_in_opponent_half,
        "pressures_in_final_third": pressures_in_final_third,
        "average_x": _safe_mean(pressure_df, "x"),
        "average_y": _safe_mean(pressure_df, "y"),
        "interpretation": _build_interpretation("Pressure"),
    }


def calculate_duel_metrics(df: pd.DataFrame) -> dict[str, object]:
    """Calculate duel-specific KPIs."""
    duel_df = _filter_event_df(df, "Duel")
    total_duels = int(len(duel_df))
    outcome_series = _get_outcome_series(duel_df)
    duels_won = int(_contains_any(outcome_series, DUEL_WIN_KEYWORDS).sum())
    duels_lost = int(_contains_any(outcome_series, DUEL_LOSS_KEYWORDS).sum())
    win_rate = _round_pct((duels_won / total_duels) * 100) if total_duels else 0.0

    return {
        "event_type": "Duel",
        "total_duels": total_duels,
        "duels_won": duels_won,
        "duels_lost": duels_lost,
        "win_rate": win_rate,
        "interpretation": _build_interpretation("Duel"),
    }


def calculate_dribble_metrics(df: pd.DataFrame) -> dict[str, object]:
    """Calculate dribble-specific KPIs."""
    dribble_df = _filter_event_df(df, "Dribble")
    total_dribbles = int(len(dribble_df))
    outcome_series = _get_outcome_series(dribble_df)
    successful_dribbles = int(
        _contains_any(outcome_series, ("successful", "complete", "won", "success")).sum()
    )
    unsuccessful_dribbles = max(total_dribbles - successful_dribbles, 0)
    success_rate = _round_pct((successful_dribbles / total_dribbles) * 100) if total_dribbles else 0.0

    if "x" in dribble_df.columns:
        x_series = pd.to_numeric(dribble_df["x"], errors="coerce")
        dribbles_in_final_third = int((x_series >= 80).fillna(False).sum())
    else:
        dribbles_in_final_third = 0

    return {
        "event_type": "Dribble",
        "total_dribbles": total_dribbles,
        "successful_dribbles": successful_dribbles,
        "unsuccessful_dribbles": unsuccessful_dribbles,
        "success_rate": success_rate,
        "dribbles_in_final_third": dribbles_in_final_third,
        "interpretation": _build_interpretation("Dribble"),
    }


def calculate_recovery_metrics(df: pd.DataFrame) -> dict[str, object]:
    """Calculate ball-recovery KPIs."""
    recovery_df = _filter_event_df(df, "Ball Recovery")
    total_recoveries = int(len(recovery_df))

    if "x" in recovery_df.columns:
        x_series = pd.to_numeric(recovery_df["x"], errors="coerce")
        recoveries_in_own_half = int((x_series < 60).fillna(False).sum())
        recoveries_in_opponent_half = int((x_series >= 60).fillna(False).sum())
        recoveries_in_final_third = int((x_series >= 80).fillna(False).sum())
    else:
        recoveries_in_own_half = 0
        recoveries_in_opponent_half = 0
        recoveries_in_final_third = 0

    return {
        "event_type": "Ball Recovery",
        "total_recoveries": total_recoveries,
        "recoveries_in_own_half": recoveries_in_own_half,
        "recoveries_in_opponent_half": recoveries_in_opponent_half,
        "recoveries_in_final_third": recoveries_in_final_third,
        "interpretation": _build_interpretation("Ball Recovery"),
    }


def calculate_generic_event_metrics(df: pd.DataFrame, event_type: str) -> dict[str, object]:
    """Calculate a generic event summary for unsupported specific event types."""
    event_df = _filter_event_df(df, event_type)
    card_stats = calculate_event_card_stats(df, event_type)
    return {
        "event_type": event_type,
        "total_events": int(len(event_df)),
        "successful_events": int(card_stats["successful_events"]),
        "success_rate": float(card_stats["success_rate"]) if card_stats["show_success_rate"] else 0.0,
        "average_x": _safe_mean(event_df, "x"),
        "average_y": _safe_mean(event_df, "y"),
        "show_success_rate": bool(card_stats["show_success_rate"]),
        "info_label": str(card_stats["info_label"]),
        "interpretation": _build_interpretation(event_type),
    }


def get_supported_specific_metric_events() -> list[str]:
    """Return the list of event types available in the specific metrics tab."""
    return list(SUPPORTED_SPECIFIC_EVENTS)


def get_event_analysis_description(event_type: str) -> str:
    """Return a short explanation of what the selected event analysis covers."""
    return EVENT_ANALYSIS_DESCRIPTIONS.get(
        event_type,
        "Resume la actividad del evento seleccionado con los filtros activos.",
    )


def get_metric_definitions() -> dict[str, str]:
    """Return methodological definitions shown in the UI."""
    return dict(METRIC_DEFINITIONS)


def get_metric_display_name(metric_key: str) -> str:
    """Return a user-facing Spanish label for a metric key."""
    return METRIC_DISPLAY_NAMES.get(metric_key, metric_key.replace("_", " ").capitalize())


def calculate_specific_event_metrics(df: pd.DataFrame, event_type: str) -> dict[str, object]:
    """Dispatch event-specific metric calculations with a generic fallback."""
    calculators = {
        "Pass": calculate_pass_metrics,
        "Carry": calculate_carry_metrics,
        "Shot": calculate_shot_metrics,
        "Pressure": calculate_pressure_metrics,
        "Duel": calculate_duel_metrics,
        "Dribble": calculate_dribble_metrics,
        "Ball Recovery": calculate_recovery_metrics,
    }
    calculator = calculators.get(event_type)
    if calculator is None:
        return calculate_generic_event_metrics(df, event_type)
    return calculator(df)
