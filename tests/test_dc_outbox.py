"""DC producer failover: failed events spool to an outbox, later emits replay it."""

import json
import urllib.error

import pytest

import runtime.daily_command_producer as dc


@pytest.fixture
def configured(tmp_path, monkeypatch):
    monkeypatch.setenv("DC_WEBHOOK_URL", "https://dc.example.com/webhook")
    monkeypatch.setenv("WEBHOOK_SECRET", "test-secret")
    monkeypatch.setenv("DC_OUTBOX_PATH", str(tmp_path / "outbox.jsonl"))
    return tmp_path / "outbox.jsonl"


def _fail(monkeypatch, exc):
    def bad(req, timeout=0):
        raise exc

    monkeypatch.setattr(dc, "urlopen_with_retries", lambda req, **kw: bad(req))


def _ok(monkeypatch):
    delivered = []

    class _Resp:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def read(self):
            return b'{"ok": true}'

    def good(req, **kw):
        delivered.append(json.loads(req.data))
        return _Resp()

    monkeypatch.setattr(dc, "urlopen_with_retries", good)
    return delivered


def test_unconfigured_is_noop(monkeypatch):
    monkeypatch.delenv("DC_WEBHOOK_URL", raising=False)
    monkeypatch.delenv("WEBHOOK_SECRET", raising=False)
    out = dc.emit("x.y", {})
    assert out == {"ok": False, "skipped": True, "reason": "DC not configured"}


def test_transient_failure_spools(configured, monkeypatch):
    _fail(monkeypatch, urllib.error.URLError("conn refused"))
    out = dc.emit_opportunity(company="Acme", external_id="opp-1")
    assert out["ok"] is False and out["spooled"] is True

    records = [json.loads(l) for l in configured.read_text().splitlines()]
    assert len(records) == 1
    assert records[0]["event_type"] == "revenue_opportunity.detected"
    assert records[0]["idempotency_key"] == "opp-1"


def test_permanent_failure_not_spooled(configured, monkeypatch):
    _fail(
        monkeypatch,
        urllib.error.HTTPError("u", 422, "bad", hdrs=None, fp=None),
    )
    out = dc.emit("x.y", {})
    assert out["ok"] is False and out["spooled"] is False
    assert not configured.exists()


def test_next_emit_replays_outbox(configured, monkeypatch):
    _fail(monkeypatch, urllib.error.URLError("down"))
    dc.emit_opportunity(company="Acme", external_id="opp-1")
    assert configured.exists()

    delivered = _ok(monkeypatch)
    out = dc.emit_system_failed(service="test", error="x")
    assert out.get("ok") is True
    # new emit proves connectivity first, then the queued event is replayed
    assert delivered[0]["event_type"] == "revenue_system.failed"
    assert delivered[1]["event_type"] == "revenue_opportunity.detected"
    assert delivered[1]["idempotency_key"] == "opp-1"
    # fully drained outbox is removed
    assert not configured.exists()


def test_failed_replay_keeps_queue(configured, monkeypatch):
    _fail(monkeypatch, urllib.error.URLError("down"))
    dc.emit_opportunity(company="A", external_id="e1")
    dc.emit_opportunity(company="B", external_id="e2")
    assert len(configured.read_text().splitlines()) == 2


def test_spool_disabled_by_empty_path(configured, monkeypatch):
    monkeypatch.setenv("DC_OUTBOX_PATH", "")
    _fail(monkeypatch, urllib.error.URLError("down"))
    out = dc.emit("x.y", {})
    assert out["ok"] is False
    assert not configured.exists()
