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
    connector = registry.connectors["playwright_local"]
    registry.connectors["playwright_local"] = type(connector)(
        id=connector.id,
        state="forbidden_without_approval",
        enabled=True,
        permissions=connector.permissions,
    )
    with pytest.raises(RegistryError):
        registry.assert_connector_allowed("local-research", "playwright_local")


# ── New agent tests ───────────────────────────────────────────────────────────

def test_ollama_gateway_disabled_returns_none(monkeypatch):
    """Ollama gateway returns None when GMAOS_LOCAL_MODEL_ENABLED is false."""
    monkeypatch.setenv("GMAOS_LOCAL_MODEL_ENABLED", "false")
    from runtime.ollama_gateway import call_ollama
    assert call_ollama("system", "hello") is None


def test_ollama_gateway_unreachable_returns_none(monkeypatch):
    """Unreachable Ollama endpoint degrades gracefully to None."""
    monkeypatch.setenv("GMAOS_LOCAL_MODEL_ENABLED", "true")
    monkeypatch.setenv("GMAOS_LOCAL_MODEL_ENDPOINT", "http://127.0.0.1:19999")  # nothing there
    monkeypatch.setenv("GMAOS_LOCAL_MODEL_TIMEOUT", "2")
    from runtime.ollama_gateway import call_ollama
    result = call_ollama("system", "hello")
    assert result is None


def test_sovereign_orchestrator_ollama_first(monkeypatch):
    """Orchestrator uses Ollama when available, bypasses Claude."""
    monkeypatch.setenv("GMAOS_LOCAL_MODEL_ENABLED", "true")
    import runtime.ollama_gateway as og
    import runtime.claude_gateway as cg
    monkeypatch.setattr(og, "call_ollama", lambda s, m, max_tokens=512: "Ollama plan: step A, step B.")
    monkeypatch.setattr(cg, "call_claude", lambda s, m, max_tokens=512: "Should not be called")
    import importlib
    import runtime.agent_impls.sovereign_orchestrator as mod
    importlib.reload(mod)
    agent = mod.Agent()
    result = agent.run("Run profit cycle", "", ["local_files"])
    assert result.metrics["tier"] == "ollama"
    assert "Ollama plan" in result.output


def test_sovereign_orchestrator_claude_fallback_when_ollama_absent(monkeypatch):
    """Orchestrator falls back to Claude when Ollama returns None."""
    import runtime.ollama_gateway as og
    import runtime.claude_gateway as cg
    monkeypatch.setattr(og, "call_ollama", lambda s, m, max_tokens=512: None)
    monkeypatch.setattr(cg, "call_claude", lambda s, m, max_tokens=512: "Claude plan: step X.")
    import importlib
    import runtime.agent_impls.sovereign_orchestrator as mod
    importlib.reload(mod)
    agent = mod.Agent()
    result = agent.run("Run profit cycle", "", ["local_files"])
    assert result.metrics["tier"] == "claude_api"
    assert "Claude plan" in result.output


def test_router_local_model_tier_when_ollama_enabled(monkeypatch):
    """Router selects LOCAL_MODEL tier for medium complexity when Ollama is enabled."""
    monkeypatch.setenv("GMAOS_LOCAL_MODEL_ENABLED", "true")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    import importlib
    import runtime.local_model_router as mod
    importlib.reload(mod)
    router = mod.LocalModelRouter()
    route = router.route(0.45)  # above DETERMINISTIC threshold, below LOCAL_MODEL threshold
    assert route.decision.tier == "LOCAL_MODEL"


def test_router_claude_tier_when_no_ollama_but_key_present(monkeypatch):
    """Router selects CLAUDE_API tier when Ollama is off but Claude key is set."""
    monkeypatch.setenv("GMAOS_LOCAL_MODEL_ENABLED", "false")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "anthropic-ci-test")
    import importlib
    import runtime.local_model_router as mod
    importlib.reload(mod)
    router = mod.LocalModelRouter()
    route = router.route(0.45)
    assert route.decision.tier == "CLAUDE_API"


def test_router_human_review_when_no_models_high_complexity(monkeypatch):
    """Router queues for human review when no models available and complexity is high."""
    monkeypatch.setenv("GMAOS_LOCAL_MODEL_ENABLED", "false")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    import importlib
    import runtime.local_model_router as mod
    importlib.reload(mod)
    router = mod.LocalModelRouter()
    route = router.route(0.95)
    assert route.decision.tier == "HUMAN_REVIEW_QUEUE"


def test_sovereign_orchestrator_fallback_without_key(monkeypatch):
    """Without an API key the orchestrator returns a deterministic fallback."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    # Reload module to pick up env change
    import importlib
    import runtime.agent_impls.sovereign_orchestrator as mod
    importlib.reload(mod)
    agent = mod.Agent()
    result = agent.run("Run a profit cycle", "", ["local_files"])
    assert result.metrics["tier"] == "deterministic_fallback"
    assert "SOVEREIGN_ORCHESTRATOR_RESULT" in result.output
    assert result.metrics["agent"] == "sovereign-orchestrator"


def test_sovereign_orchestrator_with_mocked_claude(monkeypatch):
    """With a key present and Claude mocked, the orchestrator returns AI output."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "anthropic-ci-test-key")
    import runtime.claude_gateway as gw
    monkeypatch.setattr(gw, "call_claude", lambda system, msg, max_tokens=1024: "Mocked plan: step 1, step 2.")
    import importlib
    import runtime.agent_impls.sovereign_orchestrator as mod
    importlib.reload(mod)
    agent = mod.Agent()
    result = agent.run("Run a profit cycle", "context here", ["local_files"])
    assert result.metrics["tier"] == "claude_api"
    assert "SOVEREIGN_ORCHESTRATOR_RESULT" in result.output
    assert "Mocked plan" in result.output


def test_lifelong_catch_correct_fallback_without_key(tmp_path, monkeypatch):
    """Without an API key the LC&C agent skips recording and returns a stub."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("GMAOS_CORRECTIONS_PATH", str(tmp_path / "corrections.jsonl"))
    import importlib
    import runtime.agent_impls.lifelong_catch_correct as mod
    importlib.reload(mod)
    agent = mod.Agent()
    result = agent.run("Self-improve prompts", "", ["local_files"])
    assert result.metrics["tier"] == "deterministic_fallback"
    assert "LC&C_RESULT" in result.output
    assert not (tmp_path / "corrections.jsonl").exists()


def test_lifelong_catch_correct_records_with_mocked_claude(tmp_path, monkeypatch):
    """With Claude mocked, the LC&C agent records the improvement to disk."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "anthropic-ci-test-key")
    monkeypatch.setenv("GMAOS_CORRECTIONS_PATH", str(tmp_path / "corrections.jsonl"))
    import runtime.claude_gateway as gw
    monkeypatch.setattr(gw, "call_claude", lambda system, msg, max_tokens=256: "Rewrite seo_title prompt to include keyword in first 5 words.")
    import importlib
    import runtime.agent_impls.lifelong_catch_correct as mod
    importlib.reload(mod)
    agent = mod.Agent()
    result = agent.run("Self-improve", "", ["local_files"])
    assert result.metrics["tier"] == "claude_api"
    assert "LC&C_RESULT" in result.output
    corrections_file = tmp_path / "corrections.jsonl"
    assert corrections_file.exists()
    import json
    record = json.loads(corrections_file.read_text())
    assert record["category"] == "lcc_self_improve"
    assert "seo_title" in record["correction"]


def test_lifelong_catch_correct_registered_in_registry():
    """LC&C agent must be registered and allowed to use local_files connector."""
    registry = RuntimeRegistry()
    # Should not raise
    registry.assert_connector_allowed("lifelong-catch-correct", "local_files")


def test_sovereign_orchestrator_dispatches_end_to_end(tmp_path, monkeypatch):
    """Full stack: sovereign-orchestrator routes through core to Claude mock."""
    monkeypatch.setenv("GMAOS_AUDIT_LOG", str(tmp_path / "audit.jsonl"))
    monkeypatch.setenv("GMAOS_APPROVAL_DB", str(tmp_path / "approvals.json"))
    monkeypatch.setenv("GMAOS_VECTOR_CACHE", str(tmp_path / "vector.sqlite3"))
    monkeypatch.setenv("GMAOS_EMBEDDING_DIM", "4")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "anthropic-ci-test-key")
    import runtime.claude_gateway as gw
    monkeypatch.setattr(gw, "call_claude", lambda system, msg, max_tokens=512: "Cycle plan: scan trends -> draft -> publish.")
    import importlib
    import runtime.agent_impls.sovereign_orchestrator as mod
    importlib.reload(mod)
    core = SovereignAutomationCore()
    result = core.execute(
        "system",
        "context",
        "Run the profit cycle",
        [0.5, 0.5, 0.5, 0.5],
        agent_id="sovereign-orchestrator",
    )
    assert result.status == "ok"
    assert "SOVEREIGN_ORCHESTRATOR_RESULT" in result.output


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
