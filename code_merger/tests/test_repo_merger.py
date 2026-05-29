"""Repo-level merge integration test."""
import textwrap
from pathlib import Path
from code_merger.repo_merger import merge_repositories


def _setup(tmp_path: Path) -> tuple[Path, Path, Path]:
    base = tmp_path / "base"
    target = tmp_path / "target"
    out = tmp_path / "out"
    (base / "backend").mkdir(parents=True)
    (target / "src").mkdir(parents=True)

    (base / "backend" / "service.py").write_text(textwrap.dedent("""
        def run(data):
            return data
    """).strip() + "\n")

    (target / "src" / "service.py").write_text(textwrap.dedent('''
        import json
        def run(data: str) -> dict:
            """Run and parse."""
            try:
                return json.loads(data)
            except Exception:
                return {}
    ''').strip() + "\n")

    (base / "lib.js").write_text("function k() { return 1 }\n")
    (target / "lib.js").write_text(
        "/** doc */\nfunction k(): number { try { return 1 } catch { return 0 } }\n"
    )
    return base, target, out


def test_repo_merge_pairs_by_basename(tmp_path):
    base, target, out = _setup(tmp_path)
    report = merge_repositories(base, target, out, match_by_basename=True)
    assert report.total_upgrades >= 2
    merged_py = out / "backend" / "service.py"
    merged_js = out / "lib.js"
    assert merged_py.exists()
    assert merged_js.exists()
    assert "json.loads" in merged_py.read_text()
    assert "number" in merged_js.read_text()


def test_repo_merge_exact_paths_skips_when_paths_differ(tmp_path):
    base, target, out = _setup(tmp_path)
    report = merge_repositories(base, target, out, match_by_basename=False)
    merged_py = out / "backend" / "service.py"
    # service.py won't match because paths differ; lib.js does match.
    assert not merged_py.exists()
    assert (out / "lib.js").exists()
