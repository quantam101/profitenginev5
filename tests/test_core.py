from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from runtime.api import app
from runtime.registry import RegistryError, RuntimeRegistry
from runtime.sovereign_core import SovereignAutomationCore


def test_core_smoke(tmp_path, monkeypatch):
    monkeypatch.setenv("GMAOS_AUDIT_LOG", str(tmp_path / "audit.jsonl"))
    monkeypatch.setenv("GMAOS_APPROVAL_DB", str(tmp_path / "approvals.json"))
    monkeypatch.setenv("GMAOS_VECTOR_CACHE", str(tmp_path / "vector.sqlite3"))
    monkeypatch.setenv("GMAOS_EMBEDDING_DIM", "4")
    core = SovereignAutomationCore()
    result = core.execute("system", "context", "Create a local draft", [0.1, 0.1, 0.1, 0.1])
    assert result.status == "ok"
    assert result.route_tier == "DETERMINISTIC_LOCAL"
    assert result.details["connector_id"] == "local_files"


def test_complex_work_requires_approval(tmp_path, monkeypatch):
    monkeypatch.setenv("GMAOS_AUDIT_LOG", str(tmp_path / "audit.jsonl"))
    monkeypatch.setenv("GMAOS_APPROVAL_DB", str(tmp_path / "approvals.json"))
    monkeypatch.setenv("GMAOS_VECTOR_CACHE", str(tmp_path / "vector.sqlite3"))
    monkeypatch.setenv("GMAOS_EMBEDDING_DIM", "4")
    core = SovereignAutomationCore()
    result = core.execute("system", "context", "Deploy production and send client email", [0.2, 0.2, 0.2, 0.2])
    assert result.status == "approval_required"


def test_stale_module_source_removed():
    modules_dir = Path("modules")
    assert not modules_dir.exists()


def test_local_research_agent_dispatches_end_to_end(tmp_path, monkeypatch):
    monkeypatch.setenv("GMAOS_AUDIT_LOG", str(tmp_path / "audit.jsonl"))
    monkeypatch.setenv("GMAOS_APPROVAL_DB", str(tmp_path / "approvals.json"))
    monkeypatch.setenv("GMAOS_VECTOR_CACHE", str(tmp_path / "vector.sqlite3"))
    monkeypatch.setenv("GMAOS_EMBEDDING_DIM", "4")
    monkeypatch.setenv("GMAOS_EMBEDDING_DIM", "4")
    monkeypatch.setenv("GMAOS_EMBEDDING_DIM", "4")
    core = SovereignAutomationCore()
    result = core.execute(
        "system",
        "source note one\nsource note two",
        "Draft a local research summary",
        [0.3, 0.3, 0.3, 0.3],
        agent_id="local-research",
    )
    assert result.status == "ok"
    assert result.route_tier == "DETERMINISTIC_LOCAL"
    assert "LOCAL_RESEARCH_RESULT" in result.output
    assert result.details["agent_metrics"]["evidence_notes"] >= 1


def test_registry_blocks_unapproved_connector():
    registry = RuntimeRegistry()
    with pytest.raises(RegistryError):
        registry.assert_connector_allowed("local-research", "openai_api")


def test_registry_blocks_enabled_but_non_free_connector_state():
    registry = RuntimeRegistry()
    connector = registry.connectors["github_write"]
    registry.connectors["github_write"] = type(connector)(
        id=connector.id,
        state="forbidden_without_approval",
        enabled=True,
        permissions=connector.permissions,
    )
    with pytest.raises(RegistryError):
        registry.assert_connector_allowed("local-engineering", "github_write")


def test_runtime_api_serves_health_and_execute(tmp_path, monkeypatch):
    monkeypatch.setenv("GMAOS_AUDIT_LOG", str(tmp_path / "audit.jsonl"))
    monkeypatch.setenv("GMAOS_APPROVAL_DB", str(tmp_path / "approvals.json"))
    monkeypatch.setenv("GMAOS_VECTOR_CACHE", str(tmp_path / "vector.sqlite3"))
    monkeypatch.setenv("GMAOS_EMBEDDING_DIM", "4")
    client = TestClient(app)

    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["ok"] is True
    assert health.headers["x-request-id"]

    execution = client.post(
        "/execute",
        json={
            "objective": "Draft a local research summary",
            "dynamic_context": "approved source note",
            "embedding_vector": [0.4, 0.4, 0.4, 0.4],
            "agent_id": "local-research",
        },
    )
    assert execution.status_code == 200
    assert execution.json()["status"] == "ok"
