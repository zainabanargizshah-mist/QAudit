"""Regression checks for report exports."""

from qshield.reporting import generate_pdf_report


def test_pdf_report_generates_a_valid_pdf_document():
    pdf_bytes = generate_pdf_report([], [], [], [], {})

    assert pdf_bytes.startswith(b"%PDF-")
    assert len(pdf_bytes) > 1_000
