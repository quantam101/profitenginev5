"""
ProfitEngine v5 — Daily Audit-Log Digest
=========================================
Runs every morning at 07:00 UTC via the GitHub Actions 'digest.yml' workflow.
Sends a Telegram message (and optional Gmail fallback) summarising:
  • Yesterday's net revenue  (real Stripe figures when STRIPE_API_KEY is set)
  • Pending HITL approvals that need action
  • Catch-and-Correct findings from the last 24 h
  • Agent-run health snapshot

Usage
-----
  # From the server (normal cron path):
  docker compose exec -T runtime python -m runtime.agent_impls.daily_digest

  # One-shot local test:
  TELEGRAM_BOT_TOKEN=xxx TELEGRAM_CHAT_ID=yyy python -m runtime.agent_impls.daily_digest

  # Find your Telegram chat-ID (send the bot any message first, then run):
  TELEGRAM_BOT_TOKEN=xxx python -m runtime.agent_impls.daily_digest --get-chat-id

Required env vars
-----------------
  TELEGRAM_BOT_TOKEN   — from @BotFather (never commit the real value)
  TELEGRAM_CHAT_ID     — numeric ID of the chat/group to post in

Optional env vars
-----------------
  STRIPE_API_KEY            — enables real Stripe revenue figures
  BACKEND_URL               — internal backend base URL (default http://backend:8001)
  GMAOS_CORRECTIONS_PATH    — corrections log (default /data/corrections.jsonl)
  GMAIL_USER                — Gmail fallback sender  (e.g. alreadyherellc@gmail.com)
  GMAIL_APP_PASSWORD        — Gmail App Password for SMTP
  ALERT_EMAIL               — Gmail fallback recipient
  APP_PUBLIC_URL            — dashboard URL in the digest footer
"""
from __future__ import annotations

import base64
import json
import os
import smtplib
import sys
import urllib.request
import urllib.parse
from datetime import datetime, timedelta, timezone
from email.mime.text import MIMEText
from pathlib import Path


# ── Configuration ─────────────────────────────────────────────────────────────
TELEGRAM_TOKEN   = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
STRIPE_KEY       = os.getenv("STRIPE_API_KEY", "")
BACKEND_URL      = os.getenv("BACKEND_URL", "http://backend:8001").rstrip("/")
CORRECTIONS_PATH = os.getenv("GMAOS_CORRECTIONS_PATH", "/data/corrections.jsonl")
GMAIL_USER       = os.getenv("GMAIL_USER", "")
GMAIL_PASSWORD   = os.getenv("GMAIL_APP_PASSWORD", "")
ALERT_EMAIL      = os.getenv("ALERT_EMAIL", "")
DASHBOARD_URL    = os.getenv("APP_PUBLIC_URL", "https://profitengine.alreadyherellc.com")

TELEGRAM_API = "https://api.telegram.org"
STRIPE_API   = "https://api.stripe.com/v1"


# ── HTTP helpers (stdlib only — zero extra deps) ───────────────────────────────

def _get_json(url: str, timeout: int = 8) -> dict | list:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return json.loads(r.read())
    except Exception:
        return {}


def _post_json(url: str, payload: dict, headers: dict | None = None,
               timeout: int = 10) -> dict:
    data = json.dumps(payload).encode()
    h = {"Content-Type": "application/json", **(headers or {})}
    req = urllib.request.Request(url, data=data, headers=h, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def _stripe_get(path: str, params: dict | None = None) -> dict | list:
    """Authenticated GET against the Stripe REST API."""
    if not STRIPE_KEY:
        return {}
    qs = f"?{urllib.parse.urlencode(params)}" if params else ""
    url = f"{STRIPE_API}{path}{qs}"
    creds = base64.b64encode(f"{STRIPE_KEY}:".encode()).decode()
    req = urllib.request.Request(url, headers={"Authorization": f"Basic {creds}"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read())
    except Exception:
        return {}


# ── Data collectors ────────────────────────────────────────────────────────────

def _utc_day_range() -> tuple[datetime, datetime]:
    """Returns (yesterday_start, today_start) in UTC."""
    now   = datetime.now(timezone.utc)
    today = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
    return today - timedelta(days=1), today


def collect_revenue(yesterday: datetime, today: datetime) -> dict:
    """
    Real Stripe figures when STRIPE_API_KEY is present; falls back to the
    backend /api/revenue/stats fixture.
    """
    if STRIPE_KEY:
        params = {
            "created[gte]": int(yesterday.timestamp()),
            "created[lt]":  int(today.timestamp()),
            "limit": 100,
        }
        charges = _stripe_get("/charges", params)
        succeeded = [
            c for c in charges.get("data", [])
            if c.get("status") == "succeeded"
        ]
        net = round(sum(c.get("amount", 0) for c in succeeded) / 100, 2)
        return {
            "source":      "stripe",
            "yesterday_usd": net,
            "txn_count":   len(succeeded),
        }
    # Backend fixture fallback
    stats = _get_json(f"{BACKEND_URL}/api/revenue/stats")
    if isinstance(stats, dict) and "total_30d" in stats:
        return {
            "source":        "fixture",
            "yesterday_usd": round(stats["total_30d"] / 30, 2),
            "best_stream":   stats.get("best_stream", "—"),
            "active_streams": stats.get("active_streams", 0),
        }
    return {"source": "unavailable", "yesterday_usd": 0.0}


def collect_approvals() -> dict:
    """Count open (pending) HITL approvals from the backend."""
    approvals = _get_json(f"{BACKEND_URL}/api/approvals")
    if not isinstance(approvals, list):
        return {"total": 0, "pending": 0, "high_risk": 0}
    pending   = [a for a in approvals if a.get("state", "open") == "open"]
    high_risk = [a for a in pending   if a.get("risk") in ("high", "critical")]
    return {
        "total":     len(approvals),
        "pending":   len(pending),
        "high_risk": len(high_risk),
    }


def collect_agent_runs(yesterday: datetime) -> dict:
    """Count yesterday's agent runs from the backend API."""
    runs = _get_json(f"{BACKEND_URL}/api/agent-runs?limit=200")
    if not isinstance(runs, list):
        return {"completed": 0, "errored": 0, "total_cost_usd": 0.0, "total_saved_usd": 0.0}

    yesterday_iso = yesterday.isoformat()
    today_iso     = (yesterday + timedelta(days=1)).isoformat()
    recent = [
        r for r in runs
        if yesterday_iso <= (r.get("queued_at") or "") < today_iso
    ]
    completed  = sum(1 for r in recent if r.get("status") == "completed")
    errored    = sum(1 for r in recent if r.get("status") == "errored")
    cost       = round(sum(r.get("cost_usd", 0.0) for r in recent), 4)
    saved      = round(sum(r.get("saved_usd", 0.0) for r in recent), 4)
    return {
        "completed":       completed,
        "errored":         errored,
        "total_cost_usd":  cost,
        "total_saved_usd": saved,
    }


def collect_catch_correct(yesterday: datetime) -> dict:
    """Parse corrections.jsonl, return entries from the last 24 h."""
    path = Path(CORRECTIONS_PATH)
    if not path.exists():
        return {"count": 0, "samples": []}

    yesterday_iso = yesterday.isoformat()
    today_iso     = (yesterday + timedelta(days=1)).isoformat()
    findings: list[dict] = []

    try:
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            ts = rec.get("timestamp") or rec.get("at") or ""
            if yesterday_iso <= ts < today_iso:
                findings.append(rec)
    except OSError:
        pass

    samples = [
        f"[{r.get('category', '?')}] {r.get('issue', '')[:80]}"
        for r in findings[:3]
    ]
    return {"count": len(findings), "samples": samples}


def collect_proof_of_work() -> dict:
    """System health snapshot from the backend."""
    data = _get_json(f"{BACKEND_URL}/api/proof-of-work")
    if not isinstance(data, dict):
        return {}
    return {
        "score":            data.get("score", 0.0),
        "uptime_pct":       data.get("uptime_pct", 0.0),
        "passed_cycles":    data.get("passed_cycles_24h", 0),
        "failed_cycles":    data.get("failed_cycles_24h", 0),
        "guard_blocks":     data.get("guard_blocks_24h", 0),
    }


# ── Message formatter ──────────────────────────────────────────────────────────

def build_message(
    date_label: str,
    revenue:    dict,
    approvals:  dict,
    runs:       dict,
    cnc:        dict,
    pow_:       dict,
) -> str:
    lines: list[str] = []

    # Header
    lines += [
        f"📊 *ProfitEngine Daily Digest*",
        f"_{date_label} · 07:00 UTC_",
        "",
    ]

    # Revenue
    rev = revenue.get("yesterday_usd", 0.0)
    src = "Stripe" if revenue.get("source") == "stripe" else "estimate"
    txn = revenue.get("txn_count")
    rev_line = f"  {src}: *${rev:,.2f}*"
    if txn is not None:
        rev_line += f"  ({txn} txn{'s' if txn != 1 else ''})"
    if "best_stream" in revenue:
        rev_line += f"\n  Best stream: {revenue['best_stream']}"
    lines += ["💰 *Revenue (yesterday)*", rev_line, ""]

    # HITL Approvals
    pending   = approvals.get("pending", 0)
    high_risk = approvals.get("high_risk", 0)
    if pending == 0:
        appr_line = "  ✅ No pending approvals"
    elif high_risk:
        appr_line = f"  🔴 *{pending} pending*  ({high_risk} high-risk — review now)"
    else:
        appr_line = f"  🟡 {pending} pending  (no high-risk)"
    lines += ["✋ *HITL Approvals*", appr_line, ""]

    # Agent Runs
    ok  = runs.get("completed", 0)
    err = runs.get("errored",   0)
    cost  = runs.get("total_cost_usd",  0.0)
    saved = runs.get("total_saved_usd", 0.0)
    runs_line = f"  ✅ {ok} ok  •  ❌ {err} error{'s' if err != 1 else ''}"
    if ok + err > 0:
        runs_line += f"\n  💾 Cost: ${cost:.4f}  Saved: ${saved:.4f}"
    lines += ["🤖 *Agent Runs (yesterday)*", runs_line, ""]

    # Catch & Correct
    count = cnc.get("count", 0)
    if count == 0:
        cnc_line = "  ✅ No findings yesterday"
    else:
        cnc_line = f"  📝 {count} finding{'s' if count != 1 else ''} logged"
        for s in cnc.get("samples", []):
            cnc_line += f"\n    • {s}"
    lines += ["🔍 *Catch & Correct*", cnc_line, ""]

    # System health
    if pow_:
        score   = pow_.get("score", 0.0)
        uptime  = pow_.get("uptime_pct", 0.0)
        passed  = pow_.get("passed_cycles", 0)
        failed  = pow_.get("failed_cycles", 0)
        guards  = pow_.get("guard_blocks", 0)
        health_emoji = "✅" if score >= 0.9 else ("⚠️" if score >= 0.7 else "🔴")
        pow_line = (
            f"  {health_emoji} PoW: {score:.2f}  •  Uptime: {uptime:.2f}%\n"
            f"  Cycles: {passed} ok / {failed} failed  •  Guard blocks: {guards}"
        )
        lines += ["⚙️ *System Health*", pow_line, ""]

    # Footer
    lines += [f"[Open Dashboard]({DASHBOARD_URL})"]

    return "\n".join(lines)


# ── Delivery ───────────────────────────────────────────────────────────────────

def send_telegram(text: str) -> bool:
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("[digest] TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set — skipping Telegram.")
        return False
    result = _post_json(
        f"{TELEGRAM_API}/bot{TELEGRAM_TOKEN}/sendMessage",
        {
            "chat_id":                  TELEGRAM_CHAT_ID,
            "text":                     text,
            "parse_mode":               "Markdown",
            "disable_web_page_preview": True,
        },
    )
    if result.get("ok"):
        print("[digest] Telegram message sent ✓")
        return True
    print(f"[digest] Telegram error: {result.get('description') or result}")
    return False


def send_email(subject: str, body: str) -> bool:
    if not (GMAIL_USER and GMAIL_PASSWORD and ALERT_EMAIL):
        return False
    try:
        msg = MIMEText(body.replace("*", "").replace("_", ""), "plain")
        msg["Subject"] = subject
        msg["From"]    = GMAIL_USER
        msg["To"]      = ALERT_EMAIL
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(GMAIL_USER, GMAIL_PASSWORD)
            smtp.send_message(msg)
        print(f"[digest] Email sent to {ALERT_EMAIL} ✓")
        return True
    except Exception as exc:
        print(f"[digest] Email error: {exc}")
        return False


# ── Chat-ID helper ─────────────────────────────────────────────────────────────

def print_chat_id() -> None:
    """Print the chat-ID of the last message the bot received (run once to set it up)."""
    if not TELEGRAM_TOKEN:
        print("Set TELEGRAM_BOT_TOKEN first, then send your bot any message and re-run.")
        return
    data = _get_json(f"{TELEGRAM_API}/bot{TELEGRAM_TOKEN}/getUpdates")
    updates = data.get("result", []) if isinstance(data, dict) else []
    if not updates:
        print("No updates yet — send your bot a message first (e.g. /start), then re-run.")
        return
    last = updates[-1]
    msg  = last.get("message") or last.get("channel_post") or {}
    chat = msg.get("chat", {})
    print(f"Chat ID : {chat.get('id')}")
    print(f"Type    : {chat.get('type')}")
    print(f"Title   : {chat.get('title') or chat.get('first_name', '—')}")
    print(f"\nAdd this to your server .env (and GitHub Secrets) as:\n  TELEGRAM_CHAT_ID={chat.get('id')}")


# ── Entry point ────────────────────────────────────────────────────────────────

def main() -> None:
    if "--get-chat-id" in sys.argv:
        print_chat_id()
        return

    yesterday, today = _utc_day_range()
    date_label = yesterday.strftime("%a %-d %b %Y")

    print(f"[digest] Building digest for {date_label} …")

    revenue   = collect_revenue(yesterday, today)
    approvals = collect_approvals()
    runs      = collect_agent_runs(yesterday)
    cnc       = collect_catch_correct(yesterday)
    pow_      = collect_proof_of_work()

    message = build_message(date_label, revenue, approvals, runs, cnc, pow_)
    print("[digest] Message preview:\n" + message)

    telegram_ok = send_telegram(message)

    # Email fallback — only if Telegram failed AND gmail is configured
    if not telegram_ok:
        subject = f"ProfitEngine Digest — {date_label}"
        send_email(subject, message)


if __name__ == "__main__":
    main()
