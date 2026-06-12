from __future__ import annotations

import pandas as pd

from src.core.spatial.delaunay import compute_delaunay_edges, recommend_pass_by_delaunay
from src.core.spatial.pass_decision import suggest_alternative_pass, suggest_alternative_pass_by_voronoi_area
from src.core.spatial.voronoi import build_voronoi_regions_with_diagnostics, calculate_space_metrics


def prepare_spatial_event_context(
    *,
    selected_event: pd.Series,
    freeze_frame_df: pd.DataFrame,
    selected_plots: list[str],
    scoring_profile: str,
) -> dict[str, object]:
    """Prepare the common non-visual payload shared by spatial modules."""
    return {
        "selected_event": selected_event,
        "freeze_frame_df": freeze_frame_df,
        "selected_plots": selected_plots,
        "scoring_profile": scoring_profile,
        "warnings": [],
    }


def prepare_voronoi_context(
    *,
    selected_event: pd.Series,
    freeze_frame_df: pd.DataFrame,
    selected_plots: list[str],
    scoring_profile: str,
) -> dict[str, object]:
    """Prepare the base raw Voronoi payload shared by all Voronoi subviews."""
    context = prepare_spatial_event_context(
        selected_event=selected_event,
        freeze_frame_df=freeze_frame_df,
        selected_plots=selected_plots,
        scoring_profile=scoring_profile,
    )

    voronoi_result = build_voronoi_regions_with_diagnostics(freeze_frame_df)
    voronoi_regions_df = voronoi_result.get("regions_df", pd.DataFrame())
    if voronoi_regions_df.empty:
        context["warnings"] = [
            str(
                voronoi_result.get("reason")
                or "No se pudo calcular Voronoi para este freeze-frame. Se mantiene el resto del análisis espacial."
            )
        ]

    combined_edges_df = pd.DataFrame()
    if "combined" in selected_plots:
        combined_edges_df = compute_delaunay_edges(freeze_frame_df)

    context.update(
        {
            "voronoi_result": voronoi_result,
            "voronoi_regions_df": voronoi_regions_df,
            "combined_delaunay_edges_df": combined_edges_df,
        }
    )
    return context


def get_voronoi_metrics_context(
    *,
    freeze_frame_df: pd.DataFrame,
    voronoi_regions_df: pd.DataFrame,
) -> dict[str, object]:
    """Prepare the raw Voronoi metric payload."""
    space_metrics_df = calculate_space_metrics(freeze_frame_df, voronoi_regions_df) if not voronoi_regions_df.empty else pd.DataFrame()
    return {"space_metrics_df": space_metrics_df}


def get_voronoi_alternatives_context(
    *,
    selected_event: pd.Series,
    freeze_frame_df: pd.DataFrame,
    voronoi_regions_df: pd.DataFrame,
    scoring_profile: str,
) -> dict[str, object]:
    """Prepare the raw Voronoi recommendation payload."""
    delaunay_edges_df = compute_delaunay_edges(freeze_frame_df)
    return {
        "delaunay_edges_df": delaunay_edges_df,
        "delaunay_recommendation": recommend_pass_by_delaunay(selected_event, freeze_frame_df, delaunay_edges_df),
        "voronoi_recommendation": suggest_alternative_pass_by_voronoi_area(selected_event, freeze_frame_df, voronoi_regions_df),
        "scoring_recommendation": suggest_alternative_pass(
            selected_event,
            freeze_frame_df,
            voronoi_regions_df,
            scoring_profile=scoring_profile,
        ),
    }


def get_voronoi_debug_context(
    *,
    voronoi_regions_df: pd.DataFrame,
    space_metrics_df: pd.DataFrame,
) -> dict[str, object]:
    """Prepare the raw Voronoi debug payload."""
    return {
        "debug_voronoi_regions_df": voronoi_regions_df.copy() if isinstance(voronoi_regions_df, pd.DataFrame) else pd.DataFrame(),
        "debug_space_metrics_raw_df": space_metrics_df.copy() if isinstance(space_metrics_df, pd.DataFrame) else pd.DataFrame(),
    }


def prepare_delaunay_context(
    *,
    selected_event: pd.Series,
    freeze_frame_df: pd.DataFrame,
    selected_plots: list[str],
    scoring_profile: str,
) -> dict[str, object]:
    """Prepare the base raw Delaunay payload shared by all Delaunay subviews."""
    context = prepare_spatial_event_context(
        selected_event=selected_event,
        freeze_frame_df=freeze_frame_df,
        selected_plots=selected_plots,
        scoring_profile=scoring_profile,
    )
    context["delaunay_edges_df"] = compute_delaunay_edges(freeze_frame_df)
    voronoi_regions_df = pd.DataFrame()
    if "combined" in selected_plots:
        voronoi_result = build_voronoi_regions_with_diagnostics(freeze_frame_df)
        voronoi_regions_df = voronoi_result.get("regions_df", pd.DataFrame())
        if voronoi_regions_df.empty:
            context["warnings"] = [
                str(
                    voronoi_result.get("reason")
                    or "No se pudo calcular Voronoi para la vista combinada. Se mantiene el resto del análisis Delaunay."
                )
            ]
    context["voronoi_regions_df"] = voronoi_regions_df
    return context


def get_delaunay_connections_context(
    *,
    delaunay_edges_df: pd.DataFrame,
) -> dict[str, object]:
    """Prepare the raw Delaunay connection payload."""
    return {"delaunay_edges_df": delaunay_edges_df}


def get_delaunay_alternatives_context(
    *,
    selected_event: pd.Series,
    freeze_frame_df: pd.DataFrame,
    scoring_profile: str,
    delaunay_edges_df: pd.DataFrame,
) -> dict[str, object]:
    """Prepare the raw Delaunay recommendation payload."""
    voronoi_result = build_voronoi_regions_with_diagnostics(freeze_frame_df)
    voronoi_regions_df = voronoi_result.get("regions_df", pd.DataFrame())
    return {
        "voronoi_result": voronoi_result,
        "voronoi_regions_df": voronoi_regions_df,
        "delaunay_recommendation": recommend_pass_by_delaunay(selected_event, freeze_frame_df, delaunay_edges_df),
        "scoring_recommendation": suggest_alternative_pass(
            selected_event,
            freeze_frame_df,
            voronoi_regions_df,
            scoring_profile=scoring_profile,
        ),
    }


def get_delaunay_debug_context(
    *,
    delaunay_edges_df: pd.DataFrame,
) -> dict[str, object]:
    """Prepare the raw Delaunay debug payload."""
    return {
        "debug_edges_raw_df": delaunay_edges_df.copy() if isinstance(delaunay_edges_df, pd.DataFrame) else pd.DataFrame(),
    }
