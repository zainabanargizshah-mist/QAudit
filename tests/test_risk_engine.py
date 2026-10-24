"""
Tests for the risk scoring engine.
"""

import pytest
from qshield.risk_engine import compute_risk_score
from qshield.detection import analyze_asset
from qshield.models import DetectionFinding, DEFAULT_SCORING_CONFIG


def _make_asset(**overrides):
    """Create a test asset dict with defaults."""
    base = {
        "asset_id": "TEST-001",
        "asset_name": "Test Asset",
        "asset_type": "API",
        "cryptographic_algorithm": "RSA-2048",
        "cryptographic_purpose": "Key Establishment",
        "data_sensitivity": "Internal",
        "data_retention_years": 1,
        "business_criticality": "Medium",
        "internet_exposed": False,
        "dependency_count": 0,
        "migration_status": "Not Started",
    }
    base.update(overrides)
    return base


class TestScoreRange:
    """Verify scores stay within 0-100 range."""

    def test_minimum_score(self):
        asset = _make_asset(
            cryptographic_algorithm="AES-256",
            cryptographic_purpose="Encryption",
            data_sensitivity="Public",
            data_retention_years=1,
            business_criticality="Low",
            internet_exposed=False,
            dependency_count=0,
        )
        finding = analyze_asset(asset)
        score = compute_risk_score(asset, finding)
        assert 0 <= score.total_score <= 100
        assert score.total_score < 35  # Should be Low risk

    def test_maximum_score(self):
        asset = _make_asset(
            cryptographic_algorithm="RSA-2048",
            cryptographic_purpose="Key Establishment",
            data_sensitivity="Restricted",
            data_retention_years=30,
            business_criticality="Critical",
            internet_exposed=True,
            dependency_count=25,
        )
        finding = analyze_asset(asset)
        score = compute_risk_score(asset, finding)
        assert 0 <= score.total_score <= 100
        assert score.total_score >= 80  # Should be Critical


class TestCryptoExposureImpact:
    """Verify cryptographic exposure drives scores correctly."""

    def test_vulnerable_higher_than_safe(self):
        asset_vuln = _make_asset(cryptographic_algorithm="RSA-2048", cryptographic_purpose="Key Establishment")
        asset_safe = _make_asset(cryptographic_algorithm="AES-256", cryptographic_purpose="Encryption")

        finding_vuln = analyze_asset(asset_vuln)
        finding_safe = analyze_asset(asset_safe)

        score_vuln = compute_risk_score(asset_vuln, finding_vuln)
        score_safe = compute_risk_score(asset_safe, finding_safe)

        assert score_vuln.total_score > score_safe.total_score

    def test_pqc_lower_than_vulnerable(self):
        asset_pqc = _make_asset(cryptographic_algorithm="ML-KEM-768", cryptographic_purpose="Key Establishment")
        asset_vuln = _make_asset(cryptographic_algorithm="RSA-2048", cryptographic_purpose="Key Establishment")

        finding_pqc = analyze_asset(asset_pqc)
        finding_vuln = analyze_asset(asset_vuln)

        score_pqc = compute_risk_score(asset_pqc, finding_pqc)
        score_vuln = compute_risk_score(asset_vuln, finding_vuln)

        assert score_pqc.total_score < score_vuln.total_score


class TestDataSensitivityImpact:
    """Verify data sensitivity affects scores."""

    def test_restricted_higher_than_public(self):
        asset_high = _make_asset(data_sensitivity="Restricted", data_retention_years=25)
        asset_low = _make_asset(data_sensitivity="Public", data_retention_years=1)

        finding_high = analyze_asset(asset_high)
        finding_low = analyze_asset(asset_low)

        score_high = compute_risk_score(asset_high, finding_high)
        score_low = compute_risk_score(asset_low, finding_low)

        assert score_high.total_score > score_low.total_score

    def test_long_retention_increases_score(self):
        asset_long = _make_asset(data_retention_years=30)
        asset_short = _make_asset(data_retention_years=1)

        finding = analyze_asset(asset_long)

        score_long = compute_risk_score(asset_long, finding)
        score_short = compute_risk_score(asset_short, finding)

        assert score_long.total_score > score_short.total_score


class TestBusinessCriticalityImpact:
    """Verify business criticality affects scores."""

    def test_critical_higher_than_low(self):
        asset_crit = _make_asset(business_criticality="Critical")
        asset_low = _make_asset(business_criticality="Low")

        finding = analyze_asset(asset_crit)

        score_crit = compute_risk_score(asset_crit, finding)
        score_low = compute_risk_score(asset_low, finding)

        assert score_crit.total_score > score_low.total_score


class TestInternetExposureImpact:
    """Verify internet exposure affects scores."""

    def test_exposed_higher_than_internal(self):
        asset_exposed = _make_asset(internet_exposed=True)
        asset_internal = _make_asset(internet_exposed=False)

        finding = analyze_asset(asset_exposed)

        score_exposed = compute_risk_score(asset_exposed, finding)
        score_internal = compute_risk_score(asset_internal, finding)

        assert score_exposed.total_score > score_internal.total_score


class TestUncertaintyHandling:
    """Verify that incomplete evidence increases risk, not decreases it."""

    def test_unknown_algo_gets_uncertainty_penalty(self):
        asset = _make_asset(cryptographic_algorithm="UnknownAlgo")
        finding = analyze_asset(asset)
        score = compute_risk_score(asset, finding)

        assert score.needs_review is True
        assert finding.confidence == "Low"
        # Uncertainty should push score up, not down
        assert score.total_score > 0

    def test_empty_algo_needs_review(self):
        asset = _make_asset(cryptographic_algorithm="")
        finding = analyze_asset(asset)
        score = compute_risk_score(asset, finding)

        assert score.needs_review is True


class TestRiskBands:
    """Verify risk band classifications."""

    def test_critical_band(self):
        asset = _make_asset(
            cryptographic_algorithm="RSA-2048",
            data_sensitivity="Restricted",
            data_retention_years=30,
            business_criticality="Critical",
            internet_exposed=True,
            dependency_count=25,
        )
        finding = analyze_asset(asset)
        score = compute_risk_score(asset, finding)
        assert score.risk_level == "Critical"

    def test_low_band(self):
        asset = _make_asset(
            cryptographic_algorithm="AES-256",
            cryptographic_purpose="Encryption",
            data_sensitivity="Public",
            data_retention_years=1,
            business_criticality="Low",
            internet_exposed=False,
            dependency_count=0,
        )
        finding = analyze_asset(asset)
        score = compute_risk_score(asset, finding)
        assert score.risk_level == "Low"


class TestScoreExplanation:
    """Verify score results include explanations and actions."""

    def test_has_explanation(self):
        asset = _make_asset()
        finding = analyze_asset(asset)
        score = compute_risk_score(asset, finding)

        assert score.explanation != ""
        assert len(score.explanation) > 20

    def test_has_top_factors(self):
        asset = _make_asset()
        finding = analyze_asset(asset)
        score = compute_risk_score(asset, finding)

        assert len(score.top_factors) > 0

    def test_has_suggested_actions(self):
        asset = _make_asset()
        finding = analyze_asset(asset)
        score = compute_risk_score(asset, finding)

        assert len(score.suggested_actions) > 0

    def test_has_breakdown(self):
        asset = _make_asset()
        finding = analyze_asset(asset)
        score = compute_risk_score(asset, finding)

        assert "crypto_exposure" in score.breakdown
        assert "data_sensitivity_retention" in score.breakdown
        assert "business_criticality" in score.breakdown


class TestScoreReproducibility:
    """Verify scores are deterministic."""

    def test_same_input_same_score(self):
        asset = _make_asset()
        finding = analyze_asset(asset)

        score1 = compute_risk_score(asset, finding)
        score2 = compute_risk_score(asset, finding)

        assert score1.total_score == score2.total_score
        assert score1.risk_level == score2.risk_level
