"""EAOS POD image factory.

Renders 4500x5400 px, 300 DPI print-on-demand artwork for Printify/Printful.
The catalog metadata is also used to build Etsy-ready listing packs.
"""
from __future__ import annotations

import logging
import os
import sqlite3
from typing import Any

logger = logging.getLogger("EAOS.ImageFactory")

try:
    from PIL import Image, ImageDraw, ImageFont
    _HAS_PILLOW = True
except ImportError:
    _HAS_PILLOW = False
    logger.warning("[ImageFactory] Pillow not installed - install with: pip install pillow")

WORKSPACE = os.environ.get("EAOS_POD_ROOT", "./datacenter/pod_factory")
DB_PATH = os.environ.get("EAOS_POD_DB", "./datacenter/pod_cache.db")

PALETTES = {
    "cyber": {"bg": (0, 0, 0, 0), "text": (0, 255, 192, 255), "accent": (255, 255, 255, 255)},
    "bold": {"bg": (0, 0, 0, 0), "text": (255, 255, 255, 255), "accent": (255, 80, 0, 255)},
    "midnight": {"bg": (10, 10, 30, 255), "text": (255, 255, 255, 255), "accent": (0, 180, 255, 255)},
    "gold": {"bg": (0, 0, 0, 0), "text": (255, 215, 0, 255), "accent": (255, 255, 255, 255)},
    "vault": {"bg": (0, 0, 0, 0), "text": (210, 245, 255, 255), "accent": (45, 212, 191, 255)},
    "culture": {"bg": (0, 0, 0, 0), "text": (255, 244, 214, 255), "accent": (244, 63, 94, 255)},
}

SKU_CATALOG = [
    {
        "sku": "AHL-001",
        "title": "Already Here",
        "subtitle": "For builders who move before the room catches up",
        "palette": "culture",
        "etsy_title": "Already Here Builder T-Shirt, Founder Shirt, Creator Gift, Startup Tee",
        "description": (
            "A clean statement tee for founders, creators, operators, and builders who are already moving. "
            "Printed on demand and made for everyday work, launch days, and late-night build sessions."
        ),
        "tags": ["founder shirt", "startup tee", "creator gift", "builder shirt", "operator tee", "tech founder", "business gift", "hustle shirt", "minimal tee", "work shirt", "entrepreneur", "already here", "ai builder"],
    },
    {
        "sku": "AHL-002",
        "title": "Profit Engine",
        "subtitle": "Build systems. Ship value. Track proof.",
        "palette": "bold",
        "etsy_title": "Profit Engine T-Shirt, Entrepreneur Shirt, Business Owner Gift",
        "description": (
            "A sharp operator tee for people building real income systems. Designed for entrepreneurs, "
            "small business owners, and creators who care about proof, output, and momentum."
        ),
        "tags": ["profit engine", "business shirt", "entrepreneur", "owner gift", "startup shirt", "operator tee", "founder gift", "side hustle", "income system", "creator shirt", "workwear", "launch shirt", "money mindset"],
    },
    {
        "sku": "AHL-003",
        "title": "Sovereign AI",
        "subtitle": "Human-led systems for autonomous work",
        "palette": "midnight",
        "etsy_title": "Sovereign AI T-Shirt, AI Builder Shirt, Automation Engineer Gift",
        "description": (
            "A premium-feel AI automation shirt for builders who keep the human in charge. Made for prompt "
            "engineers, automation builders, founders, and technical operators."
        ),
        "tags": ["ai shirt", "automation", "prompt engineer", "ai builder", "tech gift", "engineer gift", "founder shirt", "sovereign ai", "developer tee", "startup tee", "operator", "machine learning", "techwear"],
    },
    {
        "sku": "AHL-004",
        "title": "Proof First",
        "subtitle": "No hype. Ledger before launch.",
        "palette": "gold",
        "etsy_title": "Proof First T-Shirt, No Hype Founder Shirt, Business Ledger Tee",
        "description": (
            "For operators who would rather show receipts than make noise. A founder and builder shirt built "
            "around proof of work, verified revenue, and honest momentum."
        ),
        "tags": ["proof of work", "founder shirt", "no hype", "ledger", "operator tee", "startup gift", "business owner", "builder gift", "creator tee", "honest work", "revenue", "launch day", "minimal shirt"],
    },
    {
        "sku": "AHL-005",
        "title": "Design Vault",
        "subtitle": "Useful assets for useful work",
        "palette": "vault",
        "etsy_title": "Design Vault T-Shirt, Designer Gift, Creative Operator Shirt",
        "description": (
            "A clean creative-ops shirt for designers, makers, and digital product builders. Built for the Fly "
            "Design Vault audience and anyone turning ideas into usable assets."
        ),
        "tags": ["design vault", "designer gift", "creative shirt", "digital product", "maker shirt", "asset shop", "etsy seller", "creator gift", "brand design", "minimal tee", "operator", "print on demand", "fly design"],
    },
    {
        "sku": "AHL-006",
        "title": "Build And Ship",
        "subtitle": "Less waiting. More finished work.",
        "palette": "bold",
        "etsy_title": "Build And Ship T-Shirt, Maker Shirt, Developer Gift, Launch Day Tee",
        "description": (
            "A direct, no-fluff shirt for makers who finish. Good for developers, founders, creators, and "
            "anyone who prefers shipped work over endless planning."
        ),
        "tags": ["build and ship", "developer gift", "maker shirt", "launch day", "ship it", "founder tee", "creator shirt", "startup gift", "builder gift", "operator tee", "productivity", "work shirt", "coding shirt"],
    },
    {
        "sku": "AHL-007",
        "title": "AI Stack",
        "subtitle": "Tools change. Builders compound.",
        "palette": "cyber",
        "etsy_title": "AI Stack T-Shirt, Developer Shirt, Automation Builder Gift",
        "description": (
            "A technical shirt for people building with AI tools, automations, agents, and workflows. Designed "
            "as a simple uniform for modern builders."
        ),
        "tags": ["ai stack", "developer shirt", "automation gift", "ai tools", "agent builder", "tech founder", "coding gift", "software shirt", "prompt engineer", "builder tee", "workflow", "startup tee", "techwear"],
    },
    {
        "sku": "AHL-008",
        "title": "Already Paid",
        "subtitle": "Systems working while you build the next one",
        "palette": "gold",
        "etsy_title": "Already Paid T-Shirt, Entrepreneur Tee, Passive Income Builder Shirt",
        "description": (
            "A confident builder tee for people creating products, services, stores, and income paths. It is "
            "about systems, receipts, and momentum, not empty promises."
        ),
        "tags": ["already paid", "income builder", "entrepreneur", "side hustle", "business shirt", "founder gift", "operator tee", "passive income", "creator shirt", "money systems", "startup tee", "proof first", "builder shirt"],
    },
]


class PODJournal:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS pod_products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sku TEXT UNIQUE,
                    file_path TEXT,
                    printify_id TEXT,
                    status TEXT DEFAULT 'RENDERED',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
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
        names = ["DejaVuSans-Bold.ttf", "arialbd.ttf", "segoeuib.ttf", "Arial Bold.ttf"] if bold else [
            "DejaVuSans.ttf", "arial.ttf", "segoeui.ttf", "Arial.ttf",
        ]
        search = [
            "/usr/share/fonts/truetype/dejavu/",
            "/usr/share/fonts/truetype/",
            "/usr/share/fonts/",
            "/System/Library/Fonts/",
            "C:/Windows/Fonts/",
            os.path.expanduser("~/fonts/"),
            "./",
        ]
        for name in names:
            for path in search:
                full = os.path.join(path, name)
                if os.path.exists(full):
                    try:
                        return ImageFont.truetype(full, size)
                    except Exception as exc:
                        logger.debug("Font load failed for %s: %s", full, exc)
                        continue
        return ImageFont.load_default()

    def _wrap_text(self, text: str, font: Any, max_width: int) -> list[str]:
        words = text.split()
        lines: list[str] = []
        current: list[str] = []
        for word in words:
            test = " ".join(current + [word])
            bbox = font.getbbox(test)
            if bbox[2] - bbox[0] <= max_width:
                current.append(word)
            else:
                if current:
                    lines.append(" ".join(current))
                current = [word]
        if current:
            lines.append(" ".join(current))
        return lines

    def construct_apparel_artwork(self, sku: str, title: str, subtitle: str, palette: str = "cyber") -> str:
        if not _HAS_PILLOW:
            logger.error("[ImageFactory] Pillow not available")
            return ""

        pal = PALETTES.get(palette, PALETTES["cyber"])
        width, height = 4500, 5400
        img = Image.new("RGBA", (width, height), pal["bg"])
        draw = ImageDraw.Draw(img)

        border = 210
        draw.rectangle([border, border, width - border, height - border], outline=pal["accent"], width=24)
        draw.rectangle([border + 60, border + 60, width - border - 60, border + 126], fill=pal["accent"])

        title_font = self._load_font(330, bold=True)
        y = 1030
        for line in self._wrap_text(title.upper(), title_font, width - 680):
            bbox = title_font.getbbox(line)
            draw.text(((width - (bbox[2] - bbox[0])) // 2, y), line, fill=pal["text"], font=title_font)
            y += 370

        y += 70
        draw.line([(720, y), (width - 720, y)], fill=pal["accent"], width=18)
        y += 155

        subtitle_font = self._load_font(142)
        for line in self._wrap_text(subtitle, subtitle_font, width - 860):
            bbox = subtitle_font.getbbox(line)
            draw.text(((width - (bbox[2] - bbox[0])) // 2, y), line, fill=(218, 218, 218, 255), font=subtitle_font)
            y += 192

        brand_font = self._load_font(96)
        brand = "Already Here LLC"
        bbox = brand_font.getbbox(brand)
        draw.text(((width - (bbox[2] - bbox[0])) // 2, height - 360), brand, fill=(160, 160, 160, 210), font=brand_font)

        out = os.path.join(self.output_dir, f"{sku}_artwork.png")
        img.save(out, "PNG", dpi=(300, 300))
        logger.info("[ImageFactory] %s rendered -> %s", sku, out)
        self.journal.record(sku, out)
        return os.path.abspath(out)

    def render_full_catalog(self) -> list[str]:
        paths = []
        for item in SKU_CATALOG:
            path = self.construct_apparel_artwork(item["sku"], item["title"], item["subtitle"], item["palette"])
            if path:
                paths.append(path)
        return paths


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    rendered = ProductionImageFactory().render_full_catalog()
    logger.info("POD catalog render complete: %s files", len(rendered))
