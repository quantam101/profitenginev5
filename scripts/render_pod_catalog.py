"""Render POD artwork for all 8 Already Here LLC SKUs.

Tries HuggingFace FLUX image generation first (real AI art, much higher
quality and conversion rate on Etsy). Falls back to the Pillow text render
if HF_TOKEN is missing or the API call fails.
"""
from __future__ import annotations

import os
import sys
import time
import urllib.error
import urllib.request
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from runtime.eaos.image_factory import ProductionImageFactory, SKU_CATALOG

# HuggingFace Inference — FLUX.1-schnell (free, fast, high quality)
# api-inference.huggingface.co was decommissioned; hf-inference now lives behind the router
HF_IMAGE_API = "https://router.huggingface.co/hf-inference/models/black-forest-labs/FLUX.1-schnell"
HF_TOKEN = os.getenv("HF_TOKEN", "").strip()

# Exact text each design must carry — FLUX renders typography unreliably
# (missing letters, garbled words), so every AI render is OCR-verified
# against this before it can ship. Failures fall back to Pillow, which
# renders text deterministically.
REQUIRED_TEXT = {
    "AHL-001": "ALREADY HERE",
    "AHL-002": "PROFIT ENGINE",
    "AHL-003": "ZERO COST OPERATOR",
    "AHL-004": "ALREADY HERE LLC",
    "AHL-005": "AUTONOMOUS",
    "AHL-006": "SHIP PROOF",
    "AHL-007": "SYSTEMS NOISE",
    "AHL-008": "ALREADY HERE",
}

# Prompt template per SKU
PROMPT_TEMPLATES = {
    "AHL-001": "minimalist streetwear graphic, bold text 'ALREADY HERE' on dark background, creator aesthetic, clean typography, print-on-demand tee design, 4500x5400",
    "AHL-002": "powerful entrepreneur graphic, 'PROFIT ENGINE' bold industrial text, dark background, money systems aesthetic, founder shirt design, print ready",
    "AHL-003": "stoic operator graphic, 'ZERO COST OPERATOR' minimal bold type, black background, tech founder aesthetic, high-contrast, Etsy print design",
    "AHL-004": "clean builder graphic, 'ALREADY HERE LLC' wordmark, dark minimal brand tee, founder culture, clean sans-serif, print-on-demand ready",
    "AHL-005": "AI builder culture graphic, 'AUTONOMOUS' bold type, cyber minimal aesthetic, dark background, tech startup tee, high resolution print art",
    "AHL-006": "creator economy graphic, 'SHIP PROOF' bold statement, dark brand tee, operator culture, clean design, Etsy listing ready",
    "AHL-007": "flow state graphic, 'SYSTEMS > NOISE' bold minimal type, black background, founder mindset tee, clean typography, print ready artwork",
    "AHL-008": "sovereign operator graphic, 'ALREADY HERE' arch text with stars, dark premium tee, creator culture, bold clean design, print-on-demand",
}


def _hf_generate_image(sku: str, prompt: str, dest: Path) -> bool:
    """Call HuggingFace FLUX API to generate artwork. Returns True on success."""
    if not HF_TOKEN:
        return False
    payload = json.dumps({"inputs": prompt, "parameters": {"width": 1024, "height": 1024}}).encode()
    req = urllib.request.Request(
        HF_IMAGE_API,
        data=payload,
        method="POST",
        headers={
            "Authorization": f"Bearer {HF_TOKEN}",
            "Content-Type": "application/json",
            "X-Use-Cache": "0",
        },
    )
    try:
        for attempt in range(3):
            try:
                with urllib.request.urlopen(req, timeout=120) as resp:  # noqa: S310
                    content_type = resp.headers.get("Content-Type", "")
                    data = resp.read()
                    if b"PNG" in data[:8] or b"\x89PNG" in data[:4] or "image" in content_type:
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        dest.write_bytes(data)
                        print(f"[HF] {sku} — FLUX image generated ({len(data)//1024}KB)")
                        return True
                    # Model loading response
                    try:
                        msg = json.loads(data)
                        if "estimated_time" in str(msg):
                            wait = float(str(msg).split("estimated_time")[1].split(",")[0].strip(": "))
                            print(f"[HF] {sku} — model loading, waiting {wait:.0f}s...")
                            time.sleep(min(wait + 2, 30))
                            continue
                    except Exception:
                        pass
                    print(f"[HF] {sku} — unexpected response type: {content_type}")
                    return False
            except urllib.error.HTTPError as exc:
                if exc.code == 503:
                    print(f"[HF] {sku} — model loading (503), retry {attempt+1}/3...")
                    time.sleep(20)
                    continue
                print(f"[HF] {sku} — HTTP {exc.code}: {exc.read().decode()[:200]}")
                return False
    except Exception as exc:
        print(f"[HF] {sku} — error: {exc}")
        return False
    return False


# Words FLUX tends to garble next to otherwise-correct text (LRADY, CREATER,
# FOUNTER...). Any OCR token within edit distance 2 of these — without being
# an exact match — fails the render even when the required words are present.
BRAND_VOCAB = {
    "ALREADY", "HERE", "PROFIT", "ENGINE", "ZERO", "COST", "OPERATOR",
    "AUTONOMOUS", "SHIP", "PROOF", "SYSTEMS", "NOISE", "CREATOR",
    "FOUNDER", "CULTURE", "SOVEREIGN", "ECONOMY",
}


def _edit_distance(a: str, b: str) -> int:
    if abs(len(a) - len(b)) > 2:
        return 3  # beyond our threshold, exact value irrelevant
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def _ocr_text_ok(dest: Path, required: str):
    """OCR the rendered image and verify every required word appears.

    Returns True/False, or None when OCR isn't installed (gate skipped so
    environments without tesseract keep the old behavior).
    """
    try:
        import pytesseract
        from PIL import Image, ImageOps
    except ImportError:
        print("[ocr] pytesseract not installed — gate skipped")
        return None
    words = ["".join(c for c in w if c.isalpha()) for w in required.upper().split()]
    needed = [w for w in words if len(w) > 2]
    seen: set = set()
    try:
        img = Image.open(dest).convert("L")
        # Tesseract's default mode misses white-on-dark poster text; sparse
        # segmentation (psm 11) and an inverted copy recover most of it.
        for variant in (img, ImageOps.invert(img)):
            for cfg in ("--psm 11", "--psm 3"):
                raw = pytesseract.image_to_string(variant, config=cfg).upper()
                seen |= set("".join(c if c.isalpha() else " " for c in raw).split())
    except Exception as exc:
        print(f"[ocr] unavailable ({exc}) — gate skipped")
        return None
    missing = [w for w in needed if w not in seen]
    if missing:
        print(f"[ocr] missing {missing} in render (saw: {sorted(seen)[:12]})")
        return False
    garbled = sorted(
        t for t in seen
        if len(t) >= 4 and t not in BRAND_VOCAB
        and any(_edit_distance(t, v) <= 2 for v in BRAND_VOCAB)
    )
    if garbled:
        print(f"[ocr] near-miss garble {garbled} in render — rejecting")
        return False
    return True


def main() -> int:
    factory = ProductionImageFactory()
    target = os.getenv("TARGET_SKU", "").strip()
    use_hf = bool(HF_TOKEN)

    if use_hf:
        print(f"[render] HF_TOKEN present — will attempt FLUX image generation first")
    else:
        print("[render] No HF_TOKEN — using Pillow text render")

    catalog = [item for item in SKU_CATALOG if not target or item["sku"] == target]
    if target and not catalog:
        print(f"SKU {target} not found")
        return 1

    pod_root = Path(os.getenv("EAOS_POD_ROOT", "./datacenter/pod_factory"))
    render_dir = pod_root / "render_cache"
    render_dir.mkdir(parents=True, exist_ok=True)

    paths = []
    for item in catalog:
        sku = item["sku"]
        dest = render_dir / f"{sku}_artwork.png"
        generated = False

        if use_hf:
            prompt = PROMPT_TEMPLATES.get(sku, f"bold print-on-demand tee design, {item['title']}, dark background, minimal typography")
            required = REQUIRED_TEXT.get(sku, "")
            for attempt in range(2):
                generated = _hf_generate_image(sku, prompt, dest)
                if not generated or not required:
                    break
                ok = _ocr_text_ok(dest, required)
                if ok is not False:
                    break
                print(f"[ocr] {sku} — FLUX typography failed validation (attempt {attempt + 1}/2)")
                generated = False

        if not generated:
            print(f"[render] {sku} — using Pillow fallback")
            path = factory.construct_apparel_artwork(sku, item["title"], item["subtitle"], item["palette"])
            paths.append(path)
        else:
            paths.append(str(dest))

    print(f"Rendered {len(paths)} SKUs")
    for p in paths:
        print(f"  {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
