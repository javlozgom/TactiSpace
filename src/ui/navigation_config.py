from __future__ import annotations

MATCH_OVERVIEW_VIEW = "🏟️ Vista general"
EVENT_ANALYSIS_VIEW = "🎯 Sistema de análisis"
RAW_DEBUG_VIEW = "🗂️ Datos y depuración"

NAV_OPTIONS = [
    MATCH_OVERVIEW_VIEW,
    EVENT_ANALYSIS_VIEW,
    RAW_DEBUG_VIEW,
]

VIEW_ICONS = {
    MATCH_OVERVIEW_VIEW: "🏟️",
    EVENT_ANALYSIS_VIEW: "🎯",
    RAW_DEBUG_VIEW: "🧪",
}

MATCH_OVERVIEW_SECTIONS = [
    "🏠 Inicio",
    "📊 Resumen",
    "📘 Guía",
]

EVENT_ANALYSIS_SECTIONS = [
    "📏 Métricas específicas",
    "📋 Eventos",
    "🌡️ Mapa de calor",
    "⚖️ Comparativa",
    "🗺️ Voronoi/Delaunay",
    "⚠️ Pérdidas",
]

MAIN_VIEW_ALIASES = {
    MATCH_OVERVIEW_VIEW: MATCH_OVERVIEW_VIEW,
    EVENT_ANALYSIS_VIEW: EVENT_ANALYSIS_VIEW,
    RAW_DEBUG_VIEW: RAW_DEBUG_VIEW,
    "🏟️ Vista general": MATCH_OVERVIEW_VIEW,
    "🎯 Sistema de análisis": EVENT_ANALYSIS_VIEW,
    "🗂️ Datos y depuración": RAW_DEBUG_VIEW,
    "🗂️ Datos y depuracion": RAW_DEBUG_VIEW,
    "Inicio": MATCH_OVERVIEW_VIEW,
    "Resumen": MATCH_OVERVIEW_VIEW,
    "Guía de uso": MATCH_OVERVIEW_VIEW,
    "Guia de uso": MATCH_OVERVIEW_VIEW,
    "Análisis de eventos": EVENT_ANALYSIS_VIEW,
    "Análisis espacial": EVENT_ANALYSIS_VIEW,
    "Analisis espacial": EVENT_ANALYSIS_VIEW,
    "Sistema de análisis": EVENT_ANALYSIS_VIEW,
    "Sistema de analisis": EVENT_ANALYSIS_VIEW,
    "Métricas específicas": EVENT_ANALYSIS_VIEW,
    "Metricas especificas": EVENT_ANALYSIS_VIEW,
    "Comparativa": EVENT_ANALYSIS_VIEW,
    "Voronoi, Delaunay y sugerencia de pase": EVENT_ANALYSIS_VIEW,
    "Voronoi/Delaunay": EVENT_ANALYSIS_VIEW,
    "Eventos": EVENT_ANALYSIS_VIEW,
    "Mapa de calor": EVENT_ANALYSIS_VIEW,
    "Pérdidas": EVENT_ANALYSIS_VIEW,
    "Perdidas": EVENT_ANALYSIS_VIEW,
    "Pases fallidos": EVENT_ANALYSIS_VIEW,
    "Datos brutos": RAW_DEBUG_VIEW,
    "Datos y depuración": RAW_DEBUG_VIEW,
    "Datos y depuracion": RAW_DEBUG_VIEW,
    "MÃ©tricas especÃ­ficas": EVENT_ANALYSIS_VIEW,
    "PÃ©rdidas": EVENT_ANALYSIS_VIEW,
    "AnÃ¡lisis espacial": EVENT_ANALYSIS_VIEW,
    "GuÃ­a de uso": MATCH_OVERVIEW_VIEW,
    "MÃƒÂ©tricas especÃƒÂ­ficas": EVENT_ANALYSIS_VIEW,
    "PÃƒÂ©rdidas": EVENT_ANALYSIS_VIEW,
    "AnÃƒÂ¡lisis espacial": EVENT_ANALYSIS_VIEW,
    "MÃƒÆ’Ã‚Â©tricas especÃƒÂ­ficas": EVENT_ANALYSIS_VIEW,
    "PÃƒÆ’Ã‚Â©rdidas": EVENT_ANALYSIS_VIEW,
    "AnÃƒÆ’Ã‚Â¡lisis espacial": EVENT_ANALYSIS_VIEW,
}

LEGACY_SECTION_ALIASES = {
    "Inicio": ("match_overview_section", MATCH_OVERVIEW_SECTIONS[0]),
    "Resumen": ("match_overview_section", MATCH_OVERVIEW_SECTIONS[1]),
    "Guía de uso": ("match_overview_section", MATCH_OVERVIEW_SECTIONS[2]),
    "Guia de uso": ("match_overview_section", MATCH_OVERVIEW_SECTIONS[2]),
    "Métricas específicas": ("event_analysis_section", EVENT_ANALYSIS_SECTIONS[0]),
    "Metricas especificas": ("event_analysis_section", EVENT_ANALYSIS_SECTIONS[0]),
    "Eventos": ("event_analysis_section", EVENT_ANALYSIS_SECTIONS[1]),
    "Mapa de calor": ("event_analysis_section", EVENT_ANALYSIS_SECTIONS[2]),
    "Comparativa": ("event_analysis_section", EVENT_ANALYSIS_SECTIONS[3]),
    "Voronoi, Delaunay y sugerencia de pase": ("event_analysis_section", EVENT_ANALYSIS_SECTIONS[4]),
    "Voronoi/Delaunay": ("event_analysis_section", EVENT_ANALYSIS_SECTIONS[4]),
    "Análisis espacial": ("event_analysis_section", EVENT_ANALYSIS_SECTIONS[4]),
    "Analisis espacial": ("event_analysis_section", EVENT_ANALYSIS_SECTIONS[4]),
    "Pérdidas": ("event_analysis_section", EVENT_ANALYSIS_SECTIONS[5]),
    "Perdidas": ("event_analysis_section", EVENT_ANALYSIS_SECTIONS[5]),
    "Pases fallidos": ("event_analysis_section", EVENT_ANALYSIS_SECTIONS[5]),
    "MÃ©tricas especÃ­ficas": ("event_analysis_section", EVENT_ANALYSIS_SECTIONS[0]),
    "PÃ©rdidas": ("event_analysis_section", EVENT_ANALYSIS_SECTIONS[5]),
    "AnÃ¡lisis espacial": ("event_analysis_section", EVENT_ANALYSIS_SECTIONS[4]),
    "GuÃ­a de uso": ("match_overview_section", MATCH_OVERVIEW_SECTIONS[2]),
    "MÃƒÂ©tricas especÃƒÂ­ficas": ("event_analysis_section", EVENT_ANALYSIS_SECTIONS[0]),
    "PÃƒÂ©rdidas": ("event_analysis_section", EVENT_ANALYSIS_SECTIONS[5]),
    "AnÃƒÂ¡lisis espacial": ("event_analysis_section", EVENT_ANALYSIS_SECTIONS[4]),
    "MÃƒÆ’Ã‚Â©tricas especÃƒÂ­ficas": ("event_analysis_section", EVENT_ANALYSIS_SECTIONS[0]),
    "PÃƒÆ’Ã‚Â©rdidas": ("event_analysis_section", EVENT_ANALYSIS_SECTIONS[5]),
    "AnÃƒÆ’Ã‚Â¡lisis espacial": ("event_analysis_section", EVENT_ANALYSIS_SECTIONS[4]),
}


def repair_view_text(view_name: object) -> str:
    """Best-effort repair of mojibake labels coming from old session state."""
    text = str(view_name or MATCH_OVERVIEW_VIEW)
    try:
        repaired = text.encode("latin1").decode("utf-8")
    except Exception:
        repaired = text
    return repaired


def canonicalize_view_name(view_name: object) -> str:
    """Resolve one current or legacy label into a main top-level view."""
    repaired = repair_view_text(view_name)
    return MAIN_VIEW_ALIASES.get(repaired, repaired if repaired in NAV_OPTIONS else MATCH_OVERVIEW_VIEW)


def resolve_legacy_section(view_name: object) -> tuple[str, str] | None:
    """Return the state key and section label implied by one legacy view name."""
    repaired = repair_view_text(view_name)
    return LEGACY_SECTION_ALIASES.get(repaired)
