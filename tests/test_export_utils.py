import matplotlib.pyplot as plt
import pandas as pd

from src.export_utils import dataframe_to_csv_bytes, figure_to_png_bytes


def test_dataframe_to_csv_bytes_returns_bytes():
    df = pd.DataFrame([{"a": 1}])

    csv_bytes = dataframe_to_csv_bytes(df)

    assert isinstance(csv_bytes, bytes)
    assert b"a" in csv_bytes


def test_figure_to_png_bytes_returns_bytes():
    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1])

    png_bytes = figure_to_png_bytes(fig)
    plt.close(fig)

    assert isinstance(png_bytes, bytes)
    assert len(png_bytes) > 0
