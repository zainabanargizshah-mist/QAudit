"""
Report generation for Q-Shield.

Generates professional PDF and CSV reports from current assessment data.
Reports are generated from live data, not static templates.
"""

import io
import csv
from datetime import datetime, timezone
from typing import List, Dict, Optional

from qshield.models import NIST_PQC_STANDARDS, DEFAULT_SCORING_CONFIG


def generate_csv_report(
    assets: List[dict],
    findings: List[dict],
    scores: List[dict],
) -> str:
    """Generate a combined CSV assessment report."""
    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow([
        "Asset ID", "Asset Name", "Type", "Domain", "Environment",
        "Algorithm", "Purpose", "Protocol", "Data Sensitivity",
        "Business Criticality", "Internet Exposed", "Dependency Count",
        "Migration Status", "Risk Score", "Risk Level",
        "Quantum Vulnerable", "PQC Algorithm", "Needs Review",
        "Vulnerability Type", "Evidence", "Recommendation",
    ])

    finding_map = {f.get("asset_id", ""): f for f in findings}
    score_map = {s.get("asset_id", ""): s for s in scores}

    for asset in assets:
        aid = asset.get("asset_id", "")
        f = finding_map.get(aid, {})
        s = score_map.get(aid, {})

        writer.writerow([
            aid,
            asset.get("asset_name", ""),
            asset.get("asset_type", ""),
            asset.get("business_domain", ""),
            asset.get("environment", ""),
            asset.get("cryptographic_algorithm", ""),
            asset.get("cryptographic_purpose", ""),
            asset.get("protocol", ""),
            asset.get("data_sensitivity", ""),
            asset.get("business_criticality", ""),
            asset.get("internet_exposed", ""),
            asset.get("dependency_count", ""),
            asset.get("migration_status", ""),
            s.get("total_score", ""),
            s.get("risk_level", ""),
            f.get("is_quantum_vulnerable", ""),
            f.get("is_pqc", ""),
            f.get("needs_review", ""),
            f.get("vulnerability_type", ""),
            f.get("evidence", ""),
            f.get("recommendation", ""),
        ])

    return output.getvalue()


def generate_pdf_report(
    assets: List[dict],
    findings: List[dict],
    scores: List[dict],
    recommendations: List[dict],
    summary_stats: dict,
) -> bytes:
    """Build a designed, auditable report from the exact stored assessment data."""
    from fpdf import FPDF

    navy = (18, 33, 59)
    ink = (35, 48, 67)
    muted = (100, 116, 139)
    line = (220, 228, 237)
    pale = (245, 248, 252)
    teal = (0, 139, 145)
    risk_colors = {
        "Critical": (190, 43, 52),
        "High": (222, 105, 45),
        "Medium": (201, 151, 38),
        "Low": (43, 139, 102),
        "Unknown": (124, 139, 157),
    }

    class ReportPDF(FPDF):
        def header(self):
            if self.page_no() == 1:
                return
            self.set_fill_color(*navy)
            self.rect(0, 0, 210, 13, style="F")
            self.set_xy(14, 3.4)
            self.set_text_color(255, 255, 255)
            self.set_font("Helvetica", "B", 8)
            self.cell(65, 5, "Q-SHIELD  /  QUANTUM READINESS")
            self.set_font("Helvetica", "", 8)
            self.cell(0, 5, "ASSESSMENT REPORT", align="R")
            self.set_y(19)

        def footer(self):
            if self.page_no() == 1:
                return
            self.set_y(-13)
            self.set_draw_color(*line)
            self.line(14, self.get_y(), 196, self.get_y())
            self.set_y(-10)
            self.set_text_color(*muted)
            self.set_font("Helvetica", "", 7)
            self.cell(120, 5, "Decision-support estimate - review findings before action")
            self.cell(0, 5, f"{self.page_no()} / {{nb}}", align="R")

    pdf = ReportPDF(format="A4")
    pdf.alias_nb_pages()
    pdf.set_margins(14, 20, 14)
    pdf.set_auto_page_break(auto=True, margin=17)
    pdf.set_title("Q-Shield Quantum-Readiness Assessment")
    pdf.set_author("Q-Shield")

    finding_map = {str(f.get("asset_id", "")): f for f in findings}
    score_map = {str(s.get("asset_id", "")): s for s in scores}
    rec_map = {str(r.get("asset_id", "")): r for r in recommendations}
    rows = []
    for asset in assets:
        aid = str(asset.get("asset_id", ""))
        finding = finding_map.get(aid, {})
        score = score_map.get(aid, {})
        rec = rec_map.get(aid, {})
        rows.append({"asset": asset, "finding": finding, "score": score, "rec": rec})

    assessed = [r for r in rows if r["finding"] or r["score"]]
    quantum_vulnerable = sum(bool(r["finding"].get("is_quantum_vulnerable")) for r in assessed)
    pqc_assets = sum(bool(r["finding"].get("is_pqc")) for r in assessed)
    needs_review = sum(
        bool(r["finding"].get("needs_review") or r["score"].get("needs_review"))
        for r in assessed
    )
    high_priority = sum(
        r["score"].get("risk_level") in ("Critical", "High") for r in assessed
    )
    risk_counts = {level: 0 for level in ("Critical", "High", "Medium", "Low", "Unknown")}
    for row in assessed:
        level = row["score"].get("risk_level") or "Unknown"
        risk_counts[level if level in risk_counts else "Unknown"] += 1

    def section(title, subtitle=None):
        pdf.set_text_color(*navy)
        pdf.set_font("Helvetica", "B", 16)
        pdf.cell(0, 9, _safe_str(title), new_x="LMARGIN", new_y="NEXT")
        if subtitle:
            pdf.set_text_color(*muted)
            pdf.set_font("Helvetica", "", 8)
            pdf.multi_cell(0, 4, _safe_str(subtitle))
        pdf.ln(2)

    def label_value(x, y, width, label, value, value_size=9):
        pdf.set_xy(x, y)
        pdf.set_text_color(*muted)
        pdf.set_font("Helvetica", "B", 7)
        pdf.cell(width, 4, _safe_str(label.upper()))
        pdf.set_xy(x, y + 5)
        pdf.set_text_color(*ink)
        pdf.set_font("Helvetica", "B", value_size)
        pdf.multi_cell(width, 4.5, _safe_str(value or "Not recorded"))

    def key_value(label, value, indent=0, value_color=ink):
        x = 14 + indent
        width = 182 - indent
        pdf.set_x(x)
        pdf.set_text_color(*muted)
        pdf.set_font("Helvetica", "B", 8)
        pdf.cell(42, 4.5, _safe_str(label))
        pdf.set_text_color(*value_color)
        pdf.set_font("Helvetica", "", 8)
        pdf.multi_cell(width - 42, 4.5, _safe_str(value or "Not recorded"))

    def chart_bar(x, y, width, value, maximum, color, height=4):
        pdf.set_fill_color(*line)
        pdf.rect(x, y, width, height, style="F")
        if value and maximum:
            pdf.set_fill_color(*color)
            pdf.rect(x, y, max(0.8, width * min(value / maximum, 1)), height, style="F")

    # Cover and portfolio snapshot.
    pdf.add_page()
    pdf.set_fill_color(*navy)
    pdf.rect(0, 0, 210, 101, style="F")
    pdf.set_fill_color(*teal)
    pdf.rect(14, 17, 19, 1.6, style="F")
    pdf.set_xy(14, 24)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, "Q-SHIELD  /  SECURITY POSTURE")
    pdf.set_xy(14, 43)
    pdf.set_font("Helvetica", "B", 25)
    pdf.multi_cell(175, 11, "Quantum-Readiness\nAssessment Report")
    pdf.set_xy(14, 76)
    pdf.set_text_color(206, 220, 235)
    pdf.set_font("Helvetica", "", 9)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    pdf.cell(0, 6, f"Generated {now}  |  {len(assets)} inventory assets  |  {len(assessed)} assessed")

    pdf.set_y(114)
    page_w = 182
    gap = 4
    card_w = (page_w - 3 * gap) / 4
    kpis = [
        ("ASSESSED", len(assessed), navy),
        ("QUANTUM-VULNERABLE", quantum_vulnerable, risk_colors["Critical"]),
        ("CRITICAL / HIGH", high_priority, risk_colors["High"]),
        ("NEEDS REVIEW", needs_review, teal),
    ]
    for index, (label, value, color) in enumerate(kpis):
        x = 14 + index * (card_w + gap)
        pdf.set_fill_color(*pale)
        pdf.set_draw_color(*line)
        pdf.rect(x, 114, card_w, 27, style="DF")
        pdf.set_xy(x + 3, 117)
        pdf.set_text_color(*muted)
        pdf.set_font("Helvetica", "B", 6)
        pdf.multi_cell(card_w - 6, 3, label)
        pdf.set_xy(x + 3, 126)
        pdf.set_text_color(*color)
        pdf.set_font("Helvetica", "B", 17)
        pdf.cell(card_w - 6, 9, str(value))

    pdf.set_xy(14, 150)
    pdf.set_text_color(*navy)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, "Portfolio snapshot", new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(*ink)
    pdf.set_font("Helvetica", "", 9)
    pdf.multi_cell(0, 5, _safe_str(
        f"This report contains {len(assessed)} assessed asset records from an inventory of {len(assets)}. "
        f"{quantum_vulnerable} assessed assets are flagged as quantum-vulnerable, {pqc_assets} use a PQC algorithm, "
        f"and {needs_review} require manual review. {high_priority} are rated Critical or High by the stored risk score."
    ))

    # Risk distribution chart (counts are exactly the included assessment rows).
    pdf.set_xy(14, 178)
    pdf.set_text_color(*navy)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, "Risk distribution", new_x="LMARGIN", new_y="NEXT")
    chart_x, bar_x, bar_w, row_h = 14, 55, 115, 10
    max_risk = max(risk_counts.values(), default=0) or 1
    for i, level in enumerate(("Critical", "High", "Medium", "Low", "Unknown")):
        y = 188 + i * row_h
        pdf.set_xy(chart_x, y)
        pdf.set_text_color(*ink)
        pdf.set_font("Helvetica", "", 8)
        pdf.cell(37, 5, level)
        chart_bar(bar_x, y + 0.5, bar_w, risk_counts[level], max_risk, risk_colors[level], 4)
        pdf.set_xy(bar_x + bar_w + 4, y)
        pdf.set_font("Helvetica", "B", 8)
        pdf.cell(14, 5, str(risk_counts[level]))
    pdf.set_y(242)
    pdf.set_text_color(*muted)
    pdf.set_font("Helvetica", "", 7)
    pdf.multi_cell(182, 4, "Counts use the risk levels saved with the assessment records included in this report. No scores are recalculated during report generation.")
    pdf.set_y(260)
    pdf.set_fill_color(255, 248, 232)
    pdf.rect(14, 260, 182, 20, style="F")
    pdf.set_xy(18, 264)
    pdf.set_text_color(122, 86, 25)
    pdf.set_font("Helvetica", "B", 8)
    pdf.cell(0, 4, "Decision-support report - not a compliance certification")
    pdf.set_xy(18, 270)
    pdf.set_font("Helvetica", "", 7)
    pdf.multi_cell(172, 4, "Findings and scores require review by qualified security professionals before action.")

    # Risk landscape and portfolio priorities.
    pdf.add_page()
    section("Risk landscape", "Portfolio-level charts use the same stored findings and risk levels shown in the asset detail pages.")
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(*navy)
    pdf.cell(0, 7, "Assessment indicators", new_x="LMARGIN", new_y="NEXT")
    indicators = [
        ("Quantum-vulnerable", quantum_vulnerable, len(assessed), risk_colors["Critical"]),
        ("PQC in use", pqc_assets, len(assessed), teal),
        ("Manual review", needs_review, len(assessed), risk_colors["High"]),
    ]
    for i, (name, value, total, color) in enumerate(indicators):
        y = 43 + i * 15
        pdf.set_xy(14, y)
        pdf.set_text_color(*ink)
        pdf.set_font("Helvetica", "", 8)
        pdf.cell(47, 5, name)
        chart_bar(62, y + 0.5, 105, value, total or 1, color, 5)
        pdf.set_xy(171, y)
        pdf.set_font("Helvetica", "B", 8)
        pdf.cell(25, 5, f"{value} / {total}", align="R")

    pdf.set_y(91)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(*navy)
    pdf.cell(0, 7, "Highest risk scores", new_x="LMARGIN", new_y="NEXT")
    top_rows = sorted(
        (r for r in assessed if r["score"]),
        key=lambda r: float(r["score"].get("total_score", 0) or 0),
        reverse=True,
    )[:10]
    if not top_rows:
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*muted)
        pdf.cell(0, 7, "No stored risk scores are available.", new_x="LMARGIN", new_y="NEXT")
    for index, row in enumerate(top_rows):
        y = 101 + index * 15
        score = float(row["score"].get("total_score", 0) or 0)
        level = row["score"].get("risk_level", "Unknown")
        color = risk_colors.get(level, risk_colors["Unknown"])
        name = row["asset"].get("asset_name") or row["asset"].get("asset_id") or "Unnamed asset"
        pdf.set_xy(14, y)
        pdf.set_text_color(*ink)
        pdf.set_font("Helvetica", "", 7)
        pdf.cell(65, 5, _safe_str(str(name)[:42]))
        chart_bar(82, y + 0.5, 85, score, 100, color, 4)
        pdf.set_xy(170, y)
        pdf.set_text_color(*color)
        pdf.set_font("Helvetica", "B", 8)
        pdf.cell(26, 5, f"{score:.1f}  {level}", align="R")
    pdf.set_y(max(pdf.get_y(), 253))
    pdf.set_text_color(*muted)
    pdf.set_font("Helvetica", "", 7)
    pdf.multi_cell(182, 4, "Score bars are plotted on a 0-100 scale. Full scoring factors, evidence, and recommendations appear in each asset detail.")

    # Detailed asset findings. One asset per page keeps evidence and factor values readable.
    ordered_rows = sorted(
        rows,
        key=lambda r: float(r["score"].get("total_score", -1) or -1),
        reverse=True,
    )
    for row in ordered_rows:
        asset, finding, score, rec = row["asset"], row["finding"], row["score"], row["rec"]
        pdf.add_page()
        aid = str(asset.get("asset_id", ""))
        name = asset.get("asset_name") or aid or "Unnamed asset"
        risk_score = score.get("total_score")
        risk_level = score.get("risk_level") or "Unknown"
        color = risk_colors.get(risk_level, risk_colors["Unknown"])
        section("Asset detail", f"{_safe_str(name)}  |  ID: {_safe_str(aid)}")

        pdf.set_fill_color(*pale)
        pdf.rect(14, 42, 182, 21, style="F")
        pdf.set_xy(18, 45)
        pdf.set_text_color(*muted)
        pdf.set_font("Helvetica", "B", 7)
        pdf.cell(30, 4, "STORED RISK SCORE")
        pdf.set_xy(18, 50)
        pdf.set_text_color(*color)
        pdf.set_font("Helvetica", "B", 16)
        pdf.cell(31, 9, f"{float(risk_score):.1f}" if risk_score is not None else "N/A")
        pdf.set_xy(52, 50)
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(38, 8, risk_level.upper())
        badges = [
            ("QUANTUM VULNERABLE", bool(finding.get("is_quantum_vulnerable"))),
            ("PQC IN USE", bool(finding.get("is_pqc"))),
            ("NEEDS REVIEW", bool(finding.get("needs_review") or score.get("needs_review"))),
        ]
        for i, (label, active) in enumerate(badges):
            x = 98 + i * 32
            pdf.set_xy(x, 47)
            pdf.set_text_color(*(teal if active and label == "PQC IN USE" else color if active else muted))
            pdf.set_font("Helvetica", "B", 5.5)
            pdf.multi_cell(28, 3, label, align="C")
            pdf.set_xy(x, 55)
            pdf.set_font("Helvetica", "B", 8)
            pdf.cell(28, 4, "YES" if active else "NO", align="C")

        pdf.set_y(70)
        section("Asset profile")
        profile = [
            ("Type", asset.get("asset_type", "Not recorded")),
            ("Business domain", asset.get("business_domain", "Not recorded")),
            ("Environment", asset.get("environment", "Not recorded")),
            ("Algorithm", asset.get("cryptographic_algorithm", "Not recorded")),
            ("Purpose", asset.get("cryptographic_purpose", "Not recorded")),
            ("Protocol", asset.get("protocol", "Not recorded")),
            ("Data sensitivity", asset.get("data_sensitivity", "Not recorded")),
            ("Retention", f"{asset.get('data_retention_years', 'Not recorded')} years"),
            ("Business criticality", asset.get("business_criticality", "Not recorded")),
            ("Internet exposed", "Yes" if asset.get("internet_exposed") else "No"),
            ("Dependencies", asset.get("dependency_count", "Not recorded")),
            ("Migration status", asset.get("migration_status", "Not recorded")),
            ("Certificate expiry", asset.get("certificate_expiry", "Not recorded")),
            ("Owner", asset.get("owner", "Not recorded")),
        ]
        col_width = 58
        for i, (label, value) in enumerate(profile):
            col = i % 3
            row_index = i // 3
            label_value(14 + col * 61, 89 + row_index * 13, col_width, label, str(value), 8)

        pdf.set_y(154)
        section("Detection findings")
        key_value("Quantum exposure", "Potentially vulnerable to quantum attacks" if finding.get("is_quantum_vulnerable") else "Not flagged as quantum-vulnerable")
        key_value("PQC classification", "PQC algorithm detected" if finding.get("is_pqc") else "No PQC algorithm detected")
        key_value("Vulnerability type", finding.get("vulnerability_type", "Not recorded"))
        key_value("Rule / confidence", f"{finding.get('rule_id', 'Not recorded')} / {finding.get('confidence', 'Not recorded')}")
        key_value("Evidence", finding.get("evidence", "No evidence recorded"))

        pdf.ln(2)
        section("Risk score breakdown", "Weighted contributions are copied from the stored assessment score; their sum should match the score above within rounding.")
        breakdown = score.get("breakdown", {}) or {}
        header_y = pdf.get_y()
        pdf.set_text_color(*muted)
        pdf.set_font("Helvetica", "B", 6)
        for x, width, text_value, align in (
            (14, 45, "FACTOR", "L"),
            (59, 27, "RAW x WEIGHT", "R"),
            (89, 76, "WEIGHTED CONTRIBUTION (POINTS)", "C"),
            (168, 28, "POINTS", "R"),
        ):
            pdf.set_xy(x, header_y)
            pdf.cell(width, 4, text_value, align=align, new_x="RIGHT", new_y="TOP")
        pdf.set_y(header_y + 5)
        component_total = 0.0
        for factor, info in breakdown.items():
            contribution = float(info.get("weighted_contribution", 0) or 0)
            raw = float(info.get("raw_score", 0) or 0)
            weight = float(info.get("weight", 0) or 0)
            component_total += contribution
            y = pdf.get_y()
            pdf.set_xy(14, y)
            pdf.set_text_color(*ink)
            pdf.set_font("Helvetica", "", 6.5)
            pdf.cell(45, 5, _safe_str(factor.replace("_", " ").title()))
            pdf.set_xy(59, y)
            pdf.cell(27, 5, f"{raw:.0%} x {weight:.0%}", align="R")
            chart_bar(89, y + 0.7, 76, contribution, 30, teal, 3.5)
            pdf.set_xy(168, y)
            pdf.set_font("Helvetica", "B", 7)
            pdf.cell(28, 5, f"{contribution:.1f}", align="R")
            pdf.set_y(y + 6)
        if not breakdown:
            key_value("Breakdown", "No component breakdown was stored for this assessment.")
        elif risk_score is not None:
            delta = component_total - float(risk_score)
            pdf.ln(1)
            pdf.set_text_color(*muted)
            pdf.set_font("Helvetica", "B", 7)
            pdf.cell(
                0, 4,
                _safe_str(f"Component total: {component_total:.1f}  |  Stored score: {float(risk_score):.1f}  |  Rounding difference: {delta:+.1f}"),
                new_x="LMARGIN", new_y="NEXT",
            )

        if score.get("explanation"):
            pdf.ln(1)
            key_value("Score explanation", score.get("explanation"))
        if finding.get("recommendation"):
            pdf.ln(1)
            key_value("Detection guidance", finding.get("recommendation"))

        if not finding and not score:
            key_value("Assessment status", "No assessment record was present for this inventory asset.")

        # Keep the full action register on its own intentional page so no
        # recommendation is split into an almost-empty continuation page.
        if rec:
            pdf.add_page()
            section("Migration plan", f"{_safe_str(name)}  |  ID: {_safe_str(aid)}")
            priority = rec.get("risk_priority", risk_level)
            priority_color = risk_colors.get(priority, muted)
            pdf.set_fill_color(*pale)
            pdf.rect(14, 43, 182, 24, style="F")
            label_value(18, 47, 48, "Risk priority", priority, 9)
            label_value(78, 47, 50, "Current status", rec.get("migration_status", asset.get("migration_status", "Not Started")), 9)
            label_value(139, 47, 52, "Assessment score", f"{float(risk_score):.1f} / 100" if risk_score is not None else "Not scored", 9)
            pdf.set_fill_color(*priority_color)
            pdf.rect(14, 66, 182, 1.4, style="F")
            pdf.set_y(77)
            section("Recommended target")
            key_value("Standard", rec.get("target_standard", "Determine based on usage context"))
            key_value("Algorithm", rec.get("target_algorithm", "Not specified"))
            key_value("Identified concern", rec.get("identified_concern", finding.get("vulnerability_type", "Not recorded")))
            key_value("Dependencies", rec.get("dependencies", "Not recorded"))

            def action_list(title, items, accent):
                items = items or []
                if not items:
                    return
                pdf.ln(5)
                pdf.set_text_color(*navy)
                pdf.set_font("Helvetica", "B", 10)
                pdf.cell(0, 6, _safe_str(title), new_x="LMARGIN", new_y="NEXT")
                for number, item in enumerate(items, start=1):
                    y = pdf.get_y() + 1
                    pdf.set_fill_color(*accent)
                    pdf.ellipse(15, y + 0.2, 5, 5, style="F")
                    pdf.set_xy(15, y + 0.5)
                    pdf.set_text_color(255, 255, 255)
                    pdf.set_font("Helvetica", "B", 6)
                    pdf.cell(5, 4, str(number), align="C")
                    pdf.set_xy(23, y)
                    pdf.set_text_color(*ink)
                    pdf.set_font("Helvetica", "", 8)
                    pdf.multi_cell(169, 4.5, _safe_str(str(item)))
                    pdf.ln(1)

            action_list("Suggested actions", rec.get("suggested_actions", []), teal)
            action_list("Validation requirements", rec.get("validation_requirements", []), risk_colors["High"])
            action_list("Testing requirements", rec.get("testing_requirements", []), navy)

            pdf.ln(5)
            pdf.set_fill_color(255, 248, 232)
            pdf.rect(14, pdf.get_y(), 182, 17, style="F")
            pdf.set_xy(18, pdf.get_y() + 3)
            pdf.set_text_color(122, 86, 25)
            pdf.set_font("Helvetica", "B", 8)
            pdf.cell(0, 4, "Review before implementation")
            pdf.set_xy(18, pdf.get_y() + 7)
            pdf.set_font("Helvetica", "", 7)
            pdf.multi_cell(174, 4, "Recommendations are generated from the recorded asset purpose, detection finding, and score. Confirm technical fit, dependencies, and current NIST guidance with qualified reviewers.")

    # Method and references.
    pdf.add_page()
    section("Methodology and references", "Interpretation notes for the assessment data represented in this PDF.")
    pdf.set_text_color(*ink)
    pdf.set_font("Helvetica", "", 9)
    pdf.multi_cell(0, 5, _safe_str(DEFAULT_SCORING_CONFIG["disclaimer"]))
    pdf.ln(3)
    pdf.set_text_color(*navy)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, "Score calculation", new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(*ink)
    pdf.set_font("Helvetica", "", 8)
    pdf.multi_cell(0, 4.5, "Each factor is normalized from 0 to 1, multiplied by its configured weight, summed, and scaled to 0-100. The report displays stored totals and stored component contributions; it does not recompute assessments.")
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 8)
    pdf.cell(82, 5, "FACTOR")
    pdf.cell(20, 5, "WEIGHT", align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.set_draw_color(*line)
    pdf.line(14, pdf.get_y(), 196, pdf.get_y())
    for factor, weight in DEFAULT_SCORING_CONFIG["weights"].items():
        pdf.set_text_color(*ink)
        pdf.set_font("Helvetica", "", 8)
        pdf.cell(82, 5, _safe_str(factor.replace("_", " ").title()))
        pdf.cell(20, 5, f"{weight:.0%}", align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 6, "Risk bands", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 8)
    for level, (low, high) in DEFAULT_SCORING_CONFIG["risk_bands"].items():
        pdf.set_text_color(*risk_colors.get(level, muted))
        pdf.cell(0, 5, _safe_str(f"{level}: {low}-{high}"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(*muted)
    pdf.set_font("Helvetica", "", 7)
    pdf.multi_cell(0, 4, "Risk labels are copied from saved assessments. Fractional scores in gaps between configured integer bounds can be labeled Unknown by the scoring engine.")
    pdf.ln(3)
    pdf.set_text_color(*navy)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 6, "NIST post-quantum standards", new_x="LMARGIN", new_y="NEXT")
    for code, info in NIST_PQC_STANDARDS.items():
        reference_y = pdf.get_y()
        pdf.set_xy(14, reference_y)
        pdf.set_text_color(*ink)
        pdf.set_font("Helvetica", "B", 8)
        pdf.cell(17, 5, _safe_str(code), new_x="RIGHT", new_y="TOP")
        pdf.set_xy(32, reference_y)
        pdf.set_font("Helvetica", "", 8)
        pdf.multi_cell(165, 5, _safe_str(info["title"] + " - " + info["url"]))
    pdf.ln(2)
    pdf.set_text_color(*muted)
    pdf.set_font("Helvetica", "", 7)
    pdf.multi_cell(0, 4, "Scope note: assessment coverage may be lower than inventory size. Unassessed inventory items are listed in the asset details and are not counted as scored assets. Detection is rule-based, analyzes declared inventory data, and does not inspect live traffic. This report does not certify compliance.")

    return bytes(pdf.output())


def _safe_str(text) -> str:
    """Ensure text is safe for PDF output (latin-1 compatible)."""
    if not isinstance(text, str):
        text = str(text)
    return text.encode("latin-1", errors="replace").decode("latin-1")
