"""
Tests for input validation.
"""

import pytest
import json
from qshield.validation import (
    validate_file_upload, validate_dataframe, validate_single_asset,
    sanitize_text, MAX_UPLOAD_MB, MAX_RECORDS, ALLOWED_EXTENSIONS,
)


class TestFileUploadValidation:
    """Test file upload security checks."""

    def test_rejects_exe(self):
        valid, msg, _ = validate_file_upload(b"binary", "malware.exe")
        assert valid is False

    def test_rejects_py(self):
        valid, msg, _ = validate_file_upload(b"import os", "script.py")
        assert valid is False

    def test_accepts_csv(self):
        csv = b"asset_id,asset_name,asset_type,cryptographic_algorithm\nA,B,C,D\n"
        valid, msg, df = validate_file_upload(csv, "data.csv")
        assert valid is True

    def test_accepts_json(self):
        data = json.dumps([{"asset_id": "1", "asset_name": "T", "asset_type": "API", "cryptographic_algorithm": "RSA"}]).encode()
        valid, msg, df = validate_file_upload(data, "data.json")
        assert valid is True

    def test_rejects_too_large(self):
        big = b"x" * ((MAX_UPLOAD_MB + 1) * 1024 * 1024)
        valid, msg, _ = validate_file_upload(big, "big.csv")
        assert valid is False

    def test_rejects_too_many_rows(self):
        header = "asset_id,asset_name,asset_type,cryptographic_algorithm\n"
        rows = "".join(f"A{i},Name{i},API,RSA\n" for i in range(MAX_RECORDS + 1))
        csv = (header + rows).encode()
        valid, msg, _ = validate_file_upload(csv, "huge.csv")
        assert valid is False


class TestDangerousContent:
    """Test rejection of potentially unsafe content."""

    def test_rejects_null_bytes(self):
        result = sanitize_text("normal\x00text")
        assert "\x00" not in result

    def test_rejects_html_tags(self):
        result = sanitize_text("<img src=x onerror=alert(1)>")
        assert "<" not in result
        assert ">" not in result

    def test_rejects_ampersand(self):
        result = sanitize_text("a&b")
        assert "&" not in result

    def test_preserves_normal_text(self):
        result = sanitize_text("RSA-2048 Key Establishment")
        assert result == "RSA-2048 Key Establishment"

    def test_truncates_long_input(self):
        result = sanitize_text("A" * 1000)
        assert len(result) == 500


class TestFieldValidation:
    """Test individual field validation rules."""

    def test_long_field_rejected(self):
        import pandas as pd
        df = pd.DataFrame([{
            "asset_id": "V-001",
            "asset_name": "x" * 600,
            "asset_type": "API",
            "cryptographic_algorithm": "RSA",
        }])
        assets, errors = validate_dataframe(df)
        assert len(errors) > 0
        assert any("exceeds" in e["message"] for e in errors)

    def test_non_numeric_retention(self):
        import pandas as pd
        df = pd.DataFrame([{
            "asset_id": "V-002",
            "asset_name": "Test",
            "asset_type": "API",
            "cryptographic_algorithm": "RSA",
            "data_retention_years": "abc",
        }])
        assets, errors = validate_dataframe(df)
        assert len(errors) > 0
