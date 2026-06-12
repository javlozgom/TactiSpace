from __future__ import annotations

import pandas as pd

from src.ui.components.spatial_layout import render_delaunay_subview_nav
from src.ui.config.spatial_labels import DELAUNAY_SUBVIEWS
from src.ui.presenters.spatial_presenter import build_delaunay_ui_context
from src.ui.views.spatial_delaunay_alternatives import render_delaunay_alternatives
from src.ui.views.spatial_delaunay_connections import render_delaunay_connections
from src.ui.views.spatial_delaunay_network import render_delaunay_network


def render_delaunay_panel(
    *,
    selected_event: pd.Series,
    freeze_frame_df: pd.DataFrame,
    selected_plots: list[str],
    scoring_profile: str,
) -> None:
    """Render the Delaunay analysis module with a prepared UI context."""
    active_subview = render_delaunay_subview_nav()
    if active_subview not in DELAUNAY_SUBVIEWS:
        active_subview = DELAUNAY_SUBVIEWS[0]
    context = build_delaunay_ui_context(
        selected_event=selected_event,
        freeze_frame_df=freeze_frame_df,
        active_subview=active_subview,
        selected_plots=selected_plots,
        scoring_profile=scoring_profile,
    )

    if active_subview == DELAUNAY_SUBVIEWS[0]:
        render_delaunay_network(context=context)
    elif active_subview == DELAUNAY_SUBVIEWS[1]:
        render_delaunay_connections(context=context)
    elif active_subview == DELAUNAY_SUBVIEWS[2]:
        render_delaunay_alternatives(context=context)
    else:
        render_delaunay_network(context=context)
