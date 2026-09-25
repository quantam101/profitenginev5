from __future__ import annotations

from fastapi.testclient import TestClient


def test_llm_router_defaults_to_ollama(monkeypatch):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("OLLAMA_API_KEY", "ollama")
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")

    import importlib
    import agents.taylor.llm_router as llm_router
    importlib.reload(llm_router)  # PROVIDERS snapshot env at import time
    get_router = llm_router.get_router

    active = get_router().active_provider()
    assert active is not None
    assert active.name == "ollama-llama3.2"


def test_taylor_health_and_safe_payment_prompt(tmp_path, monkeypatch):
    monkeypatch.setenv("TAYLOR_DB_PATH", str(tmp_path / "taylor.db"))
    monkeypatch.setenv("OLLAMA_API_KEY", "ollama")

    from agents.taylor.server import app

    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["payments"]["mode"] == "checkout_link_sms"


def test_appointment_tool_persists_without_twilio(tmp_path, monkeypatch):
    monkeypatch.setenv("TAYLOR_DB_PATH", str(tmp_path / "taylor.db"))
    monkeypatch.delenv("TWILIO_ACCOUNT_SID", raising=False)
    monkeypatch.delenv("TWILIO_AUTH_TOKEN", raising=False)

    from agents.taylor.server import app

    client = TestClient(app)
    response = client.post(
        "/tool/book_appointment",
        json={
            "slot_datetime": "2026-06-08T09:00:00",
            "service_type": "audit",
            "site_address": "123 Main St, Phoenix, AZ",
            "contact_phone": "+16025550100",
            "contact_name": "Test Caller",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["appointment_id"] >= 1
    assert body["sms_sent"] is False


def test_twilio_voice_returns_twiml(tmp_path, monkeypatch):
    monkeypatch.setenv("TAYLOR_DB_PATH", str(tmp_path / "taylor.db"))

    from agents.taylor.server import app

    client = TestClient(app)
    response = client.post("/twilio/voice", data={"CallSid": "CA123", "From": "+16025550100"})
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/xml")
    assert "<Response>" in response.text
    assert "<Dial>" in response.text


def test_call_ended_event_is_logged(tmp_path, monkeypatch):
    monkeypatch.setenv("TAYLOR_DB_PATH", str(tmp_path / "taylor.db"))

    from agents.taylor.server import app

    client = TestClient(app)
    response = client.post(
        "/events/call-ended",
        json={"data": {"call_id": "call_123", "call_analysis": {"call_summary": "Booked estimate"}}},
    )
    assert response.status_code == 200
    assert response.json()["call_id"] == "call_123"

    health = client.get("/health")
    assert health.json()["store"]["events"] == 1


def test_payment_tool_fails_closed_without_stripe(tmp_path, monkeypatch):
    monkeypatch.setenv("TAYLOR_DB_PATH", str(tmp_path / "taylor.db"))
    monkeypatch.delenv("STRIPE_SECRET_KEY", raising=False)

    from agents.taylor.server import app

    client = TestClient(app)
    response = client.post(
        "/tool/create_secure_payment_link",
        json={
            "amount_in_cents": 35000,
            "billing_zip": "85001",
            "phone_number": "+16025550100",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["action"] == "transfer"
    assert "STRIPE_SECRET_KEY" in body["error"]
