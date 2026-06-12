from __future__ import annotations

import pandas as pd
import streamlit as st

from src.repositories.export_repository import dataframe_to_csv_bytes
from src.ui.tables import build_event_diagnostics, build_recommendation_comparison_df
from src.ui.views.spatial_formatters import format_score
from src.ui.views.spatial_utils import extract_event_id


def build_spatial_case_export_df(
    selected_event: pd.Series,
    freeze_frame_df: pd.DataFrame,
    delaunay_recommendation: dict,
    scoring_recommendation: dict,
) -> pd.DataFrame:
    """Build a compact export dataframe for the selected spatial case."""
    rows = build_event_diagnostics(selected_event, freeze_frame_df)
    rows.extend(
        [
            {"Campo": "recomendación_delaunay", "Valor": delaunay_recommendation.get("recommended_player") or "-"},
            {"Campo": "id_recomendación_delaunay", "Valor": delaunay_recommendation.get("spatial_reference_id") or "-"},
            {"Campo": "score_delaunay", "Valor": format_score(delaunay_recommendation.get("delaunay_score"))},
            {"Campo": "recomendación_scoring", "Valor": scoring_recommendation.get("recommended_player") or "-"},
            {"Campo": "id_recomendación_scoring", "Valor": scoring_recommendation.get("spatial_reference_id") or "-"},
            {"Campo": "score_scoring", "Valor": format_score(scoring_recommendation.get("score"))},
        ]
    )
    return pd.DataFrame(rows)


def render_case_export_section(
    selected_event: pd.Series,
    freeze_frame_df: pd.DataFrame,
    delaunay_recommendation: dict,
    scoring_recommendation: dict,
) -> None:
    """Render lightweight downloads for the selected spatial case."""
    case_df = build_spatial_case_export_df(
        selected_event=selected_event,
        freeze_frame_df=freeze_frame_df,
        delaunay_recommendation=delaunay_recommendation,
        scoring_recommendation=scoring_recommendation,
    )
    comparison_df = build_recommendation_comparison_df(delaunay_recommendation, scoring_recommendation)
    event_id = extract_event_id(selected_event) or "spatial_case"

    export_cols = st.columns(2)
    with export_cols[0]:
        st.download_button(
            "Descargar diagnóstico CSV",
            data=dataframe_to_csv_bytes(case_df),
            file_name=f"spatial_case_{event_id}.csv",
            mime="text/csv",
            width="stretch",
            icon=":material/download:",
        )
    with export_cols[1]:
        st.download_button(
            "Descargar comparativa CSV",
            data=dataframe_to_csv_bytes(comparison_df),
            file_name=f"spatial_case_comparison_{event_id}.csv",
            mime="text/csv",
            width="stretch",
            icon=":material/download:",
        )
