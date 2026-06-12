from __future__ import annotations

import pandas as pd

from src.services.spatial_analysis_service import (
    get_delaunay_alternatives_context,
    get_delaunay_connections_context,
    get_delaunay_debug_context,
    get_voronoi_alternatives_context,
    get_voronoi_debug_context,
    get_voronoi_metrics_context,
    prepare_delaunay_context,
    prepare_voronoi_context,
)
from src.ui.config.spatial_labels import DELAUNAY_SUBVIEWS, VORONOI_SUBVIEWS
from src.ui.tables import (
    build_delaunay_edge_distances_df,
    build_delaunay_edges_debug_df,
    build_delaunay_neighbors_df,
    build_display_space_metrics_df,
    build_event_diagnostics_display_df,
    build_voronoi_debug_df,
    build_voronoi_team_summary_df,
    lookup_spatial_reference_id,
    rename_spatial_reference_column,
)
from src.ui.views.spatial_formatters import normalize_recommendation_text


def build_voronoi_ui_context(
    *,
    selected_event: pd.Series,
    freeze_frame_df: pd.DataFrame,
    active_subview: str,
    selected_plots: list[str],
    scoring_profile: str,
) -> dict[str, object]:
    """Build the UI-ready Voronoi context for the requested subview."""
    base_context = prepare_voronoi_context(
        selected_event=selected_event,
        freeze_frame_df=freeze_frame_df,
        selected_plots=selected_plots,
        scoring_profile=scoring_profile,
    )
    ui_context = _build_spatial_base_ui_context(base_context, active_subview)
    ui_context["delaunay_edges_df"] = ui_context.pop("combined_delaunay_edges_df", pd.DataFrame())

    if active_subview == VORONOI_SUBVIEWS[1]:
        metrics_context = get_voronoi_metrics_context(
            freeze_frame_df=freeze_frame_df,
            voronoi_regions_df=ui_context["voronoi_regions_df"],
        )
        ui_context.update(_build_voronoi_metrics_ui_context(metrics_context, freeze_frame_df, ui_context["voronoi_regions_df"]))
    elif active_subview == VORONOI_SUBVIEWS[2]:
        alternatives_context = get_voronoi_alternatives_context(
            selected_event=selected_event,
            freeze_frame_df=freeze_frame_df,
            voronoi_regions_df=ui_context["voronoi_regions_df"],
            scoring_profile=scoring_profile,
        )
        ui_context.update(_build_voronoi_alternatives_ui_context(alternatives_context, freeze_frame_df, scoring_profile))

    return ui_context


def build_delaunay_ui_context(
    *,
    selected_event: pd.Series,
    freeze_frame_df: pd.DataFrame,
    active_subview: str,
    selected_plots: list[str],
    scoring_profile: str,
) -> dict[str, object]:
    """Build the UI-ready Delaunay context for the requested subview."""
    base_context = prepare_delaunay_context(
        selected_event=selected_event,
        freeze_frame_df=freeze_frame_df,
        selected_plots=selected_plots,
        scoring_profile=scoring_profile,
    )
    ui_context = _build_spatial_base_ui_context(base_context, active_subview)

    if active_subview == DELAUNAY_SUBVIEWS[1]:
        connections_context = get_delaunay_connections_context(delaunay_edges_df=ui_context["delaunay_edges_df"])
        ui_context.update(_build_delaunay_connections_ui_context(connections_context, freeze_frame_df))
    elif active_subview == DELAUNAY_SUBVIEWS[2]:
        alternatives_context = get_delaunay_alternatives_context(
            selected_event=selected_event,
            freeze_frame_df=freeze_frame_df,
            scoring_profile=scoring_profile,
            delaunay_edges_df=ui_context["delaunay_edges_df"],
        )
        ui_context.update(_build_delaunay_alternatives_ui_context(alternatives_context, freeze_frame_df, scoring_profile))

    return ui_context


def _build_spatial_base_ui_context(base_context: dict[str, object], active_subview: str) -> dict[str, object]:
    """Add UI-ready defaults shared by Voronoi and Delaunay."""
    selected_event = base_context["selected_event"]
    freeze_frame_df = base_context["freeze_frame_df"]
    return {
        **base_context,
        "active_subview": active_subview,
        "event_diagnostics_df": build_event_diagnostics_display_df(selected_event, freeze_frame_df),
        "debug_voronoi_df": pd.DataFrame(),
        "debug_space_metrics_df": pd.DataFrame(),
        "debug_space_metrics_display_df": pd.DataFrame(),
        "debug_edges_df": pd.DataFrame(),
        "display_space_metrics_df": pd.DataFrame(),
        "display_space_metrics_display_df": pd.DataFrame(),
        "team_summary_df": pd.DataFrame(),
        "neighbors_df": pd.DataFrame(),
        "edge_distances_df": pd.DataFrame(),
        "delaunay_recommendation": {},
        "voronoi_recommendation": {},
        "scoring_recommendation": {},
    }


def _build_voronoi_metrics_ui_context(
    metrics_context: dict[str, object],
    freeze_frame_df: pd.DataFrame,
    voronoi_regions_df: pd.DataFrame,
) -> dict[str, object]:
    space_metrics_df = metrics_context["space_metrics_df"]
    display_space_metrics_df = build_display_space_metrics_df(space_metrics_df, freeze_frame_df)
    return {
        "space_metrics_df": space_metrics_df,
        "display_space_metrics_df": display_space_metrics_df,
        "display_space_metrics_display_df": rename_spatial_reference_column(display_space_metrics_df),
        "team_summary_df": build_voronoi_team_summary_df(voronoi_regions_df, freeze_frame_df),
    }


def _build_voronoi_alternatives_ui_context(
    alternatives_context: dict[str, object],
    freeze_frame_df: pd.DataFrame,
    scoring_profile: str,
) -> dict[str, object]:
    normalized_context = dict(alternatives_context)
    _normalize_recommendations(
        freeze_frame_df,
        [
            normalized_context.get("delaunay_recommendation"),
            normalized_context.get("voronoi_recommendation"),
            normalized_context.get("scoring_recommendation"),
        ],
        scoring_profile,
    )
    return normalized_context


def _build_voronoi_debug_ui_context(
    debug_context: dict[str, object],
    freeze_frame_df: pd.DataFrame,
) -> dict[str, object]:
    debug_space_metrics_df = build_display_space_metrics_df(debug_context["debug_space_metrics_raw_df"], freeze_frame_df)
    return {
        "debug_voronoi_df": build_voronoi_debug_df(debug_context["debug_voronoi_regions_df"]),
        "debug_space_metrics_df": debug_space_metrics_df,
        "debug_space_metrics_display_df": rename_spatial_reference_column(debug_space_metrics_df),
    }


def _build_delaunay_connections_ui_context(
    connections_context: dict[str, object],
    freeze_frame_df: pd.DataFrame,
) -> dict[str, object]:
    return {
        "neighbors_df": build_delaunay_neighbors_df(freeze_frame_df, connections_context["delaunay_edges_df"]),
        "edge_distances_df": build_delaunay_edge_distances_df(freeze_frame_df, connections_context["delaunay_edges_df"]),
    }


def _build_delaunay_alternatives_ui_context(
    alternatives_context: dict[str, object],
    freeze_frame_df: pd.DataFrame,
    scoring_profile: str,
) -> dict[str, object]:
    normalized_context = dict(alternatives_context)
    _normalize_recommendations(
        freeze_frame_df,
        [
            normalized_context.get("delaunay_recommendation"),
            normalized_context.get("scoring_recommendation"),
        ],
        scoring_profile,
    )
    return normalized_context


def _build_delaunay_debug_ui_context(debug_context: dict[str, object]) -> dict[str, object]:
    return {"debug_edges_df": build_delaunay_edges_debug_df(debug_context["debug_edges_raw_df"])}


def _normalize_recommendations(
    freeze_frame_df: pd.DataFrame,
    recommendations: list[dict | None],
    scoring_profile: str,
) -> None:
    """Attach local ids and normalized labels to recommendation payloads."""
    for recommendation in recommendations:
        if not isinstance(recommendation, dict):
            continue
        recommendation["spatial_reference_id"] = lookup_spatial_reference_id(
            freeze_frame_df,
            recommendation.get("recommended_player"),
            recommendation.get("recommended_location"),
        )
        recommendation["resolved_scoring_profile"] = scoring_profile
        normalize_recommendation_text(recommendation)
