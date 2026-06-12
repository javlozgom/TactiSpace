from __future__ import annotations

import streamlit as st

from src.ui.components import render_info_box


def render_voronoi_reading(*, voronoi_result: dict[str, object]) -> None:
    """Render textual interpretation and methodological notes focused on Voronoi."""
    reason = str(voronoi_result.get("reason") or "").strip()
    if reason:
        st.info(reason)
        st.divider()

    render_info_box(
        "Lectura Voronoi",
        (
            "Esta subvista reúne las explicaciones existentes sobre espacio, áreas de influencia y "
            "limitaciones del análisis basado en proximidad."
        ),
        tone="neutral",
    )
    with st.expander("📘 Glosario y notas metodológicas", expanded=True):
        st.markdown(
            "\n".join(
                [
                    "- **Freeze-frame**: snapshot 360 del contexto del evento, con posiciones visibles de compañeros y rivales.",
                    "- **Actor**: jugador que ejecuta la acción analizada; en esta pestaña actúa como origen del pase fallido.",
                    "- **Jugadores visibles**: futbolistas que aparecen en el freeze-frame del caso. Toda la lectura espacial depende solo de ellos.",
                    "- **Identificadores T*/R***: numeración local del caso. `T1`, `T2`... identifican compañeros visibles y `R1`, `R2`... rivales visibles.",
                    "- **Voronoi**: divide el espacio según proximidad. Cada región representa la zona de influencia aproximada de un jugador.",
                    "- **Área Voronoi**: superficie aproximada asociada a cada jugador visible. Más área suele implicar más espacio potencial alrededor de ese punto.",
                    "- **Unidades de área**: el área Voronoi se expresa en unidades cuadradas del sistema de coordenadas del campo usado por los datos.",
                    "- **Influencia espacial por equipo**: suma de áreas Voronoi de los jugadores visibles de cada equipo. Es una aproximación local, no posesión real del campo.",
                    "- **Unidades porcentuales**: métricas como `% influencia espacial` son proporciones relativas calculadas dentro del freeze-frame visible del caso.",
                    "- **Presión cercana**: proximidad del rival más cercano al posible receptor; cuanto mayor distancia, menor presión inmediata.",
                    "- **Score / scoring**: valor heurístico usado para ordenar alternativas. Sirve para comparar opciones dentro del mismo caso, no como probabilidad real de éxito.",
                    "- **Importante**: ninguno de los métodos garantiza que el pase sea técnicamente óptimo o ejecutable.",
                    "- **Limitaciones**: no se modela orientación corporal, velocidad, timing fino ni calidad técnica del ejecutor.",
                ]
            )
        )
