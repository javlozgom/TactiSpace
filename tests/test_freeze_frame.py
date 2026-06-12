import pandas as pd

from src.freeze_frame import (
    detect_freeze_frame_columns,
    get_freeze_frame_for_event,
    load_freeze_frames,
    normalize_freeze_frame_df,
    split_freeze_frame_players,
)


def test_detect_freeze_frame_columns_detects_expected_fields():
    df = pd.DataFrame(columns=["freeze_frame", "visible_area", "event_id"])
    result = detect_freeze_frame_columns(df)
    assert result["has_freeze_frame"] is True
    assert result["freeze_frame_column"] == "freeze_frame"
    assert result["visible_area_column"] == "visible_area"
    assert result["event_id_column"] == "event_id"


def test_normalize_freeze_frame_df_handles_empty_dataframe():
    df = normalize_freeze_frame_df(pd.DataFrame())
    assert df.empty
    assert "event_id" in df.columns


def test_get_freeze_frame_for_event_returns_empty_when_no_match():
    event_row = pd.Series({"event_id": "evt-1"})
    freeze_frames_df = pd.DataFrame([{"event_id": "evt-2", "player": "A", "x": 10, "y": 20}])
    result = get_freeze_frame_for_event(event_row, freeze_frames_df)
    assert result.empty


def test_split_freeze_frame_players_separates_teammates_and_opponents():
    freeze_frame_df = pd.DataFrame(
        [
            {"event_id": "evt-1", "player": "A", "teammate": True, "x": 10, "y": 20},
            {"event_id": "evt-1", "player": "B", "teammate": False, "x": 20, "y": 20},
        ]
    )
    teammates_df, opponents_df = split_freeze_frame_players(freeze_frame_df)
    assert len(teammates_df) == 1
    assert len(opponents_df) == 1


def test_load_freeze_frames_reads_raw_json_directory(tmp_path):
    raw_dir = tmp_path / "three_sixty"
    raw_dir.mkdir()
    (raw_dir / "3930158.json").write_text(
        (
            '[{"event_uuid":"evt-1","visible_area":[120,80,0,80],'
            '"freeze_frame":[{"teammate":true,"actor":true,"keeper":false,"location":[60,40]}]}]'
        ),
        encoding="utf-8",
    )

    result = load_freeze_frames(str(raw_dir))

    assert not result.empty
    assert "event_uuid" in result.columns


def test_load_freeze_frames_filters_raw_json_directory_by_match_ids(tmp_path):
    raw_dir = tmp_path / "three_sixty"
    raw_dir.mkdir()
    (raw_dir / "111.json").write_text(
        (
            '[{"event_uuid":"evt-111","visible_area":[120,80,0,80],'
            '"freeze_frame":[{"teammate":true,"actor":true,"keeper":false,"location":[60,40]}]}]'
        ),
        encoding="utf-8",
    )
    (raw_dir / "222.json").write_text(
        (
            '[{"event_uuid":"evt-222","visible_area":[120,80,0,80],'
            '"freeze_frame":[{"teammate":false,"actor":false,"keeper":false,"location":[30,20]}]}]'
        ),
        encoding="utf-8",
    )

    result = load_freeze_frames(str(raw_dir), match_ids=("222",))

    assert not result.empty
    assert result["event_uuid"].tolist() == ["evt-222"]
