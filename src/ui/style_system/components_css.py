from __future__ import annotations


def build_components_css(hero_visual_image: str) -> str:
    """Return CSS for shared cards, headers and panels."""
    return f"""
        .fea-page-header,
        .fea-hero,
        .fea-soft-card,
        .fea-glass-card,
        .fea-kpi-card,
        .fea-feature-card,
        .fea-step-card,
        .fea-demo-card,
        .fea-term-card,
        .fea-info-box,
        .fea-context-bar,
        div[data-testid="stVerticalBlockBorderWrapper"] {{
            border-radius: var(--fea-radius) !important;
        }}

        .fea-hero {{
            margin-bottom: 18px;
            padding: clamp(20px, 2.2vw, 28px);
            background:
                linear-gradient(180deg, rgba(255, 255, 255, .98), rgba(248, 251, 255, .96)),
                radial-gradient(circle at 88% 0%, rgba(14, 165, 233, .10), transparent 26%);
            border: 1px solid var(--fea-border);
            box-shadow: 0 10px 26px rgba(15, 23, 42, .045);
        }}

        .fea-page-header {{
            position: relative;
            min-height: 176px;
            margin-bottom: 20px;
            padding: clamp(22px, 2.45vw, 31px);
            overflow: hidden;
            background:
                linear-gradient(90deg, rgba(255,255,255,.98) 0%, rgba(247,250,255,.96) 48%, rgba(241,246,252,.96) 100%),
                radial-gradient(circle at 76% 14%, rgba(124,58,237,.22), transparent 26%),
                radial-gradient(circle at 91% 45%, rgba(20,184,166,.18), transparent 30%);
            border: 1px solid var(--fea-border);
            box-shadow: 0 12px 30px rgba(15, 23, 42, .055);
        }}

        .fea-page-header::after {{
            content: "";
            position: absolute;
            inset: 0;
            z-index: 0;
            pointer-events: none;
            background: linear-gradient(
                90deg,
                rgba(255, 255, 255, 0) 0%,
                rgba(255, 255, 255, .02) 58%,
                rgba(255, 255, 255, .20) 72%,
                rgba(255, 255, 255, .55) 86%,
                rgba(255, 255, 255, .78) 100%
            );
        }}

        .fea-page-copy {{
            position: relative;
            z-index: 2;
            max-width: 760px;
        }}

        .fea-page-eyebrow,
        .fea-badge,
        .method-badge {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            width: fit-content;
            max-width: 100%;
            margin: 0;
            padding: 6px 10px;
            border-radius: 999px;
            border: 1px solid rgba(15, 23, 42, .09);
            background: #f8fafc;
            color: #475569;
            font-size: .75rem;
            font-weight: 900;
            line-height: 1.08;
            overflow-wrap: anywhere;
        }}

        .fea-page-eyebrow {{
            margin-bottom: 12px;
            color: var(--blue);
            background: #eff6ff;
            border-color: #bfdbfe;
        }}

        .fea-page-header h2,
        .fea-hero h2 {{
            margin: 0 !important;
            color: var(--navy);
            font-size: var(--fea-title-size);
            font-weight: 950;
            line-height: 1.1;
            letter-spacing: -.01em;
        }}

        .fea-page-header p,
        .fea-hero p {{
            margin: 11px 0 0 0 !important;
            color: #334155;
            font-size: var(--fea-subtitle-size);
            line-height: 1.6;
            max-width: 64ch;
        }}

        .fea-hero-visual {{
            position: absolute;
            right: 4px;
            top: 4px;
            width: min(48%, 760px);
            height: calc(100% - 8px);
            z-index: 1;
            opacity: .94;
            background:
                linear-gradient(90deg, rgba(255,255,255,0) 0%, rgba(255,255,255,.18) 20%, rgba(255,255,255,.56) 42%, rgba(255,255,255,.84) 62%, rgba(255,255,255,.96) 100%),
                {hero_visual_image} center / contain no-repeat;
            -webkit-mask-image: linear-gradient(90deg, transparent 0%, rgba(0,0,0,.34) 11%, rgba(0,0,0,.82) 26%, rgba(0,0,0,1) 42%, rgba(0,0,0,1) 100%);
            mask-image: linear-gradient(90deg, transparent 0%, rgba(0,0,0,.34) 11%, rgba(0,0,0,.82) 26%, rgba(0,0,0,1) 42%, rgba(0,0,0,1) 100%);
        }}

        .fea-section-header {{
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: 14px;
            margin: 18px 0 10px;
        }}

        .fea-section-title-wrap {{
            display: flex;
            align-items: flex-start;
            gap: 11px;
            min-width: 0;
        }}

        .fea-section-icon,
        .fea-kpi-icon,
        .fea-feature-icon,
        .fea-demo-icon,
        .fea-info-icon,
        .fea-filter-title-icon,
        .fea-filter-label-icon {{
            display: inline-grid;
            place-items: center;
            flex: 0 0 auto;
            color: var(--blue);
            background: #eff6ff;
            border: 1px solid #bfdbfe;
            border-radius: 999px;
        }}

        .fea-section-icon {{
            width: 32px;
            height: 32px;
            border-radius: 11px;
        }}

        .fea-section-header h3 {{
            margin: 0 !important;
            color: var(--navy);
            font-size: var(--fea-section-size);
            font-weight: 950;
            line-height: 1.22;
        }}

        .fea-section-header p {{
            margin: 4px 0 0 0 !important;
            color: var(--fea-muted);
            font-size: .91rem;
            line-height: 1.52;
            max-width: 70ch;
        }}

        .fea-kpi-grid,
        .fea-card-grid,
        .fea-term-grid {{
            display: grid;
            width: 100%;
            gap: var(--fea-gap);
        }}

        .fea-kpi-grid {{
            grid-template-columns: repeat(auto-fit, minmax(min(220px, 100%), 1fr));
        }}

        .fea-card-grid-4 {{
            grid-template-columns: repeat(auto-fit, minmax(min(215px, 100%), 1fr));
        }}

        .fea-card-grid-3,
        .fea-term-grid {{
            grid-template-columns: repeat(auto-fit, minmax(min(260px, 100%), 1fr));
        }}

        .fea-kpi-card,
        .fea-feature-card,
        .fea-step-card,
        .fea-demo-card,
        .fea-term-card,
        .fea-info-box,
        div[data-testid="stVerticalBlockBorderWrapper"] {{
            background: linear-gradient(180deg, #ffffff, #fbfdff) !important;
            border: 1px solid var(--fea-border) !important;
            box-shadow: 0 10px 26px rgba(15, 23, 42, .05) !important;
        }}

        .fea-debug-panel,
        .tacti-debug-panel {{
            background: linear-gradient(180deg, rgba(248, 250, 252, .96), rgba(255, 255, 255, .98));
            border: 1px solid rgba(148, 163, 184, .18);
        }}

        .fea-kpi-card,
        .fea-feature-card,
        .fea-step-card,
        .fea-demo-card,
        .fea-term-card {{
            height: 100%;
            min-height: 122px;
            padding: var(--fea-card-padding);
        }}

        .fea-kpi-top {{
            display: flex;
            align-items: center;
            gap: 11px;
        }}

        .fea-kpi-icon,
        .fea-feature-icon,
        .fea-demo-icon,
        .fea-info-icon {{
            width: 42px;
            height: 42px;
        }}

        .fea-kpi-label {{
            color: #334155;
            font-size: .83rem;
            font-weight: 850;
            line-height: 1.28;
        }}

        .fea-kpi-value {{
            margin-top: 13px;
            color: var(--navy);
            font-size: 1.72rem;
            font-weight: 950;
            line-height: 1.05;
            overflow-wrap: anywhere;
        }}

        .fea-kpi-sub,
        .fea-feature-card p,
        .fea-step-card p,
        .fea-demo-card p,
        .fea-term-card p,
        .fea-info-body {{
            margin: 8px 0 0;
            color: var(--fea-muted);
            font-size: var(--fea-body-size);
            line-height: 1.6;
        }}

        .fea-feature-card h4,
        .fea-step-card h4,
        .fea-demo-card h4,
        .fea-term-card h4,
        .fea-info-title {{
            margin: 10px 0 0 !important;
            color: var(--navy);
            font-size: var(--tacti-card-title-size);
            font-weight: 950;
            line-height: 1.24;
        }}

        .fea-kpi-blue .fea-kpi-value, .fea-badge-blue, .fea-badge-primary {{ color: var(--blue); }}
        .fea-kpi-green .fea-kpi-value, .fea-badge-green {{ color: var(--green); }}
        .fea-kpi-red .fea-kpi-value, .fea-badge-red {{ color: var(--red); }}
        .fea-kpi-orange .fea-kpi-value, .fea-badge-orange {{ color: var(--orange); }}
        .fea-kpi-purple .fea-kpi-value, .fea-badge-purple {{ color: var(--purple); }}
        .fea-kpi-teal .fea-kpi-value, .fea-badge-teal {{ color: var(--teal); }}

        .fea-badge-blue, .fea-badge-primary {{ background: #eff6ff; border-color: #bfdbfe; }}
        .fea-badge-green {{ background: #f0fdf4; border-color: #bbf7d0; }}
        .fea-badge-red {{ background: #fef2f2; border-color: #fecaca; }}
        .fea-badge-orange {{ background: #fff7ed; border-color: #fed7aa; }}
        .fea-badge-purple {{ background: #f5f3ff; border-color: #ddd6fe; }}
        .fea-badge-teal {{ background: #f0fdfa; border-color: #99f6e4; }}

        .fea-badge-dot {{
            width: 6px;
            height: 6px;
            border-radius: 999px;
            background: currentColor;
        }}

        .fea-badges-row,
        .fea-inline-badges,
        .fea-hero-badges {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin: 11px 0;
        }}

        .fea-info-box {{
            display: flex;
            gap: 12px;
            padding: 16px 16px;
            border-left: 4px solid var(--blue) !important;
        }}

        .fea-context-bar {{
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            gap: 10px;
            margin: 12px 0 16px;
            padding: 13px 14px;
            background: rgba(255, 255, 255, .88);
            border: 1px solid var(--fea-border);
            box-shadow: var(--fea-shadow-soft);
        }}

        .fea-context-item {{
            display: inline-flex;
            align-items: center;
            gap: 7px;
            padding: 7px 11px;
            color: var(--fea-muted);
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 999px;
            font-size: .84rem;
            line-height: 1.18;
        }}

        .fea-plot-toolbar {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
            margin: 10px 0 8px;
            padding: 10px 12px;
            background: rgba(248, 250, 252, .78);
            border: 1px solid rgba(148, 163, 184, .18);
            border-radius: 12px;
        }}

        .fea-plot-toolbar-copy {{
            color: var(--fea-muted);
            font-size: var(--fea-caption-size);
            line-height: 1.45;
        }}

        .fea-plot-toolbar-copy strong {{
            color: var(--navy);
            font-weight: 850;
        }}

        .fea-context-item strong {{
            color: var(--blue);
            font-weight: 900;
        }}

        @media (max-width: 1180px) {{
            .fea-hero-visual {{
                display: none;
            }}
        }}

        @media (max-width: 900px) {{
            .fea-page-header {{
                min-height: auto;
            }}
            .fea-page-header h2,
            .fea-hero h2 {{
                font-size: 1.5rem;
            }}
        }}
    """
