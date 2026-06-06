from __future__ import annotations

from runtime.enterprise_mesh import EnterpriseMesh


def test_enterprise_mesh_dispatches_and_snapshots(tmp_path):
    mesh = EnterpriseMesh(db_path=tmp_path / "mesh.db", max_workers=2)

    payload = mesh.dispatch(
        ["free-tier-cost-guard", "motivation-engine"],
        "prove revenue before selling hosted software",
    )

    assert payload["ok"] is True
    assert payload["failed_count"] == 0
    assert payload["agent_count"] == 2
    assert {result["mode"] for result in payload["results"]} == {"live_parallel_worker"}

    readiness = mesh.readiness()
    assert readiness["ok"] is True
    assert readiness["snapshots"] == 2


def test_enterprise_mesh_reports_missing_agent_without_fake_success(tmp_path):
    mesh = EnterpriseMesh(db_path=tmp_path / "mesh.db", max_workers=1)

    payload = mesh.dispatch(["missing-agent"], "test deterministic failure")

    assert payload["ok"] is False
    assert payload["failed_count"] == 1
    assert payload["results"][0]["mode"] == "deterministic_error"
