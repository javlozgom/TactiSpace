from __future__ import annotations

import pandas as pd
import streamlit as st

from src.ui.components import dataframe_preview
from src.ui.components.metric_card import render_metric_cards
from src.ui.layout_kit.page import render_page_shell
from src.ui.layout_kit.section import render_section_title


def _render_dataset_cards() -> None:
    """Render transparent dataset metadata for the normalized pipeline."""
    datasets = [
        ("Eventos", "data/processed/events_normalized.parquet", "Fuente principal de la app."),
        ("Lineups", "data/processed/lineups_normalized.parquet", "Enriquecimiento por jugador y posición."),
        ("360", "data/processed/three_sixty_normalized.parquet", "Freeze-frames y análisis espacial."),
        ("Matches", "data/raw/statsbomb/euro_2024/matches.json", "Etiquetas legibles de partidos."),
    ]
    with st.container(border=True):
        cols = st.columns(4, gap="large", vertical_alignment="top")
        for column, (title, path, body) in zip(cols, datasets):
            with column:
                st.markdown(f"**{title}**")
                st.caption(path)
                st.write(body)


def render_raw_data_view(events_df: pd.DataFrame) -> None:
    """Render the raw normalized data view."""
    render_page_shell(
        "Datos brutos",
        "Inspección del subconjunto procesado según el filtro global.",
        eyebrow="Datos",
        tone="neutral",
    )
    if not events_df.empty:
        render_metric_cards(
            [
                {"label": "Filas", "value": f"{len(events_df):,}", "icon": "list", "tone": "blue"},
                {"label": "Columnas", "value": len(events_df.columns), "icon": "table", "tone": "teal"},
                {
                    "label": "Partidos",
                    "value": f"{events_df['match_id'].nunique():,}" if "match_id" in events_df.columns else "-",
                    "icon": "map-pin",
                    "tone": "purple",
                },
            ]
        )
        st.divider()
    render_section_title("Datasets normalizados", "Rutas usadas por la aplicación y papel de cada fichero.")
    _render_dataset_cards()
    st.divider()
    render_section_title("Tabla principal", "Vista del dataset normalizado ajustado al contexto filtrado.")
    with st.container(border=True):
        dataframe_preview(events_df, "Datos normalizados")
