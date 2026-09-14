#!/usr/bin/env python3
"""Fail-closed verification for YouTube uploads used by newsletter publishers.

Pipeline artifacts are evidence that an upload attempt completed, not proof that
an end user can actually open the resulting video.  Newsletter code must call
``verified_youtube_uploads`` before counting, linking, or recording a video in
its permanent content ledger.

Verification deliberately uses YouTube's public oEmbed endpoint and requires a
successful response with basic video metadata.  No API key is required.  Any
network, HTTP, parsing, or validation failure is treated as *not verified* so
we never claim that inaccessible/private/deleted videos were published.
"""
from __future__ import annotations

import json
import re
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Callable, Iterable

_VIDEO_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")
_YOUTUBE_HOSTS = {"youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be", "www.youtu.be"}
_OEMBED_URL = "https://www.youtube.com/oembed"
_USER_AGENT = "already-here-newsletter/1.0"


def video_id_from_upload(upload: dict[str, Any]) -> str:
    """Return a validated canonical YouTube video id, or an empty string."""
    candidate = str(upload.get("video_id") or "").strip()
    if _VIDEO_ID_RE.fullmatch(candidate):
        return candidate

    raw_url = str(upload.get("url") or "").strip()
    if not raw_url:
        return ""
    try:
        parsed = urllib.parse.urlsplit(raw_url)
    except ValueError:
        return ""

    host = (parsed.hostname or "").lower()
    if host not in _YOUTUBE_HOSTS:
        return ""

    candidate = ""
    if host in {"youtu.be", "www.youtu.be"}:
        candidate = parsed.path.strip("/").split("/", 1)[0]
    elif parsed.path == "/watch":
        candidate = urllib.parse.parse_qs(parsed.query).get("v", [""])[0]
    else:
        parts = parsed.path.strip("/").split("/")
        if len(parts) >= 2 and parts[0] in {"shorts", "embed", "live"}:
            candidate = parts[1]

    return candidate if _VIDEO_ID_RE.fullmatch(candidate or "") else ""


def canonical_video_url(upload: dict[str, Any]) -> str:
    """Return the canonical watch URL for a valid upload artifact."""
    video_id = video_id_from_upload(upload)
    return f"https://www.youtube.com/watch?v={video_id}" if video_id else ""


def public_video_metadata(
    video_url: str,
    *,
    timeout: float = 12.0,
    opener: Callable[..., Any] = urllib.request.urlopen,
) -> dict[str, Any] | None:
    """Return oEmbed metadata only when YouTube independently confirms access."""
    if not video_url:
        return None
    endpoint = f"{_OEMBED_URL}?{urllib.parse.urlencode({'url': video_url, 'format': 'json'})}"
    request = urllib.request.Request(endpoint, headers={"User-Agent": _USER_AGENT})
    try:
        with opener(request, timeout=timeout) as response:
            status = getattr(response, "status", 200)
            if status != 200:
                return None
            payload = json.loads(response.read())
    except (
        urllib.error.HTTPError,
        urllib.error.URLError,
        TimeoutError,
        OSError,
        ValueError,
        json.JSONDecodeError,
    ):
        return None

    if not isinstance(payload, dict):
        return None
    if not str(payload.get("title") or "").strip():
        return None
    if not str(payload.get("author_name") or "").strip():
        return None
    return payload


def verified_youtube_uploads(
    uploads: Iterable[dict[str, Any]],
    *,
    timeout: float = 12.0,
    opener: Callable[..., Any] = urllib.request.urlopen,
) -> list[dict[str, Any]]:
    """Return unique, independently verified public/accessibly linked uploads.

    Only artifacts explicitly marked ``status=success`` are candidates.  A
    successful artifact that cannot be proven accessible through oEmbed is
    omitted.  Returned records always contain canonical ``video_id`` and
    ``url`` fields.
    """
    verified: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    for raw in uploads:
        if not isinstance(raw, dict) or raw.get("status") != "success":
            continue
        video_id = video_id_from_upload(raw)
        if not video_id or video_id in seen_ids:
            continue
        canonical_url = f"https://www.youtube.com/watch?v={video_id}"
        metadata = public_video_metadata(
            canonical_url, timeout=timeout, opener=opener
        )
        if metadata is None:
            continue

        item = dict(raw)
        item["video_id"] = video_id
        item["url"] = canonical_url
        item["verified_public"] = True
        item["verified_title"] = str(metadata.get("title") or "").strip()
        verified.append(item)
        seen_ids.add(video_id)

    return verified
