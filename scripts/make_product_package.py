#!/usr/bin/env python3
"""Gumroad upload-kit builder. Assembles everything the one manual publish
step needs into dist/gumroad/<slug>/ — PDF, 1280x720 cover, 600x600
thumbnail, listing description, product.json — and REFUSES to complete if
any piece is missing (validation gate, per the production-safe workflow).

Cover/thumbnail are drawn with Pillow (pure Python, deterministic — Edge's
--screenshot mode proved flaky while a desktop Edge session is running).

Usage: python scripts/make_product_package.py            # the Blueprint
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

PRODUCT = {
    "title": "The $0 Content Engine: Complete Blueprint",
    "price": 30,
    "currency": "USD",
    "slug": "content-engine",
    "summary": ("The complete build manual for a fully automated short-form "
                "content business — every script, prompt, command, and "
                "workflow, running in production. $0 in tooling."),
    "call_to_action": "Get the Complete Blueprint",
    "pdf": "content/ebooks/content-engine-blueprint.pdf",
    "tags": ["content automation", "youtube shorts", "faceless channel",
             "passive income", "python", "no-code"],
    "sales_page": "https://quantam101.github.io/content/ebooks/blueprint/",
}

DESCRIPTION = """\
Stop renting a $300/month "automation stack" and build the real thing in one weekend — for $0 in tooling.

This is the complete build manual for the content engine we run in production at Already Here LLC. Every week it mines what's already winning on YouTube, writes 20-second scripts, renders studio-grade vertical video (neural voiceover, word-synced captions, licensed B-roll), and posts to YouTube, Instagram, and Facebook before we wake up.

WHAT YOU GET (9 parts + appendix, PDF, lifetime updates):
• The trend-mining code and the views-per-day scoring formula, ready to paste
• All 5 script formats with fill-in-the-blank hooks + the exact LLM prompt chain (free-tier fallback order included)
• The full render pipeline: every ffmpeg filter, the "CapCut look" caption technique, the edge-tts settings that don't sound robotic
• Publishing setup for YouTube, Instagram Reels, and Facebook — including the two Meta token gotchas that cost us days of debugging
• The complete GitHub Actions workflows with our real cron schedule
• The repost engine that turns one good video into 4–6 impression cycles
• The money layer: affiliate injection, lead magnet funnel, product ladder — FTC compliance baked in
• A 30-day launch calendar and a troubleshooting table of every failure we've actually hit

WHO IT'S FOR: solo founders, side-hustlers, and small agencies who can copy-paste and follow instructions. If you can run `pip install`, you can run this engine. No face, no voice recording, no editor.

COMPLIANT BY DESIGN: you recreate topics with your own scripts and licensed footage — never re-uploading anyone's content. That one rule is why this system survives while "faceless channel" hacks get accounts banned.

Questions? dispatch@alreadyherellc.com — a human answers. See the engine's output at @alreadyherellc.
"""

def _font(bold: bool, italic: bool, size: int):
    from PIL import ImageFont
    names = (["georgiab.ttf", "arialbd.ttf"] if bold else
             ["georgiai.ttf", "ariali.ttf"] if italic else
             ["georgia.ttf", "arial.ttf"])
    for n in names:
        try:
            return ImageFont.truetype(rf"C:\Windows\Fonts\{n}", size)
        except OSError:
            continue
    return ImageFont.load_default(size)


def render_image(out: Path, w: int, h: int) -> bool:
    """Draw the cover at w x h: dark green gradient, title with $0 accent."""
    from PIL import Image, ImageDraw
    top, bottom, accent = (13, 31, 22), (26, 127, 78), (127, 212, 168)
    img = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(img)
    for y in range(h):  # vertical gradient
        t = y / h
        d.line([(0, y), (w, y)], fill=tuple(
            int(a + (b - a) * t * 0.85) for a, b in zip(top, bottom)))

    s = w / 1280  # scale everything from the 1280-wide design
    def center(text, y, font, fill):
        bb = d.textbbox((0, 0), text, font=font)
        d.text(((w - bb[2] + bb[0]) / 2, y), text, font=font, fill=fill)
        return bb[3] - bb[1]

    y = h * (0.30 if w != h else 0.26)
    center("C O M P L E T E   B L U E P R I N T", y - 52 * s,
           _font(False, False, int(24 * s)), accent)
    # title with accent-colored $0: measure segments to center the whole line
    tf = _font(True, False, int(84 * s))
    segs = [("The ", (253, 252, 248)), ("$0", accent),
            (" Content Engine", (253, 252, 248))]
    widths = [d.textbbox((0, 0), t, font=tf)[2] for t, _ in segs]
    x = (w - sum(widths)) / 2
    for (t, fill), tw in zip(segs, widths):
        d.text((x, y), t, font=tf, fill=fill)
        x += tw
    sub = ["Every script, prompt, command & workflow behind",
           "a fully automated short-form content business"]
    sy = y + 130 * s
    for line in sub:
        sy += 10 * s + center(line, sy, _font(False, True, int(28 * s)),
                              (201, 216, 207))
    center("A L R E A D Y   H E R E   L L C", h - 70 * s,
           _font(False, False, int(20 * s)), (143, 174, 156))

    img.save(out, "PNG")
    ok = out.exists() and out.stat().st_size > 8_000
    print(f"{'ok' if ok else 'FAILED'} {out.name} ({w}x{h})")
    return ok


def main() -> None:
    pdf = Path(PRODUCT["pdf"])
    if not pdf.exists():
        print(f"missing PDF: {pdf} — run make_ebook.py --pdf first")
        sys.exit(1)

    dest = Path("dist/gumroad") / PRODUCT["slug"]
    dest.mkdir(parents=True, exist_ok=True)

    shutil.copy2(pdf, dest / f"{PRODUCT['slug']}-ebook.pdf")
    (dest / "description.txt").write_text(DESCRIPTION, encoding="utf-8")
    (dest / "product.json").write_text(json.dumps({
        **{k: PRODUCT[k] for k in ("title", "price", "currency", "slug",
                                   "summary", "call_to_action", "tags",
                                   "sales_page")},
        "files": [f"{PRODUCT['slug']}-ebook.pdf"],
        "cover": "gumroad-cover.png",
        "thumbnail": "gumroad-thumbnail.png",
    }, indent=2), encoding="utf-8")

    covers_ok = (render_image(dest / "gumroad-cover.png", 1280, 720)
                 and render_image(dest / "gumroad-thumbnail.png", 600, 600))

    required = [f"{PRODUCT['slug']}-ebook.pdf", "gumroad-cover.png",
                "gumroad-thumbnail.png", "description.txt", "product.json"]
    missing = [f for f in required if not (dest / f).exists()]
    if missing or not covers_ok:
        print(f"FAILED_VALIDATION — missing: {missing or 'cover render'}")
        sys.exit(1)

    print(f"\npackage complete: {dest}")
    for f in sorted(dest.iterdir()):
        print(f"  {f.name} ({f.stat().st_size // 1024} KB)")
    print("\nManual step (the only one): gumroad.com -> New product -> "
          f"Digital product -> title/price/summary/description from "
          f"product.json + description.txt -> upload PDF under Content -> "
          f"cover images -> URL slug '{PRODUCT['slug']}' -> Publish.\n"
          "Then run: python scripts/set_product_url.py <live product URL>")


if __name__ == "__main__":
    main()
