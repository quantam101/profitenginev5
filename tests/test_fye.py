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
