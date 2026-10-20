from scripts.seo_content_quality import find_duplicate_post, validate_article_quality


def article(body: str, title: str = "Best Free SEO Tools in 2026"):
    return {
        "title": title,
        "meta_description": "A practical, evidence-aware guide to current free SEO tools, limits, workflows, and search optimization techniques for bloggers and site owners.",
        "body": body,
    }


def strong_body(extra: str = "") -> str:
    sections = []
    for i in range(1, 7):
        sections.append(
            f"## Section {i}\n\n"
            + (
                "Useful evidence-based workflow guidance with concrete steps, trade-offs, examples, "
                "verification notes, and implementation details. " * 34
            )
        )
    return (
        "\n\n".join(sections)
        + "\n\n[Google Search Central](https://developers.google.com/search/docs/essentials)"
        + "\n\n[Search Console](https://support.google.com/webmasters/answer/7576553)"
        + "\n\n## Sources\n\nPrimary documentation is linked above.\n"
        + extra
    )


def test_accepts_structurally_strong_current_roundup():
    result = validate_article_quality(article(strong_body()))
    assert result.ok, result.errors
    assert result.word_count >= 1000
    assert result.h2_count >= 5
    assert result.external_link_count >= 2


def test_rejects_obsolete_faq_schema_claim():
    result = validate_article_quality(
        article(
            strong_body(
                "\nFAQ schema helps Google surface your answers in People Also Ask rich results."
            )
        )
    )
    assert not result.ok
    assert any("FAQ schema" in error for error in result.errors)


def test_rejects_tinypng_500_monthly_web_claim():
    result = validate_article_quality(
        article(strong_body("\nTinyPNG offers 500 free image compressions per month."))
    )
    assert not result.ok
    assert any("TinyPNG" in error for error in result.errors)


def test_rejects_keyword_rich_alt_text_language():
    result = validate_article_quality(
        article(strong_body("\nAlways use keyword-rich alt text on every image."))
    )
    assert not result.ok
    assert any("alt text" in error for error in result.errors)


def test_current_roundup_requires_reference_links():
    body = (
        strong_body()
        .replace(
            "[Google Search Central](https://developers.google.com/search/docs/essentials)",
            "Google Search Central",
        )
        .replace(
            "[Search Console](https://support.google.com/webmasters/answer/7576553)",
            "Search Console",
        )
    )
    result = validate_article_quality(article(body))
    assert not result.ok
    assert any("reference links" in error for error in result.errors)


def test_rejects_table_flattened_onto_one_line():
    flattened = (
        "\n| Pitfall | What Happens | How to Mitigate | |———|————–|—————–| "
        "| Hidden Costs | Credit card charged after limit | Set budget alerts |"
    )
    result = validate_article_quality(article(strong_body(flattened)))
    assert not result.ok
    assert any("flattened onto a single line" in error for error in result.errors)


def test_accepts_normal_multiline_table():
    proper = (
        "\n\n| Pitfall | What Happens | How to Mitigate |\n"
        "| --- | --- | --- |\n"
        "| Hidden Costs | Credit card charged | Set budget alerts |\n"
    )
    result = validate_article_quality(article(strong_body(proper)))
    assert result.ok, result.errors


# ── Technical accuracy gate (added 2026-10-19) ────────────────────────────────



def tutorial_body(extra: str = "", sources: bool = True) -> str:
    sections = []
    for i in range(1, 7):
        sections.append(
            f"## Step {i}\n\n"
            + ("Concrete, verified implementation guidance with commands and trade-offs. " * 30)
        )
    code = "\n\n```bash\nnpx wrangler deploy\n```\n\n```js\nexport default {}\n```\n"
    refs = (
        "\n\n## Sources\n\n"
        "- [Workers limits](https://developers.cloudflare.com/workers/platform/limits/)\n"
        "- [Workers pricing](https://developers.cloudflare.com/workers/platform/pricing/)\n"
        if sources
        else "\n\n## Sources\n\nCloudflare Workers documentation\nCloudflare Workers pricing page\n"
    )
    return "\n\n".join(sections) + code + extra + refs


def tutorial(body: str):
    return article(body, title="Deploy an API on Cloudflare Workers")


def test_accepts_current_cloudflare_tutorial():
    result = validate_article_quality(tutorial(tutorial_body()))
    assert result.ok, result.errors


def test_rejects_retired_wrangler_commands():
    for snippet in (
        "npm install -g @cloudflare/wrangler",
        "Then run wrangler publish to ship it.",
        "Start with wrangler generate joke-api.",
    ):
        result = validate_article_quality(tutorial(tutorial_body(f"\n\n{snippet}\n")))
        assert not result.ok, snippet
        assert any("wrangler" in e.lower() for e in result.errors), result.errors


def test_rejects_inverted_workers_cpu_limits():
    text = (
        "\n\nOn Cloudflare Workers the free tier allows up to 50 ms of CPU per request. "
        "The paid plan allows up to 30 ms per request.\n"
    )
    errors = validate_article_quality(tutorial(tutorial_body(text))).errors
    assert any("10 ms" in e for e in errors), errors
    assert any("30 seconds" in e for e in errors), errors


def test_rejects_discontinued_and_wrong_platform_claims():
    for snippet, needle in (
        ("Vercel KV (beta) gives you a built-in store.", "Vercel KV"),
        ("Cloudflare Workers paid plans can reduce cold starts by keeping instances warm.", "isolates"),
        ("You get a 403 Forbidden when reading a secret that is missing.", "undefined"),
    ):
        errors = validate_article_quality(tutorial(tutorial_body(f"\n\n{snippet}\n"))).errors
        assert any(needle in e for e in errors), (snippet, errors)


def test_code_tutorial_requires_linked_sources():
    errors = validate_article_quality(tutorial(tutorial_body(sources=False))).errors
    assert any("Sources section" in e for e in errors), errors


def test_prose_article_without_code_does_not_need_sources_section():
    body = "\n\n".join(
        f"## Part {i}\n\n" + ("Field service scheduling guidance for dispatch teams. " * 40)
        for i in range(1, 7)
    )
    result = validate_article_quality(article(body, title="Scheduling Field Technicians Efficiently"))
    assert result.ok, result.errors


def test_duplicate_guard_matches_known_repeats():
    existing = [
        "2026-10-16-cloudflare-workers-build-deploy-apis-no-cost.md",
        "2026-06-15-setup-free-postgres-database-supabase.md",
        "2026-10-14-best-free-apis-side-projects.md",
    ]
    assert find_duplicate_post("cloudflare-workers-build-and-deploy-apis-at-no-cost", existing)
    assert find_duplicate_post("cloudflare-workers-build-deploy-apis-free", existing)
    assert find_duplicate_post("set-up-free-postgres-database-supabase", existing)
    assert find_duplicate_post("best-free-apis-for-side-projects", existing)


def test_duplicate_guard_allows_distinct_topics():
    existing = ["2026-10-16-cloudflare-workers-build-deploy-apis-no-cost.md"]
    assert find_duplicate_post("cloudflare-r2-offsite-backups", existing) is None
    assert find_duplicate_post("pos-terminal-install-checklist", existing) is None
    assert find_duplicate_post("", existing) is None


def test_deprecation_warning_sentences_are_not_stale_claims():
    for snippet in (
        "Never run wrangler publish; it was replaced by wrangler deploy.",
        "Older tutorials use wrangler generate, which is retired.",
        "Vercel KV was discontinued; use a Marketplace integration instead.",
    ):
        result = validate_article_quality(tutorial(tutorial_body(f"\n\n{snippet}\n")))
        assert result.ok, (snippet, result.errors)


def test_retired_command_in_code_block_still_fails_next_to_a_warning():
    text = "\n\nThe old command is retired.\n\n```bash\nnpx wrangler publish\n```\n"
    errors = validate_article_quality(tutorial(tutorial_body(text))).errors
    assert any("wrangler" in e.lower() for e in errors), errors


def test_numeric_limit_claims_are_never_exempt():
    text = "\n\nUnlike the retired plan, Cloudflare Workers free tier allows 50 ms of CPU per request.\n"
    errors = validate_article_quality(tutorial(tutorial_body(text))).errors
    assert any("10 ms" in e for e in errors), errors
