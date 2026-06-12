from __future__ import annotations

import streamlit as st

from src.state import keys


def request_filter_reset() -> None:
    st.session_state[keys.RESET_FILTERS_REQUESTED] = True


def get_global_filter_values() -> dict[str, object]:
    return {
        "match_filter": st.session_state.get(keys.MATCH_FILTER, "Todos"),
        "team_filter": st.session_state.get(keys.TEAM_FILTER, "Todos"),
        "player_filter": st.session_state.get(keys.PLAYER_FILTER, "Todos"),
        "minute_filter": st.session_state.get(keys.MINUTE_FILTER),
    }
