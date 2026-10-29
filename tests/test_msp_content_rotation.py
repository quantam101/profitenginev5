"""Regression checks for unattended MSP-only canonical publication."""
from pathlib import Path

from scripts import article_topics, publish_article

ROOT = Path(__file__).resolve().parents[1]


def test_rotation_never_selects_unrelated_income_topics():
    assert len(article_topics.MSP_TOPICS) >= 25
    assert len(article_topics.MSP_TOPICS) == len(set(article_topics.MSP_TOPICS))
    assert all("Passive Income" not in t and "Affiliate Marketing" not in t
               for t in article_topics.MSP_TOPICS)
    assert all(article_topics.pick_topic(offset) in article_topics.MSP_TOPICS
               for offset in range(370))


def test_unattended_publication_ignores_growth_topic_queue(monkeypatch):
    monkeypatch.setenv("CONTENT_NICHE", "msp")
    monkeypatch.delenv("ARTICLE_TOPIC", raising=False)
    monkeypatch.setattr(publish_article, "_fetch_cmdos_topic",
                        lambda: (_ for _ in ()).throw(AssertionError(
                            "unrelated Growth Command OS queue must not be used")))
    assert publish_article._default_topic() in article_topics.MSP_TOPICS


def test_manual_topic_override_remains_supported(monkeypatch):
    monkeypatch.setenv("CONTENT_NICHE", "msp")
    monkeypatch.setenv("ARTICLE_TOPIC", "Commercial network upgrade planning")
    assert publish_article._default_topic() == "Commercial network upgrade planning"


def test_daily_content_is_scheduled_without_push_publication():
    workflow = (ROOT / ".github/workflows/daily-content.yml").read_text()
    assert "cron: '5 7 * * *'" in workflow
    assert "CONTENT_NICHE: msp" in workflow
    assert workflow.count("CONTENT_NICHE: msp") == 2
    assert "\n  push:" not in workflow
