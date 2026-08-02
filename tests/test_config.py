"""Configuration loading and overrides."""

from __future__ import annotations

from pathlib import Path

try:  # pragma: no cover - each branch is exercised by its matching CI runtime.
    import tomllib
except ModuleNotFoundError:  # Python 3.9 and 3.10
    import tomli as tomllib

import pytest

from agents_doctor import __version__
from agents_doctor.config import (
    DEFAULT_MAX_BYTES,
    Config,
    ConfigError,
    apply_overrides,
    load_codex_settings,
    load_config,
)
from agents_doctor.models import Severity


def test_defaults_match_the_agents_own_defaults(make_repo):
    root = make_repo({"AGENTS.md": "hi"})
    config = load_config(root)
    assert config.max_bytes == DEFAULT_MAX_BYTES == 32 * 1024
    assert config.source is None


def test_dedicated_file_is_read(make_repo):
    root = make_repo({".agents-doctor.toml": "max_bytes = 4096\n"})
    config = load_config(root)
    assert config.max_bytes == 4096
    assert config.source == ".agents-doctor.toml"


def test_pyproject_table_is_read(make_repo):
    root = make_repo({"pyproject.toml": "[tool.agents-doctor]\nmax_bytes = 2048\n"})
    config = load_config(root)
    assert config.max_bytes == 2048
    assert "pyproject.toml" in (config.source or "")


def test_dedicated_file_wins_over_pyproject(make_repo):
    root = make_repo(
        {
            ".agents-doctor.toml": "max_bytes = 111\n",
            "pyproject.toml": "[tool.agents-doctor]\nmax_bytes = 222\n",
        }
    )
    assert load_config(root).max_bytes == 111


def test_pyproject_without_our_table_is_ignored(make_repo):
    root = make_repo({"pyproject.toml": "[project]\nname = 'x'\n"})
    assert load_config(root).max_bytes == DEFAULT_MAX_BYTES


def test_rule_severity_override(make_repo):
    root = make_repo({".agents-doctor.toml": '[rules]\nAD002 = "warning"\n'})
    config = load_config(root)
    assert config.severity_for("AD002", Severity.ERROR) is Severity.WARNING


def test_rule_can_be_switched_off(make_repo):
    root = make_repo({".agents-doctor.toml": '[rules]\nAD001 = "off"\n'})
    assert load_config(root).severity_for("AD001", Severity.ERROR) is None


def test_unknown_option_is_rejected(make_repo):
    root = make_repo({".agents-doctor.toml": "maxbytes = 10\n"})
    with pytest.raises(ConfigError, match="unknown option"):
        load_config(root)


def test_invalid_severity_is_rejected(make_repo):
    root = make_repo({".agents-doctor.toml": '[rules]\nAD001 = "loud"\n'})
    with pytest.raises(ConfigError, match="AD001"):
        load_config(root)


def test_invalid_max_bytes_is_rejected(make_repo):
    root = make_repo({".agents-doctor.toml": "max_bytes = -1\n"})
    with pytest.raises(ConfigError, match="non-negative integer"):
        load_config(root)


def test_malformed_toml_is_rejected(make_repo):
    root = make_repo({".agents-doctor.toml": "max_bytes = = 1\n"})
    with pytest.raises(ConfigError, match="invalid TOML"):
        load_config(root)


def test_command_line_overrides_the_file():
    assert apply_overrides(Config(max_bytes=100), max_bytes=500).max_bytes == 500
    assert apply_overrides(Config(max_bytes=100), max_bytes=None).max_bytes == 100


def test_override_rejects_a_non_positive_budget():
    with pytest.raises(ConfigError):
        apply_overrides(Config(), max_bytes=-1)


def test_zero_budget_is_allowed_like_codex(make_repo):
    assert load_config(make_repo({".agents-doctor.toml": "max_bytes = 0\n"})).max_bytes == 0


def test_codex_loader_settings_are_read_without_rejecting_other_options(make_repo):
    root = make_repo(
        {
            "config.toml": (
                "project_doc_max_bytes = 4096\n"
                'project_doc_fallback_filenames = ["CLAUDE.md"]\n'
                'project_root_markers = [".hg", ".git"]\n'
                'model = "unrelated"\n'
            )
        }
    )
    settings = load_codex_settings(root / "config.toml")
    assert settings.max_bytes == 4096
    assert settings.fallback_filenames == ["CLAUDE.md"]
    assert settings.root_markers == [".hg", ".git"]


def test_codex_loader_rejects_invalid_loader_settings(make_repo):
    root = make_repo({"config.toml": "project_doc_max_bytes = -1\n"})
    with pytest.raises(ConfigError, match="project_doc_max_bytes"):
        load_codex_settings(root / "config.toml")


@pytest.mark.parametrize("setting", ["fallback_filenames", "project_doc_fallback_filenames"])
def test_path_like_fallback_filenames_are_rejected(make_repo, setting):
    """A repository configuration must not turn instruction discovery into file escape."""
    root = make_repo({"config.toml": f'{setting} = ["../private.md"]\n'})
    if setting == "fallback_filenames":
        root = make_repo({".agents-doctor.toml": 'fallback_filenames = ["../private.md"]\n'})
        with pytest.raises(ConfigError, match="not a path"):
            load_config(root)
    else:
        with pytest.raises(ConfigError, match="not a path"):
            load_codex_settings(root / "config.toml")


def test_path_like_codex_root_markers_are_rejected(make_repo):
    root = make_repo({"config.toml": 'project_root_markers = ["../marker"]\n'})
    with pytest.raises(ConfigError, match="not a path"):
        load_codex_settings(root / "config.toml")


def test_runtime_audit_requirements_match_project_dependencies() -> None:
    """The security job must audit exactly the dependencies users install."""
    root = Path(__file__).resolve().parents[1]
    project = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    expected = project["dependencies"]
    actual = [
        line.strip()
        for line in (root / "requirements" / "runtime.txt").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    assert actual == expected


def test_runtime_version_matches_distribution_metadata() -> None:
    root = Path(__file__).resolve().parents[1]
    project = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    assert __version__ == project["version"]
