"""Safety invariants for the published composite GitHub Action."""

from __future__ import annotations

from pathlib import Path


def test_action_forwards_extra_arguments_without_shell_globbing() -> None:
    action = (Path(__file__).resolve().parents[1] / "action.yml").read_text(encoding="utf-8")
    assert 'read -r -a extra_args <<< "$AD_ARGS"' in action
    assert '"${extra_args[@]}"' in action
    assert " $AD_ARGS" not in action


def test_action_pins_its_setup_dependency_to_a_commit() -> None:
    action = (Path(__file__).resolve().parents[1] / "action.yml").read_text(encoding="utf-8")
    assert "actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97" in action
