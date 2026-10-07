"""Fail-closed persistence + real readiness probing tests."""
import importlib.util
import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_cycles_fail_closed_when_redis_unconfigured(tmp_path, monkeypatch, capsys):
    monkeypatch.delenv("UPSTASH_REDIS_REST_URL", raising=False)
    monkeypatch.delenv("UPSTASH_REDIS_REST_TOKEN", raising=False)
    log = tmp_path / "cycles.jsonl"
    log.write_text(json.dumps({"status": "ok"}) + "\n")
    monkeypatch.setenv("GMAOS_CYCLE_LOG", str(log))
    m = _load("push_cycles", REPO / "scripts/push_cycles_to_redis.py")
    assert m.main() == 2  # records exist but can't persist → nonzero


def test_cycles_empty_log_ok_without_redis(tmp_path, monkeypatch):
    monkeypatch.delenv("UPSTASH_REDIS_REST_URL", raising=False)
    monkeypatch.delenv("UPSTASH_REDIS_REST_TOKEN", raising=False)
    log = tmp_path / "cycles.jsonl"
    log.write_text("")
    monkeypatch.setenv("GMAOS_CYCLE_LOG", str(log))
    m = _load("push_cycles", REPO / "scripts/push_cycles_to_redis.py")
    assert m.main() in (0, 2)  # no records to lose; unconfigured flags 2


def test_readiness_marks_missing_as_waiting(monkeypatch):
    m = _load("preflight", REPO / "scripts/distribution_preflight.py")
    for env in ("DEVTO_API_KEY",):
        monkeypatch.delenv(env, raising=False)
    row = m.status(m.CHANNELS[1], probe=False)  # devto
    assert row["state"] == "WAITING FOR AUTH"
    assert "DEVTO_API_KEY" in row["missing"]


def test_readiness_failed_when_probe_rejects(monkeypatch):
    m = _load("preflight", REPO / "scripts/distribution_preflight.py")
    monkeypatch.setenv("DEVTO_API_KEY", "x" * 20)
    monkeypatch.setitem(m.PROBES, "devto", lambda: (False, "HTTP 401"))
    row = m.status(m.CHANNELS[1], probe=True)
    assert row["state"] == "FAILED"
    assert "401" in row["detail"]


def test_utm_tags_traffic_links_only():
    m = _load("pub", REPO / "scripts/publish_article.py")
    url = m._utm("https://www.alreadyherellc.com/content/x/", "threads")
    assert "utm_source=threads" in url and "utm_campaign=alreadyhere-content" in url
    assert m._utm("", "threads") == ""
