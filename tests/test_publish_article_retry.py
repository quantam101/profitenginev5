"""Regression coverage for bounded quality repair in publish_article."""

import json
from unittest.mock import patch

import pytest

import scripts.publish_article as pa


def _article_json(words: int = 1500) -> str:
    body = " ".join(["useful evidence-based workflow guidance"] * (words // 4))
    return json.dumps({
        "title": "Quality Repair Test Article",
        "meta_description": "A concrete description long enough for the deterministic fixture.",
        "body": "## Section\n\n" + body,
    })


def _fake_quality(ok: bool, words: int = 1500):
    class Q:
        def __init__(self):
            self.ok = ok
            self.warnings = []
            self.errors = [] if ok else ["too short"]
            self.word_count = words
            self.h2_count = 6
            self.external_link_count = 2
    return Q()


@pytest.fixture
def provider_env(monkeypatch):
    monkeypatch.setattr(pa, "GROQ_KEY", "groq-test-key")
    monkeypatch.setattr(pa, "GEMINI_KEY", "gemini-test-key")
    monkeypatch.setattr(pa, "GROQ_MODELS", ["groq-test"])
    monkeypatch.setattr(pa, "GEMINI_MODELS", ["gemini-test"])


def test_groq_repair_succeeds_after_initial_quality_failure(provider_env):
    groq_calls = []

    def fake_groq(prompt, model=None):
        groq_calls.append((prompt, model))
        return _article_json(words=200 if len(groq_calls) == 1 else 1500)

    qualities = [_fake_quality(False, 200), _fake_quality(True, 1500)]
    with patch.object(pa, "_call_groq", side_effect=fake_groq), \
         patch.object(pa, "_call_gemini") as gemini, \
         patch("scripts.seo_content_quality.validate_article_quality",
               side_effect=qualities), \
         patch("scripts.seo_content_quality.format_quality_errors",
               return_value="article too short"):
        article = pa.generate_article("topic")

    assert article["title"] == "Quality Repair Test Article"
    assert len(groq_calls) == 2
    assert "QUALITY DEFECTS" in groq_calls[1][0]
    gemini.assert_not_called()


def test_falls_back_to_gemini_repair_then_fails_closed(provider_env):
    with patch.object(pa, "_call_groq", return_value=_article_json(words=200)) as groq, \
         patch.object(pa, "_call_gemini", return_value=_article_json(words=300)) as gemini, \
         patch("scripts.seo_content_quality.validate_article_quality",
               side_effect=[
                   _fake_quality(False, 200),
                   _fake_quality(False, 200),
                   _fake_quality(False, 300),
               ]), \
         patch("scripts.seo_content_quality.format_quality_errors",
               side_effect=["too short", "still short", "still short"]):
        with pytest.raises(RuntimeError, match="bounded repair attempts"):
            pa.generate_article("topic")

    assert groq.call_count == 2
    assert gemini.call_count == 1


def test_passing_first_draft_does_not_repair(provider_env):
    with patch.object(pa, "_call_groq", return_value=_article_json()) as groq, \
         patch.object(pa, "_call_gemini") as gemini, \
         patch("scripts.seo_content_quality.validate_article_quality",
               return_value=_fake_quality(True)):
        pa.generate_article("topic")

    assert groq.call_count == 1
    gemini.assert_not_called()
