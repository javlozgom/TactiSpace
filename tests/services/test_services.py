from __future__ import annotations

import pandas as pd

from src.core.exceptions import DomainError
from src.repositories.cache_repository import (
    get_freeze_frames_cached,
    get_match_labels_cached,
    get_normalized_events_cached,
)
from src.services import data_service, export_service, losses_service, spatial_analysis_service, summary_service
from src.services.context_service import build_view_contexts
from src.services.data_service import get_freeze_frames, get_match_labels, get_normalized_events
from src.services.export_service import build_dataframe_export, build_figure_export
from src.services.filter_service import filter_events, get_filter_options
from src.services.spatial_analysis_service import (
    get_delaunay_alternatives_context,
    get_delaunay_connections_context,
    get_delaunay_debug_context,
    get_voronoi_alternatives_context,
    get_voronoi_debug_context,
    get_voronoi_metrics_context,
    prepare_delaunay_context,
    prepare_spatial_event_context,
    prepare_voronoi_context,
)
from src.services.spatial_service import count_visible_spatial_events, get_spatial_match_ids
from src.services.summary_service import get_player_summary, get_summary_metrics


def test_domain_error_is_exception():
    error = DomainError("boom")

    assert isinstance(error, Exception)
    assert str(error) == "boom"


def test_get_filter_options_and_filter_events_cover_happy_path():
    df = pd.DataFrame(
        [
            {"match_id": 2, "team": "Spain", "player": "Rodri", "event_type": "Pass", "minute": 10},
            {"match_id": 1, "team": "Croatia", "player": "Modric", "event_type": "Shot", "minute": 20},
        ]
    )

    options = get_filter_options(df)
    filtered = filter_events(
        df,
        match_id="2",
        team="Spain",
        player="Rodri",
        event_type="Pass",
        minute_range=(5, 15),
    )

    assert options["matches"] == ["Todos", "1", "2"]
    assert options["teams"] == ["Todos", "Croatia", "Spain"]
    assert options["players"] == ["Todos", "Modric", "Rodri"]
    assert options["event_types"] == ["Todos", "Pass", "Shot"]
    assert options["min_minute"] == 10
    assert options["max_minute"] == 20
    assert filtered["player"].tolist() == ["Rodri"]


def test_build_view_contexts_reuses_filters_metrics_and_spatial_count(monkeypatch):
    events_df = pd.DataFrame(
        [
            {"match_id": "1", "team": "Spain", "player": "Rodri", "event_type": "Pass", "minute": 10, "event_id": "evt-1"},
            {"match_id": "2", "team": "Croatia", "player": "Modric", "event_type": "Shot", "minute": 20, "event_id": "evt-2"},
        ]
    )
    freeze_frames_df = pd.DataFrame([{"event_id": "evt-1"}])

    monkeypatch.setattr(
        "src.services.context_service.calculate_basic_metrics",
        lambda df: {"events": len(df)},
    )

    result = build_view_contexts(
        events_df,
        selected_match="1",
        selected_team="Spain",
        selected_player="Rodri",
        selected_minutes=(0, 15),
        freeze_frames_df=freeze_frames_df,
    )

    assert result["metrics"] == {"events": 1}
    assert result["spatial_match_ids"] == ("1",)
    assert result["visible_spatial_events"] == 1
    assert result["filtered_df"]["player"].tolist() == ["Rodri"]
    assert result["comparative_context_df"]["team"].tolist() == ["Spain"]


def test_get_normalized_events_uses_uploaded_file_branch(monkeypatch):
    raw_df = pd.DataFrame([{"event": 1}])
    normalized_df = pd.DataFrame([{"normalized": True}])

    monkeypatch.setattr(data_service, "load_events", lambda uploaded_file=None, default_path=None: raw_df)
    monkeypatch.setattr(data_service, "normalize_events", lambda df: normalized_df)

    result = get_normalized_events("default.csv", "normalized.parquet", "lineups.parquet", b"a,b\n1,2\n", "v1")

    assert result.equals(normalized_df)


def test_get_normalized_events_prefers_existing_normalized_file(monkeypatch, tmp_path):
    normalized_path = tmp_path / "events_normalized.parquet"
    normalized_path.write_text("placeholder", encoding="utf-8")
    normalized_df = pd.DataFrame([{"normalized": True}])
    derived_df = pd.DataFrame([{"derived": True}])

    monkeypatch.setattr(
        data_service,
        "load_events",
        lambda uploaded_file=None, default_path=None: normalized_df,
    )
    monkeypatch.setattr(data_service, "is_normalized_events_df", lambda df: True)
    monkeypatch.setattr(data_service, "add_derived_event_columns", lambda df: derived_df)

    result = get_normalized_events("default.csv", str(normalized_path), "lineups.parquet", None, "v1")

    assert result.equals(derived_df)


def test_get_normalized_events_normalizes_raw_and_enriches_with_lineups(monkeypatch, tmp_path):
    default_path = tmp_path / "events.csv"
    lineups_path = tmp_path / "lineups.parquet"
    default_path.write_text("placeholder", encoding="utf-8")
    lineups_path.write_text("placeholder", encoding="utf-8")
    raw_df = pd.DataFrame([{"event": 1}])
    normalized_df = pd.DataFrame([{"normalized": True}])
    lineups_df = pd.DataFrame([{"player": "Rodri"}])
    enriched_df = pd.DataFrame([{"enriched": True}])
    derived_df = pd.DataFrame([{"derived": True}])

    monkeypatch.setattr(data_service, "load_events", lambda uploaded_file=None, default_path=None: raw_df)
    monkeypatch.setattr(data_service, "is_normalized_events_df", lambda df: False)
    monkeypatch.setattr(data_service, "normalize_events", lambda df: normalized_df)
    monkeypatch.setattr(data_service, "load_lineups", lambda path: lineups_df)
    monkeypatch.setattr(data_service, "is_normalized_lineups_df", lambda df: True)
    monkeypatch.setattr(data_service, "enrich_events_with_lineups", lambda events, lineups: enriched_df)
    monkeypatch.setattr(data_service, "add_derived_event_columns", lambda df: derived_df if df is enriched_df else df)

    result = get_normalized_events(str(default_path), "missing.parquet", str(lineups_path), None, "v1")

    assert result.equals(derived_df)


def test_get_match_labels_and_get_freeze_frames_delegate(monkeypatch):
    monkeypatch.setattr(data_service, "load_match_labels", lambda: {"1": "Spain vs Croatia"})
    monkeypatch.setattr(data_service, "load_freeze_frames", lambda path, match_ids=None: pd.DataFrame([{"event_id": "evt-1"}]))
    monkeypatch.setattr(data_service, "normalize_freeze_frame_df", lambda df: pd.DataFrame([{"event_id": "evt-1", "x": 1, "y": 2}]))

    assert get_match_labels("v1") == {"1": "Spain vs Croatia"}
    assert get_freeze_frames("three_sixty", match_ids=("1",)).to_dict("records") == [{"event_id": "evt-1", "x": 1, "y": 2}]


def test_cache_repository_delegates_to_data_service(monkeypatch):
    monkeypatch.setattr("src.repositories.cache_repository.get_normalized_events", lambda *args: pd.DataFrame([{"ok": True}]))
    monkeypatch.setattr("src.repositories.cache_repository.get_match_labels", lambda version: {"1": version})
    monkeypatch.setattr("src.repositories.cache_repository.get_freeze_frames", lambda path, match_ids=None: pd.DataFrame([{"path": path, "match_ids": match_ids}]))

    assert get_normalized_events_cached("a", "b", "c", None, "v1").to_dict("records") == [{"ok": True}]
    assert get_match_labels_cached("v1") == {"1": "v1"}
    assert get_freeze_frames_cached("ff", ("1",)).to_dict("records") == [{"path": "ff", "match_ids": ("1",)}]


def test_export_and_summary_services_delegate(monkeypatch):
    monkeypatch.setattr(export_service, "dataframe_to_csv_bytes", lambda df: b"csv")
    monkeypatch.setattr(export_service, "figure_to_png_bytes", lambda fig: b"png")
    monkeypatch.setattr(summary_service, "calculate_basic_metrics", lambda df: {"count": len(df)})
    monkeypatch.setattr(summary_service, "calculate_player_summary", lambda df: pd.DataFrame([{"player": "Rodri"}]))

    assert build_dataframe_export(pd.DataFrame([{"x": 1}])) == b"csv"
    assert build_figure_export(object()) == b"png"
    assert get_summary_metrics(pd.DataFrame([{"x": 1}, {"x": 2}])) == {"count": 2}
    assert get_player_summary(pd.DataFrame([{"player": "Rodri"}]))["player"].tolist() == ["Rodri"]


def test_spatial_service_handles_selected_match_freeze_frames_and_fallback_columns():
    filtered_df = pd.DataFrame(
        [
            {"match_id": "1", "event_id": "evt-1", "has_freeze_frame": True},
            {"match_id": "2", "event_id": "evt-2", "has_freeze_frame": False},
        ]
    )
    freeze_frames_df = pd.DataFrame([{"event_id": "evt-1"}, {"event_id": "evt-1"}, {"event_id": "evt-3"}])

    assert get_spatial_match_ids("1", filtered_df) == ("1",)
    assert get_spatial_match_ids("Todos", filtered_df) == ("1", "2")
    assert get_spatial_match_ids(None, pd.DataFrame()) is None
    assert count_visible_spatial_events(filtered_df, freeze_frames_df) == 1
    assert count_visible_spatial_events(filtered_df, None) == 1
    assert count_visible_spatial_events(pd.DataFrame([{"three_sixty_event_id": "evt-1"}]), None) == 1


def test_prepare_spatial_and_voronoi_contexts(monkeypatch):
    event = pd.Series({"event_id": "evt-1"})
    freeze_frame_df = pd.DataFrame([{"player": "Rodri"}])
    warnings_result = {"regions_df": pd.DataFrame(), "reason": "sin regiones"}

    monkeypatch.setattr(
        spatial_analysis_service,
        "build_voronoi_regions_with_diagnostics",
        lambda df: warnings_result,
    )
    monkeypatch.setattr(
        spatial_analysis_service,
        "compute_delaunay_edges",
        lambda df: pd.DataFrame([{"edge": 1}]),
    )
    monkeypatch.setattr(
        spatial_analysis_service,
        "calculate_space_metrics",
        lambda ff, regions: pd.DataFrame([{"area": 1.0}]),
    )
    monkeypatch.setattr(
        spatial_analysis_service,
        "recommend_pass_by_delaunay",
        lambda selected_event, ff, edges: {"kind": "delaunay"},
    )
    monkeypatch.setattr(
        spatial_analysis_service,
        "suggest_alternative_pass_by_voronoi_area",
        lambda selected_event, ff, regions: {"kind": "voronoi"},
    )
    monkeypatch.setattr(
        spatial_analysis_service,
        "suggest_alternative_pass",
        lambda selected_event, ff, regions, scoring_profile=None: {"kind": scoring_profile},
    )

    base_context = prepare_spatial_event_context(
        selected_event=event,
        freeze_frame_df=freeze_frame_df,
        selected_plots=["combined"],
        scoring_profile="smart",
    )
    voronoi_context = prepare_voronoi_context(
        selected_event=event,
        freeze_frame_df=freeze_frame_df,
        selected_plots=["combined"],
        scoring_profile="smart",
    )
    metrics_context = get_voronoi_metrics_context(
        freeze_frame_df=freeze_frame_df,
        voronoi_regions_df=pd.DataFrame([{"player": "Rodri"}]),
    )
    alternatives_context = get_voronoi_alternatives_context(
        selected_event=event,
        freeze_frame_df=freeze_frame_df,
        voronoi_regions_df=pd.DataFrame([{"player": "Rodri"}]),
        scoring_profile="smart",
    )
    debug_context = get_voronoi_debug_context(
        voronoi_regions_df=pd.DataFrame([{"player": "Rodri"}]),
        space_metrics_df=pd.DataFrame([{"area": 1.0}]),
    )

    assert base_context["warnings"] == []
    assert voronoi_context["warnings"] == ["sin regiones"]
    assert voronoi_context["combined_delaunay_edges_df"].to_dict("records") == [{"edge": 1}]
    assert metrics_context["space_metrics_df"].to_dict("records") == [{"area": 1.0}]
    assert alternatives_context["delaunay_recommendation"] == {"kind": "delaunay"}
    assert alternatives_context["voronoi_recommendation"] == {"kind": "voronoi"}
    assert alternatives_context["scoring_recommendation"] == {"kind": "smart"}
    assert debug_context["debug_voronoi_regions_df"].to_dict("records") == [{"player": "Rodri"}]


def test_prepare_delaunay_contexts(monkeypatch):
    event = pd.Series({"event_id": "evt-1"})
    freeze_frame_df = pd.DataFrame([{"player": "Rodri"}])

    monkeypatch.setattr(
        spatial_analysis_service,
        "compute_delaunay_edges",
        lambda df: pd.DataFrame([{"edge": 1}]),
    )
    monkeypatch.setattr(
        spatial_analysis_service,
        "build_voronoi_regions_with_diagnostics",
        lambda df: {"regions_df": pd.DataFrame([{"region": 1}])},
    )
    monkeypatch.setattr(
        spatial_analysis_service,
        "recommend_pass_by_delaunay",
        lambda selected_event, ff, edges: {"kind": "delaunay"},
    )
    monkeypatch.setattr(
        spatial_analysis_service,
        "suggest_alternative_pass",
        lambda selected_event, ff, regions, scoring_profile=None: {"kind": scoring_profile},
    )

    context = prepare_delaunay_context(
        selected_event=event,
        freeze_frame_df=freeze_frame_df,
        selected_plots=["combined"],
        scoring_profile="smart",
    )
    connections_context = get_delaunay_connections_context(delaunay_edges_df=context["delaunay_edges_df"])
    alternatives_context = get_delaunay_alternatives_context(
        selected_event=event,
        freeze_frame_df=freeze_frame_df,
        scoring_profile="smart",
        delaunay_edges_df=context["delaunay_edges_df"],
    )
    debug_context = get_delaunay_debug_context(delaunay_edges_df=context["delaunay_edges_df"])

    assert context["delaunay_edges_df"].to_dict("records") == [{"edge": 1}]
    assert context["voronoi_regions_df"].to_dict("records") == [{"region": 1}]
    assert connections_context["delaunay_edges_df"].to_dict("records") == [{"edge": 1}]
    assert alternatives_context["delaunay_recommendation"] == {"kind": "delaunay"}
    assert alternatives_context["scoring_recommendation"] == {"kind": "smart"}
    assert debug_context["debug_edges_raw_df"].to_dict("records") == [{"edge": 1}]


def test_losses_service_exports_expected_symbols():
    assert "get_loss_events" in losses_service.__all__
    assert callable(losses_service.get_loss_events)
