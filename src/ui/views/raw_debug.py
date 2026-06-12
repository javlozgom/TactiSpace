from __future__ import annotations

import pandas as pd

from src.ui.components.insight_card import render_insight_card
from src.ui.layout_kit.page import render_page_shell
from src.ui.views.raw_data import render_raw_data_view


RAW_DEBUG_SECTIONS = [
    "🗂️ Datos brutos",
]


def render_raw_debug_view(filtered_df: pd.DataFrame) -> None:
    """Render the grouped raw-data/debug experience."""
    render_page_shell(
        "🗂️ Datos y depuración",
        "Vista técnica de validación del subconjunto activo. Reúne la inspección tabular y la verificación del contexto aplicado.",
        eyebrow="Trazabilidad",
        tone="neutral",
    )
    render_insight_card(
        "Uso recomendado",
        (
            "Utiliza esta vista para comprobar que los filtros globales están aplicados como esperas y para revisar "
            "las filas reales que sostienen cualquier conclusión obtenida en el resto de la app."
        ),
    )
    render_raw_data_view(filtered_df)
