"""
Command-line interface for the ProfitEngine code merger.

Usage
-----
    profitengine merge base.py target.py -o merged.py
    profitengine score path/to/file.py
    profitengine repo /path/to/base /path/to/target -o /path/to/output

The CLI uses ``argparse`` (no extra dependency) so it ships clean.
"""
from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path

from . import __version__
from .python_merger import merge_python_files
from .js_merger import merge_js_files
from .repo_merger import merge_repositories
from .scoring import score_python_function


# ---------------------------------------------------------------------------
# Sub-command handlers
# ---------------------------------------------------------------------------
def _detect_language(path: Path) -> str:
    ext = path.suffix.lower()
    if ext == ".py":
        return "python"
    if ext in {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"}:
        return "js"
    raise SystemExit(f"Unsupported file extension: {ext}")


def cmd_merge(args: argparse.Namespace) -> int:
    base = Path(args.base)
    target = Path(args.target)
    lang = _detect_language(base)
    base_src = base.read_text(encoding="utf-8")
    target_src = target.read_text(encoding="utf-8")

    if lang == "python":
        result = merge_python_files(
            base_src, target_src, add_unique_blocks=args.add_unique
        )
    else:
        result = merge_js_files(
            base_src, target_src, add_unique_blocks=args.add_unique
        )

    out_path = Path(args.output) if args.output else None
    if out_path:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(result.merged_source, encoding="utf-8")
        print(f"[ok] wrote merged file -> {out_path}")
    else:
        sys.stdout.write(result.merged_source)

    print("\n" + result.summary(), file=sys.stderr)
    return 0


def cmd_score(args: argparse.Namespace) -> int:
    path = Path(args.file)
    src = path.read_text(encoding="utf-8")
    lang = _detect_language(path)
    if lang != "python":
        raise SystemExit("Score command currently supports Python only.")
    tree = ast.parse(src)
    rows = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            score = score_python_function(node)
            rows.append({"name": node.name, **score.as_dict()})
    if args.json:
        print(json.dumps(rows, indent=2))
    else:
        if not rows:
            print("(no top-level functions or classes found)")
        for r in rows:
            print(
                f"{r['name']:30s}  total={r['total']:>5}  "
                f"robust={r['robustness']:>4}  complete={r['completeness']:>5}  "
                f"maintain={r['maintainability']:>5}  cyclomatic={r['complexity']}"
            )
    return 0


def cmd_repo(args: argparse.Namespace) -> int:
    report = merge_repositories(
        base_repo=args.base,
        target_repo=args.target,
        output_dir=args.output,
        add_unique_blocks=args.add_unique,
        match_by_basename=not args.exact_paths,
        only_changed=not args.write_all,
    )
    summary = report.as_dict()["totals"]
    print(json.dumps(summary, indent=2))
    if args.report:
        report.save(args.report)
        print(f"[ok] full report -> {args.report}")
    return 0


# ---------------------------------------------------------------------------
# Argparse wiring
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="profitengine",
        description="AST-based code merger — pulls the best parts of two codebases.",
    )
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="command", required=True)

    p_merge = sub.add_parser("merge", help="Merge a single file pair")
    p_merge.add_argument("base", help="Base file (kept as the foundation)")
    p_merge.add_argument("target", help="Target file (source of upgrades)")
    p_merge.add_argument("-o", "--output", help="Write merged file here (else stdout)")
    p_merge.add_argument(
        "--add-unique",
        action="store_true",
        help="Append functions/classes unique to the target file.",
    )
    p_merge.set_defaults(func=cmd_merge)

    p_score = sub.add_parser("score", help="Score every top-level def/class in a file")
    p_score.add_argument("file", help="Python file to score")
    p_score.add_argument("--json", action="store_true", help="Emit JSON instead of table")
    p_score.set_defaults(func=cmd_score)

    p_repo = sub.add_parser("repo", help="Walk two repositories and merge pairwise")
    p_repo.add_argument("base", help="Base repo path")
    p_repo.add_argument("target", help="Target repo path")
    p_repo.add_argument("-o", "--output", required=True, help="Output directory")
    p_repo.add_argument(
        "--add-unique",
        action="store_true",
        help="Also append blocks unique to the target file.",
    )
    p_repo.add_argument(
        "--exact-paths",
        action="store_true",
        help="Require identical relative paths instead of matching by filename.",
    )
    p_repo.add_argument(
        "--write-all",
        action="store_true",
        help="Write merged file even if no upgrades were applied.",
    )
    p_repo.add_argument("--report", help="Path to write full JSON report")
    p_repo.set_defaults(func=cmd_repo)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
