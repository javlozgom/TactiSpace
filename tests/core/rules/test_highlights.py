import pandas as pd

from src.highlights import detect_highlight_actions, summarize_highlights


def test_detect_highlight_actions_detects_relevant_actions():
    df = pd.DataFrame(
        [
            {"event_type": "Pass", "player": "A", "team": "X", "minute": 1, "second": 1, "x": 20, "y": 20, "end_x": 40, "end_y": 30},
            {"event_type": "Carry", "player": "A", "team": "X", "minute": 1, "second": 2, "x": 30, "y": 20, "end_x": 45, "end_y": 30},
            {"event_type": "Shot", "player": "A", "team": "X", "minute": 1, "second": 3, "x": 100, "y": 30},
            {"event_type": "Ball Recovery", "player": "A", "team": "X", "minute": 1, "second": 4, "x": 70, "y": 30},
            {"event_type": "Pressure", "player": "A", "team": "X", "minute": 1, "second": 5, "x": 85, "y": 30},
            {"event_type": "Dispossessed", "player": "A", "team": "X", "minute": 1, "second": 6, "x": 30, "y": 30},
        ]
    )

    highlights = detect_highlight_actions(df)

    assert not highlights.empty
    assert "highlight_type" in highlights.columns


def test_summarize_highlights_counts_correctly():
    df = pd.DataFrame(
        [
            {"event_type": "Pass", "player": "A", "team": "X", "minute": 1, "second": 1, "x": 20, "y": 20, "end_x": 40, "end_y": 30},
            {"event_type": "Carry", "player": "A", "team": "X", "minute": 1, "second": 2, "x": 30, "y": 20, "end_x": 45, "end_y": 30},
            {"event_type": "Shot", "player": "A", "team": "X", "minute": 1, "second": 3, "x": 100, "y": 30},
        ]
    )

    summary = summarize_highlights(df)

    assert summary["total_highlights"] >= 3
