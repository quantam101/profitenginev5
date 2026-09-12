from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator


SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_key TEXT NOT NULL UNIQUE,
  started_at TEXT NOT NULL,
  completed_at TEXT,
  status TEXT NOT NULL CHECK(status IN ('running','completed','failed')),
  error TEXT
);
CREATE TABLE IF NOT EXISTS leads (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  fingerprint TEXT NOT NULL UNIQUE,
  company_name TEXT NOT NULL,
  category TEXT NOT NULL,
  contact_name TEXT,
  contact_role TEXT,
  phone TEXT,
  email TEXT,
  source_url TEXT NOT NULL,
  solicitation_id TEXT,
  equipment_type TEXT,
  deadline TEXT,
  outreach_status TEXT NOT NULL DEFAULT 'new',
  compliance_status TEXT NOT NULL DEFAULT 'unverified',
  compliance_json TEXT NOT NULL DEFAULT '{}',
  outreach_json TEXT NOT NULL DEFAULT '{}',
  discovered_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(outreach_status, compliance_status);
"""


class LeadRepository:
    def __init__(self, path: Path) -> None:
        self.path = path

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.path, timeout=30)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA busy_timeout=30000")
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def initialize(self) -> None:
        with self.connect() as conn:
            conn.executescript(SCHEMA)

    def upsert_lead(self, lead: dict[str, Any], now: str) -> None:
        required = ("fingerprint", "company_name", "category", "source_url")
        missing = [key for key in required if not str(lead.get(key, "")).strip()]
        if missing:
            raise ValueError(f"lead is missing required fields: {', '.join(missing)}")
        columns = [
            "fingerprint", "company_name", "category", "contact_name", "contact_role",
            "phone", "email", "source_url", "solicitation_id", "equipment_type", "deadline",
        ]
        values = [lead.get(key) for key in columns]
        with self.connect() as conn:
            conn.execute(
                f"""INSERT INTO leads ({','.join(columns)}, discovered_at, updated_at)
                VALUES ({','.join('?' for _ in columns)}, ?, ?)
                ON CONFLICT(fingerprint) DO UPDATE SET
                  company_name=excluded.company_name, category=excluded.category,
                  contact_name=excluded.contact_name, contact_role=excluded.contact_role,
                  phone=excluded.phone, email=excluded.email, source_url=excluded.source_url,
                  solicitation_id=excluded.solicitation_id, equipment_type=excluded.equipment_type,
                  deadline=excluded.deadline, updated_at=excluded.updated_at""",
                (*values, now, now),
            )

    def save_artifacts(self, fingerprint: str, outreach: dict[str, Any], compliance: dict[str, Any], now: str) -> None:
        status = "eligible" if compliance.get("eligible") is True else "blocked"
        with self.connect() as conn:
            changed = conn.execute(
                "UPDATE leads SET outreach_json=?, compliance_json=?, compliance_status=?, outreach_status='drafted', updated_at=? WHERE fingerprint=?",
                (json.dumps(outreach, sort_keys=True), json.dumps(compliance, sort_keys=True), status, now, fingerprint),
            ).rowcount
            if changed != 1:
                raise KeyError(f"unknown lead fingerprint: {fingerprint}")

    def list_leads(self) -> list[dict[str, Any]]:
        with self.connect() as conn:
            return [dict(row) for row in conn.execute("SELECT * FROM leads ORDER BY id")]

