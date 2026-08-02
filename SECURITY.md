# Security Policy

## Supported versions

Only the latest tagged release receives security fixes. Development snapshots may
change without a security advisory.

## Reporting a vulnerability

Please report security issues privately through
[GitHub Security Advisories](https://github.com/satoissei/agents-doctor/security/advisories/new)
rather than opening a public issue. Do not include secrets, production paths, or
private repository content in a public issue, pull request, or discussion.

Please include the affected version, a minimal sanitized reproduction, impact, and
any suggested mitigation. The maintainer targets an acknowledgement within seven
calendar days and will coordinate a fix, disclosure timing, and attribution only
with the reporter's consent. This is a target rather than a service-level agreement.

## Threat model

`agents-doctor` reads instruction files inside the directory it is pointed at and
writes findings to standard output. It makes no network requests, sends no
telemetry, and executes no commands from the files it reads. It follows symbolic
links because the loader it reproduces does; a symlink in an untrusted checkout can
therefore point outside that checkout. Run the tool only on repositories you are
authorized to inspect, and review reports before sharing them.

See [PRIVACY.md](PRIVACY.md) for the data-handling details.
