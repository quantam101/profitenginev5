"""
30-Day Revenue Execution Matrix — Already Here LLC
Dual-Track Velocity Model: Track Alpha (cash-flow) + Track Beta ($25k scaler).
Persisted in WAL SQLite alongside the mesh engine ledger.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import aiosqlite

_DB_PATH = os.getenv("MESH_DB_PATH", "production_mesh_edge.db")


# ── Phase definitions ─────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Phase:
    phase_id: str          # e.g. "ALPHA_I"
    track: str             # "alpha" | "beta"
    name: str
    day_start: int
    day_end: int
    target_usd: float
    primary_driver: str
    tactical_action: str


PHASES: List[Phase] = [
    # ── Track Alpha: Immediate Cash-Flow ──────────────────────────────────────
    Phase(
        phase_id="ALPHA_I",
        track="alpha",
        name="Commercial Network Optimization",
        day_start=1, day_end=3,
        target_usd=500.0,
        primary_driver="WiFi/Starlink failover audits + Cat6/Cat7 tune-ups",
        tactical_action=(
            "Target local mid-tier commercial hubs (medical clinics, warehouses). "
            "Deploy rapid on-site Network Infrastructure & Wireless Penetration Audits at $350/site. "
            "Credit diagnostic toward remediation if gaps found."
        ),
    ),
    Phase(
        phase_id="ALPHA_II",
        track="alpha",
        name="High-Value Aerial Data",
        day_start=4, day_end=7,
        target_usd=1_500.0,
        primary_driver="DJI commercial drone surveys",
        tactical_action=(
            "Deploy DJI assets for commercial real estate, roofing, and solar site surveys. "
            "Deliver orthomosaic mapping models within 48 hours of flight. "
            "Target property management firms and roofing contractors in Southwest region."
        ),
    ),
    # ── Track Beta: $25k Scaler ───────────────────────────────────────────────
    Phase(
        phase_id="BETA_I",
        track="beta",
        name="Commercial Infrastructure Contracts",
        day_start=8, day_end=15,
        target_usd=7_500.0,
        primary_driver="Structured cabling / server rack installations",
        tactical_action=(
            "Close two mid-market structured cabling and server rack installations. "
            "Leverage local commercial pipelines, target warehouses and logistics hubs. "
            "Package Cat6/Cat7 + patch panel + managed switch as a bundled turnkey contract."
        ),
    ),
    Phase(
        phase_id="BETA_II",
        track="beta",
        name="Logistics Brokerage & Tech Procurement",
        day_start=16, day_end=30,
        target_usd=16_000.0,
        primary_driver="Freight lane matching + sub-contracting procurement",
        tactical_action=(
            "Scale freight lane matching via broker relationships. "
            "Execute sub-contracting procurement pathways via business set-aside avenues. "
            "Layer tech hardware procurement margins on top of service contracts."
        ),
    ),
]

TOTAL_TARGET_USD = sum(p.target_usd for p in PHASES)  # $25,500


# ── Database schema ───────────────────────────────────────────────────────────

_SCHEMA = """
CREATE TABLE IF NOT EXISTS revenue_phases (
    phase_id        TEXT PRIMARY KEY,
    track           TEXT NOT NULL,
    name            TEXT NOT NULL,
    day_start       INTEGER NOT NULL,
    day_end         INTEGER NOT NULL,
    target_usd      REAL NOT NULL,
    realized_usd    REAL DEFAULT 0.0,
    status          TEXT DEFAULT 'pending',   -- pending | active | complete | blocked
    started_at      TEXT,
    completed_at    TEXT,
    notes           TEXT
);

CREATE TABLE IF NOT EXISTS revenue_leads (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    phase_id        TEXT NOT NULL REFERENCES revenue_phases(phase_id),
    track           TEXT NOT NULL,
    company_name    TEXT NOT NULL,
    contact_name    TEXT,
    contact_email   TEXT,
    contact_phone   TEXT,
    service_type    TEXT,           -- audit | drone | cabling | logistics
    quoted_usd      REAL,
    realized_usd    REAL DEFAULT 0.0,
    status          TEXT DEFAULT 'prospecting',  -- prospecting | outreach_sent | follow_up | won | lost
    outreach_sent_at TEXT,
    won_at          TEXT,
    notes           TEXT,
    inserted_at     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS revenue_events (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    phase_id    TEXT,
    lead_id     INTEGER,
    event_type  TEXT NOT NULL,
    amount_usd  REAL DEFAULT 0.0,
    description TEXT,
    created_at  TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_leads_status   ON revenue_leads(status);
CREATE INDEX IF NOT EXISTS idx_leads_phase    ON revenue_leads(phase_id);
CREATE INDEX IF NOT EXISTS idx_events_phase   ON revenue_events(phase_id);
"""


# ── Matrix manager ────────────────────────────────────────────────────────────

class RevenueMatrix:
    def __init__(self, db_path: str = _DB_PATH) -> None:
        self._path = db_path

    async def init(self) -> None:
        async with aiosqlite.connect(self._path) as db:
            await db.executescript(_SCHEMA)
            # Seed phase rows (idempotent)
            await db.executemany(
                """INSERT OR IGNORE INTO revenue_phases
                   (phase_id, track, name, day_start, day_end, target_usd)
                   VALUES (?,?,?,?,?,?)""",
                [
                    (p.phase_id, p.track, p.name, p.day_start, p.day_end, p.target_usd)
                    for p in PHASES
                ],
            )
            await db.commit()

    async def dashboard(self) -> Dict[str, Any]:
        async with aiosqlite.connect(self._path) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute(
                "SELECT phase_id, track, name, target_usd, realized_usd, status FROM revenue_phases ORDER BY day_start"
            )
            phases = [dict(r) for r in await cur.fetchall()]

            cur = await db.execute(
                "SELECT COUNT(*) as total, SUM(CASE WHEN status='won' THEN 1 ELSE 0 END) as won FROM revenue_leads"
            )
            lead_stats = dict(await cur.fetchone())

        total_realized = sum(p["realized_usd"] for p in phases)
        alpha_realized = sum(p["realized_usd"] for p in phases if p["track"] == "alpha")
        beta_realized  = sum(p["realized_usd"] for p in phases if p["track"] == "beta")

        return {
            "total_target_usd":   TOTAL_TARGET_USD,
            "total_realized_usd": total_realized,
            "gap_usd":            TOTAL_TARGET_USD - total_realized,
            "completion_pct":     round(total_realized / TOTAL_TARGET_USD * 100, 1),
            "alpha_realized_usd": alpha_realized,
            "beta_realized_usd":  beta_realized,
            "lead_total":         lead_stats["total"],
            "lead_won":           lead_stats["won"],
            "phases":             phases,
        }

    async def add_lead(
        self,
        phase_id: str,
        track: str,
        company_name: str,
        service_type: str,
        quoted_usd: float,
        contact_name: str = "",
        contact_email: str = "",
        contact_phone: str = "",
        notes: str = "",
    ) -> int:
        ts = _now()
        async with aiosqlite.connect(self._path) as db:
            cur = await db.execute(
                """INSERT INTO revenue_leads
                   (phase_id, track, company_name, contact_name, contact_email, contact_phone,
                    service_type, quoted_usd, notes, inserted_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (phase_id, track, company_name, contact_name, contact_email,
                 contact_phone, service_type, quoted_usd, notes, ts),
            )
            await db.execute(
                "INSERT INTO revenue_events (phase_id, lead_id, event_type, amount_usd, description, created_at) VALUES (?,?,?,?,?,?)",
                (phase_id, cur.lastrowid, "lead_added", quoted_usd, f"New lead: {company_name}", ts),
            )
            await db.commit()
            return cur.lastrowid

    async def mark_outreach_sent(self, lead_id: int) -> None:
        async with aiosqlite.connect(self._path) as db:
            await db.execute(
                "UPDATE revenue_leads SET status='outreach_sent', outreach_sent_at=? WHERE id=?",
                (_now(), lead_id),
            )
            await db.commit()

    async def close_won(self, lead_id: int, realized_usd: float) -> None:
        ts = _now()
        async with aiosqlite.connect(self._path) as db:
            cur = await db.execute("SELECT phase_id, quoted_usd FROM revenue_leads WHERE id=?", (lead_id,))
            row = await cur.fetchone()
            if not row:
                raise ValueError(f"Lead {lead_id} not found")
            phase_id = row[0]

            await db.execute(
                "UPDATE revenue_leads SET status='won', realized_usd=?, won_at=? WHERE id=?",
                (realized_usd, ts, lead_id),
            )
            await db.execute(
                "UPDATE revenue_phases SET realized_usd=realized_usd+? WHERE phase_id=?",
                (realized_usd, phase_id),
            )
            # Auto-complete phase if target reached
            await db.execute(
                """UPDATE revenue_phases SET status='complete', completed_at=?
                   WHERE phase_id=? AND realized_usd >= target_usd AND status != 'complete'""",
                (ts, phase_id),
            )
            await db.execute(
                "INSERT INTO revenue_events (phase_id, lead_id, event_type, amount_usd, description, created_at) VALUES (?,?,?,?,?,?)",
                (phase_id, lead_id, "won", realized_usd, f"Closed ${realized_usd:,.0f}", ts),
            )
            await db.commit()

    async def activate_phase(self, phase_id: str) -> None:
        async with aiosqlite.connect(self._path) as db:
            await db.execute(
                "UPDATE revenue_phases SET status='active', started_at=? WHERE phase_id=? AND status='pending'",
                (_now(), phase_id),
            )
            await db.commit()

    async def pending_leads(self, track: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        async with aiosqlite.connect(self._path) as db:
            db.row_factory = aiosqlite.Row
            if track:
                cur = await db.execute(
                    "SELECT * FROM revenue_leads WHERE status NOT IN ('won','lost') AND track=? LIMIT ?",
                    (track, limit),
                )
            else:
                cur = await db.execute(
                    "SELECT * FROM revenue_leads WHERE status NOT IN ('won','lost') LIMIT ?",
                    (limit,),
                )
            return [dict(r) for r in await cur.fetchall()]

    async def print_dashboard(self) -> None:
        d = await self.dashboard()
        bar_len = 30
        filled = round(d["completion_pct"] / 100 * bar_len)
        bar = "█" * filled + "░" * (bar_len - filled)

        print("\n" + "=" * 60)
        print("  Already Here LLC -- 30-Day Revenue Matrix")
        print("=" * 60)
        print(f"  [{bar}] {d['completion_pct']}%")
        print(f"  Realized: ${d['total_realized_usd']:>10,.2f} / ${d['total_target_usd']:,.0f}")
        print(f"  Gap:      ${d['gap_usd']:>10,.2f}")
        print(f"  Leads:    {d['lead_won']} won / {d['lead_total']} total")
        print(f"\n  Track Alpha (cash-flow): ${d['alpha_realized_usd']:,.2f}")
        print(f"  Track Beta  ($25k goal): ${d['beta_realized_usd']:,.2f}")
        print(f"\n  {'Phase':<12} {'Track':<6} {'Target':>10} {'Realized':>10} {'Status'}")
        print("  " + "-" * 56)
        for p in d["phases"]:
            print(
                f"  {p['phase_id']:<12} {p['track']:<6} "
                f"${p['target_usd']:>9,.0f} ${p['realized_usd']:>9,.2f} {p['status']}"
            )
        print("=" * 60 + "\n")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ── CLI ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    async def _cli() -> None:
        matrix = RevenueMatrix()
        await matrix.init()
        await matrix.print_dashboard()

    asyncio.run(_cli())
