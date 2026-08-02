# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-08-02

### Fixed

- Stop reading instruction-file contents after the simulated loader's byte budget
  is exhausted.
- Treat anchors in inline-code path references correctly and ignore references
  that resolve outside the checked repository.
- Report malformed or non-UTF-8 configuration as a normal CLI usage error.
- Count all descendant working directories affected by lost instructions.

### Security

- Reject path-like fallback filenames and root markers.
- Pin executable GitHub Actions to reviewed commit SHAs.
- Run dependency, static-analysis, and tracked-file secret checks in CI and before
  release.

[Unreleased]: https://github.com/satoissei/agents-doctor/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/satoissei/agents-doctor/releases/tag/v0.2.0
