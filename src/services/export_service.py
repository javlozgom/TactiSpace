from __future__ import annotations

import pandas as pd

from src.repositories.export_repository import dataframe_to_csv_bytes, figure_to_png_bytes


def build_dataframe_export(df: pd.DataFrame) -> bytes:
    """Return CSV bytes for dataframe downloads."""
    return dataframe_to_csv_bytes(df)


def build_figure_export(fig) -> bytes:
    """Return PNG bytes for figure downloads."""
    return figure_to_png_bytes(fig)
