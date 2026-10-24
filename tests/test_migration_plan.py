"""Tests for deterministic migration planning and AI response handling."""

from qshield.migration_plan import (
    build_ai_payload,
    build_independent_analysis,
    calculate_asset_progress,
    deterministic_plan,
    merge_ai_plan,
    parse_ai_plan,
)
from qshield.models import DetectionFinding, RiskScoreResult


def _asset(**overrides):
    asset = {
        "asset_id": "A-1",
        "asset_name": "Payments API",
        "asset_type": "API",
        "cryptographic_algorithm": "RSA-2048",
        "cryptographic_purpose": "Key Establishment",
        "migration_status": "Completed",
        "verification_status": "unverified",
        "data_sensitivity": "Restricted",
        "data_retention_years": 15,
        "business_criticality": "Critical",
        "internet_exposed": True,
        "dependency_count": 4,
    }
    asset.update(overrides)
    return asset


def test_completed_unverified_asset_is_not_100_percent():
    finding = DetectionFinding(asset_id="A-1", is_quantum_vulnerable=True)
    score = RiskScoreResult(asset_id="A-1", total_score=90, risk_level="Critical")
    assert calculate_asset_progress(_asset(), finding, score) == 85
    assert calculate_asset_progress(
        _asset(verification_status="verified"), finding, score
    ) == 100


def test_independent_analysis_maps_nist_and_owasp_controls():
    finding = DetectionFinding(
        asset_id="A-1",
        purpose="Key Establishment",
        is_quantum_vulnerable=True,
        needs_review=False,
        vulnerability_type="Shor threat",
    )
    score = RiskScoreResult(asset_id="A-1", total_score=90, risk_level="Critical")
    analysis = build_independent_analysis([_asset()], [finding], [score])
    row = analysis["assets"][0]

    assert row["nist_standard"] == "FIPS 203"
    assert row["target_algorithm"] == "ML-KEM"
    assert any(control["id"] == "OWASP-A02-CLASSICAL-PUBLIC-KEY" for control in row["owasp_controls"])
    assert analysis["overall_progress"] == 85


def test_ai_payload_can_redact_identity_fields():
    analysis = build_independent_analysis(
        [_asset()],
        [DetectionFinding(asset_id="A-1")],
        [RiskScoreResult(asset_id="A-1")],
    )
    payload = build_ai_payload(analysis, [_asset()], redact_identity=True)
    item = payload["inventory"][0]
    assert item["asset_id"] == "ASSET-1"
    assert item["asset_name"] == "Asset 1"
    assert item["owner"] == "redacted"
    assert item["cryptographic_algorithm"] == "RSA-2048"


def test_ai_json_is_parsed_and_deterministic_progress_is_preserved():
    analysis = build_independent_analysis(
        [_asset()],
        [DetectionFinding(asset_id="A-1", is_quantum_vulnerable=True)],
        [RiskScoreResult(asset_id="A-1", total_score=90, risk_level="Critical")],
    )
    raw = parse_ai_plan(
        "```json\n{\"title\": \"AI Plan\", \"executive_summary\": \"Review first.\"}\n```"
    )
    plan = merge_ai_plan(raw, analysis)
    assert plan["title"] == "AI Plan"
    assert plan["ai_generated"] is True
    assert plan["overall_progress"] == analysis["overall_progress"]
    assert deterministic_plan(analysis)["ai_generated"] is False
