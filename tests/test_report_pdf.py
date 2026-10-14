from __future__ import annotations

from pathlib import Path

import pytest

import runtime.report_pdf as rp

pytestmark = pytest.mark.skipif(not rp.pdf_available(), reason="fpdf2 not installed")


def test_build_report_pdf_writes_real_pdf(tmp_path):
    spec = rp.ReportSpec(
        title="Weekly Revenue Report",
        subtitle="ProfitEngine v5",
        sections=[
            rp.ReportSection(
                heading="Metrics",
                items={"Earnings": "$12.34", "Posts published": 3},
            ),
            rp.ReportSection(
                heading="Actions Taken",
                lines=["published city page for Phoenix", "rescan trends"],
            ),
        ],
    )
    out = rp.build_report_pdf(spec, str(tmp_path / "reports" / "weekly.pdf"))

    assert out is not None
    pdf = Path(out)
    assert pdf.exists()
    content = pdf.read_bytes()
    assert content.startswith(b"%PDF")
    assert len(content) > 500


def test_daily_summary_pdf_renders_real_data(tmp_path):
    data = {
        "date": "2026-10-14",
        "earnings": 7.5,
        "traffic_sources": {"google": 120, "reddit": 40},
        "actions_taken": ["posted 1 article"],
    }
    out = rp.daily_summary_pdf(data, str(tmp_path / "daily.pdf"))

    assert out is not None
    assert Path(out).read_bytes().startswith(b"%PDF")


def test_certificate_pdf(tmp_path):
    out = rp.certificate_pdf(
        "Jane Doe", "has completed 100 volunteer hours.", str(tmp_path)
    )

    assert out is not None
    assert Path(out).name == "Jane_Doe_certificate.pdf"
    assert Path(out).read_bytes().startswith(b"%PDF")


def test_build_report_pdf_returns_none_without_fpdf(tmp_path, monkeypatch):
    monkeypatch.setattr(rp, "FPDF", None)
    out = rp.build_report_pdf(
        rp.ReportSpec(title="x"), str(tmp_path / "r.pdf")
    )
    assert out is None
    assert not (tmp_path / "r.pdf").exists()
