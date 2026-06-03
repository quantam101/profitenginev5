"""
EAOS POD Image Factory — 4500×5400 px print-on-demand artwork generator.
Pure Pillow — no GPU required. Outputs 300 DPI PNG ready for Printify/Printful.
"""
import os
import json
import logging
import hashlib
import sqlite3
import asyncio
import urllib.request
import urllib.parse
from typing import List, Dict, Any, Optional

logger = logging.getLogger("EAOS.ImageFactory")

try:
    from PIL import Image, ImageDraw, ImageFont
    _HAS_PILLOW = True
except ImportError:
    _HAS_PILLOW = False
    logger.warning("[ImageFactory] Pillow not installed — install with: pip install pillow")

WORKSPACE = os.environ.get("EAOS_POD_ROOT", "./datacenter/pod_factory")
DB_PATH   = os.environ.get("EAOS_POD_DB",   "./datacenter/pod_cache.db")

# Design palette — high-contrast for dark-garment printing
PALETTES = {
    "cyber":    {"bg": (0, 0, 0, 0),       "text": (0, 255, 192, 255),   "accent": (255, 255, 255, 255)},
    "bold":     {"bg": (0, 0, 0, 0),       "text": (255, 255, 255, 255), "accent": (255, 80, 0, 255)},
    "midnight": {"bg": (10, 10, 30, 255),  "text": (255, 255, 255, 255), "accent": (0, 180, 255, 255)},
    "gold":     {"bg": (0, 0, 0, 0),       "text": (255, 215, 0, 255),   "accent": (255, 255, 255, 255)},
}

SKU_CATALOG = [
    {"sku": "AHL-001", "title": "ALREADY HERE", "subtitle": "AI-Powered Profit Engine · 2026", "palette": "cyber"},
    {"sku": "AHL-002", "title": "PROFIT ENGINE", "subtitle": "Building the Future. Automated.", "palette": "bold"},
    {"sku": "AHL-003", "title": "SOVEREIGN AI", "subtitle": "Zero Cost. Maximum Velocity.", "palette": "midnight"},
    {"sku": "AHL-004", "title": "PASSIVE INCOME", "subtitle": "While You Sleep · Already Here LLC", "palette": "gold"},
    {"sku": "AHL-005", "title": "TOKEN FORGE", "subtitle": "Multi-Model AI API Proxy · Free Tier", "palette": "cyber"},
    {"sku": "AHL-006", "title": "BUILD & SHIP", "subtitle": "Deploy Fast. Earn Faster.", "palette": "bold"},
    {"sku": "AHL-007", "title": "AI STACK", "subtitle": "Groq · Gemini · Claude · Local LLM", "palette": "midnight"},
    {"sku": "AHL-008", "title": "ALREADY PAID", "subtitle": "Automated Revenue · 24/7 Income", "palette": "gold"},
]


class PODJournal:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS pod_products (
                    id         INTEGER PRIMARY KEY AUTOINCREMENT,
                    sku        TEXT UNIQUE,
                    file_path  TEXT,
                    printify_id TEXT,
                    status     TEXT DEFAULT 'RENDERED',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def record(self, sku: str, file_path: str, printify_id: str = "") -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO pod_products (sku, file_path, printify_id, status) VALUES (?, ?, ?, ?)",
                (sku, file_path, printify_id, "PUSHED" if printify_id else "RENDERED"),
            )
            conn.commit()


class ProductionImageFactory:
    def __init__(self, workspace: str = WORKSPACE):
        self.output_dir = os.path.join(workspace, "render_cache")
        os.makedirs(self.output_dir, exist_ok=True)
        self.journal = PODJournal()

    def _load_font(self, size: int, bold: bool = False) -> Any:
        names = ["DejaVuSans-Bold.ttf", "DejaVuSans.ttf", "Arial.ttf", "Helvetica.ttf"] if bold \
            else ["DejaVuSans.ttf", "Arial.ttf", "Helvetica.ttf"]
        search = [
            "/usr/share/fonts/truetype/dejavu/",
            "/usr/share/fonts/truetype/",
            "/usr/share/fonts/",
            "/System/Library/Fonts/",
            os.path.expanduser("~/fonts/"),
            "./",
        ]
        for name in names:
            for path in search:
                full = os.path.join(path, name)
                if os.path.exists(full):
                    try:
                        return ImageFont.truetype(full, size)
                    except Exception:
                        pass
        return ImageFont.load_default()

    def _wrap_text(self, text: str, font: Any, max_width: int) -> List[str]:
        words = text.split()
        lines, cur = [], []
        for word in words:
            test = " ".join(cur + [word])
            w = font.getbbox(test)[2] - font.getbbox(test)[0]
            if w <= max_width:
                cur.append(word)
            else:
                if cur:
                    lines.append(" ".join(cur))
                cur = [word]
        if cur:
            lines.append(" ".join(cur))
        return lines

    def construct_apparel_artwork(self, sku: str, title: str, subtitle: str,
                                   palette: str = "cyber") -> str:
        if not _HAS_PILLOW:
            logger.error("[ImageFactory] Pillow not available")
            return ""

        pal = PALETTES.get(palette, PALETTES["cyber"])
        W, H = 4500, 5400

        img  = Image.new("RGBA", (W, H), pal["bg"])
        draw = ImageDraw.Draw(img)

        # Border
        B = 200
        draw.rectangle([B, B, W - B, H - B], outline=pal["accent"], width=25)

        # Top accent bar
        draw.rectangle([B + 50, B + 50, W - B - 50, B + 120], fill=pal["text"])

        # Title
        t_font = self._load_font(340, bold=True)
        t_lines = self._wrap_text(title.upper(), t_font, max_width=W - 600)
        y = 1000
        for line in t_lines:
            bx = t_font.getbbox(line)
            draw.text(((W - (bx[2] - bx[0])) // 2, y), line, fill=pal["text"], font=t_font)
            y += 380

        # Divider
        y += 80
        draw.line([(700, y), (W - 700, y)], fill=pal["accent"], width=18)
        y += 160

        # Subtitle
        s_font = self._load_font(160)
        for line in self._wrap_text(subtitle, s_font, max_width=W - 800):
            bx = s_font.getbbox(line)
            draw.text(((W - (bx[2] - bx[0])) // 2, y), line, fill=(200, 200, 200, 255), font=s_font)
            y += 210

        # Bottom brand mark
        b_font = self._load_font(100)
        brand = "alreadyherellc.com"
        bx = b_font.getbbox(brand)
        draw.text(((W - (bx[2] - bx[0])) // 2, H - 350), brand,
                  fill=(120, 120, 120, 180), font=b_font)

        out = os.path.join(self.output_dir, f"{sku}_artwork.png")
        img.save(out, "PNG", dpi=(300, 300))
        logger.info(f"[ImageFactory] {sku} rendered → {out}")
        self.journal.record(sku, out)
        return os.path.abspath(out)

    def render_full_catalog(self) -> List[str]:
        """Render every SKU in the catalog."""
        paths = []
        for item in SKU_CATALOG:
            path = self.construct_apparel_artwork(
                sku=item["sku"], title=item["title"],
                subtitle=item["subtitle"], palette=item["palette"],
            )
            if path:
                paths.append(path)
        return paths


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    factory = ProductionImageFactory()
    factory.render_full_catalog()
    logger.info("POD catalog render complete.")
