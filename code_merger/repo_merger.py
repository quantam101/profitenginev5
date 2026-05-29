"""
Repository-level merge orchestrator.

Walks two repository roots, pairs files by *relative path* (or by basename when
the directory layout differs), and applies the appropriate language-specific
merger. Produces a :class:`RepoMergeReport` plus an output directory of merged
files for downstream review / branching.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, asdict
from pathlib import Path

from .python_merger import merge_python_files
from .js_merger import merge_js_files


_PY_EXTS = {".py"}
_JS_EXTS = {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"}
_SKIP_DIRS = {
    ".git", "node_modules", ".next", "dist", "build", "venv", ".venv",
    "__pycache__", ".pytest_cache", ".turbo", ".cache", "coverage",
    "test_reports", ".idea", ".vscode",
}


@dataclass
class FileMerge:
    base_path: str
    target_path: str
    language: str
    upgrades: list[dict]
    additions: list[str]
    output_path: str

    def as_dict(self) -> dict:
        return asdict(self)


@dataclass
class RepoMergeReport:
    base_repo: str
    target_repo: str
    output_dir: str
    files_merged: list[FileMerge] = field(default_factory=list)
    files_skipped: list[dict] = field(default_factory=list)
    base_only_files: list[str] = field(default_factory=list)
    target_only_files: list[str] = field(default_factory=list)

    @property
    def total_upgrades(self) -> int:
        return sum(len(f.upgrades) for f in self.files_merged)

    @property
    def total_additions(self) -> int:
        return sum(len(f.additions) for f in self.files_merged)

    def as_dict(self) -> dict:
        return {
            "base_repo": self.base_repo,
            "target_repo": self.target_repo,
            "output_dir": self.output_dir,
            "totals": {
                "files_with_upgrades": sum(1 for f in self.files_merged if f.upgrades),
                "files_processed": len(self.files_merged),
                "files_skipped": len(self.files_skipped),
                "upgrades": self.total_upgrades,
                "additions": self.total_additions,
            },
            "files_merged": [f.as_dict() for f in self.files_merged],
            "files_skipped": self.files_skipped,
            "base_only_files": self.base_only_files,
            "target_only_files": self.target_only_files,
        }

    def save(self, path: str | os.PathLike) -> None:
        Path(path).write_text(json.dumps(self.as_dict(), indent=2), encoding="utf-8")


def _walk(root: Path) -> dict[str, Path]:
    """Return a map of relative path -> absolute path, skipping known junk dirs."""
    root = root.resolve()
    out: dict[str, Path] = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in _SKIP_DIRS]
        for fn in filenames:
            full = Path(dirpath) / fn
            ext = full.suffix.lower()
            if ext not in _PY_EXTS | _JS_EXTS:
                continue
            rel = str(full.relative_to(root))
            out[rel] = full
    return out


def _pair_files(
    base_files: dict[str, Path],
    target_files: dict[str, Path],
    match_by_basename: bool,
) -> list[tuple[str, Path, Path]]:
    """Return list of (base_rel, base_abs, target_abs) for files to merge."""
    pairs: list[tuple[str, Path, Path]] = []
    if not match_by_basename:
        for rel, base_abs in base_files.items():
            if rel in target_files:
                pairs.append((rel, base_abs, target_files[rel]))
        return pairs

    target_by_name: dict[str, list[Path]] = {}
    for rel, abs_path in target_files.items():
        target_by_name.setdefault(abs_path.name, []).append(abs_path)
    for rel, base_abs in base_files.items():
        candidates = target_by_name.get(base_abs.name, [])
        if not candidates:
            continue
        if base_abs.suffix.lower() in _PY_EXTS:
            picks = [c for c in candidates if c.suffix.lower() in _PY_EXTS]
        else:
            picks = [c for c in candidates if c.suffix.lower() in _JS_EXTS]
        if picks:
            pairs.append((rel, base_abs, picks[0]))
    return pairs


def merge_repositories(
    base_repo: str | os.PathLike,
    target_repo: str | os.PathLike,
    output_dir: str | os.PathLike,
    *,
    add_unique_blocks: bool = False,
    match_by_basename: bool = True,
    only_changed: bool = True,
) -> RepoMergeReport:
    """
    Compare two repos and merge the best parts into a fresh ``output_dir``.

    Parameters
    ----------
    base_repo, target_repo
        Filesystem paths to two repositories.
    output_dir
        Destination for merged files. Original directory layout from
        ``base_repo`` is preserved for each merged file.
    add_unique_blocks
        Pull definitions that exist only in ``target_repo``.
    match_by_basename
        When ``True`` (default), match files that share a filename even when
        relative directory paths differ. When ``False``, only files at the
        exact same relative path are paired.
    only_changed
        Write the merged file only when at least one upgrade or addition was
        applied. Skip files where the base already wins.
    """
    base_root = Path(base_repo).resolve()
    target_root = Path(target_repo).resolve()
    out_root = Path(output_dir).resolve()
    out_root.mkdir(parents=True, exist_ok=True)

    base_files = _walk(base_root)
    target_files = _walk(target_root)

    pairs = _pair_files(base_files, target_files, match_by_basename)
    paired_base = {p[0] for p in pairs}
    target_paired_paths: set[str] = set()
    for _, _, tgt in pairs:
        try:
            target_paired_paths.add(str(tgt.relative_to(target_root)))
        except ValueError:
            target_paired_paths.add(str(tgt))

    report = RepoMergeReport(
        base_repo=str(base_root),
        target_repo=str(target_root),
        output_dir=str(out_root),
        base_only_files=sorted(p for p in base_files if p not in paired_base),
        target_only_files=sorted(p for p in target_files if p not in target_paired_paths),
    )

    for rel, base_abs, target_abs in pairs:
        ext = base_abs.suffix.lower()
        language = "python" if ext in _PY_EXTS else "js/ts"
        try:
            base_src = base_abs.read_text(encoding="utf-8")
            target_src = target_abs.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError) as exc:
            report.files_skipped.append({"path": rel, "reason": f"read error: {exc}"})
            continue

        try:
            if language == "python":
                result = merge_python_files(
                    base_src, target_src, add_unique_blocks=add_unique_blocks
                )
                merged_src = result.merged_source
                upgrades = result.upgrades
                additions = result.additions
            else:
                js_result = merge_js_files(
                    base_src, target_src, add_unique_blocks=add_unique_blocks
                )
                merged_src = js_result.merged_source
                upgrades = js_result.upgrades
                additions = js_result.additions
        except SyntaxError as exc:
            report.files_skipped.append({"path": rel, "reason": f"syntax error: {exc}"})
            continue

        if only_changed and not upgrades and not additions:
            continue

        out_path = out_root / rel
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(merged_src, encoding="utf-8")
        report.files_merged.append(
            FileMerge(
                base_path=str(base_abs),
                target_path=str(target_abs),
                language=language,
                upgrades=upgrades,
                additions=additions,
                output_path=str(out_path),
            )
        )

    return report
