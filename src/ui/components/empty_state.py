from __future__ import annotations

from src.ui.components.cards import render_empty_state as _render_empty_state


def render_empty_state(message: str, hint: str | None = None) -> None:
    """Render the shared empty state."""
    _render_empty_state(message, hint)
