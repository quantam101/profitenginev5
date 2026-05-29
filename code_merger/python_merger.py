"""
AST-based merger for Python source files.

Strategy
--------
1. Parse base + target into ``ast.Module`` trees.
2. Index every top-level ``def`` / ``async def`` / ``class`` by name in each tree.
3. Score each block via :mod:`code_merger.scoring`.
4. For overlapping names, swap the base block with the target block when the
   target's score is *strictly higher*. Optionally append unique blocks from
   the target that don't exist in the base.
5. Detect new ``import`` statements in the target whose modules don't appear
   in the base and prepend them so swapped functions keep their dependencies.

Output is rendered using :func:`ast.unparse` (Python 3.9+) — no astor needed.
"""
from __future__ import annotations

import ast
from dataclasses import dataclass, field
from typing import Optional

from .scoring import score_python_function, ScoreBreakdown


_DEF_TYPES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)


@dataclass
class _Block:
    name: str
    node: ast.AST
    score: ScoreBreakdown


@dataclass
class PythonMergeResult:
    merged_source: str
    upgrades: list[dict] = field(default_factory=list)   # name, base, target, delta
    additions: list[str] = field(default_factory=list)   # added unique blocks
    added_imports: list[str] = field(default_factory=list)
    base_only: list[str] = field(default_factory=list)   # blocks unique to base
    target_only: list[str] = field(default_factory=list)

    def summary(self) -> str:
        lines = [
            f"Upgraded {len(self.upgrades)} block(s):",
        ]
        for u in self.upgrades:
            lines.append(
                f"  - {u['name']}: {u['base']} -> {u['target']} (+{u['delta']})"
            )
        if self.added_imports:
            lines.append(f"Added {len(self.added_imports)} import(s):")
            for imp in self.added_imports:
                lines.append(f"  + {imp}")
        if self.additions:
            lines.append(f"Pulled {len(self.additions)} new block(s):")
            for a in self.additions:
                lines.append(f"  + {a}")
        return "\n".join(lines)


def _index_blocks(tree: ast.Module) -> dict[str, _Block]:
    blocks: dict[str, _Block] = {}
    for node in tree.body:
        if isinstance(node, _DEF_TYPES):
            blocks[node.name] = _Block(
                name=node.name,
                node=node,
                score=score_python_function(node),
            )
    return blocks


def _collect_imports(tree: ast.Module) -> tuple[list[ast.stmt], set[str]]:
    """Return list of import nodes plus the set of imported root module names."""
    imports: list[ast.stmt] = []
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.Import):
            imports.append(node)
            for alias in node.names:
                names.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            imports.append(node)
            if node.module:
                names.add(node.module.split(".")[0])
    return imports, names


def merge_python_files(
    base_source: str,
    target_source: str,
    *,
    add_unique_blocks: bool = False,
) -> PythonMergeResult:
    """
    Merge ``target_source`` into ``base_source``.

    Parameters
    ----------
    base_source
        The source of the file you want to *upgrade*.
    target_source
        The source you want to pull better implementations from.
    add_unique_blocks
        When ``True``, append top-level functions/classes that only exist in
        the target. Defaults to ``False`` (conservative).

    Returns
    -------
    PythonMergeResult
        The merged source plus a report of every change made.
    """
    base_tree = ast.parse(base_source)
    target_tree = ast.parse(target_source)

    base_index = _index_blocks(base_tree)
    target_index = _index_blocks(target_tree)

    upgrades: list[dict] = []

    # --- swap weaker blocks in base with better ones from target ---
    new_body: list[ast.stmt] = []
    for node in base_tree.body:
        if isinstance(node, _DEF_TYPES) and node.name in target_index:
            base_b = base_index[node.name]
            target_b = target_index[node.name]
            if target_b.score.total > base_b.score.total:
                upgrades.append({
                    "name": node.name,
                    "base": base_b.score.total,
                    "target": target_b.score.total,
                    "delta": round(target_b.score.total - base_b.score.total, 3),
                    "reason": "; ".join(target_b.score.notes),
                })
                new_body.append(target_b.node)
                continue
        new_body.append(node)

    # --- optionally append blocks unique to target ---
    additions: list[str] = []
    target_only_names: list[str] = []
    if add_unique_blocks:
        for name, block in target_index.items():
            if name not in base_index:
                new_body.append(block.node)
                additions.append(name)
                target_only_names.append(name)
    else:
        target_only_names = [n for n in target_index if n not in base_index]

    # --- handle imports: include target imports for added/swapped names ---
    added_imports: list[str] = []
    if upgrades or additions:
        _, base_modules = _collect_imports(base_tree)
        target_imports, _ = _collect_imports(target_tree)
        # naive but safe: keep target imports whose root module isn't in base.
        new_imports: list[ast.stmt] = []
        for imp in target_imports:
            roots: list[str] = []
            if isinstance(imp, ast.Import):
                roots = [a.name.split(".")[0] for a in imp.names]
            elif isinstance(imp, ast.ImportFrom) and imp.module:
                roots = [imp.module.split(".")[0]]
            if any(r not in base_modules for r in roots):
                new_imports.append(imp)
                added_imports.append(ast.unparse(imp))
        # prepend after the existing module docstring (if any)
        insert_at = 0
        if (
            new_body
            and isinstance(new_body[0], ast.Expr)
            and isinstance(new_body[0].value, ast.Constant)
            and isinstance(new_body[0].value.value, str)
        ):
            insert_at = 1
        new_body = new_body[:insert_at] + new_imports + new_body[insert_at:]

    base_tree.body = new_body
    ast.fix_missing_locations(base_tree)
    merged_source = ast.unparse(base_tree) + "\n"

    return PythonMergeResult(
        merged_source=merged_source,
        upgrades=upgrades,
        additions=additions,
        added_imports=added_imports,
        base_only=[n for n in base_index if n not in target_index],
        target_only=target_only_names,
    )


def diff_python_files(base_source: str, target_source: str) -> dict:
    """Dry-run: return the upgrade report without producing merged code."""
    res = merge_python_files(base_source, target_source, add_unique_blocks=False)
    return {
        "upgrades": res.upgrades,
        "base_only": res.base_only,
        "target_only": res.target_only,
    }
