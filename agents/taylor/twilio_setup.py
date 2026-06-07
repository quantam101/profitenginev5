"""Configure a purchased Twilio number for Taylor.

This script can search and buy a number, or configure an existing
TWILIO_PHONE_NUMBER_SID. It never prints auth tokens.
"""

from __future__ import annotations

import os
import sys


def _require(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        sys.exit(f"Missing required env var: {name}")
    return value


def main() -> None:
    try:
        from twilio.rest import Client
    except ImportError:
        sys.exit("Install dependency first: python -m pip install twilio")

    sid = _require("TWILIO_ACCOUNT_SID")
    token = _require("TWILIO_AUTH_TOKEN")
    server_url = _require("TAYLOR_SERVER_URL").rstrip("/")
    existing_sid = os.getenv("TWILIO_PHONE_NUMBER_SID", "").strip()

    client = Client(sid, token)
    voice_url = f"{server_url}/twilio/voice"
    sms_url = f"{server_url}/twilio/sms"

    if existing_sid:
        number = client.incoming_phone_numbers(existing_sid).update(
            voice_url=voice_url,
            voice_method="POST",
            sms_url=sms_url,
            sms_method="POST",
            friendly_name="Already Here LLC - Taylor",
        )
        print(f"Configured existing Twilio number: {number.phone_number}")
        print(f"Voice URL: {voice_url}")
        print(f"SMS URL:   {sms_url}")
        return

    area_code = os.getenv("TWILIO_AREA_CODE", "602")
    available = client.available_phone_numbers("US").local.list(
        area_code=area_code,
        voice_enabled=True,
        sms_enabled=True,
        limit=5,
    )
    if not available:
        sys.exit(f"No Twilio numbers found for area code {area_code}. Buy one manually and rerun with TWILIO_PHONE_NUMBER_SID.")

    print("Available numbers:")
    for index, number in enumerate(available):
        print(f"{index}: {number.phone_number} {number.locality or ''} {number.region or ''}".strip())

    choice = input("Choose number index to purchase [0]: ").strip() or "0"
    selected = available[int(choice)]
    purchased = client.incoming_phone_numbers.create(
        phone_number=selected.phone_number,
        friendly_name="Already Here LLC - Taylor",
        voice_url=voice_url,
        voice_method="POST",
        sms_url=sms_url,
        sms_method="POST",
    )
    print(f"Purchased and configured: {purchased.phone_number}")
    print(f"TWILIO_FROM_NUMBER={purchased.phone_number}")
    print(f"TWILIO_PHONE_NUMBER_SID={purchased.sid}")


if __name__ == "__main__":
    main()

