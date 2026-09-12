from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import Settings
from .db import LeadRepository
from .ollama import OllamaClient


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
                "You are a factual B2B medical-logistics writer. Never invent credentials, insurance, contacts, or performance claims.",
                f"Draft an outreach email and call script for this verified prospect: {json.dumps(lead)}. Company facts: {json.dumps(self.compliance_facts())}.",
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

