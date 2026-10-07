#!/usr/bin/env python3
"""Distribution readiness report that tests *publishability*, not presence.

Every configured channel gets a real authenticated probe against the
platform API (a read-only call that exercises the same credentials the
publisher uses). States:

  READY            creds present AND probe succeeded
  FAILED           creds present but probe returned an error — the channel
                   cannot actually publish; emits ::error annotations
  WAITING FOR AUTH creds missing

Secret values are never printed; probe errors are truncated.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Optional


@dataclass(frozen=True)
class Channel:
    name: str
    required: tuple[str, ...]
    tier: str
    note: str = ""


CHANNELS: tuple[Channel, ...] = (
    Channel("canonical-content", ("GITHUB_CONTENT_TOKEN",), "required", "Already Here canonical article repository"),
    Channel("devto", ("DEVTO_API_KEY",), "syndication"),
    Channel("hashnode", ("HASHNODE_API_KEY", "HASHNODE_PUBLICATION_ID"), "syndication"),
    Channel("medium", ("MEDIUM_API_KEY", "MEDIUM_AUTHOR_ID"), "syndication"),
    Channel("x-twitter", ("TWITTER_API_KEY", "TWITTER_API_SECRET", "TWITTER_ACCESS_TOKEN", "TWITTER_ACCESS_SECRET"), "social"),
    Channel("linkedin", ("LINKEDIN_ACCESS_TOKEN", "LINKEDIN_PERSON_URN"), "social"),
    Channel("reddit", ("REDDIT_CLIENT_ID", "REDDIT_CLIENT_SECRET", "REDDIT_USERNAME", "REDDIT_PASSWORD"), "social"),
    Channel("tiktok", ("TIKTOK_ACCESS_TOKEN",), "social"),
    Channel("telegram", ("TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"), "social"),
    Channel("facebook", ("FB_PAGE_ID", "FB_PAGE_ACCESS_TOKEN"), "social"),
    Channel("instagram", ("IG_USER_ID", "FB_PAGE_ACCESS_TOKEN"), "social"),
    Channel("youtube", ("YOUTUBE_CLIENT_ID", "YOUTUBE_CLIENT_SECRET", "YOUTUBE_REFRESH_TOKEN"), "video-social"),
    Channel("growth-command-os", ("CMDOS_BASE_URL",), "owned"),
)


def present(name: str) -> bool:
    return bool(os.getenv(name, "").strip())


def _getenv(name: str) -> str:
    return os.getenv(name, "").strip()


# ── Live probes ───────────────────────────────────────────────────────────

_TIMEOUT = 10


def _redact(text: str) -> str:
    """Strip anything that could carry a credential from an error string:
    long token-like words and URL query strings (FB/IG/Telegram put tokens
    in request URLs, and urllib error messages echo them back)."""
    import re
    text = re.sub(r"[?&][^\s]*", "", text)
    return " ".join(w if len(w) < 40 else "<redacted>" for w in text.split())


def _http(req: urllib.request.Request) -> tuple[bool, str]:
    """Return (ok, detail). Never includes secret values in detail."""
    req.add_header("User-Agent", "already-here-readiness/2.0")
    try:
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as r:
            r.read()
            return True, "ok"
    except urllib.error.HTTPError as e:
        try:
            body = e.read()[:160].decode("utf-8", "replace")
        except Exception:
            body = ""
        # API error bodies sometimes embed tokens in echo'd request fields —
        # strip anything that looks like a long token before logging.
        return False, f"HTTP {e.code}: {_redact(body)}"
    except Exception as e:
        # URLError messages echo the request URL — never log it.
        return False, f"{type(e).__name__}: {_redact(str(e))[:120]}"


def _get(url: str, headers: Optional[dict] = None) -> tuple[bool, str]:
    return _http(urllib.request.Request(url, headers=headers or {}))


def _post(url: str, data: dict, headers: Optional[dict] = None) -> tuple[bool, str]:
    return _http(urllib.request.Request(
        url, data=json.dumps(data).encode(), method="POST",
        headers={"Content-Type": "application/json", **(headers or {})}))


def _oauth1_header(method: str, url: str) -> str:
    ck, cs, at, ats = (_getenv("TWITTER_API_KEY"), _getenv("TWITTER_API_SECRET"),
                       _getenv("TWITTER_ACCESS_TOKEN"), _getenv("TWITTER_ACCESS_SECRET"))
    params = {
        "oauth_consumer_key": ck, "oauth_nonce": uuid.uuid4().hex,
        "oauth_signature_method": "HMAC-SHA1", "oauth_timestamp": str(int(time.time())),
        "oauth_token": at, "oauth_version": "1.0",
    }
    enc = lambda s: urllib.parse.quote(s, safe="")
    base = f"{method}&{enc(url)}&{enc('&'.join(f'{enc(k)}={enc(v)}' for k, v in sorted(params.items())))}"
    sig = base64.b64encode(hmac.new(
        f"{enc(cs)}&{enc(ats)}".encode(), base.encode(), hashlib.sha1).digest()).decode()
    params["oauth_signature"] = sig
    return "OAuth " + ", ".join(f'{enc(k)}="{enc(v)}"' for k, v in sorted(params.items()))


def _p_canonical() -> tuple[bool, str]:
    owner = _getenv("GITHUB_CONTENT_OWNER") or "quantam101"
    repo = _getenv("GITHUB_CONTENT_REPO") or "content"
    ok, d = _get(f"https://api.github.com/repos/{owner}/{repo}",
                 {"Authorization": f"Bearer {_getenv('GITHUB_CONTENT_TOKEN')}"})
    return ok, d


def _p_devto() -> tuple[bool, str]:
    return _get("https://dev.to/api/users/me", {"api-key": _getenv("DEVTO_API_KEY")})


def _p_hashnode() -> tuple[bool, str]:
    ok, d = _post("https://gql.hashnode.com", {"query": "{ me { id username } }"},
                  {"Authorization": f"Bearer {_getenv('HASHNODE_API_KEY')}"})
    return ok, d


def _p_medium() -> tuple[bool, str]:
    return _get("https://api.medium.com/v1/me",
                {"Authorization": f"Bearer {_getenv('MEDIUM_API_KEY')}"})


def _p_twitter() -> tuple[bool, str]:
    url = "https://api.twitter.com/2/users/me"
    return _get(url, {"Authorization": _oauth1_header("GET", url)})


def _p_linkedin() -> tuple[bool, str]:
    return _get("https://api.linkedin.com/v2/userinfo",
                {"Authorization": f"Bearer {_getenv('LINKEDIN_ACCESS_TOKEN')}"})


def _p_reddit() -> tuple[bool, str]:
    creds = base64.b64encode(
        f"{_getenv('REDDIT_CLIENT_ID')}:{_getenv('REDDIT_CLIENT_SECRET')}".encode()).decode()
    body = urllib.parse.urlencode({
        "grant_type": "password", "username": _getenv("REDDIT_USERNAME"),
        "password": _getenv("REDDIT_PASSWORD")}).encode()
    return _http(urllib.request.Request(
        "https://www.reddit.com/api/v1/access_token", data=body, method="POST",
        headers={"Authorization": f"Basic {creds}"}))


def _p_tiktok() -> tuple[bool, str]:
    return _get("https://open.tiktokapis.com/v2/user/info/?fields=open_id",
                {"Authorization": f"Bearer {_getenv('TIKTOK_ACCESS_TOKEN')}"})


def _p_telegram() -> tuple[bool, str]:
    return _get(f"https://api.telegram.org/bot{_getenv('TELEGRAM_BOT_TOKEN')}/getMe")


def _p_facebook() -> tuple[bool, str]:
    return _get(f"https://graph.facebook.com/v21.0/{_getenv('FB_PAGE_ID')}"
                f"?fields=name&access_token={_getenv('FB_PAGE_ACCESS_TOKEN')}")


def _p_instagram() -> tuple[bool, str]:
    tok = _getenv("FB_PAGE_ACCESS_TOKEN")
    return _get(f"https://graph.facebook.com/v21.0/{_getenv('IG_USER_ID')}"
                f"?fields=id,username,account_type&access_token={tok}")


def _p_youtube() -> tuple[bool, str]:
    body = urllib.parse.urlencode({
        "client_id": _getenv("YOUTUBE_CLIENT_ID"),
        "client_secret": _getenv("YOUTUBE_CLIENT_SECRET"),
        "refresh_token": _getenv("YOUTUBE_REFRESH_TOKEN"),
        "grant_type": "refresh_token"}).encode()
    return _http(urllib.request.Request("https://oauth2.googleapis.com/token",
                                        data=body, method="POST",
                                        headers={"Content-Type": "application/x-www-form-urlencoded"}))


def _p_cmdos() -> tuple[bool, str]:
    return _get(f"{_getenv('CMDOS_BASE_URL').rstrip('/')}/api/content-sync/topics?limit=1")


PROBES: dict[str, Callable[[], tuple[bool, str]]] = {
    "canonical-content": _p_canonical,
    "devto": _p_devto,
    "hashnode": _p_hashnode,
    "medium": _p_medium,
    "x-twitter": _p_twitter,
    "linkedin": _p_linkedin,
    "reddit": _p_reddit,
    "tiktok": _p_tiktok,
    "telegram": _p_telegram,
    "facebook": _p_facebook,
    "instagram": _p_instagram,
    "youtube": _p_youtube,
    "growth-command-os": _p_cmdos,
}


# ── Status evaluation ─────────────────────────────────────────────────────

def status(channel: Channel, probe: bool = True) -> dict[str, object]:
    missing = [name for name in channel.required if not present(name)]
    state = "WAITING FOR AUTH" if missing else "READY"
    detail = ""
    if not missing and probe and channel.name in PROBES:
        ok, detail = PROBES[channel.name]()
        state = "READY" if ok else "FAILED"
    return {
        "name": channel.name,
        "tier": channel.tier,
        "configured": not missing,
        "state": state,
        "missing": missing,
        "detail": detail,
        "note": channel.note,
    }


def markdown_table(rows: Iterable[dict[str, object]]) -> str:
    lines = [
        "### Distribution readiness",
        "",
        "| Channel | Tier | State | Detail | Missing configuration |",
        "|---|---|---|---|---|",
    ]
    for row in rows:
        missing = ", ".join(row["missing"]) if row["missing"] else "—"
        detail = (row.get("detail") or "").replace("|", "\\|")[:120] or "—"
        lines.append(f"| {row['name']} | {row['tier']} | {row['state']} | {detail} | {missing} |")
    return "\n".join(lines) + "\n"


def main() -> int:
    probe = os.getenv("READINESS_LIVE_PROBES", "1") != "0"
    rows = [status(channel, probe=probe) for channel in CHANNELS]
    ready = [row for row in rows if row["state"] == "READY"]
    failed = [row for row in rows if row["state"] == "FAILED"]
    waiting = [row for row in rows if row["state"] == "WAITING FOR AUTH"]

    print(f"[distribution] {len(ready)} READY / {len(failed)} FAILED / "
          f"{len(waiting)} WAITING of {len(rows)} channels")
    for row in rows:
        tag = {"READY": "READY", "FAILED": "FAILED", "WAITING FOR AUTH": "WAITING"}[row["state"]]
        extra = row["detail"] or ", ".join(row["missing"])
        print(f"[{tag}] {row['name']}: {extra}")
        if row["state"] == "FAILED":
            print(f"::error::{row['name']} is configured but cannot publish: {row['detail']}")

    summary_path = os.getenv("GITHUB_STEP_SUMMARY", "").strip()
    if summary_path:
        Path(summary_path).write_text(
            Path(summary_path).read_text(encoding="utf-8") + markdown_table(rows)
            if Path(summary_path).exists()
            else markdown_table(rows),
            encoding="utf-8",
        )

    output_path = os.getenv("DISTRIBUTION_STATUS_FILE", "").strip()
    if output_path:
        Path(output_path).write_text(
            json.dumps({"ready": len(ready), "failed": len(failed),
                        "waiting": len(waiting), "total": len(rows),
                        "channels": rows}, indent=2) + "\n",
            encoding="utf-8",
        )

    # Canonical publication is the one hard requirement.
    canonical = next(row for row in rows if row["name"] == "canonical-content")
    if canonical["state"] != "READY":
        print(f"::error::canonical-content is {canonical['state']} ({canonical['detail']})"
              " — publication cannot be certified")
        return 1

    if waiting:
        print(f"::warning::{len(waiting)} optional distribution channel(s) are waiting for account authorization")

    # A configured-but-failing channel is a broken revenue path, not a
    # green check. Any FAILED channel makes the run DEGRADED (nonzero) —
    # "success" must mean every channel that is configured can publish.
    if failed:
        names = ", ".join(row["name"] for row in failed)
        print(f"::error::DEGRADED — {len(failed)} configured channel(s) cannot "
              f"publish: {names}")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
