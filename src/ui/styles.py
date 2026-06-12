"""Centralised Streamlit styling for the TactiSpace app."""

from __future__ import annotations

from src.ui.style_system.global_css import apply_global_styles as apply_app_styles


def apply_global_styles() -> None:
    """Backward-compatible alias."""
    apply_app_styles()


def render_fixed_shell_start() -> None:
    """Compatibility helper."""
    return None


def render_fixed_shell_end() -> None:
    """Compatibility helper."""
    return None


def render_tabs_container_start() -> None:
    """Compatibility helper."""
    return None


def render_tabs_container_end() -> None:
    """Compatibility helper."""
    return None
