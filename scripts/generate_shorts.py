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
import secrets
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

def _choice(seq):
    return secrets.choice(seq)

def _randint(a, b):
    return a + secrets.randbelow(b - a + 1)

def _shuffle(seq):
    for i in range(len(seq) - 1, 0, -1):
        j = secrets.randbelow(i + 1)
        seq[i], seq[j] = seq[j], seq[i]

W, H = 1080, 1920
OUT = Path("videos/openmontage")
TMP = Path("videos/_work")
FONT = next((f for f in (
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
) if os.path.exists(f)), "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
VOICES = ["en-US-GuyNeural", "en-US-AriaNeural", "en-US-ChristopherNeural"]

PROGRAMS = [
    {"name": "semrush", "product": "Semrush",
     "angle": "all-in-one SEO and marketing toolkit",
     "keywords": "marketing analytics laptop office",
     "cta": "Link in the description",
     "benefits": ["spies on exactly what keywords your competitors rank for",
                  "finds the low-competition keywords you can actually win",
                  "audits your whole site for SEO issues in one click",
                  "tracks your rankings so you know what's working"],
     "pain": "guessing at SEO and getting nowhere"},
    {"name": "hostinger", "product": "Hostinger",
     "angle": "fast, cheap web hosting",
     "keywords": "website server technology code",
     "cta": "Grab the deal below",
     "benefits": ["loads your site in under a second so visitors don't bounce",
                  "costs less than a coffee a month",
                  "sets up a live site in minutes with one-click installs",
                  "throws in a free domain and SSL"],
     "pain": "overpaying for slow, clunky hosting"},
    {"name": "digitalocean", "product": "DigitalOcean",
     "angle": "simple cloud hosting for developers",
     "keywords": "cloud data center servers developer",
     "cta": "Start free — link below",
     "benefits": ["spins up a cloud server in 55 seconds",
                  "has flat, predictable pricing with no surprise bills",
                  "scales from a side project to millions of users",
                  "comes with free credit to start"],
     "pain": "fighting with overcomplicated, overpriced cloud platforms"},
    # ── B2B field-ops programs — market our own Arizona coverage retainers.
    #    "link" overrides the affiliate funnel in link_block/description.
    {"name": "az-smart-hands", "product": "Already Here Field Coverage",
     "angle": "Arizona smart hands on demand",
     "keywords": "data center technician server rack cables",
     "cta": "Reserve coverage — link below",
     "benefits": ["puts vetted hands in any Phoenix data center within your SLA",
                  "photo-documents every ticket so remote teams see the work",
                  "bills a flat $200 minimum — no travel surprises",
                  "covers rack and stack, swaps, and vendor escort statewide"],
     "pain": "flying a tech to Phoenix for a 30-minute cable swap",
     "link": "https://www.alreadyherellc.com/arizona-field-coverage"},
    {"name": "az-msp-coverage", "product": "Already Here Field Coverage",
     "angle": "Arizona coverage for MSPs",
     "keywords": "IT technician office network installation",
     "cta": "Reserve coverage — link below",
     "benefits": ["gives your MSP an Arizona bench without an Arizona hire",
                  "guarantees 24-48 hour onsite response on retainer",
                  "white-labels under your ticketing and your brand",
                  "starts at $2,000 a month with 20 onsite hours included"],
     "pain": "losing Arizona clients because you can't get onsite",
     "link": "https://www.alreadyherellc.com/arizona-field-coverage"},
    {"name": "az-field-dispatch", "product": "Already Here Field Coverage",
     "angle": "field dispatch across Arizona",
     "keywords": "van technician driving tools jobsite",
     "cta": "Reserve coverage — link below",
     "benefits": ["dispatches POS, printer, network, and CCTV work statewide",
                  "quotes 42 productized services at fixed prices",
                  "answers dispatch requests the same business day",
                  "reserves capacity monthly so you're never in the queue"],
     "pain": "juggling five one-off contractors across one state",
     "link": "https://www.alreadyherellc.com/arizona-field-coverage"},
]


def run(cmd: list[str], timeout: int = 180) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, timeout=timeout)


def esc_drawtext(t: str) -> str:
    return t.replace("\\", "\\\\").replace(":", "\\:").replace("'", "’").replace("%", "\\%")


# ── 1. Script writing (AI chain → template). Format-aware. ──────────────────────
_FORMAT_BRIEFS = {
    "sales": ("that sells {product}, a {angle}",
              "- Then 2 concrete, specific benefits (not vague).\n"
              "- End with a punchy call to action."),
    "tips": ("giving 3 rapid-fire, genuinely useful tips about {product} ({angle})",
             "- Number the tips: First… Second… Third…\n"
             "- Each tip is one concrete action, not advice-shaped filler.\n"
             "- End by telling them to follow for more."),
    "secrets": ("revealing insider secrets about {product} ({angle})",
                "- Conspiratorial, 'they don't want you to know' tone — but every claim true and specific.\n"
                "- 2 secrets max, each with the concrete payoff.\n"
                "- End with an open loop and follow CTA."),
    "story": ("telling a first-person mini story about {angle} using {product}",
              "- Arc: struggle → discovery → payoff, in plain spoken language.\n"
              "- Make it feel personal and specific, not generic.\n"
              "- End with the one-line lesson and a follow CTA."),
    "diy": ("walking through how to {angle} yourself, step by step, with {product}",
            "- Exactly 3 numbered steps, each one concrete action.\n"
            "- Beginner-friendly: no jargon without a 3-word explanation.\n"
            "- End with the result they get and a follow CTA."),
    "micro": ("telling a two-beat micro story about {angle} with {product}",
              "- Beat 1: one short setup sentence — a struggle or a bold claim.\n"
              "- Beat 2: the twist or payoff, concrete and specific.\n"
              "- Write it so the ending loops naturally back into the first line "
              "(micro Shorts win on replays).\n"
              "- No CTA sentence — the caption and description do that job."),
}


def _script_prompt(prog: dict) -> str:
    fmt = prog.get("format", "sales")
    what, rules = _FORMAT_BRIEFS.get(fmt, _FORMAT_BRIEFS["sales"])
    secs, words = ("5-7", "~16 words total, hard max 20") if fmt == "micro" \
        else ("20-25", "~55 words total, hard max 65")
    return (
        f"You are a viral retention scriptwriter for YouTube Shorts. Write a {secs} second "
        f"voiceover script {what.format(product=prog['product'], angle=prog['angle'])}.\n"
        f"Rules:\n"
        f"- First sentence is an aggressive open-loop hook (a bold question or pattern interrupt).\n"
        f"{rules}\n"
        f"- Spoken plain text ONLY. No scene directions, no emojis, no hashtags, no quotes, no markdown.\n"
        f"- Short punchy sentences. {words}."
    )


def _clean_script(txt: str) -> str:
    return re.sub(r"[\*#`\"]", "", txt).strip()


# Multi-provider AI chain. Each entry: (label, env-var, url, header-fn, body-fn, parse-fn).
# Tried in order; any that returns text wins. All optional — templates are the backstop.
def _openai_style(model):
    return (lambda k: {"Authorization": f"Bearer {k}"},
            lambda p: {"model": model, "messages": [{"role": "user", "content": p}],
                       "temperature": 0.85, "max_tokens": 250},
            lambda d: d["choices"][0]["message"]["content"])


_AI_PROVIDERS = [
    ("OpenRouter", "OPENROUTER_API_KEY", "https://openrouter.ai/api/v1/chat/completions",
     *_openai_style("meta-llama/llama-3.3-70b-instruct:free")),
    ("Groq", "GROQ_API_KEY", "https://api.groq.com/openai/v1/chat/completions",
     *_openai_style("llama-3.3-70b-versatile")),
    ("DeepSeek", "DEEPSEEK_API_KEY", "https://api.deepseek.com/chat/completions",
     *_openai_style("deepseek-chat")),
    ("Gemini", "GEMINI_API_KEY",
     "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent",
     lambda k: {"x-goog-api-key": k},
     lambda p: {"contents": [{"parts": [{"text": p}]}], "generationConfig": {"temperature": 0.9}},
     lambda d: d["candidates"][0]["content"]["parts"][0]["text"]),
]


def ai_complete(prompt: str, min_len: int = 40, max_len: int = 700) -> str | None:
    """Generic completion over the free-provider chain. Returns None if no
    provider is configured/succeeds — callers must have a template backstop."""
    for label, envk, url, hfn, bfn, pfn in _AI_PROVIDERS:
        key = os.getenv(envk, "").strip()
        if not key:
            continue
        for attempt in range(2):  # one retry (handles transient 429)
            try:
                req = urllib.request.Request(
                    url, data=json.dumps(bfn(prompt)).encode(), method="POST",
                    headers={**hfn(key), "Content-Type": "application/json",
                             "User-Agent": "already-here-shorts/1.0"})
                with urllib.request.urlopen(req, timeout=30) as r:
                    txt = _clean_script(pfn(json.loads(r.read())))
                if min_len < len(txt) < max_len:
                    print(f"   script via {label} ({len(txt)} chars)")
                    return txt
                break
            except urllib.error.HTTPError as e:
                if e.code == 429 and attempt == 0:
                    time.sleep(3)
                    continue
                print(f"   {label} failed (HTTP {e.code})")
                break
            except Exception as e:
                print(f"   {label} failed ({str(e)[:50]})")
                break
    return None


# ── Rich template engine (zero external dependency — the unbreakable backstop) ───
_HOOKS = [
    "Stop {pain}.",
    "Still {pain}? Watch this.",
    "Nobody tells you this about {product}.",
    "This is why smart people stopped {pain}.",
    "{product} is the unfair advantage nobody talks about.",
    "Here's what changed everything for me.",
    "If you're {pain}, you need to see this.",
    "I wish I knew about {product} sooner.",
]
_CONNECT = ["Here's the deal.", "It's simple.", "Look.", "Here's why.", "Check this out."]
_CLOSERS = [
    "Thousands already made the switch.",
    "It pays for itself fast.",
    "Do it before your competition does.",
    "This is the easy button.",
    "Stop leaving money on the table.",
]


def _template_script(prog: dict) -> str:
    pain = prog.get("pain", "doing it the hard way")
    fmt = prog.get("format", "sales")
    benefits = list(prog.get("benefits", []))
    _shuffle(benefits)
    b = benefits[:3] if benefits else ["just works"]
    if fmt == "micro":
        # two beats, ~14 words, loop-friendly — skip the connectors/closers
        b0 = " ".join(b[0].split()[:6])
        return f"I kept {pain}. Then {prog['product']} — {b0}. Every time."
    hook = _choice(_HOOKS).format(pain=pain, product=prog["product"])
    if fmt == "tips" and len(b) >= 3:
        body = f"First, {b[0]}. Second, {b[1]}. Third, {b[2]}"
        hook = f"Three {prog['product']} tips nobody shows you."
    elif fmt == "secrets" and len(b) >= 2:
        hook = f"Nobody tells you this about {prog['product']}."
        body = f"Here's the secret: it {b[0]}. And the part they skip — it {b[1]}"
    elif fmt == "story" and len(b) >= 2:
        hook = f"I almost gave up on {prog['angle']}."
        body = f"Then I found {prog['product']}. It {b[0]}. Now it {b[1]}"
    elif fmt == "diy" and len(b) >= 3:
        hook = f"Do this yourself — three steps."
        body = f"Step one: {b[0]}. Step two: {b[1]}. Step three: {b[2]}"
    else:
        body = f"{prog['product']} {b[0]}"
        if len(b) > 1:
            body += f", and it {b[1]}"
    parts = [hook, _choice(_CONNECT), body + ".", _choice(_CLOSERS),
             f"{prog['cta']} and try it today." if fmt == "sales"
             else f"{prog['cta']}."]
    return " ".join(parts)


def gen_script(prog: dict) -> str:
    s = ai_complete(_script_prompt(prog))
    if s:
        return s
    print("   script via template engine")
    return _template_script(prog)


# ── 2. Voiceover + word timings (edge-tts) ──────────────────────────────────────
async def synth_vo(text: str, mp3: Path, voice: str) -> list[tuple[float, float, str]]:
    import edge_tts
    words: list[tuple[float, float, str]] = []
    comm = edge_tts.Communicate(text, voice=voice, rate="+6%", boundary="WordBoundary")
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


_ACCENTS = ["&H00FFFFFF", "&H0037F0FF", "&H007DEF3D", "&H00F0A020"]  # white, yellow, green, blue (BGR)


def build_ass(words: list[tuple[float, float, str]], ass: Path, total: float,
              script: str = "", kinetic: bool = False) -> None:
    """CapCut-style captions: 1-2 words per beat, big/bold, pop-in scale + fade,
    rotating accent colours. Auto-wrap + margins prevent edge overflow.
    kinetic=True is the animation style: ONE word per beat, bigger, with
    per-beat position jitter and slight rotation — typography IS the visual."""
    if not words and script:
        words = _even_words(script, total)
    # Base style: big bold, thick outline + shadow, centered (an5), generous side margins.
    style = ("Style: Cap,DejaVu Sans,104,&H00FFFFFF,&H000000FF,&H00000000,&H90000000,"
             "-1,0,0,0,100,100,1,0,1,8,4,5,110,110,0,1")
    header = (
        "[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\nWrapStyle: 0\n\n"
        "[V4+ Styles]\nFormat: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,"
        "BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,"
        "Shadow,Alignment,MarginL,MarginR,MarginV,Encoding\n" + style + "\n\n"
        "[Events]\nFormat: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text\n")

    # Group into beats: kinetic = one word each; classic = 1-2 short words.
    beats: list[tuple[float, float, str]] = []
    chunk: list[tuple[float, float, str]] = []
    for w in words or []:
        chunk.append(w)
        joined = " ".join(c[2] for c in chunk)
        end_punct = w[2].endswith((".", "!", "?", ",", ";", ":"))
        if kinetic or len(chunk) >= 2 or len(joined) >= 11 or end_punct:
            beats.append((chunk[0][0], chunk[-1][1], joined))
            chunk = []
    if chunk:
        beats.append((chunk[0][0], max(chunk[-1][1], total), " ".join(c[2] for c in chunk)))

    lines = []
    for i, (st, en, txt) in enumerate(beats):
        en = max(en, st + 0.28)
        col = _ACCENTS[i % len(_ACCENTS)]
        if kinetic:
            # full-screen typography: bigger, drifting anchor, slight tilt
            x = 540 + _randint(-70, 70)
            y = 1030 + _randint(-140, 140)
            rz = _randint(-5, 5)
            eff = (f"{{\\an5\\pos({x},{y})\\c{col}&\\fs150\\frz{rz}\\fad(50,30)"
                   f"\\fscx40\\fscy40\\t(0,110,\\fscx115\\fscy115)"
                   f"\\t(110,190,\\fscx100\\fscy100)}}")
        else:
            # anchor an5 (center) at 62% height via \pos; pop-in with overshoot
            eff = (f"{{\\an5\\pos(540,1200)\\c{col}&\\fad(60,40)"
                   f"\\fscx52\\fscy52\\t(0,120,\\fscx110\\fscy110)\\t(120,200,\\fscx100\\fscy100)}}")
        clean = re.sub(r"[,;:]", "", txt).upper().strip()
        lines.append(f"Dialogue: 0,{_ass_time(st)},{_ass_time(en)},Cap,,0,0,0,,{eff}{clean}")
    ass.write_text(header + "\n".join(lines) + "\n", encoding="utf-8")


# ── 4. Scenes: multi-clip Pexels B-roll with xfade transitions (+ cut times) ─────
_TRANS = ["slideleft", "circleopen", "fade", "slideup", "smoothright", "wiperight", "zoomin"]


def build_scenes(prog: dict, duration: float, out: Path, work: Path) -> list[float]:
    """Build the background video. visual=kinetic skips B-roll on purpose —
    the animated gradient is the canvas and the typography is the show.
    Otherwise, with a Pexels key: N ~3s clips stitched with
    xfade transitions — returns the list of cut (transition-midpoint) timestamps
    for SFX. Without a key or on any failure: single animated gradient, returns []."""
    key = os.getenv("PEXELS_API_KEY", "").strip()
    if not key or prog.get("visual") == "kinetic":
        gradient_bg(prog, duration, out)
        return []
    try:
        X = 0.5  # crossfade seconds
        # micro shorts (<10s) look frantic with 3+ cuts — cap at 2 clips there
        n = max(2 if duration < 10 else 3, min(7, round(duration / 3.0)))
        q = urllib.parse.quote(" ".join(prog["keywords"].split()[:2]))
        req = urllib.request.Request(
            f"https://api.pexels.com/videos/search?query={q}&orientation=portrait&per_page=15&size=medium",
            headers={"Authorization": key, "User-Agent": "already-here-shorts/1.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read())
        clips: list[Path] = []
        for vid in data.get("videos", []):
            files = [f for f in vid.get("video_files", []) if f.get("height", 0) >= 1080] or vid.get("video_files", [])
            if not files:
                continue
            src = sorted(files, key=lambda f: abs(f.get("height", 0) - 1920))[0]["link"]
            cp = work / f"raw{len(clips)}.mp4"
            dreq = urllib.request.Request(src, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(dreq, timeout=90) as resp, open(cp, "wb") as fh:
                shutil.copyfileobj(resp, fh)
            clips.append(cp)
            if len(clips) >= n:
                break
        if len(clips) < 2:
            gradient_bg(prog, duration, out)
            return []
        n = len(clips)
        seg = (duration + (n - 1) * X) / n  # so total after xfade == duration
        segs = []
        for i, cp in enumerate(clips):
            sp = work / f"seg{i}.mp4"
            run(["ffmpeg", "-y", "-stream_loop", "-1", "-t", f"{seg:.3f}", "-i", str(cp),
                 "-vf", f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,fps=30",
                 "-an", "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p", str(sp)], timeout=120)
            if not sp.exists():
                gradient_bg(prog, duration, out)
                return []
            segs.append(sp)
        inputs: list[str] = []
        for sp in segs:
            inputs += ["-i", str(sp)]
        fc, cut_times = [], []
        prev = "[0:v]"
        for i in range(1, n):
            off = i * (seg - X)
            lbl = "[bg]" if i == n - 1 else f"[x{i}]"
            fc.append(f"{prev}[{i}:v]xfade=transition={_TRANS[(i - 1) % len(_TRANS)]}:duration={X}:offset={off:.3f}{lbl}")
            cut_times.append(round(off + X / 2, 3))
            prev = lbl
        run(["ffmpeg", "-y", *inputs, "-filter_complex", ";".join(fc), "-map", "[bg]",
             "-t", f"{duration:.2f}", "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p", str(out)],
            timeout=240)
        if out.exists() and out.stat().st_size > 10000:
            print(f"   B-roll: {n} clips, {len(cut_times)} transitions")
            return cut_times
        gradient_bg(prog, duration, out)
        return []
    except Exception as e:
        print(f"   Pexels scenes failed ({str(e)[:70]}) — gradient")
        gradient_bg(prog, duration, out)
        return []


def make_swoosh(out: Path) -> None:
    run(["ffmpeg", "-y", "-f", "lavfi", "-i", "anoisesrc=d=0.45:c=pink:a=0.8",
         "-af", "highpass=f=250,lowpass=f=5500,afade=t=in:d=0.06,afade=t=out:st=0.14:d=0.3,volume=1.3",
         "-ar", "44100", "-ac", "2", str(out)], timeout=60)


def gradient_bg(prog: dict, duration: float, out: Path) -> None:
    palettes = [("0x0f2027", "0x203a43", "0x2c5364"), ("0x1a2a6c", "0x2a5298", "0xb21f1f"),
                ("0x11998e", "0x1c2541", "0x38ef7d"), ("0x232526", "0x414345", "0x536976")]
    c0, c1, c2 = _choice(palettes)
    run(["ffmpeg", "-y", "-f", "lavfi",
         "-i", f"gradients=s={W}x{H}:c0={c0}:c1={c1}:c2={c2}:n=3:speed=0.012:d={duration:.2f}:r=30",
         "-vf", "zoompan=z='min(zoom+0.0006,1.12)':d=1:s={0}x{1}:fps=30".format(W, H),
         "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p", str(out)], timeout=240)


# ── 5. Music bed ────────────────────────────────────────────────────────────────
def music_bed(duration: float, out: Path) -> None:
    bundled = sorted(Path("assets/music").glob("*.mp3")) if Path("assets/music").exists() else []
    if bundled:
        run(["ffmpeg", "-y", "-stream_loop", "-1", "-i", str(_choice(bundled)),
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


# ── 6. Compose (video + captions/branding + VO/music/swoosh-at-cuts) ─────────────
def compose(bg: Path, vo: Path, ass: Path, music: Path, swoosh: Path,
            cut_times: list[float], prog: dict, out: Path, duration: float) -> bool:
    top = esc_drawtext(prog["product"].upper())
    cta = esc_drawtext(prog["cta"].upper())
    ass_path = ass.as_posix().replace(":", "\\:")
    font = FONT
    if ":" in font:  # Windows drive colon breaks ffmpeg filter parsing — use a relative copy
        local_font = TMP / "font.ttf"
        if not local_font.exists():
            shutil.copy(FONT, local_font)
        font = local_font.as_posix()
    vf = (
        f"[0:v]drawtext=fontfile={font}:text='{top}':fontsize=64:fontcolor=white:borderw=4:"
        f"bordercolor=black@0.6:x=(w-text_w)/2:y=150,"
        f"drawtext=fontfile={font}:text='{cta}':fontsize=46:fontcolor=0xFFD54F:borderw=4:"
        f"bordercolor=black@0.7:x=(w-text_w)/2:y=h-230,"
        f"subtitles='{ass_path}'[v]"
    )
    inputs = ["-i", str(bg), "-i", str(vo), "-i", str(music)]
    afc = "[1:a]volume=1.0[vo];[2:a]volume=0.5[mu]"
    mix = "[vo][mu]"
    n_in = 2
    use_sfx = bool(cut_times) and swoosh.exists()
    if use_sfx:
        inputs += ["-i", str(swoosh)]
        k = len(cut_times)
        afc += ";[3:a]asplit=%d%s" % (k, "".join(f"[sw{j}]" for j in range(k)))
        for j, ct in enumerate(cut_times):
            ms = int(ct * 1000)
            afc += f";[sw{j}]adelay={ms}|{ms}[d{j}]"
            mix += f"[d{j}]"
            n_in += 1
    afc += f";{mix}amix=inputs={n_in}:duration=first:dropout_transition=0:normalize=0[a]"
    cmd = [
        "ffmpeg", "-y", *inputs,
        "-filter_complex", vf + ";" + afc,
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
    voice = _choice(VOICES)
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

    # micros without an explicit visual flip a coin: kinetic typography vs
    # B-roll — the tracker's view data decides which style wins
    if prog.get("format") == "micro" and "visual" not in prog:
        prog["visual"] = _choice(["kinetic", "broll"])
    kinetic = prog.get("visual") == "kinetic"
    if kinetic:
        print("   visual=kinetic (typography animation)")

    ass = work / "caps.ass"
    build_ass(words, ass, dur, script, kinetic=kinetic)

    bg = work / "bg.mp4"
    cut_times = build_scenes(prog, dur, bg, work)
    if not bg.exists():
        print("   ❌ background failed")
        return None

    music = work / "music.m4a"
    music_bed(dur, music)
    swoosh = work / "swoosh.wav"
    if cut_times:
        make_swoosh(swoosh)

    stamp = datetime.now().strftime("%Y%m%d%H%M%S")
    out = OUT / f"{name}_{stamp}.mp4"
    if not compose(bg, vo, ass, music, swoosh, cut_times, prog, out, dur):
        print("   ❌ compose failed")
        return None
    size = out.stat().st_size
    print(f"   ✅ {out.name} ({size//1024} KB, {dur:.0f}s)")
    return {
        "program": name,
        "title": (f"{prog['product']} — {prog['angle'].title()} #Shorts"
                  if prog.get("format") in ("story", "micro")
                  else f"{prog['product']} Review — {prog['angle'].title()} (2026)"),
        "description": (
            f"{script}\n\n{link_block(prog)}\n\n#shorts #fieldservice #arizona #{name}"
            if prog.get("link") else
            f"{script}\n\n{link_block(prog)}\n\n#shorts #{name} #affiliate\n\n"
            "Affiliate disclosure: links may earn a commission at no cost to you."),
        "path": str(out), "size_bytes": size,
    }


def link_block(prog: dict) -> str:
    """The clickable links every description must carry — the whole funnel.
    Program-specific affiliate URL from AFFILIATE_LINKS (JSON map, env),
    then our owned links (always present, always monetizable).
    B2B programs (with a "link" key) advertise our own service instead."""
    if prog.get("link"):
        return "\n".join([
            f"→ Reserve Arizona field coverage: {prog['link']}",
            "→ Full service catalog (fixed prices): "
            "https://www.alreadyherellc.com/services-catalog",
            "→ Dispatch a request: https://www.alreadyherellc.com/dispatch",
            "Questions: dispatch@alreadyherellc.com",
        ])
    links = {}
    try:
        links = json.loads(os.getenv("AFFILIATE_LINKS", "") or "{}")
    except Exception:
        pass
    lines = []
    url = links.get(prog["name"]) or links.get(prog["product"].lower())
    if url:
        lines.append(f"→ Try {prog['product']}: {url}")
    lines.append("→ Free playbook — The $0 Content Engine: "
                 "https://quantam101.github.io/content/ebooks/zero-dollar-content-engine/")
    lines.append("→ The Complete Blueprint (full build manual): "
                 "https://quantam101.github.io/content/ebooks/blueprint/")
    lines.append("→ Our tools & kits: https://alreadyhere.gumroad.com")
    return "\n".join(lines)


async def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    if not shutil.which("ffmpeg"):
        print("ffmpeg not on PATH", file=sys.stderr); sys.exit(1)
    programs = list(PROGRAMS)
    trending = Path("trending_programs.json")
    if trending.exists():  # produced by find_trending.py → trending_to_programs.py
        extra = [p for p in json.loads(trending.read_text())
                 if p.get("name") not in {q["name"] for q in programs}]
        print(f"+ {len(extra)} trending program(s) merged")
        programs += extra
    videos = []
    for prog in programs:
        try:
            v = await make_one(prog)
            if v:
                videos.append(v)
        except Exception as e:
            print(f"   ❌ {prog['name']} errored: {e}")
    print(f"\n✅ Campaign: {len(videos)}/{len(programs)} videos generated")
    Path("videos_manifest.json").write_text(json.dumps(videos, indent=2))
    if not videos:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
