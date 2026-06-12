from __future__ import annotations

import pandas as pd
import streamlit as st

from src.ui.components.spatial_layout import render_voronoi_subview_nav
from src.ui.config.spatial_labels import VORONOI_SUBVIEWS
from src.ui.presenters.spatial_presenter import build_voronoi_ui_context
from src.ui.views.spatial_voronoi_alternatives import render_voronoi_alternatives
from src.ui.views.spatial_voronoi_metrics import render_voronoi_metrics
from src.ui.views.spatial_voronoi_view import render_voronoi_view


def render_voronoi_panel(
    *,
    selected_event: pd.Series,
    freeze_frame_df: pd.DataFrame,
    selected_plots: list[str],
    scoring_profile: str,
) -> None:
    """Render the Voronoi analysis module with a prepared UI context."""
    active_subview = render_voronoi_subview_nav()
    if active_subview not in VORONOI_SUBVIEWS:
        active_subview = VORONOI_SUBVIEWS[0]
    context = build_voronoi_ui_context(
        selected_event=selected_event,
        freeze_frame_df=freeze_frame_df,
        active_subview=active_subview,
        selected_plots=selected_plots,
        scoring_profile=scoring_profile,
    )
    for warning in context.get("warnings", []):
        st.info(warning)

    if active_subview == VORONOI_SUBVIEWS[0]:
        render_voronoi_view(context=context)
    elif active_subview == VORONOI_SUBVIEWS[1]:
        render_voronoi_metrics(context=context)
    elif active_subview == VORONOI_SUBVIEWS[2]:
        render_voronoi_alternatives(context=context)
    else:
        render_voronoi_view(context=context)
