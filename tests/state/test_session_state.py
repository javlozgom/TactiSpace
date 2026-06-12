from __future__ import annotations

import pandas as pd

from src.state import filters_state, keys, navigation_state, session, ui_state
from src.state.defaults import SESSION_DEFAULTS
from src.ui.navigation_config import EVENT_ANALYSIS_VIEW, MATCH_OVERVIEW_VIEW, RAW_DEBUG_VIEW


class DummyUpload:
    def __init__(self, payload: bytes):
        self._payload = payload

    def getvalue(self) -> bytes:
        return self._payload


def _patch_session_state(monkeypatch):
    state: dict[str, object] = {}
    for module in [filters_state, navigation_state, session, ui_state]:
        monkeypatch.setattr(module.st, "session_state", state, raising=False)
    return state


def test_state_helpers_manage_session_state(monkeypatch):
    state = _patch_session_state(monkeypatch)
    nav_options = [MATCH_OVERVIEW_VIEW, EVENT_ANALYSIS_VIEW, RAW_DEBUG_VIEW]
    state[keys.REQUESTED_ACTIVE_VIEW] = EVENT_ANALYSIS_VIEW

    session.initialize_session_state(nav_options)

    assert state[keys.ACTIVE_VIEW] == EVENT_ANALYSIS_VIEW
    assert state[keys.PLAYER_FILTER] == SESSION_DEFAULTS[keys.PLAYER_FILTER]

    state[keys.HEADER_CSV_UPLOAD] = DummyUpload(b"abc")
    assert session.resolve_uploaded_file_bytes() == b"abc"

    session.mark_default_data_for_next_run()
    assert session.resolve_uploaded_file_bytes() is None

    filters_state.request_filter_reset()
    assert session.consume_filter_reset_request() is True
    session.clear_filter_reset_request()
    assert session.consume_filter_reset_request() is False

    assert session.has_minute_filter() is False
    state[keys.MINUTE_FILTER] = (10, 20)
    assert session.has_minute_filter() is True

    session.set_active_view(MATCH_OVERVIEW_VIEW)
    assert session.get_active_view() == MATCH_OVERVIEW_VIEW

    df = pd.DataFrame([{"x": 1}])
    session.store_last_filtered_df(df)
    session.store_visible_spatial_events(4)
    session.mark_app_bootstrapped()

    assert navigation_state.get_requested_view() is None
    navigation_state.request_view(RAW_DEBUG_VIEW)
    assert navigation_state.get_requested_view() == RAW_DEBUG_VIEW
    assert navigation_state.get_active_view() == MATCH_OVERVIEW_VIEW
    navigation_state.set_active_view(RAW_DEBUG_VIEW)
    assert navigation_state.get_active_view() == RAW_DEBUG_VIEW

    assert filters_state.get_global_filter_values()["minute_filter"] == (10, 20)
    assert ui_state.get_visible_spatial_events() == 4
    ui_state.set_visible_spatial_events(7)
    assert ui_state.get_visible_spatial_events() == 7
    assert ui_state.get_last_filtered_df().equals(df)
