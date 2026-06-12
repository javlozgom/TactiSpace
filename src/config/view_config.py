from __future__ import annotations


PRESETS = {
    "Análisis de mediocentro": {
        "description": "Prioriza progresión, volumen de pase, recuperaciones y secuencias tras recepción.",
        "recommended_events": ["Pass", "Carry", "Ball Recovery", "Pressure"],
        "recommended_views": ["🏟️ Vista general", "🎯 Sistema de análisis", "🗂️ Datos y depuración"],
        "focus_metrics": ["progressive_passes", "progressive_carries", "recoveries_in_opponent_half"],
    },
    "Análisis de atacante": {
        "description": "Enfoca conducciones, tiros, regates y presencia en el último tercio.",
        "recommended_events": ["Carry", "Shot", "Dribble", "Pass"],
        "recommended_views": ["🏟️ Vista general", "🎯 Sistema de análisis", "🎯 Sistema de análisis"],
        "focus_metrics": ["total_shots", "successful_dribbles", "box_entries"],
    },
    "Análisis defensivo": {
        "description": "Revisa duelos, recuperaciones, despejes y presiones en zonas útiles.",
        "recommended_events": ["Duel", "Ball Recovery", "Clearance", "Pressure"],
        "recommended_views": ["🏟️ Vista general", "🎯 Sistema de análisis", "🎯 Sistema de análisis"],
        "focus_metrics": ["duels_won", "recoveries_in_own_half", "pressures_in_final_third"],
    },
    "Análisis de pérdidas": {
        "description": "Localiza pérdidas, errores técnicos y pases fallidos con mayor riesgo.",
        "recommended_events": ["Dispossessed", "Miscontrol", "Pass", "Dribble"],
        "recommended_views": ["🎯 Sistema de análisis", "🗂️ Datos y depuración", "🎯 Sistema de análisis"],
        "focus_metrics": ["failed_passes", "failed_dribbles", "losses_own_half"],
    },
    "Análisis de progresión": {
        "description": "Estudia cómo el equipo avanza con pase y conducción y qué ocurre después.",
        "recommended_events": ["Pass", "Carry", "Shot"],
        "recommended_views": ["🎯 Sistema de análisis", "🗂️ Datos y depuración", "🎯 Sistema de análisis"],
        "focus_metrics": ["progressive_passes", "progressive_carries", "final_third_passes"],
    },
}


def get_analysis_presets() -> dict:
    """Return analysis presets available in the app."""
    return dict(PRESETS)


def get_preset(name: str) -> dict:
    """Return one preset by name or an empty dict if missing."""
    return dict(PRESETS.get(name, {}))
