"""
Quality scoring for individual code blocks (functions / classes / methods).

Score pillars
-------------
- Robustness  : try/except handling, input validation, defensive returns
- Completeness: type hints, docstrings, default arguments
- Maintainability: inverse of cyclomatic complexity (lower is better)

The output is a deterministic, explainable ``ScoreBreakdown`` so the merger
can report *why* a given block won.
"""
from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field, asdict
from typing import Any


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------
@dataclass
class ScoreBreakdown:
    """Explainable per-function quality score."""
    total: float = 0.0
    robustness: float = 0.0
    completeness: float = 0.0
    maintainability: float = 0.0
    complexity: int = 1
    notes: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Python scoring
# ---------------------------------------------------------------------------
_COMPLEXITY_NODES = (
    ast.If, ast.For, ast.While, ast.AsyncFor,
    ast.Try, ast.With, ast.AsyncWith,
    ast.BoolOp, ast.IfExp, ast.comprehension,
)


def _cyclomatic_complexity(node: ast.AST) -> int:
    """McCabe complexity — 1 + count of decision points."""
    score = 1
    for child in ast.walk(node):
        if isinstance(child, _COMPLEXITY_NODES):
            score += 1
        elif isinstance(child, ast.ExceptHandler):
            score += 1
    return score


def _has_docstring(node: ast.AST) -> bool:
    try:
        return bool(ast.get_docstring(node))
    except TypeError:
        return False


def score_python_function(node: ast.AST) -> ScoreBreakdown:
    """
    Score a Python ``FunctionDef`` / ``AsyncFunctionDef`` / ``ClassDef`` node.

    Returns a :class:`ScoreBreakdown` with total score and detailed notes.
    """
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        raise TypeError(f"Unsupported AST node type: {type(node).__name__}")

    breakdown = ScoreBreakdown()

    # --- robustness (try / raise / validation) ---
    has_try = any(isinstance(n, ast.Try) for n in ast.walk(node))
    has_raise = any(isinstance(n, ast.Raise) for n in ast.walk(node))
    if has_try:
        breakdown.robustness += 2.0
        breakdown.notes.append("try/except present")
    if has_raise:
        breakdown.robustness += 0.5
        breakdown.notes.append("explicit raise")

    # --- completeness (typing + docstring) ---
    if _has_docstring(node):
        breakdown.completeness += 1.0
        breakdown.notes.append("docstring present")

    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        has_return_anno = node.returns is not None
        typed_args = sum(1 for a in node.args.args if a.annotation is not None)
        total_args = max(1, len(node.args.args))
        anno_ratio = typed_args / total_args
        if has_return_anno:
            breakdown.completeness += 0.5
            breakdown.notes.append("return type hint")
        breakdown.completeness += anno_ratio  # 0..1
        if anno_ratio > 0:
            breakdown.notes.append(f"{typed_args}/{total_args} args typed")

    # --- maintainability (inverse complexity, capped) ---
    complexity = _cyclomatic_complexity(node)
    breakdown.complexity = complexity
    # Reward functions with complexity <= 10, penalize beyond.
    if complexity <= 10:
        breakdown.maintainability = round(1.0 - (complexity - 1) * 0.05, 3)
    else:
        breakdown.maintainability = round(max(0.0, 0.5 - (complexity - 10) * 0.05), 3)
    breakdown.notes.append(f"cyclomatic={complexity}")

    breakdown.total = round(
        breakdown.robustness + breakdown.completeness + breakdown.maintainability,
        3,
    )
    return breakdown


# ---------------------------------------------------------------------------
# JavaScript / TypeScript scoring (regex-based heuristic)
# ---------------------------------------------------------------------------
_JS_TYPED_PARAM_RE = re.compile(r"\(([^)]*)\)")
_JS_RETURN_TYPE_RE = re.compile(r"\)\s*:\s*[A-Za-z_$][\w<>\[\],\s|&?]*")
_JS_TRY_RE = re.compile(r"\btry\s*{")
_JS_THROW_RE = re.compile(r"\bthrow\b")
_JS_DOCBLOCK_RE = re.compile(r"/\*\*[\s\S]*?\*/")
_JS_DECISION_RE = re.compile(
    r"\b(if|else if|for|while|case|catch|\?\?|&&|\|\|)\b|\?[^:]*:"
)


def score_js_function(source: str, leading_doc: str = "") -> ScoreBreakdown:
    """
    Heuristic score for a single JS/TS function body (string slice).

    ``leading_doc`` is the comment block immediately above the function, if any.
    """
    breakdown = ScoreBreakdown()

    # robustness
    if _JS_TRY_RE.search(source):
        breakdown.robustness += 2.0
        breakdown.notes.append("try/catch present")
    if _JS_THROW_RE.search(source):
        breakdown.robustness += 0.5
        breakdown.notes.append("explicit throw")

    # completeness — JSDoc and TS annotations
    if _JS_DOCBLOCK_RE.search(leading_doc):
        breakdown.completeness += 1.0
        breakdown.notes.append("JSDoc present")

    params_match = _JS_TYPED_PARAM_RE.search(source)
    if params_match:
        params = params_match.group(1)
        if params.strip():
            tokens = [p for p in params.split(",") if p.strip()]
            typed = sum(1 for p in tokens if ":" in p)
            total = max(1, len(tokens))
            ratio = typed / total
            breakdown.completeness += ratio
            if typed:
                breakdown.notes.append(f"{typed}/{total} params typed")

    if _JS_RETURN_TYPE_RE.search(source):
        breakdown.completeness += 0.5
        breakdown.notes.append("return type annotation")

    # maintainability — count decision points
    decisions = len(_JS_DECISION_RE.findall(source))
    complexity = decisions + 1
    breakdown.complexity = complexity
    if complexity <= 10:
        breakdown.maintainability = round(1.0 - (complexity - 1) * 0.05, 3)
    else:
        breakdown.maintainability = round(max(0.0, 0.5 - (complexity - 10) * 0.05), 3)
    breakdown.notes.append(f"cyclomatic≈{complexity}")

    breakdown.total = round(
        breakdown.robustness + breakdown.completeness + breakdown.maintainability,
        3,
    )
    return breakdown
