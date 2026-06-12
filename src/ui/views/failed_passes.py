from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from src.repositories.export_repository import dataframe_to_csv_bytes, figure_to_png_bytes
from src.services.losses_service import (
    calculate_failed_pass_metrics,
    get_failed_pass_context,
    get_failed_passes,
    summarize_failed_passes_by_player,
)
from src.core.models.player_labels import apply_player_display_names, build_player_label_maps
from src.ui.components import (
    render_download_csv,
    render_empty_state,
    render_kpi_row,
    render_metric_table,
    render_page_intro,
    render_plot_card,
)
from src.ui.components.visualizations import plot_events_on_pitch


def render_failed_passes_view(filtered_df: pd.DataFrame) -> None:
    """Render the failed passes analysis view."""
    render_page_intro(
        "Pases fallidos",
        "Esta sección estudia pases no completados y su contexto posterior como paso previo al futuro análisis de decisión."
    )

    failed_pass_df = get_failed_passes(filtered_df)
    full_to_display, _ = build_player_label_maps(filtered_df)
    filter_cols = st.columns(3)
    with filter_cols[0]:
        progressive_filter = st.selectbox(
            "Progresivo",
            ["Todos", "Sí", "No"],
            key="failed_passes_progressive_filter",
        )
    with filter_cols[1]:
        destination_filter = st.selectbox(
            "Destino",
            ["Todos", "Último tercio", "Área"],
            key="failed_passes_destination_filter",
        )
    with filter_cols[2]:
        origin_zone_filter = st.selectbox(
            "Zona de origen",
            ["Todas", "Tercio defensivo", "Tercio medio", "Tercio ofensivo"],
            key="failed_passes_origin_zone_filter",
        )

    filtered_failed_pass_df = _apply_failed_passes_view_filters(
        failed_pass_df,
        progressive_filter,
        destination_filter,
        origin_zone_filter,
    )
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

    render_kpi_row(
        [
            {"label": "Pases fallidos", "value": metrics["total_failed_passes"], "tone": "red", "icon": "send"},
            {"label": "Distancia media", "value": _format_metric_value(metrics["average_length"]), "tone": "blue", "icon": "route"},
            {"label": "Progresivos", "value": metrics["progressive_failed_passes"], "tone": "teal", "icon": "arrow-right"},
            {"label": "Al último tercio", "value": metrics["failed_passes_to_final_third"], "tone": "orange", "icon": "target"},
            {"label": "Al área", "value": metrics["failed_box_entries"], "tone": "purple", "icon": "map-pin"},
        ]
    )

    content_cols = st.columns([1.3, 1], vertical_alignment="top")
    with content_cols[0]:
        if filtered_failed_pass_df.empty:
            render_empty_state(
                "No hay pases fallidos para los filtros seleccionados.",
                "Prueba a ampliar el rango de minutos o seleccionar Todos en jugador.",
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
                description="Visualiza el origen y destino de los pases no completados del contexto activo.",
                allow_expand=False,
            )
            try:
                st.download_button(
                    "Exportar mapa PNG",
                    data=figure_to_png_bytes(failed_pass_map_fig),
                    file_name="failed_passes_map.png",
                    mime="image/png",
                    width="stretch",
                    icon=":material/download:",
                )
            finally:
                plt.close(failed_pass_map_fig)

    with content_cols[1]:
        render_metric_table(summary_df, title="Resumen por jugador")
        render_download_csv(
            summary_df,
            "failed_passes_summary.csv",
            label="Exportar resumen CSV",
        )

    if context_df.empty:
        render_empty_state(
            "No hay contexto posterior para los pases fallidos seleccionados.",
            "Prueba a quitar filtros internos o ampliar el rango de minutos.",
        )
    else:
        render_metric_table(context_df, title="Contexto posterior")
        render_download_csv(context_df, "failed_passes_context.csv", label="Exportar contexto CSV")


def _apply_failed_passes_view_filters(
    df: pd.DataFrame,
    progressive_filter: str,
    destination_filter: str,
    origin_zone_filter: str,
) -> pd.DataFrame:
    """Apply view-level filters for failed passes."""
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
