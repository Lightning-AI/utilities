# Devtools

[![UnitTests](https://github.com/Lightning-AI/devtools/actions/workflows/ci_testing.yml/badge.svg?event=push)](https://github.com/Lightning-AI/devtools/actions/workflows/ci_testing.yml)
[![Apply checks](https://github.com/Lightning-AI/devtools/actions/workflows/ci_use-checks.yml/badge.svg?event=push)](https://github.com/Lightning-AI/devtools/actions/workflows/ci_use-checks.yml)
[![Documentation Status](https://readthedocs.org/projects/pt-dev-toolbox/badge/?version=latest)](https://pt-dev-toolbox.readthedocs.io/en/latest/?badge=latest)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/Lightning-AI/devtools/main.svg?badge_token=mqheL1-cTn-280Vx4cJUdg)](https://results.pre-commit.ci/latest/github/Lightning-AI/devtools/main?badge_token=mqheL1-cTn-280Vx4cJUdg)

# This repository covers the following use-cases

1. GitHub workflows
1. GitHub actions
1. CLI `pl_devtools`

## 1. Reusable workflows

### Usage

```yml
name: Check schema

on: [push]

jobs:
  check-schema:
    uses: Lightning-AI/devtools/.github/workflows/check-schema.yml@main
    with:
      azure-dir: ""
```

See usage of other workflows in [.github/workflows/ci_use-checks.yml](.github/workflows/ci_use-checks.yml).

## 2. Reusable composite actions

See available composite actions [.github/actions/](.github/actions/).

### Usage

```yml
name: Do something with cache

on: [push]

jobs:
  pytest:
    runs-on: ubuntu-20.04
    steps:
    - uses: actions/checkout@v3
    - uses: actions/setup-python@v4
      with:
        python-version: 3.9
    - uses: Lightning-AI/devtools/.github/actions/cache
      with:
        python-version: 3.9
        requires: oldest
        # requires: latest
```

## 3. CLI

The package provides common CLI commands.

### Installation

```bash
pip install lightning-devtools
# OR from source
pip install https://github.com/Lightning-AI/devtools/archive/refs/heads/main.zip
```

### Usage

```bash
python -m pl_devtools [group] [command]
```

```console
$ cat requirements/test.txt
coverage>=5.0
codecov>=2.1
pytest>=6.0
pytest-cov
pytest-timeout
$ python -m pl_devtools requirements set-oldest
$ cat requirements/test.txt
coverage==5.0
codecov==2.1
pytest==6.0
pytest-cov
pytest-timeout
```
