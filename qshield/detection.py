"""
Deterministic cryptographic detection engine for Q-Shield.

Classifies cryptographic algorithms by their quantum vulnerability,
distinguishing between key establishment, digital signatures, encryption,
and hashing. Every finding records the evidence and rule that produced it.

This engine does NOT claim to detect quantum attacks. It identifies
cryptographic usage that is known or suspected to be vulnerable to a
sufficiently capable quantum computer, based on published research
and NIST guidance.
"""

from typing import Dict, List, Optional
from qshield.models import DetectionFinding, CryptographicAsset


# ── Algorithm Classification Rules ────────────────────────────────────

# Rule format: (pattern_list, rule_id, vulnerability_type, is_vulnerable,
#   is_pqc, confidence, evidence_template, recommendation)

ASYMMETRIC_VULNERABLE_RULES = [
    # RSA — all purposes
    {
        "patterns": ["rsa"],
        "rule_id": "RULE-RSA-001",
        "vulnerability_type": "Shor's algorithm threat to RSA",
        "is_vulnerable": True,
        "confidence": "High",
        "evidence": (
            "RSA is based on integer factorization, which is efficiently "
            "solvable by Shor's algorithm on a sufficiently capable quantum "
            "computer. Used for: {purpose}."
        ),
        "recommendation": {
            "Key Establishment": (
                "Plan migration to ML-KEM (FIPS 203) for key encapsulation. "
                "Consider hybrid classical/PQC key establishment during transition."
            ),
            "Digital Signature": (
                "Plan migration to ML-DSA (FIPS 204) or SLH-DSA (FIPS 205) "
                "for digital signatures."
            ),
            "Encryption": (
                "RSA is used for public-key encryption. Plan migration to "
                "ML-KEM (FIPS 203) for key establishment, then use symmetric "
                "encryption for bulk data."
            ),
            "_default": (
                "Assess the specific RSA usage and plan migration to the "
                "appropriate NIST PQC standard."
            ),
        },
    },
    # ECDH / ECDHE — key establishment
    {
        "patterns": ["ecdh", "ecdhe"],
        "rule_id": "RULE-ECC-001",
        "vulnerability_type": "Shor's algorithm threat to ECDH/ECDHE",
        "is_vulnerable": True,
        "confidence": "High",
        "evidence": (
            "Elliptic-curve Diffie-Hellman (ECDH/ECDHE) key establishment "
            "relies on the elliptic curve discrete logarithm problem, which "
            "is efficiently solvable by Shor's algorithm. Used for: {purpose}."
        ),
        "recommendation": {
            "Key Establishment": (
                "Plan migration to ML-KEM (FIPS 203) for key encapsulation. "
                "Consider hybrid ECDH+ML-KEM during transition."
            ),
            "_default": (
                "Assess ECDH/ECDHE usage context and migrate key establishment "
                "to ML-KEM (FIPS 203)."
            ),
        },
    },
    # ECC / ECDSA — digital signatures
    {
        "patterns": ["ecdsa", "eddsa", "ed25519", "ed448"],
        "rule_id": "RULE-ECC-002",
        "vulnerability_type": "Shor's algorithm threat to ECC signatures",
        "is_vulnerable": True,
        "confidence": "High",
        "evidence": (
            "Elliptic-curve digital signatures (ECDSA/EdDSA) rely on the "
            "elliptic curve discrete logarithm problem. Used for: {purpose}."
        ),
        "recommendation": {
            "Digital Signature": (
                "Plan migration to ML-DSA (FIPS 204) or SLH-DSA (FIPS 205) "
                "for digital signatures."
            ),
            "_default": (
                "Assess ECC signature usage and plan migration to ML-DSA "
                "(FIPS 204) or SLH-DSA (FIPS 205)."
            ),
        },
    },
    # Generic ECC catch-all
    {
        "patterns": ["ecc", "elliptic"],
        "rule_id": "RULE-ECC-003",
        "vulnerability_type": "Shor's algorithm threat to ECC",
        "is_vulnerable": True,
        "confidence": "Medium",
        "evidence": (
            "Elliptic-curve cryptography is vulnerable to Shor's algorithm. "
            "The specific ECC usage (key establishment vs. signatures) should "
            "be verified. Used for: {purpose}."
        ),
        "recommendation": {
            "_default": (
                "Determine whether ECC is used for key establishment "
                "(migrate to ML-KEM per FIPS 203) or digital signatures "
                "(migrate to ML-DSA per FIPS 204 or SLH-DSA per FIPS 205)."
            ),
        },
    },
    # Classical Diffie-Hellman
    {
        "patterns": ["diffie-hellman", "dh", "dhe"],
        "rule_id": "RULE-DH-001",
        "vulnerability_type": "Shor's algorithm threat to DH",
        "is_vulnerable": True,
        "confidence": "High",
        "evidence": (
            "Classical Diffie-Hellman key establishment relies on the "
            "discrete logarithm problem, which is efficiently solvable "
            "by Shor's algorithm. Used for: {purpose}."
        ),
        "recommendation": {
            "_default": (
                "Plan migration to ML-KEM (FIPS 203) for key establishment."
            ),
        },
    },
    # DSA (classical)
    {
        "patterns": ["dsa"],
        "rule_id": "RULE-DSA-001",
        "vulnerability_type": "Shor's algorithm threat to DSA",
        "is_vulnerable": True,
        "confidence": "High",
        "evidence": (
            "DSA relies on the discrete logarithm problem. "
            "Used for: {purpose}."
        ),
        "recommendation": {
            "_default": (
                "Plan migration to ML-DSA (FIPS 204) or SLH-DSA "
                "(FIPS 205) for digital signatures."
            ),
        },
    },
]

# ── PQC Algorithm Rules ───────────────────────────────────────────────

PQC_RULES = [
    {
        "patterns": ["ml-kem", "mlkem", "kyber"],
        "rule_id": "RULE-PQC-001",
        "algorithm_name": "ML-KEM",
        "standard": "FIPS 203",
        "purpose_match": "Key Establishment",
        "evidence": (
            "ML-KEM (Module-Lattice-Based Key-Encapsulation Mechanism) is a "
            "NIST-standardized PQC algorithm for key encapsulation (FIPS 203). "
            "This asset uses a post-quantum key establishment mechanism."
        ),
        "note": (
            "Using a PQC algorithm does not automatically prove complete "
            "system quantum readiness. Implementation correctness, protocol "
            "integration, and certificate chain updates must also be verified."
        ),
    },
    {
        "patterns": ["ml-dsa", "mldsa", "dilithium"],
        "rule_id": "RULE-PQC-002",
        "algorithm_name": "ML-DSA",
        "standard": "FIPS 204",
        "purpose_match": "Digital Signature",
        "evidence": (
            "ML-DSA (Module-Lattice-Based Digital Signature Algorithm) is a "
            "NIST-standardized PQC algorithm for digital signatures (FIPS 204). "
            "This asset uses a post-quantum signature mechanism."
        ),
        "note": (
            "Using a PQC algorithm does not automatically prove complete "
            "system quantum readiness. Implementation correctness and "
            "interoperability must be verified."
        ),
    },
    {
        "patterns": ["slh-dsa", "slhdsa", "sphincs"],
        "rule_id": "RULE-PQC-003",
        "algorithm_name": "SLH-DSA",
        "standard": "FIPS 205",
        "purpose_match": "Digital Signature",
        "evidence": (
            "SLH-DSA (Stateless Hash-Based Digital Signature Algorithm) is a "
            "NIST-standardized PQC algorithm for digital signatures (FIPS 205). "
            "This is a conservative, hash-based signature scheme."
        ),
        "note": (
            "Using a PQC algorithm does not automatically prove complete "
            "system quantum readiness."
        ),
    },
]

# ── Symmetric & Hash Rules ────────────────────────────────────────────

SYMMETRIC_RULES = {
    "aes-256": {
        "rule_id": "RULE-SYM-001",
        "is_vulnerable": False,
        "confidence": "High",
        "evidence": (
            "AES-256 provides 128-bit security against Grover's algorithm "
            "(which halves effective symmetric key length). AES-256 is "
            "generally considered quantum-resistant for symmetric encryption."
        ),
        "recommendation": "No immediate PQC migration required for symmetric AES-256.",
    },
    "aes-128": {
        "rule_id": "RULE-SYM-002",
        "is_vulnerable": False,
        "confidence": "Medium",
        "evidence": (
            "AES-128 provides 64-bit security against Grover's algorithm. "
            "While not immediately broken, consider evaluating whether "
            "AES-256 is more appropriate for long-term data protection."
        ),
        "recommendation": (
            "Consider upgrading to AES-256 for long-term data protection, "
            "especially for data with extended retention requirements."
        ),
    },
    "aes": {
        "rule_id": "RULE-SYM-003",
        "is_vulnerable": False,
        "confidence": "Medium",
        "evidence": (
            "AES is a symmetric algorithm. Grover's algorithm reduces "
            "effective key strength by half but does not break AES. "
            "The specific key size should be verified."
        ),
        "recommendation": "Verify key size. AES-256 is recommended for quantum-era data protection.",
    },
    "chacha20": {
        "rule_id": "RULE-SYM-004",
        "is_vulnerable": False,
        "confidence": "High",
        "evidence": (
            "ChaCha20 is a symmetric stream cipher with 256-bit keys, "
            "providing 128-bit security against Grover's algorithm."
        ),
        "recommendation": "No immediate PQC migration required.",
    },
    "3des": {
        "rule_id": "RULE-SYM-005",
        "is_vulnerable": False,
        "confidence": "High",
        "evidence": (
            "3DES has a small block size (64-bit) and limited effective key "
            "strength. It is deprecated for classical security reasons, "
            "independent of quantum computing."
        ),
        "recommendation": "Migrate away from 3DES for classical security reasons (small block size, slow).",
    },
}

HASH_RULES = {
    "sha-256": {
        "rule_id": "RULE-HASH-001",
        "is_vulnerable": False,
        "confidence": "High",
        "evidence": (
            "SHA-256 provides 128-bit collision resistance against quantum "
            "attacks (Grover's algorithm affects preimage resistance, not "
            "collision resistance, by a square-root factor). SHA-256 is "
            "generally considered adequate for most applications."
        ),
        "recommendation": "No immediate migration required. SHA-256 remains suitable.",
    },
    "sha-384": {
        "rule_id": "RULE-HASH-002",
        "is_vulnerable": False,
        "confidence": "High",
        "evidence": "SHA-384 offers strong quantum-era security margins.",
        "recommendation": "No migration required.",
    },
    "sha-512": {
        "rule_id": "RULE-HASH-003",
        "is_vulnerable": False,
        "confidence": "High",
        "evidence": "SHA-512 offers strong quantum-era security margins.",
        "recommendation": "No migration required.",
    },
    "sha-3": {
        "rule_id": "RULE-HASH-004",
        "is_vulnerable": False,
        "confidence": "High",
        "evidence": (
            "SHA-3 is not structurally weakened by known quantum attacks "
            "beyond generic Grover-based preimage speedup. SHA-3 with "
            "sufficient output length is considered quantum-resistant."
        ),
        "recommendation": "No migration required.",
    },
    "sha-1": {
        "rule_id": "RULE-HASH-005",
        "is_vulnerable": False,
        "confidence": "High",
        "evidence": (
            "SHA-1 is broken for collision resistance by classical attacks "
            "and should be migrated regardless of quantum computing concerns."
        ),
        "recommendation": "Migrate from SHA-1 to SHA-256 or SHA-3 for classical security.",
    },
    "md5": {
        "rule_id": "RULE-HASH-006",
        "is_vulnerable": False,
        "confidence": "High",
        "evidence": (
            "MD5 is broken for collision resistance by classical attacks. "
            "This is a classical security issue, not a quantum concern."
        ),
        "recommendation": "Migrate from MD5 immediately for classical security.",
    },
}


# ── Detection Engine ──────────────────────────────────────────────────

def analyze_asset(asset: dict) -> DetectionFinding:
    """
    Analyze a single asset's cryptographic configuration and return a
    DetectionFinding. The analysis is deterministic and rule-based.
    """
    algo_raw = str(asset.get("cryptographic_algorithm", "")).strip()
    purpose_raw = str(asset.get("cryptographic_purpose", "")).strip()
    algo_lower = algo_raw.lower().replace(" ", "").replace("_", "")

    if not algo_raw or algo_lower in ("unknown", "none", "n/a", ""):
        return DetectionFinding(
            asset_id=asset.get("asset_id", ""),
            algorithm=algo_raw or "Unknown",
            purpose=purpose_raw or "Unknown",
            is_quantum_vulnerable=False,
            is_pqc=False,
            needs_review=True,
            confidence="Low",
            vulnerability_type="Insufficient information",
            evidence=(
                "No cryptographic algorithm specified. Cannot determine "
                "quantum vulnerability. Manual review required."
            ),
            rule_id="RULE-UNK-001",
            recommendation="Identify and document the cryptographic algorithm in use.",
        )

    # Check for hybrid configurations
    hybrid_finding = _check_hybrid(algo_lower, algo_raw, purpose_raw, asset)
    if hybrid_finding:
        return hybrid_finding

    # Check PQC algorithms
    for rule in PQC_RULES:
        if any(p in algo_lower for p in rule["patterns"]):
            return DetectionFinding(
                asset_id=asset.get("asset_id", ""),
                algorithm=algo_raw,
                purpose=purpose_raw or rule["purpose_match"],
                is_quantum_vulnerable=False,
                is_pqc=True,
                needs_review=False,
                confidence="High",
                vulnerability_type="PQC algorithm in use",
                evidence=rule["evidence"],
                rule_id=rule["rule_id"],
                recommendation=rule["note"],
            )

    # Check asymmetric vulnerable algorithms
    for rule in ASYMMETRIC_VULNERABLE_RULES:
        if any(p in algo_lower for p in rule["patterns"]):
            # Avoid false match: "dsa" should not match "ml-dsa" or "slh-dsa"
            if rule["rule_id"] == "RULE-DSA-001":
                if any(pqc in algo_lower for pqc in ["ml-dsa", "mldsa", "slh-dsa", "slhdsa"]):
                    continue
            # Avoid "dh" matching "slh-dsa" etc.
            if rule["rule_id"] == "RULE-DH-001":
                if any(pqc in algo_lower for pqc in ["slh-dsa", "slhdsa", "ecdh", "ecdhe"]):
                    continue
            # Avoid "ecc" matching pqc names
            if rule["rule_id"] == "RULE-ECC-003":
                if any(pqc in algo_lower for pqc in ["ecdh", "ecdhe", "ecdsa"]):
                    continue

            purpose = purpose_raw if purpose_raw and purpose_raw != "Unknown" else "unspecified purpose"
            rec_map = rule["recommendation"]
            rec = rec_map.get(purpose_raw, rec_map.get("_default", ""))

            return DetectionFinding(
                asset_id=asset.get("asset_id", ""),
                algorithm=algo_raw,
                purpose=purpose_raw or "Unknown",
                is_quantum_vulnerable=True,
                is_pqc=False,
                needs_review=False,
                confidence=rule["confidence"],
                vulnerability_type=rule["vulnerability_type"],
                evidence=rule["evidence"].format(purpose=purpose),
                rule_id=rule["rule_id"],
                recommendation=rec,
            )

    # Check symmetric algorithms
    for sym_key, sym_rule in SYMMETRIC_RULES.items():
        if sym_key.replace("-", "") in algo_lower or sym_key in algo_lower:
            return DetectionFinding(
                asset_id=asset.get("asset_id", ""),
                algorithm=algo_raw,
                purpose=purpose_raw or "Encryption",
                is_quantum_vulnerable=False,
                is_pqc=False,
                needs_review=False,
                confidence=sym_rule["confidence"],
                vulnerability_type="Symmetric algorithm",
                evidence=sym_rule["evidence"],
                rule_id=sym_rule["rule_id"],
                recommendation=sym_rule["recommendation"],
            )

    # Check hash algorithms
    for hash_key, hash_rule in HASH_RULES.items():
        hash_normalized = hash_key.replace("-", "")
        if hash_normalized in algo_lower or hash_key in algo_lower:
            return DetectionFinding(
                asset_id=asset.get("asset_id", ""),
                algorithm=algo_raw,
                purpose=purpose_raw or "Hashing",
                is_quantum_vulnerable=False,
                is_pqc=False,
                needs_review=False,
                confidence=hash_rule["confidence"],
                vulnerability_type="Hash algorithm",
                evidence=hash_rule["evidence"],
                rule_id=hash_rule["rule_id"],
                recommendation=hash_rule["recommendation"],
            )

    # Unknown algorithm — needs review
    return DetectionFinding(
        asset_id=asset.get("asset_id", ""),
        algorithm=algo_raw,
        purpose=purpose_raw or "Unknown",
        is_quantum_vulnerable=False,
        is_pqc=False,
        needs_review=True,
        confidence="Low",
        vulnerability_type="Unrecognized algorithm",
        evidence=(
            f"Algorithm '{algo_raw}' is not recognized by the detection engine. "
            "Manual review is required to determine quantum vulnerability."
        ),
        rule_id="RULE-UNK-002",
        recommendation=(
            f"Investigate the algorithm '{algo_raw}' to determine its "
            "cryptographic category and quantum vulnerability status."
        ),
    )


def _check_hybrid(algo_lower: str, algo_raw: str, purpose_raw: str,
                   asset: dict) -> Optional[DetectionFinding]:
    """Check for hybrid classical+PQC configurations."""
    has_classical = any(
        p in algo_lower for p in ["rsa", "ecdh", "ecdsa", "ecc"]
    )
    has_pqc = any(
        p in algo_lower for p in [
            "ml-kem", "mlkem", "kyber", "ml-dsa", "mldsa",
            "dilithium", "slh-dsa", "slhdsa", "sphincs"
        ]
    )

    if has_classical and has_pqc:
        return DetectionFinding(
            asset_id=asset.get("asset_id", ""),
            algorithm=algo_raw,
            purpose=purpose_raw or "Hybrid",
            is_quantum_vulnerable=False,
            is_pqc=True,
            needs_review=True,
            confidence="Medium",
            vulnerability_type="Hybrid classical/PQC configuration",
            evidence=(
                f"Asset appears to use a hybrid classical/PQC configuration "
                f"({algo_raw}). Hybrid usage provides defense-in-depth during "
                f"the PQC transition. However, hybrid configuration alone does "
                f"not prove complete quantum readiness — implementation "
                f"correctness, protocol support, and interoperability must "
                f"be verified."
            ),
            rule_id="RULE-HYB-001",
            recommendation=(
                "Verify hybrid implementation correctness. Ensure both "
                "classical and PQC components are properly integrated. "
                "Test interoperability with dependent systems."
            ),
        )
    return None


def analyze_assets(assets: List[dict]) -> List[DetectionFinding]:
    """Analyze a list of asset dicts and return findings."""
    return [analyze_asset(a) for a in assets]
