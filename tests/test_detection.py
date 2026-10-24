"""
Tests for the cryptographic detection engine.
"""

import pytest
from qshield.detection import analyze_asset
from qshield.models import DetectionFinding


class TestRSADetection:
    """Test RSA algorithm classification."""

    def test_rsa_key_establishment(self):
        finding = analyze_asset({
            "asset_id": "T-001",
            "cryptographic_algorithm": "RSA-2048",
            "cryptographic_purpose": "Key Establishment",
        })
        assert finding.is_quantum_vulnerable is True
        assert finding.is_pqc is False
        assert finding.needs_review is False
        assert finding.confidence == "High"
        assert "Shor" in finding.evidence
        assert "RULE-RSA" in finding.rule_id
        assert "ML-KEM" in finding.recommendation
        assert "FIPS 203" in finding.recommendation

    def test_rsa_digital_signature(self):
        finding = analyze_asset({
            "asset_id": "T-002",
            "cryptographic_algorithm": "RSA-4096",
            "cryptographic_purpose": "Digital Signature",
        })
        assert finding.is_quantum_vulnerable is True
        assert "ML-DSA" in finding.recommendation or "SLH-DSA" in finding.recommendation

    def test_rsa_encryption(self):
        finding = analyze_asset({
            "asset_id": "T-003",
            "cryptographic_algorithm": "RSA-2048",
            "cryptographic_purpose": "Encryption",
        })
        assert finding.is_quantum_vulnerable is True
        assert "ML-KEM" in finding.recommendation

    def test_rsa_unspecified_purpose(self):
        finding = analyze_asset({
            "asset_id": "T-004",
            "cryptographic_algorithm": "RSA",
            "cryptographic_purpose": "",
        })
        assert finding.is_quantum_vulnerable is True
        assert finding.rule_id.startswith("RULE-RSA")


class TestECCDetection:
    """Test ECC algorithm classification."""

    def test_ecdhe_key_establishment(self):
        finding = analyze_asset({
            "asset_id": "T-010",
            "cryptographic_algorithm": "ECDHE",
            "cryptographic_purpose": "Key Establishment",
        })
        assert finding.is_quantum_vulnerable is True
        assert "RULE-ECC-001" == finding.rule_id
        assert "ML-KEM" in finding.recommendation

    def test_ecdh_key_establishment(self):
        finding = analyze_asset({
            "asset_id": "T-011",
            "cryptographic_algorithm": "ECDH",
            "cryptographic_purpose": "Key Establishment",
        })
        assert finding.is_quantum_vulnerable is True
        assert "FIPS 203" in finding.recommendation

    def test_ecdsa_signature(self):
        finding = analyze_asset({
            "asset_id": "T-012",
            "cryptographic_algorithm": "ECDSA P-256",
            "cryptographic_purpose": "Digital Signature",
        })
        assert finding.is_quantum_vulnerable is True
        assert "RULE-ECC-002" == finding.rule_id
        assert "ML-DSA" in finding.recommendation or "SLH-DSA" in finding.recommendation

    def test_eddsa(self):
        finding = analyze_asset({
            "asset_id": "T-013",
            "cryptographic_algorithm": "EdDSA",
            "cryptographic_purpose": "Digital Signature",
        })
        assert finding.is_quantum_vulnerable is True

    def test_ed25519(self):
        finding = analyze_asset({
            "asset_id": "T-014",
            "cryptographic_algorithm": "Ed25519",
            "cryptographic_purpose": "Digital Signature",
        })
        assert finding.is_quantum_vulnerable is True

    def test_generic_ecc(self):
        finding = analyze_asset({
            "asset_id": "T-015",
            "cryptographic_algorithm": "ECC",
            "cryptographic_purpose": "Unknown",
        })
        assert finding.is_quantum_vulnerable is True
        assert finding.confidence == "Medium"  # Generic ECC has lower confidence


class TestDHDetection:
    """Test classical Diffie-Hellman detection."""

    def test_diffie_hellman(self):
        finding = analyze_asset({
            "asset_id": "T-020",
            "cryptographic_algorithm": "Diffie-Hellman",
            "cryptographic_purpose": "Key Establishment",
        })
        assert finding.is_quantum_vulnerable is True
        assert "RULE-DH-001" == finding.rule_id

    def test_dsa(self):
        finding = analyze_asset({
            "asset_id": "T-021",
            "cryptographic_algorithm": "DSA",
            "cryptographic_purpose": "Digital Signature",
        })
        assert finding.is_quantum_vulnerable is True
        assert "RULE-DSA-001" == finding.rule_id


class TestSymmetricDetection:
    """Test symmetric algorithm handling — must NOT be classified as quantum-broken."""

    def test_aes256_not_vulnerable(self):
        finding = analyze_asset({
            "asset_id": "T-030",
            "cryptographic_algorithm": "AES-256",
            "cryptographic_purpose": "Encryption",
        })
        assert finding.is_quantum_vulnerable is False
        assert finding.is_pqc is False
        assert finding.needs_review is False
        assert "quantum-resistant" in finding.evidence.lower() or "not" in finding.evidence.lower()

    def test_aes128_not_broken(self):
        finding = analyze_asset({
            "asset_id": "T-031",
            "cryptographic_algorithm": "AES-128",
            "cryptographic_purpose": "Encryption",
        })
        assert finding.is_quantum_vulnerable is False
        assert "Grover" in finding.evidence

    def test_chacha20_not_vulnerable(self):
        finding = analyze_asset({
            "asset_id": "T-032",
            "cryptographic_algorithm": "ChaCha20",
            "cryptographic_purpose": "Encryption",
        })
        assert finding.is_quantum_vulnerable is False

    def test_3des_not_quantum_broken(self):
        """3DES is weak classically but not quantum-broken."""
        finding = analyze_asset({
            "asset_id": "T-033",
            "cryptographic_algorithm": "3DES",
            "cryptographic_purpose": "Encryption",
        })
        assert finding.is_quantum_vulnerable is False
        assert "deprecated" in finding.evidence.lower() or "classical" in finding.evidence.lower()


class TestHashDetection:
    """Test hash algorithm handling — must NOT be classified as quantum-broken."""

    def test_sha256_not_vulnerable(self):
        finding = analyze_asset({
            "asset_id": "T-040",
            "cryptographic_algorithm": "SHA-256",
            "cryptographic_purpose": "Hashing",
        })
        assert finding.is_quantum_vulnerable is False
        assert finding.needs_review is False

    def test_sha3_not_vulnerable(self):
        finding = analyze_asset({
            "asset_id": "T-041",
            "cryptographic_algorithm": "SHA-3",
            "cryptographic_purpose": "Hashing",
        })
        assert finding.is_quantum_vulnerable is False

    def test_sha1_classical_weakness(self):
        """SHA-1 is broken classically but not by quantum."""
        finding = analyze_asset({
            "asset_id": "T-042",
            "cryptographic_algorithm": "SHA-1",
            "cryptographic_purpose": "Hashing",
        })
        assert finding.is_quantum_vulnerable is False
        assert "classical" in finding.evidence.lower() or "broken" in finding.evidence.lower()

    def test_md5_classical_weakness(self):
        finding = analyze_asset({
            "asset_id": "T-043",
            "cryptographic_algorithm": "MD5",
            "cryptographic_purpose": "Hashing",
        })
        assert finding.is_quantum_vulnerable is False
        assert "classical" in finding.evidence.lower() or "broken" in finding.evidence.lower()


class TestPQCDetection:
    """Test PQC algorithm recognition."""

    def test_mlkem(self):
        finding = analyze_asset({
            "asset_id": "T-050",
            "cryptographic_algorithm": "ML-KEM-768",
            "cryptographic_purpose": "Key Establishment",
        })
        assert finding.is_pqc is True
        assert finding.is_quantum_vulnerable is False
        assert "FIPS 203" in finding.evidence

    def test_mldsa(self):
        finding = analyze_asset({
            "asset_id": "T-051",
            "cryptographic_algorithm": "ML-DSA-65",
            "cryptographic_purpose": "Digital Signature",
        })
        assert finding.is_pqc is True
        assert finding.is_quantum_vulnerable is False
        assert "FIPS 204" in finding.evidence

    def test_slhdsa(self):
        finding = analyze_asset({
            "asset_id": "T-052",
            "cryptographic_algorithm": "SLH-DSA-SHA2-128s",
            "cryptographic_purpose": "Digital Signature",
        })
        assert finding.is_pqc is True
        assert "FIPS 205" in finding.evidence

    def test_kyber_alias(self):
        finding = analyze_asset({
            "asset_id": "T-053",
            "cryptographic_algorithm": "Kyber-768",
            "cryptographic_purpose": "Key Establishment",
        })
        assert finding.is_pqc is True

    def test_dilithium_alias(self):
        finding = analyze_asset({
            "asset_id": "T-054",
            "cryptographic_algorithm": "Dilithium",
            "cryptographic_purpose": "Digital Signature",
        })
        assert finding.is_pqc is True


class TestHybridDetection:
    """Test hybrid classical+PQC configuration detection."""

    def test_ecdhe_mlkem_hybrid(self):
        finding = analyze_asset({
            "asset_id": "T-060",
            "cryptographic_algorithm": "ECDHE + ML-KEM",
            "cryptographic_purpose": "Key Establishment",
        })
        assert finding.is_pqc is True
        assert finding.is_quantum_vulnerable is False
        assert finding.needs_review is True  # Hybrid needs verification
        assert "hybrid" in finding.evidence.lower()
        assert "RULE-HYB-001" == finding.rule_id

    def test_rsa_mldsa_hybrid(self):
        finding = analyze_asset({
            "asset_id": "T-061",
            "cryptographic_algorithm": "RSA + ML-DSA",
            "cryptographic_purpose": "Digital Signature",
        })
        assert finding.is_pqc is True
        assert finding.needs_review is True


class TestUnknownAlgorithms:
    """Test unknown and incomplete records."""

    def test_empty_algorithm(self):
        finding = analyze_asset({
            "asset_id": "T-070",
            "cryptographic_algorithm": "",
            "cryptographic_purpose": "",
        })
        assert finding.needs_review is True
        assert finding.is_quantum_vulnerable is False
        assert finding.confidence == "Low"
        assert "RULE-UNK-001" == finding.rule_id

    def test_unknown_algorithm(self):
        finding = analyze_asset({
            "asset_id": "T-071",
            "cryptographic_algorithm": "CustomCipher-v3",
            "cryptographic_purpose": "Encryption",
        })
        assert finding.needs_review is True
        assert finding.confidence == "Low"
        assert "RULE-UNK-002" == finding.rule_id

    def test_none_algorithm(self):
        finding = analyze_asset({
            "asset_id": "T-072",
            "cryptographic_algorithm": "None",
        })
        assert finding.needs_review is True

    def test_missing_asset_id(self):
        finding = analyze_asset({
            "cryptographic_algorithm": "RSA-2048",
        })
        assert finding.is_quantum_vulnerable is True
        assert finding.asset_id == ""


class TestPurposeDistinction:
    """Verify that key establishment and signatures are distinguished."""

    def test_rsa_key_est_recommends_mlkem(self):
        finding = analyze_asset({
            "asset_id": "T-080",
            "cryptographic_algorithm": "RSA-2048",
            "cryptographic_purpose": "Key Establishment",
        })
        assert "ML-KEM" in finding.recommendation
        assert "FIPS 203" in finding.recommendation

    def test_rsa_signature_recommends_mldsa(self):
        finding = analyze_asset({
            "asset_id": "T-081",
            "cryptographic_algorithm": "RSA-2048",
            "cryptographic_purpose": "Digital Signature",
        })
        assert "ML-DSA" in finding.recommendation or "SLH-DSA" in finding.recommendation
        assert "FIPS 204" in finding.recommendation or "FIPS 205" in finding.recommendation

    def test_ecdh_recommends_mlkem_not_mldsa(self):
        finding = analyze_asset({
            "asset_id": "T-082",
            "cryptographic_algorithm": "ECDHE",
            "cryptographic_purpose": "Key Establishment",
        })
        assert "ML-KEM" in finding.recommendation
        # Should NOT recommend a signature algorithm for key establishment
        assert "SLH-DSA" not in finding.recommendation


class TestEvidenceRecording:
    """Verify that findings record evidence and rule IDs."""

    def test_finding_has_rule_id(self):
        finding = analyze_asset({
            "asset_id": "T-090",
            "cryptographic_algorithm": "RSA-2048",
            "cryptographic_purpose": "Encryption",
        })
        assert finding.rule_id.startswith("RULE-")

    def test_finding_has_evidence(self):
        finding = analyze_asset({
            "asset_id": "T-091",
            "cryptographic_algorithm": "ECDSA P-256",
            "cryptographic_purpose": "Digital Signature",
        })
        assert len(finding.evidence) > 20

    def test_finding_has_vulnerability_type(self):
        finding = analyze_asset({
            "asset_id": "T-092",
            "cryptographic_algorithm": "Diffie-Hellman",
        })
        assert finding.vulnerability_type != ""
