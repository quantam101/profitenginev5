"""Unit tests for python_merger."""
import textwrap
from code_merger.python_merger import merge_python_files


def test_merge_swaps_weaker_function():
    base = textwrap.dedent("""
        def hello(name):
            return "hi " + name
    """).strip()
    target = textwrap.dedent('''
        def hello(name: str) -> str:
            """Return a greeting for the supplied name."""
            try:
                return "hi " + str(name)
            except Exception:
                return ""
    ''').strip()
    res = merge_python_files(base, target)
    assert any(u["name"] == "hello" for u in res.upgrades)
    assert "try:" in res.merged_source
    assert "def hello(name: str) -> str" in res.merged_source


def test_merge_keeps_better_base():
    strong = textwrap.dedent('''
        def hello(name: str) -> str:
            """Return greeting."""
            try:
                return "hi " + name
            except Exception:
                return ""
    ''').strip()
    weak = "def hello(name):\n    return 'hi ' + name\n"
    res = merge_python_files(strong, weak)
    assert res.upgrades == []
    assert 'try:' in res.merged_source  # base preserved


def test_merge_adds_unique_target_blocks_when_requested():
    base = "def a():\n    return 1\n"
    target = (
        "def a():\n"
        "    return 1\n"
        "def brand_new(x: int) -> int:\n"
        "    return x + 1\n"
    )
    res = merge_python_files(base, target, add_unique_blocks=True)
    assert "brand_new" in res.additions
    assert "def brand_new" in res.merged_source


def test_merge_skip_unique_blocks_by_default():
    base = "def a():\n    return 1\n"
    target = "def a():\n    return 1\n\ndef extra():\n    return 2\n"
    res = merge_python_files(base, target)
    assert res.additions == []
    assert "def extra" not in res.merged_source
    assert "extra" in res.target_only


def test_merge_pulls_missing_imports_when_swapping():
    base = textwrap.dedent("""
        def parse(data):
            return data
    """).strip()
    target = textwrap.dedent('''
        import json
        def parse(data: str) -> dict:
            """Parse json blob."""
            try:
                return json.loads(data)
            except Exception:
                return {}
    ''').strip()
    res = merge_python_files(base, target)
    assert any(u["name"] == "parse" for u in res.upgrades)
    assert "import json" in res.merged_source
    assert "import json" in res.added_imports[0]


def test_merge_preserves_module_docstring_position():
    base = '"""base mod doc."""\n\ndef f():\n    return 1\n'
    target = '"""tgt doc."""\nimport os\ndef f() -> int:\n    """doc."""\n    try:\n        return os.cpu_count()\n    except Exception:\n        return 1\n'
    res = merge_python_files(base, target)
    assert res.merged_source.startswith('"""base mod doc."""')
    assert "import os" in res.merged_source
