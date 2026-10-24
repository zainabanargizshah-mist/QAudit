"""Shared assessment pipeline used by Streamlit pages and tests."""

from __future__ import annotations

from qshield.database import Database
from qshield.detection import aggregate_findings, analyze_asset, analyze_usages
from qshield.risk_engine import compute_risk_score


def assess_asset(database: Database, asset: dict) -> tuple[dict, dict]:
    """Assess one asset, including all structured usages attached to it."""
    usages = database.get_crypto_usages(asset.get("asset_id", ""))
    if usages:
        finding = aggregate_findings(
            analyze_usages(asset, usages), asset.get("asset_id", "")
        )
    else:
        finding = analyze_asset(asset)
    score = compute_risk_score(asset, finding)
    database.save_assessment(asset["asset_id"], finding.to_dict(), score.to_dict())
    return finding.to_dict(), score.to_dict()


def assess_all(database: Database) -> int:
    """Recalculate every stored asset and return the number assessed."""
    assets = database.get_all_assets()
    for asset in assets:
        assess_asset(database, asset)
    database.log_activity("Assessment completed", f"Assessed {len(assets)} assets", len(assets))
    return len(assets)
