from __future__ import annotations

import pandas as pd

from src.ui.views.spatial_formatters import format_coordinate_pair, safe_display
from src.ui.views.spatial_utils import (
    coalesce_event_value,
    count_opponents,
    count_teammates,
    count_visible_players,
    freeze_frame_has_actor,
)


def build_event_diagnostics(event_row: pd.Series, freeze_frame_df: pd.DataFrame) -> list[dict[str, object]]:
    """Build one compact diagnostic summary for export and downstream reuse."""
    return [
        {"Campo": "match_id / partido", "Valor": coalesce_event_value(event_row, ["match_id", "partido"])},
        {"Campo": "minuto y segundo", "Valor": f"{safe_display(event_row.get('minute'))}:{safe_display(event_row.get('second'))}"},
        {"Campo": "jugador", "Valor": safe_display(event_row.get("player"))},
        {"Campo": "equipo", "Valor": safe_display(event_row.get("team"))},
        {"Campo": "tipo de evento", "Valor": safe_display(coalesce_event_value(event_row, ["event_type", "type", "type_name"]))},
        {"Campo": "coordenadas inicio x,y", "Valor": format_coordinate_pair(event_row.get("x"), event_row.get("y"))},
        {"Campo": "coordenadas destino end_x,end_y", "Valor": format_coordinate_pair(event_row.get("end_x"), event_row.get("end_y"))},
        {"Campo": "freeze-frame disponible", "Valor": "Sí" if not freeze_frame_df.empty else "No"},
        {"Campo": "jugadores visibles", "Valor": count_visible_players(freeze_frame_df)},
        {"Campo": "compañeros visibles", "Valor": count_teammates(freeze_frame_df)},
        {"Campo": "rivales visibles", "Valor": count_opponents(freeze_frame_df)},
        {"Campo": "actor detectado", "Valor": "Sí" if freeze_frame_has_actor(freeze_frame_df) else "No"},
    ]


def build_event_diagnostics_display_df(
    selected_event: pd.Series,
    freeze_frame_df: pd.DataFrame,
) -> pd.DataFrame:
    """Prepare the diagnostics table for Streamlit display with a stable text column type."""
    diagnostics_df = pd.DataFrame(build_event_diagnostics(selected_event, freeze_frame_df))
    if diagnostics_df.empty or "Valor" not in diagnostics_df.columns:
        return diagnostics_df
    diagnostics_df["Valor"] = diagnostics_df["Valor"].map(safe_display)
    return diagnostics_df
