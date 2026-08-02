"""Configuration loading.

Settings are read from the first source that exists:

1. ``.agents-doctor.toml`` at the repository root (whole file is the config)
2. ``[tool.agents-doctor]`` in ``pyproject.toml``

Every value can be overridden on the command line.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

from agents_doctor.models import Severity

if sys.version_info >= (3, 11):  # pragma: no cover - version branch
    import tomllib
else:  # pragma: no cover - version branch
    import tomli as tomllib

#: Codex's default ``project_doc_max_bytes``. Instruction files are concatenated
#: root-first and the result is cut off at this many bytes, without warning.
DEFAULT_MAX_BYTES = 32 * 1024

DEFAULT_EXCLUDE = (
    ".git",
    ".hg",
    ".svn",
    ".tox",
    ".venv",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
    "node_modules",
    "vendor",
    "venv",
    "dist",
    "build",
    "target",
    "site-packages",
)

CONFIG_FILENAME = ".agents-doctor.toml"
PYPROJECT_TABLE = "agents-doctor"


class ConfigError(ValueError):
    """Raised when a configuration file exists but cannot be used."""


def _load_toml(path: Path, source: str) -> dict[str, Any]:
    """Load TOML with errors the CLI can report as a normal usage failure."""
    try:
        return tomllib.loads(path.read_text(encoding="utf-8"))
    except UnicodeDecodeError as exc:
        raise ConfigError(f"{source}: must be valid UTF-8") from exc
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"{source}: invalid TOML: {exc}") from exc
    except OSError as exc:
        raise ConfigError(f"{source}: cannot be read: {exc}") from exc


def _validate_local_names(values: list[str], option: str) -> list[str]:
    """Accept only names that remain inside each directory being inspected.

    Fallback instruction files and root markers are joined to a repository path.
    Permitting an absolute path or ``..`` component there would let a repository-
    controlled configuration inspect files outside the checkout.
    """
    for value in values:
        if (
            not value
            or value in {".", ".."}
            or "\x00" in value
            or "/" in value
            or "\\" in value
            or Path(value).is_absolute()
        ):
            raise ConfigError(
                f"{option}: each value must be a non-empty filename or directory name, not a path"
            )
    return values


@dataclass(frozen=True)
class CodexSettings:
    """Codex loader settings relevant to instruction discovery."""

    max_bytes: int | None = None
    fallback_filenames: list[str] | None = None
    root_markers: list[str] | None = None


@dataclass(frozen=True)
class Config:
    """Resolved settings for one run."""

    max_bytes: int = DEFAULT_MAX_BYTES
    exclude: list[str] = field(default_factory=lambda: list(DEFAULT_EXCLUDE))
    ignore_paths: list[str] = field(default_factory=list)
    """Reference targets that are never reported as missing (fnmatch patterns)."""

    fallback_filenames: list[str] = field(default_factory=list)
    """Extra per-directory filenames, mirroring ``project_doc_fallback_filenames``.

    Set this to whatever the agent is configured with, otherwise the simulation
    will miss files the agent does load.
    """

    rules: dict[str, str] = field(default_factory=dict)
    """Rule id -> ``"off"`` or a severity name, overriding the rule's default."""

    source: str | None = None
    """Repo-relative path the settings came from, or ``None`` when nothing was found."""

    def severity_for(self, rule_id: str, default: Severity) -> Severity | None:
        """Return the effective severity for a rule, or ``None`` when disabled."""
        override = self.rules.get(rule_id)
        if override is None:
            return default
        if override.strip().lower() in {"off", "none", "disabled"}:
            return None
        return Severity.parse(override)


def _coerce(data: dict[str, Any], source: str) -> Config:
    known = {
        "max_bytes",
        "exclude",
        "ignore_paths",
        "fallback_filenames",
        "rules",
    }
    unknown = sorted(set(data) - known)
    if unknown:
        raise ConfigError(
            f"{source}: unknown option(s): {', '.join(unknown)}. "
            f"Supported options: {', '.join(sorted(known))}."
        )

    max_bytes = data.get("max_bytes", DEFAULT_MAX_BYTES)
    if not isinstance(max_bytes, int) or isinstance(max_bytes, bool) or max_bytes < 0:
        raise ConfigError(f"{source}: max_bytes must be a non-negative integer")

    def string_list(key: str, default: list[str], *, local_names: bool = False) -> list[str]:
        value = data.get(key)
        if value is None:
            return default
        if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
            raise ConfigError(f"{source}: {key} must be a list of strings")
        values = list(value)
        return _validate_local_names(values, f"{source}: {key}") if local_names else values

    rules_raw = data.get("rules", {})
    if not isinstance(rules_raw, dict) or not all(isinstance(v, str) for v in rules_raw.values()):
        raise ConfigError(f'{source}: rules must be a table of rule-id -> severity or "off"')
    rules = {str(k).upper(): v for k, v in rules_raw.items()}
    for rule_id, value in rules.items():
        if value.strip().lower() in {"off", "none", "disabled"}:
            continue
        try:
            Severity.parse(value)
        except ValueError as exc:
            raise ConfigError(
                f'{source}: rules.{rule_id} must be "off", "error", "warning" or "info"'
            ) from exc

    return Config(
        max_bytes=max_bytes,
        exclude=string_list("exclude", list(DEFAULT_EXCLUDE)),
        ignore_paths=string_list("ignore_paths", []),
        fallback_filenames=string_list("fallback_filenames", [], local_names=True),
        rules=rules,
        source=source,
    )


def load_config(root: Path) -> Config:
    """Load configuration for the repository rooted at ``root``."""
    dedicated = root / CONFIG_FILENAME
    if dedicated.is_file():
        data = _load_toml(dedicated, CONFIG_FILENAME)
        return _coerce(data, CONFIG_FILENAME)

    pyproject = root / "pyproject.toml"
    if pyproject.is_file():
        data = _load_toml(pyproject, "pyproject.toml")
        tool = data.get("tool")
        if tool is None:
            return Config()
        if not isinstance(tool, dict):
            raise ConfigError("pyproject.toml: tool must be a table")
        table = tool.get(PYPROJECT_TABLE)
        if table is None:
            return Config()
        if not isinstance(table, dict):
            raise ConfigError(f"pyproject.toml: tool.{PYPROJECT_TABLE} must be a table")
        return _coerce(table, f"pyproject.toml [tool.{PYPROJECT_TABLE}]")

    return Config()


def apply_overrides(config: Config, *, max_bytes: int | None = None) -> Config:
    """Apply command-line overrides on top of file-based settings."""
    if max_bytes is not None:
        if max_bytes < 0:
            raise ConfigError("--max-bytes must be a non-negative integer")
        config = replace(config, max_bytes=max_bytes)
    return config


def load_codex_settings(path: Path) -> CodexSettings:
    """Read the Codex settings that affect AGENTS.md loading.

    Codex's configuration contains many unrelated options, so unknown keys are
    intentionally ignored here. This function only extracts the three loader
    settings that affect the simulation.
    """
    if not path.is_file():
        raise ConfigError(f"Codex config does not exist: {path}")
    data = _load_toml(path, "Codex config")

    max_bytes = data.get("project_doc_max_bytes")
    if max_bytes is not None and (
        not isinstance(max_bytes, int) or isinstance(max_bytes, bool) or max_bytes < 0
    ):
        raise ConfigError("Codex config: project_doc_max_bytes must be a non-negative integer")

    def string_list(key: str, *, local_names: bool = False) -> list[str] | None:
        value = data.get(key)
        if value is None:
            return None
        if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
            raise ConfigError(f"Codex config: {key} must be a list of strings")
        values = list(value)
        return _validate_local_names(values, f"Codex config: {key}") if local_names else values

    return CodexSettings(
        max_bytes=max_bytes,
        fallback_filenames=string_list("project_doc_fallback_filenames", local_names=True),
        root_markers=string_list("project_root_markers", local_names=True),
    )


def apply_codex_settings(config: Config, settings: CodexSettings) -> Config:
    """Apply loader settings from an explicit Codex config file."""
    return replace(
        config,
        max_bytes=(settings.max_bytes if settings.max_bytes is not None else config.max_bytes),
        fallback_filenames=(
            list(settings.fallback_filenames)
            if settings.fallback_filenames is not None
            else config.fallback_filenames
        ),
    )
