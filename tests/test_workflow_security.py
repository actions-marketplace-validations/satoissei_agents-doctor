"""Regression checks for the repository's GitHub Actions supply-chain posture."""

from __future__ import annotations

import re
from pathlib import Path

_USES = re.compile(r"^\s*-\s+uses:\s+[^@\s]+@([^\s#]+)", re.MULTILINE)


def test_executable_github_actions_are_pinned_to_full_commits() -> None:
    root = Path(__file__).resolve().parents[1]
    sources = [root / "action.yml", *(root / ".github" / "workflows").glob("*.yml")]
    for source in sources:
        refs = _USES.findall(source.read_text(encoding="utf-8"))
        assert refs, f"{source} should declare at least one action"
        assert all(re.fullmatch(r"[0-9a-f]{40}", ref) for ref in refs), (
            f"{source} contains a mutable GitHub Action reference: {refs}"
        )
