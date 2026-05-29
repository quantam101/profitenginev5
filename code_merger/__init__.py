"""
ProfitEngine Code Merger
========================
AST-based Automated Program Repair tool that compares two codebases and
merges the "best" parts of each — scored on robustness, completeness and
maintainability. Supports Python and JavaScript / TypeScript.
"""

from .scoring import score_python_function, score_js_function, ScoreBreakdown
from .python_merger import merge_python_files, PythonMergeResult
from .js_merger import merge_js_files, JsMergeResult
from .repo_merger import merge_repositories, RepoMergeReport

__version__ = "0.1.0"

__all__ = [
    "score_python_function",
    "score_js_function",
    "ScoreBreakdown",
    "merge_python_files",
    "PythonMergeResult",
    "merge_js_files",
    "JsMergeResult",
    "merge_repositories",
    "RepoMergeReport",
]
