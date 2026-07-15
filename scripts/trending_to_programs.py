#!/usr/bin/env python3
"""Turn trending_topics.json (from find_trending.py) into program specs that
generate_shorts.py can render. The AI chain designs each program; a template
fallback keeps the pipeline unbreakable with zero keys configured.

We recreate TOPICS with our own scripts and licensed B-roll — never the videos.

Usage:  python scripts/trending_to_programs.py          # top 3 topics
        python scripts/trending_to_programs.py 5        # top 5

Output: trending_programs.json (same schema as generate_shorts.PROGRAMS)
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from generate_shorts import ai_complete  # noqa: E402

_PROMPT = (
    'A short video titled "{title}" (niche: {query}) is getting {vpd} views/day on YouTube.\n'
    "Design OUR OWN original 20-second faceless short on the same TOPIC (do not copy the video).\n"
    "Return STRICT JSON only (no markdown fences) with keys:\n"
    'product: 2-4 word topic name; angle: what the video teaches, 5-10 words;\n'
    'keywords: 3-5 words for stock-footage search; cta: short call to action;\n'
    'pain: viewer problem as a gerund phrase (e.g. "guessing at SEO");\n'
    "benefits: array of 4 concrete, specific one-line takeaways."
)


def _slug(t: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", t.lower()).strip("_")[:40] or "topic"


def _fallback(v: dict) -> dict:
    # trim the title at the first separator; that's usually the topic
    product = re.split(r"[|\-–—:#(]", v["title"])[0].strip() or v["query"]
    if len(product) > 48:  # cut at a word boundary, not mid-word
        product = product[:48].rsplit(" ", 1)[0]
    angle = v["query"].replace("shorts", "").strip()
    return {
        "product": product, "angle": angle,
        "keywords": angle + " computer office",
        "cta": "Follow for more",
        "pain": "doing this the hard way",
        "benefits": [
            f"breaks down {product} in plain English",
            "shows the exact steps most people skip",
            "works even if you're starting from zero",
            "takes minutes to apply, not weeks",
        ],
    }


def to_program(v: dict) -> dict:
    prog = None
    raw = ai_complete(_PROMPT.format(title=v["title"], query=v["query"],
                                     vpd=v.get("views_per_day") or "many"),
                      min_len=60, max_len=2000)
    if raw:
        try:
            m = re.search(r"\{.*\}", raw, re.S)
            cand = json.loads(m.group(0) if m else raw)
            if all(k in cand for k in ("product", "angle", "keywords", "cta", "pain", "benefits")):
                prog = cand
        except Exception:
            print("   ! AI returned unparseable JSON — template fallback")
    if prog is None:
        prog = _fallback(v)
    prog["name"] = _slug(prog["product"])
    prog["source"] = {"title": v["title"], "url": v["url"],
                      "views_per_day": v.get("views_per_day")}
    return prog


def main() -> None:
    top_n = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 3
    src = Path("trending_topics.json")
    if not src.exists():
        print("no trending_topics.json — run find_trending.py first")
        sys.exit(1)
    topics = json.loads(src.read_text())[:top_n]
    programs, seen = [], set()
    for v in topics:
        p = to_program(v)
        if p["name"] in seen:
            continue
        seen.add(p["name"])
        print(f"* {p['product']}  ({p['name']})")
        programs.append(p)
    Path("trending_programs.json").write_text(json.dumps(programs, indent=2))
    print(f"\nok {len(programs)} programs -> trending_programs.json")
    if not programs:
        sys.exit(1)


if __name__ == "__main__":
    main()
