from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


def slugify(value: str, fallback: str = "profitengine-asset", limit: int = 80) -> str:
    slug = re.sub(r"[^a-z0-9-]", "-", value.lower())
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug[:limit] or fallback


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


@dataclass(frozen=True)
class ContentAssetPack:
    topic: str
    canonical_url: str
    output_dir: Path

    @property
    def slug(self) -> str:
        return slugify(self.topic)

    def scene_plan(self) -> list[dict[str, str]]:
        topic = clean_text(self.topic)
        return [
            {
                "headline": topic,
                "body": "Turn one useful article into a video, offer, affiliate campaign, and reusable sales asset.",
                "visual_prompt": f"clean modern business dashboard, content automation, {topic}, vertical social video",
            },
            {
                "headline": "Faceless video automation",
                "body": "Create short vertical videos without a camera crew, studio, or manual editing session.",
                "visual_prompt": "faceless content studio, automated video workflow, timeline, subtitles, creator tools",
            },
            {
                "headline": "Affiliate-ready content",
                "body": "Each asset can route attention back to monetized articles, tools, and digital products.",
                "visual_prompt": "affiliate marketing funnel, digital products, conversion paths, useful online tools",
            },
            {
                "headline": "Small business leverage",
                "body": "Already Here LLC turns repeatable workflows into practical automation infrastructure.",
                "visual_prompt": "small business owner using AI dashboard, operations, practical automation",
            },
            {
                "headline": "24/7 distribution",
                "body": "Publish to active channels when credentials are connected, then keep the source asset reusable.",
                "visual_prompt": "social media distribution network, YouTube, Telegram, short video publishing",
            },
            {
                "headline": "Next action",
                "body": "Use the article, video, product idea, and social post together instead of leaving content unused.",
                "visual_prompt": "checklist completed, launch dashboard, packaged digital product ready to sell",
            },
        ]

    def subtitle_text(self) -> str:
        return "\n".join(scene["body"] for scene in self.scene_plan())

    def _write(self, relative_name: str, content: str) -> str:
        path = self.output_dir / relative_name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return str(path)

    def write_all(self) -> dict[str, str]:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        files = {
            "blog_brief": self._write("blog-brief.md", self._blog_brief()),
            "ebook": self._write("mini-ebook.md", self._mini_ebook()),
            "manual": self._write("implementation-manual.md", self._manual()),
            "self_help": self._write("self-help-checklist.md", self._self_help_checklist()),
            "caption_pack": self._write("social-caption-pack.json", self._caption_pack()),
            "video_script": self._write("video-script.md", self._video_script()),
        }
        return files

    def capability_manifest(self, *, hf_token_present: bool, hf_image_enabled: bool, ffmpeg_present: bool) -> dict[str, Any]:
        return {
            "topic": self.topic,
            "canonical_url": self.canonical_url,
            "capabilities": {
                "faceless_mp4": {"status": "live", "engine": "ffmpeg_pillow"},
                "ai_written_assets": {"status": "live", "outputs": ["blog", "ebook", "manual", "self_help", "captions"]},
                "huggingface_text_provider": {"status": "configured" if hf_token_present else "missing_secret"},
                "huggingface_image_scenes": {
                    "status": "enabled" if hf_token_present and hf_image_enabled else "deterministic_fallback",
                    "engine": "black-forest-labs/FLUX.1-schnell",
                },
                "huggingface_tts": {"status": "available_to_runtime" if hf_token_present else "silent_audio_fallback"},
                "talking_head_avatar": {
                    "status": "not_installed",
                    "reason": "requires a licensed avatar/lip-sync provider or approved local model endpoint",
                },
                "capcut_equivalent_editor": {
                    "status": "partial_backend_only",
                    "live_parts": ["script", "slides", "captions", "mp4", "social_distribution"],
                    "missing_parts": ["timeline_ui", "avatar_clone", "stock_broll_library", "template_marketplace"],
                },
                "ffmpeg": {"status": "present" if ffmpeg_present else "missing"},
            },
        }

    def _blog_brief(self) -> str:
        return f"""# {self.topic}

## Search Intent
Readers want a practical path from idea to revenue asset without needing a production team.

## Angle
Show how to turn one topic into a reusable article, short video, product checklist, and social campaign.

## Recommended Structure
1. Define the buyer problem.
2. Explain the repeatable content-to-video workflow.
3. Show the asset stack: article, video, checklist, offer, social post.
4. Add monetization paths: affiliate, Gumroad, service setup, newsletter.
5. Close with a clear next step.

## CTA
See the full automation stack at {self.canonical_url}
"""

    def _mini_ebook(self) -> str:
        return f"""# {self.topic}: Mini eBook

## Chapter 1: The Leverage Point
One useful topic can become more than a post. It can become a blog article, short video, social thread, lead magnet, and service offer.

## Chapter 2: The Production System
Start with a single buyer question. Convert it into a structured article, then extract the strongest points into short video scenes and captions.

## Chapter 3: The Revenue Stack
Attach one monetization path to every asset: affiliate link, digital download, setup service, or consultation request.

## Chapter 4: The Distribution Loop
Publish the core asset first, then distribute derivative assets to channels that already have credentials and proof tracking.

## Chapter 5: The Operating Rule
Never create content that cannot point to a next action. Every asset should teach, prove, or route.
"""

    def _manual(self) -> str:
        return f"""# Implementation Manual: {self.topic}

## Inputs
- Topic: {self.topic}
- Primary destination: {self.canonical_url}
- Output formats: blog, MP4, captions, mini eBook, checklist, social post

## Workflow
1. Generate or approve the article topic.
2. Produce the article and affiliate-safe CTA.
3. Build the video scene plan.
4. Render the MP4 and validate size/type.
5. Publish the video to public hosting.
6. Send to connected channels.
7. Save written assets for reuse as products or lead magnets.

## Quality Gate
- MP4 must be a real video file.
- Social posting must log sent/uploaded/skipped states.
- Missing credentials must not fail the pipeline.
- Avatar/talking-head generation must remain disabled until a real provider is connected.
"""

    def _self_help_checklist(self) -> str:
        return f"""# Self-Help Action Checklist: {self.topic}

- Pick one specific audience.
- Write the buyer problem in one sentence.
- Create one useful article that solves part of the problem.
- Convert the article into six short video scenes.
- Add one clear CTA to every asset.
- Package the checklist or manual as a downloadable product.
- Publish only to verified channels.
- Review outcomes weekly and improve the next topic.
"""

    def _caption_pack(self) -> str:
        captions = {
            "youtube": f"{self.topic}\n\nA practical automation workflow from article to video to reusable revenue assets.\n\n{self.canonical_url}",
            "telegram": f"New ProfitEngine video: {self.topic}\n\nWatch/read: {self.canonical_url}",
            "linkedin": f"One topic can become a blog, short video, checklist, offer, and social post. Here is the system behind {self.topic}: {self.canonical_url}",
            "x": f"{self.topic}: one article, one video, one reusable asset stack. {self.canonical_url}",
            "hashtags": ["ProfitEngine", "AlreadyHereLLC", "AITools", "PassiveIncome", "ContentAutomation"],
        }
        return json.dumps(captions, indent=2, sort_keys=True)

    def _video_script(self) -> str:
        lines = [f"# Video Script: {self.topic}", ""]
        for index, scene in enumerate(self.scene_plan(), start=1):
            lines.append(f"## Scene {index}: {scene['headline']}")
            lines.append(scene["body"])
            lines.append("")
        return "\n".join(lines)
