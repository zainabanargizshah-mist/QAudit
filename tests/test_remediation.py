"""Regression tests for provenance, freshness, scoring boundaries, and safe exports."""

import os
import tempfile

import pandas as pd

from qshield.database import Database
from qshield.detection import analyze_asset, analyze_usages
from qshield.models import CryptographicAsset
from qshield.reporting import generate_csv_report
from qshield.risk_engine import risk_level_for_score
from qshield.validation import validate_dataframe


def test_score_bands_are_continuous():
    bands = {
        "Low": (0.0, 35.0),
        "Medium": (35.0, 60.0),
        "High": (60.0, 80.0),
        "Critical": (80.0, 100.0),
    }
    assert risk_level_for_score(34.9, bands) == "Low"
    assert risk_level_for_score(35.0, bands) == "Medium"
    assert risk_level_for_score(59.9, bands) == "Medium"
    assert risk_level_for_score(60.0, bands) == "High"
    assert risk_level_for_score(79.9, bands) == "High"
    assert risk_level_for_score(80.0, bands) == "Critical"


def test_duplicate_upload_ids_are_rejected():
    frame = pd.DataFrame([
        {"asset_id": "A-1", "asset_name": "One", "asset_type": "API", "cryptographic_algorithm": "RSA"},
        {"asset_id": "A-1", "asset_name": "Two", "asset_type": "API", "cryptographic_algorithm": "AES-256"},
    ])
    assets, errors = validate_dataframe(frame)
    assert len(assets) == 1
    assert any(error["field"] == "asset_id" and "Duplicate" in error["message"] for error in errors)


def test_multiple_crypto_usages_can_be_assessed():
    asset = {"asset_id": "A-1", "cryptographic_algorithm": "AES-256", "cryptographic_purpose": "Encryption"}
    findings = analyze_usages(asset, [
        {"algorithm": "AES-256", "purpose": "Encryption"},
        {"algorithm": "RSA-2048", "purpose": "Key Wrapping"},
    ])
    assert len(findings) == 2
    assert findings[0].is_quantum_vulnerable is False
    assert findings[1].is_quantum_vulnerable is True


def test_assessment_becomes_stale_after_asset_edit():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    try:
        db = Database(path)
        asset = CryptographicAsset(asset_id="A-1", asset_name="Original", cryptographic_algorithm="RSA-2048")
        db.upsert_asset(asset)
        finding = analyze_asset(asset.to_dict())
        db.save_assessment("A-1", finding.to_dict(), {"total_score": 70, "risk_level": "High"})
        asset.asset_name = "Edited"
        db.upsert_asset(asset)
        assessment = db.get_assessment("A-1")
        assert assessment is not None
        assert assessment["assessment_status"] == "stale"
    finally:
        os.unlink(path)


def test_csv_export_escapes_formula_cells():
    csv_text = generate_csv_report(
        [{"asset_id": "=BAD", "asset_name": "@formula", "cryptographic_algorithm": "AES-256"}],
        [],
        [],
    )
    assert "'=BAD" in csv_text
    assert "'@formula" in csv_text
