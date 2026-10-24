"""
Data models and schema definitions for Q-Shield.

Defines the CryptographicAsset schema, enumerations for risk levels,
migration statuses, and the scoring configuration.
"""

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Optional
import json


# ── Enumerations ──────────────────────────────────────────────────────

class RiskLevel(str, Enum):
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    UNKNOWN = "Unknown"


class MigrationStatus(str, Enum):
    NOT_STARTED = "Not Started"
    ASSESSMENT = "Assessment"
    PLANNED = "Planned"
    TESTING = "Testing"
    READY_FOR_REVIEW = "Ready for Review"
    COMPLETED = "Completed"


class DataSensitivity(str, Enum):
    PUBLIC = "Public"
    INTERNAL = "Internal"
    CONFIDENTIAL = "Confidential"
    RESTRICTED = "Restricted"


class BusinessCriticality(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class AssetType(str, Enum):
    API = "API"
    DATABASE = "Database"
    WEB_APPLICATION = "Web Application"
    CERTIFICATE_AUTHORITY = "Certificate Authority"
    AUTHENTICATION_SERVICE = "Authentication Service"
    SIGNING_SERVICE = "Signing Service"
    KEY_MANAGEMENT = "Key Management"
    MESSAGING = "Messaging"
    FILE_TRANSFER = "File Transfer"
    VPN = "VPN"
    OTHER = "Other"


class CryptoPurpose(str, Enum):
    KEY_ESTABLISHMENT = "Key Establishment"
    DIGITAL_SIGNATURE = "Digital Signature"
    ENCRYPTION = "Encryption"
    HASHING = "Hashing"
    KEY_WRAPPING = "Key Wrapping"
    AUTHENTICATION = "Authentication"
    INTEGRITY = "Integrity"
    HYBRID = "Hybrid"
    UNKNOWN = "Unknown"


class Environment(str, Enum):
    PRODUCTION = "Production"
    STAGING = "Staging"
    DEVELOPMENT = "Development"
    DR = "Disaster Recovery"
    LEGACY = "Legacy"


# ── Asset Fields Spec ─────────────────────────────────────────────────

ASSET_FIELDS = [
    "asset_id", "asset_name", "asset_type", "business_domain",
    "environment", "owner", "cryptographic_algorithm",
    "cryptographic_purpose", "protocol", "certificate_expiry",
    "data_sensitivity", "data_retention_years", "business_criticality",
    "internet_exposed", "dependency_count", "migration_status", "notes"
]

REQUIRED_FIELDS = [
    "asset_id", "asset_name", "asset_type", "cryptographic_algorithm"
]


# ── Cryptographic Asset ──────────────────────────────────────────────

@dataclass
class CryptographicAsset:
    """Represents a single cryptographic asset in the enterprise inventory."""
    asset_id: str = ""
    asset_name: str = ""
    asset_type: str = "Other"
    business_domain: str = ""
    environment: str = "Production"
    owner: str = ""
    cryptographic_algorithm: str = ""
    cryptographic_purpose: str = "Unknown"
    protocol: str = ""
    certificate_expiry: str = ""
    data_sensitivity: str = "Internal"
    data_retention_years: int = 1
    business_criticality: str = "Medium"
    internet_exposed: bool = False
    dependency_count: int = 0
    migration_status: str = "Not Started"
    notes: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "CryptographicAsset":
        known = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {}
        for k, v in data.items():
            if k in known:
                if k == "internet_exposed":
                    filtered[k] = _parse_bool(v)
                elif k in ("data_retention_years", "dependency_count"):
                    filtered[k] = _parse_int(v)
                else:
                    filtered[k] = str(v) if v is not None else ""
        return cls(**filtered)


def _parse_bool(v) -> bool:
    if isinstance(v, bool):
        return v
    if isinstance(v, str):
        return v.strip().lower() in ("true", "yes", "1", "y")
    return bool(v)


def _parse_int(v) -> int:
    try:
        return int(float(str(v)))
    except (ValueError, TypeError):
        return 0


# ── Detection Finding ─────────────────────────────────────────────────

@dataclass
class DetectionFinding:
    """Result of cryptographic detection analysis on an asset."""
    asset_id: str = ""
    algorithm: str = ""
    purpose: str = ""
    is_quantum_vulnerable: bool = False
    is_pqc: bool = False
    needs_review: bool = False
    confidence: str = "Medium"  # High, Medium, Low
    vulnerability_type: str = ""
    evidence: str = ""
    rule_id: str = ""
    recommendation: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


# ── Risk Score Result ─────────────────────────────────────────────────

@dataclass
class RiskScoreResult:
    """Explainable risk score for a single asset."""
    asset_id: str = ""
    total_score: float = 0.0
    risk_level: str = "Unknown"
    breakdown: dict = field(default_factory=dict)
    top_factors: list = field(default_factory=list)
    explanation: str = ""
    suggested_actions: list = field(default_factory=list)
    needs_review: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


# ── Scoring Configuration ────────────────────────────────────────────

DEFAULT_SCORING_CONFIG = {
    "weights": {
        "crypto_exposure": 0.30,
        "data_sensitivity_retention": 0.25,
        "business_criticality": 0.20,
        "internet_exposure": 0.10,
        "dependency_complexity": 0.10,
        "evidence_confidence": 0.05,
    },
    "risk_bands": {
        "Critical": (80, 100),
        "High": (60, 79),
        "Medium": (35, 59),
        "Low": (0, 34),
    },
    "disclaimer": (
        "These scores are decision-support estimates for migration planning. "
        "They are not certified security ratings or official NIST classifications. "
        "All findings require human review before action."
    ),
}


# ── Standards Reference ───────────────────────────────────────────────

NIST_PQC_STANDARDS = {
    "FIPS 203": {
        "title": "ML-KEM (Module-Lattice-Based Key-Encapsulation Mechanism)",
        "purpose": "Key encapsulation and shared-secret establishment",
        "algorithm": "ML-KEM",
        "url": "https://csrc.nist.gov/pubs/fips/203/final",
        "organization": "NIST",
        "status": "Final Standard",
    },
    "FIPS 204": {
        "title": "ML-DSA (Module-Lattice-Based Digital Signature Algorithm)",
        "purpose": "Digital signatures",
        "algorithm": "ML-DSA",
        "url": "https://csrc.nist.gov/pubs/fips/204/final",
        "organization": "NIST",
        "status": "Final Standard",
    },
    "FIPS 205": {
        "title": "SLH-DSA (Stateless Hash-Based Digital Signature Algorithm)",
        "purpose": "Digital signatures (hash-based, conservative choice)",
        "algorithm": "SLH-DSA",
        "url": "https://csrc.nist.gov/pubs/fips/205/final",
        "organization": "NIST",
        "status": "Final Standard",
    },
}
