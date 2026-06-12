from __future__ import annotations

import streamlit as st

from src.ui.components import render_info_box


def render_delaunay_reading() -> None:
    """Render textual interpretation and methodological notes focused on Delaunay."""
    render_info_box(
        "Lectura Delaunay",
        (
            "Esta subvista reúne las explicaciones existentes sobre triangulación, conectividad local y "
            "límites de la lectura geométrica."
        ),
        tone="neutral",
    )
    with st.expander("📘 Glosario y notas metodológicas", expanded=True):
        st.markdown(
            "\n".join(
                [
                    "- **Delaunay**: triangulación dual de Voronoi. Aporta una lectura de vecindad y conectividad local.",
                    "- **Aristas Delaunay**: conexiones entre jugadores que funcionan como vecindad geométrica local dentro del snapshot.",
                    "- **Delaunay y equipos**: la triangulación conecta vértices vecinos por proximidad geométrica sin distinguir entre compañeros y rivales.",
                    "- **Vecinos del mismo equipo**: compañeros o rivales conectados entre sí por Delaunay dentro del caso actual.",
                    "- **Recomendación Delaunay**: propone compañeros conectados espacialmente al actor mediante la triangulación.",
                    "- **Unidades de distancia**: distancias al pasador, longitud de arista y distancia al rival más cercano se expresan en unidades del mismo sistema de coordenadas del campo.",
                    "- **Progresión**: avance hacia portería rival medido de forma aproximada por la ganancia en el eje longitudinal del campo.",
                    "- **Unidades de posición**: las coordenadas `x` e `y` se leen en el sistema del campo normalizado por el dataset, con longitud 120 y anchura 80.",
                    "- **Importante**: ninguno de los métodos garantiza que el pase sea técnicamente óptimo o ejecutable.",
                    "- **Limitaciones**: no se modela orientación corporal, velocidad, timing fino ni calidad técnica del ejecutor.",
                ]
            )
        )
