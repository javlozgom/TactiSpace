from __future__ import annotations

import pandas as pd

from src.ui.components import render_context_bar
from src.ui.components.spatial_visualizations import plot_delaunay_recommendation
from src.ui.views.spatial_case_selector import (
    SPATIAL_DEMO_CASES_PATH,
    build_match_labels,
    ensure_spatial_case_picker_state,
    filter_failed_passes_with_freeze_frame,
    format_failed_pass_label,
    format_match_label,
    is_spatial_case_picker_visible,
    render_failed_pass_selector,
    render_scoring_profile_info_box,
    render_spatial_view_controls,
    resolve_default_selector_index,
    resolve_preselected_event_id,
    resolve_spatial_controls_state,
    show_spatial_case_picker,
    store_selected_spatial_event_id,
)
from src.ui.views.spatial_debug import render_delaunay_debug_section, render_voronoi_debug_section
from src.ui.views.spatial_exports import build_spatial_case_export_df, render_case_export_section
from src.ui.views.spatial_formatters import (
    describe_scoring_profile_compact,
    format_coordinate_pair,
    format_location,
    format_ratio,
    format_score,
    normalize_coordinate_key,
    normalize_merge_key,
    normalize_recommendation_text,
    safe_display,
    safe_int_like,
    spatial_reference_sort_key,
)
from src.ui.views.spatial_recommendation_ui import (
    render_delaunay_recommendation,
    render_delaunay_score_breakdown_table,
    render_pass_recommendation,
    render_pass_recommendation_details,
    render_recommendation_comparison_table,
    render_score_breakdown_table,
    render_scoring_on_delaunay_recommendation,
    render_voronoi_scoring_comparison_table,
)
from src.ui.tables import (
    build_delaunay_edges_debug_df,
    build_delaunay_neighbors_df,
    build_display_space_metrics_df,
    build_event_diagnostics,
    build_event_diagnostics_display_df,
    build_recommendation_comparison_df,
    build_voronoi_debug_df,
    build_voronoi_scoring_comparison_df,
    build_voronoi_team_summary_df,
    drop_empty_display_columns,
    lookup_spatial_reference_id,
    merge_spatial_reference_ids,
    rename_spatial_reference_column,
)
from src.ui.views.spatial_utils import (
    assign_spatial_reference_ids,
    coalesce_event_value,
    count_opponents,
    count_teammates,
    count_visible_players,
    extract_event_id,
    freeze_frame_has_actor,
    visible_freeze_frame_df,
)


def _get_match_labels() -> dict[str, str]:
    """Compatibility wrapper for cached match labels."""
    return build_match_labels()


def count_freeze_frame_events_in_context(
    filtered_df: pd.DataFrame,
    freeze_frames_df: pd.DataFrame,
) -> int:
    """Count unique freeze-frame events that belong to the current filtered context."""
    if filtered_df.empty or freeze_frames_df.empty:
        return 0
    if "event_id" not in filtered_df.columns or "event_id" not in freeze_frames_df.columns:
        return 0

    visible_event_ids = set(filtered_df["event_id"].dropna().astype(str).tolist())
    if not visible_event_ids:
        return 0

    return int(
        freeze_frames_df["event_id"]
        .dropna()
        .astype(str)
        .loc[lambda series: series.isin(visible_event_ids)]
        .nunique()
    )
