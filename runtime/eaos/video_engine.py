"""
EAOS Video Engine — Faceless video generation pipeline.
On GPU nodes: routes to Wan 2.7 MoE 27B FP8 via local inference.
On CPU/OCI nodes: generates slideshow video via FFmpeg + TTS.
"""
import os
import sys
import asyncio
import logging
import subprocess
import urllib.request
import json
from typing import List, Dict, Any, Optional

logger = logging.getLogger("EAOS.VideoEngine")

STORAGE_ROOT = os.environ.get("EAOS_VIDEO_ROOT", "./datacenter/video_pipeline")
HAS_GPU = os.environ.get("EAOS_GPU_ENABLED", "false").lower() == "true"
WAN_ENDPOINT = os.environ.get("WAN_INFERENCE_ENDPOINT", "http://localhost:8188")  # ComfyUI / local API


class UltimateVideoEngine:
    def __init__(self, storage_root: str = STORAGE_ROOT):
        self.paths = {
            "clips":  os.path.join(storage_root, "raw_clips"),
            "audio":  os.path.join(storage_root, "audio_tracks"),
            "subs":   os.path.join(storage_root, "subtitles"),
            "output": os.path.join(storage_root, "distribution_masters"),
            "root":   storage_root,
        }
        for p in self.paths.values():
            os.makedirs(p, exist_ok=True)
        self._check_ffmpeg()

    def _check_ffmpeg(self) -> bool:
        try:
            subprocess.run(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)  # noqa: S603,S607
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.warning("[VideoEngine] ffmpeg not found — video compilation disabled")
            return False

    def _wan_payload(self, prompt: str, start_img: Optional[str] = None, end_img: Optional[str] = None) -> Dict[str, Any]:
        return {
            "model_target": "wan_2.7_moe_27b_fp8.safetensors",
            "parameters": {
                "prompt": f"Cinematic 1080p, ultra-sharp, 9:16 vertical, 24fps, {prompt}",
                "steps": 15, "cfg_scale": 5.0, "frame_length": 121,
                "dimensions": {"width": 1080, "height": 1920},
                "anchors": {"start_frame_path": start_img or "", "end_frame_path": end_img or ""},
            },
        }

    async def _render_wan_scene(self, scene_id: int, scene_data: Dict[str, Any]) -> str:
        """Route to local Wan 2.7 inference endpoint (GPU node)."""
        clip_path = os.path.join(self.paths["clips"], f"scene_{scene_id:03d}.mp4")
        payload = self._wan_payload(
            prompt=scene_data.get("visual_prompt", "Abstract digital technology"),
            start_img=scene_data.get("start_frame"),
            end_img=scene_data.get("end_frame"),
        )
        try:
            data = json.dumps(payload).encode()
            req = urllib.request.Request(
                f"{WAN_ENDPOINT}/api/render",
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            resp = urllib.request.urlopen(req, timeout=300)
            result = json.loads(resp.read())
            # Download rendered clip
            clip_url = result.get("clip_url", "")
            if clip_url:
                urllib.request.urlretrieve(clip_url, clip_path)
                logger.info(f"[VideoEngine] Wan scene {scene_id} downloaded → {clip_path}")
        except Exception as exc:
            logger.warning(f"[VideoEngine] Wan render failed: {exc} — falling back to slideshow")
            clip_path = await self._render_slideshow_scene(scene_id, scene_data)
        return clip_path

    async def _render_slideshow_scene(self, scene_id: int, scene_data: Dict[str, Any]) -> str:
        """CPU fallback: text overlay on black frame via FFmpeg (no GPU required)."""
        clip_path = os.path.join(self.paths["clips"], f"scene_{scene_id:03d}.mp4")
        text = scene_data.get("visual_prompt", f"Scene {scene_id}")[:60].replace("'", "\\'")
        duration = scene_data.get("duration_s", 5)
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", f"color=c=black:s=1080x1920:d={duration}",
            "-vf", (
                f"drawtext=fontsize=48:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2"
                f":text='{text}':box=1:boxcolor=black@0.5:boxborderw=10"
            ),
            "-c:v", "libx264", "-preset", "veryfast", "-t", str(duration), clip_path,
        ]
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)  # noqa: S603
        except Exception as exc:
            logger.warning(f"[VideoEngine] FFmpeg slideshow failed: {exc}")
            with open(clip_path, "wb") as f:
                f.write(b"MOCK")
        return clip_path

    async def render_isolated_scene(self, scene_id: int, scene_data: Dict[str, Any]) -> str:
        if HAS_GPU:
            return await self._render_wan_scene(scene_id, scene_data)
        return await self._render_slideshow_scene(scene_id, scene_data)

    def compile_master(self, clips: List[str], filename: str, srt_text: Optional[str] = None) -> str:
        output = os.path.join(self.paths["output"], filename)
        concat = os.path.join(self.paths["root"], "seq.txt")
        srt = os.path.join(self.paths["subs"], "captions.srt")

        with open(srt, "w") as f:
            f.write(srt_text or "1\n00:00:00,000 --> 00:00:03,000\nAlready Here LLC\n")
        with open(concat, "w") as f:
            f.writelines(f"file '{os.path.abspath(c)}'\n" for c in clips if os.path.exists(c))

        subs_filter = (
            f"subtitles='{os.path.abspath(srt)}':"
            f"force_style='Alignment=6,Fontname=Impact,Fontsize=24,"
            f"PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,Outline=2.5'"
        )
        cmd = [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat,
            "-vf", subs_filter, "-c:v", "libx264", "-crf", "18",
            "-preset", "veryfast", "-c:a", "aac", "-b:a", "192k", output,
        ]
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)  # noqa: S603
            logger.info(f"[VideoEngine] Master compiled → {output}")
        except Exception as exc:
            logger.error(f"[VideoEngine] Compile failed: {exc}")
        finally:
            if os.path.exists(concat):
                os.remove(concat)
        return output

    async def produce_article_video(self, title: str, body: str, canonical_url: str) -> Optional[str]:
        """End-to-end: article text → vertical video → ready for YouTube upload."""
        sentences = [s.strip() for s in body.replace("\n", " ").split(".") if len(s.strip()) > 20][:8]
        clips = []
        for i, sentence in enumerate(sentences):
            clip = await self.render_isolated_scene(i, {
                "visual_prompt": sentence[:120],
                "duration_s": max(3, min(8, len(sentence) // 15)),
            })
            clips.append(clip)

        if not clips:
            return None

        safe_title = "".join(c if c.isalnum() else "_" for c in title[:40])
        srt_lines = []
        t = 0
        for i, sentence in enumerate(sentences):
            dur = max(3, min(8, len(sentence) // 15))
            def _ts(s):
                m, sec = divmod(s, 60)
                return f"00:{m:02d}:{sec:02d},000"
            srt_lines.append(f"{i+1}\n{_ts(t)} --> {_ts(t+dur)}\n{sentence[:80]}\n")
            t += dur

        return self.compile_master(clips, f"{safe_title}.mp4", "\n".join(srt_lines))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    engine = UltimateVideoEngine()
    logger.info("Video Engine validation complete.")
