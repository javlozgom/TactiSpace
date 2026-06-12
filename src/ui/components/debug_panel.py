from __future__ import annotations

import pandas as pd
import streamlit as st

from src.ui.components.cards import render_empty_state
from src.ui.components.dataframes import render_metric_table
from src.ui.components.page_header import render_section_header


def render_debug_panel(
    *,
    title: str,
    dataframes: list[tuple[str, pd.DataFrame]],
    empty_message: str,
    empty_hint: str,
    expanded: bool = False,
) -> None:
    """Render one standardized technical/debug expander."""
    non_empty_items = [(label, df) for label, df in dataframes if not df.empty]
    with st.expander(title, expanded=expanded):
        if not non_empty_items:
            render_empty_state(empty_message, empty_hint)
            return
        for label, df in non_empty_items:
            render_section_header(label)
            render_metric_table(df, border=False)
