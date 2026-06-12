from src.ui.sidebar import _is_selectable_player_name


def test_is_selectable_player_name_excludes_unknown_and_empty_values():
    assert _is_selectable_player_name("Rodri") is True
    assert _is_selectable_player_name(" Unknown ") is False
    assert _is_selectable_player_name("") is False
    assert _is_selectable_player_name(None) is False
