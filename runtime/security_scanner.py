from __future__ import annotations

from pathlib import Path
from typing import List

# Only match actual key VALUE prefixes — not env-var names like ANTHROPIC_API_KEY
# or assignment patterns like API_KEY= which appear legitimately in every gateway file.
# Ruff (select=S) and ESLint handle code-quality / hardcoded-credential checks;
# this scanner exists only to catch accidentally committed key values.
SECRET_MARKERS = [
    "sk-ant-",               # Anthropic live key
    "sk-proj-",              # OpenAI live key
    "BEGIN PRIVATE KEY",     # PEM private key block
    "BEGIN RSA PRIVATE KEY", # RSA PEM block
    "AWS_SECRET_ACCESS_KEY=", # AWS secret with a value (not just the var name)
]

# Files that self-referentially list the marker strings (scanner definitions,
# key-rotation docs, example env files).  Keep this list short — if a file keeps
# ending up here, the marker is too broad, not the file too noisy.
_IGNORED_FILES = {
    "security_scanner.py",
    "security_check.py",   # runner script — self-referentially documents markers
    "verifier.py",
    "health.mjs",
    "package-lock.json",
}

_IGNORED_RELATIVE = {
    ".env.example",
    "scripts/secrets.env.example",
    "tests/test_core.py",  # uses example key strings as test fixtures
    "CONTINUATION.md",
    "DEPLOYMENT.md",
    "DEPLOY.md",
    "docs/LAUNCH_CHECKLIST.md",
    "docs/AFFILIATE_SETUP.md",
}

_IGNORED_DIRS = {".git", "node_modules", ".next", "__pycache__", ".pytest_cache"}


def scan_text(text: str) -> List[str]:
    lowered = text.lower()
    return [marker for marker in SECRET_MARKERS if marker.lower() in lowered]


def scan_repo(root: str = ".") -> List[str]:
    findings: List[str] = []
    root_path = Path(root).resolve()
    for path in root_path.rglob("*"):
        if not path.is_file():
            continue
        if any(part in _IGNORED_DIRS for part in path.parts):
            continue
        if path.name in _IGNORED_FILES:
            continue
        # Normalise to forward-slash relative path for cross-platform matching
        try:
            rel = path.relative_to(root_path).as_posix()
        except ValueError:
            rel = str(path)
        if rel in _IGNORED_RELATIVE:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        markers = scan_text(text)
        if markers:
            findings.append(f"{path}: {','.join(markers)}")
    return findings
