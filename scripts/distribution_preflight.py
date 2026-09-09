#!/usr/bin/env python3
"""Credential-safe distribution readiness report.

This script checks only whether the environment variables required by each
publisher are present. It never prints secret values and it does not call any
external platform. Missing optional channels are warnings, not publication
failures: the canonical article must continue publishing even while an account
is waiting for OAuth/credential authorization.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


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


def status(channel: Channel) -> dict[str, object]:
    missing = [name for name in channel.required if not present(name)]
    return {
        "name": channel.name,
        "tier": channel.tier,
        "configured": not missing,
        "missing": missing,
        "note": channel.note,
    }


def markdown_table(rows: Iterable[dict[str, object]]) -> str:
    lines = [
        "### Distribution readiness",
        "",
        "| Channel | Tier | State | Missing configuration |",
        "|---|---|---|---|",
    ]
    for row in rows:
        state = "READY" if row["configured"] else "WAITING FOR AUTH"
        missing = ", ".join(row["missing"]) if row["missing"] else "—"
        lines.append(f"| {row['name']} | {row['tier']} | {state} | {missing} |")
    return "\n".join(lines) + "\n"


def main() -> int:
    rows = [status(channel) for channel in CHANNELS]
    ready = [row for row in rows if row["configured"]]
    waiting = [row for row in rows if not row["configured"]]

    # Human-readable console output; variable NAMES are safe, values are never printed.
    print(f"[distribution] {len(ready)}/{len(rows)} channels configured")
    for row in rows:
        if row["configured"]:
            print(f"[READY] {row['name']}")
        else:
            print(f"[WAITING] {row['name']}: {', '.join(row['missing'])}")

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
            json.dumps({"configured": len(ready), "total": len(rows), "channels": rows}, indent=2) + "\n",
            encoding="utf-8",
        )

    # Canonical publication is the one hard requirement.
    canonical = next(row for row in rows if row["name"] == "canonical-content")
    if not canonical["configured"]:
        print("::error::canonical-content credentials are missing; publication cannot be certified")
        return 1

    if waiting:
        print(f"::warning::{len(waiting)} optional distribution channel(s) are waiting for account authorization")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
