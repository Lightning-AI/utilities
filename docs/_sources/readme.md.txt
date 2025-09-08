# Lightning Utilities











__This repository covers the following use-cases:__

1. _Reusable GitHub workflows_
2. _Shared GitHub actions_
3. _General Python utilities in `lightning_utilities.core`_
4. _CLI `python -m lightning_utilities.cli --help`_

## 1. Reusable workflows

__Usage:__

```yaml
name: Check schema

on: [push]

jobs:

  check-schema:
    uses: Lightning-AI/utilities/.github/workflows/check-schema.yml@v0.5.0
    with:
      azure-dir: ""  # skip Azure check

  check-code:
    uses: Lightning-AI/utilities/.github/workflows/check-code.yml@main
    with:
      actions-ref: main  # normally you shall use the same version as the workflow
```

See usage of other workflows in [.github/workflows/ci-use-checks.yaml](https://github.com/Lightning-AI/utilities/tree/main/.github/workflows/ci-use-checks.yaml).

## 2. Reusable composite actions

See available composite actions [.github/actions/](https://github.com/Lightning-AI/utilities/tree/main/.github/actions).

__Usage:__

```yaml
name: Do something with cache

on: [push]

jobs:
  pytest:
    runs-on: ubuntu-24.04
    steps:
    - uses: actions/checkout@v3
    - uses: actions/setup-python@v4
      with:
        python-version: 3.9
    - uses: Lightning-AI/utilities/.github/actions/cache
      with:
        python-version: 3.9
        requires: oldest # or latest
```

## 3. General Python utilities `lightning_utilities.core`

<details>
  <summary>Installation</summary>
From source:

```bash
pip install https://github.com/Lightning-AI/utilities/archive/refs/heads/main.zip
```

From pypi:

```bash
pip install lightning_utilities
```

</details>

__Usage:__

Example for optional imports:

```python
from lightning_utilities.core.imports import module_available

if module_available("some_package.something"):
    from some_package import something
```

## 4. CLI `lightning_utilities.cli`

The package provides common CLI commands.

<details>
  <summary>Installation</summary>

From pypi:

```bash
pip install lightning_utilities[cli]
```

</details>

__Usage:__

```bash
python -m lightning_utilities.cli [group] [command]
```

<details>
  <summary>Example for setting min versions</summary>

```console
$ cat requirements/test.txt
coverage>=5.0
codecov>=2.1
pytest>=6.0
pytest-cov
pytest-timeout
$ python -m lightning_utilities.cli requirements set-oldest
$ cat requirements/test.txt
coverage==5.0
codecov==2.1
pytest==6.0
pytest-cov
pytest-timeout
```

</details>
