from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import Settings
from .db import LeadRepository
from .ollama import OllamaClient


UNIVERSAL_RATE_CARD = {
    "scheduled_field_engineering_hourly": 125,
    "scheduled_minimum_hours": 2,
    "scheduled_dispatch_minimum": 250,
    "advanced_engineering_hourly": 150,
    "same_day_priority_hourly": 175,
    "after_hours_weekend_hourly_range": [187.5, 200],
    "emergency_response_hourly": 225,
    "site_audit_fixed": 1500,
    "priority_retainer_monthly": 2000,
    "priority_retainer_scheduled_hours_range": [8, 10],
    "materials_markup_percent": 20,
    "payment_terms_target": "Net 15",
    "payment_terms_max_without_approval": "Net 30",
}
RATE_POLICY = (
    "Use the Already Here LLC universal Weston rate card for every new quote, outreach draft, "
    "renewal, and change order: $125/hour scheduled field engineering with a two-hour/$250 minimum; "
    "$150/hour advanced engineering or smart hands with a two-hour/$300 minimum; $175/hour same-day "
    "priority with a two-hour/$350 minimum; $187.50-$200/hour after-hours or weekend with a two-hour "
    "minimum; $225/hour emergency response with a two-hour/$450 minimum; $1,500 fixed standardized "
    "site audit; materials at cost plus 20%; Net 15 target and Net 30 maximum without owner approval. "
    "The $2,000/month priority retainer includes approximately 8-10 scheduled support hours; additional "
    "dispatch and project work is billed separately. Fixed-price, route, software, storage, and project "
    "work must be separately scoped. Never discount below $100/hour effective scheduled, $200 per "
    "scheduled dispatch, $125/hour advanced, or $1,250 per site audit without explicit written owner approval. "
    "Existing signed legacy rates are historical facts only and must not be reused for new work."
)

OUTREACH_SCHEMA = {
    "type": "object",
    "required": ["subject", "email_body", "call_script"],
    "properties": {
        "subject": {"type": "string"},
        "email_body": {"type": "string"},
        "call_script": {"type": "string"},
    },
}
COMPLIANCE_SCHEMA = {
    "type": "object",
    "required": ["eligible", "blocking_reasons", "required_evidence"],
    "properties": {
        "eligible": {"type": "boolean"},
        "blocking_reasons": {"type": "array", "items": {"type": "string"}},
        "required_evidence": {"type": "array", "items": {"type": "string"}},
    },
}


def fingerprint(lead: dict[str, Any]) -> str:
    stable = "|".join(str(lead.get(k, "")).strip().lower() for k in ("company_name", "solicitation_id", "source_url"))
    return hashlib.sha256(stable.encode()).hexdigest()


class MedicalAgentMesh:
    def __init__(self, settings: Settings, client: OllamaClient | None = None) -> None:
        settings.validate()
        self.settings = settings
        self.repo = LeadRepository(settings.database_path)
        self.client = client or OllamaClient(settings.ollama_url, settings.ollama_model)

    def load_local_sources(self, path: Path | None = None) -> list[dict[str, Any]]:
        source = path or self.settings.source_file
        if not source.exists():
            return []
        data = json.loads(source.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            raise ValueError("opportunity source must be a JSON array")
        return data

    def compliance_facts(self) -> dict[str, Any]:
        return {
            "auto_liability_usd": self.settings.company_auto_liability,
            "cargo_coverage_usd": self.settings.company_cargo_coverage,
            "hipaa_certified": self.settings.driver_hipaa,
            "bbp_certified": self.settings.driver_bbp,
        }

    def run(self, source_path: Path | None = None) -> dict[str, Any]:
        self.repo.initialize()
        self.client.healthcheck()
        now = datetime.now(timezone.utc).isoformat()
        sources = self.load_local_sources(source_path)
        processed = 0
        for raw in sources:
            lead = dict(raw)
            lead["fingerprint"] = fingerprint(lead)
            self.repo.upsert_lead(lead, now)
            outreach = self.client.generate_json(
                "You are a factual B2B medical-logistics writer. Never invent credentials, insurance, contacts, performance claims, or discounts. " + RATE_POLICY,
                f"Draft an outreach email and call script for this verified prospect: {json.dumps(lead)}. Company facts: {json.dumps(self.compliance_facts())}. Universal rate card: {json.dumps(UNIVERSAL_RATE_CARD)}.",
                OUTREACH_SCHEMA,
            )
            compliance = self.client.generate_json(
                "You are a conservative compliance gate. Missing proof is a blocker. Never infer certifications or insurance.",
                f"Compare this prospect to the verified company facts. Require $1M auto liability, $100k cargo, HIPAA, and BBP unless the source states otherwise. Prospect: {json.dumps(lead)}. Facts: {json.dumps(self.compliance_facts())}.",
                COMPLIANCE_SCHEMA,
            )
            self.repo.save_artifacts(lead["fingerprint"], outreach, compliance, now)
            processed += 1
        return {"processed": processed, "database": str(self.settings.database_path), "send_enabled": self.settings.allow_outreach_send}
