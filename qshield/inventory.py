"""
Inventory management for Q-Shield.

Handles loading demo data, importing from CSV/JSON, and managing
the asset lifecycle within the database.
"""

import os
import json
import pandas as pd
from typing import List, Tuple, Dict

from qshield.models import CryptographicAsset, ASSET_FIELDS
from qshield.database import Database
from qshield.validation import validate_file_upload, validate_dataframe


DEMO_DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "demo_assets.csv")


def load_demo_assets() -> List[CryptographicAsset]:
    """Load the synthetic demo dataset. Falls back to built-in generator if CSV not found."""
    path = os.path.normpath(DEMO_DATA_PATH)
    if not os.path.exists(path):
        return _generate_demo_assets()
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    df.columns = [c.strip().lower() for c in df.columns]
    assets, errors = validate_dataframe(df)
    return assets


def _generate_demo_assets() -> List[CryptographicAsset]:
    """Generate synthetic demo assets when CSV is not available."""
    return [
        CryptographicAsset(
            asset_id="ASSET-001", asset_name="Legacy Payment API",
            asset_type="API", business_domain="Payments",
            environment="Production", owner="Payments Team",
            cryptographic_algorithm="RSA-2048", cryptographic_purpose="Key Establishment",
            protocol="TLS 1.2", certificate_expiry="2027-03-15",
            data_sensitivity="Restricted", data_retention_years=10,
            business_criticality="Critical", internet_exposed=True,
            dependency_count=12, migration_status="Not Started",
            notes="Handles card payment processing for all channels.",
        ),
        CryptographicAsset(
            asset_id="ASSET-002", asset_name="Customer Records Database",
            asset_type="Database", business_domain="Core Banking",
            environment="Production", owner="Data Engineering",
            cryptographic_algorithm="AES-256", cryptographic_purpose="Encryption",
            protocol="TDE", certificate_expiry="",
            data_sensitivity="Restricted", data_retention_years=25,
            business_criticality="Critical", internet_exposed=False,
            dependency_count=8, migration_status="Not Started",
            notes="Encrypted at rest with AES-256. Key management uses RSA for key wrapping.",
        ),
        CryptographicAsset(
            asset_id="ASSET-003", asset_name="Banking Web Gateway",
            asset_type="Web Application", business_domain="Digital Banking",
            environment="Production", owner="Digital Channels",
            cryptographic_algorithm="ECDHE", cryptographic_purpose="Key Establishment",
            protocol="TLS 1.3", certificate_expiry="2026-11-20",
            data_sensitivity="Confidential", data_retention_years=5,
            business_criticality="High", internet_exposed=True,
            dependency_count=15, migration_status="Assessment",
            notes="Primary internet-facing banking portal.",
        ),
        CryptographicAsset(
            asset_id="ASSET-004", asset_name="Digital Signature Service",
            asset_type="Signing Service", business_domain="Legal & Compliance",
            environment="Production", owner="InfoSec",
            cryptographic_algorithm="ECDSA P-256", cryptographic_purpose="Digital Signature",
            protocol="CMS/PKCS#7", certificate_expiry="2028-06-30",
            data_sensitivity="Restricted", data_retention_years=30,
            business_criticality="Critical", internet_exposed=False,
            dependency_count=6, migration_status="Not Started",
            notes="Used for legally binding document signatures with long retention.",
        ),
        CryptographicAsset(
            asset_id="ASSET-005", asset_name="Internal Certificate Authority",
            asset_type="Certificate Authority", business_domain="Infrastructure",
            environment="Production", owner="PKI Team",
            cryptographic_algorithm="RSA-4096", cryptographic_purpose="Digital Signature",
            protocol="X.509", certificate_expiry="2035-01-01",
            data_sensitivity="Confidential", data_retention_years=20,
            business_criticality="Critical", internet_exposed=False,
            dependency_count=25, migration_status="Assessment",
            notes="Root CA for all internal certificates. Migration affects entire PKI.",
        ),
        CryptographicAsset(
            asset_id="ASSET-006", asset_name="Legacy Reporting Application",
            asset_type="Web Application", business_domain="Finance",
            environment="Legacy", owner="Finance IT",
            cryptographic_algorithm="3DES", cryptographic_purpose="Encryption",
            protocol="TLS 1.0", certificate_expiry="2025-12-31",
            data_sensitivity="Internal", data_retention_years=3,
            business_criticality="Low", internet_exposed=False,
            dependency_count=2, migration_status="Not Started",
            notes="Scheduled for decommission. Uses deprecated 3DES encryption.",
        ),
        CryptographicAsset(
            asset_id="ASSET-007", asset_name="Internal Auth Service",
            asset_type="Authentication Service", business_domain="Identity",
            environment="Production", owner="Identity Team",
            cryptographic_algorithm="RSA-2048", cryptographic_purpose="Digital Signature",
            protocol="OAuth 2.0 / JWT", certificate_expiry="2027-08-15",
            data_sensitivity="Confidential", data_retention_years=7,
            business_criticality="High", internet_exposed=True,
            dependency_count=18, migration_status="Not Started",
            notes="JWT signing for SSO. All internal services depend on this.",
        ),
        CryptographicAsset(
            asset_id="ASSET-008", asset_name="PQC Pilot Service",
            asset_type="API", business_domain="R&D",
            environment="Development", owner="Crypto R&D",
            cryptographic_algorithm="ML-KEM-768", cryptographic_purpose="Key Establishment",
            protocol="TLS 1.3", certificate_expiry="2027-01-15",
            data_sensitivity="Internal", data_retention_years=1,
            business_criticality="Low", internet_exposed=False,
            dependency_count=1, migration_status="Testing",
            notes="Experimental PQC pilot using ML-KEM for key encapsulation.",
        ),
        CryptographicAsset(
            asset_id="ASSET-009", asset_name="Interbank SWIFT Gateway",
            asset_type="Messaging", business_domain="Payments",
            environment="Production", owner="Payments Infrastructure",
            cryptographic_algorithm="RSA-2048", cryptographic_purpose="Key Establishment",
            protocol="TLS 1.2", certificate_expiry="2027-05-01",
            data_sensitivity="Restricted", data_retention_years=15,
            business_criticality="Critical", internet_exposed=True,
            dependency_count=10, migration_status="Not Started",
            notes="SWIFT messaging gateway. Regulatory and partner dependencies.",
        ),
        CryptographicAsset(
            asset_id="ASSET-010", asset_name="File Transfer Service",
            asset_type="File Transfer", business_domain="Operations",
            environment="Production", owner="Ops Team",
            cryptographic_algorithm="Diffie-Hellman", cryptographic_purpose="Key Establishment",
            protocol="SFTP", certificate_expiry="2026-09-30",
            data_sensitivity="Confidential", data_retention_years=5,
            business_criticality="Medium", internet_exposed=True,
            dependency_count=4, migration_status="Not Started",
            notes="Secure file transfer with external partners.",
        ),
        CryptographicAsset(
            asset_id="ASSET-011", asset_name="Data Warehouse ETL",
            asset_type="Database", business_domain="Analytics",
            environment="Production", owner="Data Team",
            cryptographic_algorithm="AES-128", cryptographic_purpose="Encryption",
            protocol="", certificate_expiry="",
            data_sensitivity="Internal", data_retention_years=3,
            business_criticality="Medium", internet_exposed=False,
            dependency_count=3, migration_status="Not Started",
            notes="ETL pipeline data encrypted with AES-128.",
        ),
        CryptographicAsset(
            asset_id="ASSET-012", asset_name="Mobile Banking API",
            asset_type="API", business_domain="Digital Banking",
            environment="Production", owner="Mobile Team",
            cryptographic_algorithm="ECDHE", cryptographic_purpose="Key Establishment",
            protocol="TLS 1.3", certificate_expiry="2027-02-28",
            data_sensitivity="Restricted", data_retention_years=7,
            business_criticality="Critical", internet_exposed=True,
            dependency_count=20, migration_status="Assessment",
            notes="Primary mobile banking API serving millions of users.",
        ),
        CryptographicAsset(
            asset_id="ASSET-013", asset_name="Hybrid TLS Pilot",
            asset_type="Web Application", business_domain="R&D",
            environment="Development", owner="Crypto R&D",
            cryptographic_algorithm="ECDHE + ML-KEM", cryptographic_purpose="Key Establishment",
            protocol="TLS 1.3", certificate_expiry="2027-06-01",
            data_sensitivity="Internal", data_retention_years=1,
            business_criticality="Low", internet_exposed=False,
            dependency_count=2, migration_status="Testing",
            notes="Testing hybrid classical/PQC TLS handshake.",
        ),
        CryptographicAsset(
            asset_id="ASSET-014", asset_name="Document Integrity Checker",
            asset_type="Signing Service", business_domain="Compliance",
            environment="Production", owner="Compliance Team",
            cryptographic_algorithm="SHA-256", cryptographic_purpose="Hashing",
            protocol="", certificate_expiry="",
            data_sensitivity="Confidential", data_retention_years=10,
            business_criticality="High", internet_exposed=False,
            dependency_count=3, migration_status="Not Started",
            notes="Generates SHA-256 hashes for document integrity verification.",
        ),
        CryptographicAsset(
            asset_id="ASSET-015", asset_name="VPN Concentrator",
            asset_type="VPN", business_domain="Infrastructure",
            environment="Production", owner="Network Team",
            cryptographic_algorithm="RSA-2048", cryptographic_purpose="Key Establishment",
            protocol="IKEv2/IPsec", certificate_expiry="2027-09-30",
            data_sensitivity="Confidential", data_retention_years=5,
            business_criticality="High", internet_exposed=True,
            dependency_count=8, migration_status="Not Started",
            notes="Enterprise VPN gateway for remote access.",
        ),
    ]


def import_assets_to_db(
    db: Database, assets: List[CryptographicAsset], source: str = "upload"
) -> int:
    """Import assets into the database and log the activity."""
    count = db.upsert_assets(assets)
    db.log_activity(
        action=f"Imported {count} assets",
        details=f"Source: {source}",
        asset_count=count,
    )
    return count


def get_assets_dataframe(db: Database) -> pd.DataFrame:
    """Get all assets as a pandas DataFrame."""
    assets = db.get_all_assets()
    if not assets:
        return pd.DataFrame(columns=ASSET_FIELDS)
    df = pd.DataFrame(assets)
    # Select only standard fields, ignore DB metadata
    cols = [c for c in ASSET_FIELDS if c in df.columns]
    return df[cols]


def export_assets_csv(db: Database) -> str:
    """Export assets as CSV string."""
    df = get_assets_dataframe(db)
    return df.to_csv(index=False)
