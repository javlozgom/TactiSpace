from src.presets import get_analysis_presets, get_preset


def test_get_analysis_presets_returns_non_empty_dict():
    presets = get_analysis_presets()

    assert isinstance(presets, dict)
    assert presets


def test_get_preset_returns_existing_preset():
    preset = get_preset("Análisis de mediocentro")

    assert preset
    assert "description" in preset


def test_get_preset_missing_returns_empty_dict():
    assert get_preset("No existe") == {}
