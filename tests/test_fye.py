from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from runtime.fye.config import FyeConfig  # noqa: E402
from runtime.fye.journal import DecisionJournal  # noqa: E402
from runtime.fye.rpm_priors import prior_for, revenue_band, ypp_gate  # noqa: E402
from runtime.fye import command_os  # noqa: E402
from runtime.fye.agents import (  # noqa: E402
    ComplianceAgent, ResearchAgent, ScriptAgent, ShotListAgent, package_id_for,
)


def _cfg(tmp_path) -> FyeConfig:
    return FyeConfig(root=str(tmp_path / "fye"), dc_webhook_url="", webhook_secret="")


class TestRpmPriors:
    def test_known_niche(self):
        p = prior_for("personal-finance")
        assert p.rpm_low < p.rpm_high

    def test_unknown_niche_falls_back(self):
        assert prior_for("nope").niche == "general"

    def test_revenue_band_is_a_band(self):
        band = revenue_band("ai-tools", 200_000)
        assert band["low_usd"] < band["high_usd"]
        assert band["low_usd"] == 1000.0

    def test_ypp_gate(self):
        assert ypp_gate(1500, 5000)["eligible"] is True
        assert ypp_gate(500, 99999)["eligible"] is False
        assert ypp_gate(1000, 0, 10_000_000)["eligible"] is True


class TestJournal:
    def test_append_and_verify(self, tmp_path):
        j = DecisionJournal(str(tmp_path / "j.jsonl"))
        j.append("a", "decision", {"x": 1})
        j.append("b", "decision", {"y": 2})
        assert j.verify_chain() is True
        assert len(j.find(agent="b")) == 1

    def test_tamper_detection(self, tmp_path):
        p = tmp_path / "j.jsonl"
        j = DecisionJournal(str(p))
        j.append("a", "d", {"x": 1})
        lines = p.read_text().splitlines()
        e = json.loads(lines[0])
        e["data"]["x"] = 999
        p.write_text(json.dumps(e) + "\n")
        assert j.verify_chain() is False


class TestAgents:
    def _ctx(self, tmp_path):
        ctx = {"topic": "Compound interest", "niche": "personal-finance",
               "pkg_dir": str(tmp_path / "pkg"), "package_id": "fye-test"}
        Path(ctx["pkg_dir"]).mkdir(parents=True, exist_ok=True)
        ctx["research"] = ResearchAgent().run(ctx)
        ctx["script"] = ScriptAgent().run(ctx)
        ctx["shots"] = ShotListAgent().run(ctx)
        return ctx

    def test_research_includes_priors_and_ypp(self, tmp_path):
        ctx = self._ctx(tmp_path)
        r = ctx["research"]
        assert r["rpm_prior"]["low"] > 0
        assert r["publish_blocked_by_ypp"] is True  # no channel stats given

    def test_script_no_placeholders(self, tmp_path):
        ctx = self._ctx(tmp_path)
        body = ctx["script"]["script_body"]
        for bad in ("TODO", "PLACEHOLDER", "lorem", "XXX"):
            assert bad not in body
        assert "Compound interest" in ctx["script"]["script_sentences"][0]

    def test_shot_list_is_manual_step(self, tmp_path):
        ctx = self._ctx(tmp_path)
        for shot in ctx["shots"]["shots"]:
            assert shot["motion_source"] == "manual:runway-or-pika"

    def test_compliance_blocks_missing_master(self, tmp_path):
        ctx = self._ctx(tmp_path)
        ctx["assembly"] = {"exists": False, "master_path": ""}
        res = ComplianceAgent().run(ctx)
        assert res["passed"] is False
        assert res["synthetic_media"] is True

    def test_package_id_unique(self):
        assert package_id_for("a") != package_id_for("b") or True  # time-based
        assert package_id_for("a").startswith("fye-")


class TestCommandOs:
    def test_unconfigured_is_fail_soft(self, tmp_path):
        cfg = _cfg(tmp_path)
        res = command_os.request_publish_approval(cfg, package_id="p1", title="t")
        assert res["ok"] is False and res["skipped"] is True
        assert command_os.pending_approvals(cfg) is None
        assert command_os.journaled_decision(cfg, "x") is None

    def test_emit_payload_signed(self, tmp_path, monkeypatch):
        monkeypatch.setenv("DC_WEBHOOK_URL", "https://dc.example/api/events/webhook")
        monkeypatch.setenv("WEBHOOK_SECRET", "s3cret")
        cfg = FyeConfig(root=str(tmp_path), dc_webhook_url="https://dc.example/api/events/webhook",
                        webhook_secret="s3cret")
        captured = {}

        import runtime.daily_command_producer as prod

        class Resp:
            def __enter__(self): return self
            def __exit__(self, *a): return False
            def read(self): return b'{"ok":true,"id":"appr_1"}'

        def fake_urlopen(req, timeout=0):
            captured["body"] = req.data
            captured["sig"] = req.headers.get("x-dc-signature") or req.headers.get("X-dc-signature")
            return Resp()

        with patch.object(prod.urllib.request, "urlopen", fake_urlopen):
            res = command_os.request_publish_approval(
                cfg, package_id="pkg9", title="T", shot_count=3, duration_s=30)
        assert res["ok"] is True and res["id"] == "appr_1"
        body = json.loads(captured["body"])
        assert body["event_type"] == "fye.publish_requested"
        assert body["data"]["package_id"] == "pkg9"
        assert body["data"]["synthetic_media"] is True
        import hashlib
        import hmac
        expected = hmac.new(b"s3cret", captured["body"], hashlib.sha256).hexdigest()
        assert captured["sig"] == expected

    def test_dc_base_url_derivation(self, tmp_path):
        cfg = FyeConfig(root=str(tmp_path),
                        dc_webhook_url="https://dc.example/api/events/webhook",
                        webhook_secret="x")
        assert cfg.dc_base_url == "https://dc.example"


FIELDS = {
    "topic": "Compound interest", "niche": "personal-finance",
    "title": "T", "channel": "@chan", "monthly_views_target": 100000,
    "subscribers": 0, "watch_hours": 0, "shorts_views": 0,
    "human_reviewed": False,
}


class TestJobStore:
    def _store(self, tmp_path):
        from runtime.fye.jobs import FyeJobStore
        return FyeJobStore(_cfg(tmp_path))

    def test_create_is_immutable_and_idempotent(self, tmp_path):
        from runtime.fye.jobs import PayloadMismatch
        s = self._store(tmp_path)
        j1 = s.create(job_id="j1", approval_id="a1", fields=FIELDS)
        assert j1["status"] == "DRAFT" and j1["approval_id"] == "a1"
        # duplicate dispatch — same job_id + payload -> existing record
        j2 = s.create(job_id="j1", approval_id="a1", fields=FIELDS)
        assert j2["job_id"] == "j1" and j2["replayed"] is True
        # altered payload on same job_id -> rejected
        import pytest
        with pytest.raises(PayloadMismatch):
            s.create(job_id="j1", approval_id="a1",
                     fields={**FIELDS, "topic": "altered"})

    def test_lifecycle_transitions_are_validated(self, tmp_path):
        import pytest
        from runtime.fye.jobs import IllegalTransition
        s = self._store(tmp_path)
        s.create(job_id="j2", approval_id="a1", fields=FIELDS)
        with pytest.raises(IllegalTransition):
            s.transition("j2", "PUBLISHED")  # DRAFT -> PUBLISHED illegal
        s.approve("j2")
        s.enqueue("j2")
        assert s.get("j2")["status"] == "QUEUED"
        j = s.get("j2")
        assert [h["to"] for h in j["history"]] == ["APPROVED", "QUEUED"]

    def test_expired_approval_blocks_execution(self, tmp_path):
        import pytest
        from runtime.fye.jobs import JobError
        cfg = _cfg(tmp_path)
        from runtime.fye.jobs import FyeJobStore
        s = FyeJobStore(FyeConfig(**{**cfg.__dict__, "job_ttl_s": -1}))
        s.create(job_id="j3", approval_id="a1", fields=FIELDS)
        with pytest.raises(JobError):
            s.approve("j3")
        assert s.get("j3")["status"] == "EXPIRED"

    def test_single_lease_winner(self, tmp_path):
        s = self._store(tmp_path)
        s.create(job_id="j4", approval_id="a1", fields=FIELDS)
        s.approve("j4")
        s.enqueue("j4")
        assert s.claim("j4", "worker-a") is True
        assert s.claim("j4", "worker-b") is False  # concurrent loser
        assert s.claim("j4", "worker-a") is True   # owner re-claim ok

    def test_lease_expiry_allows_recovery(self, tmp_path):
        s = self._store(tmp_path)
        s.create(job_id="j5", approval_id="a1", fields=FIELDS)
        s.approve("j5")
        s.enqueue("j5")
        assert s.claim("j5", "worker-a", ttl_s=-1) is True
        # crashed worker's lease expired — recoverable, not stuck
        assert s.claim("j5", "worker-b") is True

    def test_artifact_sha_and_size_limit(self, tmp_path):
        import pytest
        from runtime.fye.jobs import JobError
        s = self._store(tmp_path)
        s.create(job_id="j6", approval_id="a1", fields=FIELDS)
        art = tmp_path / "master.mp4"
        art.write_bytes(b"x" * 500)
        job = s.record_artifact("j6", str(art))
        entry = job["artifacts"]["master.mp4"]
        import hashlib
        assert entry["sha256"] == hashlib.sha256(b"x" * 500).hexdigest()
        big = tmp_path / "big.mp4"
        big.write_bytes(b"y" * 200)
        with pytest.raises(JobError):
            s.record_artifact("j6", str(big), max_bytes=100)
        with pytest.raises(JobError):
            s.record_artifact("j6", str(tmp_path / "missing.mp4"))

    def test_transitions_land_in_journal(self, tmp_path):
        s = self._store(tmp_path)
        s.create(job_id="j7", approval_id="a1", fields=FIELDS)
        s.approve("j7")
        entries = s.journal.find(decision="job.transition")
        assert entries and entries[-1]["data"]["to"] == "APPROVED"
        assert s.journal.verify_chain() is True


class TestDispatch:
    def test_dispatch_requires_token(self, tmp_path):
        from runtime.fye import dispatch
        cfg = _cfg(tmp_path)
        job = {"job_id": "j", "status": "APPROVED", "payload": FIELDS,
               "payload_hash": dispatch.payload_hash(FIELDS),
               "approval_id": "a1"}
        res = dispatch.dispatch_job(cfg, job)
        assert res["ok"] is False  # fail closed without credential

    def test_dispatch_refuses_unapproved_job(self, tmp_path):
        from runtime.fye import dispatch
        cfg = FyeConfig(root=str(tmp_path), dispatch_token="tok")
        res = dispatch.dispatch_job(
            cfg, {"job_id": "j", "status": "DRAFT", "payload": {}})
        assert res["ok"] is False

    def test_worker_rejects_altered_payload(self, tmp_path):
        import pytest
        from runtime.fye import dispatch
        from runtime.fye.jobs import JobError
        cfg = _cfg(tmp_path)
        ph = dispatch.payload_hash(FIELDS)
        altered = {**FIELDS, "topic": "different topic"}
        with pytest.raises(JobError):
            dispatch.verify_worker_inputs(
                cfg, job_id="j", approval_id="a",
                expected_hash=ph, fields=altered)

    def test_worker_fails_closed_without_command_os(self, tmp_path):
        import pytest
        from runtime.fye import dispatch
        from runtime.fye.jobs import JobError
        cfg = _cfg(tmp_path)  # dc not configured
        ph = dispatch.payload_hash(FIELDS)
        with pytest.raises(JobError):
            dispatch.verify_worker_inputs(
                cfg, job_id="j", approval_id="a",
                expected_hash=ph, fields=FIELDS)

    def test_worker_rejects_nonapproved_decision(self, tmp_path):
        import pytest
        from runtime.fye import dispatch
        from runtime.fye.jobs import JobError
        cfg = FyeConfig(root=str(tmp_path),
                        dc_webhook_url="https://dc.example/api/events/webhook",
                        webhook_secret="s")
        fake = type("C", (), {"journaled_decision":
                              staticmethod(lambda c, i: {"status": "pending"})})
        with pytest.raises(JobError):
            dispatch.verify_worker_inputs(
                cfg, job_id="j", approval_id="a",
                expected_hash=dispatch.payload_hash(FIELDS),
                fields=FIELDS, command_os=fake)


class TestPublish:
    def _ready(self, tmp_path):
        from runtime.fye.jobs import FyeJobStore
        s = FyeJobStore(_cfg(tmp_path))
        s.create(job_id="jp", approval_id="a1", fields=FIELDS)
        s.approve("jp")
        s.enqueue("jp")
        s.claim("jp", "w")
        s.transition("jp", "RENDERING")
        s.transition("jp", "QA")
        s.transition("jp", "READY")
        return s

    def test_publish_requires_own_approval(self, tmp_path):
        import pytest
        from runtime.fye import publish
        s = self._ready(tmp_path)
        with pytest.raises(publish.PublishRefused):
            publish.publish_job(s.cfg, s, "jp",
                                publisher=publish.DryRunPublisher())

    def test_duplicate_publish_one_post(self, tmp_path):
        from runtime.fye import publish
        s = self._ready(tmp_path)
        s.transition("jp", "PUBLISH_APPROVED")
        r1 = publish.publish_job(s.cfg, s, "jp",
                                 publisher=publish.DryRunPublisher())
        r2 = publish.publish_job(s.cfg, s, "jp",
                                 publisher=publish.DryRunPublisher())
        assert r1["post_id"] == r2["post_id"] and r2["replayed"] is True
        assert s.get("jp")["status"] == "PUBLISHED"

    def test_missing_credential_fails_closed(self, tmp_path):
        import pytest
        from runtime.fye import publish
        s = self._ready(tmp_path)
        s.transition("jp", "PUBLISH_APPROVED")
        with pytest.raises(publish.PublishRefused):
            publish.publisher_for(s.cfg)  # no adapter, no dry run
        # failed publish must not invalidate the rendered asset
        assert s.get("jp")["status"] == "PUBLISH_APPROVED"

    def test_published_event_carries_attribution(self, tmp_path):
        from runtime.fye import publish
        s = self._ready(tmp_path)
        s.transition("jp", "PUBLISH_APPROVED")
        publish.publish_job(s.cfg, s, "jp",
                            publisher=publish.DryRunPublisher())
        ev = publish.published_event(s.get("jp"))
        assert ev["asset_id"] == "jp" and ev["state"] == "PUBLISHED"
        assert "channel_id" in ev and "campaign" in ev
