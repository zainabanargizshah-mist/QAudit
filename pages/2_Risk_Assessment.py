"""Q-Shield risk queue: prioritize findings, explain scores, and assign action."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from qshield.database import Database
from qshield.detection import analyze_asset
from qshield.risk_engine import compute_risk_score
from qshield.ui import inject_styles, render_flow_map, render_page_header, render_sidebar, section_title


st.set_page_config(page_title="Risk Queue — Q-Shield", page_icon="◈", layout="wide")
inject_styles()
render_sidebar("Risk Queue")


@st.cache_resource
def get_database() -> Database:
    return Database()


db = get_database()


render_page_header(
    "RISK QUEUE",
    "Turn findings into accountable action",
    "Start with the highest-risk assets, compare them in a compact queue, then open one record to see the evidence and score drivers behind its priority.",
)
render_flow_map([
    ("N1", "Observe", "Inventory the cryptographic estate."),
    ("N2", "Detect", "Classify vulnerable and PQC usage."),
    ("N3", "Prioritize", "Explain what needs attention first."),
    ("N4", "Migrate", "Move assets through a verified roadmap."),
])

assets = db.get_all_assets()
if not assets:
    st.info("No assets loaded. Start in Inventory to load demo data or import a sanitized dataset.")
    if st.button("Open Inventory", type="primary"):
        st.switch_page("pages/1_Asset_Inventory.py")
    st.stop()

action_col1, action_col2 = st.columns([1.1, 3])
with action_col1:
    if st.button("↻ Run assessment", type="primary", use_container_width=True):
        progress = st.progress(0, text="Analyzing inventory...")
        for index, asset in enumerate(assets, start=1):
            finding = analyze_asset(asset)
            score = compute_risk_score(asset, finding)
            db.save_assessment(asset["asset_id"], finding.to_dict(), score.to_dict())
            progress.progress(index / len(assets), text=f"Analyzing {asset['asset_name']}...")
        progress.empty()
        db.log_activity("Assessment completed", f"Assessed {len(assets)} assets", len(assets))
        st.success(f"Assessment complete · {len(assets)} assets analyzed")
        st.rerun()
with action_col2:
    st.caption("Detection is deterministic. Scores are estimates for migration planning, not certified security ratings.")

assessments = db.get_all_assessments()
if not assessments:
    st.info("No assessment results yet. Run the assessment to populate the priority queue.")
    st.stop()

risk_counts = {level: 0 for level in ("Critical", "High", "Medium", "Low")}
for assessment in assessments:
    if assessment.get("risk_level") in risk_counts:
        risk_counts[assessment["risk_level"]] += 1

section_title("Risk posture", "Use the summary to orient yourself, then filter the queue below.")
metric_cols = st.columns(4)
for column, level in zip(metric_cols, risk_counts):
    column.metric(level, risk_counts[level])

section_title("Filter and prioritize", "The queue is ordered by score. Filters reduce noise without hiding the evidence behind a finding.")
filter_col1, filter_col2, filter_col3 = st.columns([1.1, 1.2, 2])
with filter_col1:
    risk_filter = st.multiselect("Risk level", list(risk_counts))
with filter_col2:
    vuln_filter = st.selectbox("Finding type", ["All", "Quantum vulnerable", "PQC in use", "Needs review"])
with filter_col3:
    search = st.text_input("Search queue", placeholder="Asset name, algorithm, owner")

asset_map = {asset["asset_id"]: asset for asset in assets}
filtered = assessments
if risk_filter:
    filtered = [item for item in filtered if item.get("risk_level") in risk_filter]
if vuln_filter == "Quantum vulnerable":
    filtered = [item for item in filtered if item.get("is_quantum_vulnerable")]
elif vuln_filter == "PQC in use":
    filtered = [item for item in filtered if item.get("is_pqc")]
elif vuln_filter == "Needs review":
    filtered = [item for item in filtered if item.get("needs_review")]
if search:
    filtered = [
        item for item in filtered
        if search.lower() in " ".join(str(value).lower() for value in asset_map.get(item.get("asset_id"), {}).values())
    ]

st.caption(f"Showing {len(filtered)} of {len(assessments)} findings")
queue_rows = []
for item in filtered:
    asset = asset_map.get(item.get("asset_id"), {})
    finding = item.get("finding_json", {})
    queue_rows.append(
        {
            "Asset": asset.get("asset_name", item.get("asset_id", "Unknown")),
            "Risk": item.get("risk_level", "Unknown"),
            "Score": round(item.get("risk_score", 0)),
            "Algorithm": asset.get("cryptographic_algorithm", "Unknown"),
            "Owner": asset.get("owner") or "Unassigned",
            "Migration": asset.get("migration_status", "Not Started"),
            "Signal": "Needs review" if item.get("needs_review") else finding.get("vulnerability_type", "No quantum vulnerability detected"),
        }
    )

st.dataframe(pd.DataFrame(queue_rows), use_container_width=True, hide_index=True, height=300)

if filtered:
    selected_id = st.selectbox(
        "Open finding",
        [item["asset_id"] for item in filtered],
        format_func=lambda asset_id: f"{asset_map.get(asset_id, {}).get('asset_name', asset_id)} · {next((item.get('risk_score', 0) for item in filtered if item.get('asset_id') == asset_id), 0):.0f}/100",
    )
    selected = next(item for item in filtered if item["asset_id"] == selected_id)
    selected_asset = asset_map.get(selected_id, {})
    finding = selected.get("finding_json", {})
    score = selected.get("score_json", {})

    section_title("Finding detail", "A focused evidence drawer for the selected asset.")
    detail_col1, detail_col2 = st.columns([1.35, 1])
    with detail_col1:
        st.markdown('<div class="qs-card">', unsafe_allow_html=True)
        st.markdown(f"### {selected_asset.get('asset_name', selected_id)}")
        st.caption(f"`{selected_id}` · {selected_asset.get('owner') or 'Owner unassigned'} · {selected_asset.get('environment', 'Environment unknown')}")
        st.markdown(f"**Algorithm:** `{selected_asset.get('cryptographic_algorithm', 'N/A')}`")
        st.markdown(f"**Purpose:** {selected_asset.get('cryptographic_purpose', 'N/A')} · **Protocol:** {selected_asset.get('protocol', 'N/A')}")
        st.markdown(f"**Business criticality:** {selected_asset.get('business_criticality', 'N/A')} · **Internet exposed:** {'Yes' if selected_asset.get('internet_exposed') else 'No'}")
        st.markdown("---")
        st.markdown("**Detection finding**")
        st.markdown(f"{finding.get('vulnerability_type', 'No vulnerability classification')} · Rule `{finding.get('rule_id', 'N/A')}`")
        st.markdown(f"**Confidence:** {finding.get('confidence', 'N/A')}")
        st.markdown(f"**Evidence:** {finding.get('evidence', 'N/A')}")
        if finding.get("recommendation"):
            st.markdown(f'<div class="qs-callout"><strong>Recommended direction</strong><br>{finding["recommendation"]}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with detail_col2:
        st.markdown('<div class="qs-card">', unsafe_allow_html=True)
        st.markdown("**Explainable risk score**")
        st.markdown(f"## {selected.get('risk_score', 0):.0f}/100")
        st.caption(f"{selected.get('risk_level', 'Unknown')} priority · last assessed {selected.get('assessed_at', 'unknown')}")
        for factor, info in score.get("breakdown", {}).items():
            label = factor.replace("_", " ").title()
            weighted = info.get("weighted_contribution", 0)
            raw = info.get("raw_score", 0)
            st.progress(min(max(float(raw), 0), 1), text=f"{label} · {weighted:.1f} pts")
        st.markdown("**Top factors**")
        for factor in score.get("top_factors", [])[:3]:
            st.markdown(f"- {factor}")
        if score.get("suggested_actions"):
            st.markdown("**Suggested actions**")
            for action in score["suggested_actions"]:
                st.markdown(f"- {action}")
        if selected.get("needs_review"):
            st.warning("Manual review required. Unknown or incomplete evidence includes an uncertainty penalty.")
        if st.button("Open Migration Roadmap", type="primary", use_container_width=True):
            st.switch_page("pages/3_Migration_Planner.py")
        st.markdown('</div>', unsafe_allow_html=True)

section_title("Score distribution", "A comparison view for the entire assessment, with risk-band thresholds visible.")
score_rows = []
for item in assessments:
    asset = asset_map.get(item.get("asset_id"), {})
    score_rows.append({"Asset": asset.get("asset_name", item.get("asset_id")), "Score": item.get("risk_score", 0), "Risk": item.get("risk_level", "Unknown")})
score_df = pd.DataFrame(score_rows).sort_values("Score", ascending=True)
fig = px.bar(
    score_df,
    x="Score",
    y="Asset",
    color="Risk",
    orientation="h",
    text="Score",
    color_discrete_map={"Critical": "#c9283e", "High": "#d96820", "Medium": "#b87909", "Low": "#16845a", "Unknown": "#8b98aa"},
)
fig.update_layout(
    height=max(300, len(score_rows) * 34),
    margin=dict(l=8, r=20, t=12, b=8),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    xaxis_title="Risk score (0–100)",
    yaxis_title="",
    font=dict(color="#66758a"),
)
fig.update_traces(textposition="outside")
for threshold, label, color in [(80, "Critical", "#c9283e"), (60, "High", "#d96820"), (35, "Medium", "#b87909")]:
    fig.add_vline(x=threshold, line_dash="dot", line_color=color, annotation_text=label, annotation_position="top")
st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
