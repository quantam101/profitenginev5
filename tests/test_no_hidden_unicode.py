from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

TEXT_SUFFIXES = {
    ".css",
    ".html",
    ".js",
    ".json",
    ".jsx",
    ".md",
    ".mjs",
    ".py",
    ".sh",
    ".ts",
    ".tsx",
    ".txt",
    ".yaml",
    ".yml",
}

SKIP_DIRS = {
    ".git",
    ".next",
    ".pytest_cache",
    "__pycache__",
    "node_modules",
    "test_reports",
    "video_pipeline",
}

HIDDEN_CHARS = {
    "\ufeff": "byte-order mark",
    "\ufffe": "reversed byte-order mark",
    "\u200b": "zero-width space",
    "\u200c": "zero-width non-joiner",
    "\u200d": "zero-width joiner",
    "\u2060": "word joiner",
}


def _should_scan(path: Path) -> bool:
    if path.suffix.lower() not in TEXT_SUFFIXES:
        return False
    return not any(part in SKIP_DIRS for part in path.relative_to(ROOT).parts)


def test_repository_text_files_do_not_contain_hidden_unicode() -> None:
    offenders: list[str] = []

    for path in ROOT.rglob("*"):
        if not path.is_file() or not _should_scan(path):
            continue

        text = path.read_text(encoding="utf-8", errors="replace")
        for line_number, line in enumerate(text.splitlines(), start=1):
            for char, label in HIDDEN_CHARS.items():
                if char in line:
                    offenders.append(f"{path.relative_to(ROOT)}:{line_number}: {label}")

    assert not offenders, "Hidden Unicode characters found:\n" + "\n".join(offenders)
