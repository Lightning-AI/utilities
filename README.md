# Lightning Devtools

[![UnitTests](https://github.com/Lightning-AI/dev-toolbox/actions/workflows/ci_testing.yml/badge.svg?event=push)](https://github.com/Lightning-AI/dev-toolbox/actions/workflows/ci_testing.yml)
[![Apply checks](https://github.com/Lightning-AI/dev-toolbox/actions/workflows/ci_use-checks.yml/badge.svg?event=push)](https://github.com/Lightning-AI/dev-toolbox/actions/workflows/ci_use-checks.yml)
[![Documentation Status](https://readthedocs.org/projects/pt-dev-toolbox/badge/?version=latest)](https://pt-dev-toolbox.readthedocs.io/en/latest/?badge=latest)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/Lightning-AI/dev-toolbox/main.svg?badge_token=mqheL1-cTn-280Vx4cJUdg)](https://results.pre-commit.ci/latest/github/Lightning-AI/dev-toolbox/main?badge_token=mqheL1-cTn-280Vx4cJUdg)

This repository provides:
1. reusable GitHub workflows and actions
2. tooling package used in our CI `pl_devtools`.


### 1. Reusable workflows

#### Example
```yml
name: Check schema

on: [push]

jobs:
  check-schema:
    uses: Lightning-AI/lightning-devtools/.github/workflows/check-schema.yml@main
    with:
      azure-dir: ""
```

See usage of other workflows in [.github/workflows/ci_use-checks.yml](.github/workflows/ci_use-checks.yml)

### 2. Reusable composite actions

#### Example
```yml
name: Do something with cache

on: [push]

jobs:
  do_something:
    - name: Cache
      uses: Lightning-AI/lightning-devtools/.github/actions/cache
      with:
        python-version: 3.9
```

### 3. Tooling package

The package provides common CLI commands used in our CI.

#### Installation
```
pip install lightning-devtools
```

#### Example
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