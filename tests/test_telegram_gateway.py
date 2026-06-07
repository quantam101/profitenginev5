from __future__ import annotations

from fastapi.testclient import TestClient

from runtime.telegram_gateway import parse_update, stable_embedding


def _update(text: str) -> dict:
    return {
        "message": {
            "chat": {"id": 12345},
            "from": {"username": "operator"},
            "text": text,
        }
    }


def test_parse_known_command_routes_to_agent() -> None:
    command = parse_update(_update("/traffic Etsy launch pack"))
    assert command is not None
    assert command.agent_id == "traffic-agent"
    assert command.objective == "Etsy launch pack"
    assert command.actor == "telegram:operator"


def test_parse_agent_command() -> None:
    command = parse_update(_update("/agent proof-ledger verify revenue threshold"))
    assert command is not None
    assert command.agent_id == "proof-ledger"
    assert command.objective == "verify revenue threshold"


def test_stable_embedding_is_deterministic() -> None:
    first = stable_embedding("traffic-agent:Etsy launch pack")
    second = stable_embedding("traffic-agent:Etsy launch pack")
    assert first == second
    assert len(first) == 384


def test_telegram_webhook_rejects_bad_secret(monkeypatch) -> None:
    monkeypatch.setenv("TELEGRAM_WEBHOOK_SECRET", "real-secret")

    from runtime.api import app

    client = TestClient(app)
    response = client.post("/telegram/webhook", json=_update("/status"), headers={"x-telegram-bot-api-secret-token": "bad"})
    assert response.status_code == 403


def test_telegram_webhook_executes_runtime(monkeypatch) -> None:
    monkeypatch.setenv("TELEGRAM_WEBHOOK_SECRET", "real-secret")

    import runtime.api as api

    def fake_execute(payload):
        return {
            "status": "ok",
            "route_tier": "DETERMINISTIC_LOCAL",
            "output": f"agent={payload.agent_id}; objective={payload.objective}",
            "cached": False,
            "details": {},
        }

    sent_messages = []
    monkeypatch.setattr(api, "execute", fake_execute)
    monkeypatch.setattr(api, "send_telegram_message", lambda chat_id, text: sent_messages.append((chat_id, text)) or True)

    client = TestClient(api.app)
    response = client.post(
        "/telegram/webhook",
        json=_update("/offers find best cash offer"),
        headers={"x-telegram-bot-api-secret-token": "real-secret"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["executed"] is True
    assert body["agent_id"] == "offer-scout"
    assert sent_messages
    assert "agent=offer-scout" in sent_messages[0][1]
