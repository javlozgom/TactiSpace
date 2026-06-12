from __future__ import annotations

import streamlit as st

from src.ui.components.empty_state import render_empty_state
from src.ui.layout_kit.section import render_section_title
from src.ui.views.spatial_recommendation_ui import render_pass_recommendation, render_voronoi_scoring_comparison_table


def render_voronoi_alternatives(*, context: dict[str, object]) -> None:
    """Render space-based alternatives and cross-method comparison."""
    render_section_title(
        "Sugerencia del método Voronoi",
        "Se muestran por separado la sugerencia basada en Voronoi y la sugerencia basada en scoring espacial.",
    )
    st.divider()
    if "scoring_rec" not in context["selected_plots"]:
        render_empty_state(
            "No hay alternativas calculadas todavía para esta vista.",
            "Activa `Pase sugerido por scoring` en los controles superiores para ver esta subvista.",
        )
    else:
        render_pass_recommendation(
            event_row=context["selected_event"],
            freeze_frame_df=context["freeze_frame_df"],
            voronoi_regions_df=context["voronoi_regions_df"],
            recommendation=context["voronoi_recommendation"],
            title="Sugerencia según Voronoi",
            description="La alternativa prioriza el jugador con mayor área Voronoi disponible en el freeze-frame actual.",
            badges=[("VORONOI", "blue"), ("REAL", "red")],
            profile_label="Método",
            profile_value="Voronoi",
            score_label="Área Voronoi",
            options_title="Opciones ordenadas según Voronoi",
            breakdown_title="Desglose Voronoi",
            breakdown_columns=["Factor", "Valor", "Prioridad"],
            options_columns=[
                "spatial_reference_id",
                "voronoi_result",
                "voronoi_area",
                "nearest_opponent_distance",
                "forward_progress",
                "distance_to_passer",
            ],
            options_rename_map={"voronoi_result": "Resultado Voronoi"},
        )
        st.divider()
        render_pass_recommendation(
            event_row=context["selected_event"],
            freeze_frame_df=context["freeze_frame_df"],
            voronoi_regions_df=context["voronoi_regions_df"],
            recommendation=context["scoring_recommendation"],
            title="Sugerencia según scoring espacial",
            description="La alternativa combina progresión, espacio, presión y coste del pase en un único score heurístico.",
            breakdown_columns=["Factor", "Valor", "Peso"],
            options_columns=[
                "spatial_reference_id",
                "pass_score",
                "distance_to_passer",
                "forward_progress",
                "nearest_opponent_distance",
                "voronoi_area",
            ],
            options_rename_map={"pass_score": "Resultado scoring"},
        )

    st.divider()
    render_section_title(
        "Comparativa Voronoi vs scoring",
        "Contraste entre la sugerencia centrada en área Voronoi y la recomendación heurística de scoring espacial.",
    )
    render_voronoi_scoring_comparison_table(context["voronoi_recommendation"], context["scoring_recommendation"])
