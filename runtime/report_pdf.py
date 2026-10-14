"""Designed PDF report builder (fpdf2).

Ported and generalized from quantam101/ai-profit-suite
(``volunteer_tracker.py`` + ``scripts/generate_summary.py``). Produces
phone-openable, print-ready PDF deliverables — titled sections, metric
tables, key/value tables, footer branding. Pure stdlib + fpdf2; fpdf2
is a lazy import so the module loads fine without it installed.

Usage::

    from runtime.report_pdf import ReportPDF

    pdf = ReportPDF(title="Weekly Operations Summary", org="Already Here LLC")
    pdf.add_metrics([("Revenue", "$1,240"), ("Jobs closed", "18")])
    pdf.add_section("Top traffic", "Organic: 420 visits\\nDirect: 180")
    pdf.add_table(["Product", "Units", "Revenue"],
                  [["Smart Hands", "12", "$840"], ["Haul", "6", "$400"]])
    pdf.output("report.pdf")          # or pdf.bytes() -> bytes
"""

from __future__ import annotations

import datetime as _dt
from typing import Iterable, Optional, Sequence, Tuple

_BRAND = (18, 52, 86)      # deep navy header band
_ACCENT = (0, 120, 140)    # teal accent line
_TEXT = (33, 37, 41)
_MUTED = (108, 117, 125)
_ROW_ALT = (244, 247, 250)


def _fpdf():
    try:
        from fpdf import FPDF
    except ImportError as exc:
        raise RuntimeError(
            "fpdf2 is required for PDF reports — install with `pip install fpdf2`"
        ) from exc
    return FPDF


def _t(text: object) -> str:
    """Core PDF fonts are latin-1; replace common unicode, drop the rest."""
    s = str(text)
    for a, b in {"\u2014": "-", "\u2013": "-", "\u2018": "'", "\u2019": "'",
                 "\u201c": '"', "\u201d": '"', "\u2026": "...", "\u2022": "-"}.items():
        s = s.replace(a, b)
    return s.encode("latin-1", "replace").decode("latin-1")


class ReportPDF:
    """One-shot report builder. A4 pages, header band, auto footer."""

    def __init__(self, title: str, org: str = "Already Here LLC",
                 subtitle: Optional[str] = None) -> None:
        self.title = title
        self.org = org
        self.subtitle = subtitle
        FPDF = _fpdf()

        class _Doc(FPDF):
            def footer(inner):  # noqa: N805 — fpdf signature
                inner.set_y(-14)
                inner.set_font("helvetica", "I", 8)
                inner.set_text_color(*_MUTED)
                inner.cell(0, 8, _t(f"{org} — generated {_dt.date.today():%Y-%m-%d}  |  page {inner.page_no()}"), align="C")

        self._doc = _Doc(orientation="P", unit="mm", format="A4")
        self._doc.set_auto_page_break(auto=True, margin=20)
        self._doc.set_margins(16, 16, 16)
        self._doc.add_page()
        self._header()

    def _header(self) -> None:
        d = self._doc
        d.set_fill_color(*_BRAND)
        d.rect(0, 0, 210, 30, style="F")
        d.set_fill_color(*_ACCENT)
        d.rect(0, 30, 210, 1.6, style="F")
        d.set_xy(16, 7)
        d.set_font("helvetica", "B", 16)
        d.set_text_color(255, 255, 255)
        d.cell(0, 8, _t(self.title))
        d.set_xy(16, 17)
        d.set_font("helvetica", "", 10)
        d.set_text_color(210, 226, 235)
        d.cell(0, 6, _t(self.subtitle or self.org))
        d.set_y(38)
        d.set_text_color(*_TEXT)

    def add_metrics(self, metrics: Iterable[Tuple[str, str]]) -> None:
        """Row of boxed headline metrics: [(label, value)]."""
        items = list(metrics)
        if not items:
            return
        d = self._doc
        n = len(items)
        gap = 4
        w = (178 - gap * (n - 1)) / n
        max_h = 18
        if d.get_y() + max_h > d.page_break_trigger:
            d.add_page()
        x0, y = 16, d.get_y()
        for i, (label, value) in enumerate(items):
            x = x0 + i * (w + gap)
            d.set_fill_color(*_ROW_ALT)
            d.rect(x, y, w, max_h, style="F")
            d.set_xy(x + 2, y + 3)
            d.set_font("helvetica", "B", 13)
            d.set_text_color(*_BRAND)
            d.cell(w - 4, 7, _t(value))
            d.set_xy(x + 2, y + 11)
            d.set_font("helvetica", "", 8)
            d.set_text_color(*_MUTED)
            d.cell(w - 4, 5, _t(str(label)[:40]))
        d.set_y(y + max_h + 6)
        d.set_text_color(*_TEXT)

    def add_section(self, heading: str, body: str) -> None:
        d = self._doc
        d.set_font("helvetica", "B", 12)
        d.set_text_color(*_BRAND)
        d.cell(0, 8, _t(heading), new_x="LMARGIN", new_y="NEXT")
        d.set_draw_color(*_ACCENT)
        d.line(16, d.get_y(), 60, d.get_y())
        d.ln(2)
        d.set_font("helvetica", "", 10)
        d.set_text_color(*_TEXT)
        d.multi_cell(0, 5.5, _t(body))
        d.ln(4)

    def add_table(self, header: Sequence[str], rows: Sequence[Sequence[str]],
                  col_widths: Optional[Sequence[float]] = None) -> None:
        d = self._doc
        widths = list(col_widths) if col_widths else [178 / len(header)] * len(header)
        d.set_font("helvetica", "B", 9)
        d.set_fill_color(*_BRAND)
        d.set_text_color(255, 255, 255)
        for i, h in enumerate(header):
            d.cell(widths[i], 7, _t(h), border=0, fill=True)
        d.ln()
        d.set_font("helvetica", "", 9)
        for r, row in enumerate(rows):
            if r % 2 == 1:
                d.set_fill_color(*_ROW_ALT)
                fill = True
            else:
                fill = False
            d.set_text_color(*_TEXT)
            for i, cell in enumerate(row):
                d.cell(widths[i], 6.5, self._fit(_t(cell), widths[i] - 2), border=0, fill=fill)
            d.ln()
        d.ln(4)

    def _fit(self, text: str, width: float) -> str:
        """Clip text to a column width so long values can't overprint."""
        d = self._doc
        if d.get_string_width(text) <= width:
            return text
        while text and d.get_string_width(text + "...") > width:
            text = text[:-1]
        return (text + "...") if text else ""

    def add_kv_table(self, pairs: Iterable[Tuple[str, str]],
                     key_label: str = "Field", value_label: str = "Value") -> None:
        self.add_table([key_label, value_label],
                       [[k, v] for k, v in pairs],
                       col_widths=[70, 108])

    def bytes(self) -> bytes:
        return bytes(self._doc.output())

    def output(self, path: str) -> str:
        self._doc.output(path)
        return path
