from __future__ import annotations

SPATIAL_PAGE_TITLE = "Voronoi, Delaunay y sugerencia de pase"
SPATIAL_PAGE_SUBTITLE = (
    "Explora pases fallidos mediante freeze-frame, Voronoi, triangulación de Delaunay y "
    "recomendaciones interpretables."
)
SPATIAL_PAGE_EYEBROW = "Espacial"

PLOT_OPTION_LABELS = {
    "original": "Freeze-frame + pase fallido",
    "voronoi": "Voronoi + pase fallido",
    "delaunay": "Delaunay + pase fallido",
    "combined": "Voronoi + Delaunay + pase fallido",
    "delaunay_rec": "Pase sugerido por Delaunay",
    "scoring_rec": "Pase sugerido por scoring",
}
DEFAULT_SPATIAL_PLOTS = list(PLOT_OPTION_LABELS.keys())

SCORING_PROFILE_OPTIONS = ["Conservador", "Intermedio", "Arriesgado"]
SPATIAL_PLOT_RENDER_WIDTH = 900

SPATIAL_MODULE_OPTIONS = [
    ("voronoi", "🧩 Voronoi"),
    ("delaunay", "📐 Delaunay"),
]
SPATIAL_MODULE_HELP = {
    "🧩 Voronoi": (
        "Análisis centrado en espacio, influencia territorial y alternativas basadas en scoring espacial."
    ),
    "📐 Delaunay": "Análisis centrado en conectividad local, vecinos geométricos y alternativas de red.",
}
SPATIAL_MODULE_HEADER = {
    "title": "Módulos espaciales",
    "description": (
        "Selecciona el bloque espacial que quieres consultar. Cada módulo despliega después sus apartados "
        "específicos."
    ),
}

VORONOI_SUBVIEWS = [
    "👁️ Vista",
    "📊 Métricas",
    "🔁 Alternativas",
]
VORONOI_SUBVIEW_HELP = {
    "👁️ Vista": "Visualización principal del caso con freeze-frame, regiones Voronoi y vista combinada cuando aplique.",
    "📊 Métricas": "Áreas, presión y métricas espaciales resumidas por jugador y por equipo.",
    "🔁 Alternativas": "Alternativas de pase basadas en scoring espacial y comparación entre métodos.",
}
VORONOI_MODULE_HEADER = {
    "title": "🧩 Voronoi",
    "description": "Consulta espacio, influencia y alternativas del caso sin mezclar otros bloques visuales.",
}

DELAUNAY_SUBVIEWS = [
    "🕸️ Red",
    "📊 Conexiones",
    "🔁 Alternativas",
]
DELAUNAY_SUBVIEW_HELP = {
    "🕸️ Red": "Visualización principal de la red Delaunay y del pase analizado.",
    "📊 Conexiones": "Vecinos del mismo equipo y resumen de conectividad local del caso.",
    "🔁 Alternativas": "Alternativas basadas en conectividad y comparación entre métodos.",
}
DELAUNAY_MODULE_HEADER = {
    "title": "📐 Delaunay",
    "description": "Consulta conectividad, vecindad local y alternativas geométricas del caso seleccionado.",
}
