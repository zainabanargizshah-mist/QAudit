"""
Q-Shield — Migration Planner Page

Generates PQC migration recommendations, displays phased migration
framework, and allows migration status tracking.
"""

import streamlit as st
import pandas as pd
import json
from datetime import datetime, timezone
from streamlit.errors import StreamlitAPIException

from qshield.auth import require_login, render_auth_sidebar
from qshield.database import Database
from qshield.detection import analyze_asset
from qshield.risk_engine import compute_risk_score
from qshield.recommendations import (
    generate_all_recommendations, get_migration_phases,
)
from qshield.models import MigrationStatus, NIST_PQC_STANDARDS, DetectionFinding, RiskScoreResult, CryptographicAsset
from qshield.ai_assistant import AIAssistant
from qshield.ui import inject_styles, render_sidebar, render_page_header
from qshield.migration_plan import (
    build_ai_payload,
    build_independent_analysis,
)
from qshield.reporting import generate_migration_plan_pdf


st.set_page_config(
    page_title="Migration Planner — Q-Shield",
    page_icon="🗺️",
    layout="wide",
)

require_login()

st.markdown("""
<style>
    [data-testid="stSidebar"] { background-color: #1a1f36; }
    [data-testid="stSidebar"] * { color: #e0e4ef !important; }
    .demo-badge {
        display: inline-block; background-color: #f59e0b;
        color: #1a1f36 !important; padding: 3px 10px; border-radius: 4px;
        font-size: 0.7rem; font-weight: 700;
    }
    .phase-card {
        background: #ffffff; border: 1px solid #e2e8f0;
        border-radius: 8px; padding: 16px; margin: 8px 0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .phase-number {
        display: inline-block; background: #0e7c86; color: white;
        width: 28px; height: 28px; border-radius: 50%;
        text-align: center; line-height: 28px; font-weight: 700;
        margin-right: 8px; font-size: 0.85rem;
    }
    footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)
inject_styles()

@st.cache_resource
def get_database():
    return Database()

db = get_database()

render_sidebar("Migration Roadmap")

# ── Header ───────────────────────────────────────────────────────────
render_page_header("Transition · planning", "PQC Migration Planner", "Phased migration recommendations aligned with NIST PQC standards. 'Completed' status means a user has recorded completion — it is not inferred from algorithm presence.")

assets = db.get_all_assets()
assessments = db.get_all_assessments()

if not assets:
    st.info("📭 No assets loaded. Use **Asset Inventory** to load demo data or upload a CSV/JSON file.")
    st.stop()

if not assessments:
    st.info("⏳ Run an assessment first from the **Risk Assessment** page.")
    st.stop()

# ── Build Recommendations ────────────────────────────────────────────
asset_map = {a["asset_id"]: a for a in assets}
findings = []
scores = []

for a in assessments:
    f_data = a.get("finding_json", {})
    s_data = a.get("score_json", {})
    findings.append(DetectionFinding(**{k: v for k, v in f_data.items() if k in DetectionFinding.__dataclass_fields__}))
    scores.append(RiskScoreResult(**{k: v for k, v in s_data.items() if k in RiskScoreResult.__dataclass_fields__}))

recs = generate_all_recommendations(assets, findings, scores)
independent_analysis = build_independent_analysis(assets, findings, scores, recs)

# ── Migration Phase Framework ────────────────────────────────────────
with st.expander("📋 PQC Migration Phase Framework", expanded=False):
    phases = get_migration_phases()
    for phase in phases:
        st.markdown(f"""
        <div class="phase-card">
            <span class="phase-number">{phase['phase']}</span>
            <strong>{phase['name']}</strong><br>
            <small>{phase['description']}</small>
        </div>
        """, unsafe_allow_html=True)
        for activity in phase["activities"]:
            st.markdown(f"  - {activity}")

st.markdown("---")

# ── NIST PQC Standards Reference ────────────────────────────────────
with st.expander("📚 NIST PQC Standards Quick Reference", expanded=False):
    for fips, info in NIST_PQC_STANDARDS.items():
        st.markdown(f"**{fips}: {info['title']}**")
        st.markdown(f"- Purpose: {info['purpose']}")
        st.markdown(f"- Algorithm: `{info['algorithm']}`")
        st.markdown(f"- Status: {info['status']}")
        st.markdown(f"- URL: [{info['url']}]({info['url']})")
        st.markdown("")

st.markdown("---")

# ── Recommendations Table ────────────────────────────────────────────
st.markdown(f"### Migration Recommendations ({len(recs)} assets)")

# Filters
rcol1, rcol2 = st.columns(2)
with rcol1:
    priority_filter = st.multiselect(
        "Filter by Priority",
        ["Critical", "High", "Medium", "Low"],
    )
with rcol2:
    show_only_vulnerable = st.checkbox("Show only quantum-vulnerable assets", value=False)

filtered_recs = recs
if priority_filter:
    filtered_recs = [r for r in filtered_recs if r.get("risk_priority") in priority_filter]
if show_only_vulnerable:
    finding_map = {f.asset_id: f for f in findings}
    filtered_recs = [r for r in filtered_recs if finding_map.get(r["asset_id"], DetectionFinding()).is_quantum_vulnerable]

for rec in filtered_recs:
    aid = rec["asset_id"]
    priority = rec.get("risk_priority", "Unknown")
    icon = "🔴" if priority == "Critical" else "🟠" if priority == "High" else "🟡" if priority == "Medium" else "🟢"

    with st.expander(
        f"{icon} {rec['asset_name']} — {priority} ({rec.get('risk_score', 0)}/100) "
        f"· Status: {rec.get('migration_status', 'N/A')}"
        f" · Verification: {asset_map.get(aid, {}).get('verification_status', 'unverified')}"
        f"{'  ⚠️ REVIEW' if rec.get('needs_review') else ''}",
    ):
        mc1, mc2 = st.columns([3, 2])

        with mc1:
            st.markdown(f"**Current Algorithm:** `{rec.get('current_algorithm', 'N/A')}`")
            st.markdown(f"**Purpose:** {rec.get('current_purpose', 'N/A')}")
            st.markdown(f"**Identified Concern:** {rec.get('identified_concern', 'N/A')}")

            if rec.get("target_standard"):
                st.success(f"🎯 **Target Standard:** {rec['target_standard']}")
                st.markdown(f"**Target Algorithm:** {rec.get('target_algorithm', 'N/A')}")

            st.markdown("**Suggested Actions:**")
            for action in rec.get("suggested_actions", []):
                if action:
                    st.markdown(f"- {action}")

            st.markdown(f"**Dependencies:** {rec.get('dependencies', 'N/A')}")

        with mc2:
            st.markdown("**Validation Requirements:**")
            for v in rec.get("validation_requirements", []):
                st.markdown(f"- {v}")

            st.markdown("**Testing Requirements:**")
            for t in rec.get("testing_requirements", []):
                st.markdown(f"- {t}")

            # Migration status update
            st.markdown("---")
            st.markdown("**Update Migration Status:**")
            all_statuses = [e.value for e in MigrationStatus]
            current = rec.get("migration_status", "Not Started")
            new_status = st.selectbox(
                "Status", all_statuses,
                index=all_statuses.index(current) if current in all_statuses else 0,
                key=f"status_{aid}",
            )
            if st.button("Update Status", key=f"update_{aid}"):
                asset = db.get_asset(aid)
                if asset:
                    asset["migration_status"] = new_status
                    from qshield.models import CryptographicAsset
                    db.upsert_asset(CryptographicAsset.from_dict(asset))
                    db.log_activity(
                        f"Migration status changed to '{new_status}'",
                        f"Asset: {aid}",
                    )
                    st.success(f"✅ Updated {aid} to '{new_status}'")
                    st.rerun()

            if rec.get("needs_review"):
                st.warning("⚠️ Requires manual review before action.")
            if rec.get("blockers"):
                st.warning("Blockers: " + " · ".join(rec["blockers"]))
            st.caption("Planning guidance only. Confirm assumptions, dependencies, and implementation evidence before approval.")

st.markdown("---")

# ── Full AI Migration Plan ────────────────────────────────────────────
ai = AIAssistant()
st.markdown("### 🧠 Full AI Migration Plan")
st.caption(
    "Q-Shield first performs an independent NIST/OWASP analysis. Gemini then "
    "turns that analysis into a complete migration plan; it cannot overwrite "
    "the deterministic risk score or evidence-based progress percentage."
)

progress_col, vulnerable_col, review_col, control_col = st.columns(4)
progress_col.metric("Migration Progress", f"{independent_analysis['overall_progress']}%")
vulnerable_col.metric("Quantum Vulnerable", independent_analysis["quantum_vulnerable_count"])
review_col.metric("Needs Review", independent_analysis["needs_review_count"])
control_col.metric("OWASP Controls", independent_analysis["owasp_control_count"])

with st.expander("🔐 Gemini data-sharing consent", expanded=True):
    st.warning(
        "Only enable this after confirming that the inventory is approved for "
        "external AI processing. Never send private keys, passwords, tokens, or "
        "unapproved confidential data."
    )
    redact_identity = st.checkbox(
        "Redact asset IDs, names, owners, business domains, and verification evidence before sending",
        value=True,
        help="Recommended. The model still receives cryptographic and risk fields needed for planning.",
        key="migration_plan_redact_identity",
    )
    allow_plan_ai = st.checkbox(
        "I authorize sending the selected inventory data and deterministic analysis to the configured Gemini provider",
        value=False,
        key="migration_plan_allow_ai",
    )

if st.button("🚀 Generate Full 0–100% Migration Plan", type="primary", use_container_width=True):
    if not allow_plan_ai:
        st.error("Enable the Gemini data-sharing consent checkbox before generating an AI plan.")
    elif not ai.is_available():
        st.error(
            "Gemini is not configured. Add a replacement key locally as GEMINI_API_KEY "
            "in .env or Streamlit secrets, then reload the app."
        )
    else:
        payload = build_ai_payload(
            independent_analysis,
            assets,
            redact_identity=redact_identity,
        )
        with st.spinner("Gemini is analyzing the inventory and writing the migration plan..."):
            migration_plan = ai.generate_migration_plan(payload, allow_external=True)
        st.session_state["migration_plan"] = migration_plan
        st.session_state["migration_plan_generated_at"] = datetime.now(timezone.utc).strftime(
            "%Y-%m-%d %H:%M UTC"
        )
        if ai.last_error:
            st.warning(
                f"Gemini was not used: {ai.last_error} Showing the deterministic baseline instead."
            )
        else:
            st.success("✅ Full migration plan generated by Gemini. Review it before implementation.")

migration_plan = st.session_state.get("migration_plan")
if migration_plan:
    generated_at = st.session_state.get("migration_plan_generated_at", "")
    st.markdown("#### Generated plan")
    st.markdown(f"**{migration_plan.get('title', 'Q-Shield Migration Plan')}**")
    st.info(migration_plan.get("executive_summary", "No executive summary was returned."))
    st.caption(
        f"Mode: {migration_plan.get('response_mode', 'unknown')} · "
        f"Risk-weighted progress: {migration_plan.get('overall_progress', 0)}% · "
        f"Standards reference: {migration_plan.get('standards_reference_version', 'unknown')}"
    )

    plan_tab1, plan_tab2, plan_tab3, plan_tab4 = st.tabs(
        ["Phases", "Priority Actions", "Open Questions", "Standards"]
    )
    with plan_tab1:
        for phase in migration_plan.get("phases", []) or []:
            if not isinstance(phase, dict):
                continue
            st.markdown(
                f"**Phase {phase.get('phase', '')}: {phase.get('name', '')}** — "
                f"{phase.get('objective', phase.get('description', ''))}"
            )
            for activity in phase.get("activities", []) or []:
                st.markdown(f"- {activity}")
            for label in ("entry_criteria", "exit_criteria", "evidence_required", "rollback_or_contingency"):
                values = phase.get(label, [])
                if values:
                    display = "; ".join(values) if isinstance(values, list) else values
                    st.markdown(f"**{label.replace('_', ' ').title()}:** {display}")
    with plan_tab2:
        actions = migration_plan.get("asset_actions", []) or []
        if not actions:
            st.info("No asset actions were returned.")
        for action in actions:
            if not isinstance(action, dict):
                continue
            name = action.get("asset_name") or action.get("asset_id", "Asset")
            priority = action.get("risk_level", action.get("priority", "Unknown"))
            st.markdown(
                f"**{name}** — {priority} · "
                f"{action.get('progress_percent', independent_analysis['overall_progress'])}% progress"
            )
            for label in (
                "current_state", "target_state", "rationale", "actions", "dependencies",
                "validation", "evidence_required", "owner", "estimated_sequence",
            ):
                value = action.get(label)
                if value:
                    if isinstance(value, list):
                        value = "; ".join(str(item) for item in value)
                    st.markdown(f"- **{label.replace('_', ' ').title()}:** {value}")
            st.markdown("---")
    with plan_tab3:
        st.markdown("**Open questions**")
        for question in migration_plan.get("open_questions", []) or []:
            st.markdown(f"- {question}")
        st.markdown("**Assumptions**")
        for assumption in migration_plan.get("assumptions", []) or []:
            st.markdown(f"- {assumption}")
    with plan_tab4:
        for standard in migration_plan.get("standards_used", []) or []:
            st.markdown(f"- {standard}")

    try:
        plan_pdf = generate_migration_plan_pdf(migration_plan, generated_at=generated_at)
        st.download_button(
            "📥 Download Full Migration Plan PDF",
            plan_pdf,
            file_name="qshield_full_migration_plan.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
    except Exception as exc:
        st.error(f"Could not generate the migration-plan PDF: {str(exc)[:200]}")

st.markdown("---")

# ── AI Assistant ─────────────────────────────────────────────────────
st.markdown("### 🤖 AI Migration Assistant")

if ai.is_available():
    st.success(f"✅ {ai.provider_name} is configured · `{ai.model}` · responses are advisory")
else:
    st.info(
        f"💡 AI assistant is not configured. {ai.configuration_message()} "
        "Rule-based recommendations are active."
    )

# Send aggregate counts and a few anonymized risk records only. Asset IDs,
# names, owners, notes, and uploaded source data are excluded.
context_summary = {
    "asset_count": len(assets),
    "assessment_count": len(assessments),
    "quantum_vulnerable_count": sum(bool(a.get("is_quantum_vulnerable")) for a in assessments),
    "pqc_in_use_count": sum(bool(a.get("is_pqc")) for a in assessments),
    "needs_review_count": sum(bool(a.get("needs_review")) for a in assessments),
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
context_summary = json.dumps(context_summary, ensure_ascii=True)

st.caption(
    "On each question, Q-Shield sends Gemini your question and a limited, "
    "anonymized assessment summary. Asset names, IDs, owners, notes, and raw uploads are excluded."
)

allow_external_ai = st.checkbox(
    "Allow this limited anonymized summary to be sent to the configured AI provider",
    value=False,
)

prompt_options = [
    "Generate an executive summary of this assessment",
    "Summarize the highest-priority assets for migration",
    "Draft a phased PQC migration plan for this organization",
    "Explain the compatibility concerns for migrating from RSA to ML-KEM",
    "What are the key risks of harvest-now-decrypt-later attacks?",
]

selected_prompt = st.selectbox("Select a question or write your own:", prompt_options)
custom_prompt = st.text_input("Or enter a custom question:", placeholder="Ask about the assessment...")

if st.button("🤖 Ask AI Assistant", type="primary"):
    prompt = custom_prompt if custom_prompt else selected_prompt
    with st.spinner("Analyzing..."):
        response = ai.query(prompt, context=context_summary, allow_external=allow_external_ai)
    if ai.last_notice:
        st.info(ai.last_notice)
    if ai.last_error:
        st.warning(
            f"AI-generated analysis is unavailable for this request. {ai.last_error} "
            "The response below is rule-based guidance, not a custom AI migration plan."
        )
    st.caption(
        f"Response mode: {ai.last_response_mode} · standards reference: "
        f"{ai.response_metadata.get('standards_reference_version', 'unknown')}"
    )
    st.markdown(response)
