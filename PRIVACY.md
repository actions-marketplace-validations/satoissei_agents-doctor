# Privacy

## Local-first by design

`agents-doctor` is a local CLI. It does not send telemetry, make network requests,
create accounts, or execute commands found in instruction files. It reads the files
needed to model an agent's instruction loader and writes reports to standard output.

## What the tool reads and reports

The tool may read `AGENTS.md`, `AGENTS.override.md`, configured fallback files, and
an explicitly supplied Codex configuration file. It reports repository-relative
paths, byte and character counts, diagnostic messages, and (for broken references)
the referenced token. It does **not** print the full contents of instruction files.

Paths and tokens can still be sensitive. Review text, JSON, GitHub annotation, and
SARIF output before pasting it into an issue, pull request, chat, CI log, or external
service. Replace private directory names, customer identifiers, tokens, and internal
URLs with synthetic values.

## Symlinks and trusted scope

The compatibility model follows symbolic links. A repository-controlled instruction
file can therefore resolve outside the checkout. Run the tool only on repositories
and directories you are authorized to inspect. Avoid passing a configuration file
that contains data you are not permitted to read.

Repository configuration cannot use fallback filenames or root markers to escape the
checked directory: those settings accept plain names only. An explicitly supplied
`--codex-config` is still a file you chose to provide, so treat it as sensitive.

## Your controls

- Run the CLI locally and keep its output local when a repository is sensitive.
- Use synthetic fixtures for bug reports; issue templates require a privacy check.
- Remove secrets and private paths from CI logs and uploaded SARIF files.
- Report a privacy or security concern privately under [SECURITY.md](SECURITY.md).

This policy describes the project as released. If a future feature changes the
local-first boundary, it must update this file, the README, tests, and release notes
in the same change.
