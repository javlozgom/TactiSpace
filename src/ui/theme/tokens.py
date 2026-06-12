from __future__ import annotations

SPACE_XS = "0.28rem"
SPACE_SM = "0.55rem"
SPACE_MD = "0.95rem"
SPACE_LG = "1.28rem"
SPACE_XL = "1.95rem"
SECTION_GAP = "1.28rem"
CARD_PADDING = "1.08rem"
GRID_GAP = "0.95rem"

PAGE_TITLE_SIZE = "clamp(1.52rem, 1.6vw, 1.76rem)"
PAGE_SUBTITLE_SIZE = "0.99rem"
SECTION_TITLE_SIZE = "1.08rem"
CARD_TITLE_SIZE = "0.96rem"
BODY_SIZE = "0.95rem"
CAPTION_SIZE = "0.81rem"
METRIC_VALUE_SIZE = "1.5rem"

CARD_RADIUS = "16px"
BUTTON_RADIUS = "999px"
PANEL_RADIUS = "16px"

TEXT_PRIMARY = "#071338"
TEXT_SECONDARY = "#334155"
MUTED = "#64748b"
BORDER = "rgba(15, 23, 42, .10)"
CARD_BG = "#ffffff"
PANEL_BG = "#fbfdff"
ACCENT = "#0b63f6"
SUCCESS = "#16a34a"
WARNING = "#ea580c"
DANGER = "#dc2626"

CARD_SHADOW = "0 20px 46px rgba(15, 23, 42, .075)"
SUBTLE_SHADOW = "0 10px 28px rgba(15, 23, 42, .05)"


def css_token_vars() -> str:
    """Return CSS custom properties mirroring the Python theme tokens."""
    return f"""
        --tacti-space-xs: {SPACE_XS};
        --tacti-space-sm: {SPACE_SM};
        --tacti-space-md: {SPACE_MD};
        --tacti-space-lg: {SPACE_LG};
        --tacti-space-xl: {SPACE_XL};
        --tacti-section-gap: {SECTION_GAP};
        --tacti-card-padding: {CARD_PADDING};
        --tacti-grid-gap: {GRID_GAP};
        --tacti-page-title-size: {PAGE_TITLE_SIZE};
        --tacti-page-subtitle-size: {PAGE_SUBTITLE_SIZE};
        --tacti-section-title-size: {SECTION_TITLE_SIZE};
        --tacti-card-title-size: {CARD_TITLE_SIZE};
        --tacti-body-size: {BODY_SIZE};
        --tacti-caption-size: {CAPTION_SIZE};
        --tacti-metric-value-size: {METRIC_VALUE_SIZE};
        --tacti-card-radius: {CARD_RADIUS};
        --tacti-button-radius: {BUTTON_RADIUS};
        --tacti-panel-radius: {PANEL_RADIUS};
        --tacti-text-primary: {TEXT_PRIMARY};
        --tacti-text-secondary: {TEXT_SECONDARY};
        --tacti-muted: {MUTED};
        --tacti-border: {BORDER};
        --tacti-card-bg: {CARD_BG};
        --tacti-panel-bg: {PANEL_BG};
        --tacti-accent: {ACCENT};
        --tacti-success: {SUCCESS};
        --tacti-warning: {WARNING};
        --tacti-danger: {DANGER};
        --tacti-card-shadow: {CARD_SHADOW};
        --tacti-subtle-shadow: {SUBTLE_SHADOW};
    """.strip()
