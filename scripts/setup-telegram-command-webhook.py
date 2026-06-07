from __future__ import annotations

import json
import os
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        sys.exit(f"Missing required env var: {name}")
    return value


def main() -> None:
    token = require_env("TELEGRAM_BOT_TOKEN")
    webhook_url = require_env("TELEGRAM_WEBHOOK_URL")
    secret = require_env("TELEGRAM_WEBHOOK_SECRET")

    payload = json.dumps({
        "url": webhook_url,
        "secret_token": secret,
        "allowed_updates": ["message", "edited_message"],
        "drop_pending_updates": False,
    }).encode("utf-8")
    request = Request(
        f"https://api.telegram.org/bot{token}/setWebhook",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=20) as response:  # noqa: S310
            body = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        sys.exit(f"Telegram setWebhook failed: HTTP {exc.code} {exc.read().decode('utf-8', errors='replace')[:300]}")
    except (OSError, URLError) as exc:
        sys.exit(f"Telegram setWebhook failed: {exc}")

    if not body.get("ok"):
        sys.exit(f"Telegram setWebhook failed: {body}")

    print("Telegram command webhook configured")
    print(f"Webhook URL: {webhook_url}")


if __name__ == "__main__":
    main()
