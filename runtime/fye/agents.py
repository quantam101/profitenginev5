"""
FYE per-process agents. Each process gets exactly one agent; the
FyeOrchestrator (the supervising AI) runs them in order and journals
every gate decision.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import re
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .config import FyeConfig
from .rpm_priors import prior_for, revenue_band, ypp_gate

logger = logging.getLogger("fye.agents")


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:48]


def xml_escape(text: str) -> str:
    return (text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;").replace("'", "&#39;"))


class ResearchAgent:
    """Picks niche/topic and attaches honest RPM planning priors."""
    name = "research"

    def run(self, ctx: Dict[str, Any]) -> Dict[str, Any]:
        niche = ctx.get("niche") or "science-explainer"
        topic = ctx.get("topic") or "Untitled explainer"
        prior = prior_for(niche)
        views_target = int(ctx.get("monthly_views_target", 100_000))
        result = {
            "niche": niche,
            "topic": topic,
            # Labeled planning priors — never surfaced as promised revenue.
            "rpm_prior": {"low": prior.rpm_low, "high": prior.rpm_high, "note": prior.note},
            "revenue_band": revenue_band(niche, views_target),
            "ypp": ypp_gate(
                subscribers=int(ctx.get("subscribers", 0)),
                watch_hours=float(ctx.get("watch_hours", 0)),
                shorts_views=int(ctx.get("shorts_views", 0)),
            ),
        }
        result["publish_blocked_by_ypp"] = not result["ypp"]["eligible"]
        return result


class ScriptAgent:
    """Deterministic offline script: hook → beats → CTA. No placeholders."""
    name = "script"

    def run(self, ctx: Dict[str, Any]) -> Dict[str, Any]:
        research = ctx["research"]
        topic, niche = research["topic"], research["niche"]
        title = ctx.get("title") or f"{topic} — Explained in 5 Minutes"
        sentences = [
            f"{topic} is one of those ideas that sounds simple until you actually try to apply it.",
            f"In this video we break down how {topic} really works, step by step.",
            f"First, the core mechanic: {topic} lives or dies on consistency, not intensity.",
            "Second, the compounding effect — small improvements stack faster than big bets.",
            "Third, the failure mode most people ignore until it costs them months.",
            f"By the end you will have a working mental model of {niche.replace('-', ' ')} applied to {topic}.",
            "If this helped, subscribe — the next breakdown builds directly on this one.",
        ]
        body = " ".join(sentences)
        return {
            "title": title[:100],
            "hook": sentences[0],
            "script_sentences": sentences,
            "script_body": body,
            "description": (
                f"{body[:300]}...\n\n"
                "This video contains AI-generated media. "
                "Revenue figures are planning estimates, not guarantees."
            ),
            "tags": [niche, "explainer", "already-here-llc"],
        }


class ShotListAgent:
    """
    Emits a shot list artifact. Runway/Pika are paid, API-gated, and
    volatile — FYE produces the shot list a human executes there rather
    than faking that automation.
    """
    name = "shots"

    def run(self, ctx: Dict[str, Any]) -> Dict[str, Any]:
        sentences: List[str] = ctx["script"]["script_sentences"]
        shots = []
        for i, line in enumerate(sentences, 1):
            shots.append({
                "shot": i,
                "duration_s": max(3, min(8, len(line) // 15)),
                "visual_prompt": line[:120],
                "motion_source": "manual:runway-or-pika",
                "fallback": "local-slideshow",
                "notes": "Manual step: Runway/Pika exports land in the package dir as scene_XXX.mp4.",
            })
        return {"shots": shots, "shot_count": len(shots)}


class StillsAgent:
    """
    Automated stills path: Flux on Replicate (opt-in, paid). When disabled
    by config or zero-spend policy, renders real styled title-card stills
    locally — actual image files, not placeholders.
    """
    name = "stills"

    def __init__(self, cfg: FyeConfig) -> None:
        self.cfg = cfg

    def _flux_still(self, prompt: str, out_path: Path) -> bool:
        if not self.cfg.replicate_enabled:
            return False
        try:
            payload = json.dumps({
                "input": {"prompt": prompt[:500], "aspect_ratio": "9:16",
                          "output_format": "png"},
            }).encode()
            req = urllib.request.Request(
                "https://api.replicate.com/v1/models/"
                f"{self.cfg.replicate_model}/predictions",
                data=payload, method="POST", headers={
                    "Authorization": f"Bearer {self.cfg.replicate_token}",
                    "Content-Type": "application/json",
                    "Prefer": "wait=60",
                })
            with urllib.request.urlopen(req, timeout=90) as r:
                result = json.loads(r.read() or b"{}")
            output = result.get("output")
            url = output[0] if isinstance(output, list) and output else output
            if not url:
                return False
            with urllib.request.urlopen(str(url), timeout=60) as r:
                out_path.write_bytes(r.read())
            return out_path.stat().st_size > 1000
        except Exception as exc:
            logger.warning("[Stills] Flux failed (%s) — local render", exc)
            return False

    def _local_still(self, text: str, out_path: Path, idx: int) -> bool:
        """Deterministic SVG title card — real renderable still, zero spend."""
        hue = (idx * 47) % 360
        words = xml_escape(text[:90])
        svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="1920">'
            f'<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">'
            f'<stop offset="0" stop-color="hsl({hue},55%,14%)"/>'
            f'<stop offset="1" stop-color="hsl({(hue+40)%360},60%,26%)"/>'
            f'</linearGradient></defs>'
            f'<rect width="1080" height="1920" fill="url(#g)"/>'
            f'<text x="540" y="960" font-family="sans-serif" font-size="56" '
            f'fill="#ffffff" text-anchor="middle">'
        )
        # crude wrap at ~24 chars
        wrapped, line = [], ""
        for w in words.split():
            if len(line) + len(w) > 24:
                wrapped.append(line)
                line = w
            else:
                line = f"{line} {w}".strip()
        if line:
            wrapped.append(line)
        for j, wline in enumerate(wrapped[:8]):
            dy = (j - len(wrapped[:8]) // 2) * 72
            svg += f'<tspan x="540" dy="{dy if j else 0}">{wline}</tspan>'
        svg += "</text></svg>"
        out_path.write_text(svg, encoding="utf-8")
        return True

    def run(self, ctx: Dict[str, Any]) -> Dict[str, Any]:
        """Priority per shot: stock B-roll clip > Flux still (opt-in) > SVG card.
        B-roll entries carry an mp4 path the assembly agent renders directly."""
        from . import media

        stills_dir = Path(ctx["pkg_dir"]) / "stills"
        stills_dir.mkdir(parents=True, exist_ok=True)
        rendered = []
        used_broll = False
        for shot in ctx["shots"]["shots"]:
            i = shot["shot"]
            prompt = shot["visual_prompt"]
            if self.cfg.broll_enabled:
                query = " ".join(prompt.split()[:4])
                broll_path = stills_dir / f"shot_{i:03d}.mp4"
                src = media.fetch_broll(query, broll_path,
                                        self.cfg.pexels_key, self.cfg.pixabay_key)
                if src:
                    rendered.append({"shot": i, "path": os.fspath(broll_path),
                                     "source": src, "kind": "broll"})
                    used_broll = True
                    continue
            if self.cfg.replicate_enabled:
                flux_path = stills_dir / f"shot_{i:03d}.png"
                if self._flux_still(prompt, flux_path):
                    rendered.append({"shot": i, "path": os.fspath(flux_path),
                                     "source": "flux", "kind": "still"})
                    continue
            svg_path = stills_dir / f"shot_{i:03d}.svg"
            if self._local_still(prompt, svg_path, i):
                rendered.append({"shot": i, "path": os.fspath(svg_path),
                                 "source": "local-svg", "kind": "still"})
        source = ("broll" if used_broll else
                  "flux" if self.cfg.replicate_enabled else "local-svg")
        return {"stills": rendered, "source": source}


class VoiceoverAgent:
    """Voice cascade: edge-tts neural voice (word timings) → HF TTS → silent."""
    name = "voiceover"

    def run(self, ctx: Dict[str, Any]) -> Dict[str, Any]:
        from . import media
        from ..eaos import video_engine  # lazy: heavy module

        audio_dir = Path(ctx["pkg_dir"]) / "audio"
        audio_dir.mkdir(parents=True, exist_ok=True)
        text = ctx["script"]["script_body"]
        duration = sum(s["duration_s"] for s in ctx["shots"]["shots"])
        words: List[Any] = []
        provider = "silent"

        # Tier 1: edge-tts neural voice — free, no key, word-level timings.
        out = audio_dir / "voiceover.mp3"
        voice = self._pick_voice()
        try:
            words, ok = asyncio.run(media.synth_voiceover(text, out, voice))
        except Exception as exc:
            logger.warning("[Voiceover] edge-tts failed (%s) — HF fallback", exc)
            ok = False
        if ok:
            provider = f"edge-tts:{voice}"
        else:
            # Tier 2: HuggingFace Inference TTS (needs HF_TOKEN).
            out = audio_dir / "voiceover.wav"
            ok = asyncio.run(video_engine._hf_tts(text[:512], os.fspath(out)))
            if ok:
                provider = "huggingface-tts"

        if not ok:
            out = audio_dir / "voiceover.wav"
            ok = asyncio.run(video_engine._silent_audio(max(duration, 5), os.fspath(out)))

        audio_seconds = media.media_seconds(out) or float(max(duration, 5))
        return {"audio_path": os.fspath(out), "generated": bool(ok),
                "provider": provider, "words": words,
                "audio_seconds": round(audio_seconds, 2)}

    def _pick_voice(self) -> str:
        from . import media
        try:
            voice = self._cfg_voice()
        except Exception:
            voice = ""
        return voice or media._rng.choice(media.VOICES)

    def _cfg_voice(self) -> str:
        # cfg is optional on this agent — read env directly when absent.
        cfg = getattr(self, "cfg", None)
        if cfg is not None and getattr(cfg, "tts_voice", ""):
            return cfg.tts_voice
        return os.environ.get("FYE_TTS_VOICE", "").strip()


class AssemblyAgent:
    """Renders scenes + compiles the master via the shared video engine."""
    name = "assembly"

    def run(self, ctx: Dict[str, Any]) -> Dict[str, Any]:
        """Per-shot scenes (B-roll > Ken Burns still > gradient card) → xfade
        stitch → word-timed captions → VO + music duck → master MP4."""
        from . import media

        pkg = Path(ctx["pkg_dir"])
        scenes_dir = pkg / "scenes"
        scenes_dir.mkdir(parents=True, exist_ok=True)
        stills_by_shot = {s["shot"]: s for s in ctx.get("stills", {}).get("stills", [])}
        voiceover = ctx.get("voiceover", {})
        vo_path = Path(voiceover["audio_path"]) if voiceover.get("audio_path") else None
        words = voiceover.get("words") or []
        total = float(voiceover.get("audio_seconds") or
                      sum(s["duration_s"] for s in ctx["shots"]["shots"]))
        n = len(ctx["shots"]["shots"])
        # Each scene must cover its stitch segment (share of the timeline +
        # share of the xfade overlap), or the stitched video ends before the
        # narration. Scale each shot's planned duration_s to the real total so
        # long/short shots keep their relative screen time.
        xfade = 0.5
        planned = [max(float(s.get("duration_s") or 0), 0.1)
                   for s in ctx["shots"]["shots"]]
        span = total + (n - 1) * xfade
        scale = span / max(sum(planned), 0.1)

        # ── Scenes: render each shot to a normalized mp4, concurrently. ──
        def _render_scene(i: int, shot: Dict[str, Any]) -> Optional[Tuple[Path, float]]:
            out = scenes_dir / f"scene_{i:03d}.mp4"
            entry = stills_by_shot.get(shot["shot"])
            dur = planned[i] * scale
            if entry and entry.get("kind") == "broll":
                if media.scene_from_broll(Path(entry["path"]), dur, out):
                    return out, dur
            if entry and str(entry.get("path", "")).endswith((".png", ".jpg")):
                if media.scene_from_image(Path(entry["path"]), dur, out):
                    return out, dur
            if media.scene_from_svg(Path(entry["path"]) if entry else scenes_dir / "x.svg",
                                    shot["visual_prompt"], dur, out):
                return out, dur
            return None

        scene_paths: List[Path] = []
        scene_durs: List[float] = []
        with ThreadPoolExecutor(max_workers=min(4, n)) as pool:
            futs = [pool.submit(_render_scene, i, s)
                    for i, s in enumerate(ctx["shots"]["shots"])]
            for f in futs:
                res = f.result()
                if res:
                    scene_paths.append(res[0])
                    scene_durs.append(res[1])

        bg = scenes_dir / "_bg.mp4"
        if not media.stitch_scenes(scene_paths, bg, total, scene_durs=scene_durs):
            logger.error("[Assembly] stitch failed — falling back to engine compile")
            return self._legacy_compile(ctx)

        # ── Captions + audio duck → master. ──
        ass = pkg / "captions.ass"
        media.build_ass(words, ass, total, script=ctx["script"]["script_body"])
        music = pkg / "audio" / "music.m4a"
        media.music_bed(total, music)

        out = pkg / "master.mp4"
        ok = media.compose_master(bg, vo_path, ass, music if music.exists() else None,
                                  ctx["script"].get("title", ""), out, total)
        if not ok:
            return self._legacy_compile(ctx)
        return {"master_path": os.fspath(out),
                "exists": True,
                "scene_count": len(scene_paths),
                "captions": "ass-word-timed" if words else "ass-even-fallback"}

    def _legacy_compile(self, ctx: Dict[str, Any]) -> Dict[str, Any]:
        """Old path via UltimateVideoEngine — kept as last-resort fallback."""
        from ..eaos.video_engine import get_engine
        engine = get_engine()

        async def _build() -> str:
            tasks = [
                engine.render_isolated_scene(i, {
                    "visual_prompt": s["visual_prompt"],
                    "duration_s": s["duration_s"],
                })
                for i, s in enumerate(ctx["shots"]["shots"], 1)
            ]
            clips = list(await asyncio.gather(*tasks))
            sentences = ctx["script"]["script_sentences"]
            durations = [s["duration_s"] for s in ctx["shots"]["shots"]]
            srt = video_srt(sentences, durations)
            audio = ctx.get("voiceover", {}).get("audio_path")
            return await engine.compile_master(
                clips, f"{ctx['package_id']}.mp4", srt, audio_path=audio)

        out = asyncio.run(_build())
        return {"master_path": out,
                "exists": os.path.exists(out) and os.path.getsize(out) > 100,
                "fallback": "engine-slideshow"}


def video_srt(sentences: List[str], durations: List[int]) -> str:
    def ts(sec: int) -> str:
        h, rem = divmod(sec, 3600)
        m, s = divmod(rem, 60)
        return f"{h:02d}:{m:02d}:{s:02d},000"
    lines, t = [], 0
    for i, (s, d) in enumerate(zip(sentences, durations), 1):
        lines.append(f"{i}\n{ts(t)} --> {ts(t + d)}\n{s[:80]}\n")
        t += d
    return "\n".join(lines)


class ComplianceAgent:
    """
    YouTube synthetic-media disclosure + honesty gate. Blocks the package
    unless disclosure metadata is complete; never emits revenue promises.
    """
    name = "compliance"

    def run(self, ctx: Dict[str, Any]) -> Dict[str, Any]:
        research = ctx["research"]
        issues: List[str] = []
        desc = ctx["script"]["description"]
        if "AI-generated" not in desc:
            issues.append("description missing synthetic-media disclosure")
        if not ctx.get("assembly", {}).get("exists"):
            issues.append("master video missing or empty")
        result = {
            "synthetic_media": True,
            "disclosure_text": "This video contains AI-generated media.",
            "rpm_label": "US-weighted planning prior — not a revenue promise.",
            "ypp_gate": research["ypp"],
            "issues": issues,
            "passed": not issues,
        }
        return result


class PublishGateAgent:
    """
    Emit fye.publish_requested to Command OS (hex-signed), then verify the
    journaled decision via GET /api/approvals/{id}. Publishing is always
    human-approved — this agent never self-approves.
    """
    name = "publish_gate"

    def __init__(self, cfg: FyeConfig) -> None:
        self.cfg = cfg

    def run(self, ctx: Dict[str, Any]) -> Dict[str, Any]:
        from . import command_os

        manifest_path = Path(ctx["pkg_dir"]) / "manifest.json"
        manifest = {
            "package_id": ctx["package_id"],
            "title": ctx["script"]["title"],
            "niche": ctx["research"]["niche"],
            "shots": ctx["shots"]["shots"],
            "stills": ctx["stills"]["stills"],
            "master_path": ctx["assembly"]["master_path"],
            "rpm_prior": ctx["research"]["rpm_prior"],
            "revenue_band_prior": ctx["research"]["revenue_band"],
            "disclosure": ctx["compliance"]["disclosure_text"],
            "synthetic_media": True,
            "generated_at": time.time(),
        }
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

        # Publishing carries its own approval: target fye:<job>-publish is
        # distinct from the render authorization fye:<job>, so a render
        # approval never self-authorizes a channel post.
        res = command_os.request_publish_approval(
            self.cfg,
            package_id=f"{ctx['package_id']}-publish",
            title=ctx["script"]["title"],
            description=ctx["script"]["description"][:2000],
            channel=ctx["research"]["niche"],
            duration_s=sum(s["duration_s"] for s in ctx["shots"]["shots"]),
            shot_count=ctx["shots"]["shot_count"],
            human_reviewed=bool(ctx.get("human_reviewed", False)),
            risk_level="medium",
        )
        return {
            "manifest_path": os.fspath(manifest_path),
            "approval_request": res,
            "approval_id": res.get("id"),
            "status": "pending_human_decision" if res.get("ok") else res.get("reason", res.get("error", "unsubmitted")),
        }

    def verify_decision(self, approval_id: str) -> Optional[Dict[str, Any]]:
        from . import command_os
        return command_os.journaled_decision(self.cfg, approval_id)


def package_id_for(topic: str) -> str:
    stamp = time.strftime("%Y-%m-%d")
    digest = hashlib.sha256(f"{topic}:{time.time()}".encode()).hexdigest()[:8]
    return f"fye-{stamp}-{digest}"
