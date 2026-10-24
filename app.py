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
from qshield.auth import require_login, render_auth_sidebar
from qshield.database import Database
from qshield.inventory import load_demo_assets, import_assets_to_db, get_assets_dataframe
from qshield.assessment import assess_all
from qshield.models import DEFAULT_SCORING_CONFIG
from qshield.ui import inject_styles, render_sidebar, render_page_header


# ── Page Config ──────────────────────────────────────────────────────

st.set_page_config(
    page_title="Q-Shield — Quantum-Readiness Assessment",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

require_login()
inject_styles()


# ── Initialize Database ──────────────────────────────────────────────

@st.cache_resource
def get_database():
    return Database()

db = get_database()


# ── Helper: Run Assessment ───────────────────────────────────────────

def _run_assessment(database: Database):
    """Run the shared detection and scoring pipeline on all assets."""
    assess_all(database)


# ── Sidebar ──────────────────────────────────────────────────────────

render_sidebar("Command Center")
with st.sidebar:


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


# ── Main Dashboard ───────────────────────────────────────────────────

render_page_header("Quantum readiness · command center", "Q-Shield Command Center", __app_subtitle__)

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
                "Critical": "#ff1018", "High": "#171717",
                "Medium": "#77777d", "Low": "#c8c6cb"
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
                color_discrete_sequence=["#ff1018", "#171717", "#77777d", "#c8c6cb"],
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
                color_discrete_sequence=["#ff1018"],
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
                    "Critical": "#ff1018", "High": "#171717",
                    "Medium": "#77777d", "Low": "#c8c6cb"
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
            "Not Started": "#c8c6cb", "Assessment": "#77777d",
            "Planned": "#171717", "Testing": "#ff1018",
            "Ready for Review": "#c9070d", "Completed": "#45454a"
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
