"""Regression coverage for the one-shot quality-gate retry in
scripts/publish_article.py::generate_article (PR #116 review flag)."""

import json
from unittest.mock import patch

import pytest

import scripts.publish_article as pa


def _article_json(words: int = 1500) -> str:
    body = " ".join(["useful evidence-based workflow guidance"] * (words // 4))
    return json.dumps({
        "title": "Retry Test Article",
        "meta_description": "meta",
        "body": "## Section\n\n" + body,
    })


def _fake_quality(ok: bool, **kw):
    class Q:
        def __init__(self):
            self.ok = ok
            self.warnings = []
            self.errors = [] if ok else ["too short"]
            self.word_count = kw.get("words", 1500)
            self.h2_count = 6
            self.external_link_count = 2
    return Q()


@pytest.fixture
def groq_env(monkeypatch):
    monkeypatch.setattr(pa, "GROQ_KEY", "test-key")
    monkeypatch.setattr(pa, "GEMINI_KEY", "")
    monkeypatch.setattr(pa, "GROQ_MODELS", ["m1"])
    monkeypatch.setattr(pa, "GEMINI_MODELS", [])


def test_retry_succeeds_on_second_draft(groq_env):
    calls = []
    drafts = [_article_json(words=200), _article_json(words=1500)]

    def fake_call(prompt, model=None):
        calls.append(model)
        return drafts[len(calls) - 1]

    qualities = [_fake_quality(ok=False, words=200), _fake_quality(ok=True)]
    with patch.object(pa, "_call_groq", side_effect=fake_call), \
         patch("scripts.seo_content_quality.validate_article_quality",
               side_effect=qualities), \
         patch("scripts.seo_content_quality.format_quality_errors",
               return_value="too short"):
        article = pa.generate_article("topic")

    assert article["title"] == "Retry Test Article"
    assert len(calls) == 2  # exactly one regeneration


def test_retry_raises_after_two_failed_drafts(groq_env):
    calls = []

    def fake_call(prompt, model=None):
        calls.append(model)
        return _article_json(words=200)

    with patch.object(pa, "_call_groq", side_effect=fake_call), \
         patch("scripts.seo_content_quality.validate_article_quality",
               side_effect=lambda a: _fake_quality(ok=False)), \
         patch("scripts.seo_content_quality.format_quality_errors",
               return_value="too short"):
        with pytest.raises(RuntimeError, match="after retry"):
            pa.generate_article("topic")

    assert len(calls) == 2  # one initial + one retry, never a third


def test_passing_first_draft_does_not_retry(groq_env):
    calls = []

    def fake_call(prompt, model=None):
        calls.append(model)
        return _article_json()

    with patch.object(pa, "_call_groq", side_effect=fake_call), \
         patch("scripts.seo_content_quality.validate_article_quality",
               return_value=_fake_quality(ok=True)):
        pa.generate_article("topic")

    assert len(calls) == 1
