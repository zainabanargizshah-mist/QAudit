# 🛡️ Q-Shield — Quantum-Readiness Intelligence for Enterprise Security

**AI-Assisted Quantum-Readiness Assessment and PQC Migration Planner**

Q-Shield helps organizations prepare for post-quantum cryptography (PQC) by maintaining a declared cryptographic inventory, identifying algorithms that require quantum-readiness review, calculating an explainable migration-priority heuristic, and generating advisory planning guidance aligned with NIST PQC references.

> ⚠️ **This is a prototype assessment and planning tool, not an automated production migration system.** All findings are decision-support estimates requiring human review. Do not upload confidential production inventories to a public demo.

---

## Features

| Feature | Description |
|---------|-------------|
| **Declared Inventory** | Import, browse, filter, add, edit, and export declared cryptographic asset records (CSV/JSON) with provenance |
| **Detection Engine** | Deterministic, versioned rule-based classification of declared algorithm labels |
| **Migration-Priority Scoring** | Transparent 0–100 planning heuristic with configurable weights and full breakdowns |
| **Migration Planner** | Phased advisory guidance aligned with NIST FIPS 203, 204, 205 |
| **AI Assistant** | Optional provider-labeled LLM advisory with a clearly marked rule-based fallback |
| **Professional Reports** | PDF and CSV exports generated from live assessment data |
| **Methodology Reference** | Full documentation of scoring, detection rules, standards, and limitations |

## Technology Stack

- **Language:** Python 3.12
- **Frontend:** Streamlit
- **Data Processing:** Pandas
- **Storage:** SQLite (with abstraction layer)
- **Visualizations:** Plotly
- **PDF Generation:** fpdf2
- **AI Integration:** OpenAI API (optional)
- **Testing:** pytest
- **CI:** GitHub Actions

## Quick Start

### Prerequisites

- Python 3.11 or compatible version
- pip

### Installation

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/q-shield.git
cd q-shield

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
```

### Run Locally

```bash
streamlit run app.py
```

The app opens at `http://localhost:8501`. Click **＋ Load demo data** to populate a local prototype workspace with synthetic financial-system records. These are declared demo records, not discovered assets.

### Demo Login

The local prototype includes a built-in login for judge presentations:

```text
Username: judge
Password: qshield-demo
```

This is a presentation-only session gate, not production authentication. It has no user database, roles, tenant isolation, password reset, or enterprise identity integration. The defaults can be overridden locally with `QSHIELD_DEMO_USERNAME` and `QSHIELD_DEMO_PASSWORD`. For a shared or production deployment, replace it with an identity provider and disable the built-in demo credentials.

### Run Tests

```bash
python -m pytest tests/ -v
```

## Project Structure

```
q-shield/
├── app.py                          # Main entry point — Overview dashboard
├── requirements.txt                # Pinned dependencies
├── README.md
├── .gitignore
├── .env.example                    # Environment variable template
├── pages/
│   ├── 1_Asset_Inventory.py        # Asset management page
│   ├── 2_Risk_Assessment.py        # Detection & risk scoring page
│   ├── 3_Migration_Planner.py      # PQC migration recommendations
│   ├── 4_Reports.py                # PDF/CSV report exports
│   └── 5_Methodology.py            # Standards & methodology reference
├── qshield/
│   ├── __init__.py                 # Package metadata
│   ├── models.py                   # Data models & enumerations
│   ├── database.py                 # SQLite abstraction layer
│   ├── validation.py               # Input validation & sanitization
│   ├── detection.py                # Cryptographic detection engine
│   ├── risk_engine.py              # Explainable risk scoring
│   ├── inventory.py                # Asset inventory management
│   ├── recommendations.py          # Migration recommendations
│   ├── ai_assistant.py             # Optional AI integration
│   └── reporting.py                # PDF/CSV report generation
├── data/
│   ├── demo_assets.csv             # Synthetic demo dataset (15 assets)
│   └── standards_reference.json    # NIST PQC standards reference
├── tests/
│   ├── test_detection.py           # Detection engine tests
│   ├── test_risk_engine.py         # Risk scoring tests
│   ├── test_inventory.py           # Inventory & database tests
│   └── test_validation.py          # Input validation tests
├── .streamlit/
│   └── config.toml                 # Streamlit theme configuration
└── .github/
    └── workflows/
        └── tests.yml               # CI test workflow
```

## Optional AI Configuration

The app works fully without an AI API key. The Migration Planner uses Google Gemini when `GEMINI_API_KEY` is configured. OpenAI remains available as a fallback provider.

### Local Development

Create a `.env` file (never commit this):

```bash
cp .env.example .env
# Edit .env and set GEMINI_API_KEY to your Google AI Studio key
```

### Streamlit Community Cloud

Add secrets in the Streamlit dashboard:

1. Go to your app's **Settings → Secrets**
2. Add:
   ```toml
   GEMINI_API_KEY = "your-gemini-api-key"
   ```

## Deploy to Streamlit Community Cloud

1. Push this repository to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Click **New app** → select your repo
4. Set **Main file path** to `app.py`
5. (Optional) Add `GEMINI_API_KEY` in **Advanced settings → Secrets**
6. Click **Deploy**

No Docker or paid infrastructure required.

## Migration-Priority Methodology

Scores are weighted sums of normalized factors (0–100). They are planning heuristics, not probabilities, compliance ratings, CVSS scores, or NIST classifications:

| Factor | Weight | Description |
|--------|--------|-------------|
| Cryptographic Exposure | 30% | Quantum vulnerability of the algorithm |
| Data Sensitivity & Retention | 25% | Data classification + harvest-now-decrypt-later risk |
| Business Criticality | 20% | Impact if compromised |
| Internet Exposure | 10% | Public-facing vs. internal |
| Dependency Complexity | 10% | Number of dependent systems |
| Evidence Confidence | 5% | Uncertainty penalty for incomplete data |

**Priority Bands:** Critical [80,100], High [60,80), Medium [35,60), Low [0,35)

These are prototype defaults, not official NIST classifications.

## Detection Rules

| Category | Algorithms | Classification |
|----------|-----------|---------------|
| Asymmetric (Vulnerable) | RSA, ECDH, ECDHE, ECDSA, EdDSA, DH, DSA | Quantum-vulnerable (Shor's algorithm) |
| PQC Standards | ML-KEM (FIPS 203), ML-DSA (FIPS 204), SLH-DSA (FIPS 205) | Post-quantum secure |
| Symmetric | AES-256, AES-128, ChaCha20, 3DES | Not broken by quantum computing |
| Hash | SHA-256, SHA-3, SHA-512, SHA-1, MD5 | Not broken by quantum computing |
| Hybrid | Classical + PQC combinations | Transition — needs verification |
| Unknown | Unrecognized algorithms | Needs manual review |

## Standards References

- **FIPS 203:** ML-KEM for key encapsulation — [csrc.nist.gov/pubs/fips/203/final](https://csrc.nist.gov/pubs/fips/203/final)
- **FIPS 204:** ML-DSA for digital signatures — [csrc.nist.gov/pubs/fips/204/final](https://csrc.nist.gov/pubs/fips/204/final)
- **FIPS 205:** SLH-DSA for hash-based signatures — [csrc.nist.gov/pubs/fips/205/final](https://csrc.nist.gov/pubs/fips/205/final)
- **NIST IR 8547:** Transition to PQC Standards — [csrc.nist.gov/pubs/ir/8547/final](https://csrc.nist.gov/pubs/ir/8547/final)
- **OWASP A02:2021:** Cryptographic Failures — [owasp.org/Top10/A02_2021](https://owasp.org/Top10/A02_2021-Cryptographic_Failures/)

## Known Limitations

1. **Declared inventory only** — no live discovery or runtime verification
2. **Prototype status** — not a production enterprise security system
3. **Rule-based detection** — recognizes a defined set of algorithms; unusual names flagged for review
4. **No live scanning** — assesses declared configurations, not live traffic
5. **Score precision** — approximate estimates for planning, not precise measurements
6. **No multi-tenancy** — demo deployment does not isolate user data
7. **Migration status is owner-reported** — “Completed” is not verified by Q-Shield
8. **AI limitations** — AI recommendations may be incomplete; always require human review
9. **Standard evolution** — NIST guidance may be updated; reference set should be refreshed periodically

## License

This project is provided for educational and assessment-planning purposes.

---

*Q-Shield — Quantum-Readiness Intelligence for Enterprise Security*
*Track: Cybersecurity*
