"""make_newsletter compose/deliver contract: dataDate provenance, guard payload shape,
content fingerprint stability, and the sender refusing unapproved decisions."""

import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _load():
    sys.path.insert(0, str(ROOT / "scripts"))
    sys.path.insert(0, str(ROOT))
    spec = importlib.util.spec_from_file_location("make_newsletter", ROOT / "scripts" / "make_newsletter.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def nl(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    for key in ("OPENROUTER_API_KEY", "GROQ_API_KEY", "DEEPSEEK_API_KEY", "GEMINI_API_KEY",
                "RESEND_API_KEY", "ISSUE_DATA_DATE"):
        monkeypatch.delenv(key, raising=False)
    mod = _load()
    monkeypatch.setattr(mod, "ai_complete", lambda *a, **k: None)
    monkeypatch.setattr(mod, "verified_youtube_uploads", lambda uploads, **k: [
        u for u in uploads if u.get("status") == "success"])
    monkeypatch.setattr(mod, "_read_content_json", lambda path: (None, None))
    writes = []
    monkeypatch.setattr(mod, "_write_content_json", lambda path, payload, sha, msg: writes.append((path, payload)) or True)
    mod._test_writes = writes
    return mod


def _source_runs(*dates):
    Path("source_runs.json").write_text(json.dumps({"items": [
        {"databaseId": i, "created_at": f"{d}T12:40:00Z"} for i, d in enumerate(dates)]}))


def test_data_date_is_newest_source_run(nl):
    assert nl._data_date() is None
    _source_runs("2026-10-24", "2026-10-25")
    assert nl._data_date() == "2026-10-25"


def test_data_date_override_and_malformed(nl, monkeypatch):
    _source_runs("not-a-date")
    assert nl._data_date() is None
    monkeypatch.setenv("ISSUE_DATA_DATE", "2026-10-26")
    assert nl._data_date() == "2026-10-26"


def test_build_issue_payload_shape(nl):
    _source_runs("2026-10-26")
    Path("contracts.json").write_text(json.dumps([{"title": "Phoenix MDF cabling", "url": "https://example.gov/rfq/9", "pay": "$4,800"}]))
    Path("trending_topics.json").write_text(json.dumps([{"title": "Wi-Fi 7 upgrades", "reason": "interest"}]))
    Path("youtube_uploads.json").write_text(json.dumps([{"status": "success", "video_id": "abc", "url": "https://youtu.be/abc"}]))
    issue = nl.build_issue()
    assert issue["schema"] == nl.ISSUE_SCHEMA
    assert issue["dataDate"] == "2026-10-26"
    assert issue["opportunities"] == [{"section": "Contracts and bids", "title": "Phoenix MDF cabling", "url": "https://example.gov/rfq/9"}]
    assert [s["title"] for s in issue["signals"]] == ["1 verified public video", "Wi-Fi 7 upgrades"]
    assert issue["previous"] == {}
    assert issue["fingerprint"] in issue["html"]
    assert "Phoenix MDF cabling" in issue["html"]


def test_fingerprint_ignores_issue_date_but_tracks_content(nl, monkeypatch):
    sections = [("Contracts and bids", [{"title": "a"}])]
    f1 = nl._data_fingerprint(sections, [])
    monkeypatch.setattr(nl.time, "gmtime", lambda *a: (2030, 1, 1, 0, 0, 0, 0, 1, 0))
    assert nl._data_fingerprint(sections, []) == f1
    assert nl._data_fingerprint([("Contracts and bids", [{"title": "b"}])], []) != f1


def test_deliver_refuses_unapproved_decisions(nl):
    issue = {"schema": nl.ISSUE_SCHEMA, "dataDate": "2026-10-26", "subject": "s", "html": "<p>x</p>",
             "fingerprint": "f", "opportunities": [], "signals": []}
    for bad in ("stale", "empty", "invalid", "", "SEND"):
        with pytest.raises(SystemExit, match="refusing to deliver"):
            nl.deliver(issue, bad, page=False)
    with pytest.raises(SystemExit, match="refusing to deliver"):
        nl.deliver({**issue, "dataDate": None}, "send", page=False)
    with pytest.raises(SystemExit, match="refusing to deliver"):
        nl.deliver({**issue, "schema": "other"}, "send", page=False)
    assert nl._test_writes == []


def test_deliver_without_api_key_is_a_loud_failure_and_records_nothing(nl, capsys):
    issue = {"schema": nl.ISSUE_SCHEMA, "dataDate": "2026-10-26", "subject": "Issue", "html": "<p>x</p>",
             "fingerprint": "f", "opportunities": [{"title": "a"}], "signals": [], "featuredSlugs": ["slug-1"]}
    assert nl.deliver(issue, "send", page=False) is False
    out = capsys.readouterr().out
    assert "::error::issue was NOT emailed" in out
    assert nl._test_writes == []
    assert Path("newsletter.html").exists()


def test_deliver_records_last_issue_and_featured_on_success(nl, monkeypatch):
    monkeypatch.setattr(nl, "try_resend", lambda subject, body: True)
    issue = {"schema": nl.ISSUE_SCHEMA, "dataDate": "2026-10-26", "subject": "Issue", "html": "<p>x</p>",
             "fingerprint": "f", "opportunities": [], "signals": [{"title": "s"}], "featuredSlugs": ["slug-1"]}
    assert nl.deliver(issue, "brief", page=False) is True
    paths = dict(nl._test_writes)
    assert paths[nl.FEATURED_INDEX] == ["slug-1"]
    last = paths[nl.LAST_ISSUE_INDEX]
    assert last["fingerprint"] == "f" and last["decision"] == "brief" and last["dataDate"] == "2026-10-26"
    assert last["signals"] == 1 and last["opportunities"] == 0
