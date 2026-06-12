from __future__ import annotations

import pandas as pd
import streamlit as st

from src.ui.components import render_metric_table, render_section_header
from src.ui.components.spatial_layout import render_debug_section
from src.ui.views.spatial_exports import render_case_export_section


def render_voronoi_debug_section(context: dict[str, object]) -> None:
    """Render debug and technical data related to the Voronoi branch."""
    render_section_header(
        "🧪 Debug / Datos Voronoi",
        "Bloque técnico separado de la vista principal, con diagnóstico, tablas auxiliares y exportación del caso.",
    )
    render_metric_table(context["event_diagnostics_df"], title="Diagnóstico del evento seleccionado", border=False)

    debug_voronoi_df = context.get("debug_voronoi_df", pd.DataFrame())
    if not debug_voronoi_df.empty:
        render_debug_section(
            "Datos Voronoi del caso",
            debug_voronoi_df,
            empty_message="No hay datos Voronoi disponibles para este caso.",
            empty_hint="Si el cálculo Voronoi falla, el bloque técnico queda aquí aislado.",
        )

    debug_space_metrics_df = context.get("debug_space_metrics_df", pd.DataFrame())
    if not debug_space_metrics_df.empty:
        render_debug_section(
            "Datos técnicos de espacio por jugador",
            context["debug_space_metrics_display_df"],
            empty_message="No hay métricas técnicas Voronoi disponibles para este caso.",
            empty_hint="El bloque Debug conserva acceso a las tablas técnicas cuando existen.",
        )

    render_section_header(
        "📦 Exportación del caso",
        "Descarga el diagnóstico y la comparativa actual sin alterar el contenido técnico disponible.",
    )
    render_case_export_section(
        selected_event=context["selected_event"],
        freeze_frame_df=context["freeze_frame_df"],
        delaunay_recommendation=context["delaunay_recommendation"],
        scoring_recommendation=context["scoring_recommendation"],
    )


def render_delaunay_debug_section(context: dict[str, object]) -> None:
    """Render raw Delaunay data, diagnostics and downloads."""
    render_section_header(
        "🧪 Debug / Datos Delaunay",
        "Bloque técnico separado de la red principal, con aristas, diagnóstico y exportaciones del caso.",
    )
    render_metric_table(context["event_diagnostics_df"], title="Diagnóstico del evento seleccionado", border=False)

    debug_edges_df = context.get("debug_edges_df", pd.DataFrame())
    if not debug_edges_df.empty:
        render_metric_table(debug_edges_df, title="Aristas Delaunay del caso", border=False)

    render_section_header(
        "📦 Exportación del caso",
        "Descarga el diagnóstico y la comparativa actual sin alterar el contenido técnico disponible.",
    )
    render_case_export_section(
        selected_event=context["selected_event"],
        freeze_frame_df=context["freeze_frame_df"],
        delaunay_recommendation=context["delaunay_recommendation"],
        scoring_recommendation=context["scoring_recommendation"],
    )
