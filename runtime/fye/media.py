"""
FYE media kit — neural voiceover, word-timed captions, stock B-roll,
Ken Burns motion, and a ducked music bed. Ported from the proven
`scripts/generate_shorts.py` stack; every stage degrades gracefully so a
missing key or API never fails the package. Zero-spend: all sources are
free-tier or local ffmpeg synthesis.
"""
from __future__ import annotations

import json
import logging
import os
import re
import secrets
import subprocess
import urllib.parse
import urllib.request

from pathlib import Path
from typing import List, Optional, Tuple

logger = logging.getLogger("fye.media")

_rng = secrets.SystemRandom()

# Output geometry — vertical Shorts by default; FYE_ASPECT unlocks the rest.
ASPECTS = {
    "vertical": (1080, 1920), "portrait": (1080, 1920), "9:16": (1080, 1920),
    "landscape": (1920, 1080), "16:9": (1920, 1080),
    "square": (1080, 1080), "1:1": (1080, 1080),
}
W, H = ASPECTS.get((os.getenv("FYE_ASPECT") or "vertical").lower(), (1080, 1920))

FONT = next((f for f in (
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
) if os.path.exists(f)), "sans-serif")

VOICES = ["en-US-GuyNeural", "en-US-AriaNeural", "en-US-ChristopherNeural"]


def _run(cmd: List[str], timeout: int = 120) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, timeout=timeout)  # noqa: S603


def media_seconds(path: Path) -> float:
    try:
        out = _run(["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
                    "-of", "csv=p=0", str(path)], timeout=30).stdout.decode().strip()
        return float(out)
    except Exception:
        return 0.0


# ── Voiceover: edge-tts neural voice + word timings ───────────────────────────

async def synth_voiceover(text: str, out: Path, voice: str) -> Tuple[List[Tuple[float, float, str]], bool]:
    """edge-tts neural TTS. Returns ([(start, end, word)], ok). Free, no key."""
    import edge_tts  # lazy — optional dep
    words: List[Tuple[float, float, str]] = []
    comm = edge_tts.Communicate(text, voice=voice, rate="+6%", boundary="WordBoundary")
    with open(out, "wb") as f:
        async for ch in comm.stream():
            if ch["type"] == "audio":
                f.write(ch["data"])
            elif ch["type"] == "WordBoundary":
                start = ch["offset"] / 1e7
                words.append((start, start + ch["duration"] / 1e7, ch["text"]))
    return words, out.exists() and out.stat().st_size > 1000


# ── Captions: word-timed CapCut-style ASS ─────────────────────────────────────

def _ass_time(s: float) -> str:
    h = int(s // 3600)
    m = int((s % 3600) // 60)
    sec = s % 60
    return f"{h:d}:{m:02d}:{sec:05.2f}"


def _even_words(script: str, total: float) -> List[Tuple[float, float, str]]:
    toks = [w for w in re.split(r"\s+", script.strip()) if w]
    if not toks:
        return []
    span = max(total - 0.5, 1.0)
    per = span / len(toks)
    return [(i * per, (i + 1) * per, t) for i, t in enumerate(toks)]


_ACCENTS = ["&H00FFFFFF", "&H0037F0FF", "&H007DEF3D", "&H00F0A020"]


def build_ass(words: List[Tuple[float, float, str]], ass: Path, total: float,
              script: str = "") -> None:
    """CapCut-style captions: 1-2 words per beat, big/bold, pop-in scale + fade."""
    if not words and script:
        words = _even_words(script, total)
    style = ("Style: Cap,DejaVu Sans,104,&H00FFFFFF,&H000000FF,&H00000000,&H90000000,"
             "-1,0,0,0,100,100,1,0,1,8,4,5,110,110,0,1")
    header = (
        f"[Script Info]\nScriptType: v4.00+\nPlayResX: {W}\nPlayResY: {H}\nWrapStyle: 0\n\n"
        "[V4+ Styles]\nFormat: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,"
        "BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,"
        "Shadow,Alignment,MarginL,MarginR,MarginV,Encoding\n" + style + "\n\n"
        "[Events]\nFormat: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text\n")

    beats: List[Tuple[float, float, str]] = []
    chunk: List[Tuple[float, float, str]] = []
    for w in words or []:
        chunk.append(w)
        joined = " ".join(c[2] for c in chunk)
        if len(chunk) >= 2 or len(joined) >= 11 or w[2].endswith((".", "!", "?", ",", ";", ":")):
            beats.append((chunk[0][0], chunk[-1][1], joined))
            chunk = []
    if chunk:
        beats.append((chunk[0][0], max(chunk[-1][1], total), " ".join(c[2] for c in chunk)))

    lines = []
    for i, (st, en, txt) in enumerate(beats):
        en = max(en, st + 0.28)
        col = _ACCENTS[i % len(_ACCENTS)]
        eff = (f"{{\\an5\\pos({W // 2},{int(H * 0.625)})\\c{col}&\\fad(60,40)"
               f"\\fscx52\\fscy52\\t(0,120,\\fscx110\\fscy110)\\t(120,200,\\fscx100\\fscy100)}}")
        clean = re.sub(r"[,;:]", "", txt).upper().strip()
        lines.append(f"Dialogue: 0,{_ass_time(st)},{_ass_time(en)},Cap,,0,0,0,,{eff}{clean}")
    ass.write_text(header + "\n".join(lines) + "\n", encoding="utf-8")


# ── Visuals: Pexels/Pixabay B-roll (free-tier keys) ───────────────────────────

_BROLL_HOSTS = (".pexels.com", ".pixabay.com")
_BROLL_MAX_BYTES = 150 * 1024 * 1024  # stock clips are seconds long; cap abuse


def _allowed_broll_url(url: str) -> bool:
    parts = urllib.parse.urlparse(url)
    return (parts.scheme == "https"
            and (parts.hostname or "").lower().endswith(_BROLL_HOSTS))


class _AllowlistRedirect(urllib.request.HTTPRedirectHandler):
    """Re-validates every redirect target against the stock-CDN allowlist."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not _allowed_broll_url(newurl):
            raise urllib.error.HTTPError(req.full_url, code,
                                         f"redirect to disallowed host: {newurl}",
                                         headers, fp)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _download(url: str, dest: Path, timeout: int = 90) -> bool:
    """Fetch one clip with SSRF + size guards: https only, stock-CDN hosts
    only, bounded read. Anything else is rejected, not fetched."""
    try:
        parts = urllib.parse.urlparse(url)
        host = (parts.hostname or "").lower()
        if parts.scheme != "https" or not host.endswith(_BROLL_HOSTS):
            logger.warning("[B-roll] rejected URL host %r", host)
            return False
        req = urllib.request.Request(url,  # noqa: S310 — host allowlisted above
                                     headers={"User-Agent": "already-here-fye/1.0"})
        # A poisoned stock-API response could 302 to an internal host, so
        # re-run the allowlist on every redirect target before following it.
        opener = urllib.request.build_opener(_AllowlistRedirect())
        with opener.open(req, timeout=timeout) as resp:  # noqa: S310
            data = resp.read(_BROLL_MAX_BYTES + 1)
        if len(data) > _BROLL_MAX_BYTES:
            dest.unlink(missing_ok=True)
            return False
        dest.write_bytes(data)
        return dest.stat().st_size > 10_000
    except Exception:
        return False


def pexels_clip_urls(query: str, key: str, want: int) -> List[str]:
    q = urllib.parse.quote(query)
    req = urllib.request.Request(
        f"https://api.pexels.com/videos/search?query={q}&orientation=portrait&per_page=15&size=medium",
        headers={"Authorization": key, "User-Agent": "already-here-fye/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:  # noqa: S310
        data = json.loads(r.read())
    urls: List[str] = []
    for vid in data.get("videos", []):
        files = [f for f in vid.get("video_files", []) if f.get("height", 0) >= 720] or vid.get("video_files", [])
        if not files:
            continue
        urls.append(sorted(files, key=lambda f: abs(f.get("height", 0) - H))[0]["link"])
        if len(urls) >= want:
            break
    return urls


def pixabay_clip_urls(query: str, key: str, want: int) -> List[str]:
    q = urllib.parse.quote(query)
    req = urllib.request.Request(
        f"https://pixabay.com/api/videos/?key={key}&q={q}&per_page=30&safesearch=true",
        headers={"User-Agent": "already-here-fye/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:  # noqa: S310
        data = json.loads(r.read())
    portrait = H >= W
    matched, fallback = [], []
    for hit in data.get("hits", []):
        vids = hit.get("videos", {})
        chosen = None
        for size in ("large", "medium", "small", "tiny"):
            v = vids.get(size)
            if v and v.get("url"):
                if chosen is None:
                    chosen = v["url"]
                if (v.get("height", 0) >= v.get("width", 0)) == portrait:
                    matched.append(v["url"])
                    chosen = None
                    break
        if chosen:
            fallback.append(chosen)
    return (matched + fallback)[:want]


def fetch_broll(query: str, dest: Path,
                pexels_key: str = "", pixabay_key: str = "") -> Optional[str]:
    """One stock clip for a shot. Pexels first, Pixabay fallback. None if neither."""
    # Combine candidates from both sources so a broken Pexels clip doesn't
    # discard good Pixabay footage (and vice versa).
    urls: List[str] = []
    if pexels_key:
        try:
            urls += pexels_clip_urls(query, pexels_key, 3)
        except Exception as exc:
            logger.warning("[B-roll] Pexels lookup failed: %s", exc)
    if pixabay_key:
        try:
            urls += pixabay_clip_urls(query, pixabay_key, 3)
        except Exception as exc:
            logger.warning("[B-roll] Pixabay lookup failed: %s", exc)
    for u in urls:
        if _download(u, dest):
            return "pexels" if "pexels" in u else "pixabay"
    return None


# ── Scene rendering (ffmpeg) ──────────────────────────────────────────────────

_TRANSITIONS = ["slideleft", "circleopen", "fade", "slideup", "smoothright", "wiperight", "zoomin"]


def scene_from_broll(clip: Path, duration: float, out: Path) -> bool:
    """Trim/loop + scale/crop a stock clip to the shot's duration and frame."""
    r = _run(["ffmpeg", "-y", "-stream_loop", "-1", "-t", f"{duration:.3f}", "-i", str(clip),
              "-vf", f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,fps=30",
              "-an", "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p", str(out)],
             timeout=120)
    return r.returncode == 0 and out.exists() and out.stat().st_size > 10_000


def scene_from_image(img: Path, duration: float, out: Path) -> bool:
    """Ken Burns pan-zoom on a still."""
    r = _run(["ffmpeg", "-y", "-loop", "1", "-t", f"{duration:.3f}", "-i", str(img),
              "-vf", (f"scale={W * 2}:{H * 2}:force_original_aspect_ratio=increase,crop={W * 2}:{H * 2},"
                      f"zoompan=z='min(zoom+0.0008,1.15)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
                      f":d={int(duration * 30)}:s={W}x{H}:fps=30,setsar=1"),
              "-an", "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p", str(out)],
             timeout=120)
    return r.returncode == 0 and out.exists() and out.stat().st_size > 10_000


def _wrap_text(text: str, width: int = 16, max_lines: int = 4) -> list:
    """Wrap words to ~width-char lines, capped at max_lines."""
    # drawtext text= values can re-enter the ffmpeg filter parser — strip
    # every character that could start/alter a filter or close a string.
    # '%' is kept and escaped at the drawtext site (as '%%') so claims
    # like "10%" still render correctly.
    words = re.sub(r"[':\[\]{};,\\()]", " ", text).split()
    lines, cur = [], ""
    for w in words:
        if len(cur) + len(w) + 1 > width and cur:
            lines.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    if cur:
        lines.append(cur)
    return lines[:max_lines]


def scene_from_svg(svg: Path, text: str, duration: float, out: Path) -> bool:
    """Animated gradient + wrapped drawtext card (ffmpeg can't decode SVG).
    `svg` may not exist — its name only seeds the palette choice."""
    palettes = [("0x0f2027", "0x203a43", "0x2c5364"), ("0x1a2a6c", "0x2a5298", "0xb21f1f"),
                ("0x11998e", "0x1c2541", "0x38ef7d"), ("0x232526", "0x414345", "0x536976")]
    c0, c1, c2 = palettes[sum(map(ord, svg.name)) % len(palettes)]
    lines = _wrap_text(text)
    dt = ",".join(
        f"drawtext=fontfile={FONT}:text='{esc_drawtext(ln)}':fontsize=64:fontcolor=white:"
        f"borderw=3:bordercolor=black@0.6:x=(w-text_w)/2:y=(h-{len(lines)*80})/2+{i*80}"
        for i, ln in enumerate(lines))
    vf = (f"zoompan=z='min(zoom+0.0006,1.12)':d=1:s={W}x{H}:fps=30,{dt}")
    r = _run(["ffmpeg", "-y", "-f", "lavfi",
              "-i", f"gradients=s={W}x{H}:c0={c0}:c1={c1}:c2={c2}:n=3:speed=0.012:d={duration:.2f}:r=30",
              "-vf", vf, "-an", "-c:v", "libx264", "-preset", "veryfast",
              "-pix_fmt", "yuv420p", str(out)], timeout=120)
    return r.returncode == 0 and out.exists() and out.stat().st_size > 10_000


def stitch_scenes(scene_paths: List[Path], out: Path, duration: float,
                  scene_durs: Optional[List[float]] = None) -> bool:
    """Concat scenes with xfade transitions; total length == duration.
    `scene_durs` gives each scene's rendered length — required when shots
    have unequal durations so xfade offsets stay cumulative and correct."""
    n = len(scene_paths)
    if n == 0:
        return False
    if n == 1:
        r = _run(["ffmpeg", "-y", "-i", str(scene_paths[0]), "-t", f"{duration:.2f}",
                  "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p", str(out)],
                 timeout=240)
        return r.returncode == 0 and out.exists() and out.stat().st_size > 10_000
    x = 0.5
    if scene_durs and len(scene_durs) == n:
        segs = scene_durs
    else:
        seg = (duration + (n - 1) * x) / n
        segs = [seg] * n
    # Transition i overlaps the tail of scene i: offset = cumulative length
    # of scenes 1..i minus the i overlaps already consumed.
    offsets: List[float] = []
    acc = 0.0
    for i in range(1, n):
        acc += segs[i - 1]
        offsets.append(acc - i * x)
    inputs: List[str] = []
    for sp in scene_paths:
        inputs += ["-i", str(sp)]
    fc: List[str] = []
    prev = "[0:v]"
    for i in range(1, n):
        off = offsets[i - 1]
        lbl = "[bg]" if i == n - 1 else f"[x{i}]"
        fc.append(f"{prev}[{i}:v]xfade=transition={_TRANSITIONS[(i - 1) % len(_TRANSITIONS)]}"
                  f":duration={x}:offset={off:.3f}{lbl}")
        prev = lbl
    r = _run(["ffmpeg", "-y", *inputs, "-filter_complex", ";".join(fc),
              "-map", "[bg]", "-t", f"{duration:.2f}",
              "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p", str(out)],
             timeout=240)
    return r.returncode == 0 and out.exists() and out.stat().st_size > 10_000


# ── Music bed ─────────────────────────────────────────────────────────────────

def music_bed(duration: float, out: Path, music_dir: Optional[Path] = None) -> bool:
    """Bundled track if FYE_MUSIC_DIR/assets/music has mp3s, else procedural pad."""
    candidates = [p for p in (music_dir, Path("assets/music")) if p and p.exists()]
    bundled = sorted(candidates[0].glob("*.mp3")) if candidates else []
    if bundled:
        r = _run(["ffmpeg", "-y", "-stream_loop", "-1", "-i", str(_rng.choice(bundled)),
                  "-t", f"{duration:.2f}", "-af", "volume=0.14", "-c:a", "aac", str(out)], timeout=120)
        if r.returncode == 0 and out.exists():
            return True
    r = _run(["ffmpeg", "-y",
              "-f", "lavfi", "-i", f"sine=frequency=196:duration={duration:.2f}",
              "-f", "lavfi", "-i", f"sine=frequency=294:duration={duration:.2f}",
              "-filter_complex",
              "[0:a][1:a]amix=inputs=2,tremolo=f=5:d=0.4,lowpass=f=900,"
              "aecho=0.8:0.7:60:0.3,volume=0.09[a]",
              "-map", "[a]", "-c:a", "aac", str(out)], timeout=120)
    return r.returncode == 0 and out.exists() and out.stat().st_size > 1000


# ── Final compose ─────────────────────────────────────────────────────────────

def esc_drawtext(t: str) -> str:
    # '%' starts a drawtext expansion sequence — double it to print literally.
    return re.sub(r"([':\\])", r"\\\1", t.replace("%", "%%"))


def compose_master(bg: Path, vo: Optional[Path], ass: Optional[Path], music: Optional[Path],
                   title: str, out: Path, duration: float) -> bool:
    """bg video + captions + title banner + VO/music duck → master MP4."""
    filters = []
    if title:
        banner = " ".join(_wrap_text(title.upper(), width=22, max_lines=1))
        filters.append(
            f"drawtext=fontfile={FONT}:text='{esc_drawtext(banner)}':fontsize=54:"
            f"fontcolor=white:borderw=4:bordercolor=black@0.6:x=(w-text_w)/2:y=140")
    if ass and ass.exists():
        filters.append(f"subtitles='{ass.as_posix().replace(':', chr(92) + ':')}'")
    vf = f"[0:v]{','.join(filters)}[v]" if filters else "[0:v]copy[v]"

    inputs = ["-i", str(bg)]
    afc, mix, n_in = "", "", 1
    if vo and vo.exists():
        inputs += ["-i", str(vo)]
        afc += "[1:a]volume=1.0[vo];"
        mix = "[vo]"
        n_in = 1
    if music and music.exists():
        inputs += ["-i", str(music)]
        mi = len(inputs) // 2 - 1  # inputs are [-i, path] pairs; index = pairs - 1
        afc += f"[{mi}:a]volume=0.5[mu];"
        mix += "[mu]"
        n_in += 1
    if mix:
        afc += f"{mix}amix=inputs={n_in}:duration=first:dropout_transition=0:normalize=0[a]"
        maps = ["-map", "[v]", "-map", "[a]"]
    else:
        maps = ["-map", "[v]"]

    cmd = ["ffmpeg", "-y", *inputs, "-filter_complex", vf + ";" + afc if afc else vf,
           *maps, "-t", f"{duration:.2f}", "-c:v", "libx264", "-preset", "veryfast",
           "-crf", "22", "-pix_fmt", "yuv420p"]
    if mix:
        cmd += ["-c:a", "aac", "-b:a", "160k"]
    cmd += ["-movflags", "+faststart", str(out)]
    r = _run(cmd, timeout=300)
    return r.returncode == 0 and out.exists() and out.stat().st_size > 20_000
