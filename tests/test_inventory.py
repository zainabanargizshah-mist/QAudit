"""
Tests for inventory management and validation.
"""

import pytest
import os
import json
import tempfile

from qshield.inventory import load_demo_assets, import_assets_to_db, get_assets_dataframe
from qshield.validation import (
    validate_file_upload, validate_dataframe, validate_single_asset, sanitize_text,
)
from qshield.database import Database
from qshield.models import CryptographicAsset


@pytest.fixture
def tmp_db():
    """Create a temporary database for testing."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    db = Database(db_path=path)
    yield db
    os.unlink(path)


class TestDemoAssets:
    """Test demo dataset loading."""

    def test_load_demo_assets(self):
        assets = load_demo_assets()
        assert len(assets) > 0
        assert all(isinstance(a, CryptographicAsset) for a in assets)

    def test_demo_has_varied_algorithms(self):
        assets = load_demo_assets()
        algos = {a.cryptographic_algorithm for a in assets}
        assert len(algos) >= 5  # Should have variety

    def test_demo_has_varied_criticality(self):
        assets = load_demo_assets()
        crits = {a.business_criticality for a in assets}
        assert len(crits) >= 3

    def test_demo_has_pqc_asset(self):
        assets = load_demo_assets()
        pqc = [a for a in assets if "ML-KEM" in a.cryptographic_algorithm or "ML-DSA" in a.cryptographic_algorithm]
        assert len(pqc) >= 1

    def test_demo_import_to_db(self, tmp_db):
        assets = load_demo_assets()
        count = import_assets_to_db(tmp_db, assets, source="test")
        assert count == len(assets)
        assert tmp_db.asset_count() == len(assets)


class TestCSVValidation:
    """Test CSV upload validation."""

    def test_valid_csv(self):
        csv_content = (
            "asset_id,asset_name,asset_type,cryptographic_algorithm\n"
            "A-001,Test,API,RSA-2048\n"
        ).encode()
        valid, msg, df = validate_file_upload(csv_content, "test.csv")
        assert valid is True
        assert df is not None
        assert len(df) == 1

    def test_invalid_extension(self):
        valid, msg, df = validate_file_upload(b"data", "test.xlsx")
        assert valid is False
        assert "Unsupported" in msg

    def test_empty_csv(self):
        csv_content = "asset_id,asset_name\n".encode()
        valid, msg, df = validate_file_upload(csv_content, "test.csv")
        assert valid is False
        assert "no data" in msg.lower()

    def test_oversized_file(self):
        # Create a file larger than max
        big_data = b"x" * (11 * 1024 * 1024)  # 11 MB
        valid, msg, df = validate_file_upload(big_data, "test.csv")
        assert valid is False
        assert "large" in msg.lower()

    def test_malformed_csv(self):
        bad_csv = b'\x00\x01\x02\x03'
        valid, msg, df = validate_file_upload(bad_csv, "test.csv")
        # Should either fail parsing or produce no valid rows
        # The behavior depends on pandas, but it should not crash
        assert isinstance(valid, bool)


class TestJSONValidation:
    """Test JSON upload validation."""

    def test_valid_json_array(self):
        data = json.dumps([{
            "asset_id": "J-001",
            "asset_name": "JSON Test",
            "asset_type": "API",
            "cryptographic_algorithm": "RSA-2048",
        }]).encode()
        valid, msg, df = validate_file_upload(data, "test.json")
        assert valid is True
        assert len(df) == 1

    def test_valid_json_object(self):
        data = json.dumps({"assets": [{
            "asset_id": "J-002",
            "asset_name": "JSON Test 2",
            "asset_type": "Database",
            "cryptographic_algorithm": "AES-256",
        }]}).encode()
        valid, msg, df = validate_file_upload(data, "test.json")
        assert valid is True

    def test_invalid_json(self):
        valid, msg, df = validate_file_upload(b"{bad json", "test.json")
        assert valid is False
        assert "parse" in msg.lower() or "failed" in msg.lower()


class TestDataFrameValidation:
    """Test individual row validation."""

    def test_missing_required_field(self):
        import pandas as pd
        df = pd.DataFrame([{
            "asset_id": "",
            "asset_name": "No ID",
            "asset_type": "API",
            "cryptographic_algorithm": "RSA",
        }])
        assets, errors = validate_dataframe(df)
        assert len(errors) > 0
        assert any("asset_id" in e["field"] for e in errors)

    def test_valid_row(self):
        import pandas as pd
        df = pd.DataFrame([{
            "asset_id": "V-001",
            "asset_name": "Valid",
            "asset_type": "API",
            "cryptographic_algorithm": "RSA-2048",
        }])
        assets, errors = validate_dataframe(df)
        assert len(assets) == 1
        assert len(errors) == 0

    def test_negative_retention(self):
        import pandas as pd
        df = pd.DataFrame([{
            "asset_id": "N-001",
            "asset_name": "Negative",
            "asset_type": "API",
            "cryptographic_algorithm": "RSA",
            "data_retention_years": "-5",
        }])
        assets, errors = validate_dataframe(df)
        assert len(errors) > 0


class TestSingleAssetValidation:
    """Test single asset validation for add/edit forms."""

    def test_valid_asset(self):
        data = {
            "asset_id": "S-001",
            "asset_name": "Single",
            "asset_type": "API",
            "cryptographic_algorithm": "RSA-2048",
        }
        valid, issues = validate_single_asset(data)
        assert valid is True
        assert len(issues) == 0

    def test_missing_name(self):
        data = {
            "asset_id": "S-002",
            "asset_name": "",
            "asset_type": "API",
            "cryptographic_algorithm": "RSA",
        }
        valid, issues = validate_single_asset(data)
        assert valid is False


class TestSanitization:
    """Test text sanitization."""

    def test_removes_html(self):
        result = sanitize_text("<script>alert('xss')</script>")
        assert "<" not in result
        assert ">" not in result

    def test_truncates_long_text(self):
        result = sanitize_text("x" * 1000)
        assert len(result) <= 500


class TestDatabasePersistence:
    """Test database CRUD operations."""

    def test_upsert_and_retrieve(self, tmp_db):
        asset = CryptographicAsset(
            asset_id="DB-001",
            asset_name="DB Test",
            asset_type="API",
            cryptographic_algorithm="RSA-2048",
        )
        tmp_db.upsert_asset(asset)
        result = tmp_db.get_asset("DB-001")
        assert result is not None
        assert result["asset_name"] == "DB Test"

    def test_update_existing(self, tmp_db):
        asset = CryptographicAsset(asset_id="DB-002", asset_name="Original")
        tmp_db.upsert_asset(asset)

        asset.asset_name = "Updated"
        tmp_db.upsert_asset(asset)

        result = tmp_db.get_asset("DB-002")
        assert result["asset_name"] == "Updated"

    def test_delete_asset(self, tmp_db):
        asset = CryptographicAsset(asset_id="DB-003", asset_name="To Delete")
        tmp_db.upsert_asset(asset)
        assert tmp_db.delete_asset("DB-003") is True
        assert tmp_db.get_asset("DB-003") is None

    def test_delete_nonexistent(self, tmp_db):
        assert tmp_db.delete_asset("NOPE") is False

    def test_asset_count(self, tmp_db):
        assert tmp_db.asset_count() == 0
        tmp_db.upsert_asset(CryptographicAsset(asset_id="DB-004"))
        assert tmp_db.asset_count() == 1

    def test_get_all_assets(self, tmp_db):
        tmp_db.upsert_asset(CryptographicAsset(asset_id="DB-005", asset_name="A"))
        tmp_db.upsert_asset(CryptographicAsset(asset_id="DB-006", asset_name="B"))
        all_assets = tmp_db.get_all_assets()
        assert len(all_assets) == 2

    def test_activity_log(self, tmp_db):
        tmp_db.log_activity("test action", "test details", 5)
        activity = tmp_db.get_recent_activity(1)
        assert len(activity) == 1
        assert activity[0]["action"] == "test action"

    def test_assessment_persistence(self, tmp_db):
        asset = CryptographicAsset(asset_id="DB-007", asset_name="Assessed")
        tmp_db.upsert_asset(asset)
        tmp_db.save_assessment(
            "DB-007",
            {"is_quantum_vulnerable": True, "rule_id": "RULE-TEST"},
            {"total_score": 75.0, "risk_level": "High"},
        )
        result = tmp_db.get_assessment("DB-007")
        assert result is not None
        assert result["risk_score"] == 75.0
        assert result["risk_level"] == "High"

    def test_summary_stats(self, tmp_db):
        asset = CryptographicAsset(asset_id="DB-008")
        tmp_db.upsert_asset(asset)
        tmp_db.save_assessment(
            "DB-008",
            {"is_quantum_vulnerable": True, "needs_review": False, "is_pqc": False},
            {"total_score": 85.0, "risk_level": "Critical"},
        )
        stats = tmp_db.get_summary_stats()
        assert stats["total_assets"] == 1
        assert stats["quantum_vulnerable"] == 1
