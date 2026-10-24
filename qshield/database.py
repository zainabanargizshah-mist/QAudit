"""
Database abstraction layer for Q-Shield.

Uses SQLite by default with an interface that permits later replacement.
All queries use parameterized statements to prevent SQL injection.
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import List, Optional, Dict, Any

from qshield.models import CryptographicAsset, ASSET_FIELDS, asset_input_fingerprint
from qshield.standards import standards_reference_version


DEFAULT_DB_PATH = os.environ.get("QSHIELD_DB_PATH", "qshield.db")


class Database:
    """SQLite-backed storage for cryptographic asset inventory."""

    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = db_path
        self._init_tables()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def _asset_fingerprint(self, asset: dict) -> str:
        usages = self.get_crypto_usages(asset.get("asset_id", "")) if asset.get("asset_id") else []
        return asset_input_fingerprint(asset, usages)

    def _init_tables(self):
        conn = self._get_conn()
        try:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS assets (
                    asset_id TEXT PRIMARY KEY,
                    asset_name TEXT NOT NULL,
                    asset_type TEXT DEFAULT 'Other',
                    business_domain TEXT DEFAULT '',
                    environment TEXT DEFAULT 'Production',
                    owner TEXT DEFAULT '',
                    cryptographic_algorithm TEXT DEFAULT '',
                    cryptographic_purpose TEXT DEFAULT 'Unknown',
                    protocol TEXT DEFAULT '',
                    certificate_expiry TEXT DEFAULT '',
                    data_sensitivity TEXT DEFAULT 'Internal',
                    data_retention_years INTEGER DEFAULT 1,
                    business_criticality TEXT DEFAULT 'Medium',
                    internet_exposed INTEGER DEFAULT 0,
                    dependency_count INTEGER DEFAULT 0,
                    migration_status TEXT DEFAULT 'Not Started',
                    notes TEXT DEFAULT '',
                    created_at TEXT DEFAULT '',
                    updated_at TEXT DEFAULT ''
                );

                CREATE TABLE IF NOT EXISTS activity_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    action TEXT NOT NULL,
                    details TEXT DEFAULT '',
                    asset_count INTEGER DEFAULT 0
                );

                CREATE TABLE IF NOT EXISTS assessment_results (
                    asset_id TEXT PRIMARY KEY,
                    risk_score REAL DEFAULT 0.0,
                    risk_level TEXT DEFAULT 'Unknown',
                    is_quantum_vulnerable INTEGER DEFAULT 0,
                    is_pqc INTEGER DEFAULT 0,
                    needs_review INTEGER DEFAULT 0,
                    finding_json TEXT DEFAULT '{}',
                    score_json TEXT DEFAULT '{}',
                    assessed_at TEXT DEFAULT '',
                    input_fingerprint TEXT DEFAULT '',
                    asset_revision INTEGER DEFAULT 1,
                    assessment_status TEXT DEFAULT 'current',
                    detector_version TEXT DEFAULT '',
                    score_config_version TEXT DEFAULT '',
                    standards_reference_version TEXT DEFAULT '',
                    FOREIGN KEY (asset_id) REFERENCES assets(asset_id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS asset_crypto_usages (
                    usage_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    asset_id TEXT NOT NULL,
                    algorithm TEXT NOT NULL,
                    purpose TEXT DEFAULT 'Unknown',
                    key_size_or_parameter_set TEXT DEFAULT '',
                    protocol_or_location TEXT DEFAULT '',
                    evidence_source TEXT DEFAULT 'manual',
                    evidence_confidence TEXT DEFAULT 'low',
                    observation_status TEXT DEFAULT 'unverified',
                    created_at TEXT DEFAULT '',
                    updated_at TEXT DEFAULT '',
                    UNIQUE(asset_id, algorithm, purpose, protocol_or_location),
                    FOREIGN KEY (asset_id) REFERENCES assets(asset_id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS review_decisions (
                    review_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    asset_id TEXT NOT NULL,
                    decision TEXT NOT NULL,
                    reviewer TEXT DEFAULT '',
                    evidence TEXT DEFAULT '',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (asset_id) REFERENCES assets(asset_id) ON DELETE CASCADE
                );
            """)
            self._ensure_asset_columns(conn)
            self._ensure_assessment_columns(conn)
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def _ensure_columns(conn: sqlite3.Connection, table: str, columns: dict[str, str]) -> None:
        existing = {row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
        for name, definition in columns.items():
            if name not in existing:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {definition}")

    def _ensure_asset_columns(self, conn: sqlite3.Connection) -> None:
        self._ensure_columns(conn, "assets", {
            "evidence_source": "TEXT DEFAULT 'manual'",
            "evidence_collected_at": "TEXT DEFAULT ''",
            "evidence_location": "TEXT DEFAULT ''",
            "evidence_reference": "TEXT DEFAULT ''",
            "purpose_source": "TEXT DEFAULT 'manual'",
            "purpose_confidence": "TEXT DEFAULT 'low'",
            "implementation_claim": "TEXT DEFAULT ''",
            "verification_status": "TEXT DEFAULT 'unverified'",
            "verified_by": "TEXT DEFAULT ''",
            "verified_at": "TEXT DEFAULT ''",
            "verification_evidence": "TEXT DEFAULT ''",
            "revision": "INTEGER DEFAULT 1",
        })

    def _ensure_assessment_columns(self, conn: sqlite3.Connection) -> None:
        self._ensure_columns(conn, "assessment_results", {
            "input_fingerprint": "TEXT DEFAULT ''",
            "asset_revision": "INTEGER DEFAULT 1",
            "assessment_status": "TEXT DEFAULT 'current'",
            "detector_version": "TEXT DEFAULT ''",
            "score_config_version": "TEXT DEFAULT ''",
            "standards_reference_version": "TEXT DEFAULT ''",
        })

    # ── Asset CRUD ───────────────────────────────────────────────────

    def upsert_asset(self, asset: CryptographicAsset) -> None:
        now = datetime.utcnow().isoformat()
        conn = self._get_conn()
        try:
            previous = conn.execute(
                "SELECT * FROM assets WHERE asset_id = ?", (asset.asset_id,)
            ).fetchone()
            previous_dict = dict(previous) if previous else None
            previous_fingerprint = self._asset_fingerprint(previous_dict) if previous_dict else None
            current_fingerprint = self._asset_fingerprint(asset.to_dict())
            revision = int(previous_dict.get("revision", 1) or 1) if previous_dict else 1
            if previous_dict and previous_fingerprint != current_fingerprint:
                revision += 1
            conn.execute("""
                INSERT INTO assets (
                    asset_id, asset_name, asset_type, business_domain,
                    environment, owner, cryptographic_algorithm,
                    cryptographic_purpose, protocol, certificate_expiry,
                    data_sensitivity, data_retention_years, business_criticality,
                    internet_exposed, dependency_count, migration_status,
                    notes, evidence_source, evidence_collected_at, evidence_location,
                    evidence_reference, purpose_source, purpose_confidence,
                    implementation_claim, verification_status, verified_by,
                    verified_at, verification_evidence, revision, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(asset_id) DO UPDATE SET
                    asset_name=excluded.asset_name,
                    asset_type=excluded.asset_type,
                    business_domain=excluded.business_domain,
                    environment=excluded.environment,
                    owner=excluded.owner,
                    cryptographic_algorithm=excluded.cryptographic_algorithm,
                    cryptographic_purpose=excluded.cryptographic_purpose,
                    protocol=excluded.protocol,
                    certificate_expiry=excluded.certificate_expiry,
                    data_sensitivity=excluded.data_sensitivity,
                    data_retention_years=excluded.data_retention_years,
                    business_criticality=excluded.business_criticality,
                    internet_exposed=excluded.internet_exposed,
                    dependency_count=excluded.dependency_count,
                    migration_status=excluded.migration_status,
                    notes=excluded.notes,
                    evidence_source=excluded.evidence_source,
                    evidence_collected_at=excluded.evidence_collected_at,
                    evidence_location=excluded.evidence_location,
                    evidence_reference=excluded.evidence_reference,
                    purpose_source=excluded.purpose_source,
                    purpose_confidence=excluded.purpose_confidence,
                    implementation_claim=excluded.implementation_claim,
                    verification_status=excluded.verification_status,
                    verified_by=excluded.verified_by,
                    verified_at=excluded.verified_at,
                    verification_evidence=excluded.verification_evidence,
                    revision=excluded.revision,
                    updated_at=excluded.updated_at
            """, (
                asset.asset_id, asset.asset_name, asset.asset_type,
                asset.business_domain, asset.environment, asset.owner,
                asset.cryptographic_algorithm, asset.cryptographic_purpose,
                asset.protocol, asset.certificate_expiry,
                asset.data_sensitivity, asset.data_retention_years,
                asset.business_criticality,
                1 if asset.internet_exposed else 0,
                asset.dependency_count, asset.migration_status,
                 asset.notes, asset.evidence_source, asset.evidence_collected_at,
                 asset.evidence_location, asset.evidence_reference,
                 asset.purpose_source, asset.purpose_confidence,
                 asset.implementation_claim, asset.verification_status,
                 asset.verified_by, asset.verified_at, asset.verification_evidence,
                 revision, now, now
            ))
            if previous_dict and previous_fingerprint != current_fingerprint:
                conn.execute(
                    "UPDATE assessment_results SET assessment_status = 'stale' WHERE asset_id = ?",
                    (asset.asset_id,),
                )
            conn.commit()
        finally:
            conn.close()

    def upsert_assets(self, assets: List[CryptographicAsset], replace_existing: bool = False) -> int:
        conn = self._get_conn()
        try:
            if replace_existing:
                conn.execute("DELETE FROM assets")
            count = 0
            for asset in assets:
                now = datetime.utcnow().isoformat()
                previous = conn.execute(
                    "SELECT * FROM assets WHERE asset_id = ?", (asset.asset_id,)
                ).fetchone()
                previous_dict = dict(previous) if previous else None
                old_fingerprint = self._asset_fingerprint(previous_dict) if previous_dict else None
                new_fingerprint = self._asset_fingerprint(asset.to_dict())
                revision = int(previous_dict.get("revision", 1) or 1) if previous_dict else 1
                if previous_dict and old_fingerprint != new_fingerprint:
                    revision += 1
                conn.execute("""
                    INSERT INTO assets (
                        asset_id, asset_name, asset_type, business_domain,
                        environment, owner, cryptographic_algorithm,
                        cryptographic_purpose, protocol, certificate_expiry,
                        data_sensitivity, data_retention_years, business_criticality,
                        internet_exposed, dependency_count, migration_status,
                        notes, evidence_source, evidence_collected_at, evidence_location,
                        evidence_reference, purpose_source, purpose_confidence,
                        implementation_claim, verification_status, verified_by,
                        verified_at, verification_evidence, revision, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(asset_id) DO UPDATE SET
                        asset_name=excluded.asset_name, asset_type=excluded.asset_type,
                        business_domain=excluded.business_domain, environment=excluded.environment,
                        owner=excluded.owner, cryptographic_algorithm=excluded.cryptographic_algorithm,
                        cryptographic_purpose=excluded.cryptographic_purpose, protocol=excluded.protocol,
                        certificate_expiry=excluded.certificate_expiry, data_sensitivity=excluded.data_sensitivity,
                        data_retention_years=excluded.data_retention_years, business_criticality=excluded.business_criticality,
                        internet_exposed=excluded.internet_exposed, dependency_count=excluded.dependency_count,
                        migration_status=excluded.migration_status, notes=excluded.notes,
                        evidence_source=excluded.evidence_source, evidence_collected_at=excluded.evidence_collected_at,
                        evidence_location=excluded.evidence_location, evidence_reference=excluded.evidence_reference,
                        purpose_source=excluded.purpose_source, purpose_confidence=excluded.purpose_confidence,
                        implementation_claim=excluded.implementation_claim, verification_status=excluded.verification_status,
                        verified_by=excluded.verified_by, verified_at=excluded.verified_at,
                        verification_evidence=excluded.verification_evidence, revision=excluded.revision,
                        updated_at=excluded.updated_at
                """, (
                    asset.asset_id, asset.asset_name, asset.asset_type, asset.business_domain,
                    asset.environment, asset.owner, asset.cryptographic_algorithm,
                    asset.cryptographic_purpose, asset.protocol, asset.certificate_expiry,
                    asset.data_sensitivity, asset.data_retention_years, asset.business_criticality,
                    1 if asset.internet_exposed else 0, asset.dependency_count,
                    asset.migration_status, asset.notes, asset.evidence_source,
                    asset.evidence_collected_at, asset.evidence_location, asset.evidence_reference,
                    asset.purpose_source, asset.purpose_confidence, asset.implementation_claim,
                    asset.verification_status, asset.verified_by, asset.verified_at,
                    asset.verification_evidence, revision, now, now,
                ))
                if previous_dict and old_fingerprint != new_fingerprint:
                    conn.execute(
                        "UPDATE assessment_results SET assessment_status = 'stale' WHERE asset_id = ?",
                        (asset.asset_id,),
                    )
                count += 1
            conn.commit()
            return count
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def get_asset(self, asset_id: str) -> Optional[Dict]:
        conn = self._get_conn()
        try:
            row = conn.execute(
                "SELECT * FROM assets WHERE asset_id = ?", (asset_id,)
            ).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def get_all_assets(self) -> List[Dict]:
        conn = self._get_conn()
        try:
            rows = conn.execute(
                "SELECT * FROM assets ORDER BY asset_name"
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def delete_asset(self, asset_id: str) -> bool:
        conn = self._get_conn()
        try:
            cursor = conn.execute(
                "DELETE FROM assets WHERE asset_id = ?", (asset_id,)
            )
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def delete_all_assets(self) -> int:
        conn = self._get_conn()
        try:
            cursor = conn.execute("DELETE FROM assets")
            conn.execute("DELETE FROM assessment_results")
            conn.commit()
            return cursor.rowcount
        finally:
            conn.close()

    def asset_count(self) -> int:
        conn = self._get_conn()
        try:
            row = conn.execute("SELECT COUNT(*) as cnt FROM assets").fetchone()
            return row["cnt"]
        finally:
            conn.close()

    # ── Structured cryptographic usages ───────────────────────────────

    def upsert_crypto_usage(self, asset_id: str, usage: dict) -> int:
        now = datetime.utcnow().isoformat()
        conn = self._get_conn()
        try:
            cursor = conn.execute("""
                INSERT INTO asset_crypto_usages (
                    asset_id, algorithm, purpose, key_size_or_parameter_set,
                    protocol_or_location, evidence_source, evidence_confidence,
                    observation_status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(asset_id, algorithm, purpose, protocol_or_location) DO UPDATE SET
                    key_size_or_parameter_set=excluded.key_size_or_parameter_set,
                    evidence_source=excluded.evidence_source,
                    evidence_confidence=excluded.evidence_confidence,
                    observation_status=excluded.observation_status,
                    updated_at=excluded.updated_at
            """, (
                asset_id,
                str(usage.get("algorithm", "")).strip(),
                str(usage.get("purpose", "Unknown")).strip() or "Unknown",
                str(usage.get("key_size_or_parameter_set", "")),
                str(usage.get("protocol_or_location", "")),
                str(usage.get("evidence_source", "manual")),
                str(usage.get("evidence_confidence", "low")),
                str(usage.get("observation_status", "unverified")),
                now,
                now,
            ))
            conn.execute(
                "UPDATE assessment_results SET assessment_status = 'stale' WHERE asset_id = ?",
                (asset_id,),
            )
            conn.commit()
            return int(cursor.lastrowid or 0)
        finally:
            conn.close()

    def get_crypto_usages(self, asset_id: str) -> List[Dict]:
        conn = self._get_conn()
        try:
            rows = conn.execute(
                "SELECT * FROM asset_crypto_usages WHERE asset_id = ? ORDER BY usage_id",
                (asset_id,),
            ).fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

    def delete_crypto_usage(self, usage_id: int) -> bool:
        conn = self._get_conn()
        try:
            row = conn.execute("SELECT asset_id FROM asset_crypto_usages WHERE usage_id = ?", (usage_id,)).fetchone()
            cursor = conn.execute("DELETE FROM asset_crypto_usages WHERE usage_id = ?", (usage_id,))
            if row:
                conn.execute("UPDATE assessment_results SET assessment_status = 'stale' WHERE asset_id = ?", (row[0],))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def add_review_decision(self, asset_id: str, decision: str, reviewer: str = "", evidence: str = "") -> None:
        conn = self._get_conn()
        try:
            conn.execute(
                "INSERT INTO review_decisions (asset_id, decision, reviewer, evidence, created_at) VALUES (?, ?, ?, ?, ?)",
                (asset_id, decision, reviewer, evidence, datetime.utcnow().isoformat()),
            )
            conn.commit()
        finally:
            conn.close()

    def get_review_decisions(self, asset_id: str) -> List[Dict]:
        conn = self._get_conn()
        try:
            rows = conn.execute(
                "SELECT * FROM review_decisions WHERE asset_id = ? ORDER BY review_id DESC",
                (asset_id,),
            ).fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

    # ── Assessment Results ───────────────────────────────────────────

    def _with_freshness(self, assessment: Dict) -> Dict:
        """Mark an assessment stale when its input no longer matches the asset."""
        asset = self.get_asset(assessment.get("asset_id", ""))
        if asset:
            current_fingerprint = self._asset_fingerprint(asset)
            current_revision = int(asset.get("revision", 1) or 1)
            if (
                assessment.get("input_fingerprint")
                and assessment.get("input_fingerprint") != current_fingerprint
            ) or int(assessment.get("asset_revision", 1) or 1) != current_revision:
                assessment["assessment_status"] = "stale"
        assessment.setdefault("assessment_status", "current")
        return assessment

    def save_assessment(self, asset_id: str, finding: dict,
                        score: dict) -> None:
        now = datetime.utcnow().isoformat()
        conn = self._get_conn()
        try:
            asset_row = conn.execute(
                "SELECT * FROM assets WHERE asset_id = ?", (asset_id,)
            ).fetchone()
            asset = dict(asset_row) if asset_row else {"asset_id": asset_id}
            fingerprint = self._asset_fingerprint(asset)
            conn.execute("""
                INSERT INTO assessment_results (
                    asset_id, risk_score, risk_level,
                    is_quantum_vulnerable, is_pqc, needs_review,
                    finding_json, score_json, assessed_at, input_fingerprint,
                    asset_revision, assessment_status, detector_version,
                    score_config_version, standards_reference_version
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(asset_id) DO UPDATE SET
                    risk_score=excluded.risk_score,
                    risk_level=excluded.risk_level,
                    is_quantum_vulnerable=excluded.is_quantum_vulnerable,
                    is_pqc=excluded.is_pqc,
                    needs_review=excluded.needs_review,
                    finding_json=excluded.finding_json,
                    score_json=excluded.score_json,
                    assessed_at=excluded.assessed_at,
                    input_fingerprint=excluded.input_fingerprint,
                    asset_revision=excluded.asset_revision,
                    assessment_status=excluded.assessment_status,
                    detector_version=excluded.detector_version,
                    score_config_version=excluded.score_config_version,
                    standards_reference_version=excluded.standards_reference_version
            """, (
                asset_id,
                score.get("total_score", 0.0),
                score.get("risk_level", "Unknown"),
                1 if finding.get("is_quantum_vulnerable") else 0,
                1 if finding.get("is_pqc") else 0,
                1 if finding.get("needs_review") else 0,
                json.dumps(finding),
                json.dumps(score),
                now,
                fingerprint,
                asset.get("revision", 1),
                "current",
                finding.get("detector_version", ""),
                score.get("score_config_version", ""),
                standards_reference_version(),
            ))
            conn.commit()
        finally:
            conn.close()

    def get_assessment(self, asset_id: str) -> Optional[Dict]:
        conn = self._get_conn()
        try:
            row = conn.execute(
                "SELECT * FROM assessment_results WHERE asset_id = ?",
                (asset_id,)
            ).fetchone()
            if row:
                d = dict(row)
                d["finding_json"] = json.loads(d.get("finding_json", "{}"))
                d["score_json"] = json.loads(d.get("score_json", "{}"))
                return self._with_freshness(d)
            return None
        finally:
            conn.close()

    def get_all_assessments(self) -> List[Dict]:
        conn = self._get_conn()
        try:
            rows = conn.execute(
                "SELECT * FROM assessment_results ORDER BY risk_score DESC"
            ).fetchall()
            results = []
            for r in rows:
                d = dict(r)
                d["finding_json"] = json.loads(d.get("finding_json", "{}"))
                d["score_json"] = json.loads(d.get("score_json", "{}"))
                results.append(self._with_freshness(d))
            return results
        finally:
            conn.close()

    # ── Activity Log ─────────────────────────────────────────────────

    def log_activity(self, action: str, details: str = "",
                     asset_count: int = 0) -> None:
        now = datetime.utcnow().isoformat()
        conn = self._get_conn()
        try:
            conn.execute(
                "INSERT INTO activity_log (timestamp, action, details, asset_count) "
                "VALUES (?, ?, ?, ?)",
                (now, action, details, asset_count)
            )
            conn.commit()
        finally:
            conn.close()

    def get_recent_activity(self, limit: int = 10) -> List[Dict]:
        conn = self._get_conn()
        try:
            rows = conn.execute(
                "SELECT * FROM activity_log ORDER BY id DESC LIMIT ?",
                (limit,)
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    # ── Summary Queries ──────────────────────────────────────────────

    def get_summary_stats(self) -> Dict[str, Any]:
        assessments = self.get_all_assessments()
        conn = self._get_conn()
        try:
            total = conn.execute(
                "SELECT COUNT(*) as c FROM assets"
            ).fetchone()["c"]
            vulnerable = conn.execute(
                "SELECT COUNT(*) as c FROM assessment_results "
                "WHERE is_quantum_vulnerable = 1"
            ).fetchone()["c"]
            pqc = conn.execute(
                "SELECT COUNT(*) as c FROM assessment_results WHERE is_pqc = 1"
            ).fetchone()["c"]
            critical = conn.execute(
                "SELECT COUNT(*) as c FROM assessment_results "
                "WHERE risk_level IN ('Critical', 'High')"
            ).fetchone()["c"]
            needs_review = conn.execute(
                "SELECT COUNT(*) as c FROM assessment_results "
                "WHERE needs_review = 1"
            ).fetchone()["c"]
            return {
                "total_assets": total,
                "quantum_vulnerable": vulnerable,
                "high_priority": critical,
                "pqc_assets": pqc,
                "needs_review": needs_review,
                "stale_assessments": sum(
                    assessment.get("assessment_status") == "stale"
                    for assessment in assessments
                ),
            }
        finally:
            conn.close()
