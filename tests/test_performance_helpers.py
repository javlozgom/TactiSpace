import pandas as pd

from src.ui.components import limit_dataframe_rows


def test_limit_dataframe_rows_truncates_large_dataframe():
    df = pd.DataFrame({"value": range(1205)})

    preview_df, total_rows, was_limited = limit_dataframe_rows(df, max_rows=1000)

    assert total_rows == 1205
    assert was_limited is True
    assert len(preview_df) == 1000


def test_limit_dataframe_rows_keeps_small_dataframe():
    df = pd.DataFrame({"value": [1, 2, 3]})

    preview_df, total_rows, was_limited = limit_dataframe_rows(df, max_rows=1000)

    assert total_rows == 3
    assert was_limited is False
    assert len(preview_df) == 3
