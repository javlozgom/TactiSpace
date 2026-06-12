from __future__ import annotations

import streamlit as st

from src.ui.components import render_kpi_grid


def render_metric_grid(items: list[dict]) -> None:
    """Render one standardized metric grid."""
    render_kpi_grid(items)


def render_responsive_columns(count: int, *, gap: str = "large", vertical_alignment: str = "top"):
    """Return one responsive Streamlit columns group."""
    return st.columns(count, gap=gap, vertical_alignment=vertical_alignment)
