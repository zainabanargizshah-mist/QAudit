"""
Q-Shield — Risk Assessment Page

Displays detection findings and explainable risk scores for all assets.
Allows running/re-running the assessment engine.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from qshield.database import Database
from qshield.detection import analyze_asset
from qshield.risk_engine import compute_risk_score
from qshield.models import DEFAULT_SCORING_CONFIG


st.set_page_config(
    page_title="Risk Assessment — Q-Shield",
    page_icon="⚡",
    layout="wide",
)

st.markdown("""
<style>
    [data-testid="stSidebar"] { background-color: #1a1f36; }
    [data-testid="stSidebar"] * { color: #e0e4ef !important; }
    .demo-badge {
        display: inline-block; background-color: #f59e0b;
        color: #1a1f36 !important; padding: 3px 10px; border-radius: 4px;
        font-size: 0.7rem; font-weight: 700;
    }
    .score-critical { background: #fef2f2; border-left: 4px solid #dc2626; padding: 12px; border-radius: 0 8px 8px 0; margin: 8px 0; }
    .score-high { background: #fff7ed; border-left: 4px solid #ea580c; padding: 12px; border-radius: 0 8px 8px 0; margin: 8px 0; }
    .score-medium { background: #fffbeb; border-left: 4px solid #d97706; padding: 12px; border-radius: 0 8px 8px 0; margin: 8px 0; }
    .score-low { background: #f0fdf4; border-left: 4px solid #16a34a; padding: 12px; border-radius: 0 8px 8px 0; margin: 8px 0; }
    footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_database():
    return Database()

db = get_database()

with st.sidebar:
    st.markdown("## 🛡️ Q-Shield")
    st.markdown("---")
    st.page_link("app.py", label="📊 Overview")
    st.page_link("pages/1_Asset_Inventory.py", label="📋 Asset Inventory")
    st.page_link("pages/2_Risk_Assessment.py", label="⚡ Risk Assessment")
    st.page_link("pages/3_Migration_Planner.py", label="🗺️ Migration Planner")
    st.page_link("pages/4_Reports.py", label="📄 Reports")
    st.page_link("pages/5_Methodology.py", label="📚 Methodology & Standards")

# ── Header ───────────────────────────────────────────────────────────
st.markdown("# ⚡ Risk Assessment")
st.markdown(
    "Deterministic cryptographic detection and transparent risk scoring. "
    "Scores are decision-support estimates, not certified security ratings."
)

assets = db.get_all_assets()

if not assets:
    st.info("📭 No assets loaded. Use **Asset Inventory** to load demo data or upload a CSV/JSON file.")
    st.stop()

# ── Run Assessment ───────────────────────────────────────────────────
col_run, col_info = st.columns([1, 3])
with col_run:
    if st.button("🔄 Run Assessment", type="primary", use_container_width=True):
        progress = st.progress(0, text="Analyzing assets...")
        for i, asset in enumerate(assets):
            finding = analyze_asset(asset)
            score = compute_risk_score(asset, finding)
            db.save_assessment(asset["asset_id"], finding.to_dict(), score.to_dict())
            progress.progress((i + 1) / len(assets), text=f"Analyzing {asset['asset_name']}...")
        db.log_activity("Assessment completed", f"Assessed {len(assets)} assets", len(assets))
        progress.empty()
        st.success(f"✅ Assessment complete — {len(assets)} assets analyzed")
        st.rerun()

with col_info:
    st.caption(
        "The detection engine classifies algorithms using deterministic rules. "
        "Risk scores combine cryptographic exposure, data sensitivity, "
        "business criticality, internet exposure, dependencies, and evidence confidence."
    )

st.markdown("---")

# ── Results ──────────────────────────────────────────────────────────
assessments = db.get_all_assessments()
if not assessments:
    st.info("⏳ No assessment results yet. Click **Run Assessment** above.")
    st.stop()

# Summary chart
risk_counts = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
for a in assessments:
    level = a.get("risk_level", "Unknown")
    if level in risk_counts:
        risk_counts[level] += 1

mcol1, mcol2, mcol3, mcol4 = st.columns(4)
mcol1.metric("Critical", risk_counts["Critical"])
mcol2.metric("High", risk_counts["High"])
mcol3.metric("Medium", risk_counts["Medium"])
mcol4.metric("Low", risk_counts["Low"])

st.markdown("---")

# ── Filters ──────────────────────────────────────────────────────────
fcol1, fcol2 = st.columns(2)
with fcol1:
    risk_filter = st.multiselect(
        "Filter by Risk Level",
        ["Critical", "High", "Medium", "Low"],
        default=[],
    )
with fcol2:
    vuln_filter = st.selectbox(
        "Vulnerability Filter",
        ["All", "Quantum Vulnerable Only", "PQC Only", "Needs Review"],
    )

# Build asset map
asset_map = {a["asset_id"]: a for a in assets}

# Filter assessments
filtered = assessments
if risk_filter:
    filtered = [a for a in filtered if a.get("risk_level") in risk_filter]
if vuln_filter == "Quantum Vulnerable Only":
    filtered = [a for a in filtered if a.get("is_quantum_vulnerable")]
elif vuln_filter == "PQC Only":
    filtered = [a for a in filtered if a.get("is_pqc")]
elif vuln_filter == "Needs Review":
    filtered = [a for a in filtered if a.get("needs_review")]

st.markdown(f"### Findings ({len(filtered)} assets)")

# ── Detailed Findings ────────────────────────────────────────────────
for assessment in filtered:
    aid = assessment["asset_id"]
    asset = asset_map.get(aid, {})
    finding = assessment.get("finding_json", {})
    score_data = assessment.get("score_json", {})
    risk_level = assessment.get("risk_level", "Unknown")
    risk_score = assessment.get("risk_score", 0)

    css_class = f"score-{risk_level.lower()}" if risk_level.lower() in ("critical", "high", "medium", "low") else "score-medium"

    with st.expander(
        f"{'🔴' if risk_level == 'Critical' else '🟠' if risk_level == 'High' else '🟡' if risk_level == 'Medium' else '🟢'} "
        f"{asset.get('asset_name', aid)} — {risk_score}/100 ({risk_level})"
        f"{'  ⚠️ NEEDS REVIEW' if assessment.get('needs_review') else ''}",
        expanded=(risk_level in ("Critical", "High")),
    ):
        dcol1, dcol2 = st.columns([2, 1])

        with dcol1:
            st.markdown(f"**Asset:** {asset.get('asset_name', aid)} (`{aid}`)")
            st.markdown(f"**Algorithm:** `{asset.get('cryptographic_algorithm', 'N/A')}`")
            st.markdown(f"**Purpose:** {asset.get('cryptographic_purpose', 'N/A')}")
            st.markdown(f"**Protocol:** {asset.get('protocol', 'N/A')}")
            st.markdown(f"**Environment:** {asset.get('environment', 'N/A')}")

            st.markdown("---")

            # Finding details
            st.markdown("##### Detection Finding")
            st.markdown(f"**Rule:** `{finding.get('rule_id', 'N/A')}`")
            st.markdown(f"**Vulnerability Type:** {finding.get('vulnerability_type', 'N/A')}")
            st.markdown(f"**Confidence:** {finding.get('confidence', 'N/A')}")

            vuln_status = []
            if finding.get("is_quantum_vulnerable"):
                vuln_status.append("🔴 Quantum Vulnerable")
            if finding.get("is_pqc"):
                vuln_status.append("🟢 PQC Algorithm")
            if finding.get("needs_review"):
                vuln_status.append("⚠️ Needs Review")
            if not vuln_status:
                vuln_status.append("🟢 Not Quantum Vulnerable")
            st.markdown(f"**Status:** {' · '.join(vuln_status)}")

            st.markdown(f"**Evidence:** {finding.get('evidence', 'N/A')}")

            if finding.get("recommendation"):
                st.info(f"💡 **Recommendation:** {finding['recommendation']}")

        with dcol2:
            st.markdown("##### Risk Score Breakdown")
            st.markdown(f"### {risk_score}/100")
            st.markdown(f"**Level:** {risk_level}")

            breakdown = score_data.get("breakdown", {})
            if breakdown:
                for factor, info in breakdown.items():
                    label = factor.replace("_", " ").title()
                    weighted = info.get("weighted_contribution", 0)
                    raw = info.get("raw_score", 0)
                    st.markdown(f"**{label}:** {weighted:.1f} pts ({raw:.0%})")

            st.markdown("---")
            st.markdown("**Top Factors:**")
            for tf in score_data.get("top_factors", [])[:3]:
                st.markdown(f"- {tf}")

            st.markdown("---")
            st.markdown("**Suggested Actions:**")
            for action in score_data.get("suggested_actions", []):
                st.markdown(f"- {action}")

            if score_data.get("needs_review"):
                st.warning("⚠️ Insufficient evidence — score includes uncertainty penalty.")

# ── Score Distribution Chart ─────────────────────────────────────────
st.markdown("---")
st.markdown("### Score Distribution")

score_data_list = []
for a in assessments:
    aid = a["asset_id"]
    asset = asset_map.get(aid, {})
    score_data_list.append({
        "Asset": asset.get("asset_name", aid),
        "Score": a.get("risk_score", 0),
        "Risk Level": a.get("risk_level", "Unknown"),
        "Vulnerable": "Yes" if a.get("is_quantum_vulnerable") else "No",
    })

if score_data_list:
    score_df = pd.DataFrame(score_data_list)
    score_df = score_df.sort_values("Score", ascending=True)

    color_map = {
        "Critical": "#dc2626", "High": "#ea580c",
        "Medium": "#d97706", "Low": "#16a34a", "Unknown": "#94a3b8",
    }

    fig = px.bar(
        score_df, x="Score", y="Asset", color="Risk Level",
        orientation="h", color_discrete_map=color_map,
        text="Score",
    )
    fig.update_layout(
        height=max(300, len(score_data_list) * 35),
        margin=dict(l=20, r=20, t=20, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis_title="Risk Score (0-100)",
        yaxis_title="",
    )
    fig.update_traces(textposition="outside")
    # Add risk band lines
    fig.add_vline(x=80, line_dash="dot", line_color="#dc2626", annotation_text="Critical", annotation_position="top")
    fig.add_vline(x=60, line_dash="dot", line_color="#ea580c", annotation_text="High")
    fig.add_vline(x=35, line_dash="dot", line_color="#d97706", annotation_text="Medium")

    st.plotly_chart(fig, use_container_width=True)
