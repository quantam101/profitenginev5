from __future__ import annotations

import pytest

from runtime.edge_failover import EdgeFailoverEngine, EdgeTenant, sign_payload


def test_edge_failover_stages_offline_payload_and_replays(tmp_path):
    tenant = EdgeTenant("alreadyhere", "test-secret", max_token_budget=8)
    payload = " ".join(f"token{i}" for i in range(30))
    signature = sign_payload(tenant, "edge-1", payload)
    engine = EdgeFailoverEngine(
        tenants={tenant.tenant_id: tenant},
        db_path=tmp_path / "edge.db",
    )

    staged = engine.ingest(tenant.tenant_id, "edge-1", payload, signature, server_online=False)

    assert staged["ok"] is True
    assert staged["status"] == "staged"
    assert engine.status()["status_counts"]["staged"] == 1

    replayed = engine.replay(limit=10)

    assert replayed["ok"] is True
    assert replayed["processed"] == 1
    assert engine.status()["status_counts"]["processed"] == 1


def test_edge_failover_rejects_unknown_or_unsigned_payload(tmp_path):
    tenant = EdgeTenant("alreadyhere", "test-secret")
    engine = EdgeFailoverEngine(
        tenants={tenant.tenant_id: tenant},
        db_path=tmp_path / "edge.db",
    )

    with pytest.raises(PermissionError, match="unknown tenant"):
        engine.ingest("missing", "edge-2", "payload", "bad", server_online=False)

    with pytest.raises(PermissionError, match="invalid signature"):
        engine.ingest(tenant.tenant_id, "edge-2", "payload", "bad", server_online=False)
