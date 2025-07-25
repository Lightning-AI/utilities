# Copyright The Lightning AI team.
# Licensed under the Apache License, Version 2.0 (the "License");
#     http://www.apache.org/licenses/LICENSE-2.0
#
import glob
import os.path
import re
import warnings
from collections.abc import Sequence
from pprint import pprint
from typing import Union

REQUIREMENT_ROOT = "requirements.txt"
REQUIREMENT_FILES_ALL: list = glob.glob(os.path.join("requirements", "*.txt"))
REQUIREMENT_FILES_ALL += glob.glob(os.path.join("requirements", "**", "*.txt"), recursive=True)
REQUIREMENT_FILES_ALL += glob.glob(os.path.join("**", "pyproject.toml"))
if os.path.isfile(REQUIREMENT_ROOT):
    REQUIREMENT_FILES_ALL += [REQUIREMENT_ROOT]


def prune_packages_in_requirements(
    packages: Union[str, Sequence[str]], req_files: Union[str, Sequence[str]] = REQUIREMENT_FILES_ALL
) -> None:
    """Remove some packages from given requirement files."""
    if isinstance(packages, str):
        packages = [packages]
    if isinstance(req_files, str):
        req_files = [req_files]
    for req in req_files:
        _prune_packages(req, packages)


def _prune_packages(req_file: str, packages: Sequence[str]) -> None:
    """Remove some packages from given requirement files."""
    with open(req_file) as fp:
        lines = fp.readlines()

    if isinstance(packages, str):
        packages = [packages]
    for pkg in packages:
        lines = [ln for ln in lines if not ln.startswith(pkg)]
    pprint(lines)

    with open(req_file, "w") as fp:
        fp.writelines(lines)


def _replace_min_txt(fname: str) -> None:
    with open(fname) as fopen:
        req = fopen.read().replace(">=", "==")
    with open(fname, "w") as fw:
        fw.write(req)


def _replace_min_pyproject_toml(fname: str) -> None:
    """Replace all `>=` with `==` in the standard pyproject.toml file in [project.dependencies]."""
    import tomlkit

    # Load and parse the existing pyproject.toml
    with open(fname, encoding="utf-8") as f:
        content = f.read()
    doc = tomlkit.parse(content)

    # todo: consider also replace extras in [dependency-groups] -> extras = [...]
    deps = doc.get("project", {}).get("dependencies")
    if not deps:
        return

    # Replace '>=version' with '==version' in each dependency
    for i, req in enumerate(deps):
        # Simple string value
        deps[i] = req.replace(">=", "==")

    # Dump back out, preserving layout
    with open(fname, "w", encoding="utf-8") as f:
        f.write(tomlkit.dumps(doc))


def replace_oldest_version(req_files: Union[str, Sequence[str]] = REQUIREMENT_FILES_ALL) -> None:
    """Replace the min package version by fixed one."""
    if isinstance(req_files, str):
        req_files = [req_files]
    for fname in req_files:
        if fname.endswith(".txt"):
            _replace_min_txt(fname)
        elif os.path.basename(fname) == "pyproject.toml":
            _replace_min_pyproject_toml(fname)
        else:
            warnings.warn(
                "Only *.txt with plain list of requirements or standard pyproject.toml are supported."
                f" File '{fname}' is not supported.",
                UserWarning,
                stacklevel=2,
            )


def _replace_package_name(requirements: list[str], old_package: str, new_package: str) -> list[str]:
    """Replace one package by another with the same version in a given requirement file.

    >>> _replace_package_name(["torch>=1.0 # comment", "torchvision>=0.2", "torchtext <0.3"], "torch", "pytorch")
    ['pytorch>=1.0 # comment', 'torchvision>=0.2', 'torchtext <0.3']

    """
    for i, req in enumerate(requirements):
        requirements[i] = re.sub(r"^" + re.escape(old_package) + r"(?=[ <=>#]|$)", new_package, req)
    return requirements


def replace_package_in_requirements(
    old_package: str, new_package: str, req_files: Union[str, Sequence[str]] = REQUIREMENT_FILES_ALL
) -> None:
    """Replace one package by another with same version in given requirement files."""
    if isinstance(req_files, str):
        req_files = [req_files]
    for fname in req_files:
        with open(fname) as fopen:
            reqs = fopen.readlines()
        reqs = _replace_package_name(reqs, old_package, new_package)
        with open(fname, "w") as fw:
            fw.writelines(reqs)
