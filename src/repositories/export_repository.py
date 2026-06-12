from __future__ import annotations

import io

import pandas as pd


def dataframe_to_csv_bytes(df: pd.DataFrame) -> bytes:
    """Serialize a dataframe to UTF-8 CSV bytes."""
    try:
        return df.to_csv(index=False).encode("utf-8")
    except Exception as exc:  # pragma: no cover - defensive
        raise ValueError(f"No se pudo exportar el DataFrame a CSV: {exc}") from exc


def figure_to_png_bytes(fig) -> bytes:
    """Serialize a matplotlib figure to PNG bytes."""
    buffer = io.BytesIO()
    try:
        fig.savefig(buffer, format="png", bbox_inches="tight")
        buffer.seek(0)
        return buffer.getvalue()
    except Exception as exc:  # pragma: no cover - defensive
        raise ValueError(f"No se pudo exportar la figura a PNG: {exc}") from exc
    finally:
        buffer.close()
