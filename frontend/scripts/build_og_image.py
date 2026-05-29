"""
Generate /app/frontend/public/og.png — the 1200×630 social share image
used by Open Graph (Facebook/LinkedIn) and Twitter/X card previews.

Aesthetic mirrors the dashboard:
  bg #0a0e1a · ink #f3f4f6 · ok #22c55e (green) · sov #a78bfa (purple)
  Liberation Mono (close stand-in for JetBrains Mono used by the app).

Re-run: `python3 scripts/build_og_image.py`
"""
from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


WIDTH, HEIGHT = 1200, 630
BG = (10, 14, 26, 255)          # #0a0e1a
PANEL = (15, 21, 37, 255)        # #0f1525
INK = (243, 244, 246, 255)       # #f3f4f6
INK_MUTED = (148, 163, 184, 255) # slate-400
INK_FAINT = (100, 116, 139, 255) # slate-500
OK = (34, 197, 94, 255)          # #22c55e
SOV = (167, 139, 250, 255)       # #a78bfa
LINE = (30, 41, 59, 255)         # #1e293b


def _font(size: int, *, bold: bool = False) -> ImageFont.FreeTypeFont:
    weight = "Bold" if bold else "Regular"
    path = f"/usr/share/fonts/truetype/liberation/LiberationMono-{weight}.ttf"
    return ImageFont.truetype(path, size)


def _grid(draw: ImageDraw.ImageDraw) -> None:
    """Faint vertical/horizontal hairlines for the command-OS feel."""
    step = 60
    for x in range(0, WIDTH, step):
        draw.line([(x, 0), (x, HEIGHT)], fill=(18, 24, 41, 255), width=1)
    for y in range(0, HEIGHT, step):
        draw.line([(0, y), (WIDTH, y)], fill=(18, 24, 41, 255), width=1)


def _pill(draw: ImageDraw.ImageDraw, *, x: int, y: int, label: str,
          color: tuple, font: ImageFont.FreeTypeFont,
          fill_bg: tuple | None = None, pad: int = 14) -> int:
    """Bordered uppercase pill (returns its right-edge x)."""
    bbox = draw.textbbox((0, 0), label, font=font)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    box = [x, y, x + w + pad * 2, y + h + 14]
    if fill_bg:
        draw.rectangle(box, fill=fill_bg, outline=color, width=1)
    else:
        draw.rectangle(box, outline=color, width=1)
    draw.text((x + pad, y + 6), label, fill=color, font=font)
    return box[2]


def build() -> Path:
    img = Image.new("RGBA", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(img)

    _grid(draw)

    # ── Left rail accent
    draw.rectangle([0, 0, 6, HEIGHT], fill=OK)

    # ── Top bar — wordmark + status
    draw.text((44, 38), ">_", fill=OK, font=_font(28, bold=True))
    draw.text((90, 36), "PROFIT", fill=INK, font=_font(28, bold=True))
    draw.text((90 + 110, 36), "ENGINE", fill=OK, font=_font(28, bold=True))
    draw.text((90 + 110 + 130, 38), "v5", fill=INK_FAINT, font=_font(22))

    # status pills (top-right)
    pill_font = _font(13, bold=True)
    x = WIDTH - 44
    label = "● ALL SYSTEMS OPERATIONAL"
    bbox = draw.textbbox((0, 0), label, font=pill_font)
    w = bbox[2] - bbox[0]
    x -= w + 28
    _pill(draw, x=x, y=34, label=label, color=OK, font=pill_font, pad=14)

    # ── Eyebrow
    draw.text((44, 130), "// COMMAND OS · ENTERPRISE",
              fill=OK, font=_font(15, bold=True))

    # ── H1 — large, three-line headline
    h1_font = _font(72, bold=True)
    draw.text((44, 168), "Enterprise", fill=INK, font=h1_font)
    draw.text((44, 248), "controlled autonomy", fill=OK, font=h1_font)
    draw.text((44, 328), "for revenue.", fill=INK, font=h1_font)

    # ── Subline
    sub = "20 AI agents · L3 bounded autonomy · 80%+ token-distilled · open core"
    draw.text((44, 430), sub, fill=INK_MUTED, font=_font(20))

    # ── Bottom strip — meta pills + CTA URL
    bottom_y = HEIGHT - 78
    line_y = bottom_y - 20
    draw.line([(44, line_y), (WIDTH - 44, line_y)], fill=LINE, width=1)

    pf = _font(12, bold=True)
    cursor = 44
    cursor = _pill(draw, x=cursor, y=bottom_y, label="PRIME ORCHESTRATOR",
                   color=SOV, font=pf, pad=12) + 12
    cursor = _pill(draw, x=cursor, y=bottom_y, label="ZERO-TRUST HARDENED",
                   color=INK_MUTED, font=pf, pad=12) + 12
    cursor = _pill(draw, x=cursor, y=bottom_y, label="$0/MO FIXED COST",
                   color=OK, font=pf, pad=12) + 12
    cursor = _pill(draw, x=cursor, y=bottom_y, label="COHORT 1 OPEN",
                   color=OK, font=pf, pad=12, fill_bg=(8, 32, 18, 255)) + 12

    # right-aligned URL
    url_font = _font(16, bold=True)
    url = "profitengine.dev"
    bbox = draw.textbbox((0, 0), url, font=url_font)
    w = bbox[2] - bbox[0]
    draw.text((WIDTH - 44 - w, bottom_y + 6), url, fill=INK, font=url_font)

    # ── Corner crosshair (top-right inset accent)
    cx, cy = WIDTH - 60, 90
    draw.line([(cx - 18, cy), (cx + 18, cy)], fill=OK, width=2)
    draw.line([(cx, cy - 18), (cx, cy + 18)], fill=OK, width=2)

    out_path = Path(__file__).resolve().parent.parent / "public" / "og.png"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.convert("RGB").save(out_path, format="PNG", optimize=True)
    return out_path


if __name__ == "__main__":
    path = build()
    print(f"✓ og.png written: {path} ({path.stat().st_size // 1024}kb)")
