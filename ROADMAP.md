# Roadmap

Rule ids are permanent and reserved. The gaps in the current numbering are the
rules listed here, not mistakes.

## Reserved rule ids

| ID | Name | Detects |
|----|------|---------|
| `AD003` | `unknown-command` | A command named in the instructions is not defined by any npm script, Makefile target, `pyproject.toml` script, justfile recipe or Taskfile task |
| `AD005` | `duplicate-of-parent` | A nested file repeats a parent's content verbatim, spending budget twice on the same words |
| `AD006` | `out-of-scope-reference` | A nested file describes a sibling package rather than its own directory |
| `AD007` | `possible-secret` | An API key, token or private key in an instruction file |
| `AD008` | `broken-relative-link` | A Markdown link pointing at a file that does not exist |
| `AD009` | `sibling-instructions-drift` | `CLAUDE.md` or `.github/copilot-instructions.md` has diverged from `AGENTS.md` |

`AD003` is deliberately not in the first release: it needs a parser per build tool,
and each one is a source of false positives. It ships when it can be quiet enough.

## Planned features

- **Versioned agent profiles** (`--profile codex@0.108`), so the simulation can track
  changes in loader behaviour across releases instead of assuming one fixed shape.
  This is the main reason to expect ongoing maintenance: upstream behaviour moves,
  and the profile is how that movement gets absorbed.
- **`explain --diff`**, showing what changed about the loaded context between two
  commits — useful in review when someone edits a large instruction file.

## Explicit non-goals

- Judging the prose quality of instructions. Other tools do that; this one reports
  what the agent receives.
- Rewriting or generating `AGENTS.md` files.
- Calling any model API. The tool stays offline and dependency-free so it can run
  in restricted CI environments.
