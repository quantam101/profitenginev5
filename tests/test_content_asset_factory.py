from __future__ import annotations

import json
from pathlib import Path

from runtime.eaos.content_asset_factory import ContentAssetPack, slugify


def test_slugify_is_stable_and_filesystem_safe() -> None:
    assert slugify("Best AI Tools: Passive Income!") == "best-ai-tools-passive-income"


def test_content_asset_pack_writes_reusable_assets(tmp_path) -> None:
    pack = ContentAssetPack(
        topic="Best AI tools for passive income",
        canonical_url="https://example.com/content",
        output_dir=tmp_path,
    )

    files = pack.write_all()

    assert set(files) == {"blog_brief", "caption_pack", "ebook", "manual", "self_help", "video_script"}
    for path in files.values():
        assert tmp_path in Path(path).parents
        assert Path(path).read_text(encoding="utf-8").strip()

    captions = json.loads(Path(files["caption_pack"]).read_text(encoding="utf-8"))
    assert captions["hashtags"]
    assert "youtube" in captions


def test_capability_manifest_is_truthful_about_avatar_gap(tmp_path) -> None:
    pack = ContentAssetPack("Topic", "https://example.com", tmp_path)
    manifest = pack.capability_manifest(hf_token_present=True, hf_image_enabled=True, ffmpeg_present=True)

    assert manifest["capabilities"]["faceless_mp4"]["status"] == "live"
    assert manifest["capabilities"]["huggingface_image_scenes"]["status"] == "enabled"
    assert manifest["capabilities"]["talking_head_avatar"]["status"] == "not_installed"
    assert "avatar" in manifest["capabilities"]["capcut_equivalent_editor"]["missing_parts"][1]
