"""IT/field-service topic rotation and indexing opt-in (retargeted 2026-10-22)."""

from unittest.mock import patch

import pytest

import scripts.publish_article as pa
from scripts.article_topics import TOPICS, is_on_topic, pick_topic, topic_covered

PUBLISHED = [
    "2026-08-03-pbx-vs-hosted-voip-what-you-need-to-know.md",
    "2026-08-12-troubleshoot-slow-business-network.md",
    "2026-08-23-guest-wifi-network-business-security.md",
    "2026-09-27-affiliate-marketing-beginners-guide-2026.md",
]


def test_every_rotation_topic_is_on_topic():
    assert [t for t in TOPICS if not is_on_topic(t)] == []
    assert len(set(TOPICS)) == len(TOPICS)


@pytest.mark.parametrize(
    "topic",
    [
        "Passive Income with Domain Flipping: How to Find Valuable Domains",
        "How to Make $500/Month with AI-Powered Niche Blogs",
        "Affiliate Marketing for Beginners: Complete Guide for 2026",
        "Selling Notion Templates: A Complete Guide to Passive Income in 2026",
    ],
)
def test_old_off_topic_themes_are_rejected(topic):
    assert not is_on_topic(topic)


def test_topic_covered_matches_shortened_published_slugs():
    assert topic_covered("PBX vs Hosted VoIP: What Most IT Vendors Won't Tell You", PUBLISHED)
    assert topic_covered("How to Set Up a Guest Wi-Fi Network That Keeps Your Business Safe", PUBLISHED)
    assert topic_covered("How to Troubleshoot a Slow Business Network Without Calling IT", PUBLISHED)
    assert topic_covered("POS System Installation Checklist for Retail and Restaurant Openings", PUBLISHED) is None


def test_pick_topic_skips_covered_topics():
    names = [f"2026-01-01-{i}.md" for i in range(3)]
    picked = pick_topic(names)
    assert picked in TOPICS
    assert topic_covered(picked, names) is None
    covered = [t.lower().replace(" ", "-") + ".md" for t in TOPICS[:-1]]
    assert pick_topic(covered) == TOPICS[-1]


def test_pick_topic_raises_when_everything_is_covered():
    covered = [t.lower().replace(" ", "-") + ".md" for t in TOPICS]
    with pytest.raises(RuntimeError, match="add new"):
        pick_topic(covered)


def test_default_topic_ignores_off_topic_queue_and_hint(monkeypatch):
    monkeypatch.delenv("ARTICLE_TOPIC", raising=False)
    with patch.object(pa, "_fetch_cmdos_topic", return_value="Affiliate Marketing for Beginners"), patch(
        "runtime.learning_signals.topic_hint", return_value="Passive Income with Stock Photos"
    ):
        topic = pa._default_topic([])
    assert topic in TOPICS


def test_default_topic_uses_on_topic_queue_item(monkeypatch):
    monkeypatch.delenv("ARTICLE_TOPIC", raising=False)
    queued = "How to Mount a Wireless Access Point in a Warehouse"
    with patch.object(pa, "_fetch_cmdos_topic", return_value=queued):
        assert pa._default_topic([]) == queued


def test_manual_override_is_always_honored(monkeypatch):
    monkeypatch.setenv("ARTICLE_TOPIC", "Anything the operator asks for")
    assert pa._default_topic([]) == "Anything the operator asks for"


def _post(title, tags):
    return pa.make_jekyll_post(
        {"title": title, "meta_description": "d", "tags": tags, "body": "## A\n\nbody"},
        "2026-10-22",
    )


def test_on_topic_post_opts_into_indexing():
    md = _post("POS System Installation Checklist", ["pos", "retail"])
    front = md.split("---")[1]
    assert "noindex: false" in front and "sitemap: true" in front


def test_off_topic_post_keeps_site_default_noindex():
    md = _post("Selling Notion Templates for Passive Income", ["notion", "passive-income"])
    assert "noindex" not in md.split("---")[1]


@pytest.mark.parametrize(
    "text",
    [
        "Is It Worth It to Start Affiliate Marketing?",
        "How to Make It Big with Passive Income",
        "making-it-work tags it",
    ],
)
def test_pronoun_it_does_not_count_as_it_topic(text):
    assert not is_on_topic(text)


@pytest.mark.parametrize("text", ["IT Budgeting for Small Business", "it-support", "managed it services"])
def test_it_acronym_and_it_compounds_count(text):
    assert is_on_topic(text)


def test_off_topic_queue_item_with_pronoun_is_skipped(monkeypatch):
    monkeypatch.delenv("ARTICLE_TOPIC", raising=False)
    with patch.object(pa, "_fetch_cmdos_topic", return_value="Is It Worth It to Start Affiliate Marketing?"), patch(
        "runtime.learning_signals.topic_hint", return_value=None
    ):
        assert pa._default_topic([]) in TOPICS
    md = _post("Is It Worth It to Start Affiliate Marketing?", ["affiliate", "it"])
    assert "noindex" not in md.split("---")[1]


def test_short_related_slug_does_not_hide_distinct_topic():
    topic = "How to Plan Network Cabling for a Warehouse or Distribution Center"
    assert topic_covered(topic, ["2026-07-10-network-cabling-installation.md"]) is None


def test_reworded_generated_title_is_indexed_from_selected_topic():
    md = pa.make_jekyll_post(
        {
            "title": "How Much Should Small Businesses Spend on Technology?",
            "meta_description": "d",
            "tags": ["business", "budget", "technology"],
            "body": "## A\n\nbody",
        },
        "2026-10-22",
        "IT Budgeting for Small Business: How Much to Spend on Technology",
    )
    assert "noindex: false" in md.split("---")[1]
