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

from qshield.models import CryptographicAsset, ASSET_FIELDS


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
                    FOREIGN KEY (asset_id) REFERENCES assets(asset_id) ON DELETE CASCADE
                );
            """)
            conn.commit()
        finally:
            conn.close()

    # ── Asset CRUD ───────────────────────────────────────────────────

    def upsert_asset(self, asset: CryptographicAsset) -> None:
        now = datetime.utcnow().isoformat()
        conn = self._get_conn()
        try:
            conn.execute("""
                INSERT INTO assets (
                    asset_id, asset_name, asset_type, business_domain,
                    environment, owner, cryptographic_algorithm,
                    cryptographic_purpose, protocol, certificate_expiry,
                    data_sensitivity, data_retention_years, business_criticality,
                    internet_exposed, dependency_count, migration_status,
                    notes, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                asset.notes, now, now
            ))
            conn.commit()
        finally:
            conn.close()

    def upsert_assets(self, assets: List[CryptographicAsset]) -> int:
        count = 0
        for asset in assets:
            self.upsert_asset(asset)
            count += 1
        return count

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

    # ── Assessment Results ───────────────────────────────────────────

    def save_assessment(self, asset_id: str, finding: dict,
                        score: dict) -> None:
        now = datetime.utcnow().isoformat()
        conn = self._get_conn()
        try:
            conn.execute("""
                INSERT INTO assessment_results (
                    asset_id, risk_score, risk_level,
                    is_quantum_vulnerable, is_pqc, needs_review,
                    finding_json, score_json, assessed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(asset_id) DO UPDATE SET
                    risk_score=excluded.risk_score,
                    risk_level=excluded.risk_level,
                    is_quantum_vulnerable=excluded.is_quantum_vulnerable,
                    is_pqc=excluded.is_pqc,
                    needs_review=excluded.needs_review,
                    finding_json=excluded.finding_json,
                    score_json=excluded.score_json,
                    assessed_at=excluded.assessed_at
            """, (
                asset_id,
                score.get("total_score", 0.0),
                score.get("risk_level", "Unknown"),
                1 if finding.get("is_quantum_vulnerable") else 0,
                1 if finding.get("is_pqc") else 0,
                1 if finding.get("needs_review") else 0,
                json.dumps(finding),
                json.dumps(score),
                now
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
                return d
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
                results.append(d)
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
            }
        finally:
            conn.close()
