# Contributing

Thanks for taking a look. This project is small on purpose, so most contributions
are welcome without ceremony.

## The most valuable bug report

**A repository where the simulation disagrees with what the agent actually does.**

The loader reproduction in `src/agents_doctor/discovery.py` was written by reading
agent source code, not by instrumenting a running agent. If you can show a case
where `agents-doctor explain` claims something is loaded (or lost) and reality
differs, that is the single most useful thing you can send. Include the directory
layout, the file sizes, and what the agent actually did.

## Setup

```console
git clone https://github.com/satoissei/agents-doctor
cd agents-doctor
pip install -e ".[dev]"
```

## Before opening a pull request

```console
pytest
ruff check .
ruff format --check .
mypy
agents-doctor check      # the project checks itself
```

CI runs these checks across Linux, macOS and Windows on Python 3.9 through 3.13. It
also builds the distribution, installs the wheel in a clean environment, and audits
runtime dependencies.

## Privacy when contributing

Do not commit credentials, private repository paths, customer names, or complete
instruction files from a private checkout. For a loader mismatch, reduce the report
to a synthetic directory tree, byte sizes, and sanitized command output. See
[PRIVACY.md](PRIVACY.md) and the issue forms for the expected redaction boundary.

## Adding a rule

1. Pick the next free id. **Ids are permanent** — never renumber an existing rule
   or reuse a retired one. Gaps are intentional and reserved for planned rules
   listed in [ROADMAP.md](ROADMAP.md).
2. Add a `RuleSpec` to `RULES` and a function to `CHECKS` in
   `src/agents_doctor/rules.py`.
3. Write two tests: one proving the rule fires, and one proving it stays quiet on
   well-formed input.
4. Add a row to the rules table in [README.md](README.md).

The bar for a new rule is that it must be decidable from the repository alone. If
answering "is this actually wrong?" needs context the tool cannot see, the rule
belongs in the roadmap discussion instead, not in the code. **A false positive
costs more than a missed finding**, because it teaches people to ignore the tool.

## Style

Match the surrounding code. Comments explain *why*, not *what*. Public functions
carry docstrings; private helpers usually do not need them.

## Reporting security issues

See [SECURITY.md](SECURITY.md).
