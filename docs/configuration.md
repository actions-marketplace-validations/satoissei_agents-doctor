# Configuration

Every setting is optional. `agents-doctor` reads the first source that exists:

1. `.agents-doctor.toml` at the repository root — the whole file is the config
2. `[tool.agents-doctor]` in `pyproject.toml`

Command-line flags override both.

## Options

| Option | Type | Default | Meaning |
|--------|------|---------|---------|
| `max_bytes` | integer | `32768` | Byte budget to simulate. Set it to your agent's `project_doc_max_bytes` if you changed that. `0` disables project instructions. |
| `exclude` | list of strings | see below | Directory *names* skipped while discovering files. |
| `ignore_paths` | list of strings | `[]` | `fnmatch` patterns for references `AD002` should never report. |
| `fallback_filenames` | list of strings | `[]` | Extra per-directory filenames your agent reads, mirroring `project_doc_fallback_filenames`. Each entry must be a filename, not a path. |
| `rules` | table | `{}` | Per-rule severity: `"error"`, `"warning"`, `"info"` or `"off"`. |

The default `exclude` list covers version-control, cache, virtualenv and build
directories: `.git`, `.hg`, `.svn`, `.tox`, `.venv`, `.mypy_cache`,
`.pytest_cache`, `.ruff_cache`, `__pycache__`, `node_modules`, `vendor`, `venv`,
`dist`, `build`, `target`, `site-packages`.

Setting `exclude` replaces the default list rather than adding to it.

## Example

```toml
# .agents-doctor.toml
max_bytes = 65536
ignore_paths = ["dist/*", "generated/**"]
fallback_filenames = ["CLAUDE.md"]

[rules]
AD002 = "warning"
AD004 = "off"
```

## Matching your agent's real budget

The default of 32,768 bytes is the default the reproduced loader uses. If you
raised the limit in your agent's own configuration, tell `agents-doctor` too,
otherwise it reports losses that will not happen:

```console
agents-doctor --max-bytes 65536 check
```

Keeping the value in `.agents-doctor.toml` instead means CI and your editor agree
without anyone remembering the flag.

## Custom project roots

Codex can use custom `project_root_markers`. Pass the equivalent markers on the
command line when checking a repository:

```console
agents-doctor --root-marker .hg --root-marker .workspace explain packages/api
```

The default remains `.git`.

## Reading Codex's config.toml

To simulate the settings Codex is actually using, pass its configuration file:

```console
agents-doctor --codex-config ~/.codex/config.toml explain
```

The following keys are imported:

- `project_doc_max_bytes`
- `project_doc_fallback_filenames`
- `project_root_markers`

Other Codex settings are ignored. Explicit `--max-bytes` and `--root-marker`
options override values read from the Codex file.

For safety, fallback filenames and root markers must be plain names such as
`CLAUDE.md`, `.git`, or `.workspace`. Paths, `..`, and absolute paths are rejected,
so a repository-controlled configuration cannot make the tool inspect files outside
the directory it is checking.

## Exit codes

| Code | Meaning |
|------|---------|
| `0` | Nothing to report |
| `1` | Findings were reported |
| `2` | The command could not run — bad arguments or unreadable configuration |

`check --exit-zero` reports findings while still exiting `0`, which is useful when
introducing the tool to an existing repository.
