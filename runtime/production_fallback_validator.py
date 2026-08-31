"""Production fallback validator.

Catches hardcoded, non-resolving, or placeholder infrastructure values that
have been removed from the codebase. This is a last-line static guard; real
credential and injection checks are handled by ruff/eslint.
"""
from __future__ import annotations

from pathlib import Path
from typing import List

# Decommissioned / fake production values that must never be used as defaults.
_FORBIDDEN_LITERALS = [
    "129.146.236.177",              # dead OCI server
    "backend.alreadyherellc.com",    # non-resolving fake backend
    "profitengine.alreadyherellc.com",  # non-resolving fake app domain
    "your-profitengine-domain.com",
    "<replace-me>",
    "<generated-token>",
    "<runtime-url>",
    "TODO: set later",
    "test-token",
]

# Filenames that self-referentially document the markers or are test fixtures.
_IGNORED_FILES = {
    "production_fallback_validator.py",
    "security_check.py",
    "security_scanner.py",
    "revenue-os-deploy.mjs",
}

_IGNORED_DIRS = {".git", "node_modules", ".next", "__pycache__", ".pytest_cache", ".claude"}

# Files that are not production config/runtime code (docs, runbooks, manifests)
# may still mention these values for historical context; we only gate production
# source and deployment config here.
_PRODUCTION_GLOBS = (
    "app/**",
    "lib/**",
    "runtime/**",
    "backend/**",
    "agents/**",
    "caddy/**",
    "deploy/**",
    "scripts/*",
    "docker-compose.yml",
    "package.json",
    "next.config.*",
)


def _is_production_path(path: Path) -> bool:
    rel = path.as_posix()
    for glob in _PRODUCTION_GLOBS:
        if glob.endswith("/**"):
            prefix = glob[:-3]
            if rel.startswith(prefix + "/") or rel == prefix:
                return True
        elif Path(rel).match(glob):
            return True
    return False


def scan_fallbacks(root: str = ".") -> List[str]:
    findings: List[str] = []
    root_path = Path(root).resolve()
    for path in root_path.rglob("*"):
        if not path.is_file():
            continue
        if any(part in _IGNORED_DIRS for part in path.parts):
            continue
        if path.name in _IGNORED_FILES:
            continue
        if not _is_production_path(path):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        lowered = text.lower()
        for literal in _FORBIDDEN_LITERALS:
            if literal.lower() in lowered:
                findings.append(f"{path}: forbidden fallback '{literal}'")
    return findings
