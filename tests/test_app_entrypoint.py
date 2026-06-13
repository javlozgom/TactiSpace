from __future__ import annotations

import importlib
from contextlib import nullcontext
from pathlib import Path

import pandas as pd
import pytest


app = importlib.import_module("app")


class _Placeholder:
    def __init__(self) -> None:
        self.cleared = False

    def container(self):
        return nullcontext()

    def empty(self) -> None:
        self.cleared = True


class _Column:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class _FakeStreamlit:
    def __init__(self) -> None:
        self.captions: list[str] = []
        self.errors: list[str] = []
        self.exceptions: list[object] = []
        self.page_config: dict[str, object] = {}
        self.rerun_called = False

    def set_page_config(self, **kwargs) -> None:
        self.page_config = kwargs

    def empty(self):
        return _Placeholder()

    def columns(self, *_args, **_kwargs):
        return _Column(), _Column()

    def container(self, **_kwargs):
        return nullcontext()

    def caption(self, text: str) -> None:
        self.captions.append(text)

    def error(self, text: str) -> None:
        self.errors.append(text)

    def exception(self, exc: object) -> None:
        self.exceptions.append(exc)

    def stop(self) -> None:
        raise RuntimeError("stop called")

    def rerun(self) -> None:
        self.rerun_called = True


def test_app_main_runs_happy_path_with_spatial_loading(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    fake_st = _FakeStreamlit()
    events_df = pd.DataFrame([{"match_id": 1, "team": "Spain", "player": "A", "minute": 10}])
    filtered_df = events_df.copy()
    freeze_frames_df = pd.DataFrame([{"match_id": 1, "event_uuid": "evt-1"}])
    rendered: dict[str, object] = {}
    stored: dict[str, object] = {}

    monkeypatch.setattr(app, "st", fake_st)
    monkeypatch.setattr(app, "apply_app_styles", lambda: None)
    monkeypatch.setattr(app, "initialize_session_state", lambda nav_options: None)
    monkeypatch.setattr(app, "update_loading_overlay", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(app, "resolve_uploaded_file_bytes", lambda: None)
    monkeypatch.setattr(app, "get_normalized_events_cached", lambda *args: events_df)
    monkeypatch.setattr(app, "consume_filter_reset_request", lambda: False)
    monkeypatch.setattr(app, "clear_filter_reset_request", lambda: stored.setdefault("cleared", True))
    monkeypatch.setattr(app, "has_minute_filter", lambda: True)
    monkeypatch.setattr(app, "get_active_view", lambda default: app.EVENT_ANALYSIS_VIEW)
    monkeypatch.setattr(app, "_canonical_nav_view", lambda view_name: view_name)
    monkeypatch.setattr(app, "set_active_view", lambda view_name: stored.setdefault("active_view", view_name))
    monkeypatch.setattr(app, "render_sidebar", lambda df: {"selected_match": 1, "selected_team": "Spain", "selected_player": "A", "minute_range": (0, 90)})
    monkeypatch.setattr(app, "event_analysis_requires_spatial_data", lambda: True)
    monkeypatch.setattr(app, "get_freeze_frames_cached", lambda path, match_ids=None: freeze_frames_df)

    call_state = {"count": 0}

    def _build_view_contexts(*_args, **kwargs):
        call_state["count"] += 1
        current_freeze_frames = kwargs.get("freeze_frames_df")
        return {
            "filtered_df": filtered_df,
            "position_context_df": filtered_df,
            "comparative_context_df": filtered_df,
            "metrics": {"events": len(filtered_df)},
            "spatial_match_ids": ("1",),
            "visible_spatial_events": 5 if current_freeze_frames is not None else 2,
        }

    monkeypatch.setattr(app, "build_view_contexts", _build_view_contexts)
    monkeypatch.setattr(app, "store_last_filtered_df", lambda df: stored.setdefault("last_df", df))
    monkeypatch.setattr(app, "store_visible_spatial_events", lambda count: stored.setdefault("visible", count))
    monkeypatch.setattr(app, "render_app_header", lambda df: (None, False))
    monkeypatch.setattr(app, "render_navigation", lambda: app.EVENT_ANALYSIS_VIEW)
    monkeypatch.setattr(app, "mark_default_data_for_next_run", lambda: stored.setdefault("default_data", True))
    monkeypatch.setattr(app, "mark_app_bootstrapped", lambda: stored.setdefault("bootstrapped", True))
    monkeypatch.setattr(
        app,
        "render_active_view",
        lambda active_view, **kwargs: rendered.update({"active_view": active_view, **kwargs}),
    )
    monkeypatch.setattr(app, "DEFAULT_DATA_PATH", str(tmp_path / "events.parquet"))
    monkeypatch.setattr(app, "NORMALIZED_DATA_PATH", str(tmp_path / "events_normalized.parquet"))
    monkeypatch.setattr(app, "DEFAULT_LINEUPS_PATH", str(tmp_path / "lineups.parquet"))
    monkeypatch.setattr(app, "DEFAULT_FREEZE_FRAME_PATH", str(tmp_path / "three_sixty.parquet"))
    Path(app.NORMALIZED_DATA_PATH).write_text("x", encoding="utf-8")

    app.main()

    assert fake_st.page_config["page_title"] == "TactiSpace"
    assert call_state["count"] == 2
    assert rendered["active_view"] == app.EVENT_ANALYSIS_VIEW
    assert rendered["freeze_frames_df"].equals(freeze_frames_df)
    assert stored["visible"] == 5
    assert stored["bootstrapped"] is True


def test_app_main_resets_filters_and_shows_normalization_hint(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    fake_st = _FakeStreamlit()
    events_df = pd.DataFrame([{"match_id": 1, "team": "Spain", "player": "A", "minute": 10}])
    reset_calls: list[str] = []

    monkeypatch.setattr(app, "st", fake_st)
    monkeypatch.setattr(app, "apply_app_styles", lambda: None)
    monkeypatch.setattr(app, "initialize_session_state", lambda nav_options: None)
    monkeypatch.setattr(app, "update_loading_overlay", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(app, "resolve_uploaded_file_bytes", lambda: None)
    monkeypatch.setattr(app, "get_normalized_events_cached", lambda *args: events_df)
    monkeypatch.setattr(app, "consume_filter_reset_request", lambda: True)
    monkeypatch.setattr(app, "clear_filter_reset_request", lambda: reset_calls.append("clear"))
    monkeypatch.setattr(app, "has_minute_filter", lambda: False)
    monkeypatch.setattr(app, "reset_filter_state", lambda df: reset_calls.append("reset"))
    monkeypatch.setattr(app, "get_active_view", lambda default: "vista invalida")
    monkeypatch.setattr(app, "_canonical_nav_view", lambda view_name: view_name)
    monkeypatch.setattr(app, "set_active_view", lambda view_name: reset_calls.append(f"active:{view_name}"))
    monkeypatch.setattr(app, "render_sidebar", lambda df: {"selected_match": 1, "selected_team": "Spain", "selected_player": "A", "minute_range": (0, 90)})
    monkeypatch.setattr(
        app,
        "build_view_contexts",
        lambda *_args, **_kwargs: {
            "filtered_df": events_df,
            "position_context_df": events_df,
            "comparative_context_df": events_df,
            "metrics": {},
            "spatial_match_ids": None,
            "visible_spatial_events": 0,
        },
    )
    monkeypatch.setattr(app, "store_last_filtered_df", lambda df: None)
    monkeypatch.setattr(app, "store_visible_spatial_events", lambda count: None)
    monkeypatch.setattr(app, "render_app_header", lambda df: (None, False))
    monkeypatch.setattr(app, "render_navigation", lambda: app.NAV_OPTIONS[0])
    monkeypatch.setattr(app, "render_active_view", lambda active_view, **kwargs: None)
    monkeypatch.setattr(app, "mark_app_bootstrapped", lambda: None)
    monkeypatch.setattr(app, "event_analysis_requires_spatial_data", lambda: False)
    monkeypatch.setattr(app, "DEFAULT_DATA_PATH", str(tmp_path / "events.parquet"))
    monkeypatch.setattr(app, "NORMALIZED_DATA_PATH", str(tmp_path / "missing_normalized.parquet"))
    monkeypatch.setattr(app, "DEFAULT_LINEUPS_PATH", str(tmp_path / "lineups.parquet"))
    monkeypatch.setattr(app, "DEFAULT_FREEZE_FRAME_PATH", str(tmp_path / "three_sixty.parquet"))

    app.main()

    assert reset_calls.count("reset") == 2
    assert "clear" in reset_calls
    assert any("scripts/build_all_normalized.py" in caption for caption in fake_st.captions)
