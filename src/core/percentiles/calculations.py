from __future__ import annotations

from typing import Any

import pandas as pd

from src.core.metrics.events import calculate_specific_event_metrics, get_metric_display_name
from src.core.losses.analysis import calculate_loss_metrics
from src.core.rules.position_priorities import get_position_for_player


POSITION_OPTIONS = ["Todas", "Portero", "Defensa", "Mediocentro", "Atacante"]
PERCENTILE_FAMILY_ORDER = [
    "Pase",
    "Conducción",
    "Tiro",
    "Presión",
    "Duelos y defensa",
    "Regate",
    "Pérdidas",
]

PERCENTILE_METRIC_METADATA: dict[str, dict[str, Any]] = {
    "total_passes": {
        "label": "Pases totales",
        "family": "Pase",
        "direction": "volume",
        "interpretation": "Volumen de participación en pase.",
    },
    "completed_passes": {
        "label": "Pases completados",
        "family": "Pase",
        "direction": "higher_is_better",
        "interpretation": "Capacidad para completar pases.",
    },
    "incomplete_passes": {
        "label": "Pases fallidos",
        "family": "Pase",
        "direction": "higher_is_risk",
        "interpretation": "Más valor implica más pérdidas por pase no completado.",
    },
    "completion_rate": {
        "label": "% acierto en pase",
        "family": "Pase",
        "direction": "efficiency",
        "interpretation": "Eficiencia de pase respecto al volumen intentado.",
        "requires_min_metric": "total_passes",
        "default_min_value": 10,
    },
    "progressive_passes": {
        "label": "Pases progresivos",
        "family": "Pase",
        "direction": "volume",
        "interpretation": "Capacidad para avanzar el balón mediante el pase.",
    },
    "final_third_passes": {
        "label": "Pases al último tercio",
        "family": "Pase",
        "direction": "volume",
        "interpretation": "Participación en progresión hacia zonas avanzadas.",
    },
    "box_entries": {
        "label": "Entradas al área",
        "family": "Pase",
        "direction": "volume",
        "interpretation": "Acciones que terminan dentro del área rival, ya sea por pase o conducción.",
    },
    "pass_box_entries": {
        "label": "Pases al área",
        "family": "Pase",
        "direction": "volume",
        "interpretation": "Capacidad para conectar con el área rival mediante pase.",
    },
    "total_carries": {
        "label": "Conducciones totales",
        "family": "Conducción",
        "direction": "volume",
        "interpretation": "Frecuencia de conducciones.",
    },
    "average_length": {
        "label": "Distancia media conducción",
        "family": "Conducción",
        "direction": "volume",
        "interpretation": "Longitud media de las conducciones realizadas.",
    },
    "progressive_carries": {
        "label": "Conducciones progresivas",
        "family": "Conducción",
        "direction": "volume",
        "interpretation": "Capacidad para avanzar con balón conducido.",
    },
    "final_third_carries": {
        "label": "Conducciones al último tercio",
        "family": "Conducción",
        "direction": "volume",
        "interpretation": "Presencia con conducción en zonas avanzadas.",
    },
    "carry_box_entries": {
        "label": "Conducciones al área",
        "family": "Conducción",
        "direction": "volume",
        "interpretation": "Capacidad para transportar el balón hasta el área rival.",
    },
    "total_shots": {
        "label": "Tiros totales",
        "family": "Tiro",
        "direction": "volume",
        "interpretation": "Volumen ofensivo de finalización.",
    },
    "goals": {
        "label": "Goles",
        "family": "Tiro",
        "direction": "higher_is_better",
        "interpretation": "Producción goleadora.",
    },
    "saved": {
        "label": "Tiros parados",
        "family": "Tiro",
        "direction": "volume",
        "interpretation": "Tiros a portería que obligan a intervenir al portero.",
    },
    "off_target": {
        "label": "Tiros fuera",
        "family": "Tiro",
        "direction": "higher_is_risk",
        "interpretation": "Un valor alto refleja peor precisión en el remate.",
    },
    "blocked": {
        "label": "Tiros bloqueados",
        "family": "Tiro",
        "direction": "higher_is_risk",
        "interpretation": "Un valor alto refleja más remates neutralizados antes de llegar a portería.",
    },
    "average_distance_to_goal": {
        "label": "Distancia media a portería",
        "family": "Tiro",
        "direction": "lower_is_better",
        "interpretation": "Un valor menor indica remates más cercanos a portería.",
    },
    "conversion_rate": {
        "label": "% conversión",
        "family": "Tiro",
        "direction": "efficiency",
        "interpretation": "Eficiencia finalizadora: goles divididos entre tiros.",
        "requires_min_metric": "total_shots",
        "default_min_value": 5,
    },
    "shot_on_target_rate": {
        "label": "% tiros a portería",
        "family": "Tiro",
        "direction": "efficiency",
        "interpretation": "Precisión del remate: tiros entre palos sobre tiros totales.",
        "requires_min_metric": "total_shots",
        "default_min_value": 5,
    },
    "goals_per_shot": {
        "label": "Goles por tiro",
        "family": "Tiro",
        "direction": "efficiency",
        "interpretation": "Producción goleadora por cada tiro intentado.",
        "requires_min_metric": "total_shots",
        "default_min_value": 5,
    },
    "total_pressures": {
        "label": "Presiones totales",
        "family": "Presión",
        "direction": "volume",
        "interpretation": "Volumen global de presión.",
    },
    "pressures_in_opponent_half": {
        "label": "Presiones en campo rival",
        "family": "Presión",
        "direction": "volume",
        "interpretation": "Actividad de presión en campo rival.",
    },
    "pressures_in_final_third": {
        "label": "Presiones en último tercio",
        "family": "Presión",
        "direction": "volume",
        "interpretation": "Agresividad de presión en zonas muy altas.",
    },
    "total_duels": {
        "label": "Duelos totales",
        "family": "Duelos y defensa",
        "direction": "volume",
        "interpretation": "Frecuencia de disputas individuales.",
    },
    "duels_won": {
        "label": "Duelos ganados",
        "family": "Duelos y defensa",
        "direction": "higher_is_better",
        "interpretation": "Capacidad para imponerse en duelos.",
    },
    "win_rate": {
        "label": "% duelos ganados",
        "family": "Duelos y defensa",
        "direction": "efficiency",
        "interpretation": "Eficiencia en duelos ganados sobre duelos totales.",
        "requires_min_metric": "total_duels",
        "default_min_value": 5,
    },
    "total_recoveries": {
        "label": "Recuperaciones",
        "family": "Duelos y defensa",
        "direction": "volume",
        "interpretation": "Volumen de recuperaciones de balón.",
    },
    "recoveries_in_opponent_half": {
        "label": "Recuperaciones en campo rival",
        "family": "Duelos y defensa",
        "direction": "volume",
        "interpretation": "Capacidad para recuperar alto.",
    },
    "recoveries_in_final_third": {
        "label": "Recuperaciones en último tercio",
        "family": "Duelos y defensa",
        "direction": "volume",
        "interpretation": "Actividad defensiva muy alta y agresiva.",
    },
    "total_dribbles": {
        "label": "Regates totales",
        "family": "Regate",
        "direction": "volume",
        "interpretation": "Frecuencia de intentos de regate.",
    },
    "successful_dribbles": {
        "label": "Regates exitosos",
        "family": "Regate",
        "direction": "higher_is_better",
        "interpretation": "Capacidad para superar rivales con éxito.",
    },
    "unsuccessful_dribbles": {
        "label": "Regates fallidos",
        "family": "Regate",
        "direction": "higher_is_risk",
        "interpretation": "Un valor alto indica más pérdidas en el intento de regate.",
    },
    "success_rate": {
        "label": "% éxito en regate",
        "family": "Regate",
        "direction": "efficiency",
        "interpretation": "Eficiencia en el regate respecto al volumen intentado.",
        "requires_min_metric": "total_dribbles",
        "default_min_value": 5,
    },
    "dribbles_in_final_third": {
        "label": "Regates en último tercio",
        "family": "Regate",
        "direction": "volume",
        "interpretation": "Volumen de desborde en zonas avanzadas.",
    },
    "total_losses": {
        "label": "Pérdidas totales",
        "family": "Pérdidas",
        "direction": "higher_is_risk",
        "interpretation": "Un valor alto indica mayor volumen de pérdidas.",
    },
    "losses_own_half": {
        "label": "Pérdidas en campo propio",
        "family": "Pérdidas",
        "direction": "higher_is_risk",
        "interpretation": "Pérdidas en zonas potencialmente peligrosas.",
    },
    "losses_opponent_half": {
        "label": "Pérdidas en campo rival",
        "family": "Pérdidas",
        "direction": "higher_is_risk",
        "interpretation": "Pérdidas en campo rival, normalmente menos costosas que en campo propio.",
    },
    "losses_final_third": {
        "label": "Pérdidas en último tercio",
        "family": "Pérdidas",
        "direction": "higher_is_risk",
        "interpretation": "Pérdidas en zonas muy avanzadas.",
    },
    "failed_passes": {
        "label": "Pases fallidos",
        "family": "Pérdidas",
        "direction": "higher_is_risk",
        "interpretation": "Métrica de riesgo: más pases no completados.",
    },
    "failed_dribbles": {
        "label": "Regates fallidos",
        "family": "Pérdidas",
        "direction": "higher_is_risk",
        "interpretation": "Métrica de riesgo: más pérdidas en intentos de regate.",
    },
    "miscontrols": {
        "label": "Controles defectuosos",
        "family": "Pérdidas",
        "direction": "higher_is_risk",
        "interpretation": "Métrica de riesgo: errores técnicos de control.",
    },
    "dispossessed": {
        "label": "Desposesiones",
        "family": "Pérdidas",
        "direction": "higher_is_risk",
        "interpretation": "Métrica de riesgo: pérdidas provocadas por presión o robo rival.",
    },
    "errors": {
        "label": "Errores",
        "family": "Pérdidas",
        "direction": "higher_is_risk",
        "interpretation": "Métrica de riesgo: errores directos registrados en el evento.",
    },
}

EVENT_METRIC_SOURCES = {
    "Pass": {
        "total_passes",
        "completed_passes",
        "incomplete_passes",
        "completion_rate",
        "progressive_passes",
        "final_third_passes",
        "pass_box_entries",
    },
    "Carry": {
        "total_carries",
        "average_length",
        "progressive_carries",
        "final_third_carries",
        "carry_box_entries",
    },
    "Shot": {
        "total_shots",
        "goals",
        "saved",
        "off_target",
        "blocked",
        "average_distance_to_goal",
        "conversion_rate",
        "shot_on_target_rate",
        "goals_per_shot",
    },
    "Pressure": {
        "total_pressures",
        "pressures_in_opponent_half",
        "pressures_in_final_third",
    },
    "Duel": {
        "total_duels",
        "duels_won",
        "win_rate",
    },
    "Dribble": {
        "total_dribbles",
        "successful_dribbles",
        "unsuccessful_dribbles",
        "success_rate",
        "dribbles_in_final_third",
    },
    "Ball Recovery": {
        "total_recoveries",
        "recoveries_in_opponent_half",
        "recoveries_in_final_third",
    },
}

LOSS_METRICS = {
    "total_losses",
    "losses_own_half",
    "losses_opponent_half",
    "losses_final_third",
    "failed_passes",
    "failed_dribbles",
    "miscontrols",
    "dispossessed",
    "errors",
}

INTERNAL_METRIC_TO_BASE = {
    "pass_box_entries": "box_entries",
    "carry_box_entries": "box_entries",
}


def get_percentile_metric_options() -> dict[str, dict[str, str]]:
    """Return grouped metric options for percentile comparisons."""
    grouped_options: dict[str, dict[str, str]] = {family: {} for family in PERCENTILE_FAMILY_ORDER}
    for metric_key, metadata in PERCENTILE_METRIC_METADATA.items():
        family = str(metadata.get("family", "Otras"))
        grouped_options.setdefault(family, {})
        grouped_options[family][metric_key] = get_metric_label(metric_key)
    return {family: metrics for family, metrics in grouped_options.items() if metrics}


def flatten_metric_options(metric_groups: dict[str, dict[str, str]]) -> dict[str, str]:
    """Flatten grouped metric options into one dictionary."""
    flattened: dict[str, str] = {}
    for metrics in metric_groups.values():
        flattened.update(metrics)
    return flattened


def flatten_percentile_presets(presets: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Flatten grouped percentile presets into one plain dictionary."""
    flattened: dict[str, dict[str, Any]] = {}
    for maybe_group_name, maybe_group in presets.items():
        if not isinstance(maybe_group, dict):
            continue
        if _looks_like_preset_definition(maybe_group):
            flattened[str(maybe_group_name)] = dict(maybe_group)
            continue
        for preset_name, preset_definition in maybe_group.items():
            if isinstance(preset_definition, dict) and _looks_like_preset_definition(preset_definition):
                flattened[str(preset_name)] = dict(preset_definition)
    return flattened


def get_metric_metadata(metric_key: str) -> dict[str, Any]:
    """Return metadata for one percentile metric."""
    metadata = PERCENTILE_METRIC_METADATA.get(metric_key, {})
    fallback_label = get_metric_display_name(metric_key)
    return {
        "label": metadata.get("label", fallback_label),
        "family": metadata.get("family", "Otras"),
        "direction": metadata.get("direction", "higher_is_better"),
        "interpretation": metadata.get(
            "interpretation",
            "Los percentiles comparan el rendimiento relativo de cada jugador respecto al conjunto filtrado.",
        ),
        "requires_min_metric": metadata.get("requires_min_metric"),
        "default_min_value": metadata.get("default_min_value"),
    }


def get_metric_label(metric_key: str) -> str:
    """Return the user-facing label for one metric."""
    return str(get_metric_metadata(metric_key).get("label"))


def get_metric_direction(metric_key: str) -> str:
    """Return the interpretation direction for one metric."""
    return str(get_metric_metadata(metric_key).get("direction"))


def is_risk_metric(metric_key: str) -> bool:
    """Return whether one metric should be interpreted as risk."""
    return get_metric_direction(metric_key) == "higher_is_risk"


def is_efficiency_metric(metric_key: str) -> bool:
    """Return whether one metric should be interpreted as efficiency."""
    return get_metric_direction(metric_key) == "efficiency"


def get_percentile_interpretation_text(x_metric: str, y_metric: str) -> str:
    """Return a short interpretation text for the selected pair of metrics."""
    selected_metrics = {x_metric, y_metric}
    if selected_metrics == {"total_shots", "goals"}:
        return (
            "Interpretación: producción ofensiva. "
            "Los jugadores destacados combinan alto volumen de tiro y alta producción goleadora."
        )
    if any(is_risk_metric(metric_key) for metric_key in selected_metrics):
        return (
            "Interpretación: métrica de riesgo. "
            "Un valor alto indica mayor volumen de acciones negativas o pérdida, no necesariamente mejor rendimiento."
        )
    if any(is_efficiency_metric(metric_key) for metric_key in selected_metrics):
        return (
            "Interpretación: eficiencia. "
            "Se recomienda aplicar una muestra mínima para evitar conclusiones basadas en pocos eventos."
        )
    if any(get_metric_direction(metric_key) == "volume" for metric_key in selected_metrics):
        return (
            "Interpretación: volumen de participación. "
            "Un valor alto indica mayor implicación en ese tipo de acción, no necesariamente mayor calidad."
        )
    return (
        "Interpretación: los percentiles comparan el rendimiento relativo de cada jugador respecto al conjunto filtrado."
    )


def get_percentile_presets() -> dict[str, dict[str, Any]]:
    """Return grouped percentile presets."""
    return {
        "Finalización": {
            "Producción goleadora": {
                "description": "Detecta jugadores con alto volumen de tiro y goles.",
                "x_metric": "total_shots",
                "y_metric": "goals",
                "position": "Atacante",
                "min_events": 5,
            },
            "Eficiencia finalizadora": {
                "description": "Compara volumen de tiro y porcentaje de conversión.",
                "x_metric": "total_shots",
                "y_metric": "conversion_rate",
                "position": "Atacante",
                "min_events": 5,
                "min_metric": "total_shots",
                "min_metric_value": 5,
            },
            "Precisión de tiro": {
                "description": "Relaciona tiros a puerta y conversión goleadora.",
                "x_metric": "shot_on_target_rate",
                "y_metric": "conversion_rate",
                "position": "Atacante",
                "min_events": 5,
                "min_metric": "total_shots",
                "min_metric_value": 5,
            },
            "Atacantes desequilibrantes": {
                "description": "Detecta atacantes con regates exitosos y producción de tiro.",
                "x_metric": "successful_dribbles",
                "y_metric": "total_shots",
                "position": "Atacante",
                "min_events": 5,
            },
            "Extremos desequilibrantes": {
                "description": "Relaciona regates exitosos y conducciones al área.",
                "x_metric": "successful_dribbles",
                "y_metric": "carry_box_entries",
                "position": "Atacante",
                "min_events": 5,
            },
        },
        "Creación y pase": {
            "Creadores progresivos": {
                "description": "Relaciona pases progresivos y pases al último tercio.",
                "x_metric": "progressive_passes",
                "y_metric": "final_third_passes",
                "position": "Todas",
                "min_events": 10,
            },
            "Mediocentros seguros y progresivos": {
                "description": "Relaciona precisión en pase y progresión.",
                "x_metric": "completion_rate",
                "y_metric": "progressive_passes",
                "position": "Mediocentro",
                "min_events": 10,
            },
            "Generadores de peligro": {
                "description": "Detecta jugadores que llevan el balón hacia zonas peligrosas mediante pase.",
                "x_metric": "final_third_passes",
                "y_metric": "box_entries",
                "position": "Todas",
                "min_events": 10,
            },
            "Distribuidores principales": {
                "description": "Detecta jugadores con alto volumen de pase y precisión.",
                "x_metric": "total_passes",
                "y_metric": "completion_rate",
                "position": "Todas",
                "min_events": 15,
            },
            "Centrales constructores": {
                "description": "Detecta defensas con volumen de pase y progresión desde atrás.",
                "x_metric": "total_passes",
                "y_metric": "progressive_passes",
                "position": "Defensa",
                "min_events": 15,
            },
            "Jugadores más participativos": {
                "description": "Detecta jugadores con alto volumen de acciones de pase y circulación.",
                "x_metric": "total_passes",
                "y_metric": "completed_passes",
                "position": "Todas",
                "min_events": 15,
            },
        },
        "Conducción y progresión": {
            "Conductores progresivos": {
                "description": "Detecta jugadores que progresan con balón mediante conducciones.",
                "x_metric": "progressive_carries",
                "y_metric": "final_third_carries",
                "position": "Todas",
                "min_events": 5,
            },
            "Progresión mixta": {
                "description": "Relaciona progresión mediante pase y conducción.",
                "x_metric": "progressive_passes",
                "y_metric": "progressive_carries",
                "position": "Mediocentro",
                "min_events": 10,
            },
            "Laterales profundos": {
                "description": "Detecta defensas con conducciones y acciones hacia último tercio.",
                "x_metric": "final_third_carries",
                "y_metric": "box_entries",
                "position": "Defensa",
                "min_events": 5,
            },
            "Box-to-box": {
                "description": "Relaciona conducción progresiva y recuperación en campo rival.",
                "x_metric": "progressive_carries",
                "y_metric": "recoveries_in_opponent_half",
                "position": "Mediocentro",
                "min_events": 8,
            },
            "Amenaza al área": {
                "description": "Detecta jugadores que llevan el balón hacia zona de área.",
                "x_metric": "box_entries",
                "y_metric": "final_third_passes",
                "position": "Todas",
                "min_events": 8,
            },
            "Progresión hacia zona peligrosa": {
                "description": "Relaciona pases y conducciones hacia último tercio.",
                "x_metric": "final_third_passes",
                "y_metric": "final_third_carries",
                "position": "Todas",
                "min_events": 8,
            },
        },
        "Defensa y recuperación": {
            "Defensas activos": {
                "description": "Combina recuperaciones y duelos ganados.",
                "x_metric": "total_recoveries",
                "y_metric": "duels_won",
                "position": "Defensa",
                "min_events": 10,
            },
            "Anticipación defensiva": {
                "description": "Relaciona recuperaciones en campo rival y recuperaciones totales.",
                "x_metric": "recoveries_in_opponent_half",
                "y_metric": "total_recoveries",
                "position": "Todas",
                "min_events": 10,
            },
            "Dominio en duelos": {
                "description": "Detecta jugadores con volumen y éxito en duelos.",
                "x_metric": "total_duels",
                "y_metric": "win_rate",
                "position": "Todas",
                "min_events": 8,
                "min_metric": "total_duels",
                "min_metric_value": 5,
            },
            "Mediocentros completos": {
                "description": "Combina progresión en pase y recuperación.",
                "x_metric": "progressive_passes",
                "y_metric": "total_recoveries",
                "position": "Mediocentro",
                "min_events": 10,
            },
            "Laterales equilibrados": {
                "description": "Relaciona acciones ofensivas hacia último tercio y recuperaciones.",
                "x_metric": "final_third_carries",
                "y_metric": "total_recoveries",
                "position": "Defensa",
                "min_events": 8,
            },
        },
        "Presión": {
            "Presión alta": {
                "description": "Relaciona presiones en último tercio y recuperaciones en campo rival.",
                "x_metric": "pressures_in_final_third",
                "y_metric": "recoveries_in_opponent_half",
                "position": "Todas",
                "min_events": 10,
            },
            "Presionantes intensos": {
                "description": "Relaciona presión total y presión en último tercio.",
                "x_metric": "total_pressures",
                "y_metric": "pressures_in_final_third",
                "position": "Todas",
                "min_events": 8,
            },
            "Recuperadores adelantados": {
                "description": "Detecta jugadores que recuperan en campo rival y último tercio.",
                "x_metric": "recoveries_in_opponent_half",
                "y_metric": "recoveries_in_final_third",
                "position": "Todas",
                "min_events": 5,
            },
        },
        "Riesgo y pérdidas": {
            "Alertas de pérdida": {
                "description": "Identifica jugadores con alto volumen de pérdidas y pérdidas en campo propio.",
                "x_metric": "total_losses",
                "y_metric": "losses_own_half",
                "position": "Todas",
                "min_events": 5,
                "risk_preset": True,
            },
            "Riesgo en pase": {
                "description": "Identifica jugadores con volumen de pase fallido y pérdidas en campo propio.",
                "x_metric": "failed_passes",
                "y_metric": "losses_own_half",
                "position": "Todas",
                "min_events": 5,
                "risk_preset": True,
            },
            "Riesgo técnico": {
                "description": "Relaciona controles defectuosos y desposesiones.",
                "x_metric": "miscontrols",
                "y_metric": "dispossessed",
                "position": "Todas",
                "min_events": 5,
                "risk_preset": True,
            },
        },
    }


def build_player_metric_dataset(
    df: pd.DataFrame,
    metrics: list[str],
    position_filter: str = "Todas",
    min_events: int = 1,
    min_metric: str | None = None,
    min_metric_value: int | float | None = None,
) -> pd.DataFrame:
    """Build one player-level dataset with the requested metrics."""
    requested_metrics = list(dict.fromkeys(metrics))
    support_metrics = list(dict.fromkeys([*requested_metrics, *([min_metric] if min_metric else [])]))
    columns = ["player", "team", "position", "total_events", *support_metrics]
    if df.empty or "player" not in df.columns:
        return pd.DataFrame(columns=columns)

    records: list[dict[str, Any]] = []
    for player_name in sorted(df["player"].dropna().astype(str).unique().tolist()):
        if _is_unknown_player(player_name):
            continue
        player_df = df[df["player"].astype(str) == str(player_name)].copy()
        if player_df.empty:
            continue

        total_events = int(len(player_df))
        if total_events < int(min_events):
            continue

        inferred_position = _infer_player_position(player_df, player_name)
        if _is_unknown_position(inferred_position):
            continue
        if position_filter != "Todas" and inferred_position != position_filter:
            continue

        record: dict[str, Any] = {
            "player": player_name,
            "team": _infer_player_team(player_df),
            "position": inferred_position,
            "total_events": total_events,
        }

        event_metric_cache = _build_event_metric_cache(player_df, support_metrics)
        loss_metric_cache = (
            calculate_loss_metrics(player_df)
            if any(metric in LOSS_METRICS for metric in support_metrics)
            else {}
        )

        for metric_key in support_metrics:
            record[metric_key] = _extract_metric_value(metric_key, event_metric_cache, loss_metric_cache)

        if min_metric and min_metric_value is not None:
            min_metric_numeric = pd.to_numeric(
                pd.Series([record.get(min_metric, 0)]),
                errors="coerce",
            ).fillna(0).iloc[0]
            if float(min_metric_numeric) < float(min_metric_value):
                continue

        records.append(record)

    if not records:
        return pd.DataFrame(columns=columns)

    dataset = pd.DataFrame(records)
    for metric_key in support_metrics:
        if metric_key not in dataset.columns:
            dataset[metric_key] = 0
        dataset[metric_key] = pd.to_numeric(dataset[metric_key], errors="coerce").fillna(0)
    return dataset.loc[:, columns].reset_index(drop=True)


def add_percentiles(df: pd.DataFrame, x_metric: str, y_metric: str) -> pd.DataFrame:
    """Backward-compatible percentile helper that uses interpreted percentiles."""
    return add_interpreted_percentiles(df, x_metric=x_metric, y_metric=y_metric)


def add_interpreted_percentiles(df: pd.DataFrame, x_metric: str, y_metric: str) -> pd.DataFrame:
    """Add raw and interpreted percentiles plus one combined score."""
    result_df = df.copy()
    expected_columns = [
        "x_raw_percentile",
        "y_raw_percentile",
        "x_interpreted_percentile",
        "y_interpreted_percentile",
        "combined_percentile_score",
        "x_direction",
        "y_direction",
        "percentile_mode_label",
        "x_percentile",
        "y_percentile",
    ]
    for column in expected_columns:
        if column not in result_df.columns:
            result_df[column] = pd.Series(
                dtype="float64" if "percentile" in column or "score" in column else "object"
            )
    if result_df.empty:
        return result_df

    x_values = pd.to_numeric(result_df.get(x_metric, 0), errors="coerce").fillna(0)
    y_values = pd.to_numeric(result_df.get(y_metric, 0), errors="coerce").fillna(0)
    x_raw = (x_values.rank(method="average", pct=True) * 100).round(2)
    y_raw = (y_values.rank(method="average", pct=True) * 100).round(2)
    x_direction = get_metric_direction(x_metric)
    y_direction = get_metric_direction(y_metric)

    result_df["x_raw_percentile"] = x_raw
    result_df["y_raw_percentile"] = y_raw
    result_df["x_direction"] = x_direction
    result_df["y_direction"] = y_direction
    result_df["x_interpreted_percentile"] = _interpret_percentile_series(x_raw, x_direction)
    result_df["y_interpreted_percentile"] = _interpret_percentile_series(y_raw, y_direction)
    result_df["x_percentile"] = result_df["x_interpreted_percentile"]
    result_df["y_percentile"] = result_df["y_interpreted_percentile"]
    result_df["combined_percentile_score"] = (
        (result_df["x_interpreted_percentile"] + result_df["y_interpreted_percentile"]) / 2
    ).round(2)
    result_df["percentile_mode_label"] = _build_percentile_mode_label(x_direction, y_direction)
    return result_df


def get_top_highlighted_players(df: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    """Return the top-N highlighted players by combined percentile score."""
    if df.empty:
        return df.copy()
    return (
        df.sort_values(
            [
                "combined_percentile_score",
                "x_interpreted_percentile",
                "y_interpreted_percentile",
                "player",
            ],
            ascending=[False, False, False, True],
        )
        .head(int(top_n))
        .reset_index(drop=True)
    )


def build_percentile_scatter_data(
    df: pd.DataFrame,
    x_metric: str,
    y_metric: str,
    position_filter: str = "Todas",
    min_events: int = 1,
    top_n: int = 10,
    min_metric: str | None = None,
    min_metric_value: int | float | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Build the full and highlighted datasets used by the scatter plot."""
    metric_list = [x_metric, y_metric]
    full_dataset = build_player_metric_dataset(
        df,
        metrics=metric_list,
        position_filter=position_filter,
        min_events=min_events,
        min_metric=min_metric,
        min_metric_value=min_metric_value,
    )
    full_dataset = add_interpreted_percentiles(full_dataset, x_metric=x_metric, y_metric=y_metric)
    highlighted_dataset = get_top_highlighted_players(full_dataset, top_n=top_n)
    return full_dataset, highlighted_dataset


def _infer_player_team(player_df: pd.DataFrame) -> str | None:
    """Infer the most common team for one player."""
    if "team" not in player_df.columns:
        return None
    team_mode = player_df["team"].dropna().astype(str).mode()
    return team_mode.iloc[0] if not team_mode.empty else None


def _infer_player_position(player_df: pd.DataFrame, player_name: str) -> str | None:
    """Infer the broad position for one player."""
    if "position" in player_df.columns:
        position_mode = player_df["position"].dropna().astype(str).mode()
        if not position_mode.empty:
            return get_position_for_player(player_df, player_name)
    return get_position_for_player(player_df, player_name)


def _is_unknown_position(position: object) -> bool:
    """Return whether one inferred position should be excluded from percentile views."""
    normalized = str(position or "").strip().lower()
    return normalized in {"", "unknown"}


def _is_unknown_player(player_name: object) -> bool:
    """Return whether one player label should be excluded from percentile views."""
    normalized = str(player_name or "").strip().lower()
    return normalized in {"", "unknown"}


def _build_event_metric_cache(player_df: pd.DataFrame, requested_metrics: list[str]) -> dict[str, dict[str, Any]]:
    """Compute event-specific metrics only for the required event groups."""
    cache: dict[str, dict[str, Any]] = {}
    request_box_entries = "box_entries" in requested_metrics
    for event_type, supported_metrics in EVENT_METRIC_SOURCES.items():
        if supported_metrics.intersection(requested_metrics) or (
            request_box_entries and event_type in {"Pass", "Carry"}
        ):
            cache[event_type] = calculate_specific_event_metrics(player_df, event_type)
    return cache


def _extract_metric_value(
    metric_key: str,
    event_metric_cache: dict[str, dict[str, Any]],
    loss_metric_cache: dict[str, Any],
) -> float | int:
    """Extract one metric value from the cached event/loss dictionaries."""
    if metric_key == "box_entries":
        pass_entries = _safe_metric_value(event_metric_cache.get("Pass", {}).get("box_entries", 0))
        carry_entries = _safe_metric_value(event_metric_cache.get("Carry", {}).get("box_entries", 0))
        return pass_entries + carry_entries
    if metric_key in LOSS_METRICS:
        return _safe_metric_value(loss_metric_cache.get(metric_key, 0))

    base_metric_key = INTERNAL_METRIC_TO_BASE.get(metric_key, metric_key)
    event_type = _find_metric_event_source(metric_key)
    if event_type is None:
        return 0
    return _safe_metric_value(event_metric_cache.get(event_type, {}).get(base_metric_key, 0))


def _find_metric_event_source(metric_key: str) -> str | None:
    """Return the source event type for one metric key."""
    for event_type, supported_metrics in EVENT_METRIC_SOURCES.items():
        if metric_key in supported_metrics:
            return event_type
    return None


def _safe_metric_value(value: Any) -> float | int:
    """Normalize metric values to numeric scalars."""
    if value is None or pd.isna(value):
        return 0
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float)):
        return value
    try:
        numeric_value = float(value)
        return int(numeric_value) if numeric_value.is_integer() else numeric_value
    except Exception:
        return 0


def _interpret_percentile_series(percentiles: pd.Series, direction: str) -> pd.Series:
    """Convert raw percentiles into interpreted percentiles according to the metric direction."""
    if direction == "lower_is_better":
        return (100 - percentiles).round(2)
    return percentiles.round(2)


def _build_percentile_mode_label(x_direction: str, y_direction: str) -> str:
    """Return a short interpretation label for the plotted pair."""
    if "higher_is_risk" in {x_direction, y_direction}:
        return "Riesgo"
    if "efficiency" in {x_direction, y_direction}:
        return "Eficiencia"
    if "volume" in {x_direction, y_direction}:
        return "Volumen"
    return "Rendimiento relativo"


def _looks_like_preset_definition(candidate: dict[str, Any]) -> bool:
    """Return whether a dictionary looks like one preset definition."""
    required_keys = {"description", "x_metric", "y_metric", "position", "min_events"}
    return required_keys.issubset(candidate.keys())
