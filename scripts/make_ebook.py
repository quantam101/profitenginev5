#!/usr/bin/env python3
"""Ebook lead-magnet builder. Takes an ebook in Markdown, wraps it in a clean
self-contained HTML page, and (optionally) publishes it to the public content
repo so GitHub Pages serves it — a free hosted lead magnet.

Usage:
  python scripts/make_ebook.py content/ebooks/my-book.md            # build HTML next to it
  python scripts/make_ebook.py content/ebooks/my-book.md --publish  # + push to quantam101/content

Published URL: https://quantam101.github.io/content/ebooks/<slug>/
Requires `gh` CLI authenticated (or GH_TOKEN) for --publish.
"""
from __future__ import annotations

import base64
import html
import json
import re
import subprocess
import sys
from pathlib import Path

CONTENT_REPO = "quantam101/content"
PAGES_BASE = "https://quantam101.github.io/content"

_CSS = """
:root{color-scheme:light dark}
body{max-width:680px;margin:0 auto;padding:2rem 1.2rem 4rem;
  font:17px/1.65 Georgia,'Times New Roman',serif;color:#1a1a1a;background:#fdfcf8}
h1{font-size:2rem;line-height:1.2;margin:1rem 0 .3rem}
h2{font-size:1.35rem;margin:2.2rem 0 .6rem;border-bottom:2px solid #e8e2d4;padding-bottom:.3rem}
h3{font-size:1.05rem;color:#555;font-weight:normal;font-style:italic;margin:.2rem 0 1rem}
em{color:#555}
li{margin:.35rem 0}
hr{border:none;border-top:1px solid #e8e2d4;margin:2rem 0}
strong{color:#000}
code{font-family:ui-monospace,Consolas,monospace;font-size:.88em;background:#f0ece1;
  padding:.1em .35em;border-radius:4px}
@media (prefers-color-scheme:dark){
  body{color:#e8e6e0;background:#181614}
  h3,em{color:#aaa} strong{color:#fff}
  h2,hr{border-color:#3a362e} code{background:#2a2721}}
"""


def md_to_html(md: str) -> str:
    """Tiny dependency-free Markdown→HTML for the subset ebooks use."""
    out, in_list = [], False
    for line in md.split("\n"):
        s = line.rstrip()
        def inline(t: str) -> str:
            t = html.escape(t)
            t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
            t = re.sub(r"\*(.+?)\*", r"<em>\1</em>", t)
            t = re.sub(r"`(.+?)`", r"<code>\1</code>", t)
            return t
        m = re.match(r"^(#{1,3}) (.*)", s)
        bullet = re.match(r"^[-*] (.*)", s)
        num = re.match(r"^\d+\. (.*)", s)
        if in_list and not (bullet or num):
            out.append("</ul>")
            in_list = False
        if m:
            level = len(m.group(1))
            out.append(f"<h{level}>{inline(m.group(2))}</h{level}>")
        elif s == "---":
            out.append("<hr>")
        elif bullet or num:
            if not in_list:
                out.append("<ul>")
                in_list = True
            out.append(f"<li>{inline((bullet or num).group(1))}</li>")
        elif s:
            out.append(f"<p>{inline(s)}</p>")
    if in_list:
        out.append("</ul>")
    return "\n".join(out)


def build(md_path: Path) -> Path:
    md = md_path.read_text(encoding="utf-8")
    title = next((ln[2:] for ln in md.split("\n") if ln.startswith("# ")), md_path.stem)
    page = (f"<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">"
            f"<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
            f"<title>{html.escape(title)}</title><style>{_CSS}</style></head>"
            f"<body>{md_to_html(md)}</body></html>")
    out = md_path.with_suffix(".html")
    out.write_text(page, encoding="utf-8")
    print(f"built {out}")
    return out


def publish(html_path: Path, slug: str) -> None:
    dest = f"ebooks/{slug}/index.html"
    b64 = base64.b64encode(html_path.read_bytes()).decode()
    # need the current sha if the file already exists (update vs create)
    probe = subprocess.run(["gh", "api", f"repos/{CONTENT_REPO}/contents/{dest}"],
                           capture_output=True, text=True)
    args = ["gh", "api", "-X", "PUT", f"repos/{CONTENT_REPO}/contents/{dest}",
            "-f", f"message=ebook: {slug}", "-f", f"content={b64}"]
    if probe.returncode == 0:
        args += ["-f", f"sha={json.loads(probe.stdout)['sha']}"]
    r = subprocess.run(args, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"publish failed: {r.stderr[:300]}")
        sys.exit(1)
    print(f"published: {PAGES_BASE}/ebooks/{slug}/")


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    md_path = Path(sys.argv[1])
    if not md_path.exists():
        print(f"not found: {md_path}")
        sys.exit(1)
    out = build(md_path)
    if "--publish" in sys.argv:
        publish(out, md_path.stem)


if __name__ == "__main__":
    main()
