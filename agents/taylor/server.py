"""Taylor FastAPI voice-agent backend.

Supports Retell/Vapi tool webhooks and direct Twilio voice/SMS webhooks.
Payments use Stripe Checkout links by SMS; Taylor never collects card data.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import urlencode
from xml.sax.saxutils import escape

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response

from agents.taylor.llm_router import get_router
from agents.taylor.storage import TaylorStore
from agents.taylor.system_prompt import build_system_prompt
from agents.taylor.tools import TOOLS

logger = logging.getLogger("Taylor")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [TAYLOR] %(levelname)s %(message)s")

app = FastAPI(title="Taylor Voice Agent", version="1.0.0")


def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def _store() -> TaylorStore:
    return TaylorStore(_env("TAYLOR_DB_PATH", "./datacenter/taylor.db"))


def _transfer_numbers() -> list[str]:
    return [
        _env("TAYLOR_TRANSFER_NUMBER", "+16028822920"),
        _env("TAYLOR_TRANSFER_NUMBER_BACKUP", "+16198066457"),
        _env("TAYLOR_TRANSFER_NUMBER_BACKUP_2", "+16198849241"),
    ]


def _twiml(*parts: str) -> Response:
    return Response(
        content="<?xml version=\"1.0\" encoding=\"UTF-8\"?><Response>" + "".join(parts) + "</Response>",
        media_type="application/xml",
    )


def _say(text: str) -> str:
    return f"<Say voice=\"alice\">{escape(text)}</Say>"


def _message(text: str) -> str:
    return f"<Message>{escape(text)}</Message>"


def _dial(number: str) -> str:
    return f"<Dial>{escape(number)}</Dial>"


async def _send_sms(to: str, body: str) -> bool:
    sid = _env("TWILIO_ACCOUNT_SID")
    token = _env("TWILIO_AUTH_TOKEN")
    from_number = _env("TWILIO_FROM_NUMBER")
    if not sid or not token or not from_number:
        logger.info("Twilio SMS skipped: credentials not configured")
        return False

    url = f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json"
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(
            url,
            data={"To": to, "From": from_number, "Body": body},
            auth=(sid, token),
        )
    if resp.status_code not in (200, 201):
        logger.error("Twilio SMS failed %s: %s", resp.status_code, resp.text[:300])
        return False
    return True


async def _create_stripe_checkout(
    *,
    amount_in_cents: int,
    billing_zip: str,
    invoice_id: str,
    description: str,
    phone_number: str,
) -> dict[str, str]:
    secret_key = _env("STRIPE_SECRET_KEY")
    success_url = _env("TAYLOR_PAYMENT_SUCCESS_URL", "https://www.alreadyherellc.com/payment/success")
    cancel_url = _env("TAYLOR_PAYMENT_CANCEL_URL", "https://www.alreadyherellc.com/payment/cancel")
    if not secret_key:
        raise RuntimeError("STRIPE_SECRET_KEY is not configured")
    if amount_in_cents < 50:
        raise ValueError("Payment amount must be at least 50 cents")

    data = {
        "mode": "payment",
        "success_url": success_url,
        "cancel_url": cancel_url,
        "line_items[0][quantity]": "1",
        "line_items[0][price_data][currency]": "usd",
        "line_items[0][price_data][unit_amount]": str(amount_in_cents),
        "line_items[0][price_data][product_data][name]": description[:120],
        "metadata[invoice_id]": invoice_id,
        "metadata[billing_zip]": billing_zip,
        "metadata[channel]": "taylor_voice",
        "metadata[phone_number]": phone_number,
    }
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            "https://api.stripe.com/v1/checkout/sessions",
            content=urlencode(data),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            auth=(secret_key, ""),
        )
    if resp.status_code >= 400:
        raise RuntimeError(f"Stripe Checkout failed {resp.status_code}: {resp.text[:300]}")
    payload = resp.json()
    return {"url": payload["url"], "id": payload["id"]}


@app.get("/health")
async def health() -> dict[str, Any]:
    router = get_router()
    return {
        "ok": True,
        "agent": "Taylor",
        "voice": {
            "twilio": bool(_env("TWILIO_ACCOUNT_SID") and _env("TWILIO_AUTH_TOKEN")),
            "retell": bool(_env("RETELL_API_KEY") or _env("RETELL_AGENT_ID")),
            "vapi": bool(_env("VAPI_API_KEY")),
        },
        "payments": {"stripe": bool(_env("STRIPE_SECRET_KEY")), "mode": "checkout_link_sms"},
        "llm_active_provider": router.active_provider().name if router.active_provider() else None,
        "store": _store().counts(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/llm/status")
async def llm_status() -> dict[str, Any]:
    router = get_router()
    active = router.active_provider()
    return {"active": active.name if active else None, "providers": router.status()}


async def tool_check_calendar(target_date: str, service_type: str = "general") -> dict[str, Any]:
    try:
        start = datetime.strptime(target_date, "%Y-%m-%d").date()
    except ValueError:
        start = (datetime.now(timezone.utc) + timedelta(days=1)).date()

    slots: list[dict[str, str]] = []
    day = start
    while len(slots) < 2:
        if day.weekday() < 6:
            for hour in ("09:00", "13:00"):
                slots.append({"datetime": f"{day.isoformat()}T{hour}:00", "label": f"{day:%A %B %d} at {hour}"})
                if len(slots) == 2:
                    break
        day += timedelta(days=1)
    return {"available_slots": slots, "spoken": f"I have {slots[0]['label']} or {slots[1]['label']}. Which works best."}


async def tool_book_appointment(
    slot_datetime: str,
    service_type: str,
    site_address: str,
    contact_phone: str,
    contact_name: str = "",
    company_name: str = "",
) -> dict[str, Any]:
    appointment = _store().add_appointment(
        slot_datetime=slot_datetime,
        service_type=service_type,
        site_address=site_address,
        contact_phone=contact_phone,
        contact_name=contact_name,
        company_name=company_name,
    )
    sms_sent = await _send_sms(
        contact_phone,
        f"Already Here LLC confirmed {service_type} service at {site_address} on {slot_datetime}. Ref AHL-{appointment.id}.",
    )
    return {
        "appointment_id": appointment.id,
        "sms_sent": sms_sent,
        "spoken": "Your appointment is confirmed. I sent the confirmation by text message.",
    }


async def tool_create_secure_payment_link(
    amount_in_cents: int,
    billing_zip: str,
    phone_number: str,
    invoice_id: str = "",
    description: str = "Already Here LLC service payment",
    call_id: str = "",
) -> dict[str, Any]:
    invoice = invoice_id or f"PHONE-{int(time.time())}"
    checkout = await _create_stripe_checkout(
        amount_in_cents=amount_in_cents,
        billing_zip=billing_zip,
        invoice_id=invoice,
        description=description,
        phone_number=phone_number,
    )
    _store().add_payment_link(
        call_id=call_id,
        invoice_id=invoice,
        amount_cents=amount_in_cents,
        billing_zip=billing_zip,
        checkout_url=checkout["url"],
        stripe_session_id=checkout["id"],
        phone_number=phone_number,
    )
    sms_sent = await _send_sms(phone_number, f"Already Here LLC secure payment link for invoice {invoice}: {checkout['url']}")
    return {
        "invoice_id": invoice,
        "checkout_session_id": checkout["id"],
        "checkout_url": checkout["url"],
        "sms_sent": sms_sent,
        "spoken": "I sent a secure Stripe payment link by text message. Please complete payment from that link.",
    }


async def tool_transfer_to_live(reason: str) -> dict[str, Any]:
    return {
        "action": "transfer",
        "reason": reason,
        "transfer_to": _transfer_numbers()[0],
        "transfer_to_backup": _transfer_numbers()[1],
        "transfer_to_backup_2": _transfer_numbers()[2],
        "spoken": "Please hold while I connect you with operations.",
    }


TOOL_MAP = {
    "check_calendar_availability": tool_check_calendar,
    "book_appointment": tool_book_appointment,
    "create_secure_payment_link": tool_create_secure_payment_link,
    "transfer_to_live": tool_transfer_to_live,
}


async def dispatch_tool(name: str, args: dict[str, Any], call_id: str = "") -> dict[str, Any]:
    fn = TOOL_MAP.get(name)
    if fn is None:
        return {"error": f"Unknown tool: {name}", "spoken": "I need to connect you with operations."}
    if name == "create_secure_payment_link":
        args.setdefault("call_id", call_id)
    try:
        return await asyncio.wait_for(fn(**args), timeout=0.95)
    except Exception as exc:
        logger.exception("Taylor tool failed: %s", name)
        transfer = await tool_transfer_to_live(f"{name}_failed")
        transfer["error"] = str(exc)
        return transfer


@app.post("/tool/{tool_name}")
async def call_tool_directly(tool_name: str, request: Request) -> JSONResponse:
    return JSONResponse(await dispatch_tool(tool_name, await request.json()))


@app.post("/events/call-ended")
async def call_ended_event(request: Request) -> JSONResponse:
    body = await request.json()
    data = body.get("data", body)
    call_id = str(
        data.get("call_id")
        or data.get("callId")
        or data.get("id")
        or body.get("call_id")
        or body.get("callId")
        or f"call-{int(time.time())}"
    )
    _store().log_event(call_id=call_id, event_type="call:ended", payload_json=json.dumps(body)[:8000])
    return JSONResponse({"ok": True, "call_id": call_id})


@app.post("/retell/webhook")
async def retell_webhook(request: Request) -> JSONResponse:
    body = await request.json()
    event = body.get("event", "")
    call = body.get("data", {})
    call_id = call.get("call_id", "")
    _store().log_event(call_id=call_id, event_type=f"retell:{event}", payload_json=json.dumps(body)[:8000])

    if event == "call_started":
        return JSONResponse({"agent_config": {"system_prompt": build_system_prompt(), "tools": TOOLS}})
    if event == "tool_call_invocation":
        args = call.get("arguments", {})
        if isinstance(args, str):
            args = json.loads(args)
        result = await dispatch_tool(call.get("name", ""), args, call_id)
        return JSONResponse({"result": json.dumps(result)})
    return JSONResponse({"status": "ok"})


@app.post("/vapi/webhook")
async def vapi_webhook(request: Request) -> JSONResponse:
    body = await request.json()
    message = body.get("message", {})
    msg_type = message.get("type", "")
    call_id = message.get("call", {}).get("id", "")
    _store().log_event(call_id=call_id, event_type=f"vapi:{msg_type}", payload_json=json.dumps(body)[:8000])

    if msg_type == "assistant-request":
        return JSONResponse({"assistant": {"model": {"provider": "server", "url": _env("TAYLOR_SERVER_URL")}, "voice": {"provider": "vapi"}}})
    if msg_type == "function-call":
        fn_call = message.get("functionCall", {})
        result = await dispatch_tool(fn_call.get("name", ""), fn_call.get("parameters", {}), call_id)
        return JSONResponse({"result": json.dumps(result)})
    return JSONResponse({"status": "ok"})


@app.post("/twilio/voice")
async def twilio_voice(request: Request) -> Response:
    form = await request.form()
    call_id = str(form.get("CallSid", ""))
    from_number = str(form.get("From", ""))
    _store().log_event(call_id=call_id, event_type="twilio:voice", payload_json=json.dumps({"from": from_number}))
    return _twiml(
        _say("Thanks for calling Already Here. Taylor is coming online now."),
        _say("For scheduling or payments, please stay on the line while I connect operations."),
        _dial(_transfer_numbers()[0]),
    )


@app.post("/twilio/sms")
async def twilio_sms(request: Request) -> Response:
    form = await request.form()
    from_number = str(form.get("From", ""))
    body = str(form.get("Body", ""))
    _store().log_event(call_id=from_number, event_type="twilio:sms", payload_json=json.dumps({"body": body})[:8000])
    return _twiml(_message("Already Here received your message. Taylor will follow up shortly."))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "agents.taylor.server:app",
        host=_env("TAYLOR_HOST", "127.0.0.1"),
        port=int(_env("TAYLOR_PORT", "8001")),
        reload=False,
    )
