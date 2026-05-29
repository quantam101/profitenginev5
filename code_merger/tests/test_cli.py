"""CLI smoke tests."""
from code_merger.cli import main


def test_cli_merge_outputs_file(tmp_path, capsys):
    base = tmp_path / "a.py"
    target = tmp_path / "b.py"
    out = tmp_path / "merged.py"
    base.write_text("def f(x):\n    return x\n")
    target.write_text(
        'def f(x: int) -> int:\n'
        '    """doc."""\n'
        '    try:\n'
        '        return x\n'
        '    except Exception:\n'
        '        return 0\n'
    )
    rc = main(["merge", str(base), str(target), "-o", str(out)])
    assert rc == 0
    assert out.exists()
    assert "try:" in out.read_text()


def test_cli_score(tmp_path, capsys):
    f = tmp_path / "x.py"
    f.write_text("def f(x: int) -> int:\n    return x\n")
    rc = main(["score", str(f), "--json"])
    assert rc == 0
    captured = capsys.readouterr()
    assert '"name": "f"' in captured.out


def test_cli_repo(tmp_path):
    base = tmp_path / "base"
    target = tmp_path / "tgt"
    out = tmp_path / "out"
    base.mkdir()
    target.mkdir()
    (base / "x.py").write_text("def go():\n    return 1\n")
    (target / "x.py").write_text(
        'def go() -> int:\n    """d."""\n    try:\n        return 1\n    except Exception:\n        return 0\n'
    )
    rc = main([
        "repo", str(base), str(target),
        "-o", str(out),
        "--report", str(tmp_path / "report.json"),
    ])
    assert rc == 0
    assert (out / "x.py").exists()
    assert (tmp_path / "report.json").exists()
