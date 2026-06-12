from __future__ import annotations

import pandas as pd
import streamlit as st

from src.repositories.export_repository import dataframe_to_csv_bytes


def render_download_csv(
    df: pd.DataFrame,
    filename: str,
    label: str = "Exportar CSV",
) -> None:
    """Render a CSV download button for a dataframe."""
    st.download_button(
        label,
        data=dataframe_to_csv_bytes(df),
        file_name=filename,
        mime="text/csv",
        width="stretch",
        icon=":material/download:",
    )
