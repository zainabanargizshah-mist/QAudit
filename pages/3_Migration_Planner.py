"""Q-Shield migration roadmap for moving prioritized assets toward PQC."""

from __future__ import annotations

import json

import streamlit as st

from qshield.ai_assistant import AIAssistant
from qshield.database import Database
from qshield.models import CryptographicAsset, DetectionFinding, MigrationStatus, NIST_PQC_STANDARDS, RiskScoreResult
from qshield.recommendations import generate_all_recommendations, get_migration_phases
from qshield.ui import inject_styles, render_flow_map, render_page_header, render_sidebar, section_title


st.set_page_config(page_title="Migration Roadmap — Q-Shield", page_icon="↗", layout="wide")
inject_styles()
render_sidebar("Migration Roadmap")


@st.cache_resource
def get_database() -> Database:
    return Database()


db = get_database()


render_page_header(
    "MIGRATION ROADMAP",
    "Move from exposure to verified progress",
    "Organize PQC migration as a sequence of accountable phases. Each recommendation remains linked to its current algorithm, target standard, dependencies, and validation work.",
)
render_flow_map([
    ("N1", "Observe", "Inventory the cryptographic estate."),
    ("N2", "Detect", "Classify vulnerable and PQC usage."),
    ("N3", "Prioritize", "Explain what needs attention first."),
    ("N4", "Migrate", "Move assets through a verified roadmap."),
])

assets = db.get_all_assets()
assessments = db.get_all_assessments()
if not assets:
    st.info("No assets loaded. Start in Inventory to load demo data or import a sanitized dataset.")
    if st.button("Open Inventory", type="primary"):
        st.switch_page("pages/1_Asset_Inventory.py")
    st.stop()
if not assessments:
    st.info("Run a risk assessment before building the migration roadmap.")
    if st.button("Open Risk Queue", type="primary"):
        st.switch_page("pages/2_Risk_Assessment.py")
    st.stop()

asset_map = {asset["asset_id"]: asset for asset in assets}
findings = []
scores = []
for assessment in assessments:
    finding_data = assessment.get("finding_json", {})
    score_data = assessment.get("score_json", {})
    findings.append(DetectionFinding(**{key: value for key, value in finding_data.items() if key in DetectionFinding.__dataclass_fields__}))
    scores.append(RiskScoreResult(**{key: value for key, value in score_data.items() if key in RiskScoreResult.__dataclass_fields__}))
recommendations = generate_all_recommendations(assets, findings, scores)

completed = sum(1 for asset in assets if asset.get("migration_status") == "Completed")
in_progress = sum(1 for asset in assets if asset.get("migration_status") in {"Assessment", "Planned", "Testing", "Ready for Review"})
blocked = sum(1 for recommendation in recommendations if recommendation.get("needs_review"))
progress_pct = round((completed / len(assets)) * 100) if assets else 0

section_title("Roadmap posture", "Status is recorded by the team. Q-Shield does not infer completion from algorithm presence.")
metric_cols = st.columns(4)
metric_cols[0].metric("Migration progress", f"{progress_pct}%", f"{completed} of {len(assets)} completed")
metric_cols[1].metric("In progress", in_progress, "Assessment through review")
metric_cols[2].metric("Needs review", blocked, "Evidence or hybrid configuration")
metric_cols[3].metric("Recommendations", len(recommendations), "Assets with a roadmap record")

section_title("PQC migration phases", "Use the phase framework as a shared language for security, platform, and application owners.")
phase_cols = st.columns(3)
for index, phase in enumerate(get_migration_phases()):
    with phase_cols[index % 3]:
        activities = "".join(f"<li>{activity}</li>" for activity in phase["activities"][:3])
        st.markdown(
            f"""
            <div class="qs-card" style="margin-bottom: 14px;">
                <div class="qs-card-title">Phase {phase['phase']}</div>
                <div style="font-size:1.03rem;font-weight:950;color:#080808;text-transform:uppercase;">{phase['name']}</div>
                <p class="qs-muted">{phase['description']}</p>
                <ul style="padding-left:18px;margin-bottom:0;color:#66758a;font-size:.82rem;line-height:1.55;">{activities}</ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

section_title("Recommendation queue", "Prioritize critical and high findings first, then update each asset as testing and validation progress.")
filter_col1, filter_col2 = st.columns(2)
with filter_col1:
    priority_filter = st.multiselect("Priority", ["Critical", "High", "Medium", "Low"])
with filter_col2:
    show_only_vulnerable = st.checkbox("Show only quantum-vulnerable assets", value=False)

filtered_recommendations = recommendations
if priority_filter:
    filtered_recommendations = [recommendation for recommendation in filtered_recommendations if recommendation.get("risk_priority") in priority_filter]
if show_only_vulnerable:
    finding_map = {finding.asset_id: finding for finding in findings}
    filtered_recommendations = [recommendation for recommendation in filtered_recommendations if finding_map.get(recommendation["asset_id"], DetectionFinding()).is_quantum_vulnerable]

st.caption(f"Showing {len(filtered_recommendations)} of {len(recommendations)} roadmap items")
all_statuses = [entry.value for entry in MigrationStatus]
for recommendation in filtered_recommendations:
    asset_id = recommendation["asset_id"]
    priority = recommendation.get("risk_priority", "Unknown")
    asset = asset_map.get(asset_id, {})
    with st.expander(
        f"{asset.get('asset_name', asset_id)} · {priority} · {recommendation.get('risk_score', 0):.0f}/100 · {recommendation.get('migration_status', 'Not Started')}",
        expanded=priority in {"Critical", "High"},
    ):
        detail_col1, detail_col2 = st.columns([1.25, 1])
        with detail_col1:
            st.markdown(f"**Current algorithm:** `{recommendation.get('current_algorithm', 'N/A')}`")
            st.markdown(f"**Purpose:** {recommendation.get('current_purpose', 'N/A')}")
            st.markdown(f"**Identified concern:** {recommendation.get('identified_concern', 'N/A')}")
            if recommendation.get("target_standard"):
                st.markdown(f'<div class="qs-callout"><strong>Target standard</strong><br>{recommendation["target_standard"]} · {recommendation.get("target_algorithm", "Target algorithm pending")}</div>', unsafe_allow_html=True)
            st.markdown("**Suggested actions**")
            for action in recommendation.get("suggested_actions", []):
                if action:
                    st.markdown(f"- {action}")
            st.markdown(f"**Dependencies:** {recommendation.get('dependencies', 'N/A')}")
        with detail_col2:
            st.markdown("**Validation requirements**")
            for requirement in recommendation.get("validation_requirements", []):
                st.markdown(f"- {requirement}")
            st.markdown("**Testing requirements**")
            for requirement in recommendation.get("testing_requirements", []):
                st.markdown(f"- {requirement}")
            st.markdown("---")
            current = asset.get("migration_status", "Not Started")
            new_status = st.selectbox("Update migration status", all_statuses, index=all_statuses.index(current) if current in all_statuses else 0, key=f"roadmap_status_{asset_id}")
            if st.button("Save status", key=f"roadmap_save_{asset_id}", type="primary"):
                asset["migration_status"] = new_status
                db.upsert_asset(CryptographicAsset.from_dict(asset))
                db.log_activity(f"Migration status changed to '{new_status}'", f"Asset: {asset_id}")
                st.success(f"Updated {asset_id} to {new_status}")
                st.rerun()
            if recommendation.get("needs_review"):
                st.warning("Manual review is required before migration action.")

section_title("Contextual AI assistant", "Ask questions about this assessment. Only a limited anonymized summary is sent when an AI provider is configured.")
ai = AIAssistant()
if ai.is_available():
    st.success(f"{ai.provider_name} is configured · `{ai.model}`")
else:
    st.info("AI is not configured. Rule-based recommendations remain available.")

context_summary = {
    "asset_count": len(assets),
    "assessment_count": len(assessments),
    "quantum_vulnerable_count": sum(bool(item.get("is_quantum_vulnerable")) for item in assessments),
    "pqc_in_use_count": sum(bool(item.get("is_pqc")) for item in assessments),
    "needs_review_count": sum(bool(item.get("needs_review")) for item in assessments),
    "highest_risk_assets": [],
}
for index, assessment in enumerate(assessments[:8], start=1):
    asset = asset_map.get(assessment.get("asset_id"), {})
    context_summary["highest_risk_assets"].append({
        "label": f"Asset {index}",
        "algorithm": asset.get("cryptographic_algorithm", "Unknown"),
        "purpose": asset.get("cryptographic_purpose", "Unknown"),
        "risk_score": assessment.get("risk_score"),
        "risk_level": assessment.get("risk_level", "Unknown"),
        "quantum_vulnerable": bool(assessment.get("is_quantum_vulnerable")),
        "pqc_in_use": bool(assessment.get("is_pqc")),
        "needs_review": bool(assessment.get("needs_review")),
        "migration_status": asset.get("migration_status", "Not Started"),
    })

with st.expander("Ask about the roadmap", expanded=False):
    st.caption("Asset names, IDs, owners, notes, and raw uploads are excluded from the assistant context.")
    prompt_options = [
        "Generate an executive summary of this assessment",
        "Summarize the highest-priority assets for migration",
        "Draft a phased PQC migration plan for this organization",
        "Explain the compatibility concerns for migrating from RSA to ML-KEM",
        "What are the key risks of harvest-now-decrypt-later attacks?",
    ]
    selected_prompt = st.selectbox("Choose a question", prompt_options)
    custom_prompt = st.text_input("Or write your own", placeholder="Ask about the assessment...")
    if st.button("Ask assistant", type="primary"):
        prompt = custom_prompt or selected_prompt
        with st.spinner("Preparing a grounded response..."):
            response = ai.query(prompt, context=json.dumps(context_summary, ensure_ascii=True))
        if ai.last_notice:
            st.info(ai.last_notice)
        if ai.last_error:
            st.warning(f"AI-generated analysis is unavailable for this request. {ai.last_error}")
        st.markdown(response)

with st.expander("NIST PQC standards quick reference", expanded=False):
    for fips, info in NIST_PQC_STANDARDS.items():
        st.markdown(f"**{fips}: {info['title']}**")
        st.caption(f"{info['purpose']} · `{info['algorithm']}` · {info['status']}")
