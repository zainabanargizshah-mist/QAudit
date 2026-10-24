"""
Q-Shield — Command Center

The dashboard is intentionally action-oriented: establish posture, surface
the next decisions, then let users drill into evidence when they need it.
"""

from __future__ import annotations

from datetime import datetime

import pandas as pd
import plotly.express as px
import streamlit as st

from qshield import __app_subtitle__, __version__
from qshield.database import Database
from qshield.detection import analyze_asset
from qshield.inventory import import_assets_to_db, load_demo_assets
from qshield.risk_engine import compute_risk_score
from qshield.ui import (
    inject_styles,
    render_action_list,
    render_flow_map,
    render_metric_card,
    render_page_header,
    render_sidebar,
    render_telemetry_marquee,
    section_title,
)


st.set_page_config(
    page_title="Q-Shield — Command Center",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_styles()
render_sidebar("Command Center")


@st.cache_resource
def get_database() -> Database:
    return Database()


db = get_database()


def run_assessment(database: Database) -> int:
    """Run the deterministic detection and risk scoring pipeline."""
    assets = database.get_all_assets()
    for asset in assets:
        finding = analyze_asset(asset)
        score = compute_risk_score(asset, finding)
        database.save_assessment(asset["asset_id"], finding.to_dict(), score.to_dict())
    database.log_activity("Assessment completed", f"Assessed {len(assets)} assets", len(assets))
    return len(assets)


def risk_counts(assessments: list[dict]) -> dict[str, int]:
    counts = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
    for assessment in assessments:
        level = assessment.get("risk_level", "Unknown")
        if level in counts:
            counts[level] += 1
    return counts


render_page_header(
    "Q-SHIELD COMMAND CENTER",
    "Quantum-readiness posture at a glance",
    f"{__app_subtitle__}. Start with the highest-impact decisions, then open an asset to inspect the evidence behind its score.",
)

action_col1, action_col2, action_col3 = st.columns([1.1, 1.1, 2.8])
with action_col1:
    if st.button("▶ Run assessment", type="primary", use_container_width=True):
        if db.asset_count() == 0:
            st.warning("Add or load assets before running an assessment.")
        else:
            with st.spinner("Recalculating posture and recommendations..."):
                count = run_assessment(db)
            st.success(f"Assessment complete · {count} assets analyzed")
            st.rerun()
with action_col2:
    if st.button("＋ Load demo data", use_container_width=True):
        demo = load_demo_assets()
        count = import_assets_to_db(db, demo, source="demo_dataset")
        run_assessment(db)
        st.success(f"Loaded {count} synthetic assets")
        st.rerun()
with action_col3:
    st.caption("Prototype mode · scores are decision-support estimates and require human review.")

stats = db.get_summary_stats()
assets = db.get_all_assets()
assessments = db.get_all_assessments()

render_flow_map([
    ("N1", "Observe", "Inventory the cryptographic estate."),
    ("N2", "Detect", "Classify vulnerable and PQC usage."),
    ("N3", "Prioritize", "Explain what needs attention first."),
    ("N4", "Migrate", "Move assets through a verified roadmap."),
])

if assets:
    telemetry_items = [
        ("ASSETS", str(len(assets))),
        ("VULNERABLE", str(stats["quantum_vulnerable"])),
        ("HIGH PRIORITY", str(stats["high_priority"])),
        ("PQC IN USE", str(stats["pqc_assets"])),
        ("REVIEW QUEUE", str(stats["needs_review"])),
    ]
else:
    telemetry_items = [
        ("SYSTEM", "READY"),
        ("MODE", "LOCAL PROTOTYPE"),
        ("SIGNAL", "AWAITING INVENTORY"),
        ("FLOW", "DISCOVER → VERIFY"),
    ]
render_telemetry_marquee(telemetry_items)

if not assets:
    section_title("Start with a clean assessment workspace", "Use synthetic data to explore the workflow, or import a sanitized inventory from the Inventory page.")
    empty_col1, empty_col2 = st.columns(2)
    with empty_col1:
        st.markdown(
            """
            <div class="qs-card">
                <div class="qs-card-title">Guided workflow</div>
                <div class="qs-card-value">Discover → Prioritize → Migrate</div>
                <p class="qs-muted">Q-Shield classifies algorithms, explains risk, and turns findings into a migration queue.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with empty_col2:
        st.markdown(
            '<div class="qs-callout"><strong>Safe demo reminder</strong><br>Do not upload confidential production inventories to a public demo. Use synthetic or sanitized data only.</div>',
            unsafe_allow_html=True,
        )
        if st.button("Open Inventory", type="primary", use_container_width=True):
            st.switch_page("pages/1_Asset_Inventory.py")
    st.stop()


section_title("Posture at a glance", "Every card is a decision shortcut. Open the Risk Queue to filter the underlying assets.")
metric_cols = st.columns(4)
with metric_cols[0]:
    exposure_pct = round((stats["quantum_vulnerable"] / stats["total_assets"]) * 100) if stats["total_assets"] else 0
    render_metric_card("Quantum exposure", f"{stats['quantum_vulnerable']} assets", f"{exposure_pct}% of inventory")
with metric_cols[1]:
    render_metric_card("Critical / high", str(stats["high_priority"]), "Assets needing migration attention")
with metric_cols[2]:
    completed = sum(1 for asset in assets if asset.get("migration_status") == "Completed")
    progress_pct = round((completed / len(assets)) * 100) if assets else 0
    render_metric_card("Migration progress", f"{progress_pct}%", f"{completed} of {len(assets)} assets completed")
with metric_cols[3]:
    render_metric_card("Needs review", str(stats["needs_review"]), "Unknown or hybrid evidence")

section_title("Decision layer", "The dashboard puts recommended actions beside the posture signal so users do not have to interpret every chart first.")
decision_col1, decision_col2 = st.columns([1.35, 1])

with decision_col1:
    st.markdown('<div class="qs-card">', unsafe_allow_html=True)
    st.markdown("**Risk posture**")
    counts = risk_counts(assessments)
    risk_df = pd.DataFrame([{"Risk level": key, "Assets": value} for key, value in counts.items()])
    fig = px.bar(
        risk_df,
        x="Risk level",
        y="Assets",
        color="Risk level",
        text="Assets",
        color_discrete_map={
            "Critical": "#c9283e",
            "High": "#d96820",
            "Medium": "#b87909",
            "Low": "#16845a",
        },
    )
    fig.update_layout(
        showlegend=False,
        height=285,
        margin=dict(l=8, r=8, t=12, b=8),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis_title="",
        yaxis_title="Asset count",
        font=dict(color="#66758a"),
    )
    fig.update_traces(textposition="outside")
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    st.caption("Critical and High assets are the immediate migration queue.")
    st.markdown('</div>', unsafe_allow_html=True)

with decision_col2:
    st.markdown('<div class="qs-card">', unsafe_allow_html=True)
    st.markdown("**Recommended next actions**")
    asset_map = {asset["asset_id"]: asset for asset in assets}
    top = sorted(assessments, key=lambda item: item.get("risk_score", 0), reverse=True)[:3]
    actions = []
    for assessment in top:
        asset = asset_map.get(assessment.get("asset_id"), {})
        actions.append(
            (
                f"Review {asset.get('asset_name', assessment.get('asset_id', 'asset'))}",
                f"{assessment.get('risk_level', 'Unknown')} · {asset.get('cryptographic_algorithm', 'Unknown')} · {asset.get('owner') or 'Owner unassigned'}",
            )
        )
    render_action_list(actions)
    st.markdown('</div>', unsafe_allow_html=True)

section_title("Priority queue", "The highest-risk assets are shown first. Open Risk Queue for filters, evidence, and migration actions.")
priority_col1, priority_col2 = st.columns([2.6, 1])
with priority_col1:
    rows = []
    for assessment in assessments[:5]:
        asset = asset_map.get(assessment.get("asset_id"), {})
        rows.append(
            {
                "Asset": asset.get("asset_name", assessment.get("asset_id", "Unknown")),
                "Risk": f"{assessment.get('risk_level', 'Unknown')} · {assessment.get('risk_score', 0):.0f}",
                "Algorithm": asset.get("cryptographic_algorithm", "Unknown"),
                "Owner": asset.get("owner") or "Unassigned",
                "Status": asset.get("migration_status", "Not Started"),
            }
        )
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True, height=235)
with priority_col2:
    st.markdown(
        '<div class="qs-callout"><strong>Why this queue matters</strong><br>Q-Shield combines algorithm exposure, data retention, criticality, internet exposure, dependencies, and evidence confidence.</div>',
        unsafe_allow_html=True,
    )
    if st.button("Open Risk Queue", type="primary", use_container_width=True):
        st.switch_page("pages/2_Risk_Assessment.py")

section_title("Migration progress", "Status is recorded by the team; it is never inferred solely from algorithm presence.")
status_counts = {}
for asset in assets:
    status = asset.get("migration_status", "Not Started")
    status_counts[status] = status_counts.get(status, 0) + 1
status_df = pd.DataFrame([{"Status": key, "Assets": value} for key, value in status_counts.items()])
fig = px.bar(
    status_df,
    x="Status",
    y="Assets",
    color="Status",
    text="Assets",
    color_discrete_sequence=["#93a4b8", "#3b82f6", "#7357d9", "#e39a28", "#d96820", "#16845a"],
)
fig.update_layout(
    showlegend=False,
    height=250,
    margin=dict(l=8, r=8, t=12, b=8),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    xaxis_title="",
    yaxis_title="Asset count",
    font=dict(color="#66758a"),
)
fig.update_traces(textposition="outside")
st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

with st.expander("Recent activity", expanded=False):
    activity = db.get_recent_activity(limit=8)
    if not activity:
        st.info("No activity recorded yet.")
    for event in activity:
        timestamp = event.get("timestamp", "")
        try:
            timestamp = datetime.fromisoformat(timestamp).strftime("%Y-%m-%d %H:%M UTC")
        except (TypeError, ValueError):
            pass
        st.markdown(f"- **{event.get('action', '')}** — {event.get('details', '')} · `{timestamp}`")

with st.expander("Data management", expanded=False):
    st.caption(f"{len(assets)} assets are currently stored in the local SQLite database.")
    if st.button("Clear all local data", type="secondary"):
        st.session_state["confirm_clear_dashboard"] = True
    if st.session_state.get("confirm_clear_dashboard"):
        st.warning("This permanently deletes all local assets, assessments, and their history.")
        confirm_col, cancel_col = st.columns(2)
        with confirm_col:
            if st.button("Confirm clear", type="primary"):
                deleted = db.delete_all_assets()
                db.log_activity("Cleared all data", f"Deleted {deleted} assets")
                st.session_state["confirm_clear_dashboard"] = False
                st.success(f"Cleared {deleted} assets")
                st.rerun()
        with cancel_col:
            if st.button("Cancel clear"):
                st.session_state["confirm_clear_dashboard"] = False
                st.rerun()

st.caption(f"Q-Shield v{__version__} · {__app_subtitle__}")
