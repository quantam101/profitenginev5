from __future__ import annotations

import json
from io import BytesIO
from urllib.parse import parse_qs
from urllib.parse import urlparse

from runtime import gumroad_client


class _Response(BytesIO):
    def __enter__(self) -> "_Response":
        return self

    def __exit__(self, *args: object) -> None:
        return None


def test_create_product_encodes_tags_as_repeated_fields(monkeypatch) -> None:
    captured: dict[str, bytes] = {}

    def fake_urlopen(request, timeout):
        captured["body"] = request.data
        return _Response(json.dumps({"success": True, "product": {"id": "p1"}}).encode())

    monkeypatch.setenv("GUMROAD_ACCESS_TOKEN", "token")
    monkeypatch.setattr(gumroad_client, "_product_exists", lambda name: None)
    monkeypatch.setattr(gumroad_client.urllib.request, "urlopen", fake_urlopen)

    result = gumroad_client.create_product(
        {
            "name": "Test Product",
            "price": 100,
            "description": "Digital product",
            "tags": ["ai", "content", "automation"],
            "url_suffix": "test-product",
        }
    )

    assert result["ok"] is True
    body = parse_qs(captured["body"].decode())
    assert body["tags[]"] == ["ai", "content", "automation"]


def test_get_sales_preserves_existing_query_when_adding_token(monkeypatch) -> None:
    captured: dict[str, str] = {}

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        return _Response(json.dumps({"success": True, "sales": []}).encode())

    monkeypatch.setenv("GUMROAD_ACCESS_TOKEN", "token")
    monkeypatch.setattr(gumroad_client.urllib.request, "urlopen", fake_urlopen)

    result = gumroad_client.get_sales(after="2026-06-01")

    assert result["ok"] is True
    parsed = urlparse(captured["url"])
    params = parse_qs(parsed.query)
    assert params["after"] == ["2026-06-01"]
    assert params["access_token"] == ["token"]
