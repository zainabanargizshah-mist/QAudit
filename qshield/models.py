"""
Data models and schema definitions for Q-Shield.

Defines the CryptographicAsset schema, enumerations for risk levels,
migration statuses, and the scoring configuration.
"""

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import List, Optional
import hashlib
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


class EvidenceSource(str, Enum):
    MANUAL = "manual"
    CSV_UPLOAD = "csv_upload"
    JSON_UPLOAD = "json_upload"
    DEMO_DATASET = "demo_dataset"
    CONNECTOR = "connector"
    CERTIFICATE_SCAN = "certificate_scan"
    RUNTIME_OBSERVATION = "runtime_observation"


class VerificationStatus(str, Enum):
    UNVERIFIED = "unverified"
    PARTIALLY_VERIFIED = "partially_verified"
    VERIFIED = "verified"
    REJECTED = "rejected"


# ── Asset Fields Spec ─────────────────────────────────────────────────

ASSET_FIELDS = [
    "asset_id", "asset_name", "asset_type", "business_domain",
    "environment", "owner", "cryptographic_algorithm",
    "cryptographic_purpose", "protocol", "certificate_expiry",
    "data_sensitivity", "data_retention_years", "business_criticality",
    "internet_exposed", "dependency_count", "migration_status", "notes",
    "evidence_source", "evidence_collected_at", "evidence_location",
    "evidence_reference", "purpose_source", "purpose_confidence",
    "implementation_claim", "verification_status", "verified_by",
    "verified_at", "verification_evidence",
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
    evidence_source: str = EvidenceSource.MANUAL.value
    evidence_collected_at: str = ""
    evidence_location: str = ""
    evidence_reference: str = ""
    purpose_source: str = "manual"
    purpose_confidence: str = "low"
    implementation_claim: str = ""
    verification_status: str = VerificationStatus.UNVERIFIED.value
    verified_by: str = ""
    verified_at: str = ""
    verification_evidence: str = ""

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


@dataclass
class CryptographicUsage:
    """One cryptographic use within an asset.

    Assets may use several algorithms at different protocol or storage layers;
    this structure prevents a safe bulk cipher from hiding a vulnerable key
    establishment or signing mechanism.
    """
    asset_id: str = ""
    algorithm: str = ""
    purpose: str = "Unknown"
    key_size_or_parameter_set: str = ""
    protocol_or_location: str = ""
    evidence_source: str = EvidenceSource.MANUAL.value
    evidence_confidence: str = "low"
    observation_status: str = VerificationStatus.UNVERIFIED.value

    def to_dict(self) -> dict:
        return asdict(self)


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
    classification: str = "unknown"
    quantum_impact: str = "unknown"
    classical_status: str = "unknown"
    purpose_confidence: str = "low"
    matched_patterns: list = field(default_factory=list)
    algorithm_components: list = field(default_factory=list)
    detector_version: str = "rule-engine-v2"

    def __post_init__(self):
        """Backfill richer classification metadata for legacy findings."""
        if self.classification in ("", "unknown"):
            if self.is_pqc:
                self.classification = "hybrid" if self.needs_review else "pqc"
            elif self.is_quantum_vulnerable:
                self.classification = "vulnerable"
            elif self.needs_review:
                self.classification = "unknown"
            else:
                self.classification = "classical-safe-for-quantum"
        if self.quantum_impact in ("", "unknown"):
            if self.is_quantum_vulnerable:
                self.quantum_impact = "Shor"
            elif self.is_pqc:
                self.quantum_impact = "none"
            elif self.needs_review:
                self.quantum_impact = "unknown"
            else:
                self.quantum_impact = "generic-security-reduction"
        if self.classical_status in ("", "unknown"):
            evidence = f"{self.vulnerability_type} {self.evidence}".lower()
            if any(term in evidence for term in ("broken", "deprecated")):
                self.classical_status = "broken" if "broken" in evidence else "deprecated"
            elif self.is_pqc or self.is_quantum_vulnerable or not self.needs_review:
                self.classical_status = "acceptable"
        if self.purpose_confidence in ("", "low") and self.purpose not in ("", "Unknown", "unknown"):
            self.purpose_confidence = "high"
        if not self.algorithm_components and self.algorithm:
            self.algorithm_components = split_algorithm_components(self.algorithm)
        if not self.matched_patterns and self.rule_id:
            self.matched_patterns = [self.rule_id]

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
    score_config_version: str = "planning-priority-v2"
    assessment_status: str = "current"
    input_fingerprint: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


# ── Scoring Configuration ────────────────────────────────────────────

DEFAULT_SCORING_CONFIG = {
    "version": "planning-priority-v2",
    "weights": {
        "crypto_exposure": 0.30,
        "data_sensitivity_retention": 0.25,
        "business_criticality": 0.20,
        "internet_exposure": 0.10,
        "dependency_complexity": 0.10,
        "evidence_confidence": 0.05,
    },
    "risk_bands": {
        "Critical": (80.0, 100.0),
        "High": (60.0, 80.0),
        "Medium": (35.0, 60.0),
        "Low": (0.0, 35.0),
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

try:
    from qshield.standards import nist_pqc_standards
    NIST_PQC_STANDARDS = nist_pqc_standards() or NIST_PQC_STANDARDS
except Exception:
    # Keep the embedded reference available if a packaged deployment omits data/.
    pass


def split_algorithm_components(value: str) -> list[str]:
    """Split a compound algorithm declaration into inspectable components."""
    if not value:
        return []
    normalized = str(value).replace("/", "+").replace(",", "+").replace(";", "+")
    return [part.strip() for part in normalized.split("+") if part.strip()]


def asset_input_fingerprint(asset: dict, usages: Optional[List[dict]] = None) -> str:
    """Return a stable fingerprint for fields that affect an assessment."""
    relevant = {
        key: asset.get(key)
        for key in (
            "asset_id", "asset_name", "asset_type", "business_domain",
            "environment", "owner", "cryptographic_algorithm",
            "cryptographic_purpose", "protocol", "certificate_expiry",
            "data_sensitivity", "data_retention_years",
            "business_criticality", "internet_exposed", "dependency_count",
            "migration_status", "notes", "evidence_source",
            "purpose_source", "purpose_confidence",
        )
    }
    if usages is not None:
        relevant["cryptographic_usages"] = usages
    payload = json.dumps(relevant, sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
