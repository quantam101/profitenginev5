# ProfitEngine Code Merger

AST-based code merger that compares two codebases and pulls the **best** parts
of each into a single upgraded output — function by function. The engine
underneath ProfitEngine v5's self-upgrade pipeline.

Built without LLMs. Pure static analysis using the Python `ast` module for
Python and a brace-balanced tokenizer for JavaScript / TypeScript.

## Install (dev)

```bash
pip install -r /app/backend/requirements.txt
# no extra dependencies — uses stdlib only
```

## CLI

```bash
# Merge a single file pair
python -m code_merger merge base.py target.py -o merged.py [--add-unique]

# Score every top-level function/class in a Python file
python -m code_merger score module.py [--json]

# Merge two repositories (the headline feature)
python -m code_merger repo /path/to/base /path/to/target \
  -o /path/to/output \
  --report report.json \
  [--add-unique] [--exact-paths] [--write-all]
```

## How "best" is decided

Every top-level function / class in both files is parsed into an AST and
scored on three pillars:

| Pillar | Signal |
| --- | --- |
| **Robustness** | `try` / `except` blocks, explicit `raise` statements |
| **Completeness** | Docstring, return type hint, % of args type-annotated |
| **Maintainability** | Inverse of McCabe cyclomatic complexity |

When a function exists in both files, the merger keeps the base version
**unless** the target's total score is *strictly higher*. Imports the target
function needs are also pulled in automatically.

JavaScript / TypeScript uses a heuristic (try/catch, JSDoc, TS annotations,
decision-point count) over the same three pillars.

## Library

```python
from code_merger import merge_python_files, merge_js_files, merge_repositories

result = merge_python_files(base_src, target_src, add_unique_blocks=False)
print(result.summary())
# Upgraded 2 block(s):
#   - parse: 1.4 -> 4.5 (+3.1)
print(result.merged_source)

report = merge_repositories("/repos/pev5", "/repos/ahd", "/out")
report.save("report.json")
```

## Tests

```bash
cd /app && python -m pytest code_merger/tests/ -v
# 15 passed in 0.05s
```

## Real-world demo

The repo ships a real merge of ProfitEngine v5 against already-here-dashboard:

```bash
ls /app/code_merger/demo_output/
# backend/services/llm_runner.py
# backend/services/content_generation_service.py
# runtime/agents.py
# runtime/distillation.py
# report.json
```

Summary: **4 files paired · 2 functions swapped · 32 new top-level definitions
pulled in.** See `report.json` for the full diff.

## API endpoints

The CLI is also exposed via the ProfitEngine FastAPI server (port 8001):

- `POST /api/merge` — merge two source strings
- `POST /api/score` — score every function in a Python source string
- `GET /api/demo` — return the cached AHD → PEV5 report
