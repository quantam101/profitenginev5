from pathlib import Path
import tempfile
import unittest

from medical_agent_mesh.config import Settings
from medical_agent_mesh.db import LeadRepository
from medical_agent_mesh.pipeline import MedicalAgentMesh, fingerprint


class FakeOllama:
    def healthcheck(self):
        return None

    def generate_json(self, system, prompt, schema):
        if "eligible" in schema.get("required", []):
            return {"eligible": False, "blocking_reasons": ["insurance evidence missing"], "required_evidence": ["COI"]}
        return {"subject": "Local DME support", "email_body": "Verified capabilities only.", "call_script": "Request onboarding."}


def settings(tmp_path: Path) -> Settings:
    return Settings(database_path=tmp_path / "mesh.sqlite3", source_file=tmp_path / "source.json")


class MedicalAgentMeshTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def test_loopback_guard(self):
        with self.assertRaisesRegex(ValueError, "loopback-only"):
            Settings(ollama_url="http://192.168.1.2:11434", database_path=self.tmp_path / "x.db").validate()

    def test_upsert_is_idempotent(self):
        repo = LeadRepository(self.tmp_path / "mesh.db")
        repo.initialize()
        lead = {"fingerprint": "abc", "company_name": "Acme", "category": "DME", "source_url": "https://example.test"}
        repo.upsert_lead(lead, "2026-09-12T00:00:00Z")
        repo.upsert_lead(lead, "2026-09-12T01:00:00Z")
        self.assertEqual(len(repo.list_leads()), 1)

    def test_pipeline_persists_drafts_and_blocks_unverified_claims(self):
        cfg = settings(self.tmp_path)
        cfg.source_file.write_text('[{"company_name":"Acme DME","category":"DME","source_url":"https://example.test/acme","contact_role":"Logistics Manager"}]')
        mesh = MedicalAgentMesh(cfg, FakeOllama())
        result = mesh.run()
        row = mesh.repo.list_leads()[0]
        self.assertEqual(result["processed"], 1)
        self.assertEqual(row["outreach_status"], "drafted")
        self.assertEqual(row["compliance_status"], "blocked")
        self.assertEqual(row["fingerprint"], fingerprint({"company_name":"Acme DME","source_url":"https://example.test/acme"}))


if __name__ == "__main__":
    unittest.main()
