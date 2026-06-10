import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN = REPO_ROOT / "campaigns" / "referrals" / "acorns-2026-06-09.json"
SCRIPT = REPO_ROOT / "scripts" / "content_factory_run.py"


def test_content_factory_generates_required_assets(tmp_path):
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--campaign", str(CAMPAIGN), "--output", str(tmp_path)],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=True,
    )

    assert "Generated content pack" in result.stdout

    output_dir = tmp_path / "acorns-referral-2026-06-09"
    required = [
        "book/chapter-01.md",
        "blog/article.md",
        "video/short-form-45s.md",
        "social/platform-variants.md",
        "email/newsletter.md",
        "course/micro-class-outline.md",
        "manifest.json",
    ]

    for relative_path in required:
        output_file = output_dir / relative_path
        assert output_file.exists(), relative_path
        assert output_file.read_text(encoding="utf-8").strip(), relative_path


def test_content_factory_manifest_blocks_autopublish(tmp_path):
    subprocess.run(
        [sys.executable, str(SCRIPT), "--campaign", str(CAMPAIGN), "--output", str(tmp_path)],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=True,
    )

    manifest = json.loads((tmp_path / "acorns-referral-2026-06-09" / "manifest.json").read_text(encoding="utf-8"))

    assert manifest["approval_required_before_publish"] is True
    assert manifest["publication_state"] == "not_published"
    assert manifest["external_runtime_required"] is False
    assert manifest["huggingface_optional"] is True


def test_referral_disclosure_is_preserved(tmp_path):
    subprocess.run(
        [sys.executable, str(SCRIPT), "--campaign", str(CAMPAIGN), "--output", str(tmp_path)],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=True,
    )

    social = (tmp_path / "acorns-referral-2026-06-09" / "social" / "platform-variants.md").read_text(encoding="utf-8")
    email = (tmp_path / "acorns-referral-2026-06-09" / "email" / "newsletter.md").read_text(encoding="utf-8")

    assert "Referral rewards and eligibility" in social
    assert "Referral rewards and eligibility" in email
    assert "guaranteed" not in social.lower().replace("no guaranteed", "")
