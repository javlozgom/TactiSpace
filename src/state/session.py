from __future__ import annotations

import pandas as pd
import streamlit as st

from src.state import keys
from src.state.defaults import SESSION_DEFAULTS
from src.ui.navigation_config import MATCH_OVERVIEW_VIEW, canonicalize_view_name, resolve_legacy_section


def initialize_session_state(nav_options: list[str]) -> None:
    """Initialize the top-level session state used across views."""
    requested_view = st.session_state.pop(keys.REQUESTED_ACTIVE_VIEW, None)

    for key, value in SESSION_DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = value

    if requested_view is not None:
        _apply_requested_view(requested_view, nav_options)
    else:
        st.session_state[keys.ACTIVE_VIEW] = canonicalize_view_name(st.session_state.get(keys.ACTIVE_VIEW))


def _apply_requested_view(requested_view: object, nav_options: list[str]) -> None:
    """Route one requested or legacy view to the new main navigation plus internal section state."""
    section_target = resolve_legacy_section(requested_view)
    canonical_view = canonicalize_view_name(requested_view)

    if section_target is not None:
        section_key, section_value = section_target
        st.session_state[section_key] = section_value

    if canonical_view in nav_options:
        st.session_state[keys.ACTIVE_VIEW] = canonical_view
    else:
        st.session_state[keys.ACTIVE_VIEW] = MATCH_OVERVIEW_VIEW

    # Force the top navigation selector to resync from the newly requested view.
    st.session_state.pop("active_view_nav_selector", None)


def resolve_uploaded_file_bytes() -> bytes | None:
    """Return uploaded CSV bytes unless the default dataset has been requested."""
    uploaded_file = st.session_state.get(keys.HEADER_CSV_UPLOAD)
    uploaded_file_bytes = uploaded_file.getvalue() if uploaded_file is not None else None
    if bool(st.session_state.get(keys.HEADER_USE_DEFAULT_DATA, False)) or st.session_state.pop(
        keys.FORCE_DEFAULT_DATA_NEXT_RUN,
        False,
    ):
        uploaded_file_bytes = None
    return uploaded_file_bytes


def mark_default_data_for_next_run() -> None:
    st.session_state[keys.FORCE_DEFAULT_DATA_NEXT_RUN] = True


def consume_filter_reset_request() -> bool:
    return bool(st.session_state.get(keys.RESET_FILTERS_REQUESTED, False))


def clear_filter_reset_request() -> None:
    st.session_state[keys.RESET_FILTERS_REQUESTED] = False


def has_minute_filter() -> bool:
    return keys.MINUTE_FILTER in st.session_state


def get_active_view(default: str = MATCH_OVERVIEW_VIEW) -> str:
    return st.session_state.get(keys.ACTIVE_VIEW, default)


def set_active_view(view_name: str) -> None:
    st.session_state[keys.ACTIVE_VIEW] = view_name


def store_last_filtered_df(filtered_df: pd.DataFrame) -> None:
    st.session_state[keys.LAST_FILTERED_DF] = filtered_df


def store_visible_spatial_events(count: int) -> None:
    st.session_state[keys.VISIBLE_SPATIAL_EVENTS] = count


def mark_app_bootstrapped() -> None:
    st.session_state[keys.APP_BOOTSTRAPPED] = True
