from __future__ import annotations

from src.ui.views.percentiles import _format_percentile_preset_label


def test_format_percentile_preset_label_uses_metric_labels():
    presets = {
        "Producción goleadora": {
            "x_metric": "total_shots",
            "y_metric": "goals",
        }
    }

    result = _format_percentile_preset_label("Producción goleadora", presets)

    assert result == "Tiros totales / Goles"


def test_format_percentile_preset_label_falls_back_to_preset_name():
    assert _format_percentile_preset_label("Preset libre", {}) == "Preset libre"
