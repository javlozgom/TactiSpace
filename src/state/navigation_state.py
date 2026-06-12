from __future__ import annotations

import streamlit as st

from src.state import keys
from src.ui.navigation_config import MATCH_OVERVIEW_VIEW


def get_requested_view() -> object:
    return st.session_state.get(keys.REQUESTED_ACTIVE_VIEW)


def request_view(view_name: str) -> None:
    st.session_state[keys.REQUESTED_ACTIVE_VIEW] = view_name


def get_active_view(default: str = MATCH_OVERVIEW_VIEW) -> str:
    return st.session_state.get(keys.ACTIVE_VIEW, default)


def set_active_view(view_name: str) -> None:
    st.session_state[keys.ACTIVE_VIEW] = view_name
