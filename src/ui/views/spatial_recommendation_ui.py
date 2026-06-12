from __future__ import annotations

import pandas as pd
import streamlit as st

from src.ui.components import render_context_bar, render_empty_state, render_metric_table, render_plot_card
from src.ui.components.spatial_visualizations import plot_delaunay_recommendation, plot_pass_recommendation
from src.ui.config.spatial_labels import SPATIAL_PLOT_RENDER_WIDTH
from src.ui.tables import (
    build_recommendation_comparison_df,
    build_voronoi_scoring_comparison_df,
    drop_empty_display_columns,
    merge_spatial_reference_ids,
    rename_spatial_reference_column,
)
from src.ui.views.spatial_formatters import format_score


def render_pass_recommendation(
    event_row: pd.Series,
    freeze_frame_df: pd.DataFrame,
    voronoi_regions_df: pd.DataFrame,
    recommendation: dict,
    title: str = "Recomendación por scoring",
    description: str = (
        "La sugerencia combina progresión, espacio, presión y coste del pase. El pase fallido se muestra "
        "en rojo y la opción espacialmente favorable en verde."
    ),
    badges: list[tuple[str, str]] | None = None,
    profile_label: str = "Perfil scoring",
    profile_value: str | None = None,
    score_label: str = "Score heurístico",
    options_title: str = "Opciones ordenadas según scoring",
    breakdown_title: str = "Desglose del scoring",
    breakdown_caption: str | None = None,
    breakdown_columns: list[str] | None = None,
    options_columns: list[str] | None = None,
    options_rename_map: dict[str, str] | None = None,
) -> None:
    """Render one complete scoring recommendation block, including plot and details."""
    recommendation_fig = plot_pass_recommendation(event_row, freeze_frame_df, voronoi_regions_df, recommendation)
    render_plot_card(
        title,
        recommendation_fig,
        description,
        badges=badges or [("SCORING", "blue"), ("REAL", "red")],
        figure_width=SPATIAL_PLOT_RENDER_WIDTH,
        border=False,
    )
    render_pass_recommendation_details(
        freeze_frame_df=freeze_frame_df,
        recommendation=recommendation,
        profile_label=profile_label,
        profile_value=profile_value,
        score_label=score_label,
        options_title=options_title,
        breakdown_title=breakdown_title,
        breakdown_caption=breakdown_caption,
        breakdown_columns=breakdown_columns,
        options_columns=options_columns,
        options_rename_map=options_rename_map,
    )


def render_pass_recommendation_details(
    *,
    freeze_frame_df: pd.DataFrame,
    recommendation: dict,
    profile_label: str = "Perfil scoring",
    profile_value: str | None = None,
    score_label: str = "Score heurístico",
    options_title: str = "Opciones ordenadas según scoring",
    breakdown_title: str = "Desglose del scoring",
    breakdown_caption: str | None = None,
    breakdown_columns: list[str] | None = None,
    options_columns: list[str] | None = None,
    options_rename_map: dict[str, str] | None = None,
) -> None:
    """Render the non-plot detail blocks for one scoring-based suggestion."""
    recommended_player = recommendation.get("recommended_player") or "-"
    recommended_reference_id = recommendation.get("spatial_reference_id") or "-"
    score = recommendation.get("score", 0)
    scoring_profile = profile_value or recommendation.get("resolved_scoring_profile") or "-"
    reason = str(recommendation.get("reason", "")).strip()

    render_context_bar(
        [
            {"label": "Jugador sugerido", "value": recommended_reference_id},
            {"label": profile_label, "value": scoring_profile},
            {"label": score_label, "value": f"{float(score):.3f}" if isinstance(score, (int, float)) else score},
        ]
    )
    if recommended_player not in {None, "", "-"}:
        st.caption(f"Nombre del jugador sugerido: {recommended_player}")
    if reason:
        st.caption(reason)

    if breakdown_caption:
        st.caption(breakdown_caption)
    render_score_breakdown_table(recommendation, title=breakdown_title, visible_columns=breakdown_columns)

    options_df = recommendation.get("options")
    if not isinstance(options_df, pd.DataFrame) or options_df.empty:
        render_empty_state(
            "No hay opciones de pase suficientes para generar una recomendación.",
            "El freeze-frame puede no contener compañeros candidatos claros.",
        )
        return

    display_options_df = merge_spatial_reference_ids(options_df.copy(), freeze_frame_df)
    if "spatial_reference_id" in display_options_df.columns:
        display_options_df = display_options_df[display_options_df["spatial_reference_id"].astype(str).str.startswith("T")].copy()
    display_options_df = display_options_df.drop_duplicates(subset=["spatial_reference_id"], keep="first")
    for numeric_column in ["distance_to_passer", "forward_progress", "nearest_opponent_distance", "voronoi_area", "pass_score"]:
        if numeric_column in display_options_df.columns:
            display_options_df[numeric_column] = pd.to_numeric(display_options_df[numeric_column], errors="coerce").fillna(0).round(3)
    ordered_columns = [
        col
        for col in ["spatial_reference_id", "distance_to_passer", "forward_progress", "nearest_opponent_distance", "voronoi_area", "voronoi_result", "pass_score"]
        if col in display_options_df.columns
    ]
    if options_columns:
        ordered_columns = [col for col in options_columns if col in display_options_df.columns]
    display_options_df = display_options_df[ordered_columns] if ordered_columns else display_options_df
    display_options_df = drop_empty_display_columns(display_options_df)
    if options_rename_map:
        display_options_df = display_options_df.rename(columns=options_rename_map)
    else:
        display_options_df = display_options_df.rename(columns={"voronoi_result": "Resultado Voronoi"})
    render_metric_table(rename_spatial_reference_column(display_options_df), title=options_title, border=False)


def render_scoring_on_delaunay_recommendation(
    *,
    selected_event: pd.Series,
    freeze_frame_df: pd.DataFrame,
    delaunay_edges_df: pd.DataFrame,
    recommendation: dict,
) -> None:
    """Render the scoring recommendation over a Delaunay pitch for visual consistency."""
    recommendation_fig = plot_delaunay_recommendation(
        selected_event,
        freeze_frame_df,
        delaunay_edges_df,
        recommendation,
        title="Sugerencia según scoring espacial",
    )
    render_plot_card(
        "Sugerencia según scoring espacial",
        recommendation_fig,
        "La alternativa de scoring se representa sobre la triangulación Delaunay junto con el pase sugerido.",
        badges=[("DELAUNAY", "purple"), ("SCORING", "blue"), ("REAL", "red")],
        figure_width=SPATIAL_PLOT_RENDER_WIDTH,
        border=False,
    )
    render_pass_recommendation_details(
        freeze_frame_df=freeze_frame_df,
        recommendation=recommendation,
        breakdown_columns=["Factor", "Valor", "Peso"],
        options_columns=["spatial_reference_id", "pass_score", "distance_to_passer", "forward_progress", "nearest_opponent_distance", "voronoi_area"],
        options_rename_map={"pass_score": "Resultado scoring"},
    )


def render_delaunay_recommendation(
    event_row: pd.Series,
    freeze_frame_df: pd.DataFrame,
    delaunay_edges_df: pd.DataFrame,
    recommendation: dict,
) -> None:
    """Render the Delaunay-based recommendation."""
    recommendation_fig = plot_delaunay_recommendation(event_row, freeze_frame_df, delaunay_edges_df, recommendation)
    render_plot_card(
        "Recomendación Delaunay",
        recommendation_fig,
        "La sugerencia se calcula sobre conectividad local entre jugadores visibles. El pase fallido se muestra en rojo y la sugerencia Delaunay en morado.",
        badges=[("DELAUNAY", "purple"), ("REAL", "red")],
        figure_width=SPATIAL_PLOT_RENDER_WIDTH,
        border=False,
    )

    recommended_player = recommendation.get("recommended_player")
    recommended_reference_id = recommendation.get("spatial_reference_id") or "-"
    score = recommendation.get("delaunay_score")
    reason = str(recommendation.get("reason", "")).strip()

    render_context_bar(
        [
            {"label": "Jugador sugerido", "value": recommended_reference_id},
            {"label": "Score Delaunay", "value": format_score(score)},
        ]
    )
    if recommended_player not in {None, "", "-"}:
        st.caption(f"Nombre del jugador sugerido: {recommended_player}")
    if reason:
        st.caption(reason)

    render_delaunay_score_breakdown_table(recommendation)

    candidates_df = recommendation.get("candidates")
    if not isinstance(candidates_df, pd.DataFrame) or candidates_df.empty:
        render_empty_state(
            "No hay alternativas calculadas todavía para esta vista.",
            "La red Delaunay actual no aporta candidatos suficientes para ordenar opciones.",
        )
        return

    display_candidates_df = merge_spatial_reference_ids(candidates_df.copy(), freeze_frame_df)
    if "spatial_reference_id" in display_candidates_df.columns:
        display_candidates_df = display_candidates_df[display_candidates_df["spatial_reference_id"].astype(str).str.startswith("T")].copy()
    display_candidates_df = display_candidates_df.drop_duplicates(subset=["spatial_reference_id"], keep="first")
    display_candidates_df = display_candidates_df.rename(columns={"distance": "distance_to_passer", "progression": "forward_progress"})
    for numeric_column in ["distance_to_passer", "forward_progress", "edge_length", "delaunay_score"]:
        if numeric_column in display_candidates_df.columns:
            display_candidates_df[numeric_column] = pd.to_numeric(display_candidates_df[numeric_column], errors="coerce").fillna(0).round(3)
    ordered_columns = [col for col in ["spatial_reference_id", "distance_to_passer", "forward_progress", "edge_length", "delaunay_score"] if col in display_candidates_df.columns]
    display_candidates_df = display_candidates_df[ordered_columns] if ordered_columns else display_candidates_df
    display_candidates_df = drop_empty_display_columns(display_candidates_df)
    render_metric_table(rename_spatial_reference_column(display_candidates_df), title="Opciones ordenadas según Delaunay", border=False)


def render_score_breakdown_table(
    recommendation: dict,
    title: str = "Desglose del scoring",
    visible_columns: list[str] | None = None,
) -> None:
    """Render one small table exposing the score components when available."""
    score_breakdown = recommendation.get("score_breakdown")
    if not score_breakdown:
        return

    breakdown_df = pd.DataFrame(score_breakdown)
    if breakdown_df.empty:
        return

    breakdown_df = breakdown_df.rename(
        columns={
            "factor": "Factor",
            "value": "Valor",
            "weight": "Peso",
            "math_weight": "Peso matemático real",
            "priority": "Prioridad",
            "direction": "Sentido",
            "contribution": "Contribución",
        }
    )
    for column in ["Valor", "Peso", "Prioridad", "Contribución"]:
        if column in breakdown_df.columns:
            breakdown_df[column] = pd.to_numeric(breakdown_df[column], errors="coerce").round(3)
    if visible_columns:
        breakdown_df = breakdown_df[[col for col in visible_columns if col in breakdown_df.columns]]
    render_metric_table(breakdown_df, title=title, border=False)


def render_delaunay_score_breakdown_table(recommendation: dict) -> None:
    """Render one small table exposing the Delaunay score components when available."""
    score_breakdown = recommendation.get("score_breakdown")
    if not score_breakdown:
        return

    breakdown_df = pd.DataFrame(score_breakdown)
    if breakdown_df.empty:
        return

    breakdown_df = breakdown_df.rename(
        columns={"factor": "Factor", "value": "Valor", "weight": "Peso", "contribution": "Contribución"}
    )
    for column in ["Valor", "Peso", "Contribución"]:
        if column in breakdown_df.columns:
            breakdown_df[column] = pd.to_numeric(breakdown_df[column], errors="coerce").round(3)
    render_metric_table(breakdown_df, title="Desglose del score Delaunay", border=False)


def render_recommendation_comparison_table(delaunay_recommendation: dict, scoring_recommendation: dict) -> None:
    """Render a compact comparison between the two recommendation methods."""
    render_metric_table(build_recommendation_comparison_df(delaunay_recommendation, scoring_recommendation), border=False)


def render_voronoi_scoring_comparison_table(voronoi_recommendation: dict, scoring_recommendation: dict) -> None:
    """Render a compact comparison between Voronoi-first and scoring recommendations."""
    render_metric_table(build_voronoi_scoring_comparison_df(voronoi_recommendation, scoring_recommendation), border=False)
