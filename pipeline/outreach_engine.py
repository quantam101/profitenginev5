"""
B2B Outreach Engine — Already Here LLC
Generates, queues, and dispatches personalized outreach for dual-track revenue phases.
Integrates with RevenueMatrix for lead tracking.
No placeholders — all identity fields loaded from environment.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timezone
from string import Template
from typing import Dict, List, Optional

import aiohttp

from revenue_matrix import RevenueMatrix
from smtp_dispatch import send_batch

logger = logging.getLogger("OutreachEngine")

# ── Identity config (required — no defaults, no placeholders) ─────────────────

_ID_VARS = ("OUTREACH_SENDER_NAME", "OUTREACH_SENDER_TITLE", "OUTREACH_COMPANY")


def _load_identity() -> Dict[str, str]:
    missing = [k for k in _ID_VARS if not os.getenv(k)]
    if missing:
        sys.exit(
            f"[FATAL] Missing outreach identity env vars: {', '.join(missing)}\n"
            "Example:\n"
            "  OUTREACH_SENDER_NAME='John Smith'\n"
            "  OUTREACH_SENDER_TITLE='VP of Operations'\n"
            "  OUTREACH_COMPANY='Already Here LLC'\n"
        )
    return {k: os.environ[k] for k in _ID_VARS}


# ── Outreach templates ────────────────────────────────────────────────────────

# Template variables: $company, $day, $time_a, $time_b, $sender_name, $sender_title, $sender_company

_TEMPLATES: Dict[str, str] = {

    "audit": """\
Subject: Infrastructure Audit: Network Latency & Starlink/Failover Optimization — $company

Team,

As operations scale at $company, network drops and latency bottlenecks directly impact \
your daily bottom line. Already Here LLC specializes in regional, mission-critical IT \
infrastructure, structured Cat6/Cat7 cabling, and high-speed satellite deployments.

We have an operational window open this $day to conduct a complete, on-site Network \
Infrastructure & Wireless Penetration Audit for your facility.

We will identify:
  1. Signal degradation and hardware packet-loss bottlenecks.
  2. Immediate optimization paths for your local switch infrastructure.
  3. Redundancy failover protocols to guarantee zero-downtime operations.

The standard diagnostic is $$350. If we discover actionable infrastructure gaps, that \
diagnostic is credited directly toward remediation.

Which window works best for your site lead this $day: $time_a or $time_b?

Best regards,
$sender_name
$sender_title | $sender_company
""",

    "drone": """\
Subject: 48-Hour Orthomosaic Deliverable — Aerial Site Survey for $company

Team,

High-resolution aerial data is now a competitive differentiator for commercial real estate, \
roofing assessment, and solar site feasibility. Already Here LLC deploys FAA-compliant DJI \
assets and delivers fully processed orthomosaic mapping models within 48 hours of flight.

We have availability this $day for a site survey at $company's property. Deliverables include:
  - Full orthomosaic map (GeoTIFF + web-viewer link)
  - Surface measurement data for roofing or solar layout
  - 4K still and video assets for marketing use

Typical engagement: $$750–$$1,200 depending on acreage. No equipment lead time required.

Can we schedule a 15-minute call this $day at $time_a or $time_b to confirm scope?

Best regards,
$sender_name
$sender_title | $sender_company
""",

    "cabling": """\
Subject: Turnkey Cat6/Cat7 + Structured Cabling Proposal for $company

Team,

Aging cabling infrastructure is the silent bottleneck behind most enterprise network \
performance complaints. Already Here LLC delivers turnkey structured cabling, patch-panel \
termination, and managed-switch integration for mid-market commercial facilities.

Our standard commercial package includes:
  - Cat6A or Cat7 installation to TIA-568 spec
  - Patch panel, rack mounting, and cable management
  - Post-installation certification with wiremap documentation

We have a crew window open starting $day and can scope a fixed-price proposal within 24 hours.

Available for a brief site-walk: $time_a or $time_b this $day?

Best regards,
$sender_name
$sender_title | $sender_company
""",

    "logistics": """\
Subject: Freight Lane Capacity & Tech Procurement — $company

Team,

Supply chain velocity is the margin lever most mid-market operations leave on the table. \
Already Here LLC operates as a specialized logistics broker with access to vetted regional \
carriers and direct procurement channels for commercial technology hardware.

Current capabilities for $company:
  - Spot and contract freight lane matching (dry van, flatbed, LTL)
  - Technology hardware procurement at wholesale tier
  - Set-aside contract pathways for qualifying business classifications

We are actively placing capacity this week. Can we connect this $day at $time_a or $time_b \
for a 10-minute lane-fit review?

Best regards,
$sender_name
$sender_title | $sender_company
""",
}

_SERVICE_TO_PHASE: Dict[str, str] = {
    "audit":     "ALPHA_I",
    "drone":     "ALPHA_II",
    "cabling":   "BETA_I",
    "logistics": "BETA_II",
}

_SERVICE_TO_TRACK: Dict[str, str] = {
    "audit":     "alpha",
    "drone":     "alpha",
    "cabling":   "beta",
    "logistics": "beta",
}


def render_outreach(
    service_type: str,
    company: str,
    day: str,
    time_a: str,
    time_b: str,
    identity: Dict[str, str],
) -> str:
    tmpl = _TEMPLATES.get(service_type)
    if not tmpl:
        raise ValueError(f"Unknown service_type '{service_type}'. Valid: {list(_TEMPLATES)}")
    return Template(tmpl).substitute(
        company=company,
        day=day,
        time_a=time_a,
        time_b=time_b,
        sender_name=identity["OUTREACH_SENDER_NAME"],
        sender_title=identity["OUTREACH_SENDER_TITLE"],
        sender_company=identity["OUTREACH_COMPANY"],
    )


# ── Batch outreach dispatcher ─────────────────────────────────────────────────

class OutreachEngine:
    """
    Generates and dispatches outreach for a list of target companies.
    Integrates with RevenueMatrix to create lead records automatically.

    Dispatch channel is a webhook (e.g. your CRM, email relay, or Zapier).
    Set OUTREACH_WEBHOOK_URL in env; if absent, payloads are logged only (dry-run).
    """

    def __init__(self, db_path: Optional[str] = None) -> None:
        self._matrix = RevenueMatrix(db_path or os.getenv("MESH_DB_PATH", "production_mesh_edge.db"))
        self._identity = _load_identity()
        self._webhook = os.getenv("OUTREACH_WEBHOOK_URL", "")
        if not self._webhook:
            logger.warning(
                "OUTREACH_WEBHOOK_URL not set — outreach will be generated and logged but not dispatched."
            )

    async def init(self) -> None:
        await self._matrix.init()

    async def run_batch(
        self,
        targets: List[Dict],
        day: str = "Tuesday",
        time_a: str = "09:00",
        time_b: str = "13:00",
        concurrency: int = 4,
    ) -> None:
        """
        targets: list of dicts with keys: company_name, service_type,
                 quoted_usd, and optionally contact_name/email/phone/notes.
        """
        sem = asyncio.Semaphore(concurrency)

        async def _dispatch_one(target: Dict) -> None:
            async with sem:
                service = target["service_type"]
                company = target["company_name"]
                try:
                    body = render_outreach(
                        service_type=service,
                        company=company,
                        day=day,
                        time_a=time_a,
                        time_b=time_b,
                        identity=self._identity,
                    )
                    lead_id = await self._matrix.add_lead(
                        phase_id=_SERVICE_TO_PHASE[service],
                        track=_SERVICE_TO_TRACK[service],
                        company_name=company,
                        service_type=service,
                        quoted_usd=target.get("quoted_usd", 0.0),
                        contact_name=target.get("contact_name", ""),
                        contact_email=target.get("contact_email", ""),
                        contact_phone=target.get("contact_phone", ""),
                        notes=target.get("notes", ""),
                    )

                    if self._webhook:
                        await self._post_outreach(lead_id, company, service, body)
                    else:
                        logger.info(f"[DRY-RUN] Lead {lead_id} | {company} | {service}\n{body}")
                        await self._matrix.mark_outreach_sent(lead_id)

                    logger.info(f"Outreach queued: {company} ({service})")
                except Exception as exc:
                    logger.error(f"Outreach failed for {company}: {exc}")

        await asyncio.gather(*(_dispatch_one(t) for t in targets))

    async def _post_outreach(self, lead_id: int, company: str, service: str, body: str, contact_email: str = "") -> None:
        # Path 1: Gmail SMTP direct (free, recommended)
        if contact_email and os.getenv("GMAIL_APP_PASSWORD"):
            lines = body.strip().split("\n")
            subject_line = next((l.replace("Subject:", "").strip() for l in lines if l.startswith("Subject:")), f"Already Here LLC — {company}")
            email_body = "\n".join(l for l in lines if not l.startswith("Subject:")).strip()
            ok = await send_batch([{"to": contact_email, "subject": subject_line, "body": email_body}])
            if ok.get("sent", 0):
                await self._matrix.mark_outreach_sent(lead_id)
                logger.info(f"Lead {lead_id} dispatched via Gmail SMTP → {contact_email}")
                return

        # Path 2: Webhook (Make.com, Zapier, or custom endpoint)
        if self._webhook:
            payload = {
                "lead_id": lead_id,
                "company": company,
                "service_type": service,
                "message_body": body,
                "sender_name": self._identity["OUTREACH_SENDER_NAME"],
                "sender_company": self._identity["OUTREACH_COMPANY"],
                "dispatched_at": datetime.now(timezone.utc).isoformat(),
            }
            timeout = aiohttp.ClientTimeout(total=8)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(self._webhook, json=payload) as resp:
                    if resp.status == 200:
                        await self._matrix.mark_outreach_sent(lead_id)
                        logger.info(f"Lead {lead_id} dispatched → webhook OK")
                    else:
                        body_txt = await resp.text()
                        raise RuntimeError(f"Webhook {resp.status}: {body_txt[:200]}")
            return

        # Path 3: Dry run — log to stdout
        logger.info(f"[DRY-RUN] Lead {lead_id} | {company} | no GMAIL_APP_PASSWORD or webhook set")


# ── Built-in Day-1 target list ─────────────────────────────────────────────────
# Replace or extend via OUTREACH_TARGETS_JSON env var (JSON array).

_DEFAULT_TARGETS: List[Dict] = [
    {"company_name": "Southwest Medical Partners",  "service_type": "audit",     "quoted_usd": 350.0},
    {"company_name": "Desert Valley Warehousing",   "service_type": "audit",     "quoted_usd": 350.0},
    {"company_name": "Sunbelt Logistics Group",     "service_type": "audit",     "quoted_usd": 350.0},
    {"company_name": "Mesa Commercial Roofing",     "service_type": "drone",     "quoted_usd": 850.0},
    {"company_name": "Arizona Solar Developers",    "service_type": "drone",     "quoted_usd": 1_200.0},
    {"company_name": "Phoenix Property Management", "service_type": "drone",     "quoted_usd": 750.0},
    {"company_name": "Copper State Data Centers",   "service_type": "cabling",   "quoted_usd": 4_500.0},
    {"company_name": "Southwest Distribution Co.",  "service_type": "cabling",   "quoted_usd": 3_800.0},
    {"company_name": "Pinnacle Freight Services",   "service_type": "logistics", "quoted_usd": 8_000.0},
    {"company_name": "Horizon Supply Chain LLC",    "service_type": "logistics", "quoted_usd": 7_500.0},
]


async def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Already Here LLC — B2B Outreach Engine")
    parser.add_argument("--day",    default="Tuesday", help="Day to reference in outreach")
    parser.add_argument("--time-a", default="09:00",   help="First time slot")
    parser.add_argument("--time-b", default="13:00",   help="Second time slot")
    parser.add_argument("--dry-run", action="store_true", help="Log only, do not dispatch")
    args = parser.parse_args()

    if args.dry_run:
        os.environ.pop("OUTREACH_WEBHOOK_URL", None)

    raw = os.getenv("OUTREACH_TARGETS_JSON", "")
    targets = json.loads(raw) if raw else _DEFAULT_TARGETS

    engine = OutreachEngine()
    await engine.init()
    await engine.run_batch(targets, day=args.day, time_a=args.time_a, time_b=args.time_b)

    # Print revenue dashboard after outreach run
    await engine._matrix.print_dashboard()


if __name__ == "__main__":
    asyncio.run(main())
