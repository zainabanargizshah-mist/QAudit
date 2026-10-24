"""
Q-Shield — Reports Page

Export professional PDF reports, CSV assessment data, and inventory exports.
All reports are generated from current assessment data, not static templates.
"""

import streamlit as st
import pandas as pd
import hashlib
import json
from datetime import datetime, timezone

from qshield.database import Database
from qshield.detection import analyze_asset
from qshield.risk_engine import compute_risk_score
from qshield.recommendations import generate_all_recommendations
from qshield.reporting import generate_csv_report, generate_pdf_report
from qshield.models import DetectionFinding, RiskScoreResult
from qshield.inventory import export_assets_csv


st.set_page_config(
    page_title="Reports — Q-Shield",
    page_icon="📄",
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
st.markdown("# 📄 Reports & Exports")
st.markdown(
    "Generate and download assessment reports from the current data. "
    "Reports contain decision-support findings, not compliance certifications."
)

assets = db.get_all_assets()
assessments = db.get_all_assessments()
stats = db.get_summary_stats()

if not assets:
    st.info("📭 No assets loaded. Use **Asset Inventory** to load demo data or upload a CSV/JSON file.")
    st.stop()

if not assessments:
    st.info("⏳ Run an assessment first from the **Risk Assessment** page.")
    st.stop()

# ── Report Summary ───────────────────────────────────────────────────
st.markdown("### Current Assessment Summary")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Assets", stats["total_assets"])
col2.metric("Quantum Vulnerable", stats["quantum_vulnerable"])
col3.metric("High Priority", stats["high_priority"])
col4.metric("Needs Review", stats["needs_review"])

st.markdown("---")

# ── Prepare Report Data ──────────────────────────────────────────────
finding_dicts = []
score_dicts = []
finding_objs = []
score_objs = []

for a in assessments:
    f_data = a.get("finding_json", {})
    s_data = a.get("score_json", {})
    finding_dicts.append(f_data)
    score_dicts.append(s_data)
    finding_objs.append(
        DetectionFinding(**{k: v for k, v in f_data.items() if k in DetectionFinding.__dataclass_fields__})
    )
    score_objs.append(
        RiskScoreResult(**{k: v for k, v in s_data.items() if k in RiskScoreResult.__dataclass_fields__})
    )

recs = generate_all_recommendations(assets, finding_objs, score_objs)
now = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M")

# ── Export Buttons ───────────────────────────────────────────────────
st.markdown("### Available Exports")

col_a, col_b, col_c = st.columns(3)

# CSV Inventory
with col_a:
    st.markdown("#### 📋 Asset Inventory (CSV)")
    st.caption("Raw inventory data with all asset fields.")
    csv_inv = export_assets_csv(db)
    st.download_button(
        "📥 Download Inventory CSV",
        csv_inv,
        file_name=f"qshield_inventory_{now}.csv",
        mime="text/csv",
        use_container_width=True,
    )

# CSV Assessment
with col_b:
    st.markdown("#### ⚡ Assessment Results (CSV)")
    st.caption("Combined inventory + findings + risk scores.")
    csv_report = generate_csv_report(assets, finding_dicts, score_dicts)
    st.download_button(
        "📥 Download Assessment CSV",
        csv_report,
        file_name=f"qshield_assessment_{now}.csv",
        mime="text/csv",
        use_container_width=True,
    )

# PDF Report
with col_c:
    st.markdown("#### 📄 Full PDF Report")
    st.caption("Professional report with executive summary, findings, recommendations, and methodology.")

    report_source = json.dumps(
        {"assets": assets, "assessments": assessments},
        sort_keys=True,
        default=str,
    )
    report_fingerprint = hashlib.sha256(report_source.encode("utf-8")).hexdigest()
    if st.session_state.get("pdf_report_fingerprint") != report_fingerprint:
        st.session_state.pop("pdf_report_bytes", None)
        st.session_state["pdf_report_fingerprint"] = report_fingerprint

    if st.button("📄 Generate PDF Report", type="primary", use_container_width=True):
        with st.spinner("Generating PDF report..."):
            try:
                st.session_state["pdf_report_bytes"] = generate_pdf_report(
                    assets, finding_dicts, score_dicts, recs, stats,
                )
                st.success("✅ PDF report generated successfully.")
                db.log_activity("Report generated", "PDF assessment report")
            except Exception as e:
                st.session_state.pop("pdf_report_bytes", None)
                st.error(f"❌ Error generating PDF: {str(e)[:200]}")

    pdf_bytes = st.session_state.get("pdf_report_bytes")
    if pdf_bytes:
        st.download_button(
            "📥 Download PDF Report",
            pdf_bytes,
            file_name=f"qshield_report_{now}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

st.markdown("---")

# ── Report Contents Preview ──────────────────────────────────────────
st.markdown("### Report Preview")

tab1, tab2, tab3 = st.tabs(["Executive Summary", "Top Findings", "Recommendations"])

with tab1:
    st.markdown("#### Executive Summary")
    st.markdown(f"""
    **Assessment Date:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}

    **Scope:** {stats['total_assets']} cryptographic assets assessed across
    the organization's technology estate.

    **Key Findings:**
    - **{stats['quantum_vulnerable']}** assets use cryptographic algorithms
      potentially vulnerable to quantum computing attacks (RSA, ECC, DH).
    - **{stats['high_priority']}** assets are rated Critical or High priority
      for migration assessment.
    - **{stats['pqc_assets']}** assets already use NIST-standardized
      post-quantum cryptographic algorithms.
    - **{stats['needs_review']}** assets require manual review due to
      insufficient evidence for automated classification.

    **Risk Summary:**
    The assessment identifies assets using public-key cryptography that may
    be vulnerable to Shor's algorithm on a sufficiently capable quantum
    computer. High-priority assets include internet-facing systems handling
    restricted data with long retention periods, where harvest-now-decrypt-later
    risk is elevated.

    **Recommended Action:**
    Begin PQC migration planning for Critical and High priority assets,
    starting with inventory verification and dependency analysis.

    ---
    *This is a decision-support summary, not a compliance certification.
    All findings require review by qualified security professionals.*
    """)

with tab2:
    st.markdown("#### Top 10 Findings by Risk Score")
    top_findings = sorted(assessments, key=lambda x: x.get("risk_score", 0), reverse=True)[:10]
    asset_map = {a["asset_id"]: a for a in assets}

    for a in top_findings:
        aid = a["asset_id"]
        asset = asset_map.get(aid, {})
        finding = a.get("finding_json", {})
        level = a.get("risk_level", "Unknown")
        score = a.get("risk_score", 0)

        icon = "🔴" if level == "Critical" else "🟠" if level == "High" else "🟡" if level == "Medium" else "🟢"

        st.markdown(
            f"{icon} **{asset.get('asset_name', aid)}** — "
            f"`{asset.get('cryptographic_algorithm', 'N/A')}` — "
            f"{score}/100 ({level})"
        )
        st.caption(f"  {finding.get('vulnerability_type', 'N/A')} · Rule: {finding.get('rule_id', 'N/A')}")

with tab3:
    st.markdown("#### Migration Recommendations Summary")
    vuln_recs = [r for r in recs if r.get("risk_priority") in ("Critical", "High")]

    if vuln_recs:
        for rec in vuln_recs[:10]:
            st.markdown(f"**{rec['asset_name']}** → {rec.get('target_standard', 'TBD')}")
            if rec.get("target_algorithm"):
                st.caption(f"  Target: {rec['target_algorithm']}")
    else:
        st.info("No Critical/High recommendations at this time.")

st.markdown("---")

st.markdown("""
> **Limitations:** This report is generated by Q-Shield, a prototype
> assessment tool. Scores are decision-support estimates. Detection is
> rule-based and may not cover all configurations. This tool does not
> certify compliance with any standard. All findings require human review.
""")
