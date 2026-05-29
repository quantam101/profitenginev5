"""Pytest config for backend tests — enables async fixture support."""
import pytest_asyncio  # noqa: F401  re-export for plugins

# Tells pytest-asyncio to auto-detect coroutine tests/fixtures.
collect_ignore: list[str] = []
