from __future__ import annotations

import streamlit as st

from src.ui.style_system.assets import header_background_image, hero_visual_image
from src.ui.style_system.components_css import build_components_css
from src.ui.style_system.layout_css import build_layout_css
from src.ui.style_system.shell_css import build_shell_css
from src.ui.style_system.widgets_css import build_widgets_css


def build_global_css() -> str:
    """Return shared CSS extensions for the centralized layout system."""
    shell_css = build_shell_css()
    layout_css = build_layout_css(header_background_image())
    components_css = build_components_css(hero_visual_image())
    widgets_css = build_widgets_css()
    return f"""
        <style>
        {shell_css}
        {layout_css}
        {components_css}
        {widgets_css}

        .tacti-page-stack,
        .tacti-section-stack,
        .tacti-block-stack {{
            display: grid;
            gap: var(--tacti-section-gap);
        }}

        .tacti-toolbar,
        .tacti-subnav-note,
        .tacti-data-panel-note,
        .tacti-debug-note,
        .tacti-caption {{
            color: var(--tacti-muted);
            font-size: var(--tacti-caption-size);
            line-height: 1.45;
        }}

        .tacti-card-shell,
        .tacti-data-panel,
        .tacti-debug-panel,
        .tacti-toolbar-shell,
        .tacti-status-shell {{
            background: linear-gradient(180deg, #ffffff, var(--tacti-panel-bg));
            border: 1px solid var(--tacti-border);
            border-radius: var(--tacti-panel-radius);
            box-shadow: var(--tacti-subtle-shadow);
            padding: var(--tacti-card-padding);
        }}

        .tacti-card-shell + .tacti-card-shell,
        .tacti-data-panel + .tacti-data-panel,
        .tacti-debug-panel + .tacti-debug-panel {{
            margin-top: var(--tacti-space-md);
        }}

        .tacti-inline-gap {{ height: var(--tacti-space-sm); }}

        .tacti-subnav-wrap [data-testid="stHorizontalBlock"],
        .tacti-grid-2 [data-testid="stHorizontalBlock"],
        .tacti-grid-3 [data-testid="stHorizontalBlock"],
        .tacti-grid-4 [data-testid="stHorizontalBlock"] {{
            gap: var(--tacti-grid-gap) !important;
        }}

        .tacti-quiet-divider {{
            margin: var(--tacti-space-lg) 0 !important;
            border-top: 1px solid rgba(148, 163, 184, .24) !important;
        }}
        </style>
    """


def apply_global_styles() -> None:
    """Inject the shared CSS extension layer."""
    st.markdown(build_global_css(), unsafe_allow_html=True)
