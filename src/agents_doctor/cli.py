"""Command line interface.

Exit codes are stable and meant to be used in CI:

* ``0`` -- nothing to report
* ``1`` -- findings were reported
* ``2`` -- the command could not run (bad arguments, unreadable configuration)
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from agents_doctor import __version__
from agents_doctor.config import (
    Config,
    ConfigError,
    apply_codex_settings,
    apply_overrides,
    load_codex_settings,
    load_config,
)
from agents_doctor.discovery import (
    DEFAULT_ROOT_MARKERS,
    build_load_plan,
    discover_instruction_files,
    find_project_root,
)
from agents_doctor.reporters import (
    format_budget,
    format_github,
    format_json,
    format_plan,
    format_plan_json,
    format_sarif,
    format_text,
)
from agents_doctor.rules import RULES, build_context, run_rules

EXIT_OK = 0
EXIT_FINDINGS = 1
EXIT_ERROR = 2

_FORMATTERS = {
    "text": format_text,
    "json": format_json,
    "github": format_github,
    "sarif": format_sarif,
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agents-doctor",
        description=(
            "Show what a coding agent actually loads from your AGENTS.md files, "
            "including the parts silently cut off by the byte budget."
        ),
    )
    parser.add_argument("--version", action="version", version=f"agents-doctor {__version__}")

    # Accepted on either side of the subcommand. argparse would otherwise reject
    # `check . --max-bytes N`, which is the order most people reach for. SUPPRESS
    # keeps the subcommand's copy from overwriting a value given before it.
    budget_option = argparse.ArgumentParser(add_help=False)
    for target in (parser, budget_option):
        target.add_argument(
            "--max-bytes",
            type=int,
            metavar="N",
            default=argparse.SUPPRESS,
            help="Byte budget to simulate. Defaults to 32768, matching project_doc_max_bytes.",
        )

    root_marker_option = argparse.ArgumentParser(add_help=False)
    for target in (parser, root_marker_option):
        target.add_argument(
            "--root-marker",
            action="append",
            dest="root_markers",
            default=argparse.SUPPRESS,
            metavar="NAME",
            help="Root marker to use when locating the project. Repeatable; defaults to .git.",
        )

    codex_config_option = argparse.ArgumentParser(add_help=False)
    for target in (parser, codex_config_option):
        target.add_argument(
            "--codex-config",
            metavar="PATH",
            default=argparse.SUPPRESS,
            help="Read Codex loader settings from this config.toml.",
        )

    subparsers = parser.add_subparsers(dest="command")

    check = subparsers.add_parser(
        "check",
        parents=[budget_option, root_marker_option, codex_config_option],
        help="Report problems and exit non-zero when any are found.",
    )
    check.add_argument("path", nargs="?", default=".", help="Repository path (default: .)")
    check.add_argument(
        "--format", choices=sorted(_FORMATTERS), default="text", help="Output format."
    )
    check.add_argument(
        "--rule",
        action="append",
        metavar="ID",
        help="Run only this rule. Repeatable.",
    )
    check.add_argument(
        "--exit-zero", action="store_true", help="Always exit 0, even with findings."
    )

    explain = subparsers.add_parser(
        "explain",
        parents=[budget_option, root_marker_option, codex_config_option],
        help="Show the instruction files loaded for one working directory.",
    )
    explain.add_argument(
        "path", nargs="?", default=".", help="Working directory to simulate (default: .)"
    )
    explain.add_argument(
        "--format", choices=("text", "json"), default="text", help="Output format."
    )

    budget = subparsers.add_parser(
        "budget",
        parents=[budget_option, root_marker_option, codex_config_option],
        help="Show budget pressure for every directory holding instructions.",
    )
    budget.add_argument("path", nargs="?", default=".", help="Repository path (default: .)")

    subparsers.add_parser("rules", help="List the available rules.")
    return parser


def _resolve(path_argument: str) -> Path:
    path = Path(path_argument).expanduser()
    if not path.exists():
        raise ConfigError(f"path does not exist: {path_argument}")
    return path.resolve() if path.is_dir() else path.resolve().parent


def _prepare(
    path_argument: str,
    max_bytes: int | None,
    root_markers: Sequence[str] | None = None,
    codex_config: str | None = None,
) -> tuple[Path, Path, Config]:
    target = _resolve(path_argument)
    codex_settings = load_codex_settings(Path(codex_config).expanduser()) if codex_config else None
    markers = (
        tuple(root_markers)
        if root_markers is not None
        else tuple(codex_settings.root_markers)
        if codex_settings is not None and codex_settings.root_markers is not None
        else DEFAULT_ROOT_MARKERS
    )
    root = find_project_root(target, markers)
    config = load_config(root)
    if codex_settings is not None:
        config = apply_codex_settings(config, codex_settings)
    config = apply_overrides(config, max_bytes=max_bytes)
    return target, root, config


def _run_check(args: argparse.Namespace) -> int:
    target, root, config = _prepare(
        args.path,
        getattr(args, "max_bytes", None),
        getattr(args, "root_markers", None),
        getattr(args, "codex_config", None),
    )
    del target
    files = discover_instruction_files(root, config)
    if args.rule:
        unknown = sorted({r.upper() for r in args.rule} - set(RULES))
        if unknown:
            raise ConfigError(
                f"unknown rule(s): {', '.join(unknown)}. Known rules: {', '.join(sorted(RULES))}."
            )
    context = build_context(root, config, files)
    findings = run_rules(context, only=args.rule)

    formatter = _FORMATTERS[args.format]
    print(formatter(findings, files_checked=len(files)))

    if args.exit_zero or not findings:
        return EXIT_OK
    return EXIT_FINDINGS


def _run_explain(args: argparse.Namespace) -> int:
    target, root, config = _prepare(
        args.path,
        getattr(args, "max_bytes", None),
        getattr(args, "root_markers", None),
        getattr(args, "codex_config", None),
    )
    plan = build_load_plan(target, root, config)
    formatter = format_plan_json if args.format == "json" else format_plan
    print(formatter(plan))
    return EXIT_OK


def _run_budget(args: argparse.Namespace) -> int:
    _, root, config = _prepare(
        args.path,
        getattr(args, "max_bytes", None),
        getattr(args, "root_markers", None),
        getattr(args, "codex_config", None),
    )
    files = discover_instruction_files(root, config)
    if not files:
        print("No AGENTS.md files found.")
        return EXIT_OK
    plans = [
        build_load_plan(root if f.directory == "." else root / f.directory, root, config)
        for f in files
    ]
    print(format_budget(plans))
    return EXIT_OK


def _run_rules(_: argparse.Namespace) -> int:
    for rule_id in sorted(RULES):
        spec = RULES[rule_id]
        print(f"{spec.id}  {spec.name:<24} {spec.default_severity.value:<8} {spec.summary}")
    return EXIT_OK


_COMMANDS = {
    "check": _run_check,
    "explain": _run_explain,
    "budget": _run_budget,
    "rules": _run_rules,
}


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return EXIT_ERROR
    try:
        return _COMMANDS[args.command](args)
    except ConfigError as exc:
        print(f"agents-doctor: {exc}", file=sys.stderr)
        return EXIT_ERROR
    except OSError as exc:
        print(f"agents-doctor: {exc}", file=sys.stderr)
        return EXIT_ERROR


if __name__ == "__main__":  # pragma: no cover - module entry point
    raise SystemExit(main())
