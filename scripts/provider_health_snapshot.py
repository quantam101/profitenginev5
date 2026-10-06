#!/usr/bin/env python3
"""Emit provider health without treating deployment health as provider health."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone

import httpx


def probe_groq() -> dict:
    key = os.getenv("GROQ_API_KEY", "").strip()
    if not key:
        return {"component": "ai_primary", "provider": "groq", "status": "not_configured"}
    try:
        response = httpx.get("https://api.groq.com/openai/v1/models", headers={"Authorization": f"Bearer {key}"}, timeout=10)
        response.raise_for_status()
        return {"component": "ai_primary", "provider": "groq", "status": "healthy", "http_status": response.status_code}
    except Exception as exc:
        return {"component": "ai_primary", "provider": "groq", "status": "unhealthy", "error": str(exc)[:240]}


def probe_gemini() -> dict:
    key = (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or "").strip()
    if not key:
        return {"component": "ai_failover", "provider": "gemini", "status": "not_configured"}
    try:
        response = httpx.get("https://generativelanguage.googleapis.com/v1beta/models", headers={"x-goog-api-key": key}, timeout=10)
        response.raise_for_status()
        return {"component": "ai_failover", "provider": "gemini", "status": "healthy", "http_status": response.status_code}
    except Exception as exc:
        return {"component": "ai_failover", "provider": "gemini", "status": "unhealthy", "error": str(exc)[:240]}


def main() -> int:
    snapshot = {
        "source": "profitenginev5",
        "environment": os.getenv("VERCEL_ENV", os.getenv("ENVIRONMENT", "production")),
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "providers": [probe_groq(), probe_gemini()],
    }
    print(json.dumps(snapshot, indent=2))
    return 0 if any(item["status"] == "healthy" for item in snapshot["providers"]) else 2


if __name__ == "__main__":
    raise SystemExit(main())
