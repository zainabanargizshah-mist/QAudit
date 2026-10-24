"""Shared visual language and interaction helpers for the Q-Shield UI."""

from __future__ import annotations

from html import escape
from typing import Iterable, Optional

import streamlit as st
from streamlit.errors import StreamlitAPIException


NAV_ITEMS = [
    ("app.py", "Command Center", "⌂", "Overview"),
    ("pages/1_Asset_Inventory.py", "Inventory", "▦", "Asset inventory"),
    ("pages/2_Risk_Assessment.py", "Risk Queue", "◈", "Prioritized findings"),
    ("pages/3_Migration_Planner.py", "Migration Roadmap", "↗", "PQC transition plan"),
    ("pages/4_Reports.py", "Reports", "▤", "Exports and summaries"),
    ("pages/5_Methodology.py", "Standards", "◎", "Rules and references"),
]


def render_cyber_background() -> None:
    """Render a lightweight animated cyber-security backdrop behind the UI."""
    st.markdown(
        """
        <div class="qs-cyber-background" aria-hidden="true">
            <div class="qs-cyber-orbit qs-orbit-one"></div>
            <div class="qs-cyber-orbit qs-orbit-two"></div>
            <div class="qs-cyber-node qs-node-one"></div>
            <div class="qs-cyber-node qs-node-two"></div>
            <div class="qs-cyber-node qs-node-three"></div>
            <div class="qs-floating-icon qs-float-shield">◈</div>
            <div class="qs-floating-icon qs-float-lock">⌑</div>
            <div class="qs-floating-icon qs-float-key">⚿</div>
            <div class="qs-floating-icon qs-float-network">⌬</div>
            <div class="qs-floating-icon qs-float-quantum">⟡</div>
            <div class="qs-floating-icon qs-float-audit">◎</div>
            <div class="qs-cyber-telemetry qs-telemetry-left">01001001<br>10110010<br>00101101<br>11010100</div>
            <div class="qs-cyber-telemetry qs-telemetry-right">N1 // INVENTORY<br>N2 // DETECT<br>N3 // SCORE<br>N4 // MIGRATE<br>N5 // VERIFY</div>
            <div class="qs-cyber-scanline"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_flow_map(steps: Iterable[tuple[str, str, str]]) -> None:
    """Render the continuous operational flow used across the dashboard."""
    cards = []
    for code, title, copy in steps:
        cards.append(
            f"""
            <div class="qs-flow-step">
                <div class="qs-flow-code">{escape(code)}</div>
                <div class="qs-flow-title">{escape(title)}</div>
                <div class="qs-flow-copy">{escape(copy)}</div>
            </div>
            """
        )
    # Keep the HTML block compact. Streamlit's Markdown renderer can close a
    # raw HTML block when it encounters blank lines between nested elements.
    markup = "".join(card.replace("\n", " ") for card in cards)
    st.markdown(f'<div class="qs-flow-map">{markup}</div>', unsafe_allow_html=True)


def render_telemetry_marquee(items: Iterable[tuple[str, str]]) -> None:
    """Render an ambient, data-driven telemetry band."""
    item_html = []
    for label, value in items:
        item_html.append(
            f'<div class="qs-marquee-item"><span class="qs-marquee-dot"></span><span>{escape(label)} · {escape(value)}</span></div>'
        )
    track = "".join(item_html) * 2
    st.markdown(f'<div class="qs-marquee"><div class="qs-marquee-track">{track}</div></div>', unsafe_allow_html=True)


def inject_styles() -> None:
    """Apply the shared Q-Shield visual system to the current Streamlit page."""
    st.markdown(
        """
        <style>
            :root {
                --qs-ink: #080808;
                --qs-muted: #5f5f64;
                --qs-muted-2: #8f8f94;
                --qs-canvas: #f0eef2;
                --qs-card: #ffffff;
                --qs-border: #cfcfd3;
                --qs-red: #ff1018;
                --qs-red-dark: #c9070d;
                --qs-grid: rgba(7, 7, 7, 0.09);
            }

            .stApp {
                background: var(--qs-canvas);
                background-image:
                    linear-gradient(var(--qs-grid) 1px, transparent 1px),
                    linear-gradient(90deg, var(--qs-grid) 1px, transparent 1px);
                background-size: 48px 48px;
            }

            [data-testid="stAppViewContainer"] { position: relative; }
            .main { position: relative; z-index: 1; }

            .qs-cyber-background {
                position: fixed;
                inset: 0;
                z-index: 0;
                overflow: hidden;
                pointer-events: none;
                opacity: 0.58;
            }

            .qs-cyber-background::before {
                content: "";
                position: absolute;
                inset: -10%;
                background:
                    radial-gradient(circle at 16% 27%, rgba(255,16,24,0.12), transparent 16%),
                    radial-gradient(circle at 83% 72%, rgba(0,0,0,0.12), transparent 21%),
                    repeating-linear-gradient(135deg, transparent 0 62px, rgba(0,0,0,0.06) 63px 64px);
                animation: qs-field-drift 24s linear infinite;
            }

            .qs-cyber-background::after {
                content: "";
                position: absolute;
                left: 0;
                right: 0;
                top: -4px;
                height: 2px;
                background: var(--qs-red);
                box-shadow: 0 0 20px rgba(255,16,24,0.75);
                opacity: 0.38;
                animation: qs-scan 11s linear infinite;
            }

            .qs-cyber-orbit {
                position: absolute;
                width: 420px;
                height: 420px;
                border: 1px solid rgba(8,8,8,0.16);
                border-radius: 50%;
                transform: rotate(-28deg) skewX(-12deg);
                animation: qs-orbit 20s linear infinite;
            }

            .qs-orbit-one { left: -180px; top: 20%; }
            .qs-orbit-two { right: -180px; bottom: -5%; width: 520px; height: 520px; animation-direction: reverse; animation-duration: 28s; }

            .qs-cyber-node {
                position: absolute;
                width: 8px;
                height: 8px;
                background: var(--qs-red);
                box-shadow: 0 0 0 5px rgba(255,16,24,0.13), 0 0 20px rgba(255,16,24,0.42);
                animation: qs-node-pulse 2.5s ease-in-out infinite;
            }

            .qs-node-one { left: 18%; top: 24%; }
            .qs-node-two { right: 18%; top: 48%; animation-delay: 0.8s; }
            .qs-node-three { left: 62%; bottom: 14%; animation-delay: 1.45s; }

            .qs-cyber-telemetry {
                position: absolute;
                color: rgba(8,8,8,0.4);
                font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
                font-size: 0.58rem;
                line-height: 1.9;
                letter-spacing: 0.13em;
                white-space: nowrap;
                animation: qs-telemetry 8s ease-in-out infinite alternate;
            }

            .qs-telemetry-left { left: 3%; top: 38%; transform: rotate(-90deg); transform-origin: left top; }
            .qs-telemetry-right { right: 2%; bottom: 22%; transform: rotate(90deg); transform-origin: right bottom; color: rgba(255,16,24,0.56); animation-delay: 1.6s; }

            .qs-flow-map {
                display: grid;
                grid-template-columns: repeat(4, minmax(0, 1fr));
                gap: 0;
                margin: 22px 0 30px;
                border-top: 1px solid #080808;
                border-bottom: 1px solid #080808;
                background: rgba(240,238,242,0.82);
            }

            .qs-flow-step {
                position: relative;
                min-height: 112px;
                padding: 16px 18px 18px;
                border-right: 1px solid #080808;
                transition: background 160ms ease, color 160ms ease, transform 160ms ease;
            }

            .qs-flow-step:last-child { border-right: 0; }
            .qs-flow-step:hover { color: #ffffff; background: #080808; transform: translateY(-4px); }
            .qs-flow-step:hover .qs-flow-code { color: var(--qs-red); }
            .qs-flow-step:hover .qs-flow-copy { color: #d5d5d8; }

            .qs-flow-step:not(:last-child)::after {
                content: "";
                position: absolute;
                top: 50%;
                right: -1px;
                width: 22px;
                height: 1px;
                background: var(--qs-red);
                z-index: 2;
                animation: qs-flow-pulse 2.4s ease-in-out infinite;
            }

            .qs-flow-code { color: var(--qs-red); font: 950 0.72rem ui-monospace, SFMono-Regular, Menlo, monospace; letter-spacing: 0.12em; }
            .qs-flow-title { margin-top: 8px; color: #080808; font-weight: 950; text-transform: uppercase; }
            .qs-flow-step:hover .qs-flow-title { color: #ffffff; }
            .qs-flow-copy { margin-top: 5px; color: var(--qs-muted); font-size: 0.75rem; line-height: 1.4; }

            .qs-marquee {
                overflow: hidden;
                margin: 0 0 26px;
                border-top: 1px solid #080808;
                border-bottom: 1px solid #080808;
                background: #080808;
            }

            .qs-marquee-track {
                display: flex;
                width: max-content;
                animation: qs-marquee 32s linear infinite;
            }

            .qs-marquee-item {
                display: flex;
                align-items: center;
                gap: 10px;
                min-width: 235px;
                padding: 12px 18px;
                border-right: 1px solid rgba(255,255,255,0.28);
                color: #ffffff;
                font: 0.72rem ui-monospace, SFMono-Regular, Menlo, monospace;
                letter-spacing: 0.04em;
                text-transform: uppercase;
            }

            .qs-marquee-dot { width: 7px; height: 7px; background: var(--qs-red); box-shadow: 0 0 10px rgba(255,16,24,0.8); }

            [data-testid="stHeader"] {
                background: rgba(240, 238, 242, 0.58);
                border-bottom: 1px solid rgba(8, 8, 8, 0.14);
                backdrop-filter: blur(18px) saturate(1.12);
                -webkit-backdrop-filter: blur(18px) saturate(1.12);
            }

            [data-testid="stSidebar"] {
                background: #050505;
                border-right: 3px solid var(--qs-red);
            }

            [data-testid="stSidebar"] * {
                color: #ffffff !important;
            }

            [data-testid="stSidebar"] .stButton button {
                border: 1px solid #ffffff;
                background: #050505;
            }

            [data-testid="stSidebar"] .stButton button:hover {
                border-color: var(--qs-red);
                color: #ffffff;
                background: var(--qs-red-dark);
            }

            .qs-brand {
                display: flex;
                align-items: center;
                gap: 10px;
                padding: 5px 0 12px;
                border-bottom: 1px solid rgba(255,255,255,0.28);
            }

            .qs-brand-mark {
                width: 38px;
                height: 38px;
                display: grid;
                place-items: center;
                border-radius: 0;
                color: #050505;
                background: var(--qs-red);
                font-size: 1.15rem;
                font-weight: 950;
                box-shadow: 6px 6px 0 #ffffff;
            }

            .qs-brand-name {
                color: #ffffff;
                font-size: 1.04rem;
                font-weight: 950;
                letter-spacing: 0.02em;
                text-transform: uppercase;
            }

            .qs-brand-subtitle {
                margin-top: -2px;
                color: #bcbcc2;
                font-size: 0.72rem;
                letter-spacing: 0.06em;
                text-transform: uppercase;
            }

            .qs-nav-label {
                color: var(--qs-red) !important;
                font-size: 0.68rem;
                font-weight: 950;
                letter-spacing: 0.16em;
                text-transform: uppercase;
                margin: 18px 0 8px;
            }

            .qs-ops-strip {
                display: flex;
                justify-content: space-between;
                gap: 4px;
                margin: 14px 0 4px;
                padding: 7px 8px;
                border-top: 1px solid #ffffff;
                border-bottom: 1px solid #ffffff;
                color: #ffffff;
                font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
                font-size: 0.58rem;
                letter-spacing: 0.08em;
            }

            .qs-ops-strip span:nth-child(5) { color: var(--qs-red); }

            [data-testid="stSidebar"] a {
                border-left: 3px solid transparent;
                padding: 8px 10px !important;
                margin: 3px 0;
                transition: all 160ms ease;
            }

            [data-testid="stSidebar"] a:hover {
                border-left-color: var(--qs-red);
                background: rgba(255, 16, 24, 0.16);
                transform: translateX(4px);
            }

            .qs-page-header {
                position: relative;
                overflow: hidden;
                margin: 0 0 22px;
                padding: 26px 30px 30px;
                border: 2px solid #080808;
                border-radius: 0;
                color: #ffffff;
                background: #080808;
                box-shadow: 10px 10px 0 var(--qs-red);
                animation: qs-enter 360ms ease-out both;
            }

            .qs-page-header::after {
                content: "";
                position: absolute;
                inset: 0;
                background-image:
                    linear-gradient(rgba(255,255,255,0.12) 1px, transparent 1px),
                    linear-gradient(90deg, rgba(255,255,255,0.12) 1px, transparent 1px);
                background-size: 32px 32px;
                opacity: 0.28;
                pointer-events: none;
                animation: qs-drift 18s linear infinite;
            }

            .qs-eyebrow {
                position: relative;
                z-index: 1;
                margin-bottom: 6px;
                color: var(--qs-red);
                font-size: 0.72rem;
                font-weight: 950;
                letter-spacing: 0.18em;
                text-transform: uppercase;
            }

            .qs-page-header h1 {
                position: relative;
                z-index: 1;
                margin: 0;
                color: #ffffff !important;
                font-size: clamp(1.55rem, 2.5vw, 2.2rem);
                font-weight: 950;
                letter-spacing: -0.045em;
                text-transform: uppercase;
            }

            .qs-page-header p {
                position: relative;
                z-index: 1;
                max-width: 760px;
                margin: 8px 0 0;
                color: #e1e1e4;
                font-size: 0.96rem;
                line-height: 1.55;
            }

            .qs-section-title {
                margin: 28px 0 10px;
                color: var(--qs-ink);
                font-size: 1.08rem;
                font-weight: 950;
                letter-spacing: 0.01em;
                text-transform: uppercase;
            }

            .qs-section-caption {
                margin: -4px 0 12px;
                color: var(--qs-muted);
                font-size: 0.84rem;
            }

            .qs-card {
                height: 100%;
                position: relative;
                padding: 18px;
                border: 1px solid #080808;
                border-radius: 0;
                background: var(--qs-card);
                box-shadow: 5px 5px 0 #080808;
                transition: transform 170ms ease, box-shadow 170ms ease, border-color 170ms ease;
                animation: qs-rise 420ms ease-out both;
            }

            .qs-card:hover {
                border-color: var(--qs-red);
                box-shadow: 8px 8px 0 var(--qs-red);
                transform: translate(-2px, -2px);
            }

            .qs-card-title {
                margin-bottom: 5px;
                color: var(--qs-red-dark);
                font-size: 0.74rem;
                font-weight: 950;
                letter-spacing: 0.12em;
                text-transform: uppercase;
            }

            .qs-card-value {
                color: var(--qs-ink);
                font-size: 1.72rem;
                font-weight: 950;
                letter-spacing: -0.04em;
            }

            .qs-card-help {
                margin-top: 5px;
                color: var(--qs-muted-2);
                font-size: 0.77rem;
            }

            .qs-risk-pill,
            .qs-status-pill {
                display: inline-flex;
                align-items: center;
                gap: 5px;
                padding: 4px 9px;
                border-radius: 999px;
                font-size: 0.72rem;
                font-weight: 800;
                white-space: nowrap;
            }

            .qs-risk-critical { color: #ffffff; background: var(--qs-red); }
            .qs-risk-high { color: #ffffff; background: #0a0a0a; }
            .qs-risk-medium { color: #0a0a0a; background: #e4e0e4; border: 1px solid #0a0a0a; }
            .qs-risk-low { color: #ffffff; background: #66666b; }
            .qs-risk-unknown { color: #ffffff; background: #99999f; }

            .qs-status-progress { color: #ffffff; background: #0a0a0a; }
            .qs-status-pqc { color: #ffffff; background: var(--qs-red); }
            .qs-status-review { color: #0a0a0a; background: #e4e0e4; border: 1px solid #0a0a0a; }

            .qs-action-item {
                display: flex;
                align-items: flex-start;
                gap: 12px;
                padding: 12px 0;
                border-bottom: 1px solid #0a0a0a;
            }

            .qs-action-item:last-child { border-bottom: 0; padding-bottom: 0; }

            .qs-action-index {
                display: grid;
                flex: 0 0 26px;
                height: 26px;
                place-items: center;
                border-radius: 0;
                color: #ffffff;
                background: var(--qs-red);
                font-size: 0.75rem;
                font-weight: 800;
            }

            .qs-action-title { color: var(--qs-ink); font-weight: 800; font-size: 0.88rem; }
            .qs-action-meta { margin-top: 3px; color: var(--qs-muted); font-size: 0.78rem; line-height: 1.4; }

            .qs-callout {
                padding: 12px 14px;
                border-left: 4px solid var(--qs-red);
                border-radius: 0 10px 10px 0;
                color: #0a0a0a;
                background: #ffffff;
                border-top: 1px solid #0a0a0a;
                border-bottom: 1px solid #0a0a0a;
                font-size: 0.84rem;
                line-height: 1.5;
            }

            .qs-muted { color: var(--qs-muted); }
            .qs-mono { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; }

            [data-testid="stMetric"] {
                padding: 14px 16px;
                border: 1px solid #0a0a0a;
                border-radius: 0;
                background: var(--qs-card);
                box-shadow: 5px 5px 0 var(--qs-red);
                transition: transform 170ms ease;
            }

            [data-testid="stMetric"]:hover { transform: translate(-2px, -2px); }

            [data-testid="stMetric"] label { color: var(--qs-muted) !important; }
            [data-testid="stMetricValue"] { color: var(--qs-ink) !important; }

            div[data-testid="stDataFrame"] {
                border: 1px solid #0a0a0a;
                border-radius: 0;
                overflow: visible;
            }

            div[data-testid="stExpander"] {
                border-color: #0a0a0a;
                border-radius: 0;
                background: rgba(255,255,255,0.82);
            }

            .stButton button, .stDownloadButton button {
                border-radius: 0;
                border: 1px solid #0a0a0a;
                font-weight: 950;
                letter-spacing: 0.02em;
                text-transform: uppercase;
                transition: transform 150ms ease, box-shadow 150ms ease, background 150ms ease;
            }

            .stButton button:hover, .stDownloadButton button:hover {
                color: #ffffff;
                background: var(--qs-red);
                box-shadow: 5px 5px 0 #0a0a0a;
                transform: translate(-2px, -2px);
            }

            hr { border-color: var(--qs-border); }
            footer { visibility: hidden; }

            @keyframes qs-enter {
                from { opacity: 0; transform: translateY(12px); }
                to { opacity: 1; transform: translateY(0); }
            }

            @keyframes qs-rise {
                from { opacity: 0; transform: translateY(8px); }
                to { opacity: 1; transform: translateY(0); }
            }

            @keyframes qs-drift {
                from { background-position: 0 0, 0 0; }
                to { background-position: 32px 32px, 32px 32px; }
            }

            @keyframes qs-field-drift {
                from { transform: translate3d(0, 0, 0) rotate(0deg); }
                to { transform: translate3d(2%, -2%, 0) rotate(1deg); }
            }

            @keyframes qs-scan {
                from { transform: translateY(0); }
                to { transform: translateY(100vh); }
            }

            @keyframes qs-orbit {
                from { transform: rotate(-28deg) skewX(-12deg); }
                to { transform: rotate(332deg) skewX(-12deg); }
            }

            @keyframes qs-node-pulse {
                0%, 100% { opacity: 0.42; transform: scale(0.8); }
                50% { opacity: 1; transform: scale(1.5); }
            }

            @keyframes qs-telemetry {
                from { opacity: 0.18; transform: translateY(0) rotate(-90deg); }
                to { opacity: 0.58; transform: translateY(-14px) rotate(-90deg); }
            }

            @keyframes qs-flow-pulse {
                0%, 100% { opacity: 0.35; transform: translateX(0); }
                50% { opacity: 1; transform: translateX(12px); }
            }

            @keyframes qs-marquee {
                from { transform: translateX(0); }
                to { transform: translateX(-50%); }
            }

            @media (prefers-reduced-motion: reduce) {
                *, *::before, *::after {
                    scroll-behavior: auto !important;
                    transition-duration: 0.01ms !important;
                    animation-duration: 0.01ms !important;
                    animation-iteration-count: 1 !important;
                }
            }

            @media (max-width: 900px) {
                .qs-flow-map { grid-template-columns: repeat(2, minmax(0, 1fr)); }
                .qs-flow-step:nth-child(2) { border-right: 0; }
                .qs-flow-step:nth-child(-n+2) { border-bottom: 1px solid #080808; }
                .qs-flow-step:nth-child(2)::after { display: none; }
            }

            @media (max-width: 620px) {
                .qs-flow-map { grid-template-columns: 1fr; }
                .qs-flow-step { border-right: 0; border-bottom: 1px solid #080808; }
                .qs-flow-step:last-child { border-bottom: 0; }
                .qs-flow-step::after { display: none !important; }
                .qs-page-header { padding: 22px 20px 24px; box-shadow: 6px 6px 0 var(--qs-red); }
                .qs-page-header h1 { font-size: 1.55rem; }
            }

            /* Additive flow-state layer: preserves the redline palette while
               giving related surfaces one continuous, glass-like environment. */
            .stApp {
                background-image:
                    radial-gradient(circle at 12% 8%, rgba(255, 16, 24, 0.09), transparent 25%),
                    radial-gradient(circle at 88% 84%, rgba(255, 255, 255, 0.5), transparent 28%),
                    linear-gradient(var(--qs-grid) 1px, transparent 1px),
                    linear-gradient(90deg, var(--qs-grid) 1px, transparent 1px);
                background-size: auto, auto, 48px 48px, 48px 48px;
                background-attachment: fixed;
            }

            .main .block-container {
                position: relative;
                max-width: 1480px;
                padding-top: 2.25rem;
                padding-bottom: 3.5rem;
            }

            /* Keep the Streamlit shell viewport-bounded so its content can scroll. */
            [data-testid="stAppViewContainer"] {
                height: 100vh;
                max-height: 100vh;
                overflow: hidden;
            }

            [data-testid="stAppViewContainer"] > .main {
                height: 100%;
                min-height: 0;
                overflow-y: auto;
                overscroll-behavior-y: contain;
            }

            [data-testid="stSidebar"] {
                height: 100%;
                min-height: 0;
            }

            /* Q-Shield renders its own styled links; hide Streamlit's duplicate list. */
            [data-testid="stSidebarNav"] {
                display: none;
            }

            [data-testid="stSidebar"] > div:first-child {
                height: 100%;
                overflow-y: auto;
                overscroll-behavior-y: contain;
            }

            /* Tab content needs a real inner gutter; Streamlit's default panel has none. */
            div[data-testid="stTabs"] [role="tabpanel"] {
                box-sizing: border-box;
                min-width: 0;
                padding: 16px clamp(14px, 2.5vw, 24px) 22px;
            }

            @media (max-width: 760px) {
                div[data-testid="stTabs"] [role="tablist"] { flex-wrap: wrap; }
                div[data-testid="stTabs"] [role="tab"] {
                    max-width: 100%;
                    white-space: normal;
                    text-align: center;
                }
            }

            .qs-cyber-background { opacity: 0.42; }

            .qs-cyber-background::before {
                background:
                    radial-gradient(circle at 16% 27%, rgba(255,16,24,0.15), transparent 18%),
                    radial-gradient(circle at 83% 72%, rgba(255,255,255,0.32), transparent 22%),
                    repeating-linear-gradient(135deg, transparent 0 62px, rgba(0,0,0,0.045) 63px 64px);
                filter: blur(0.2px);
            }

            .qs-floating-icon {
                position: absolute;
                display: grid;
                place-items: center;
                width: 44px;
                height: 44px;
                border: 1px solid rgba(8, 8, 8, 0.22);
                border-radius: 14px;
                color: rgba(255, 16, 24, 0.72);
                background: rgba(255, 255, 255, 0.24);
                box-shadow: 0 10px 24px rgba(8, 8, 8, 0.08), inset 0 1px 0 rgba(255,255,255,0.48);
                backdrop-filter: blur(10px);
                -webkit-backdrop-filter: blur(10px);
                font-size: 1.15rem;
                font-weight: 800;
                text-shadow: 0 0 16px rgba(255, 16, 24, 0.22);
                animation: qs-gentle-float 6s ease-in-out infinite;
            }

            .qs-float-shield { left: 15%; top: 17%; animation-delay: -1.2s; }
            .qs-float-lock { right: 15%; top: 25%; animation-delay: -3.7s; }
            .qs-float-key { left: 7%; bottom: 22%; animation-delay: -2.6s; }
            .qs-float-network { right: 8%; bottom: 18%; animation-delay: -4.3s; }
            .qs-float-quantum { left: 46%; top: 11%; animation-delay: -0.8s; }
            .qs-float-audit { right: 33%; bottom: 10%; animation-delay: -5.1s; }

            .qs-flow-map,
            .qs-marquee,
            .qs-card,
            [data-testid="stMetric"],
            div[data-testid="stDataFrame"],
            div[data-testid="stExpander"],
            div[data-testid="stTabs"] {
                position: relative;
                isolation: isolate;
            }

            .qs-flow-map,
            .qs-card,
            [data-testid="stMetric"],
            div[data-testid="stDataFrame"],
            div[data-testid="stExpander"],
            div[data-testid="stTabs"] {
                border-color: rgba(8, 8, 8, 0.58);
                background: linear-gradient(135deg, rgba(255,255,255,0.76), rgba(255,255,255,0.43));
                box-shadow: 0 18px 42px rgba(28, 17, 28, 0.08), inset 0 1px 0 rgba(255,255,255,0.62);
                backdrop-filter: blur(14px);
                -webkit-backdrop-filter: blur(14px);
            }

            .qs-flow-map::before,
            .qs-card::before,
            [data-testid="stMetric"]::before,
            div[data-testid="stExpander"]::before,
            div[data-testid="stTabs"]::before {
                content: "";
                position: absolute;
                inset: 0;
                z-index: -1;
                border-radius: inherit;
                background: linear-gradient(115deg, rgba(255,255,255,0.26), transparent 32%, rgba(255,16,24,0.035));
                pointer-events: none;
            }

            .qs-flow-step {
                background: rgba(255,255,255,0.18);
                border-right-color: rgba(8,8,8,0.42);
            }

            .qs-flow-step:hover {
                background: rgba(8,8,8,0.94);
                box-shadow: inset 0 1px 0 rgba(255,255,255,0.12);
            }

            .qs-page-header {
                border-color: rgba(8, 8, 8, 0.9);
                background: linear-gradient(120deg, rgba(8,8,8,0.9), rgba(23,15,18,0.78));
                box-shadow: 12px 12px 0 rgba(255,16,24,0.92), 0 20px 46px rgba(23, 7, 11, 0.15);
                backdrop-filter: blur(18px) saturate(1.12);
                -webkit-backdrop-filter: blur(18px) saturate(1.12);
            }

            .qs-page-header::before {
                content: "";
                position: absolute;
                inset: 1px;
                border: 1px solid rgba(255,255,255,0.12);
                border-radius: inherit;
                pointer-events: none;
            }

            .qs-card:hover,
            [data-testid="stMetric"]:hover {
                border-color: rgba(255,16,24,0.78);
                box-shadow: 0 22px 48px rgba(28, 17, 28, 0.12), 8px 8px 0 rgba(255,16,24,0.78);
                transform: translate(-2px, -4px);
            }

            .qs-callout {
                border-color: rgba(8,8,8,0.55);
                background: rgba(255,255,255,0.62);
                box-shadow: inset 0 1px 0 rgba(255,255,255,0.62);
                backdrop-filter: blur(10px);
                -webkit-backdrop-filter: blur(10px);
            }

            [data-testid="stSidebar"] {
                background: linear-gradient(165deg, rgba(5,5,5,0.98), rgba(18,8,10,0.96));
                box-shadow: 16px 0 42px rgba(8, 8, 8, 0.1);
            }

            [data-testid="stSidebar"] .stButton button,
            [data-testid="stSidebar"] a {
                background: linear-gradient(135deg, rgba(255,255,255,0.1), rgba(255,255,255,0.04));
                border-color: rgba(255,255,255,0.28);
                box-shadow: inset 0 1px 0 rgba(255,255,255,0.14), 0 8px 22px rgba(0,0,0,0.18);
                backdrop-filter: blur(12px) saturate(1.15);
                -webkit-backdrop-filter: blur(12px) saturate(1.15);
            }

            [data-testid="stSidebar"] a:hover {
                background: rgba(255,16,24,0.2);
                box-shadow: inset 0 0 0 1px rgba(255,255,255,0.16), 0 0 18px rgba(255,16,24,0.08);
            }

            [data-baseweb="input"] > div,
            [data-baseweb="select"] > div,
            textarea,
            [data-testid="stFileUploaderDropzone"] {
                border: 1px solid rgba(8,8,8,0.46) !important;
                border-radius: 12px !important;
                background: rgba(255,255,255,0.62) !important;
                box-shadow: inset 0 1px 0 rgba(255,255,255,0.6);
                transition: border-color 180ms ease, box-shadow 180ms ease, background 180ms ease;
            }

            [data-baseweb="input"] > div:focus-within,
            [data-baseweb="select"] > div:focus-within,
            textarea:focus,
            [data-testid="stFileUploaderDropzone"]:focus-within {
                border-color: var(--qs-red) !important;
                background: rgba(255,255,255,0.82) !important;
                box-shadow: 0 0 0 3px rgba(255,16,24,0.14), inset 0 1px 0 rgba(255,255,255,0.72);
            }

            .stButton button:focus-visible,
            .stDownloadButton button:focus-visible,
            [data-baseweb="select"]:focus-within,
            input:focus-visible,
            textarea:focus-visible,
            button:focus-visible,
            a:focus-visible {
                outline: 3px solid rgba(255,16,24,0.38) !important;
                outline-offset: 3px !important;
            }

            div[data-testid="stDataFrame"] {
                background: rgba(255,255,255,0.7);
            }

            div[data-testid="stExpander"] summary:hover {
                background: rgba(255,16,24,0.06);
            }

            [data-testid="stAlert"] {
                border-radius: 12px;
                border-left-width: 4px;
                box-shadow: 0 12px 26px rgba(28,17,28,0.08), inset 0 1px 0 rgba(255,255,255,0.45);
                backdrop-filter: blur(10px);
                -webkit-backdrop-filter: blur(10px);
            }

            .stProgress > div > div > div {
                background: linear-gradient(90deg, var(--qs-red-dark), var(--qs-red));
            }

            @keyframes qs-gentle-float {
                0%, 100% { transform: translate3d(0, 0, 0) rotate(0deg); }
                50% { transform: translate3d(0, -7px, 0) rotate(2deg); }
            }

            @media (max-width: 900px) {
                .qs-floating-icon { opacity: 0.55; transform: scale(0.82); }
                .qs-float-quantum,
                .qs-float-audit { display: none; }
            }

            @media (max-width: 620px) {
                .main .block-container { padding-top: 1.25rem; }
                .qs-floating-icon { display: none; }
                .qs-page-header { box-shadow: 7px 7px 0 rgba(255,16,24,0.92); }
            }

            /* Refined operations-console surfaces and reduced ambient motion. */
            :root { color-scheme: light; }

            body, .stApp, [data-testid="stAppViewContainer"] {
                color: var(--qs-ink);
                font-family: Inter, "Aptos", "Segoe UI", sans-serif;
            }

            h1, h2, h3, h4 {
                color: var(--qs-ink);
                font-weight: 800;
                text-transform: uppercase;
            }

            h2, h3, h4 { letter-spacing: 0.015em; }

            .qs-page-header {
                border-radius: 18px;
                box-shadow: 0 18px 42px rgba(18, 10, 14, 0.14), 5px 5px 0 rgba(255,16,24,0.88);
            }

            .qs-page-header::after { border-radius: inherit; }

            .qs-card,
            [data-testid="stMetric"],
            div[data-testid="stDataFrame"],
            div[data-testid="stExpander"],
            div[data-testid="stTabs"],
            .phase-card,
            .priority-item {
                border: 1px solid rgba(255, 255, 255, 0.72);
                border-radius: 16px;
                background: linear-gradient(135deg, rgba(255,255,255,0.34), rgba(255,255,255,0.18) 66%, rgba(255,16,24,0.075));
                box-shadow: 0 18px 44px rgba(25, 18, 25, 0.12), inset 0 1px 0 rgba(255,255,255,0.98), inset 0 -1px 0 rgba(255,16,24,0.16);
                backdrop-filter: blur(30px) saturate(1.35);
                -webkit-backdrop-filter: blur(30px) saturate(1.35);
            }

            .qs-card { padding: 20px; }
            [data-testid="stMetric"] { border-top: 2px solid rgba(255,16,24,0.72); }
            [data-testid="stMetricValue"] { font-variant-numeric: tabular-nums; }
            .qs-card-value { font-variant-numeric: tabular-nums; }

            div[data-testid="stExpander"] { overflow: visible; }
            div[data-testid="stDataFrame"] { overflow: visible; }

            .phase-card { padding: 18px; margin: 10px 0; }
            .phase-number { background: var(--qs-red); border-radius: 9px; }

            .priority-item {
                padding: 14px 16px;
                margin: 10px 0;
                border-left: 4px solid var(--qs-red);
            }
            .priority-item-high { border-left-color: #080808; }
            .priority-item-medium { border-left-color: #777; }

            .stButton button,
            .stDownloadButton button {
                min-height: 2.6rem;
                border-radius: 10px;
                border-color: rgba(8,8,8,0.2);
                background: rgba(255,255,255,0.76);
            }

            .stButton button[kind="primary"],
            .stDownloadButton button[kind="primary"] {
                color: #fff;
                border-color: var(--qs-red);
                background: var(--qs-red);
            }

            [data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
                color: rgba(255,255,255,0.68);
            }

            /* Ambient decoration stays static so controls and content remain the focus. */
            .qs-cyber-background::before,
            .qs-cyber-background::after,
            .qs-cyber-orbit,
            .qs-cyber-node,
            .qs-cyber-telemetry,
            .qs-floating-icon,
            .qs-marquee-track,
            .qs-flow-step:not(:last-child)::after {
                animation: none !important;
            }

            .qs-floating-icon { display: none; }

            @media (prefers-reduced-motion: reduce) {
                *, *::before, *::after {
                    scroll-behavior: auto !important;
                    transition-duration: 0.01ms !important;
                    animation-duration: 0.01ms !important;
                    animation-iteration-count: 1 !important;
                }
            }

            @media (max-width: 760px) {
                .main .block-container { padding-inline: 1rem; }
                .qs-page-header { padding: 22px 20px 24px; }
                .qs-marquee-item { min-width: 190px; }
            }

            /* Clear, quiet surfaces keep assessment data easy to scan. */
            .stApp {
                background: #f5f6f8;
                background-image: none;
            }

            .qs-cyber-background { display: none; }

            .main .block-container {
                max-width: 1440px;
                padding-top: 2rem;
                padding-bottom: 3rem;
            }

            h1, h2, h3, h4 { text-transform: none; letter-spacing: normal; }

            .qs-page-header {
                margin-bottom: 1.75rem;
                padding: 1.75rem 2rem;
                border: 1px solid #20242b;
                border-radius: 14px;
                background: #20242b;
                box-shadow: none;
                animation: none;
            }

            .qs-page-header::after { display: none; }
            .qs-eyebrow { letter-spacing: 0.1em; }
            .qs-page-header h1 { font-size: clamp(1.6rem, 2.5vw, 2.1rem); letter-spacing: -0.02em; text-transform: none; }
            .qs-page-header p { color: #d4d8df; }

            .qs-card,
            [data-testid="stMetric"],
            div[data-testid="stDataFrame"],
            div[data-testid="stExpander"],
            div[data-testid="stTabs"],
            .phase-card,
            .priority-item {
                border: 1px solid #e1e4e8;
                border-radius: 12px;
                background: #ffffff;
                box-shadow: 0 1px 3px rgba(16, 24, 40, 0.06);
                backdrop-filter: none;
                -webkit-backdrop-filter: none;
                animation: none;
            }

            .qs-card { padding: 1.1rem; }
            .qs-card:hover,
            [data-testid="stMetric"]:hover { transform: none; box-shadow: 0 1px 3px rgba(16, 24, 40, 0.06); }
            [data-testid="stMetric"] { border-top: 1px solid #e1e4e8; }
            [data-testid="stMetricLabel"] { color: #596273 !important; }
            [data-testid="stMetricValue"] { font-size: 1.7rem; }

            .stButton button,
            .stDownloadButton button {
                min-height: 2.6rem;
                border: 1px solid #c9ced6;
                border-radius: 8px;
                background: #ffffff;
                color: #20242b;
                font-weight: 650;
                letter-spacing: normal;
                text-transform: none;
                box-shadow: none;
                transition: background 150ms ease, border-color 150ms ease;
            }

            .stButton button:hover,
            .stDownloadButton button:hover {
                border-color: #aeb5c0;
                background: #f0f2f5;
                color: #20242b;
                box-shadow: none;
                transform: none;
            }

            .stButton button[kind="primary"],
            .stDownloadButton button[kind="primary"] {
                border-color: #c51f32;
                background: #c51f32;
                color: #ffffff;
            }

            .stButton button[kind="primary"]:hover,
            .stDownloadButton button[kind="primary"]:hover {
                border-color: #a71929;
                background: #a71929;
                color: #ffffff;
            }

            button:focus-visible,
            a:focus-visible,
            input:focus-visible,
            textarea:focus-visible,
            [role="combobox"]:focus-visible {
                outline: 3px solid rgba(197, 31, 50, 0.42);
                outline-offset: 2px;
            }

            [data-testid="stSidebar"] { border-right: 1px solid #30343b; }
            [data-testid="stSidebar"] a { transition: background 120ms ease, border-color 120ms ease; }
            [data-testid="stSidebar"] a:hover { transform: none; }
            [data-testid="stSidebar"] a[aria-current="page"] {
                border-left-color: var(--qs-red);
                background: rgba(255, 255, 255, 0.1);
            }

            .qs-flow-step,
            .qs-flow-step:hover { transition: none; transform: none; }

            @media (max-width: 760px) {
                .main .block-container { padding-top: 1rem; padding-inline: 1rem; }
                .qs-page-header { padding: 1.25rem; }
                [data-testid="stMetric"] { padding: 0.85rem; }
            }
        </style>
        """,
        unsafe_allow_html=True,
    )
    render_cyber_background()


def render_sidebar(active_page: str = "Command Center") -> None:
    """Render the consistent application shell and page navigation."""
    with st.sidebar:
        st.markdown(
            """
            <div class="qs-brand">
                <div class="qs-brand-mark">Q</div>
                <div>
                    <div class="qs-brand-name">Q-Shield</div>
                    <div class="qs-brand-subtitle">PQC security operations</div>
                </div>
            </div>
            <div class="qs-ops-strip"><span>N1</span><span>N2</span><span>N3</span><span>N4</span><span>N5</span></div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown('<div class="qs-nav-label">Workspace</div>', unsafe_allow_html=True)
        st.caption("Local prototype · decision-support estimates")
        st.markdown('<div class="qs-nav-label">Navigate</div>', unsafe_allow_html=True)
        for page_path, label, icon, _description in NAV_ITEMS:
            prefix = "▸" if label == active_page else "·"
            try:
                st.page_link(page_path, label=f"{prefix}  {icon}  {label}")
            except StreamlitAPIException:
                # AppTest can execute a page as a standalone script, where
                # Streamlit resolves page links relative to that page folder.
                # Keep the page renderable in that mode without affecting the
                # normal multipage navigation shell.
                st.markdown(f"{prefix}  {icon}  {label}")
        st.markdown("---")
        st.markdown('<div class="qs-nav-label">Design principles</div>', unsafe_allow_html=True)
        st.caption("Evidence first · human review · progressive disclosure")
        st.caption("Use synthetic or sanitized data in public demos.")
        st.markdown("---")
        st.caption("v0.1 · Track: Cybersecurity")


def render_page_header(eyebrow: str, title: str, description: str) -> None:
    """Render a consistent page header."""
    st.markdown(
        f"""
        <div class="qs-page-header">
            <div class="qs-eyebrow">{escape(eyebrow)}</div>
            <h1>{escape(title)}</h1>
            <p>{escape(description)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_metric_card(label: str, value: str, help_text: str = "") -> None:
    """Render a metric card that is visually consistent with the dashboard."""
    help_html = f'<div class="qs-card-help">{escape(help_text)}</div>' if help_text else ""
    st.markdown(
        f"""
        <div class="qs-card">
            <div class="qs-card-title">{escape(label)}</div>
            <div class="qs-card-value">{escape(value)}</div>
            {help_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def risk_class(level: str) -> str:
    """Return the CSS class for a risk level."""
    return {
        "Critical": "qs-risk-critical",
        "High": "qs-risk-high",
        "Medium": "qs-risk-medium",
        "Low": "qs-risk-low",
    }.get(level, "qs-risk-unknown")


def render_risk_pill(level: str, score: Optional[float] = None) -> None:
    """Render an accessible risk pill with text and optional score."""
    suffix = f" · {score:.0f}/100" if score is not None else ""
    label = f"{level}{suffix}"
    st.markdown(
        f'<span class="qs-risk-pill {risk_class(level)}">{escape(label)}</span>',
        unsafe_allow_html=True,
    )


def render_action_list(actions: Iterable[tuple[str, str]]) -> None:
    """Render numbered recommended actions."""
    rows = []
    for index, (title, meta) in enumerate(actions, start=1):
        rows.append(
            f"""
            <div class="qs-action-item">
                <div class="qs-action-index">{index}</div>
                <div>
                    <div class="qs-action-title">{escape(title)}</div>
                    <div class="qs-action-meta">{escape(meta)}</div>
                </div>
            </div>
            """
        )
    st.markdown("".join(rows) or '<div class="qs-muted">No actions currently queued.</div>', unsafe_allow_html=True)


def section_title(title: str, caption: str = "") -> None:
    """Render a compact section heading."""
    st.markdown(f'<div class="qs-section-title">{escape(title)}</div>', unsafe_allow_html=True)
    if caption:
        st.markdown(f'<div class="qs-section-caption">{escape(caption)}</div>', unsafe_allow_html=True)
