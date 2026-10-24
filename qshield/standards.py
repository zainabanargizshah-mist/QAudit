"""Canonical standards-reference loader for Q-Shield.

The application keeps one editable reference file under ``data/``.  Runtime
code reads it through this module so standards metadata is not duplicated
across UI, AI, and reporting modules.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REFERENCE_PATH = Path(__file__).resolve().parent.parent / "data" / "standards_reference.json"
FALLBACK_VERSION = "embedded-fallback"


def load_standards_reference() -> dict[str, Any]:
    """Load the canonical standards reference, with a safe minimal fallback."""
    try:
        with REFERENCE_PATH.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
            if isinstance(data, dict) and isinstance(data.get("standards"), list):
                return data
    except (OSError, json.JSONDecodeError):
        pass
    return {
        "version": FALLBACK_VERSION,
        "standards": [],
        "quantum_threat_summary": {},
    }


def standards_reference_version() -> str:
    data = load_standards_reference()
    return str(data.get("version") or data.get("last_verified") or FALLBACK_VERSION)


def standards_by_id() -> dict[str, dict[str, Any]]:
    data = load_standards_reference()
    result = {}
    for item in data.get("standards", []):
        if isinstance(item, dict) and item.get("id"):
            result[str(item["id"])] = item
    return result


def nist_pqc_standards() -> dict[str, dict[str, Any]]:
    """Return the NIST PQC subset in the shape used by existing pages."""
    result = {}
    for item in standards_by_id().values():
        identifier = str(item.get("id", ""))
        if identifier.startswith("FIPS-"):
            key = identifier.replace("-", " ", 1)
            result[key] = {
                "title": item.get("title", ""),
                "purpose": item.get("purpose", ""),
                "algorithm": item.get("algorithm", ""),
                "url": item.get("url", ""),
                "organization": item.get("organization", "NIST"),
                "status": item.get("status", "Unknown"),
                "verified": item.get("last_verified", "Unknown"),
            }
    return result
