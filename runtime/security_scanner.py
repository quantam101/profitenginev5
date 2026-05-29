from __future__ import annotations

from pathlib import Path
from typing import List

# Narrow markers — broad 'sk-' matches innocent words like 'task-', 'disk-', 'risk-'.
# Use known Anthropic / OpenAI key prefixes only.
SECRET_MARKERS = [
    "sk-ant-",
    "sk-proj-",
    "API_KEY=",
    "BEGIN PRIVATE KEY",
    "AWS_SECRET",
    "ANTHROPIC_API_KEY",
    "OPENAI_API_KEY",
]

# Files that legitimately reference marker strings as env var names, SDK kwargs,
# doc examples, or test fixture strings — not embedded secrets.
_IGNORED_FILES = {
    "security_scanner.py",
    "verifier.py",
    "health.mjs",
    "package-lock.json",
    "first-boot.sh",
    "docker-compose.yml",
}

_IGNORED_RELATIVE = {
    "app/api/advisor/route.ts",
    "app/api/widget/embed-source.ts",
    "app/dashboard/page.tsx",
    "runtime/claude_gateway.py",
    "runtime/groq_gateway.py",
    "runtime/gemini_gateway.py",
    "runtime/inference_cascade.py",
    "runtime/ollama_gateway.py",
    "runtime/local_model_router.py",
    "runtime/devto_client.py",
    "runtime/github_client.py",
    "runtime/gmail_client.py",
    "runtime/hashnode_client.py",
    "runtime/medium_client.py",
    "runtime/agent_impls/sovereign_orchestrator.py",
    "runtime/agent_impls/lifelong_catch_correct.py",
    "runtime/agent_impls/local_research.py",
    "runtime/agent_impls/trend_scanner.py",
    "runtime/agent_impls/content_gen.py",
    "runtime/agent_impls/blog_publisher.py",
    "runtime/agent_impls/content_pipeline.py",
    "tests/test_core.py",
    ".env.example",
    "CONTINUATION.md",
    "DEPLOYMENT.md",
    ".github/workflows/deploy.yml",
    ".github/workflows/cycle.yml",
    ".github/workflows/self-improve.yml",
    "scripts/bootstrap-server.sh",
    "scripts/secrets.env.example",
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
