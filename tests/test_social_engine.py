from __future__ import annotations

import json

import pytest

from runtime.eaos import social_engine


@pytest.mark.asyncio
async def test_telegram_post_strips_bom_from_credentials_and_message(monkeypatch) -> None:
    requests = []

    class DummyResponse:
        status = 200

    def fake_urlopen(request, timeout=0):  # noqa: ANN001, ANN202
        requests.append(request)
        return DummyResponse()

    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "\ufeff123456:test-token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "\ufeff987654")
    monkeypatch.setattr(social_engine.urllib.request, "urlopen", fake_urlopen)

    ok = await social_engine._post_telegram(
        social_engine.SocialPost(None, "TELEGRAM", "\ufeffNew ProfitEngine video")
    )

    assert ok is True
    assert requests
    request = requests[0]
    assert "\ufeff" not in request.full_url
    assert request.data is not None
    payload = json.loads(request.data.decode("utf-8"))
    assert payload["chat_id"] == "987654"
    assert payload["text"] == "New ProfitEngine video"
    assert request.headers["Content-type"] == "application/json; charset=UTF-8"
