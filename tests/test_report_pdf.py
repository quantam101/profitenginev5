import pytest

pytest.importorskip("fpdf")

from runtime.report_pdf import ReportPDF  # noqa: E402


def test_report_generates_valid_pdf(tmp_path):
    pdf = ReportPDF(title="Weekly Ops", org="Already Here LLC",
                    subtitle="Field operations summary")
    pdf.add_metrics([("Revenue", "$1,240"), ("Jobs closed", "18")])
    pdf.add_section("Top traffic", "Organic: 420 visits\nDirect: 180")
    pdf.add_table(
        ["Product", "Units", "Revenue"],
        [["Smart Hands", "12", "$840"], ["Haul", "6", "$400"]],
    )
    pdf.add_kv_table([("Owner", "Stephen"), ("Status", "PASS")])

    out = tmp_path / "report.pdf"
    pdf.output(str(out))
    data = out.read_bytes()
    assert data.startswith(b"%PDF-")
    assert len(data) > 1000
    assert pdf.bytes().startswith(b"%PDF-")


def test_report_multi_page_no_crash(tmp_path):
    pdf = ReportPDF(title="Long report")
    for i in range(60):
        pdf.add_section(f"Section {i}", "body " * 30)
    out = tmp_path / "long.pdf"
    pdf.output(str(out))
    assert out.read_bytes().startswith(b"%PDF-")
