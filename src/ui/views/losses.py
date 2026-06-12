from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from src.repositories.export_repository import figure_to_png_bytes
from src.services.losses_service import (
    calculate_failed_pass_metrics,
    get_failed_pass_context,
    get_failed_passes,
    summarize_failed_passes_by_player,
)
from src.services.losses_service import (
    calculate_loss_metrics,
    get_dangerous_losses,
    get_loss_events,
    summarize_losses_by_player,
)
from src.core.models.player_labels import apply_player_display_names, build_player_label_maps
from src.ui.navigation_config import EVENT_ANALYSIS_SECTIONS, EVENT_ANALYSIS_VIEW
from src.ui.components import (
    render_badges,
    render_context_bar,
    render_download_csv,
    render_empty_state,
    render_kpi_grid,
    render_metric_table,
    render_page_header,
    render_plot_card,
    render_section_header,
)
from src.ui.components.visualizations import plot_events_on_pitch


def render_losses_view(filtered_df: pd.DataFrame) -> None:
    """Render the losses analysis view."""
    render_page_header(
        "Pérdidas",
        "Clasifica pérdidas, profundiza en failed passes y conecta los eventos críticos con el módulo espacial.",
        eyebrow="Pérdidas",
    )
    render_context_bar(
        [
            {"label": "Eventos", "value": len(filtered_df)},
            {"label": "Jugadores", "value": filtered_df["player"].nunique() if not filtered_df.empty else 0},
            {"label": "Equipos", "value": filtered_df["team"].nunique() if not filtered_df.empty else 0},
        ]
    )

    loss_df = get_loss_events(filtered_df)
    failed_pass_df = get_failed_passes(filtered_df)
    full_to_display, _ = build_player_label_maps(filtered_df)
    filter_cols = st.columns(2)
    with filter_cols[0]:
        loss_type = st.selectbox(
            "Tipo de pérdida",
            ["Todos", "Failed Pass", "Failed Dribble", "Miscontrol", "Dispossessed", "Error"],
            key="losses_view_type_filter",
        )
    with filter_cols[1]:
        zone_filter = st.selectbox(
            "Zona",
            ["Todas", "Campo propio", "Campo rival", "Último tercio"],
            key="losses_view_zone_filter",
    )

    if loss_type == "Failed Pass":
        render_badges([("FAILED PASS", "red")])
        _render_failed_passes_inside_losses(
            filtered_df=filtered_df,
            failed_pass_df=failed_pass_df,
            zone_filter=zone_filter,
            full_to_display=full_to_display,
        )
        return

    filtered_loss_df = _apply_loss_view_filters(loss_df, loss_type, zone_filter)
    metrics = calculate_loss_metrics(filtered_loss_df)
    summary_df = apply_player_display_names(
        summarize_losses_by_player(filtered_loss_df),
        full_to_display,
    )

    render_kpi_grid(
        [
            {"label": "Pérdidas totales", "value": metrics["total_losses"], "sub": "Volumen agregado", "tone": "red", "icon": "alert-triangle"},
            {"label": "Campo propio", "value": metrics["losses_own_half"], "sub": "Riesgo en salida", "tone": "orange", "icon": "shield-x"},
            {"label": "Campo rival", "value": metrics["losses_opponent_half"], "sub": "Riesgo en campo rival", "tone": "purple", "icon": "map-pin"},
            {"label": "Último tercio", "value": metrics["losses_final_third"], "sub": "Riesgo ofensivo", "tone": "orange", "icon": "target"},
            {"label": "Pases fallidos", "value": metrics["failed_passes"], "sub": "Failed pass", "tone": "red", "icon": "send"},
            {"label": "Regates fallidos", "value": metrics["failed_dribbles"], "sub": "Failed dribble", "tone": "teal", "icon": "route"},
        ]
    )

    content_cols = st.columns([1.3, 1], vertical_alignment="top")
    with content_cols[0]:
        if filtered_loss_df.empty:
            render_section_header("Mapa de pérdidas")
            render_empty_state(
                "No hay pérdidas para los filtros seleccionados.",
                "Prueba a ampliar el rango de minutos o seleccionar Todos en jugador.",
            )
        else:
            loss_map_fig = plot_events_on_pitch(
                filtered_loss_df,
                title="Mapa de pérdidas",
                draw_movements=True,
                show_legend=True,
            )
            render_plot_card(
                "Mapa de pérdidas",
                loss_map_fig,
                "Localiza visualmente dónde se originan las pérdidas del contexto activo.",
                allow_expand=False,
            )
            st.download_button(
                "Exportar mapa PNG",
                data=figure_to_png_bytes(loss_map_fig),
                file_name="losses_map.png",
                mime="image/png",
                width="stretch",
                icon=":material/download:",
            )
            plt.close(loss_map_fig)

    with content_cols[1]:
        render_section_header("Resumen por jugador")
        render_metric_table(summary_df)
        render_download_csv(summary_df, "losses_summary.csv", label="Exportar resumen CSV")

    render_section_header("Pérdidas peligrosas", "Bloque específico de riesgo contextual.")
    _render_dangerous_losses_section(filtered_df, full_to_display)


def _render_dangerous_losses_section(
    filtered_df: pd.DataFrame,
    full_to_display: dict[str, str],
) -> None:
    """Render dangerous losses with its own filters, map and exports."""
    dangerous_losses_df = get_dangerous_losses(filtered_df)

    render_section_header("Qué se considera una pérdida peligrosa")
    st.caption(
        "Se etiquetan como peligrosas las pérdidas que, por su contexto espacial y de transición, dejan al rival en una situación potencialmente ventajosa. Úsalo como una señal de riesgo contextual, no como una verdad táctica absoluta."
    )

    filter_cols = st.columns(2)
    with filter_cols[0]:
        dangerous_loss_type = st.selectbox(
            "Tipo de pérdida peligrosa",
            ["Todos", "Failed Pass", "Failed Dribble", "Miscontrol", "Dispossessed", "Error"],
            key="dangerous_losses_view_type_filter",
        )
    with filter_cols[1]:
        dangerous_zone_filter = st.selectbox(
            "Zona de pérdida peligrosa",
            ["Todas", "Campo propio", "Campo rival", "Último tercio"],
            key="dangerous_losses_view_zone_filter",
        )

    dangerous_losses_filtered_df = apply_player_display_names(
        _apply_loss_view_filters(
            dangerous_losses_df,
            dangerous_loss_type,
            dangerous_zone_filter,
        ),
        full_to_display,
    )
    dangerous_summary_df = apply_player_display_names(
        summarize_losses_by_player(dangerous_losses_filtered_df),
        full_to_display,
    )

    if dangerous_losses_filtered_df.empty:
        render_empty_state(
            "No hay pérdidas peligrosas para los filtros seleccionados.",
            "Prueba a ampliar el rango de minutos o revisar la zona seleccionada.",
        )
        return

    content_cols = st.columns([1.3, 1], vertical_alignment="top")
    with content_cols[0]:
        dangerous_loss_map_fig = plot_events_on_pitch(
            dangerous_losses_filtered_df,
            title="Mapa de pérdidas peligrosas",
            draw_movements=True,
            show_legend=True,
        )
        render_plot_card(
            "Mapa de pérdidas peligrosas",
            dangerous_loss_map_fig,
            "Localiza visualmente dónde se originan las pérdidas peligrosas del contexto activo.",
            allow_expand=False,
        )
        st.download_button(
            "Exportar mapa PNG",
            data=figure_to_png_bytes(dangerous_loss_map_fig),
            file_name="dangerous_losses_map.png",
            mime="image/png",
            width="stretch",
            icon=":material/download:",
        )
        plt.close(dangerous_loss_map_fig)

    with content_cols[1]:
        render_section_header("Resumen por jugador")
        render_metric_table(dangerous_summary_df)
        render_download_csv(
            dangerous_summary_df,
            "dangerous_losses_summary.csv",
            label="Exportar resumen CSV",
        )

    render_section_header("Listado de pérdidas peligrosas")
    render_metric_table(dangerous_losses_filtered_df)
    render_download_csv(
        dangerous_losses_filtered_df,
        "dangerous_losses.csv",
        label="Exportar pérdidas peligrosas CSV",
    )


def _render_failed_passes_inside_losses(
    filtered_df: pd.DataFrame,
    failed_pass_df: pd.DataFrame,
    zone_filter: str,
    full_to_display: dict[str, str],
) -> None:
    """Render the detailed failed-pass analysis inside the losses tab."""
    render_section_header("Detalle de pases fallidos")
    st.caption(
        "Cuando el tipo de pérdida es `Failed Pass`, puedes refinar el análisis con filtros específicos de pase sin salir de la pestaña de pérdidas."
    )

    filter_cols = st.columns(3)
    with filter_cols[0]:
        progressive_filter = st.selectbox(
            "Progresivo",
            ["Todos", "Sí", "No"],
            key="losses_failed_passes_progressive_filter",
        )
    with filter_cols[1]:
        destination_filter = st.selectbox(
            "Destino",
            ["Todos", "Último tercio", "Área"],
            key="losses_failed_passes_destination_filter",
        )
    with filter_cols[2]:
        origin_zone_filter = st.selectbox(
            "Zona de origen",
            ["Todas", "Tercio defensivo", "Tercio medio", "Tercio ofensivo"],
            key="losses_failed_passes_origin_zone_filter",
        )

    filtered_failed_pass_df = _apply_failed_passes_view_filters(
        failed_pass_df,
        progressive_filter,
        destination_filter,
        origin_zone_filter,
    )
    filtered_failed_pass_df = _apply_loss_zone_filter(filtered_failed_pass_df, zone_filter)

    metrics = calculate_failed_pass_metrics(filtered_failed_pass_df)
    summary_df = apply_player_display_names(
        summarize_failed_passes_by_player(filtered_failed_pass_df),
        full_to_display,
    )
    context_df = apply_player_display_names(
        _filter_failed_pass_context(
            get_failed_pass_context(filtered_df),
            filtered_failed_pass_df,
        ),
        full_to_display,
    )

    render_kpi_grid(
        [
            {"label": "Pases fallidos", "value": metrics["total_failed_passes"], "sub": "Volumen total", "tone": "red", "icon": "send"},
            {"label": "Distancia media", "value": _format_metric_value(metrics["average_length"]), "sub": "Longitud media", "tone": "blue", "icon": "route"},
            {"label": "Progresivos", "value": metrics["progressive_failed_passes"], "sub": "Con progresión", "tone": "teal", "icon": "arrow-right"},
            {"label": "Al último tercio", "value": metrics["failed_passes_to_final_third"], "sub": "Destino ofensivo", "tone": "orange", "icon": "target"},
            {"label": "Al área", "value": metrics["failed_box_entries"], "sub": "Box entry fallida", "tone": "purple", "icon": "map-pin"},
        ]
    )

    content_cols = st.columns([1.3, 1], vertical_alignment="top")
    with content_cols[0]:
        if filtered_failed_pass_df.empty:
            render_section_header("Mapa de pases fallidos")
            render_empty_state(
                "No hay pases fallidos para los filtros seleccionados.",
                "Prueba a ampliar el rango de minutos o relajar los filtros específicos de pase.",
            )
        else:
            failed_pass_map_fig = plot_events_on_pitch(
                filtered_failed_pass_df,
                title="Mapa de pases fallidos",
                draw_movements=True,
                show_legend=True,
            )
            render_plot_card(
                "Mapa de pases fallidos",
                failed_pass_map_fig,
                "Visualiza el origen y destino de los pases no completados del contexto activo.",
                allow_expand=False,
            )
            st.download_button(
                "Exportar mapa PNG",
                data=figure_to_png_bytes(failed_pass_map_fig),
                file_name="failed_passes_map.png",
                mime="image/png",
                width="stretch",
                icon=":material/download:",
            )
            plt.close(failed_pass_map_fig)

    with content_cols[1]:
        render_section_header("Resumen por jugador")
        render_metric_table(summary_df)
        render_download_csv(
            summary_df,
            "failed_passes_summary.csv",
            label="Exportar resumen CSV",
        )

    render_section_header("Conexión con análisis espacial")
    _render_spatial_handoff(filtered_failed_pass_df)

    render_section_header("Contexto posterior")
    if context_df.empty:
        render_empty_state(
            "No hay contexto posterior para los pases fallidos seleccionados.",
            "Prueba a quitar filtros internos o ampliar el rango de minutos.",
        )
    else:
        render_metric_table(context_df)
        render_download_csv(context_df, "failed_passes_context.csv", label="Exportar contexto CSV")


def _render_spatial_handoff(filtered_failed_pass_df: pd.DataFrame) -> None:
    """Render one minimal bridge from failed passes to the spatial analysis view."""
    render_badges([("FAILED PASS", "red"), ("ANÁLISIS ESPACIAL", "teal")])
    if filtered_failed_pass_df.empty:
        render_empty_state(
            "No hay pases fallidos filtrados para analizar en el módulo espacial.",
            "Prueba a relajar los filtros específicos de pase.",
        )
        return

    event_id_column = next((column for column in ["event_id", "id"] if column in filtered_failed_pass_df.columns), None)
    if event_id_column is None:
        st.info(
            "Los eventos filtrados no incluyen `event_id` o `id`, así que no pueden preseleccionarse en `🎯 Sistema de análisis > 🗺️ Voronoi/Delaunay`."
        )
        return

    preview_columns = [
        column
        for column in [event_id_column, "minute", "second", "team", "player", "x", "y", "end_x", "end_y"]
        if column in filtered_failed_pass_df.columns
    ]
    if preview_columns:
        st.dataframe(filtered_failed_pass_df.loc[:, preview_columns], width="stretch", hide_index=True)

    options = list(range(len(filtered_failed_pass_df)))
    selected_index = st.selectbox(
        "Pase fallido para análisis espacial",
        options,
        key="losses_to_spatial_failed_pass_index",
        format_func=lambda idx: _format_failed_pass_handoff_label(filtered_failed_pass_df.iloc[int(idx)]),
    )
    selected_event = filtered_failed_pass_df.iloc[int(selected_index)]
    selected_event_id = selected_event.get(event_id_column)
    if pd.isna(selected_event_id):
        st.info("El pase seleccionado no tiene un identificador de evento válido.")
        return

    if st.button("Analizar este pase en 🗺️ Voronoi/Delaunay", width="stretch", icon=":material/map:"):
        st.session_state["selected_spatial_event_id"] = str(selected_event_id)
        st.session_state["event_analysis_section"] = EVENT_ANALYSIS_SECTIONS[4]
        st.session_state["active_view"] = EVENT_ANALYSIS_VIEW
        st.session_state["_requested_active_view"] = EVENT_ANALYSIS_VIEW
        st.rerun()


def _apply_loss_view_filters(df: pd.DataFrame, loss_type: str, zone_filter: str) -> pd.DataFrame:
    """Apply lightweight view filters for the losses page."""
    if df.empty:
        return df

    filtered_df = df.copy()
    if loss_type != "Todos":
        filtered_df = filtered_df[filtered_df["loss_type"] == loss_type].copy()

    return _apply_loss_zone_filter(filtered_df, zone_filter)


def _apply_loss_zone_filter(df: pd.DataFrame, zone_filter: str) -> pd.DataFrame:
    """Apply the common zone filter used in the losses tab."""
    if df.empty:
        return df
    filtered_df = df.copy()
    if zone_filter != "Todas" and "x" in filtered_df.columns:
        x_series = pd.to_numeric(filtered_df["x"], errors="coerce")
        if zone_filter == "Campo propio":
            filtered_df = filtered_df[(x_series < 60).fillna(False)].copy()
        elif zone_filter == "Campo rival":
            filtered_df = filtered_df[(x_series >= 60).fillna(False)].copy()
        elif zone_filter == "Último tercio":
            filtered_df = filtered_df[(x_series >= 80).fillna(False)].copy()
    return filtered_df


def _apply_failed_passes_view_filters(
    df: pd.DataFrame,
    progressive_filter: str,
    destination_filter: str,
    origin_zone_filter: str,
) -> pd.DataFrame:
    """Apply view-level filters for failed passes inside the losses tab."""
    if df.empty:
        return df

    filtered_df = df.copy()
    if progressive_filter == "Sí":
        filtered_df = filtered_df[filtered_df["progressive"].fillna(False)].copy()
    elif progressive_filter == "No":
        filtered_df = filtered_df[~filtered_df["progressive"].fillna(False)].copy()

    if destination_filter == "Último tercio":
        filtered_df = filtered_df[filtered_df["to_final_third"].fillna(False)].copy()
    elif destination_filter == "Área":
        filtered_df = filtered_df[filtered_df["box_entry"].fillna(False)].copy()

    if origin_zone_filter != "Todas":
        filtered_df = filtered_df[filtered_df["origin_zone"] == origin_zone_filter].copy()
    return filtered_df


def _format_metric_value(value: object) -> str:
    """Format metric values for KPI display."""
    if isinstance(value, float):
        if value.is_integer():
            return str(int(value))
        return f"{value:.2f}"
    return str(value)


def _format_failed_pass_handoff_label(event_row: pd.Series) -> str:
    """Build one readable label for the losses-to-spatial selector."""
    minute = event_row.get("minute", "-")
    second = event_row.get("second", "-")
    player = event_row.get("player", "Jugador desconocido")
    team = event_row.get("team", "Equipo desconocido")
    return f"{minute}:{second} - {player} - {team}"


def _filter_failed_pass_context(context_df: pd.DataFrame, failed_pass_df: pd.DataFrame) -> pd.DataFrame:
    """Keep only context rows belonging to the currently filtered failed passes."""
    if context_df.empty or failed_pass_df.empty:
        return pd.DataFrame(columns=context_df.columns)
    required_context = {"passer", "minute", "second", "possession_id"}
    required_failed = {"player", "minute", "second", "possession_id"}
    if not required_context.issubset(context_df.columns) or not required_failed.issubset(failed_pass_df.columns):
        return context_df

    keys_df = failed_pass_df.loc[:, ["player", "minute", "second", "possession_id"]].drop_duplicates().rename(
        columns={"player": "passer"}
    )
    return context_df.merge(keys_df, on=["passer", "minute", "second", "possession_id"], how="inner")
