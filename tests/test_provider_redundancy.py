import importlib.util
from pathlib import Path
from unittest.mock import patch


def _passing_quality_gate():
    """Stub the publication quality gate — these tests cover provider
    failover, not quality. Returns a mock with an ok-typed result."""

    class _Q:
        ok = True
        warnings: list = []
        errors: list = []
        word_count = 1500
        h2_count = 6
        external_link_count = 2

    return patch(
        "scripts.seo_content_quality.validate_article_quality", return_value=_Q()
    )


def load_publisher():
    path = Path(__file__).resolve().parents[1] / "scripts" / "publish_article.py"
    spec = importlib.util.spec_from_file_location("publish_article_under_test", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_primary_model_failure_falls_back_to_secondary_groq(monkeypatch):
    publisher = load_publisher()
    publisher.GROQ_KEY = "test"
    publisher.GEMINI_KEY = ""
    publisher.GROQ_MODELS = ["bad-primary", "good-secondary"]
    calls = []

    def fake_groq(prompt, model=None):
        calls.append(model)
        if model == "bad-primary":
            raise RuntimeError("primary unavailable")
        return (
            '{"title":"Fallback works","slug":"fallback-works","meta_description":"verified fallback","tags":["test"],"body":"'
            + ("x" * 400)
            + '"}'
        )

    monkeypatch.setattr(publisher, "_call_groq", fake_groq)
    with _passing_quality_gate():
        article = publisher.generate_article("Provider failover test")
    assert article["title"] == "Fallback works"
    assert calls == ["bad-primary", "good-secondary"]


def test_all_groq_failures_fall_back_to_gemini(monkeypatch):
    publisher = load_publisher()
    publisher.GROQ_KEY = "test"
    publisher.GEMINI_KEY = "test"
    publisher.GROQ_MODELS = ["g1", "g2"]
    publisher.GEMINI_MODELS = ["gemini-secondary"]
    groq_calls = []
    gemini_calls = []

    def fake_groq(prompt, model=None):
        groq_calls.append(model)
        raise RuntimeError("groq unavailable")

    def fake_gemini(prompt, model=None):
        gemini_calls.append(model)
        return (
            '{"title":"Gemini fallback","slug":"gemini-fallback","meta_description":"verified fallback","tags":["test"],"body":"'
            + ("y" * 400)
            + '"}'
        )

    monkeypatch.setattr(publisher, "_call_groq", fake_groq)
    monkeypatch.setattr(publisher, "_call_gemini", fake_gemini)
    with _passing_quality_gate():
        article = publisher.generate_article("Cross-provider failover test")
    assert article["title"] == "Gemini fallback"
    assert groq_calls == ["g1", "g2"]
    assert gemini_calls == ["gemini-secondary"]
