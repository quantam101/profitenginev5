from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen


COMMAND_AGENT_MAP = {
    "content": "content-pipeline",
    "traffic": "traffic-agent",
    "proof": "proof-ledger",
    "offers": "offer-scout",
    "margin": "margin-guard",
    "motivate": "motivation-engine",
    "research": "local-research",
    "correct": "lifelong-catch-correct",
}


HELP_TEXT = "\n".join(
    [
        "ProfitEngine command gateway is online.",
        "",
        "Commands:",
        "/status",
        "/content <topic or objective>",
        "/traffic <offer or listing>",
        "/proof",
        "/offers",
        "/margin",
        "/motivate",
        "/research <question>",
        "/correct <issue to review>",
        "/agent <agent_id> <objective>",
    ]
)


@dataclass(frozen=True)
class TelegramCommand:
    chat_id: str
    text: str
    agent_id: str
    objective: str
    actor: str
    should_execute: bool = True


def verify_secret(header_value: str | None) -> bool:
    expected = os.getenv("TELEGRAM_WEBHOOK_SECRET", "").strip()
    if not expected:
        return True
    return bool(header_value and header_value == expected)


def stable_embedding(text: str, dimensions: int = 384) -> list[float]:
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    values: list[float] = []
    for index in range(dimensions):
        byte = digest[index % len(digest)]
        values.append((byte + 1) / 256_000)
    return values


def parse_update(update: dict[str, Any]) -> TelegramCommand | None:
    message = update.get("message") or update.get("edited_message") or {}
    chat = message.get("chat") or {}
    chat_id = str(chat.get("id") or "").strip()
    text = str(message.get("text") or "").strip()
    user = message.get("from") or {}
    username = str(user.get("username") or user.get("id") or "telegram-user")
    if not chat_id or not text:
        return None

    command_token, _, remainder = text.partition(" ")
    command = command_token.split("@", 1)[0].lstrip("/").lower()
    remainder = remainder.strip()

    if command in ("start", "help"):
        return TelegramCommand(chat_id, text, "sovereign-orchestrator", HELP_TEXT, f"telegram:{username}", should_execute=False)
    if command == "status":
        return TelegramCommand(chat_id, text, "proof-ledger", "Report ProfitEngine proof, allowed offers, and locked paid offers.", f"telegram:{username}")
    if command == "agent":
        agent_id, _, objective = remainder.partition(" ")
        if not agent_id or not objective.strip():
            return TelegramCommand(chat_id, text, "sovereign-orchestrator", "Usage: /agent <agent_id> <objective>", f"telegram:{username}", should_execute=False)
        return TelegramCommand(chat_id, text, agent_id, objective.strip(), f"telegram:{username}")

    agent_id = COMMAND_AGENT_MAP.get(command)
    if agent_id:
        objective = remainder or command
        return TelegramCommand(chat_id, text, agent_id, objective, f"telegram:{username}")

    return TelegramCommand(
        chat_id=chat_id,
        text=text,
        agent_id="sovereign-orchestrator",
        objective=text,
        actor=f"telegram:{username}",
    )


def format_runtime_reply(result: dict[str, Any]) -> str:
    status = str(result.get("status", "unknown"))
    route = str(result.get("route_tier", "unknown"))
    output = str(result.get("output", "")).strip()
    if len(output) > 3200:
        output = output[:3190].rstrip() + "\n[truncated]"
    return f"Status: {status}\nRoute: {route}\n\n{output or 'No output returned.'}"


def send_telegram_message(chat_id: str, text: str) -> bool:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        return False
    payload = json.dumps({
        "chat_id": chat_id,
        "text": text[:3900],
        "disable_web_page_preview": True,
    }).encode("utf-8")
    request = Request(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=10) as response:  # noqa: S310
            return 200 <= response.status < 300
    except (OSError, URLError):
        return False
