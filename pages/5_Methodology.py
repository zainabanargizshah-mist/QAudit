"""
Q-Shield — Methodology & Standards Page

Documents the risk-scoring methodology, detection rules, NIST PQC
standards, relevant guidance, limitations, and AI behavior.
"""

import json
import os
import streamlit as st

from qshield.models import DEFAULT_SCORING_CONFIG, NIST_PQC_STANDARDS
from qshield.ai_assistant import get_standards_reference
from qshield.ui import inject_styles, render_flow_map, render_page_header, render_sidebar, section_title


st.set_page_config(
    page_title="Methodology — Q-Shield",
    page_icon="📚",
    layout="wide",
)

inject_styles()

render_sidebar("Standards")

# ── Header ───────────────────────────────────────────────────────────
render_page_header(
    "STANDARDS",
    "Make every recommendation explainable",
    "Explore the detection rules, scoring factors, NIST references, AI boundaries, and limitations behind Q-Shield's decision-support workflow.",
)
render_flow_map([
    ("N1", "Observe", "Inventory the cryptographic estate."),
    ("N2", "Detect", "Classify vulnerable and PQC usage."),
    ("N3", "Explain", "Make every finding auditable."),
    ("N4", "Verify", "Keep standards and assumptions visible."),
])

# ── NIST PQC Standards ───────────────────────────────────────────────
st.markdown("---")
section_title("NIST post-quantum cryptography standards", "These standards are the primary migration targets used by Q-Shield recommendations.")
st.markdown(
    "NIST has standardized three post-quantum cryptographic algorithms. "
    "These are the primary migration targets recommended by Q-Shield."
)

for fips, info in NIST_PQC_STANDARDS.items():
    with st.expander(f"📘 {fips}: {info['title']}", expanded=False):
        st.markdown(f"**Algorithm:** `{info['algorithm']}`")
        st.markdown(f"**Purpose:** {info['purpose']}")
        st.markdown(f"**Status:** {info['status']}")
        st.markdown(f"**URL:** [{info['url']}]({info['url']})")
        st.markdown(f"**Organization:** {info.get('organization', 'NIST')}")

        st.info(
            f"Q-Shield recommends {info['algorithm']} for "
            f"{info['purpose'].lower()}. A digital-signature algorithm "
            f"must not be used for key establishment, and a KEM must not "
            f"be used for signing."
        )

# ── Additional Guidance ──────────────────────────────────────────────
st.markdown("---")
section_title("Additional standards and guidance")

refs = get_standards_reference()
for ref_id, ref in refs.items():
    if ref_id not in NIST_PQC_STANDARDS:
        st.markdown(f"**{ref_id}: {ref['title']}**")
        st.markdown(f"- Organization: {ref.get('organization', 'N/A')}")
        st.markdown(f"- URL: [{ref['url']}]({ref['url']})")
        if ref.get("summary"):
            st.caption(ref["summary"])
        st.markdown("")

st.info(
    "Q-Shield is **not** NIST-certified, OWASP-certified, or compliant with "
    "every control in any framework. The standards listed above are "
    "references used to ground recommendations. Official standards "
    "remain the authoritative source."
)

# ── Risk Scoring Methodology ────────────────────────────────────────
st.markdown("---")
section_title("Risk scoring methodology", "The score is a transparent, configurable weighted model—not an official NIST classification.")

cfg = DEFAULT_SCORING_CONFIG

st.markdown(f"""
Q-Shield uses a transparent, configurable risk-scoring model producing
scores from **0 to 100**. The score is a weighted sum of normalized
factor scores.

> {cfg['disclaimer']}
""")

st.markdown("### Scoring Weights")

weights = cfg["weights"]
for name, weight in weights.items():
    label = name.replace("_", " ").title()
    st.markdown(f"- **{label}:** {weight:.0%}")

st.markdown("### Factor Details")

st.markdown("""
| Factor | What it measures | High score means |
|--------|-----------------|-----------------|
| Crypto Exposure | Quantum vulnerability of the algorithm | Algorithm is vulnerable to Shor's algorithm |
| Data Sensitivity & Retention | Classification and how long data must be protected | Restricted data with 10+ year retention (harvest-now-decrypt-later risk) |
| Business Criticality | Impact if the asset is compromised | Mission-critical system |
| Internet Exposure | Whether the asset faces the public internet | Exposed to external attackers |
| Dependency Complexity | Number of dependent systems | Complex migration with many dependencies |
| Evidence Confidence | How much we know about the asset | Unknown or incomplete evidence (uncertainty penalty) |
""")

st.markdown("### Uncertainty Handling")
st.markdown("""
**Incomplete evidence is never treated as proof of safety.**

When evidence is insufficient to classify an algorithm:
- The asset is marked **"Needs Review"**
- The confidence score is set to **Low**
- An **uncertainty penalty** is applied to the risk score
- The asset appears in the priority queue for manual review

This ensures unknown assets are not silently ignored.
""")

st.markdown("### Risk Bands")
st.markdown("These are prototype defaults, not official NIST classifications.")

bands = cfg["risk_bands"]
band_colors = {"Critical": "🔴", "High": "🟠", "Medium": "🟡", "Low": "🟢"}
for level, (low, high) in bands.items():
    st.markdown(f"- {band_colors.get(level, '⚪')} **{level}:** {low}–{high}")

# ── Detection Rules ──────────────────────────────────────────────────
st.markdown("---")
section_title("Detection engine rules", "Deterministic, testable classification with a rule ID and evidence for every finding.")

st.markdown("""
The detection engine classifies cryptographic algorithms using
deterministic, testable rules. Each finding records the rule ID
and evidence that produced it.

### What the Engine Detects

| Category | Algorithms | Classification |
|----------|-----------|---------------|
| **Asymmetric (Vulnerable)** | RSA, ECDH, ECDHE, ECDSA, EdDSA, DH, DSA | Quantum-vulnerable (Shor's algorithm) |
| **PQC Standards** | ML-KEM (FIPS 203), ML-DSA (FIPS 204), SLH-DSA (FIPS 205) | Post-quantum secure |
| **Symmetric** | AES-256, AES-128, ChaCha20, 3DES | Not broken by quantum (Grover halves key length) |
| **Hash** | SHA-256, SHA-384, SHA-512, SHA-3, SHA-1, MD5 | Not broken by quantum (collision resistance maintained) |
| **Hybrid** | Classical + PQC combinations | PQC transition in progress — needs verification |
| **Unknown** | Unrecognized algorithms | Needs manual review |

### Important Distinctions

- **Algorithm ≠ Purpose**: RSA for key establishment and RSA for signing
  are treated as separate concerns with different migration targets.
- **Presence ≠ Exploitability**: Detecting a vulnerable algorithm does not
  claim the vulnerability is currently exploitable.
- **Detection ≠ Quantum Attack**: The engine identifies *usage*, not
  active exploitation. No quantum attack is performed.
- **Symmetric algorithms** (AES, ChaCha20) are **not** classified as
  broken by quantum computing. Grover's algorithm halves effective key
  length but does not break AES-256.
- **Hash functions** (SHA-256, SHA-3) are **not** classified as broken.
  Quantum attacks affect preimage resistance differently from collision
  resistance.
""")

# ── AI Assistant Behavior ────────────────────────────────────────────
st.markdown("---")
section_title("AI assistant behavior and limitations")

st.markdown("""
### When AI is Available

- Provides contextual analysis grounded in NIST standards.
- Summarizes findings in plain language.
- Drafts phased migration plans.
- Answers questions about the assessment.
- All output is labeled as a **recommendation requiring human review**.

### Security Controls

- AI **does not replace** deterministic cryptographic detection.
- AI **does not modify** risk scores without an explicit tested rule.
- AI **does not invent** compliance certifications.
- Uploaded data is **not sent** to an external provider unless the user
  explicitly configures the AI integration.
- Only summary statistics are sent to the model — not raw asset data.
- User-supplied text is treated as **untrusted input**, not instructions.
- API keys are stored in environment variables or Streamlit secrets,
  never in code or logs.

### When AI is Unavailable

- The application works fully without an AI API key.
- Rule-based fallback responses are provided for common queries.
- Detection, scoring, recommendations, and reporting all function
  independently of AI.

### Data Handling

- Imported files are processed in memory and stored in a local SQLite
  database.
- No data is sent to external services unless AI is explicitly enabled.
- The database is session-local on Streamlit Community Cloud.
- **Do not upload confidential production inventories to a public demo.**
""")

# ── Limitations ──────────────────────────────────────────────────────
st.markdown("---")
section_title("Known limitations")

st.markdown("""
1. **Prototype Status**: Q-Shield is a prototype assessment tool, not a
   production-ready enterprise security system.

2. **Rule-Based Detection**: The engine recognizes a defined set of
   algorithms. Unusual or vendor-specific algorithm names may not be
   recognized and will be flagged for manual review.

3. **No Live Scanning**: The current version assesses declared
   configurations, not live network traffic or running services.

4. **Score Precision**: Risk scores are approximate estimates for
   migration planning. They should not be treated as precise
   measurements of security posture.

5. **No Multi-Tenancy**: The demo deployment does not provide
   isolation between users. Do not upload sensitive data.

6. **AI Limitations**: AI recommendations may be incomplete or
   imprecise. They always require human review.

7. **Standard Evolution**: NIST standards and guidance may be updated.
   The reference set should be periodically refreshed.
""")

# Load and display standards JSON if available
st.markdown("---")
section_title("Standards reference data")

json_path = os.path.join(os.path.dirname(__file__), "..", "data", "standards_reference.json")
json_path = os.path.normpath(json_path)

if os.path.exists(json_path):
    with open(json_path, "r") as f:
        standards_data = json.load(f)

    with st.expander("📖 Full Standards Reference (JSON)", expanded=False):
        for std in standards_data.get("standards", []):
            st.markdown(f"**{std['id']}: {std['title']}**")
            st.caption(f"Organization: {std.get('organization', 'N/A')} · Status: {std.get('status', 'N/A')}")
            st.markdown(f"URL: [{std['url']}]({std['url']})")
            if std.get("notes"):
                st.markdown(f"*{std['notes']}*")
            st.markdown("")

    # Quantum threat summary
    threat = standards_data.get("quantum_threat_summary", {})
    if threat:
        with st.expander("⚛️ Quantum Threat Summary", expanded=False):
            shor = threat.get("shors_algorithm", {})
            if shor:
                st.markdown(f"**Shor's Algorithm:** {shor.get('description', '')}")
                st.markdown(f"- Affects: `{', '.join(shor.get('affects', []))}`")
                st.markdown(f"- Does not affect: `{', '.join(shor.get('does_not_affect', []))}`")

            grover = threat.get("grovers_algorithm", {})
            if grover:
                st.markdown(f"**Grover's Algorithm:** {grover.get('description', '')}")
                st.markdown(f"- Impact on symmetric: {grover.get('impact_on_symmetric', '')}")
                st.markdown(f"- Impact on hashing: {grover.get('impact_on_hashing', '')}")
