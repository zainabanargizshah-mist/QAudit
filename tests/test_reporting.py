"""Regression checks for report exports."""

import re

from qshield.detection import analyze_assets
from qshield.inventory import load_demo_assets
from qshield.recommendations import generate_all_recommendations
from qshield.risk_engine import compute_all_scores
from qshield.reporting import generate_pdf_report


def test_pdf_report_generates_a_valid_pdf_document():
    pdf_bytes = generate_pdf_report([], [], [], [], {})

    assert pdf_bytes.startswith(b"%PDF-")
    assert len(pdf_bytes) > 1_000


def test_demo_pdf_has_no_orphaned_overflow_pages():
    assets = [asset.to_dict() for asset in load_demo_assets()]
    findings = analyze_assets(assets)
    scores = compute_all_scores(assets, findings)
    recommendations = generate_all_recommendations(assets, findings, scores)

    pdf_bytes = generate_pdf_report(
        assets,
        [finding.to_dict() for finding in findings],
        [score.to_dict() for score in scores],
        recommendations,
        {},
    )

    # Cover + landscape + one detail and migration page per demo asset + method.
    page_count = len(re.findall(rb"/Type /Page\b", pdf_bytes))
    assert page_count == 2 + len(assets) * 2 + 1
