# GitHub Code Scanning

`agents-doctor` can emit SARIF 2.1.0, which GitHub can ingest as a third-party
code scanning result. GitHub recommends relative artifact paths from the
repository root, and `agents-doctor` emits its finding paths in that form.

Create a workflow such as `.github/workflows/agents-doctor-code-scanning.yml`:

```yaml
name: agents-doctor

on:
  push:

permissions:
  contents: read
  security-events: write

jobs:
  agents-doctor:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1

      - uses: actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97 # v7.0.0
        with:
          python-version: "3.12"

      - run: python -m pip install agents-doctor
      - name: Generate SARIF
        run: agents-doctor check --format sarif > agents-doctor.sarif || test $? -eq 1

      - uses: github/codeql-action/upload-sarif@f205ea1c3313d32999d8d6a48b4f6530d4437b38 # v4
        with:
          sarif_file: agents-doctor.sarif
          category: agents-doctor
```

The `security-events: write` permission is required for the upload. The command
is allowed to return exit code 1 because that means findings were found, not that
SARIF generation failed. If the package is not yet published, install the checked
out source with `python -m pip install .` instead.
