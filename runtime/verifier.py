from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class VerificationResult:
    passed: bool
    reason: str


class Verifier:
    # Last-resort gate for actual secret VALUES in agent output. Env-var
    # NAMES and placeholders (GROQ_API_KEY=..., "set your API_KEY=") are
    # legitimate output — the inference cascade's offline help text lists
    # them, and blocking it broke every no-provider execution. Same
    # philosophy as runtime/security_scanner.py: match key shapes, not
    # words. Plain "sk-" is also gone: it matched prose like "risk-free".
    BLOCKED_PATTERNS = [
        (re.compile(r"API_KEY\s*=\s*[\"']?[A-Za-z0-9_\-]{12,}", re.IGNORECASE), "api_key_assignment"),
        (re.compile(r"BEGIN(?: [A-Z]+)? PRIVATE KEY"), "pem_private_key"),
        (re.compile(r"sk-(?:ant|proj)-[A-Za-z0-9_\-]{16,}"), "sk_prefixed_key"),
        (re.compile(r"sk-[A-Za-z0-9]{20,}"), "sk_key_value"),
        (re.compile(r"(?:password|token)\s*[:=]\s*[\"']?\S{8,}", re.IGNORECASE), "credential_assignment"),
    ]

    def verify_text_output(self, output: str) -> VerificationResult:
        if not output or not output.strip():
            return VerificationResult(False, "empty_output")
        for pattern, label in self.BLOCKED_PATTERNS:
            if pattern.search(output):
                return VerificationResult(False, f"possible_secret_leak:{label}")
        return VerificationResult(True, "verified")
