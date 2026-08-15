"""
Already Here LLC — SMTP Dispatcher
Multi-provider: Gmail SMTP (immediate), Brevo SMTP relay (professional), or any provider.

NOTE: Zoho free plan does not include SMTP — use one of the options below.

--- OPTION A: Gmail SMTP (immediate, 500/day free) ---
Sends FROM alreadyherellc@gmail.com with Reply-To dispatch@alreadyherellc.com.
Replies land in your Zoho inbox automatically.
  1. myaccount.google.com/apppasswords → Generate → name "Already Here Outreach"
  2. Add to pipeline/.env:
       SMTP_HOST=smtp.gmail.com
       SMTP_PORT=587
       SMTP_USER=alreadyherellc@gmail.com
       SMTP_PASSWORD=$GMAIL_APP_PASSWORD
       SMTP_REPLY_TO=dispatch@alreadyherellc.com

--- OPTION B: Brevo SMTP relay (professional, 300/day free, sends FROM your domain) ---
Sends FROM dispatch@alreadyherellc.com after domain DNS verification (10 min).
  1. Sign up free at brevo.com
  2. Settings → Senders & IPs → verify alreadyherellc.com domain
  3. SMTP & API → copy SMTP credentials
  4. Add to pipeline/.env:
       SMTP_HOST=smtp-relay.brevo.com
       SMTP_PORT=587
       SMTP_USER=$BREVO_LOGIN_EMAIL
       SMTP_PASSWORD=$BREVO_SMTP_KEY
       SMTP_SENDER_EMAIL=dispatch@alreadyherellc.com
       SMTP_REPLY_TO=dispatch@alreadyherellc.com

Usage:
  from smtp_dispatch import send_email, send_batch
  await send_email(to="FieldTech@cptnetworks.com", subject="...", body="...", cc="FSP@cptnetworks.com")

One-off CLI:
  SMTP_TO=FieldTech@cptnetworks.com SMTP_CC=FSP@cptnetworks.com SMTP_SUBJECT="..." SMTP_BODY="..." python pipeline/smtp_dispatch.py
"""

from __future__ import annotations

import asyncio
import logging
import argparse
import os
import re
import smtplib
import sys
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger("SMTPDispatch")

# ── Config ────────────────────────────────────────────────────────────────────

# ── SMTP config ───────────────────────────────────────────────────────────────
_SMTP_HOST   = os.getenv("SMTP_HOST",     "smtp.gmail.com")
_SMTP_PORT   = int(os.getenv("SMTP_PORT", "587"))
# SMTP credentials accept the standard SMTP_* names as well as legacy Gmail names.
_SMTP_USER   = os.getenv("SMTP_USER", "").strip() or os.getenv("GMAIL_USER", "").strip() or os.getenv("GMAIL_SENDER", "").strip()
_SMTP_PASS   = "".join(os.getenv("SMTP_PASSWORD", "").split()) or "".join(os.getenv("GMAIL_APP_PASSWORD", "").split())

# SMTP_SENDER_EMAIL lets Brevo send FROM dispatch@ even when logging in with a different user
_SMTP_SENDER  = os.getenv("SMTP_SENDER_EMAIL",  _SMTP_USER or "dispatch@alreadyherellc.com")
_SMTP_REPLY_TO = os.getenv("SMTP_REPLY_TO", os.getenv("GMAIL_REPLY_TO", "dispatch@alreadyherellc.com"))

_SENDER      = os.getenv("SMTP_SENDER_EMAIL", os.getenv("GMAIL_FROM_ADDRESS", _SMTP_USER or "dispatch@alreadyherellc.com"))
_SENDER_NAME = os.getenv("OUTREACH_SENDER_NAME", "Stephen Franklin")
_COMPANY     = os.getenv("OUTREACH_COMPANY",     "Already Here LLC")


def _check_config() -> bool:
    if not _SMTP_PASS or not _SMTP_USER:
        logger.warning(
            "SMTP not configured — email dispatch disabled.\n"
            "Add to pipeline/.env one of the following:\n"
            "  Gmail:\n"
            "    SMTP_HOST=smtp.gmail.com\n"
            "    SMTP_PORT=587\n"
            "    SMTP_USER=alreadyherellc@gmail.com\n"
            "    SMTP_PASSWORD=<16-char Gmail App Password>\n"
            "    SMTP_REPLY_TO=dispatch@alreadyherellc.com\n"
            "  Brevo:\n"
            "    SMTP_HOST=smtp-relay.brevo.com\n"
            "    SMTP_PORT=587\n"
            "    SMTP_USER=<brevo login email>\n"
            "    SMTP_PASSWORD=<brevo smtp key>\n"
            "    SMTP_SENDER_EMAIL=dispatch@alreadyherellc.com\n"
            "Get Gmail App Password: https://myaccount.google.com/apppasswords"
        )
        return False
    return True


# ── Core send (sync, runs in thread pool) ────────────────────────────────────

def _split_addresses(value: Optional[str]) -> List[str]:
    if not value:
        return []
    return [a.strip() for a in value.replace(";", ",").split(",") if a.strip()]


def _smtp_send(
    to: str,
    subject: str,
    body: str,
    reply_to: Optional[str] = None,
    cc: Optional[str] = None,
    bcc: Optional[str] = None,
) -> bool:
    """Synchronous Gmail SMTP send. Called via asyncio.to_thread."""
    to_addrs = _split_addresses(to)
    cc_addrs = _split_addresses(cc)
    bcc_addrs = _split_addresses(bcc)
    all_recipients = to_addrs + cc_addrs + bcc_addrs
    if not all_recipients:
        logger.error("No recipients provided")
        return False

    # A --from value like "Stephen Franklin <dispatch@alreadyherellc.com>" should be used as-is.
    from_header = _SENDER
    from_addr = _SENDER
    match = re.match(r"^(.*?)\s*<([^>]+)>\s*$", _SENDER)
    if match:
        from_header = _SENDER
        from_addr = match.group(2).strip()
    else:
        from_header = f"{_SENDER_NAME} | {_COMPANY} <{_SENDER}>"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]     = from_header
    msg["To"]       = ", ".join(to_addrs)
    if cc_addrs:
        msg["Cc"] = ", ".join(cc_addrs)
    msg["Reply-To"] = reply_to or _SMTP_REPLY_TO

    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP(_SMTP_HOST, _SMTP_PORT, timeout=15) as server:
            server.ehlo()
            server.starttls()
            server.login(_SMTP_USER, _SMTP_PASS)
            server.sendmail(from_addr, all_recipients, msg.as_string())
        logger.info(f"Sent → {', '.join(all_recipients)} | {subject[:60]}")
        return True
    except smtplib.SMTPAuthenticationError:
        logger.error(
            f"SMTP authentication failed ({_SMTP_HOST}).\n"
            "Zoho: use an App Password from mail.zoho.com → Settings → Security → App Passwords\n"
            "Gmail: use an App Password from myaccount.google.com/apppasswords\n"
            "Do NOT use your regular login password."
        )
        return False
    except smtplib.SMTPRecipientsRefused:
        logger.warning(f"Recipient refused: {to}")
        return False
    except Exception as exc:
        logger.error(f"SMTP error sending to {to}: {exc}")
        return False


# ── Async wrappers ────────────────────────────────────────────────────────────

async def send_email(
    to: str,
    subject: str,
    body: str,
    reply_to: Optional[str] = None,
    cc: Optional[str] = None,
    bcc: Optional[str] = None,
    dry_run: bool = False,
) -> bool:
    """
    Send a single email via the configured SMTP relay.
    If SMTP credentials are not set or dry_run=True, prints to stdout only.
    """
    if dry_run or not _check_config():
        print(f"\n[DRY-RUN] To: {to}")
        if cc:
            print(f"Cc: {cc}")
        if bcc:
            print(f"Bcc: {bcc}")
        print(f"Subject: {subject}\n{body}\n{'─'*60}")
        return True

    return await asyncio.to_thread(_smtp_send, to, subject, body, reply_to, cc, bcc)


async def send_batch(
    messages: List[dict],
    concurrency: int = 5,
    delay_between: float = 1.2,   # seconds between sends — avoids Gmail rate-limit flags
    dry_run: bool = False,
) -> dict:
    """
    Send a batch of emails with rate-limiting.

    messages: list of dicts with keys: to, subject, body, (optional) reply_to, cc, bcc
    Returns: {"sent": N, "failed": N, "skipped": N}
    """
    if not dry_run and not _check_config():
        logger.warning("Batch skipped — GMAIL_APP_PASSWORD not configured.")
        return {"sent": 0, "failed": 0, "skipped": len(messages)}

    sem = asyncio.Semaphore(concurrency)
    results = {"sent": 0, "failed": 0, "skipped": 0}

    async def _one(msg: dict) -> None:
        async with sem:
            ok = await send_email(
                to=msg["to"],
                subject=msg["subject"],
                body=msg["body"],
                reply_to=msg.get("reply_to"),
                cc=msg.get("cc"),
                bcc=msg.get("bcc"),
                dry_run=dry_run,
            )
            if ok:
                results["sent"] += 1
            else:
                results["failed"] += 1
            # Polite delay to avoid triggering Gmail's anti-spam rate limits
            await asyncio.sleep(delay_between)

    await asyncio.gather(*(_one(m) for m in messages))
    logger.info(f"Batch complete: {results}")
    return results


# ── CLI smoke test ────────────────────────────────────────────────────────────

async def _oneoff() -> bool:
    """Send a one-off email from environment variables."""
    to = os.getenv("SMTP_TO", "")
    subject = os.getenv("SMTP_SUBJECT", "")
    body = os.getenv("SMTP_BODY", "")
    if not to or not subject or not body:
        logger.error("Set SMTP_TO, SMTP_SUBJECT, and SMTP_BODY")
        return False
    cc = os.getenv("SMTP_CC") or None
    bcc = os.getenv("SMTP_BCC") or None
    reply_to = os.getenv("SMTP_REPLY_TO") or None
    dry_run = os.getenv("SMTP_DRY_RUN", "false").lower() in {"1", "true", "yes"}
    return await send_email(
        to=to,
        subject=subject,
        body=body,
        reply_to=reply_to,
        cc=cc,
        bcc=bcc,
        dry_run=dry_run,
    )


async def _test() -> None:
    """Send a test email to yourself to confirm SMTP config works."""
    test_to = os.getenv("SMTP_TEST_TO", _SENDER)
    print(f"Sending test email to {test_to} ...")
    ok = await send_email(
        to=test_to,
        subject="Already Here LLC — Zoho SMTP Config Test",
        body=(
            f"Zoho SMTP is working.\n\n"
            f"Sender: {_SENDER_NAME} | {_COMPANY}\n"
            f"Dispatch address: dispatch@alreadyherellc.com\n"
            f"Time: {datetime.now(timezone.utc).isoformat()}\n\n"
            "Outreach will send from dispatch@alreadyherellc.com automatically."
        ),
    )
    print("PASS — check your Zoho inbox." if ok else "FAIL — check the error above.")


async def _cli() -> int:
    parser = argparse.ArgumentParser(description="Send a one-off email via SMTP.")
    parser.add_argument("--to", required=True, help="Primary recipient(s), comma separated")
    parser.add_argument("--cc", help="CC recipient(s), comma separated")
    parser.add_argument("--bcc", help="BCC recipient(s), comma separated")
    parser.add_argument("--from", dest="from_header", help="From header, e.g. 'Stephen Franklin <dispatch@alreadyherellc.com>'")
    parser.add_argument("--reply-to", help="Reply-To header")
    parser.add_argument("--subject", required=True, help="Email subject")
    parser.add_argument("--body", help="Plain-text body (use --body-file for long content)")
    parser.add_argument("--body-file", help="Path to a file containing the plain-text body")
    parser.add_argument("--dry-run", action="store_true", help="Print the message without sending")
    args = parser.parse_args()

    body = args.body
    if args.body_file:
        body = Path(args.body_file).read_text(encoding="utf-8")
    if not body:
        parser.error("--body or --body-file is required")

    global _SENDER, _SMTP_REPLY_TO
    if args.from_header:
        _SENDER = args.from_header
    if args.reply_to:
        _SMTP_REPLY_TO = args.reply_to

    if args.dry_run:
        ok = await send_email(to=args.to, cc=args.cc, bcc=args.bcc, reply_to=args.reply_to, subject=args.subject, body=body, dry_run=True)
    else:
        if not _check_config():
            return 1
        ok = await send_email(to=args.to, cc=args.cc, bcc=args.bcc, reply_to=args.reply_to, subject=args.subject, body=body, dry_run=False)
    return 0 if ok else 1


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    if os.getenv("SMTP_TO"):
        ok = asyncio.run(_oneoff())
        print("OK — one-off email dispatched." if ok else "FAIL — one-off email not dispatched.")
    else:
        sys.exit(asyncio.run(_cli()))
