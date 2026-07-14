#!/usr/bin/env python3
"""Free, CI-reliable YouTube Shorts engine that produces videos built to sell.

Pipeline (all free, runs on a CPU GitHub Actions runner):
  1. Sales script      — Groq (GROQ_API_KEY) with a strong template fallback
  2. Voiceover         — edge-tts neural voice (no key), with word timings
  3. Captions          — word-timed, burned-in ASS (big, bold — Shorts retention)
  4. Motion visuals    — real Pexels B-roll if PEXELS_API_KEY, else animated gradient + Ken Burns
  5. Music bed         — assets/music/*.mp3 if present, else a soft procedural pad, ducked under VO
  6. Compose           — vertical 1080x1920 H.264 MP4

Writes videos_manifest.json consumed by the upload step. Every stage degrades
gracefully so a missing key or API never fails the whole run.
"""
from __future__ import annotations

import asyncio
import json
import os
import random
import re
import shutil
import subprocess
import sys
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

W, H = 1080, 1920
OUT = Path("videos/openmontage")
TMP = Path("videos/_work")
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
VOICES = ["en-US-GuyNeural", "en-US-AriaNeural", "en-US-ChristopherNeural"]

PROGRAMS = [
    {"name": "semrush", "product": "Semrush",
     "angle": "all-in-one SEO and marketing toolkit",
     "keywords": "marketing analytics laptop office",
     "cta": "Link in the description"},
    {"name": "hostinger", "product": "Hostinger",
     "angle": "fast, cheap web hosting",
     "keywords": "website server technology code",
     "cta": "Grab the deal below"},
    {"name": "digitalocean", "product": "DigitalOcean",
     "angle": "simple cloud hosting for developers",
     "keywords": "cloud data center servers developer",
     "cta": "Start free — link below"},
]


def run(cmd: list[str], timeout: int = 180) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, timeout=timeout)


def esc_drawtext(t: str) -> str:
    return t.replace("\\", "\\\\").replace(":", "\\:").replace("'", "’").replace("%", "\\%")


# ── 1. Sales script ────────────────────────────────────────────────────────────
def gen_script(prog: dict) -> str:
    key = os.getenv("GROQ_API_KEY", "").strip()
    ask = (
        f"Write a high-converting 20-25 second YouTube Shorts voiceover script that sells "
        f"{prog['product']}, a {prog['angle']}. Rules: open with a scroll-stopping hook in the "
        f"first sentence, give 2 concrete benefits, end with a clear call to action. "
        f"Spoken plain text only, no scene directions, no emojis, no hashtags, ~55 words max."
    )
    if key:
        try:
            body = json.dumps({
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "user", "content": ask}],
                "temperature": 0.8, "max_tokens": 200,
            }).encode()
            req = urllib.request.Request(
                "https://api.groq.com/openai/v1/chat/completions", data=body, method="POST",
                headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=30) as r:
                txt = json.loads(r.read())["choices"][0]["message"]["content"].strip()
            txt = re.sub(r"[\*#`\"]", "", txt).strip()
            if 40 < len(txt) < 700:
                print(f"   script via Groq ({len(txt)} chars)")
                return txt
        except Exception as e:
            print(f"   Groq script failed ({e}) — using template")
    p, a, cta = prog["product"], prog["angle"], prog["cta"]
    return (f"Still doing this the hard way? {p} is the {a} that top creators swear by. "
            f"It saves you hours every week and pays for itself fast. "
            f"Thousands already switched. {cta} and try it today.")


# ── 2. Voiceover + word timings (edge-tts) ──────────────────────────────────────
async def synth_vo(text: str, mp3: Path, voice: str) -> list[tuple[float, float, str]]:
    import edge_tts
    words: list[tuple[float, float, str]] = []
    comm = edge_tts.Communicate(text, voice=voice, rate="+6%")
    with open(mp3, "wb") as f:
        async for ch in comm.stream():
            if ch["type"] == "audio":
                f.write(ch["data"])
            elif ch["type"] == "WordBoundary":
                start = ch["offset"] / 1e7
                dur = ch["duration"] / 1e7
                words.append((start, start + dur, ch["text"]))
    return words


def media_seconds(path: Path) -> float:
    try:
        out = run(["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
                   "-of", "csv=p=0", str(path)], timeout=30).stdout.decode().strip()
        return float(out)
    except Exception:
        return 0.0


# ── 3. Word-timed ASS captions ──────────────────────────────────────────────────
def _ass_time(s: float) -> str:
    h = int(s // 3600); m = int((s % 3600) // 60); sec = s % 60
    return f"{h:d}:{m:02d}:{sec:05.2f}"


def _even_words(script: str, total: float) -> list[tuple[float, float, str]]:
    """Fallback timings when edge-tts returns no word boundaries: distribute the
    script's words evenly across the voiceover duration (leaving a small tail)."""
    toks = [w for w in re.split(r"\s+", script.strip()) if w]
    if not toks:
        return []
    span = max(total - 0.5, 1.0)
    per = span / len(toks)
    return [(i * per, (i + 1) * per, t) for i, t in enumerate(toks)]


def build_ass(words: list[tuple[float, float, str]], ass: Path, total: float, script: str = "") -> None:
    if not words and script:
        words = _even_words(script, total)
    style = ("Style: Cap,DejaVu Sans,110,&H00FFFFFF,&H000000FF,&H00101010,&H90000000,"
             "-1,0,0,0,100,100,0,0,1,7,3,2,90,90,520,1")
    header = (
        "[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\nWrapStyle: 2\n\n"
        "[V4+ Styles]\nFormat: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,"
        "BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,"
        "Shadow,Alignment,MarginL,MarginR,MarginV,Encoding\n" + style + "\n\n"
        "[Events]\nFormat: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text\n")
    lines = []
    chunk: list[tuple[float, float, str]] = []
    for w in words or []:
        chunk.append(w)
        if len(chunk) >= 3 or w[2].endswith((".", "!", "?", ",")):
            st, en = chunk[0][0], chunk[-1][1]
            txt = " ".join(c[2] for c in chunk).upper().replace(",", "").strip()
            lines.append(f"Dialogue: 0,{_ass_time(st)},{_ass_time(max(en, st + 0.4))},Cap,,0,0,0,,{{\\fad(80,80)}}{txt}")
            chunk = []
    if chunk:
        st, en = chunk[0][0], max(chunk[-1][1], total)
        txt = " ".join(c[2] for c in chunk).upper().replace(",", "").strip()
        lines.append(f"Dialogue: 0,{_ass_time(st)},{_ass_time(en)},Cap,,0,0,0,,{{\\fad(80,80)}}{txt}")
    ass.write_text(header + "\n".join(lines) + "\n", encoding="utf-8")


# ── 4. Background: Pexels B-roll (if key) else animated gradient ─────────────────
def fetch_pexels_broll(prog: dict, duration: float, out: Path) -> bool:
    key = os.getenv("PEXELS_API_KEY", "").strip()
    if not key:
        return False
    try:
        q = urllib.parse.quote(prog["keywords"].split()[0] + " " + prog["keywords"].split()[1])
        req = urllib.request.Request(
            f"https://api.pexels.com/videos/search?query={q}&orientation=portrait&per_page=8&size=medium",
            headers={"Authorization": key, "User-Agent": "already-here-shorts/1.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read())
        clips = []
        for vid in data.get("videos", [])[:4]:
            files = [f for f in vid.get("video_files", []) if f.get("height", 0) >= 1080]
            files = files or vid.get("video_files", [])
            if not files:
                continue
            src = sorted(files, key=lambda f: abs(f.get("height", 0) - 1920))[0]["link"]
            cp = out.parent / f"broll_{len(clips)}.mp4"
            urllib.request.urlretrieve(src, cp)
            clips.append(cp)
            if len(clips) >= 3:
                break
        if not clips:
            return False
        # scale/crop each to 1080x1920, trim ~5s, concat, loop to cover duration
        parts = []
        for i, cp in enumerate(clips):
            pp = out.parent / f"brolls_{i}.mp4"
            run(["ffmpeg", "-y", "-t", "5", "-i", str(cp),
                 "-vf", f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,fps=30",
                 "-an", "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p", str(pp)])
            parts.append(pp)
        lst = out.parent / "concat.txt"
        lst.write_text("".join(f"file '{p.name}'\n" for p in parts))
        run(["ffmpeg", "-y", "-stream_loop", "-1", "-f", "concat", "-safe", "0", "-i", str(lst),
             "-t", f"{duration:.2f}", "-c:v", "libx264", "-preset", "veryfast",
             "-pix_fmt", "yuv420p", str(out)], timeout=240)
        return out.exists() and out.stat().st_size > 10000
    except Exception as e:
        print(f"   Pexels B-roll failed ({e}) — gradient fallback")
        return False


def gradient_bg(prog: dict, duration: float, out: Path) -> None:
    palettes = [("0x0f2027", "0x203a43", "0x2c5364"), ("0x1a2a6c", "0x2a5298", "0xb21f1f"),
                ("0x11998e", "0x1c2541", "0x38ef7d"), ("0x232526", "0x414345", "0x536976")]
    c0, c1, c2 = random.choice(palettes)
    run(["ffmpeg", "-y", "-f", "lavfi",
         "-i", f"gradients=s={W}x{H}:c0={c0}:c1={c1}:c2={c2}:n=3:speed=0.012:d={duration:.2f}:r=30",
         "-vf", "zoompan=z='min(zoom+0.0006,1.12)':d=1:s={0}x{1}:fps=30".format(W, H),
         "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p", str(out)], timeout=240)


# ── 5. Music bed ────────────────────────────────────────────────────────────────
def music_bed(duration: float, out: Path) -> None:
    bundled = sorted(Path("assets/music").glob("*.mp3")) if Path("assets/music").exists() else []
    if bundled:
        run(["ffmpeg", "-y", "-stream_loop", "-1", "-i", str(random.choice(bundled)),
             "-t", f"{duration:.2f}", "-af", "volume=0.14", "-c:a", "aac", str(out)])
        if out.exists():
            return
    # soft procedural pad: two tones a fifth apart, tremolo + lowpass + reverb, low volume
    run(["ffmpeg", "-y",
         "-f", "lavfi", "-i", f"sine=frequency=196:duration={duration:.2f}",
         "-f", "lavfi", "-i", f"sine=frequency=294:duration={duration:.2f}",
         "-filter_complex",
         "[0:a][1:a]amix=inputs=2,tremolo=f=5:d=0.4,lowpass=f=900,aecho=0.8:0.7:60:0.3,volume=0.09[a]",
         "-map", "[a]", "-c:a", "aac", str(out)], timeout=120)


# ── 6. Compose ──────────────────────────────────────────────────────────────────
def compose(bg: Path, vo: Path, ass: Path, music: Path, prog: dict, out: Path, duration: float) -> bool:
    top = esc_drawtext(prog["product"].upper())
    cta = esc_drawtext(prog["cta"].upper())
    ass_path = ass.as_posix().replace(":", "\\:")
    vf = (
        f"[0:v]drawtext=fontfile={FONT}:text='{top}':fontsize=64:fontcolor=white:borderw=4:"
        f"bordercolor=black@0.6:x=(w-text_w)/2:y=150,"
        f"drawtext=fontfile={FONT}:text='{cta}':fontsize=46:fontcolor=0xFFD54F:borderw=4:"
        f"bordercolor=black@0.7:x=(w-text_w)/2:y=h-230,"
        f"subtitles='{ass_path}'[v]"
    )
    cmd = [
        "ffmpeg", "-y",
        "-i", str(bg), "-i", str(vo), "-i", str(music),
        "-filter_complex",
        vf + ";[1:a]volume=1.0[vo];[2:a]volume=0.5[mu];[vo][mu]amix=inputs=2:duration=first:dropout_transition=0[a]",
        "-map", "[v]", "-map", "[a]",
        "-t", f"{duration:.2f}",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "22", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(out),
    ]
    r = run(cmd, timeout=300)
    if r.returncode != 0:
        print(r.stderr.decode()[-1500:])
    return out.exists() and out.stat().st_size > 20000


async def make_one(prog: dict) -> dict | None:
    name = prog["name"]
    work = TMP / name
    work.mkdir(parents=True, exist_ok=True)
    print(f"▶ {prog['product']}")
    script = gen_script(prog)
    print(f"   script: {script[:80]}...")

    vo = work / "vo.mp3"
    voice = random.choice(VOICES)
    try:
        words = await synth_vo(script, vo, voice)
    except Exception as e:
        print(f"   ❌ TTS failed: {e}")
        return None
    dur = media_seconds(vo)
    if dur < 3:
        print("   ❌ voiceover too short/empty")
        return None
    dur = min(dur + 0.6, 58)
    print(f"   voice={voice} duration={dur:.1f}s words={len(words)}")

    ass = work / "caps.ass"
    build_ass(words, ass, dur, script)

    bg = work / "bg.mp4"
    if not fetch_pexels_broll(prog, dur, bg):
        gradient_bg(prog, dur, bg)
    if not bg.exists():
        print("   ❌ background failed")
        return None

    music = work / "music.m4a"
    music_bed(dur, music)

    stamp = datetime.now().strftime("%Y%m%d%H%M%S")
    out = OUT / f"{name}_{stamp}.mp4"
    if not compose(bg, vo, ass, music, prog, out, dur):
        print("   ❌ compose failed")
        return None
    size = out.stat().st_size
    print(f"   ✅ {out.name} ({size//1024} KB, {dur:.0f}s)")
    return {
        "program": name,
        "title": f"{prog['product']} Review — {prog['angle'].title()} (2026)",
        "description": (f"{script}\n\n#shorts #{name} #affiliate\n\n"
                        "Affiliate disclosure: links may earn a commission at no cost to you."),
        "path": str(out), "size_bytes": size,
    }


async def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    if not shutil.which("ffmpeg"):
        print("ffmpeg not on PATH", file=sys.stderr); sys.exit(1)
    videos = []
    for prog in PROGRAMS:
        try:
            v = await make_one(prog)
            if v:
                videos.append(v)
        except Exception as e:
            print(f"   ❌ {prog['name']} errored: {e}")
    print(f"\n✅ Campaign: {len(videos)}/{len(PROGRAMS)} videos generated")
    Path("videos_manifest.json").write_text(json.dumps(videos, indent=2))
    if not videos:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
