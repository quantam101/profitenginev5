from __future__ import annotations

from pathlib import Path

from tests.test_no_hidden_unicode import ROOT, _should_scan


MOJIBAKE_PATTERNS = {
    "\ufffd": "Unicode replacement character",
    "\u00ef\u00bf\u00bd": "UTF-8 replacement mojibake",
    "\u00e2\u20ac\u201d": "mojibake em dash",
    "\u00e2\u20ac\u201c": "mojibake en dash",
    "\u00e2\u20ac": "mojibake quote prefix",
    "\u00e2\u2020": "mojibake arrow prefix",
    "\u00e2\u0153": "mojibake checkmark prefix",
    "\u00e2\u2013": "mojibake block prefix",
    "\u00e2\u2022": "mojibake box-drawing prefix",
    "\u00e2\u20d4": "mojibake box-drawing prefix",
    "\u00f0\u0178": "mojibake emoji prefix",
}


def test_repository_text_files_do_not_contain_mojibake() -> None:
    offenders: list[str] = []

    for path in ROOT.rglob("*"):
        if not path.is_file() or not _should_scan(path):
            continue

        text = path.read_text(encoding="utf-8", errors="replace")
        for line_number, line in enumerate(text.splitlines(), start=1):
            for pattern, label in MOJIBAKE_PATTERNS.items():
                if pattern in line:
                    rel = Path(path).relative_to(ROOT)
                    offenders.append(f"{rel}:{line_number}: {label}")

    assert not offenders, "Mojibake patterns found:\n" + "\n".join(offenders)
