from __future__ import annotations

import pandas as pd

from src.ui.components.dataframes import render_metric_table
from src.ui.components.page_header import render_section_header


def render_data_panel(
    df: pd.DataFrame,
    *,
    title: str,
    description: str | None = None,
    border: bool = True,
) -> None:
    """Render one standardized titled data panel."""
    if description:
        render_section_header(title, description)
        render_metric_table(df, border=border)
        return
    render_metric_table(df, title=title, border=border)
