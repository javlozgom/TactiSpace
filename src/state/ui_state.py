from __future__ import annotations

import streamlit as st

from src.state import keys


def get_visible_spatial_events(default: int | None = None) -> int | None:
    return st.session_state.get(keys.VISIBLE_SPATIAL_EVENTS, default)


def set_visible_spatial_events(count: int) -> None:
    st.session_state[keys.VISIBLE_SPATIAL_EVENTS] = count


def get_last_filtered_df(default=None):
    return st.session_state.get(keys.LAST_FILTERED_DF, default)
