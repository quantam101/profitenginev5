from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List


@dataclass(frozen=True)
class CredentialPattern:
    name: str
    pattern: re.Pattern[str]


def _chars(values: list[int]) -> str:
    return "".join(chr(value) for value in values)


def _prefixed_token(*prefix_parts: str) -> re.Pattern[str]:
    prefix = "".join(prefix_parts)
    return re.compile(r"\b" + re.escape(prefix) + r"[A-Za-z0-9][A-Za-z0-9_-]{20,}\b")


def _pem_material() -> re.Pattern[str]:
    begin = _chars([45, 45, 45, 45, 45, 66, 69, 71, 73, 78, 32])
    middle = _chars([32, 80, 82, 73, 86, 65, 84, 69, 32, 75, 69, 89])
    end = _chars([45, 45, 45, 45, 45])
    return re.compile(re.escape(begin) + r"(?:RSA |DSA |EC |OPENSSH )?" + re.escape(middle + end))


def _aws_assignment() -> re.Pattern[str]:
    name = _chars([65, 87, 83, 95, 83, 69, 67, 82, 69, 84, 95, 65, 67, 67, 69, 83, 83, 95, 75, 69, 89])
    return re.compile(r"\b" + re.escape(name) + r"\s*=\s*['\"]?[A-Za-z0-9/+=]{20,}['\"]?")


# Match credential-shaped values, not documentation strings or env-var names.
CREDENTIAL_PATTERNS = [
    CredentialPattern("anthropic_api_key", _prefixed_token(_chars([115, 107, 45]), _chars([97, 110, 116, 45]))),
    CredentialPattern("openai_project_key", _prefixed_token(_chars([115, 107, 45]), _chars([112, 114, 111, 106, 45]))),
    CredentialPattern("pem_material", _pem_material()),
    CredentialPattern("aws_assignment", _aws_assignment()),
]

_IGNORED_FILES = {"package-lock.json"}

_IGNORED_RELATIVE = {
    ".env.example",
    "scripts/secrets.env.example",
    "tests/test_core.py",
    "runtime/daily_alerts.env.example",
    "FINAL_VERIFICATION_REPORT.md",
}

_IGNORED_DIRS = {
    ".git",
    ".next",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
    ".venv",
    "__pycache__",
    ".claude",
    "dist",
    "build",
    "node_modules",
}

_TEXT_SUFFIXES = {
    "",
    ".cjs",
    ".css",
    ".env",
    ".example",
    ".html",
    ".js",
    ".json",
    ".jsx",
    ".md",
    ".mjs",
    ".py",
    ".sh",
    ".sql",
    ".toml",
    ".ts",
    ".tsx",
    ".txt",
    ".yaml",
    ".yml",
}


def _iter_matches(text: str) -> Iterable[str]:
    for credential in CREDENTIAL_PATTERNS:
        if credential.pattern.search(text):
            yield credential.name


def scan_text(text: str) -> List[str]:
    return list(_iter_matches(text))


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
        try:
            rel = path.relative_to(root_path).as_posix()
        except ValueError:
            rel = str(path)
        if rel in _IGNORED_RELATIVE:
            continue
        if path.suffix.lower() not in _TEXT_SUFFIXES:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        matches = scan_text(text)
        if matches:
            findings.append(f"{rel}: {','.join(matches)}")
    return findings
