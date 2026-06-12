from __future__ import annotations

import base64
from pathlib import Path


def asset_data_uri(relative_path: str) -> str:
    """Return one local UI asset as a data URI for injected CSS."""
    asset_path = Path(__file__).resolve().parent.parent / relative_path
    try:
        encoded = base64.b64encode(asset_path.read_bytes()).decode("ascii")
    except OSError:
        return ""
    suffix = asset_path.suffix.lower()
    mime_type = {
        ".png": "image/png",
        ".svg": "image/svg+xml",
    }.get(suffix, "image/jpeg")
    return f"data:{mime_type};base64,{encoded}"


def header_background_image() -> str:
    """Return the CSS image value for the sticky app header background."""
    header_background_uri = asset_data_uri("assets/header_background.png")
    if header_background_uri:
        return f'url("{header_background_uri}")'
    return "linear-gradient(180deg, #ffffff, #eff6ff)"


def hero_visual_image() -> str:
    """Return the CSS image value for the hero-side decorative visual."""
    hero_visual_uri = asset_data_uri("assets/hero_visual.svg")
    return f'url("{hero_visual_uri}")' if hero_visual_uri else "none"
