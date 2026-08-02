"""Shared fixtures for building throwaway repositories."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

import pytest


@pytest.fixture
def make_repo(tmp_path: Path):
    """Build a repository from a ``{path: contents}`` mapping.

    ``contents`` may be ``str`` or ``bytes``; bytes let a test control the exact
    size, which matters because the budget is measured in bytes.
    """

    def _make(files: Mapping[str, object], *, git: bool = True) -> Path:
        root = tmp_path / "repo"
        root.mkdir(exist_ok=True)
        if git:
            (root / ".git").mkdir(exist_ok=True)
        for rel, content in files.items():
            target = root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            if isinstance(content, bytes):
                target.write_bytes(content)
            else:
                target.write_text(str(content), encoding="utf-8")
        return root

    return _make


@pytest.fixture
def filler():
    """Non-blank ASCII content of an exact byte length."""

    def _filler(size: int, marker: str = "x") -> bytes:
        if size <= 0:
            return b""
        return (marker * size).encode("ascii")[:size]

    return _filler
