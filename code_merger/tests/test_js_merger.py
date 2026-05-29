"""Unit tests for js_merger."""
from code_merger.js_merger import merge_js_files


def test_js_merge_swaps_weaker_function():
    base = "function add(a, b) { return a + b }\n"
    target = (
        "/** add two numbers */\n"
        "function add(a: number, b: number): number {\n"
        "  try { return a + b } catch (e) { throw e }\n"
        "}\n"
    )
    res = merge_js_files(base, target)
    assert any(u["name"] == "add" for u in res.upgrades)
    assert "try" in res.merged_source
    assert "number" in res.merged_source


def test_js_merge_handles_arrow_functions():
    base = "export const hello = (name) => { return 'hi ' + name }\n"
    target = (
        "/** typed hello */\n"
        "export const hello = (name: string): string => {\n"
        "  try { return 'hi ' + name } catch { return '' }\n"
        "}\n"
    )
    res = merge_js_files(base, target)
    assert any(u["name"] == "hello" for u in res.upgrades)
    assert ": string" in res.merged_source


def test_js_merge_adds_unique_when_requested():
    base = "function a() { return 1 }\n"
    target = "function a() { return 1 }\nfunction b(x: number): number { return x }\n"
    res = merge_js_files(base, target, add_unique_blocks=True)
    assert "b" in res.additions
    assert "function b" in res.merged_source


def test_js_brace_balancer_handles_nested_template_literals():
    base = "function fmt(name) { return `hi ${name}` }\n"
    target = (
        "/** doc */\n"
        "function fmt(name: string): string {\n"
        "  try { return `hi ${name.trim()}` } catch (e) { throw e }\n"
        "}\n"
    )
    res = merge_js_files(base, target)
    assert any(u["name"] == "fmt" for u in res.upgrades)
    assert "trim()" in res.merged_source
