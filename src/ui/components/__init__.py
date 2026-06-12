from __future__ import annotations

from src.ui.components.app_header import render_app_header
from src.ui.components.cards import render_empty_state, render_info_box
from src.ui.components.dataframes import (
    build_display_df,
    dataframe_preview,
    limit_dataframe_rows,
    render_limited_dataframe,
    render_method_comparison_table,
    render_metric_table,
)
from src.ui.components.downloads import render_download_csv
from src.ui.components.icons import header_logo_svg, icon_svg
from src.ui.components.kpis import render_kpi_card, render_kpi_grid, render_kpi_row
from src.ui.components.page_header import (
    canonical_view_name,
    navigate_to,
    render_badge,
    render_badges,
    render_context_bar,
    render_page_header,
    render_page_intro,
    render_section_header,
    render_view_hero,
)
from src.ui.components.plots import plot_figure, render_plot_card
from src.ui.components.selectors import render_pill_selector

__all__ = [
    "build_display_df",
    "canonical_view_name",
    "dataframe_preview",
    "header_logo_svg",
    "icon_svg",
    "limit_dataframe_rows",
    "navigate_to",
    "plot_figure",
    "render_app_header",
    "render_badge",
    "render_badges",
    "render_context_bar",
    "render_download_csv",
    "render_empty_state",
    "render_info_box",
    "render_kpi_card",
    "render_kpi_grid",
    "render_kpi_row",
    "render_limited_dataframe",
    "render_method_comparison_table",
    "render_metric_table",
    "render_page_header",
    "render_page_intro",
    "render_pill_selector",
    "render_plot_card",
    "render_section_header",
    "render_view_hero",
]
