from scripts.seo_content_quality import validate_article_quality


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
