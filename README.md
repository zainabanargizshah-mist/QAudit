# 🛡️ Q-Shield — Quantum-Readiness Intelligence for Enterprise Security

**AI-Assisted Quantum-Readiness Assessment and PQC Migration Planner**

Q-Shield helps organizations prepare for post-quantum cryptography (PQC) by building a cryptographic asset inventory, identifying quantum-vulnerable algorithms, scoring risk transparently, and generating migration recommendations aligned with NIST PQC standards.

> ⚠️ **This is a prototype assessment and planning tool, not an automated production migration system.** All findings are decision-support estimates requiring human review. Do not upload confidential production inventories to a public demo.

---

## Features

| Feature | Description |
|---------|-------------|
| **Cryptographic Inventory** | Import, browse, filter, add, edit, and export cryptographic assets (CSV/JSON) |
| **Detection Engine** | Deterministic, rule-based classification of algorithms by quantum vulnerability |
| **Explainable Risk Scoring** | Transparent 0–100 scores with configurable weights and full breakdowns |
| **Migration Planner** | Phased recommendations aligned with NIST FIPS 203, 204, 205 |
| **AI Assistant** | Optional LLM-powered analysis grounded in NIST standards (works without API key) |
| **Professional Reports** | PDF and CSV exports generated from live assessment data |
| **Methodology Reference** | Full documentation of scoring, detection rules, standards, and limitations |

## Technology Stack

- **Language:** Python 3.11+
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

The app opens at `http://localhost:8501`. Click **📥 Load Demo Data** in the sidebar to populate with synthetic financial-system assets.

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

## Risk Scoring Methodology

Scores are weighted sums of normalized factors (0–100):

| Factor | Weight | Description |
|--------|--------|-------------|
| Cryptographic Exposure | 30% | Quantum vulnerability of the algorithm |
| Data Sensitivity & Retention | 25% | Data classification + harvest-now-decrypt-later risk |
| Business Criticality | 20% | Impact if compromised |
| Internet Exposure | 10% | Public-facing vs. internal |
| Dependency Complexity | 10% | Number of dependent systems |
| Evidence Confidence | 5% | Uncertainty penalty for incomplete data |

**Risk Bands:** Critical (80–100), High (60–79), Medium (35–59), Low (0–34)

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

1. **Prototype status** — not a production enterprise security system
2. **Rule-based detection** — recognizes a defined set of algorithms; unusual names flagged for review
3. **No live scanning** — assesses declared configurations, not live traffic
4. **Score precision** — approximate estimates for planning, not precise measurements
5. **No multi-tenancy** — demo deployment does not isolate user data
6. **AI limitations** — AI recommendations may be incomplete; always require human review
7. **Standard evolution** — NIST guidance may be updated; reference set should be refreshed periodically

## License

This project is provided for educational and assessment-planning purposes.

---

*Q-Shield — Quantum-Readiness Intelligence for Enterprise Security*
*Track: Cybersecurity*
