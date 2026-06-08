"""
Already Here LLC — VP Operations Dashboard
Run: python pipeline/vp_dashboard.py [command]

Commands:
  status          Live revenue dashboard (default)
  init            Initialize / migrate database
  outreach        Preview all 10 Day-1 outreach emails (dry-run)
  won <id> <amt>  Record a closed deal: won 3 1200.00
  lead            Add a lead interactively
  distill <file>  Token-distill a log file and print stats
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Allow imports from pipeline/ directory
sys.path.insert(0, str(Path(__file__).parent))

from revenue_matrix import RevenueMatrix, PHASES, TOTAL_TARGET_USD
from token_distiller import distill_payload

DB_PATH = os.getenv("MESH_DB_PATH", "production_mesh_edge.db")

# ── Slack channel IDs (hardcoded — already created in alreadyherellc.slack.com) ─
SLACK_REVENUE_OPS = "C0B8VN2S89Y"   # #revenue-ops
SLACK_DEALS_WON   = "C0B8VN2RQBC"   # #deals-won
SLACK_GENERAL     = "C0B1XSBS2AF"   # #general

async def _slack_post(channel: str, text: str) -> None:
    """Post to Slack via bot token if available; print locally otherwise."""
    token = os.getenv("SLACK_BOT_TOKEN", "")
    if not token:
        print(f"[Slack ready — add SLACK_BOT_TOKEN to auto-post] {text[:80]}")
        return
    import aiohttp
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {"channel": channel, "text": text, "mrkdwn": True}
    try:
        async with aiohttp.ClientSession() as s:
            async with s.post(
                "https://slack.com/api/chat.postMessage",
                json=payload, headers=headers,
                timeout=aiohttp.ClientTimeout(total=6),
            ) as r:
                body = await r.json()
                if not body.get("ok"):
                    print(f"[Slack error] {body.get('error')}")
    except Exception as exc:
        print(f"[Slack post failed] {exc}")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ── Outreach preview (no webhook needed) ─────────────────────────────────────

from string import Template

_TEMPLATES = {
    "audit": """\
Subject: Infrastructure Audit: Network Latency & Starlink/Failover Optimization — ${company}

Team,

As operations scale at ${company}, network drops and latency bottlenecks directly impact \
your daily bottom line. Already Here LLC specializes in mission-critical IT infrastructure, \
structured Cat6/Cat7 cabling, and high-speed satellite deployments across the Southwest.

We have a crew window open this ${day} to conduct a complete on-site Network Infrastructure \
& Wireless Penetration Audit for your facility. We will identify:

  1. Signal degradation and hardware packet-loss bottlenecks
  2. Optimization paths for your local switch infrastructure
  3. Redundancy failover protocols to guarantee zero-downtime operations

Standard diagnostic: 350 USD. If we find actionable gaps, that fee is credited toward remediation.

Which window works best for your site lead this ${day} — ${time_a} or ${time_b}?

${sender_name}
${sender_title} | ${sender_company}
dispatch@alreadyherellc.com | 602-882-2920
alreadyherellc.com
""",
    "drone": """\
Subject: 48-Hour Orthomosaic Deliverable — Commercial Aerial Survey for ${company}

Team,

High-resolution aerial data is now a competitive edge for commercial real estate, roofing, \
and solar feasibility. Already Here LLC deploys FAA-compliant DJI assets and delivers fully \
processed orthomosaic models within 48 hours of flight.

Availability this ${day} for ${company}. Deliverables:
  - Orthomosaic map (GeoTIFF + web viewer)
  - Surface measurements for roofing or solar layout
  - 4K stills and video for marketing use

Typical engagement: 750–1,200 USD depending on acreage.

Can we confirm scope this ${day} at ${time_a} or ${time_b}?

${sender_name}
${sender_title} | ${sender_company}
dispatch@alreadyherellc.com | 602-882-2920
alreadyherellc.com
""",
    "cabling": """\
Subject: Turnkey Cat6/Cat7 Structured Cabling Proposal — ${company}

Team,

Aging cabling is the silent bottleneck behind most commercial network performance issues. \
Already Here LLC delivers turnkey structured cabling, patch-panel termination, and \
managed-switch integration for mid-market facilities.

Standard commercial package for ${company}:
  - Cat6A or Cat7 installation to TIA-568 spec
  - Patch panel, rack mounting, and cable management
  - Post-installation certification with wiremap documentation

Crew window available starting ${day}. Fixed-price proposal within 24 hours.

Site-walk available at ${time_a} or ${time_b} this ${day}?

${sender_name}
${sender_title} | ${sender_company}
dispatch@alreadyherellc.com | 602-882-2920
alreadyherellc.com
""",
    "logistics": """\
Subject: Freight Capacity & Tech Procurement — ${company}

Team,

Supply chain velocity is the margin lever most mid-market operations leave on the table. \
Already Here LLC operates as a specialized logistics broker with vetted regional carriers \
and direct wholesale technology procurement channels.

For ${company}:
  - Spot and contract freight lane matching (dry van, flatbed, LTL)
  - Technology hardware at wholesale tier
  - Set-aside contract pathways for qualifying business classifications

Placing capacity this week. Can we connect this ${day} at ${time_a} or ${time_b} for a \
10-minute lane-fit review?

${sender_name}
${sender_title} | ${sender_company}
dispatch@alreadyherellc.com | 602-882-2920
alreadyherellc.com
""",
}

_DAY1_TARGETS = [
    {"company": "Southwest Medical Partners",  "service": "audit",     "quote": 350},
    {"company": "Desert Valley Warehousing",   "service": "audit",     "quote": 350},
    {"company": "Sunbelt Logistics Group",     "service": "audit",     "quote": 350},
    {"company": "Mesa Commercial Roofing",     "service": "drone",     "quote": 850},
    {"company": "Arizona Solar Developers",    "service": "drone",     "quote": 1200},
    {"company": "Phoenix Property Management", "service": "drone",     "quote": 750},
    {"company": "Copper State Data Centers",   "service": "cabling",   "quote": 4500},
    {"company": "Southwest Distribution Co.",  "service": "cabling",   "quote": 3800},
    {"company": "Pinnacle Freight Services",   "service": "logistics", "quote": 8000},
    {"company": "Horizon Supply Chain LLC",    "service": "logistics", "quote": 7500},
]

_SVC_PHASE = {"audit": "ALPHA_I", "drone": "ALPHA_II", "cabling": "BETA_I", "logistics": "BETA_II"}
_SVC_TRACK = {"audit": "alpha",   "drone": "alpha",    "cabling": "beta",   "logistics": "beta"}


def _render(service: str, company: str, identity: dict, day: str, ta: str, tb: str) -> str:
    return Template(_TEMPLATES[service]).substitute(
        company=company, day=day, time_a=ta, time_b=tb,
        sender_name=identity.get("name", "Your Name"),
        sender_title=identity.get("title", "VP of Operations"),
        sender_company=identity.get("company", "Already Here LLC"),
    )


async def cmd_init() -> None:
    matrix = RevenueMatrix(DB_PATH)
    await matrix.init()
    print(f"Database initialized: {DB_PATH}")
    await matrix.activate_phase("ALPHA_I")
    await matrix.activate_phase("BETA_I")
    print("ALPHA_I and BETA_I activated.")


async def cmd_status() -> None:
    matrix = RevenueMatrix(DB_PATH)
    await matrix.init()
    await matrix.print_dashboard()

    import aiosqlite
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT id, company_name, service_type, quoted_usd, status, phase_id FROM revenue_leads ORDER BY id DESC LIMIT 20"
        )
        leads = [dict(r) for r in await cur.fetchall()]

    if leads:
        print(f"  {'ID':<4} {'Company':<35} {'Service':<12} {'Quoted':>8} {'Status':<18} Phase")
        print(f"  {'-'*90}")
        for l in leads:
            print(f"  {l['id']:<4} {l['company_name']:<35} {l['service_type']:<12} "
                  f"${l['quoted_usd']:>7,.0f} {l['status']:<18} {l['phase_id']}")
    else:
        print("  No leads yet. Run: python vp_dashboard.py outreach")


async def cmd_outreach(day: str = "Tuesday", ta: str = "09:00", tb: str = "13:00") -> None:
    identity = {
        "name":    os.getenv("OUTREACH_SENDER_NAME",  "Stephen Franklin"),
        "title":   os.getenv("OUTREACH_SENDER_TITLE", "VP of Operations"),
        "company": os.getenv("OUTREACH_COMPANY",      "Already Here LLC"),
    }

    matrix = RevenueMatrix(DB_PATH)
    await matrix.init()

    total_pipeline = 0
    print(f"\n{'='*70}")
    print(f"  ALREADY HERE LLC — DAY 1 OUTREACH PACKAGE ({len(_DAY1_TARGETS)} targets)")
    print(f"  Day: {day}  |  Slots: {ta} / {tb}")
    print(f"{'='*70}\n")

    for i, t in enumerate(_DAY1_TARGETS, 1):
        body = _render(t["service"], t["company"], identity, day, ta, tb)
        total_pipeline += t["quote"]

        # Register in revenue matrix (idempotent on company_name+phase)
        try:
            lead_id = await matrix.add_lead(
                phase_id=_SVC_PHASE[t["service"]],
                track=_SVC_TRACK[t["service"]],
                company_name=t["company"],
                service_type=t["service"],
                quoted_usd=float(t["quote"]),
            )
            await matrix.mark_outreach_sent(lead_id)
            lead_tag = f"Lead #{lead_id}"
        except Exception:
            lead_tag = "(already registered)"

        print(f"-- [{i:02d}] {t['company']}  |  {t['service'].upper()}  |  ${t['quote']:,}  |  {lead_tag}")
        print("-" * 70)
        print(body)

    print(f"\n{'='*70}")
    print(f"  TOTAL PIPELINE VALUE: ${total_pipeline:,}")
    print(f"  Copy each email above into your email client or CRM.")
    print(f"  Set OUTREACH_WEBHOOK_URL to auto-dispatch via API.")
    print(f"{'='*70}\n")


async def cmd_won(lead_id: int, amount: float) -> None:
    matrix = RevenueMatrix(DB_PATH)
    await matrix.init()

    # Fetch lead details before closing so we have company/service for Slack
    import aiosqlite
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT company_name, service_type, phase_id FROM revenue_leads WHERE id=?",
            (lead_id,),
        )
        row = await cur.fetchone()

    await matrix.close_won(lead_id, amount)
    print(f"Lead {lead_id} closed — ${amount:,.2f} recorded.")

    # Pull updated totals for the Slack message
    dash = await matrix.dashboard()
    total = dash["total_realized_usd"]
    gap   = dash["gap_usd"]

    if row:
        company  = row["company_name"]
        service  = row["service_type"]
        phase    = row["phase_id"]
        pct      = round(total / 25500 * 100, 1)
        msg = (
            f":money_with_wings: *DEAL CLOSED — ${amount:,.0f}*\n"
            f"*{company}* | `{service.upper()}` | Phase `{phase}` | Lead #{lead_id}\n"
            f"Total realized: *${total:,.0f}* ({pct}% of $25,500) | Gap: ${gap:,.0f}\n"
            f"`python pipeline/vp_dashboard.py status` for full pipeline"
        )
        await asyncio.gather(
            _slack_post(SLACK_DEALS_WON, msg),
            _slack_post(SLACK_REVENUE_OPS, msg),
        )

    await matrix.print_dashboard()


async def cmd_add_lead(
    company: str, service: str, quote: float,
    contact: str = "", email: str = "", phone: str = ""
) -> None:
    matrix = RevenueMatrix(DB_PATH)
    await matrix.init()
    lead_id = await matrix.add_lead(
        phase_id=_SVC_PHASE.get(service, "ALPHA_I"),
        track=_SVC_TRACK.get(service, "alpha"),
        company_name=company,
        service_type=service,
        quoted_usd=quote,
        contact_name=contact,
        contact_email=email,
        contact_phone=phone,
    )
    print(f"Lead #{lead_id} added: {company} ({service}) ${quote:,.0f}")
    await _slack_post(
        SLACK_REVENUE_OPS,
        f":clipboard: *New lead #{lead_id}* — *{company}* | `{service.upper()}` | Quoted: *${quote:,.0f}*"
    )


async def cmd_distill(filepath: str) -> None:
    text = Path(filepath).read_text(encoding="utf-8", errors="replace")
    for budget in (200, 100, 50):
        result = distill_payload(text, max_tokens=budget, model="llama3.2")
        print(f"\n── Budget {budget} tokens ──────────────────────────────")
        print(result)


# ── Entry ─────────────────────────────────────────────────────────────────────

async def main() -> None:
    args = sys.argv[1:]
    cmd = args[0] if args else "status"

    if cmd == "init":
        await cmd_init()
    elif cmd == "status":
        await cmd_status()
    elif cmd == "outreach":
        day = args[1] if len(args) > 1 else "Tuesday"
        ta  = args[2] if len(args) > 2 else "09:00"
        tb  = args[3] if len(args) > 3 else "13:00"
        await cmd_outreach(day, ta, tb)
    elif cmd == "won":
        if len(args) < 3:
            print("Usage: won <lead_id> <amount>  e.g.  won 1 350.00")
            sys.exit(1)
        await cmd_won(int(args[1]), float(args[2]))
    elif cmd == "lead":
        if len(args) < 4:
            print("Usage: lead <company> <service> <quote_usd>  [contact] [email] [phone]")
            print("Services: audit | drone | cabling | logistics")
            sys.exit(1)
        await cmd_add_lead(
            company=args[1], service=args[2], quote=float(args[3]),
            contact=args[4] if len(args) > 4 else "",
            email=args[5]   if len(args) > 5 else "",
            phone=args[6]   if len(args) > 6 else "",
        )
    elif cmd == "distill":
        if len(args) < 2:
            print("Usage: distill <filepath>")
            sys.exit(1)
        await cmd_distill(args[1])
    else:
        print(__doc__)


if __name__ == "__main__":
    asyncio.run(main())
