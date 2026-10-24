"""
Explainable risk-scoring engine for Q-Shield.

Computes a transparent risk score from 0-100 for each asset based on
configurable weights and normalized inputs. Every score includes a
breakdown, explanation, top factors, and suggested actions.

These scores are decision-support estimates for migration planning.
They are NOT certified security ratings or official NIST classifications.
"""

from typing import Dict, List, Tuple
from qshield.models import (
    RiskScoreResult, DetectionFinding, DEFAULT_SCORING_CONFIG,
    DataSensitivity, BusinessCriticality,
)


def compute_risk_score(
    asset: dict,
    finding: DetectionFinding,
    config: dict = None,
) -> RiskScoreResult:
    """
    Compute an explainable risk score for a single asset given its
    detection finding.
    """
    cfg = config or DEFAULT_SCORING_CONFIG
    weights = cfg["weights"]
    bands = cfg["risk_bands"]

    # ── Normalize each factor to 0.0 – 1.0 ──────────────────────────

    # 1. Cryptographic exposure (0-1)
    crypto_score = _score_crypto_exposure(finding)

    # 2. Data sensitivity + retention (0-1)
    data_score = _score_data_sensitivity(asset)

    # 3. Business criticality (0-1)
    biz_score = _score_business_criticality(asset)

    # 4. Internet exposure (0 or 1)
    internet_score = 1.0 if _is_exposed(asset) else 0.0

    # 5. Dependency / migration complexity (0-1)
    dep_score = _score_dependency_complexity(asset)

    # 6. Evidence confidence penalty (0-1, higher = less confident = more risk)
    confidence_score = _score_confidence_uncertainty(finding)

    # ── Weighted combination ─────────────────────────────────────────

    components = {
        "crypto_exposure": (crypto_score, weights["crypto_exposure"]),
        "data_sensitivity_retention": (data_score, weights["data_sensitivity_retention"]),
        "business_criticality": (biz_score, weights["business_criticality"]),
        "internet_exposure": (internet_score, weights["internet_exposure"]),
        "dependency_complexity": (dep_score, weights["dependency_complexity"]),
        "evidence_confidence": (confidence_score, weights["evidence_confidence"]),
    }

    total = sum(score * weight for score, weight in components.values()) * 100
    total = max(0.0, min(100.0, round(total, 1)))

    # ── Determine risk level ─────────────────────────────────────────

    risk_level = "Unknown"
    for level, (low, high) in bands.items():
        if low <= total <= high:
            risk_level = level
            break

    # ── Build breakdown ──────────────────────────────────────────────

    breakdown = {}
    for name, (score, weight) in components.items():
        breakdown[name] = {
            "raw_score": round(score, 2),
            "weight": weight,
            "weighted_contribution": round(score * weight * 100, 1),
        }

    # ── Top factors ──────────────────────────────────────────────────

    sorted_factors = sorted(
        breakdown.items(),
        key=lambda x: x[1]["weighted_contribution"],
        reverse=True,
    )
    top_factors = [
        f"{_format_factor_name(name)}: {info['weighted_contribution']:.1f} points "
        f"(score {info['raw_score']:.0%} × weight {info['weight']:.0%})"
        for name, info in sorted_factors[:3]
    ]

    # ── Explanation ──────────────────────────────────────────────────

    explanation = _build_explanation(
        asset, finding, total, risk_level, sorted_factors
    )

    # ── Suggested actions ────────────────────────────────────────────

    actions = _build_actions(asset, finding, risk_level)

    # ── Needs review ─────────────────────────────────────────────────

    needs_review = finding.needs_review or finding.confidence == "Low"

    return RiskScoreResult(
        asset_id=asset.get("asset_id", ""),
        total_score=total,
        risk_level=risk_level,
        breakdown=breakdown,
        top_factors=top_factors,
        explanation=explanation,
        suggested_actions=actions,
        needs_review=needs_review,
    )


# ── Factor Scoring Functions ──────────────────────────────────────────

def _score_crypto_exposure(finding: DetectionFinding) -> float:
    """Score based on quantum vulnerability of the algorithm."""
    if finding.is_quantum_vulnerable:
        if finding.confidence == "High":
            return 1.0
        elif finding.confidence == "Medium":
            return 0.8
        return 0.6
    if finding.is_pqc:
        return 0.05  # PQC in use — minimal residual risk
    if finding.needs_review:
        return 0.5  # Unknown = moderate until reviewed
    return 0.1  # Symmetric/hash — low quantum risk


def _score_data_sensitivity(asset: dict) -> float:
    """Score based on data sensitivity and retention period."""
    sensitivity_map = {
        "Restricted": 1.0,
        "Confidential": 0.75,
        "Internal": 0.4,
        "Public": 0.1,
    }
    sens = sensitivity_map.get(asset.get("data_sensitivity", "Internal"), 0.4)

    retention = int(asset.get("data_retention_years", 1) or 1)
    # Long retention means harvest-now-decrypt-later risk
    if retention >= 25:
        ret_factor = 1.0
    elif retention >= 10:
        ret_factor = 0.8
    elif retention >= 5:
        ret_factor = 0.6
    elif retention >= 2:
        ret_factor = 0.3
    else:
        ret_factor = 0.1

    return (sens * 0.6 + ret_factor * 0.4)


def _score_business_criticality(asset: dict) -> float:
    """Score based on business criticality level."""
    crit_map = {
        "Critical": 1.0,
        "High": 0.75,
        "Medium": 0.45,
        "Low": 0.15,
    }
    return crit_map.get(asset.get("business_criticality", "Medium"), 0.45)


def _is_exposed(asset: dict) -> bool:
    """Check if asset is internet-exposed."""
    val = asset.get("internet_exposed", False)
    if isinstance(val, bool):
        return val
    if isinstance(val, int):
        return val == 1
    if isinstance(val, str):
        return val.strip().lower() in ("true", "yes", "1", "y")
    return False


def _score_dependency_complexity(asset: dict) -> float:
    """Score based on number of dependencies (proxy for migration complexity)."""
    deps = int(asset.get("dependency_count", 0) or 0)
    if deps >= 20:
        return 1.0
    elif deps >= 10:
        return 0.7
    elif deps >= 5:
        return 0.5
    elif deps >= 2:
        return 0.3
    return 0.1


def _score_confidence_uncertainty(finding: DetectionFinding) -> float:
    """
    Score uncertainty — lower confidence means higher risk because
    we cannot confirm the asset is safe.
    """
    if finding.needs_review:
        return 1.0  # Unknown status → maximum uncertainty risk
    if finding.confidence == "Low":
        return 0.8
    if finding.confidence == "Medium":
        return 0.4
    return 0.1  # High confidence → minimal uncertainty


# ── Explanation Builders ──────────────────────────────────────────────

def _format_factor_name(name: str) -> str:
    return name.replace("_", " ").title()

def _build_explanation(
    asset: dict, finding: DetectionFinding, total: float,
    risk_level: str, sorted_factors: list
) -> str:
    """Build a plain-language explanation of the risk score."""
    parts = [
        f"Risk score: {total}/100 ({risk_level}).",
    ]

    if finding.is_quantum_vulnerable:
        parts.append(
            f"The algorithm '{finding.algorithm}' used for "
            f"'{finding.purpose}' is potentially vulnerable to quantum "
            f"attack via {finding.vulnerability_type}."
        )
    elif finding.is_pqc:
        parts.append(
            f"The asset uses PQC algorithm '{finding.algorithm}'. "
            "While this is a positive indicator, complete quantum readiness "
            "requires verification of implementation and integration."
        )
    elif finding.needs_review:
        parts.append(
            "Insufficient evidence to determine quantum vulnerability. "
            "The score includes an uncertainty penalty."
        )
    else:
        parts.append(
            f"The algorithm '{finding.algorithm}' is not directly threatened "
            "by known quantum algorithms."
        )

    # Data sensitivity context
    sens = asset.get("data_sensitivity", "Internal")
    ret = asset.get("data_retention_years", 1)
    if sens in ("Restricted", "Confidential") and int(ret or 1) > 5:
        parts.append(
            f"Data sensitivity is '{sens}' with {ret}-year retention, "
            "increasing harvest-now-decrypt-later risk."
        )

    # Top factor
    if sorted_factors:
        top_name, top_info = sorted_factors[0]
        parts.append(
            f"Top contributing factor: {_format_factor_name(top_name)} "
            f"({top_info['weighted_contribution']:.1f} points)."
        )

    return " ".join(parts)


def _build_actions(
    asset: dict, finding: DetectionFinding, risk_level: str
) -> List[str]:
    """Build suggested actions based on finding and risk."""
    actions = []

    if finding.needs_review:
        actions.append("Complete cryptographic inventory for this asset.")
        actions.append("Identify exact algorithms, key sizes, and usage context.")

    if finding.is_quantum_vulnerable:
        if risk_level in ("Critical", "High"):
            actions.append("Prioritize for PQC migration assessment.")
        else:
            actions.append("Schedule PQC migration assessment.")
        if finding.recommendation:
            actions.append(finding.recommendation)

    if finding.is_pqc and finding.needs_review:
        actions.append("Verify PQC implementation correctness and interoperability.")

    if not finding.is_quantum_vulnerable and not finding.is_pqc and not finding.needs_review:
        actions.append("No PQC migration required. Monitor for updated guidance.")

    migration = asset.get("migration_status", "Not Started")
    if migration == "Not Started" and finding.is_quantum_vulnerable:
        actions.append("Begin migration assessment phase.")

    return actions


def compute_all_scores(
    assets: List[dict],
    findings: List[DetectionFinding],
    config: dict = None,
) -> List[RiskScoreResult]:
    """Compute risk scores for all assets with their findings."""
    finding_map = {f.asset_id: f for f in findings}
    results = []
    for asset in assets:
        aid = asset.get("asset_id", "")
        finding = finding_map.get(aid)
        if finding:
            results.append(compute_risk_score(asset, finding, config))
    return results
