"""
Migration recommendations engine for Q-Shield.

Generates phased, standards-aligned migration recommendations for
each asset based on detection findings and risk scores.
"""

from typing import List, Dict
from qshield.models import (
    DetectionFinding, RiskScoreResult, NIST_PQC_STANDARDS, MigrationStatus,
)


MIGRATION_PHASES = [
    {
        "phase": 1,
        "name": "Inventory & Verification",
        "description": "Complete cryptographic inventory and verify algorithm usage.",
        "activities": [
            "Confirm cryptographic algorithms, key sizes, and protocols in use.",
            "Identify all certificate chains and trust relationships.",
            "Document data flows requiring cryptographic protection.",
        ],
    },
    {
        "phase": 2,
        "name": "Dependency Analysis",
        "description": "Identify dependencies and compatibility constraints.",
        "activities": [
            "Map upstream and downstream system dependencies.",
            "Identify vendor and partner protocol requirements.",
            "Assess regulatory and compliance constraints.",
        ],
    },
    {
        "phase": 3,
        "name": "Prioritization",
        "description": "Prioritize high-risk assets for migration.",
        "activities": [
            "Review risk scores and business criticality.",
            "Identify assets with harvest-now-decrypt-later exposure.",
            "Create prioritized migration queue.",
        ],
    },
    {
        "phase": 4,
        "name": "Testing & Validation",
        "description": "Test PQC or hybrid configurations in a controlled environment.",
        "activities": [
            "Set up isolated test environment.",
            "Implement candidate PQC algorithms.",
            "Measure performance impact (latency, bandwidth, key sizes).",
        ],
    },
    {
        "phase": 5,
        "name": "Interoperability Verification",
        "description": "Validate interoperability with dependent systems.",
        "activities": [
            "Test with partner and vendor systems.",
            "Verify certificate chain compatibility.",
            "Validate protocol version support.",
        ],
    },
    {
        "phase": 6,
        "name": "Staged Deployment",
        "description": "Plan staged deployment with rollback capability.",
        "activities": [
            "Deploy to staging/canary environment.",
            "Monitor for errors and performance regression.",
            "Prepare rollback procedures.",
            "Deploy to production with monitoring.",
        ],
    },
    {
        "phase": 7,
        "name": "Verification & Update",
        "description": "Verify results and update the inventory.",
        "activities": [
            "Confirm PQC algorithms are correctly deployed.",
            "Update cryptographic inventory records.",
            "Document lessons learned.",
            "Schedule periodic re-assessment.",
        ],
    },
]


def generate_recommendation(
    asset: dict,
    finding: DetectionFinding,
    score: RiskScoreResult,
) -> Dict:
    """Generate a migration recommendation for a single asset."""
    rec = {
        "asset_id": asset.get("asset_id", ""),
        "asset_name": asset.get("asset_name", ""),
        "current_algorithm": finding.algorithm,
        "current_purpose": finding.purpose,
        "identified_concern": finding.vulnerability_type,
        "risk_priority": score.risk_level,
        "risk_score": score.total_score,
        "needs_review": score.needs_review or finding.needs_review,
        "migration_status": asset.get("migration_status", "Not Started"),
        "suggested_actions": [],
        "target_standard": "",
        "target_algorithm": "",
        "dependencies": f"{asset.get('dependency_count', 0)} dependent systems identified",
        "validation_requirements": [],
        "testing_requirements": [],
    }

    # Determine target based on purpose
    if finding.is_quantum_vulnerable:
        purpose = finding.purpose.lower() if finding.purpose else ""
        if "key" in purpose or "establishment" in purpose or "encryption" in purpose or "wrapping" in purpose:
            rec["target_standard"] = "FIPS 203"
            rec["target_algorithm"] = "ML-KEM (Module-Lattice-Based Key-Encapsulation Mechanism)"
            rec["suggested_actions"] = [
                "Evaluate ML-KEM parameter sets (ML-KEM-512, ML-KEM-768, ML-KEM-1024).",
                "Consider hybrid classical/ML-KEM during transition period.",
                "Test key encapsulation performance and ciphertext sizes.",
                finding.recommendation,
            ]
            rec["validation_requirements"] = [
                "Verify key sizes and ciphertext sizes are compatible with protocols.",
                "Test TLS handshake with ML-KEM if applicable.",
                "Validate interoperability with partner systems.",
            ]
        elif "sign" in purpose or "signature" in purpose:
            rec["target_standard"] = "FIPS 204 / FIPS 205"
            rec["target_algorithm"] = "ML-DSA or SLH-DSA"
            rec["suggested_actions"] = [
                "Evaluate ML-DSA (FIPS 204) for general digital signatures.",
                "Consider SLH-DSA (FIPS 205) for conservative, hash-based signatures.",
                "Assess signature size impact on bandwidth and storage.",
                finding.recommendation,
            ]
            rec["validation_requirements"] = [
                "Verify signature sizes are acceptable for the protocol.",
                "Test certificate chain with PQC signatures.",
                "Validate document signature format compatibility.",
            ]
        else:
            rec["target_standard"] = "Determine based on usage context"
            rec["target_algorithm"] = "Depends on purpose: ML-KEM for key establishment, ML-DSA/SLH-DSA for signatures"
            rec["suggested_actions"] = [
                "Clarify whether the algorithm is used for key establishment or signatures.",
                finding.recommendation,
            ]

        rec["testing_requirements"] = [
            "Performance benchmarking (latency, throughput).",
            "Key/signature size compatibility testing.",
            "Rollback procedure verification.",
            "Integration testing with dependent systems.",
        ]

    elif finding.is_pqc:
        rec["identified_concern"] = "PQC algorithm in use — verify implementation"
        rec["suggested_actions"] = [
            "Verify PQC implementation follows the referenced NIST standard.",
            "Confirm interoperability with all dependent systems.",
            "Document the PQC deployment for the cryptographic inventory.",
        ]
        rec["validation_requirements"] = [
            "Implementation correctness review.",
            "Interoperability verification.",
        ]
        rec["testing_requirements"] = [
            "Functional testing of PQC integration.",
            "Performance monitoring.",
        ]

    elif finding.needs_review:
        rec["suggested_actions"] = [
            "Complete cryptographic audit to identify algorithms in use.",
            "Document key sizes, protocols, and usage context.",
            "Re-run assessment after inventory update.",
        ]
        rec["validation_requirements"] = [
            "Full cryptographic inventory verification.",
        ]

    else:
        # Symmetric / hash — no PQC migration needed
        rec["identified_concern"] = finding.vulnerability_type
        rec["suggested_actions"] = [finding.recommendation] if finding.recommendation else [
            "No PQC migration required. Continue monitoring for updated guidance."
        ]
        rec["validation_requirements"] = [
            "Periodic review of algorithm strength against updated guidance.",
        ]

    return rec


def generate_all_recommendations(
    assets: List[dict],
    findings: List[DetectionFinding],
    scores: List[RiskScoreResult],
) -> List[Dict]:
    """Generate recommendations for all assessed assets."""
    finding_map = {f.asset_id: f for f in findings}
    score_map = {s.asset_id: s for s in scores}

    recs = []
    for asset in assets:
        aid = asset.get("asset_id", "")
        finding = finding_map.get(aid)
        score_result = score_map.get(aid)
        if finding and score_result:
            recs.append(generate_recommendation(asset, finding, score_result))

    # Sort by risk score descending
    recs.sort(key=lambda r: r.get("risk_score", 0), reverse=True)
    return recs


def get_migration_phases() -> List[Dict]:
    """Return the migration phase framework."""
    return MIGRATION_PHASES
