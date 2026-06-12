from __future__ import annotations

import streamlit as st

from src.ui.components.empty_state import render_empty_state
from src.ui.layout_kit.section import render_section_title
from src.ui.views.spatial_recommendation_ui import (
    render_delaunay_recommendation,
    render_recommendation_comparison_table,
    render_scoring_on_delaunay_recommendation,
)


def render_delaunay_alternatives(*, context: dict[str, object]) -> None:
    """Render connectivity-based alternative pass suggestions."""
    render_section_title(
        "Sugerencia del método Delaunay",
        "Se muestran por separado la sugerencia basada en Delaunay y la sugerencia basada en scoring espacial.",
    )
    st.divider()
    if "delaunay_rec" not in context["selected_plots"]:
        render_empty_state(
            "No hay alternativas calculadas todavía para esta vista.",
            "Activa `Pase sugerido por Delaunay` en los controles superiores para ver esta subvista.",
        )
    else:
        render_delaunay_recommendation(
            context["selected_event"],
            context["freeze_frame_df"],
            context["delaunay_edges_df"],
            context["delaunay_recommendation"],
        )
        st.divider()
        render_scoring_on_delaunay_recommendation(
            selected_event=context["selected_event"],
            freeze_frame_df=context["freeze_frame_df"],
            delaunay_edges_df=context["delaunay_edges_df"],
            recommendation=context["scoring_recommendation"],
        )

    st.divider()
    render_section_title(
        "Comparativa Delaunay vs scoring",
        "Contraste entre la sugerencia propia de Delaunay y la recomendación heurística de scoring espacial.",
    )
    render_recommendation_comparison_table(context["delaunay_recommendation"], context["scoring_recommendation"])
