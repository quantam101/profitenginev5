"""
Generic PDF report helper — ported from ai-profit-suite
(volunteer_tracker.py + scripts/generate_summary.py)
=====================================================
Renders real reporting data to PDF via fpdf2. No placeholders: every value
written to the page comes from the caller-supplied ``ReportSpec``.

Honest-metrics rule: this module renders exactly the data it is given — it
never fabricates or pads metrics.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Sequence

logger = logging.getLogger("ReportPDF")

try:
    from fpdf import FPDF
except ImportError:  # fpdf2 not installed — degrade to no-op
    FPDF = None  # type: ignore[assignment,misc]


@dataclass
class ReportSection:
    """One section of a report: a heading plus lines and/or a key→value table."""
    heading: str
    lines: List[str] = field(default_factory=list)
    items: Dict[str, object] = field(default_factory=dict)


@dataclass
class ReportSpec:
    """Everything needed to render one report PDF."""
    title: str
    subtitle: Optional[str] = None
    sections: List[ReportSection] = field(default_factory=list)
    footer: Optional[str] = None


def pdf_available() -> bool:
    """True when fpdf2 is importable."""
    return FPDF is not None


def build_report_pdf(spec: ReportSpec, output_path: str) -> Optional[str]:
    """
    Render ``spec`` to a PDF at ``output_path``.

    Returns the output path on success, or ``None`` when fpdf2 is not
    installed (callers decide whether that is fatal — for zero-spend
    optional reporting it should not be).
    """
    if FPDF is None:
        logger.warning("[ReportPDF] fpdf2 not installed — skipping %s", output_path)
        return None

    pdf = FPDF()
    pdf.add_page()

    pdf.set_font("helvetica", "B", 16)
    pdf.cell(0, 10, spec.title, new_x="LMARGIN", new_y="NEXT", align="C")
    if spec.subtitle:
        pdf.set_font("helvetica", size=11)
        pdf.cell(0, 8, spec.subtitle, new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(6)

    for section in spec.sections:
        pdf.set_font("helvetica", "B", 13)
        pdf.cell(0, 9, section.heading, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("helvetica", size=11)
        for key, value in section.items.items():
            pdf.cell(
                0, 7, f"{key}: {value}",
                new_x="LMARGIN", new_y="NEXT",
            )
        for line in section.lines:
            pdf.multi_cell(
                0, 7, f"- {line}",
                new_x="LMARGIN", new_y="NEXT",
            )
        pdf.ln(3)

    footer = spec.footer or (
        f"Generated {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}"
    )
    pdf.set_font("helvetica", "I", 9)
    pdf.cell(0, 10, footer, new_x="LMARGIN", new_y="NEXT", align="R")

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(out))
    return str(out)


def daily_summary_pdf(data: Dict[str, object], output_path: str) -> Optional[str]:
    """
    Daily-summary report (port of scripts/generate_summary.py) built on
    ``build_report_pdf``. Expects real metrics in ``data``:
    ``date``, ``earnings``, ``traffic_sources`` (dict), ``actions_taken`` (list).
    """
    sections = [
        ReportSection(
            heading="Earnings",
            items={"Earnings": f"${data.get('earnings', 0)}"},
        ),
        ReportSection(
            heading="Top Traffic Sources",
            items={
                str(source): visits
                for source, visits in dict(data.get("traffic_sources") or {}).items()
            },
        ),
    ]
    actions: Sequence[str] = list(data.get("actions_taken") or [])  # type: ignore[arg-type]
    if actions:
        sections.append(
            ReportSection(heading="Actions Taken", lines=[str(a) for a in actions])
        )
    return build_report_pdf(
        ReportSpec(
            title=f"Daily Summary for {data.get('date')}",
            sections=sections,
        ),
        output_path,
    )


def certificate_pdf(
    name: str,
    achievement: str,
    output_dir: str,
    program: str = "Already Here LLC",
) -> Optional[str]:
    """
    Achievement certificate (port of volunteer_tracker.generate_certificate).
    ``achievement`` is the real measured accomplishment text.
    """
    safe = name.replace(" ", "_")
    out = str(Path(output_dir) / f"{safe}_certificate.pdf")
    return build_report_pdf(
        ReportSpec(
            title=program,
            subtitle="Certificate of Achievement",
            sections=[
                ReportSection(
                    heading="",
                    lines=[
                        f"This certifies that {name}",
                        achievement,
                        f"Issued on {datetime.now(timezone.utc).strftime('%Y-%m-%d')}",
                    ],
                )
            ],
            footer="",
        ),
        out,
    )
