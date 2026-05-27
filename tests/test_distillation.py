"""
Tests for the Data Distillation pipeline:
  distillation.py · token_budget.py · structured_output.py
"""
from __future__ import annotations

import pytest


# ── distillation.py ───────────────────────────────────────────────────────────

class TestDistillation:
    def test_noise_strip_removes_html(self):
        from runtime.distillation import noise_strip
        html = "<p>Hello <b>world</b> &amp; friends</p>"
        out = noise_strip(html)
        assert "<p>" not in out
        assert "&amp;" not in out
        assert "Hello" in out

    def test_noise_strip_removes_markdown_fences(self):
        from runtime.distillation import noise_strip
        # noise_strip removes the fence markers (```) but keeps the content
        # inside (which may be relevant to the objective).
        text = "Intro\n```python\ncode here\n```\nOutro"
        out = noise_strip(text)
        assert "```" not in out      # fence markers stripped
        assert "Intro" in out        # surrounding text kept
        assert "Outro" in out

    def test_dedup_sentences_removes_near_duplicates(self):
        from runtime.distillation import dedup_sentences
        # Sentence 2 is a near-duplicate of sentence 1 (Jaccard > 0.5)
        text = (
            "AI tools help small businesses save time.\n"
            "AI tools assist small businesses to save time efficiently.\n"
            "Machine learning is transforming industries worldwide."
        )
        out = dedup_sentences(text, threshold=0.5)
        # The near-dup should be dropped; distinct third sentence should remain
        assert "Machine learning" in out
        # Both originals should not both be present — one should be deduplicated
        # (The first one is kept, the second is dropped)
        first_in  = "help small businesses save time" in out
        second_in = "assist small businesses to save time efficiently" in out
        assert first_in
        assert not second_in

    def test_dedup_sentences_keeps_distinct_sentences(self):
        from runtime.distillation import dedup_sentences
        # dedup_sentences joins kept sentences with spaces; count via content
        text = (
            "Python is a programming language.\n"
            "The stock market rose sharply today.\n"
            "Quantum computing promises exponential speedup."
        )
        out = dedup_sentences(text)
        # All three are distinct — all should survive dedup
        assert "Python" in out
        assert "stock market" in out
        assert "Quantum" in out

    def test_budget_truncate_respects_limit(self):
        from runtime.distillation import budget_truncate
        long_text = "Word " * 500          # 2500 chars
        out = budget_truncate(long_text, char_budget=200)
        assert len(out) <= 210             # slight over-run for word boundary is ok

    def test_distill_reduces_length(self):
        from runtime.distillation import distill
        # Use newlines between paragraphs so boilerplate line-filter works correctly
        html_content = (
            "<html><body>\n"
            "<p>Cookie policy: we use cookies. Privacy policy: see our site.</p>\n"
            "<p>Artificial intelligence is changing affiliate marketing strategies.</p>\n"
            "<p>Cookie policy: we use cookies. Privacy policy: see our site.</p>\n"
            "<p>The best AI writing tools can help bloggers earn passive income.</p>\n"
            "</body></html>"
        )
        out = distill(html_content, objective="affiliate marketing AI tools", char_budget=500)
        assert len(out) < len(html_content)
        assert "Artificial intelligence" in out or "AI writing tools" in out

    def test_estimate_tokens_reasonable(self):
        from runtime.distillation import estimate_tokens
        text = "Hello world"  # 11 chars → ~2-3 tokens
        assert 1 <= estimate_tokens(text) <= 5

        long_text = "x" * 4000  # 4000 chars → ~1000 tokens
        assert estimate_tokens(long_text) == 1000

    def test_distill_prompt_compresses_both(self):
        from runtime.distillation import distill_prompt
        system = "You are a helpful assistant. " * 100
        user   = "Tell me about AI. " * 200
        s2, u2, metrics = distill_prompt(system, user, objective="AI")
        assert len(s2) <= len(system)
        assert len(u2) <= len(user)
        assert "system_before" in metrics
        assert "total_before_tokens" in metrics
        assert metrics["reduction_pct"] >= 0


# ── token_budget.py ───────────────────────────────────────────────────────────

class TestTokenBudget:
    def test_budget_for_known_tiers(self):
        from runtime.token_budget import budget_for
        for tier in ("ollama", "groq", "gemini", "claude_api"):
            b = budget_for(tier)
            assert b.max_input > 0
            assert b.max_output > 0

    def test_budget_for_unknown_tier_returns_groq(self):
        from runtime.token_budget import budget_for
        b = budget_for("nonexistent_tier")
        groq = budget_for("groq")
        assert b.max_input == groq.max_input

    def test_clamp_max_tokens_caps_to_tier(self):
        from runtime.token_budget import clamp_max_tokens
        # Ollama allows 512 output tokens max
        assert clamp_max_tokens(9999, "ollama") == 512
        # Claude allows 4096 max
        assert clamp_max_tokens(9999, "claude_api") == 4096
        # Smaller than tier limit — unchanged
        assert clamp_max_tokens(100, "ollama") == 100

    def test_apply_input_budget_truncates_overlong_input(self):
        from runtime.token_budget import apply_input_budget, budget_for
        tier = "ollama"
        budget = budget_for(tier)
        # Build text exceeding the tier's char limit
        big_system = "S" * (budget.max_input_chars + 500)
        big_user   = "U" * (budget.max_input_chars + 500)
        s, u, s_tok, u_tok = apply_input_budget(big_system, big_user, tier)
        assert len(s) + len(u) <= budget.max_input_chars + 10  # +10 tolerance

    def test_apply_input_budget_leaves_short_input_intact(self):
        from runtime.token_budget import apply_input_budget
        s, u, s_tok, u_tok = apply_input_budget("Short system", "Short user", "groq")
        assert s == "Short system"
        assert u == "Short user"

    def test_audit_budget_within_budget_flag(self):
        from runtime.token_budget import audit_budget
        report = audit_budget("Hello", "World", "claude_api", 1024)
        assert report.within_budget is True

    def test_audit_budget_over_budget_detection(self):
        from runtime.token_budget import audit_budget, budget_for
        tier = "ollama"
        budget = budget_for(tier)
        big = "X" * (budget.max_input_chars * 3)
        report = audit_budget(big, big, tier, 9999)
        assert report.within_budget is False


# ── structured_output.py ──────────────────────────────────────────────────────

class TestStructuredOutput:
    def test_extract_json_valid_object(self):
        from runtime.structured_output import extract_json
        r = extract_json('{"title": "Hello", "body": "World"}', required_keys=["title", "body"])
        assert r.ok
        assert r.data["title"] == "Hello"

    def test_extract_json_with_markdown_fence(self):
        from runtime.structured_output import extract_json
        text = '```json\n{"key": "value"}\n```'
        r = extract_json(text, required_keys=["key"])
        assert r.ok
        assert r.data["key"] == "value"

    def test_extract_json_missing_required_key_uses_fallback(self):
        from runtime.structured_output import extract_json
        r = extract_json('{"only_key": 1}', required_keys=["title"], fallback={"title": "default"})
        assert not r.ok
        assert r.fallback["title"] == "default"

    def test_extract_json_array(self):
        from runtime.structured_output import extract_json
        r = extract_json('[{"id": 1}, {"id": 2}]', allow_array=True)
        assert r.ok
        assert isinstance(r.data, list)
        assert len(r.data) == 2

    def test_extract_json_invalid_json_uses_fallback(self):
        from runtime.structured_output import extract_json
        r = extract_json("Not JSON at all", required_keys=["x"], fallback={"x": "fb"})
        assert not r.ok
        assert r.fallback["x"] == "fb"

    def test_extract_json_preamble_ignored(self):
        from runtime.structured_output import extract_json
        text = 'Here is the JSON you requested:\n{"answer": 42}'
        r = extract_json(text, required_keys=["answer"])
        assert r.ok
        assert r.data["answer"] == 42

    def test_extract_key_value(self):
        from runtime.structured_output import extract_key_value
        text = "Status: active\nName: Alice"
        assert extract_key_value(text, "Status", "unknown") == "active"
        assert extract_key_value(text, "Name", "unknown") == "Alice"
        assert extract_key_value(text, "Missing", "default") == "default"

    def test_extract_list_bullet_points(self):
        from runtime.structured_output import extract_list
        text = "- item one\n- item two\n- item three"
        items = extract_list(text)
        assert len(items) == 3
        assert items[0] == "item one"

    def test_output_constraint_json_appended(self):
        from runtime.structured_output import OUTPUT_CONSTRAINT_JSON
        system = "You are a writer." + OUTPUT_CONSTRAINT_JSON
        assert "JSON" in system
        assert "{" in system or "json" in system.lower()

    def test_output_constraint_concise_appended(self):
        from runtime.structured_output import OUTPUT_CONSTRAINT_CONCISE
        assert "concise" in OUTPUT_CONSTRAINT_CONCISE.lower() or "filler" in OUTPUT_CONSTRAINT_CONCISE.lower()


# ── complexity_scorer (distillation integration) ──────────────────────────────

class TestComplexityScorerDistillation:
    def test_simple_objective_is_low_complexity(self):
        from runtime.complexity_scorer import ComplexityScorer
        scorer = ComplexityScorer()
        r = scorer.score("Write a short greeting")
        assert r.score < 0.30, f"Expected low complexity, got {r.score}"

    def test_risk_terms_raise_score(self):
        from runtime.complexity_scorer import ComplexityScorer
        scorer = ComplexityScorer()
        r = scorer.score("deploy payment token password secret")
        assert r.score >= 0.50, f"Expected elevated score for risk terms, got {r.score}"
        assert len(r.risk_terms) >= 3

    def test_large_context_raises_token_len_component(self):
        from runtime.complexity_scorer import ComplexityScorer
        scorer = ComplexityScorer()
        # ~1100 token context (4400 chars)
        large_ctx = "word " * 880
        r = scorer.score("Summarise this", large_ctx)
        assert r.token_est >= 1024
        assert r.score >= 0.10, "Large context should add token_len component"

    def test_score_never_exceeds_1(self):
        from runtime.complexity_scorer import ComplexityScorer
        scorer = ComplexityScorer()
        extreme = "deploy payment stripe token password secret api key bank production merge delete execute admin" * 10
        r = scorer.score(extreme, "x" * 10_000)
        assert r.score <= 1.0

    def test_risk_terms_list_populated(self):
        from runtime.complexity_scorer import ComplexityScorer
        scorer = ComplexityScorer()
        r = scorer.score("password secret token")
        assert "password" in r.risk_terms
        assert "secret" in r.risk_terms
        assert "token" in r.risk_terms


# ── vector_cache TTL / dedup (new fields) ─────────────────────────────────────

class TestVectorCacheTTL:
    def test_stats_returns_expected_keys(self, tmp_path, monkeypatch):
        monkeypatch.setenv("GMAOS_VECTOR_CACHE", str(tmp_path / "cache.sqlite3"))
        monkeypatch.setenv("GMAOS_EMBEDDING_DIM", "4")
        from runtime.vector_cache import VectorCache
        cache = VectorCache()
        stats = cache.stats()
        assert "total_records" in stats
        assert "ttl_days" in stats

    def test_prune_expired_returns_int(self, tmp_path, monkeypatch):
        monkeypatch.setenv("GMAOS_VECTOR_CACHE", str(tmp_path / "cache.sqlite3"))
        monkeypatch.setenv("GMAOS_EMBEDDING_DIM", "4")
        from runtime.vector_cache import VectorCache
        cache = VectorCache()
        pruned = cache.prune_expired()
        assert isinstance(pruned, int)
        assert pruned == 0  # nothing to prune on fresh cache

    def test_commit_and_search_basic(self, tmp_path, monkeypatch):
        import uuid
        monkeypatch.setenv("GMAOS_VECTOR_CACHE", str(tmp_path / "cache.sqlite3"))
        monkeypatch.setenv("GMAOS_EMBEDDING_DIM", "4")
        from runtime.vector_cache import VectorCache
        cache = VectorCache()
        vec = [0.1, 0.2, 0.3, 0.4]
        record_id = str(uuid.uuid4())
        result = cache.commit(record_id, vec, "test output", namespace="test", verified=True)
        # commit() returns bool: True = committed, False = skipped (dedup)
        assert isinstance(result, bool)

    def test_dedup_skips_identical_output(self, tmp_path, monkeypatch):
        import uuid
        monkeypatch.setenv("GMAOS_VECTOR_CACHE", str(tmp_path / "cache.sqlite3"))
        monkeypatch.setenv("GMAOS_EMBEDDING_DIM", "4")
        monkeypatch.setenv("GMAOS_OUTPUT_DEDUP_FLOOR", "0.90")
        from runtime.vector_cache import VectorCache
        cache = VectorCache()
        output = "This is a unique test output string for dedup testing."
        # First commit must succeed
        r1 = cache.commit(str(uuid.uuid4()), [0.1, 0.2, 0.3, 0.4], output,
                          namespace="dedup_test", verified=True)
        assert r1 is True
        # Second commit with same output — should be skipped by dedup
        r2 = cache.commit(str(uuid.uuid4()), [0.5, 0.6, 0.7, 0.8], output,
                          namespace="dedup_test", verified=True)
        assert r2 is False  # dedup blocked it
