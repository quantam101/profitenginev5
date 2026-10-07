#!/usr/bin/env python3
"""Stitch the day's generated Shorts into one long-form compilation and append
it to videos_manifest.json so the YouTube upload step publishes it as a regular
video (watch-hours surface — Shorts feed watch time barely counts toward
monetization thresholds, long-form compilations do).

Layout per segment: 1.6s title card (program name) -> the Short itself, then a
2.8s CTA outro card. All inputs are the pipeline's own 1080x1920 h264/aac MP4s,
so segments concat cleanly; cards are rendered to match.

Usage:  python scripts/compile_daily.py            # reads videos_manifest.json
Writes: videos/openmontage/compilation_YYYYMMDD.mp4 + manifest entry
        {"program": "daily-compilation", "kind": "compilation", ...}

Fails soft: any render problem prints a reason and exits 0 without adding a
manifest entry, so the Shorts campaign is never blocked by the bonus upload.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

OUT = Path("videos/openmontage")
WORK = Path("videos/_work/compile")
W, H = 1080, 1920
FONT = next((f for f in (
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
) if Path(f).exists()), "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")


def run(cmd: list[str], timeout: int = 300) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, timeout=timeout)


def esc(t: str) -> str:
    return (t.replace("\\", "\\\\").replace(":", "\\:").replace("'", "’")
             .replace("%", "\\%"))


def card(text: str, sub: str, dur: float, out: Path, bg: str = "0x0f2027") -> bool:
    """Silent title/CTA card on a flat background."""
    txt = esc(text.upper())
    sub_e = esc(sub)
    vf = (f"drawtext=fontfile={FONT}:text='{txt}':fontsize=72:fontcolor=white:"
          f"borderw=4:bordercolor=black@0.6:x=(w-text_w)/2:y=(h-text_h)/2-40,"
          f"drawtext=fontfile={FONT}:text='{sub_e}':fontsize=42:"
          f"fontcolor=0xFFD54F:borderw=3:bordercolor=black@0.7:"
          f"x=(w-text_w)/2:y=(h/2)+60")
    r = run(["ffmpeg", "-y", "-f", "lavfi", "-i", f"color=c={bg}:s={W}x{H}:r=30:d={dur}",
             "-f", "lavfi", "-i", f"anullsrc=r=44100:cl=stereo:d={dur}",
             "-vf", vf, "-t", f"{dur}",
             "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p",
             "-c:a", "aac", "-shortest", str(out)], timeout=120)
    return r.returncode == 0 and out.exists() and out.stat().st_size > 20000


def main() -> int:
    manifest_path = Path("videos_manifest.json")
    if not manifest_path.exists():
        print("no videos_manifest.json — nothing to compile")
        return 0
    videos = [v for v in json.loads(manifest_path.read_text())
              if Path(v.get("path", "")).exists() and v.get("kind") != "compilation"]
    if len(videos) < 2:
        print(f"only {len(videos)} video(s) — compilation needs at least 2")
        return 0

    WORK.mkdir(parents=True, exist_ok=True)
    segments: list[Path] = []

    intro = WORK / "card_intro.mp4"
    if card("Today's top picks", "watch to the end", 1.8, intro):
        segments.append(intro)

    for v in videos:
        title_card = WORK / f"card_{len(segments)}.mp4"
        label = v.get("title", v["program"])[:40]
        if card(label, "", 1.4, title_card, bg="0x232526"):
            segments.append(title_card)
        segments.append(Path(v["path"]))

    outro = WORK / "card_outro.mp4"
    if card("Links in the description", "follow for daily picks", 2.8, outro, bg="0x1a2a6c"):
        segments.append(outro)

    inputs: list[str] = []
    for s in segments:
        inputs += ["-i", str(s)]
    n = len(segments)
    fc = "".join(f"[{i}:v][{i}:a]" for i in range(n)) + f"concat=n={n}:v=1:a=1[v][a]"

    stamp = time.strftime("%Y%m%d")
    out = OUT / f"compilation_{stamp}.mp4"
    r = run(["ffmpeg", "-y", *inputs, "-filter_complex", fc,
             "-map", "[v]", "-map", "[a]",
             "-c:v", "libx264", "-preset", "veryfast", "-crf", "21",
             "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k",
             "-movflags", "+faststart", str(out)], timeout=600)
    if r.returncode != 0 or not out.exists() or out.stat().st_size < 100000:
        print(f"compilation render failed: {r.stderr.decode()[-400:]}")
        return 0

    products = " + ".join(dict.fromkeys(v.get("title", v["program"]).split(" — ")[0]
                                        for v in videos[:4]))
    entry = {
        "program": "daily-compilation",
        "kind": "compilation",
        "title": f"Top Tools & Picks — Daily Roundup ({time.strftime('%b %d, %Y')})",
        "description": (
            "Today's full batch in one watch.\n\n"
            "→ Free playbook — The $0 Content Engine: "
            "https://quantam101.github.io/content/ebooks/zero-dollar-content-engine/"
            "?utm_source=youtube&utm_medium=video&utm_campaign=yt-daily-compilation\n"
            "→ Our tools & kits: https://alreadyhere.gumroad.com"
            "?utm_source=youtube&utm_medium=video&utm_campaign=yt-daily-compilation\n\n"
            "Affiliate disclosure: links may earn a commission at no cost to you."),
        "path": str(out),
        "size_bytes": out.stat().st_size,
        "segments": n,
        "features": products,
    }
    videos.append(entry)
    manifest_path.write_text(json.dumps(videos, indent=2))
    print(f"compilation: {out.name} ({out.stat().st_size // 1024} KB, {n} segments)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
