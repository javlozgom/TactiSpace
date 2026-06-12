from __future__ import annotations

import streamlit as st

from src.ui.components import render_pill_selector, render_section_header


def render_subnav(
    *,
    title: str,
    description: str | None,
    options: list[str],
    key: str,
    columns_per_row: int = 3,
    help_text_by_option: dict[str, str] | None = None,
) -> str:
    """Render one common subnavigation block with helper text."""
    render_section_header(title, description)
    current_value = render_pill_selector(title, options, key, columns_per_row=columns_per_row)
    helper_text = (help_text_by_option or {}).get(current_value)
    if helper_text:
        st.caption(f"Mostrando ahora: {current_value}. {helper_text}")
    else:
        st.caption(f"Mostrando ahora: {current_value}")
    return current_value


def render_button_group(label: str, options: list[str], key: str, *, columns_per_row: int = 4) -> str:
    """Render one compact button group using the shared pill selector."""
    return render_pill_selector(label, options, key, columns_per_row=columns_per_row)
