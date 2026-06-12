from __future__ import annotations

import pandas as pd
import streamlit as st

from src.core.spatial.freeze_frame import get_freeze_frame_for_event, has_freeze_frame_data
from src.core.spatial.pass_decision import get_failed_pass_candidates
from src.state import spatial as spatial_state
from src.ui.components import render_empty_state, render_info_box, render_section_header
from src.ui.components.spatial_layout import (
    render_spatial_data_status,
    render_spatial_header,
    render_spatial_module_nav,
    render_spatial_subview_nav,
)
from src.ui.views import spatial_shared as shared
from src.ui.views.spatial_delaunay import (
    build_delaunay_neighbors_df as _build_delaunay_neighbors_df,
    render_delaunay_panel,
)
from src.ui.views.spatial_shared import (
    assign_spatial_reference_ids as _assign_spatial_reference_ids,
    build_event_diagnostics as _build_event_diagnostics,
    build_match_labels as _shared_get_match_labels,
    count_freeze_frame_events_in_context as _count_freeze_frame_events_in_context,
    filter_failed_passes_with_freeze_frame,
    format_failed_pass_label,
    format_match_label,
    format_ratio as _format_ratio,
    safe_display,
)
from src.ui.views.spatial_voronoi import (
    build_voronoi_team_summary_df as _build_voronoi_team_summary_df,
    render_voronoi_panel,
)


def render_spatial_analysis_view(
    events_df: pd.DataFrame,
    filtered_df: pd.DataFrame,
    freeze_frames_df: pd.DataFrame | None = None,
) -> None:
    """Render the spatial analysis tab as a lightweight orchestrator."""
    _ = events_df
    freeze_frames_df = freeze_frames_df if freeze_frames_df is not None else pd.DataFrame()

    render_spatial_header()
    render_info_box(
        "📏 Unidades espaciales",
        (
            "En esta pestaña, las distancias y superficies se interpretan en el sistema de coordenadas "
            "normalizado de StatsBomb, sobre un campo representado en una escala 120x80. Por ello, las "
            "distancias deben leerse como unidades de campo StatsBomb y las áreas como unidades cuadradas "
            "de ese mismo sistema.\n\n"
            "Si se desea una lectura más intuitiva, estas magnitudes pueden expresarse de forma aproximada "
            "en metros y metros cuadrados, siempre bajo el supuesto adicional de un campo estándar. Esa "
            "conversión debe entenderse como una referencia interpretativa y no como una medición física "
            "exacta del terreno de juego real."
        ),
        tone="neutral",
    )

    failed_passes_df = get_failed_pass_candidates(filtered_df).reset_index(drop=True)
    freeze_frame_available = has_freeze_frame_data(freeze_frames_df)
    available_failed_passes_df = filter_failed_passes_with_freeze_frame(
        failed_passes_df,
        freeze_frames_df,
    ).reset_index(drop=True)

    render_spatial_data_status(
        filtered_df=filtered_df,
        freeze_frames_df=freeze_frames_df,
        failed_passes_df=failed_passes_df,
        available_failed_passes_df=available_failed_passes_df,
        freeze_frame_available=freeze_frame_available,
        freeze_frame_events=_count_freeze_frame_events_in_context(filtered_df, freeze_frames_df),
        format_ratio=_format_ratio,
    )

    if failed_passes_df.empty:
        render_empty_state(
            "No hay pases fallidos en el contexto filtrado.",
            "Prueba a ampliar filtros de partido, equipo, jugador o minutos.",
        )
        return

    if freeze_frame_available and available_failed_passes_df.empty:
        render_empty_state(
            "No hay pases fallidos con freeze-frame en el contexto filtrado.",
            "Prueba con otro partido, equipo o rango de minutos para encontrar eventos 360 seleccionables.",
        )
        return

    selector_df = (available_failed_passes_df if not available_failed_passes_df.empty else failed_passes_df).reset_index(
        drop=True
    )
    shared.ensure_spatial_case_picker_state(selector_df)

    controls, selected_event = _resolve_spatial_case_context(selector_df)
    if selected_event is None:
        return

    selected_case_label = format_failed_pass_label(selected_event, _get_match_labels())
    if not shared.is_spatial_case_picker_visible():
        render_section_header(
            "Caso seleccionado",
            "La selección superior se ha ocultado para dejar más espacio al análisis del caso.",
        )
        st.markdown(f'<p class="fea-block-note">Caso en estudio: <strong>{selected_case_label}</strong></p>', unsafe_allow_html=True)
        st.button(
            "Cambiar caso",
            key="spatial_change_case",
            on_click=shared.show_spatial_case_picker,
            width="stretch",
            icon=":material/swap_horiz:",
        )

    with st.spinner("Cargando análisis espacial..."):
        selected_freeze_frame_df = get_freeze_frame_for_event(selected_event, freeze_frames_df)
        if selected_freeze_frame_df.empty:
            render_empty_state(
                "Este pase fallido no tiene freeze-frame asociado.",
                "Prueba otro caso del selector para continuar con el análisis espacial.",
            )
            return
        selected_freeze_frame_df = _enrich_freeze_frame_team_labels(selected_event, selected_freeze_frame_df)
        selected_freeze_frame_df = _assign_spatial_reference_ids(selected_freeze_frame_df)

    with st.container(border=True):
        active_module = render_spatial_module_nav()
        if active_module == "voronoi":
            render_voronoi_panel(
                selected_event=selected_event,
                freeze_frame_df=selected_freeze_frame_df,
                selected_plots=controls["selected_plots"],
                scoring_profile=controls["scoring_profile"],
            )
        else:
            render_delaunay_panel(
                selected_event=selected_event,
                freeze_frame_df=selected_freeze_frame_df,
                selected_plots=controls["selected_plots"],
                scoring_profile=controls["scoring_profile"],
            )


def _resolve_spatial_case_context(selector_df: pd.DataFrame) -> tuple[dict[str, object], pd.Series | None]:
    """Resolve visible controls plus the selected event row."""
    case_picker_visible = shared.is_spatial_case_picker_visible()
    if case_picker_visible:
        with st.container(border=True):
            render_section_header(
                "Selección del caso",
                "Elige el pase fallido a estudiar y navega después por los módulos internos de Voronoi y Delaunay.",
            )
            preselected_event_id = st.session_state.get(spatial_state.SELECTED_EVENT_ID)
            selected_event_index = shared.render_failed_pass_selector(
                selector_df,
                preselected_event_id=preselected_event_id,
            )
            if selected_event_index is None:
                return {}, None

            current_index = int(selected_event_index)
            committed_index = st.session_state.get(spatial_state.LAST_COMMITTED_FAILED_PASS_INDEX)
            if committed_index is None:
                st.session_state[spatial_state.LAST_COMMITTED_FAILED_PASS_INDEX] = current_index
            elif int(committed_index) != current_index:
                shared.store_selected_spatial_event_id(selector_df.iloc[current_index])
                st.session_state[spatial_state.LAST_COMMITTED_FAILED_PASS_INDEX] = current_index
                st.session_state[spatial_state.CASE_PICKER_VISIBLE] = False
                st.rerun()

            controls = shared.render_spatial_view_controls()
            shared.render_scoring_profile_info_box(controls["scoring_profile"])
    else:
        controls = shared.resolve_spatial_controls_state()
        shared.render_scoring_profile_info_box(controls["scoring_profile"])
        selected_event_index = shared.resolve_default_selector_index(
            selector_df,
            st.session_state.get(spatial_state.SELECTED_EVENT_ID),
        )

    selected_event = selector_df.iloc[int(selected_event_index)]
    shared.store_selected_spatial_event_id(selected_event)
    return controls, selected_event


def _get_match_labels() -> dict[str, str]:
    """Compatibility wrapper for cached match labels."""
    return _shared_get_match_labels()


def _enrich_freeze_frame_team_labels(
    event_row: pd.Series,
    freeze_frame_df: pd.DataFrame,
) -> pd.DataFrame:
    """Fill or correct local team labels using event team plus teammate/opponent side."""
    if freeze_frame_df.empty:
        return freeze_frame_df.copy()

    working_df = freeze_frame_df.copy()
    event_team, opponent_team = _resolve_event_side_labels(event_row)
    if "team" not in working_df.columns:
        working_df["team"] = pd.Series(pd.NA, index=working_df.index, dtype="object")
    else:
        working_df["team"] = working_df["team"].astype("object")

    teammate_mask = (
        working_df["teammate"].fillna(False).astype(bool)
        if "teammate" in working_df.columns
        else pd.Series(False, index=working_df.index)
    )

    teammate_fallback = event_team or "Equipo del evento"
    opponent_fallback = opponent_team or "Equipo rival"

    teammate_missing_mask = teammate_mask & (
        working_df["team"].isna() | working_df["team"].astype(str).str.strip().isin({"", "-", "None", "nan"})
    )
    working_df.loc[teammate_missing_mask, "team"] = teammate_fallback

    opponent_mask = ~teammate_mask
    opponent_missing_mask = opponent_mask & (
        working_df["team"].isna() | working_df["team"].astype(str).str.strip().isin({"", "-", "None", "nan"})
    )
    working_df.loc[opponent_missing_mask, "team"] = opponent_fallback

    if event_team:
        opponent_same_as_event_mask = opponent_mask & (
            working_df["team"].astype(str).str.strip() == str(event_team).strip()
        )
        if opponent_same_as_event_mask.any():
            working_df.loc[opponent_same_as_event_mask, "team"] = opponent_fallback

    return working_df


def _resolve_event_side_labels(event_row: pd.Series) -> tuple[str | None, str | None]:
    """Infer event-team and opponent-team labels from event context and match metadata."""
    event_team = safe_display(shared.coalesce_event_value(event_row, ["possession_team", "team"]))
    if event_team == "-":
        event_team = None

    match_id = shared.coalesce_event_value(event_row, ["match_id", "partido"])
    match_label = format_match_label(match_id, _get_match_labels())
    teams_segment = str(match_label).split("|")[0].strip()
    if " vs " not in teams_segment:
        return event_team, None

    left_team, right_team = [part.strip() for part in teams_segment.split(" vs ", 1)]
    if event_team:
        if event_team == left_team:
            return event_team, right_team
        if event_team == right_team:
            return event_team, left_team
    return event_team, None


_render_spatial_module_nav = render_spatial_module_nav
_render_spatial_subview_nav = render_spatial_subview_nav
_render_spatial_data_status = render_spatial_data_status
_render_failed_pass_selector = shared.render_failed_pass_selector
_render_spatial_view_controls = shared.render_spatial_view_controls
_render_scoring_profile_info_box = shared.render_scoring_profile_info_box
_filter_failed_passes_with_freeze_frame = filter_failed_passes_with_freeze_frame
_format_failed_pass_label = format_failed_pass_label
_format_ratio = _format_ratio
_count_freeze_frame_events_in_context = _count_freeze_frame_events_in_context
_assign_spatial_reference_ids = _assign_spatial_reference_ids
_build_event_diagnostics = _build_event_diagnostics
_build_voronoi_team_summary_df = _build_voronoi_team_summary_df
_build_delaunay_neighbors_df = _build_delaunay_neighbors_df
_merge_spatial_reference_ids = shared.merge_spatial_reference_ids
