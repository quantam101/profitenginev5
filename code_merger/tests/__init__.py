"""Unit tests for code_merger.scoring."""
import ast
import pytest
from code_merger.scoring import (
    score_python_function,
    score_js_function,
)


def _func(src):
    return ast.parse(src).body[0]


def test_python_robustness_rewards_try_except():
    weak = _func("def f():\n    return 1\n")
    strong = _func(
        "def f():\n"
        "    try:\n"
        "        return 1\n"
        "    except Exception:\n"
        "        return 0\n"
    )
    assert score_python_function(strong).total > score_python_function(weak).total


def test_python_typing_and_docstring_rewarded():
    plain = _func("def add(a, b):\n    return a + b\n")
    typed = _func(
        'def add(a: int, b: int) -> int:\n'
        '    """Return a + b."""\n'
        '    return a + b\n'
    )
    assert score_python_function(typed).total > score_python_function(plain).total
    assert score_python_function(typed).complexity == 1


def test_python_complexity_increases_with_branches():
    simple = _func("def f(x):\n    return x\n")
    branchy = _func(
        "def f(x):\n"
        "    if x > 0:\n"
        "        return 1\n"
        "    elif x < 0:\n"
        "        return -1\n"
        "    else:\n"
        "        return 0\n"
    )
    assert score_python_function(branchy).complexity > score_python_function(simple).complexity


def test_python_rejects_invalid_node():
    node = ast.parse("x = 1").body[0]
    with pytest.raises(TypeError):
        score_python_function(node)


def test_js_score_detects_try_and_types():
    plain = "function f(x){ return x }"
    rich = (
        "/** sum of two numbers */\n"
        "function f(x: number, y: number): number {\n"
        "  try { return x + y } catch (e) { throw e }\n"
        "}"
    )
    plain_score = score_js_function(plain)
    rich_score = score_js_function(rich, leading_doc=rich)
    assert rich_score.total > plain_score.total
    assert "try/catch present" in rich_score.notes
