"""
Input validation for Q-Shield.

Validates CSV/JSON uploads, individual asset records, and enforces
file size and record count limits. Returns structured error messages
for invalid rows.
"""

import csv
import io
import json
import os
import re
from typing import List, Tuple, Dict, Any, Optional

import pandas as pd

from qshield.models import (
    CryptographicAsset, ASSET_FIELDS, REQUIRED_FIELDS,
    AssetType, DataSensitivity, BusinessCriticality, MigrationStatus,
    Environment, CryptoPurpose,
)

MAX_UPLOAD_MB = int(os.environ.get("QSHIELD_MAX_UPLOAD_MB", "10"))
MAX_RECORDS = int(os.environ.get("QSHIELD_MAX_RECORDS", "5000"))
MAX_FIELD_LENGTH = 500
ALLOWED_EXTENSIONS = {"csv", "json"}

# Characters that could indicate injection attempts
DANGEROUS_PATTERNS = re.compile(r'[<>&;`\x00-\x08\x0b\x0c\x0e-\x1f]')


def validate_file_upload(
    file_bytes: bytes, filename: str
) -> Tuple[bool, str, Optional[pd.DataFrame]]:
    """
    Validate an uploaded file. Returns (is_valid, message, dataframe).
    """
    # Check extension
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        return False, f"Unsupported file type '.{ext}'. Please upload CSV or JSON.", None

    # Check size
    size_mb = len(file_bytes) / (1024 * 1024)
    if size_mb > MAX_UPLOAD_MB:
        return False, f"File too large ({size_mb:.1f} MB). Maximum is {MAX_UPLOAD_MB} MB.", None

    # Parse
    try:
        if ext == "csv":
            df = pd.read_csv(io.BytesIO(file_bytes), dtype=str, keep_default_na=False)
        else:
            data = json.loads(file_bytes.decode("utf-8"))
            if isinstance(data, list):
                df = pd.DataFrame(data).astype(str)
            elif isinstance(data, dict) and "assets" in data:
                df = pd.DataFrame(data["assets"]).astype(str)
            else:
                return False, "JSON must be an array of asset objects or {\"assets\": [...]}.", None
    except (json.JSONDecodeError, pd.errors.ParserError) as e:
        return False, f"Failed to parse file: {str(e)[:200]}", None
    except Exception as e:
        return False, f"Unexpected error reading file: {str(e)[:200]}", None

    if df.empty:
        return False, "File contains no data rows.", None

    if len(df) > MAX_RECORDS:
        return False, f"File contains {len(df)} rows. Maximum is {MAX_RECORDS}.", None

    # Strip whitespace from column names
    df.columns = [c.strip().lower() for c in df.columns]

    return True, f"Parsed {len(df)} records successfully.", df


def validate_dataframe(df: pd.DataFrame) -> Tuple[List[CryptographicAsset], List[Dict]]:
    """
    Validate a DataFrame of asset records. Returns (valid_assets, errors).
    Each error dict has: {row, field, value, message}.
    """
    valid_assets = []
    errors = []

    for idx, row in df.iterrows():
        row_num = idx + 2  # Account for 1-indexed + header
        row_dict = row.to_dict()
        row_errors = _validate_row(row_dict, row_num)

        if row_errors:
            errors.extend(row_errors)
        else:
            asset = CryptographicAsset.from_dict(row_dict)
            valid_assets.append(asset)

    return valid_assets, errors


def _validate_row(row: dict, row_num: int) -> List[Dict]:
    """Validate a single row and return list of errors."""
    errors = []

    # Check required fields
    for field_name in REQUIRED_FIELDS:
        val = row.get(field_name, "").strip()
        if not val:
            errors.append({
                "row": row_num,
                "field": field_name,
                "value": "",
                "message": f"Required field '{field_name}' is missing or empty."
            })

    # Check field lengths
    for field_name, val in row.items():
        if isinstance(val, str) and len(val) > MAX_FIELD_LENGTH:
            errors.append({
                "row": row_num,
                "field": field_name,
                "value": val[:50] + "...",
                "message": f"Field '{field_name}' exceeds {MAX_FIELD_LENGTH} characters."
            })

    # Check for dangerous content
    for field_name, val in row.items():
        if isinstance(val, str) and DANGEROUS_PATTERNS.search(val):
            errors.append({
                "row": row_num,
                "field": field_name,
                "value": "(sanitized)",
                "message": f"Field '{field_name}' contains potentially unsafe characters."
            })

    # Validate numeric fields
    for num_field in ("data_retention_years", "dependency_count"):
        val = row.get(num_field, "")
        if val and str(val).strip():
            try:
                n = int(float(str(val)))
                if n < 0:
                    errors.append({
                        "row": row_num,
                        "field": num_field,
                        "value": str(val),
                        "message": f"'{num_field}' must be non-negative."
                    })
            except (ValueError, TypeError):
                errors.append({
                    "row": row_num,
                    "field": num_field,
                    "value": str(val),
                    "message": f"'{num_field}' must be a number."
                })

    # Validate asset_id uniqueness is handled at the database level

    return errors


def validate_single_asset(data: dict) -> Tuple[bool, List[str]]:
    """Validate a single asset dict for manual add/edit. Returns (valid, errors)."""
    issues = []
    for f in REQUIRED_FIELDS:
        if not data.get(f, "").strip():
            issues.append(f"'{f}' is required.")

    for f, v in data.items():
        if isinstance(v, str) and len(v) > MAX_FIELD_LENGTH:
            issues.append(f"'{f}' is too long (max {MAX_FIELD_LENGTH} chars).")
        if isinstance(v, str) and DANGEROUS_PATTERNS.search(v):
            issues.append(f"'{f}' contains unsafe characters.")

    return len(issues) == 0, issues


def sanitize_text(text: str) -> str:
    """Remove potentially dangerous characters from user-supplied text."""
    return DANGEROUS_PATTERNS.sub("", text)[:MAX_FIELD_LENGTH]
