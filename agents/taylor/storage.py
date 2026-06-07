"""SQLite persistence for Taylor calls, leads, appointments, and payments."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Appointment:
    id: int
    slot_datetime: str
    service_type: str
    site_address: str
    contact_phone: str
    contact_name: str
    company_name: str


class TaylorStore:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        parent = Path(db_path).expanduser().resolve().parent
        parent.mkdir(parents=True, exist_ok=True)
        self._init()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS taylor_appointments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    slot_datetime TEXT NOT NULL,
                    service_type TEXT NOT NULL,
                    site_address TEXT NOT NULL,
                    contact_phone TEXT NOT NULL,
                    contact_name TEXT NOT NULL DEFAULT '',
                    company_name TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS taylor_payment_links (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    call_id TEXT NOT NULL DEFAULT '',
                    invoice_id TEXT NOT NULL,
                    amount_cents INTEGER NOT NULL,
                    billing_zip TEXT NOT NULL DEFAULT '',
                    checkout_url TEXT NOT NULL,
                    stripe_session_id TEXT NOT NULL DEFAULT '',
                    phone_number TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS taylor_call_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    call_id TEXT NOT NULL DEFAULT '',
                    event_type TEXT NOT NULL,
                    payload_json TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL
                )
                """
            )

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def add_appointment(
        self,
        *,
        slot_datetime: str,
        service_type: str,
        site_address: str,
        contact_phone: str,
        contact_name: str = "",
        company_name: str = "",
    ) -> Appointment:
        with self._connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO taylor_appointments
                (slot_datetime, service_type, site_address, contact_phone, contact_name, company_name, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (slot_datetime, service_type, site_address, contact_phone, contact_name, company_name, self._now()),
            )
            appointment_id = int(cur.lastrowid)
        return Appointment(
            id=appointment_id,
            slot_datetime=slot_datetime,
            service_type=service_type,
            site_address=site_address,
            contact_phone=contact_phone,
            contact_name=contact_name,
            company_name=company_name,
        )

    def add_payment_link(
        self,
        *,
        call_id: str,
        invoice_id: str,
        amount_cents: int,
        billing_zip: str,
        checkout_url: str,
        stripe_session_id: str = "",
        phone_number: str = "",
    ) -> int:
        with self._connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO taylor_payment_links
                (call_id, invoice_id, amount_cents, billing_zip, checkout_url, stripe_session_id, phone_number, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    call_id,
                    invoice_id,
                    amount_cents,
                    billing_zip,
                    checkout_url,
                    stripe_session_id,
                    phone_number,
                    self._now(),
                ),
            )
            return int(cur.lastrowid)

    def log_event(self, *, call_id: str, event_type: str, payload_json: str = "{}") -> int:
        with self._connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO taylor_call_events (call_id, event_type, payload_json, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (call_id, event_type, payload_json, self._now()),
            )
            return int(cur.lastrowid)

    def counts(self) -> dict[str, Any]:
        with self._connect() as conn:
            appointments = conn.execute("SELECT COUNT(*) FROM taylor_appointments").fetchone()[0]
            payments = conn.execute("SELECT COUNT(*) FROM taylor_payment_links").fetchone()[0]
            events = conn.execute("SELECT COUNT(*) FROM taylor_call_events").fetchone()[0]
        return {"appointments": appointments, "payment_links": payments, "events": events}

