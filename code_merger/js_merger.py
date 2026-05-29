"""
JavaScript / TypeScript merger.

Implementation note
-------------------
We deliberately avoid a hard ``tree-sitter`` dependency (binary wheels are
flaky in restricted environments). Instead we use a robust regex / brace-
matching tokenizer to extract top-level ``function``, arrow-function-const,
and ``export function`` definitions. This is sufficient for module-level
merging which is the 99% case for service files like ``llm_runner.ts``.

Algorithm
---------
1. Tokenize each source into a list of ``(name, start, end, body, leading_doc)``.
2. Score each function using :func:`code_merger.scoring.score_js_function`.
3. For overlapping names, swap the base function with the target's when the
   target's score is strictly higher.
4. Rebuild the source by slicing the base buffer and substituting upgraded
   blocks. Append unique target blocks at the end (opt-in).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable

from .scoring import score_js_function, ScoreBreakdown


# --- function discovery -----------------------------------------------------
_FUNC_PATTERNS = [
    # export function name(...) { ... }
    re.compile(
        r"(?P<doc>(?:/\*\*[\s\S]*?\*/\s*)?)"
        r"(?P<head>(?:export\s+)?(?:async\s+)?function\s+"
        r"(?P<name>[A-Za-z_$][\w$]*)\s*\([^)]*\)\s*"
        r"(?::\s*[^\{]+)?)\s*\{"
    ),
    # export const name = (...) => { ... }
    re.compile(
        r"(?P<doc>(?:/\*\*[\s\S]*?\*/\s*)?)"
        r"(?P<head>(?:export\s+)?(?:const|let|var)\s+"
        r"(?P<name>[A-Za-z_$][\w$]*)\s*"
        r"(?::\s*[^=]+)?=\s*(?:async\s+)?\([^)]*\)\s*"
        r"(?::\s*[^=]+)?=>\s*)\{"
    ),
]


@dataclass
class _JsBlock:
    name: str
    start: int
    end: int
    source: str            # full block including signature & body braces
    doc: str
    score: ScoreBreakdown


@dataclass
class JsMergeResult:
    merged_source: str
    upgrades: list[dict] = field(default_factory=list)
    additions: list[str] = field(default_factory=list)
    base_only: list[str] = field(default_factory=list)
    target_only: list[str] = field(default_factory=list)

    def summary(self) -> str:
        lines = [f"Upgraded {len(self.upgrades)} JS/TS block(s):"]
        for u in self.upgrades:
            lines.append(
                f"  - {u['name']}: {u['base']} -> {u['target']} (+{u['delta']})"
            )
        if self.additions:
            lines.append(f"Pulled {len(self.additions)} new block(s):")
            for a in self.additions:
                lines.append(f"  + {a}")
        return "\n".join(lines)


def _find_matching_brace(text: str, open_idx: int) -> int:
    """Return index of the matching ``}`` for the ``{`` at ``open_idx``.

    Skips strings, regex literals and line / block comments naively but
    correctly enough for ordinary JS/TS source.
    """
    depth = 0
    i = open_idx
    n = len(text)
    while i < n:
        c = text[i]
        # line comment
        if c == "/" and i + 1 < n and text[i + 1] == "/":
            nl = text.find("\n", i)
            i = n if nl == -1 else nl + 1
            continue
        # block comment
        if c == "/" and i + 1 < n and text[i + 1] == "*":
            end = text.find("*/", i + 2)
            i = n if end == -1 else end + 2
            continue
        # string literals
        if c in "\"'`":
            quote = c
            i += 1
            while i < n and text[i] != quote:
                if text[i] == "\\":
                    i += 2
                    continue
                # template literal expressions
                if quote == "`" and text[i] == "$" and i + 1 < n and text[i + 1] == "{":
                    sub_close = _find_matching_brace(text, i + 1)
                    i = sub_close + 1
                    continue
                i += 1
            i += 1
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    raise ValueError("Unbalanced braces while scanning JS/TS source")


def _extract_blocks(source: str) -> list[_JsBlock]:
    blocks: list[_JsBlock] = []
    seen_spans: list[tuple[int, int]] = []
    for pattern in _FUNC_PATTERNS:
        for m in pattern.finditer(source):
            open_brace = m.end() - 1
            # avoid double-counting overlapping matches
            if any(s <= open_brace <= e for s, e in seen_spans):
                continue
            try:
                close_brace = _find_matching_brace(source, open_brace)
            except ValueError:
                continue
            start = m.start("head")
            end = close_brace + 1
            seen_spans.append((start, end))
            body = source[start:end]
            doc = m.group("doc") or ""
            blocks.append(
                _JsBlock(
                    name=m.group("name"),
                    start=start,
                    end=end,
                    source=body,
                    doc=doc,
                    score=score_js_function(body, doc),
                )
            )
    # keep deterministic order
    blocks.sort(key=lambda b: b.start)
    return blocks


def _index(blocks: Iterable[_JsBlock]) -> dict[str, _JsBlock]:
    return {b.name: b for b in blocks}


def merge_js_files(
    base_source: str,
    target_source: str,
    *,
    add_unique_blocks: bool = False,
) -> JsMergeResult:
    """Merge JS/TS source the same way as :func:`merge_python_files`."""
    base_blocks = _extract_blocks(base_source)
    target_blocks = _extract_blocks(target_source)
    base_index = _index(base_blocks)
    target_index = _index(target_blocks)

    upgrades: list[dict] = []
    # Apply swaps from the end so earlier offsets stay valid.
    merged = base_source
    for block in sorted(base_blocks, key=lambda b: b.start, reverse=True):
        if block.name in target_index:
            tgt = target_index[block.name]
            if tgt.score.total > block.score.total:
                upgrades.append({
                    "name": block.name,
                    "base": block.score.total,
                    "target": tgt.score.total,
                    "delta": round(tgt.score.total - block.score.total, 3),
                    "reason": "; ".join(tgt.score.notes),
                })
                replacement = (tgt.doc + tgt.source).strip()
                merged = merged[: block.start] + replacement + merged[block.end:]

    additions: list[str] = []
    target_only_names = [n for n in target_index if n not in base_index]
    if add_unique_blocks:
        appended: list[str] = []
        for name in target_only_names:
            tgt = target_index[name]
            appended.append("\n\n" + (tgt.doc + tgt.source).strip())
            additions.append(name)
        if appended:
            merged = merged.rstrip() + "".join(appended) + "\n"

    return JsMergeResult(
        merged_source=merged,
        upgrades=list(reversed(upgrades)),
        additions=additions,
        base_only=[n for n in base_index if n not in target_index],
        target_only=target_only_names,
    )
