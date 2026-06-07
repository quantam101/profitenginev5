from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

GRAPH_API = "https://graph.facebook.com/v21.0"


def _get_json(path: str, token: str) -> dict[str, Any]:
    separator = "&" if "?" in path else "?"
    url = f"{GRAPH_API}{path}{separator}access_token={token}"
    req = urllib.request.Request(url)  # noqa: S310 - fixed Meta Graph HTTPS API endpoint
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:  # noqa: S310
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Meta Graph API HTTP {exc.code}: {detail[:500]}") from exc


def status() -> dict[str, Any]:
    page_id = os.getenv("FB_PAGE_ID", "").strip()
    page_token = os.getenv("FB_PAGE_ACCESS_TOKEN", "").strip()
    ig_user_id = os.getenv("IG_USER_ID", "").strip()
    missing = [
        name for name, value in {
            "FB_PAGE_ID": page_id,
            "FB_PAGE_ACCESS_TOKEN": page_token,
            "IG_USER_ID": ig_user_id,
        }.items()
        if not value
    ]
    payload: dict[str, Any] = {
        "ok": not missing,
        "missing": missing,
        "facebook_page_ready": False,
        "instagram_ready": False,
    }
    if missing:
        return payload

    page = _get_json(f"/{page_id}?fields=id,name,link,connected_instagram_account", page_token)
    instagram = _get_json(f"/{ig_user_id}?fields=id,username,name", page_token)
    payload.update({
        "ok": True,
        "facebook_page_ready": bool(page.get("id")),
        "instagram_ready": bool(instagram.get("id")),
        "page": page,
        "instagram": instagram,
    })
    return payload


def main() -> int:
    try:
        result = status()
        print(json.dumps(result, indent=2))
        return 0 if result.get("ok") else 1
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
