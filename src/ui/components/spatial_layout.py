from __future__ import annotations

import pandas as pd
import streamlit as st

from src.state import spatial as spatial_state
from src.ui.components import render_empty_state, render_metric_table
from src.ui.components.status_card import render_status_card
from src.ui.config.spatial_labels import (
    DELAUNAY_MODULE_HEADER,
    DELAUNAY_SUBVIEW_HELP,
    DELAUNAY_SUBVIEWS,
    SPATIAL_MODULE_HEADER,
    SPATIAL_MODULE_HELP,
    SPATIAL_MODULE_OPTIONS,
    SPATIAL_PAGE_EYEBROW,
    SPATIAL_PAGE_SUBTITLE,
    SPATIAL_PAGE_TITLE,
    VORONOI_MODULE_HEADER,
    VORONOI_SUBVIEW_HELP,
    VORONOI_SUBVIEWS,
)
from src.ui.layout_kit.grid import render_metric_grid
from src.ui.layout_kit.navigation import render_subnav
from src.ui.layout_kit.page import render_page_shell
from src.ui.layout_kit.section import render_section_title


def render_spatial_header() -> None:
    """Render the top hero for the spatial analysis area."""
    render_page_shell(
        SPATIAL_PAGE_TITLE,
        SPATIAL_PAGE_SUBTITLE,
        eyebrow=SPATIAL_PAGE_EYEBROW,
        tone="blue",
    )


def render_spatial_module_nav() -> str:
    """Render the top-level spatial module toggle."""
    default_module = SPATIAL_MODULE_OPTIONS[0][0]
    valid_modules = {module_key for module_key, _ in SPATIAL_MODULE_OPTIONS}
    current_module = st.session_state.get(spatial_state.ACTIVE_MODULE, default_module)
    if current_module not in valid_modules:
        current_module = default_module
        st.session_state[spatial_state.ACTIVE_MODULE] = current_module

    module_labels = [module_label for _, module_label in SPATIAL_MODULE_OPTIONS]
    label_to_key = {module_label: module_key for module_key, module_label in SPATIAL_MODULE_OPTIONS}
    current_label = next(
        (module_label for module_key, module_label in SPATIAL_MODULE_OPTIONS if module_key == current_module),
        SPATIAL_MODULE_OPTIONS[0][1],
    )
    if st.session_state.get(spatial_state.ACTIVE_MODULE_LABEL) not in module_labels:
        st.session_state[spatial_state.ACTIVE_MODULE_LABEL] = current_label

    current_label = render_subnav(
        title=SPATIAL_MODULE_HEADER["title"],
        description=SPATIAL_MODULE_HEADER["description"],
        options=module_labels,
        key=spatial_state.ACTIVE_MODULE_LABEL,
        columns_per_row=2,
        help_text_by_option=SPATIAL_MODULE_HELP,
    )
    current_module = label_to_key.get(current_label, default_module)
    st.session_state[spatial_state.ACTIVE_MODULE] = current_module
    return current_module


def render_spatial_subview_nav(
    *,
    title: str,
    description: str,
    options: list[str],
    key: str,
    default: str,
    help_text_by_option: dict[str, str] | None = None,
) -> str:
    """Render one standardized spatial subnavigation block."""
    current_value = st.session_state.get(key, default)
    if current_value not in options:
        current_value = default
        st.session_state[key] = current_value
    return render_subnav(
        title=title,
        description=description,
        options=options,
        key=key,
        columns_per_row=3,
        help_text_by_option=help_text_by_option,
    )


def render_voronoi_subview_nav() -> str:
    """Render the Voronoi internal navigation."""
    return render_spatial_subview_nav(
        title=VORONOI_MODULE_HEADER["title"],
        description=VORONOI_MODULE_HEADER["description"],
        options=VORONOI_SUBVIEWS,
        key=spatial_state.VORONOI_ACTIVE_SUBVIEW,
        default=VORONOI_SUBVIEWS[0],
        help_text_by_option=VORONOI_SUBVIEW_HELP,
    )


def render_delaunay_subview_nav() -> str:
    """Render the Delaunay internal navigation."""
    return render_spatial_subview_nav(
        title=DELAUNAY_MODULE_HEADER["title"],
        description=DELAUNAY_MODULE_HEADER["description"],
        options=DELAUNAY_SUBVIEWS,
        key=spatial_state.DELAUNAY_ACTIVE_SUBVIEW,
        default=DELAUNAY_SUBVIEWS[0],
        help_text_by_option=DELAUNAY_SUBVIEW_HELP,
    )


def render_spatial_data_status(
    *,
    filtered_df: pd.DataFrame,
    freeze_frames_df: pd.DataFrame,
    failed_passes_df: pd.DataFrame,
    available_failed_passes_df: pd.DataFrame,
    freeze_frame_available: bool,
    freeze_frame_events: int,
    format_ratio,
) -> None:
    """Render high-level spatial data availability cards."""
    _ = freeze_frames_df
    total_filtered_events = len(filtered_df)
    render_metric_grid(
        [
            {
                "label": "Freeze-frame disponible",
                "value": "Sí" if freeze_frame_available else "No",
                "sub": "Datos 360",
                "tone": "blue",
            },
            {
                "label": "Eventos con freeze-frame",
                "value": format_ratio(freeze_frame_events, total_filtered_events),
                "sub": "Cobertura del contexto",
                "tone": "purple",
            },
            {
                "label": "Pases fallidos",
                "value": len(failed_passes_df),
                "sub": "Eventos candidatos",
                "tone": "orange",
            },
            {
                "label": "Pases fallidos con freeze-frame",
                "value": format_ratio(len(available_failed_passes_df), len(failed_passes_df)),
                "sub": "Cobertura analizable",
                "tone": "blue",
            },
        ]
    )

    if not freeze_frame_available:
        render_status_card(
            "Datos 360 no disponibles",
            "No se encontraron datos freeze-frame. Puedes seguir usando la app, pero el análisis espacial requiere datos 360.",
            tone="warning",
        )
    elif len(available_failed_passes_df) < len(failed_passes_df):
        render_status_card(
            "Cobertura 360 parcial",
            "No todos los pases fallidos tienen snapshot 360 asociado. El selector prioriza los eventos con freeze-frame disponible.",
            tone="info",
        )


def render_debug_section(
    title: str,
    table_df: pd.DataFrame,
    *,
    empty_message: str,
    empty_hint: str,
) -> None:
    """Render a debug table or a clean empty state."""
    if table_df.empty:
        render_empty_state(empty_message, empty_hint)
        return
    render_section_title(title)
    render_metric_table(table_df, border=False)


def render_spatial_placeholder(title: str, body: str) -> None:
    """Render a neutral explanatory placeholder."""
    render_status_card(title, body, tone="neutral")
