# agents-doctor

A CLI that reproduces how coding agents load `AGENTS.md` files and reports what
gets silently discarded.

## Layout

- `src/agents_doctor/discovery.py` — the loader reproduction. Treat it as the
  specification: every rule trusts it.
- `src/agents_doctor/rules.py` — the checks.
- `src/agents_doctor/reporters.py` — output formats.
- `src/agents_doctor/cli.py` — argument parsing and exit codes.
- `tests/` — one module per area.

## Working on this project

Run `pytest`, `ruff check .`, `ruff format .` and `mypy` before opening a pull
request. All four run in CI.

## Rules that apply to changes here

Fidelity to the real loader outranks convenience. If a change makes
`src/agents_doctor/discovery.py` diverge from the behaviour documented in its
module docstring, the docstring and the tests must change in the same commit,
with a reference to the upstream source.

A false positive is worse than a missed finding. When a check cannot decide from
the repository alone whether something is wrong, it must stay silent.

Rule ids are permanent. Never renumber a rule or reuse a retired id; gaps in the
sequence are intentional.

Every rule needs a test proving it fires and a test proving it stays quiet on
well-formed input.

This project checks itself in CI, so this file must pass its own rules.
