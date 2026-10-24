"""
Q-Shield — AI-Assisted Quantum-Readiness Assessment and PQC Migration Planner

Main application entry point. Configures the Streamlit app,
initializes the database, and renders the Overview dashboard.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

from qshield import __app_name__, __app_subtitle__, __version__
from qshield.database import Database
from qshield.inventory import load_demo_assets, import_assets_to_db, get_assets_dataframe
from qshield.detection import analyze_asset
from qshield.risk_engine import compute_risk_score
from qshield.models import DEFAULT_SCORING_CONFIG


# ── Page Config ──────────────────────────────────────────────────────

st.set_page_config(
    page_title="Q-Shield — Quantum-Readiness Assessment",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ───────────────────────────────────────────────────────

st.markdown("""
<style>
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #1a1f36;
    }
    [data-testid="stSidebar"] * {
        color: #e0e4ef !important;
    }
    [data-testid="stSidebar"] .stMarkdown h1,
    [data-testid="stSidebar"] .stMarkdown h2,
    [data-testid="stSidebar"] .stMarkdown h3 {
        color: #ffffff !important;
    }

    /* Metric cards */
    [data-testid="stMetric"] {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 12px 16px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    }
    [data-testid="stMetric"] label {
        color: #64748b !important;
        font-size: 0.8rem !important;
    }
    [data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: #1a1f36 !important;
        font-weight: 700 !important;
    }

    /* Header styling */
    .main-header {
        background: linear-gradient(135deg, #0e7c86 0%, #1a1f36 100%);
        padding: 20px 24px;
        border-radius: 10px;
        margin-bottom: 20px;
        color: white;
    }
    .main-header h1 {
        margin: 0;
        font-size: 1.8rem;
        font-weight: 700;
        color: white !important;
    }
    .main-header p {
        margin: 4px 0 0 0;
        opacity: 0.85;
        font-size: 0.95rem;
    }

    /* Demo badge */
    .demo-badge {
        display: inline-block;
        background-color: #f59e0b;
        color: #1a1f36 !important;
        padding: 3px 10px;
        border-radius: 4px;
        font-size: 0.7rem;
        font-weight: 700;
        letter-spacing: 0.5px;
        margin-left: 8px;
        vertical-align: middle;
    }

    /* Risk level badges */
    .risk-critical { color: #dc2626; font-weight: 700; }
    .risk-high { color: #ea580c; font-weight: 700; }
    .risk-medium { color: #d97706; font-weight: 600; }
    .risk-low { color: #16a34a; font-weight: 600; }

    /* Priority table */
    .priority-item {
        background: #fff;
        border-left: 4px solid #dc2626;
        padding: 10px 14px;
        margin-bottom: 8px;
        border-radius: 0 6px 6px 0;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
    .priority-item-high {
        border-left-color: #ea580c;
    }
    .priority-item-medium {
        border-left-color: #d97706;
    }

    /* Clean divider */
    hr {
        border: none;
        border-top: 1px solid #e2e8f0;
        margin: 16px 0;
    }

    /* Hide Streamlit footer */
    footer { visibility: hidden; }

    /* Info boxes */
    .info-box {
        background-color: #f0f9ff;
        border: 1px solid #bae6fd;
        border-radius: 6px;
        padding: 12px 16px;
        margin: 8px 0;
        font-size: 0.9rem;
        color: #0c4a6e;
    }
</style>
""", unsafe_allow_html=True)


# ── Initialize Database ──────────────────────────────────────────────

@st.cache_resource
def get_database():
    return Database()

db = get_database()


# ── Sidebar ──────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## 🛡️ Q-Shield")
    st.markdown(f"*{__app_subtitle__}*")
    st.markdown("---")

    st.markdown("### Navigation")
    st.page_link("app.py", label="📊 Overview", icon=None)
    st.page_link("pages/1_Asset_Inventory.py", label="📋 Asset Inventory")
    st.page_link("pages/2_Risk_Assessment.py", label="⚡ Risk Assessment")
    st.page_link("pages/3_Migration_Planner.py", label="🗺️ Migration Planner")
    st.page_link("pages/4_Reports.py", label="📄 Reports")
    st.page_link("pages/5_Methodology.py", label="📚 Methodology & Standards")

    st.markdown("---")

    # Load demo data button
    if st.button("📥 Load Demo Data", use_container_width=True,
                 help="Load synthetic financial-system data for demonstration"):
        demo = load_demo_assets()
        count = import_assets_to_db(db, demo, source="demo_dataset")
        _run_assessment(db)
        st.success(f"✅ Loaded {count} demo assets")
        st.rerun()

    # Clear data button
    if st.button("🗑️ Clear All Data", use_container_width=True,
                 help="Remove all assets and assessment data"):
        db.delete_all_assets()
        db.log_activity("Cleared all data")
        st.success("Data cleared")
        st.rerun()

    st.markdown("---")
    st.markdown(
        f"<small>v{__version__} · Track: Cybersecurity</small>",
        unsafe_allow_html=True
    )


# ── Helper: Run Assessment ───────────────────────────────────────────

def _run_assessment(database: Database):
    """Run detection and scoring on all assets."""
    assets = database.get_all_assets()
    for asset in assets:
        finding = analyze_asset(asset)
        score = compute_risk_score(asset, finding)
        database.save_assessment(
            asset["asset_id"],
            finding.to_dict(),
            score.to_dict()
        )
    database.log_activity(
        "Assessment completed",
        f"Assessed {len(assets)} assets",
        len(assets)
    )


# ── Main Dashboard ───────────────────────────────────────────────────

st.markdown(f"""
<div class="main-header">
    <h1>🛡️ Q-Shield</h1>
    <p>{__app_subtitle__}</p>
</div>
""", unsafe_allow_html=True)

# Check if data is loaded
stats = db.get_summary_stats()

if stats["total_assets"] == 0:
    st.info(
        "👋 **Welcome to Q-Shield!** No assets loaded yet. "
        "Click **📥 Load Demo Data** in the sidebar to get started, "
        "or go to **Asset Inventory** to upload your own data."
    )
    st.markdown("""
    ### What is Q-Shield?

    Q-Shield helps your organization prepare for post-quantum cryptography (PQC) by:

    1. 📋 **Building a cryptographic asset inventory** — catalog what algorithms you use and where
    2. 🔍 **Detecting quantum-vulnerable cryptography** — identify RSA, ECC, and DH usage
    3. ⚡ **Scoring risk transparently** — explainable 0-100 scores with full breakdowns
    4. 🗺️ **Planning PQC migration** — phased recommendations aligned with NIST standards
    5. 📄 **Generating reports** — professional PDF and CSV exports

    > ⚠️ **Important**: Do not upload confidential production inventories to a public demo.
    > This is a prototype assessment tool, not a production security system.
    """)
    st.stop()

# ── Summary Metrics ──────────────────────────────────────────────────

st.markdown("### Assessment Overview")

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.metric("Total Assets", stats["total_assets"])
with col2:
    st.metric("Quantum Vulnerable", stats["quantum_vulnerable"],
              help="Assets using algorithms vulnerable to Shor's algorithm")
with col3:
    st.metric("High Priority", stats["high_priority"],
              help="Assets with Critical or High risk scores")
with col4:
    st.metric("PQC Algorithms", stats["pqc_assets"],
              help="Assets already using post-quantum cryptographic algorithms")
with col5:
    st.metric("Needs Review", stats["needs_review"],
              help="Assets with insufficient evidence for classification")

st.markdown("---")

# ── Charts ───────────────────────────────────────────────────────────

assessments = db.get_all_assessments()
assets = db.get_all_assets()

if assessments:
    chart_col1, chart_col2 = st.columns(2)

    # Risk distribution
    with chart_col1:
        st.markdown("#### Risk Distribution")
        risk_counts = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
        for a in assessments:
            level = a.get("risk_level", "Unknown")
            if level in risk_counts:
                risk_counts[level] += 1

        risk_df = pd.DataFrame([
            {"Risk Level": k, "Count": v}
            for k, v in risk_counts.items() if v > 0
        ])
        if not risk_df.empty:
            color_map = {
                "Critical": "#dc2626", "High": "#ea580c",
                "Medium": "#d97706", "Low": "#16a34a"
            }
            fig = px.bar(
                risk_df, x="Risk Level", y="Count",
                color="Risk Level", color_discrete_map=color_map,
                text="Count"
            )
            fig.update_layout(
                showlegend=False, height=300,
                margin=dict(l=20, r=20, t=20, b=20),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
            )
            fig.update_traces(textposition="outside")
            st.plotly_chart(fig, use_container_width=True)

    # Algorithm distribution
    with chart_col2:
        st.markdown("#### Cryptographic Algorithm Distribution")
        algo_counts = {}
        for asset in assets:
            algo = asset.get("cryptographic_algorithm", "Unknown")
            # Simplify algorithm name for chart
            algo_simple = algo.split("-")[0] if "-" in algo else algo.split(" ")[0]
            algo_counts[algo_simple] = algo_counts.get(algo_simple, 0) + 1

        if algo_counts:
            algo_df = pd.DataFrame([
                {"Algorithm": k, "Count": v}
                for k, v in sorted(algo_counts.items(), key=lambda x: -x[1])
            ])
            fig = px.pie(
                algo_df, values="Count", names="Algorithm",
                color_discrete_sequence=px.colors.qualitative.Set2,
                hole=0.4
            )
            fig.update_layout(
                height=300,
                margin=dict(l=20, r=20, t=20, b=20),
                paper_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig, use_container_width=True)

    chart_col3, chart_col4 = st.columns(2)

    # Asset type distribution
    with chart_col3:
        st.markdown("#### Assets by System Type")
        type_counts = {}
        for asset in assets:
            atype = asset.get("asset_type", "Other")
            type_counts[atype] = type_counts.get(atype, 0) + 1

        if type_counts:
            type_df = pd.DataFrame([
                {"Type": k, "Count": v}
                for k, v in sorted(type_counts.items(), key=lambda x: -x[1])
            ])
            fig = px.bar(
                type_df, x="Count", y="Type", orientation="h",
                color_discrete_sequence=["#0e7c86"],
                text="Count"
            )
            fig.update_layout(
                height=300,
                margin=dict(l=20, r=20, t=20, b=20),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                yaxis=dict(categoryorder="total ascending"),
            )
            fig.update_traces(textposition="outside")
            st.plotly_chart(fig, use_container_width=True)

    # Migration priority by business criticality
    with chart_col4:
        st.markdown("#### Migration Priority by Criticality")
        crit_risk = {}
        asset_map = {a["asset_id"]: a for a in assets}
        for a in assessments:
            aid = a.get("asset_id", "")
            asset = asset_map.get(aid, {})
            crit = asset.get("business_criticality", "Medium")
            if a.get("is_quantum_vulnerable"):
                crit_risk[crit] = crit_risk.get(crit, 0) + 1

        if crit_risk:
            crit_df = pd.DataFrame([
                {"Criticality": k, "Vulnerable Assets": v}
                for k, v in crit_risk.items()
            ])
            order = ["Critical", "High", "Medium", "Low"]
            crit_df["sort"] = crit_df["Criticality"].map(
                {v: i for i, v in enumerate(order)}
            )
            crit_df = crit_df.sort_values("sort")
            fig = px.bar(
                crit_df, x="Criticality", y="Vulnerable Assets",
                color="Criticality",
                color_discrete_map={
                    "Critical": "#dc2626", "High": "#ea580c",
                    "Medium": "#d97706", "Low": "#16a34a"
                },
                text="Vulnerable Assets"
            )
            fig.update_layout(
                showlegend=False, height=300,
                margin=dict(l=20, r=20, t=20, b=20),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
            )
            fig.update_traces(textposition="outside")
            st.plotly_chart(fig, use_container_width=True)

    # Migration readiness
    st.markdown("#### Migration Readiness Status")
    status_counts = {}
    for asset in assets:
        status = asset.get("migration_status", "Not Started")
        status_counts[status] = status_counts.get(status, 0) + 1

    if status_counts:
        status_df = pd.DataFrame([
            {"Status": k, "Count": v}
            for k, v in status_counts.items()
        ])
        status_colors = {
            "Not Started": "#94a3b8", "Assessment": "#3b82f6",
            "Planned": "#8b5cf6", "Testing": "#f59e0b",
            "Ready for Review": "#f97316", "Completed": "#16a34a"
        }
        fig = px.bar(
            status_df, x="Status", y="Count",
            color="Status", color_discrete_map=status_colors,
            text="Count"
        )
        fig.update_layout(
            showlegend=False, height=260,
            margin=dict(l=20, r=20, t=10, b=20),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        fig.update_traces(textposition="outside")
        st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# ── Priority Queue ───────────────────────────────────────────────────

st.markdown("### 🚨 Priority Queue — Top 5 Assets for Review")

if assessments:
    # Sort by risk score descending
    sorted_assessments = sorted(
        assessments, key=lambda x: x.get("risk_score", 0), reverse=True
    )[:5]

    asset_map = {a["asset_id"]: a for a in assets}

    for a in sorted_assessments:
        aid = a["asset_id"]
        asset = asset_map.get(aid, {})
        finding = a.get("finding_json", {})
        risk_level = a.get("risk_level", "Unknown")

        level_class = f"risk-{risk_level.lower()}"
        border_class = "priority-item"
        if risk_level == "High":
            border_class += " priority-item-high"
        elif risk_level == "Medium":
            border_class += " priority-item-medium"

        st.markdown(f"""
        <div class="{border_class}">
            <strong>{asset.get('asset_name', aid)}</strong>
            <span class="{level_class}" style="float:right">
                {a.get('risk_score', 0)}/100 · {risk_level}
            </span><br>
            <small>
                Algorithm: {asset.get('cryptographic_algorithm', 'N/A')} ·
                Purpose: {asset.get('cryptographic_purpose', 'N/A')} ·
                {finding.get('vulnerability_type', '')}
            </small>
        </div>
        """, unsafe_allow_html=True)
else:
    st.info("Run an assessment to see priority rankings.")

st.markdown("---")

# ── Recent Activity ──────────────────────────────────────────────────

st.markdown("### 📋 Recent Activity")
activity = db.get_recent_activity(limit=8)

if activity:
    for act in activity:
        ts = act.get("timestamp", "")
        try:
            dt = datetime.fromisoformat(ts)
            ts_display = dt.strftime("%Y-%m-%d %H:%M UTC")
        except (ValueError, TypeError):
            ts_display = ts

        st.markdown(
            f"- **{act.get('action', '')}** — {act.get('details', '')} "
            f"<small style='color:#94a3b8'>({ts_display})</small>",
            unsafe_allow_html=True
        )
else:
    st.info("No activity recorded yet. Load demo data or import assets to begin.")
