#!/usr/bin/env python

import os
from importlib.util import module_from_spec, spec_from_file_location

from pkg_resources import parse_requirements
from setuptools import find_packages, setup

_PATH_ROOT = os.path.realpath(os.path.dirname(__file__))
_PATH_SOURCE = os.path.join(_PATH_ROOT, "src")
_PATH_REQUIRE = os.path.join(_PATH_ROOT, "requirements")


def _load_py_module(fname, pkg="pl_devtools"):
    spec = spec_from_file_location(os.path.join(pkg, fname), os.path.join(_PATH_SOURCE, pkg, fname))
    py = module_from_spec(spec)
    spec.loader.exec_module(py)
    return py


def _load_requirements(path_dir: str, file_name: str = "requirements.txt", comment_char: str = "#") -> list:
    """Load requirements from a file.

    >>> _load_requirements(_PATH_ROOT)  # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
    ['torch...', 'pytorch-lightning...'...]
    """
    with open(os.path.join(path_dir, file_name)) as file:
        lines = [ln.strip() for ln in file.readlines()]
    reqs = []
    for ln in lines:
        # filer all comments
        if comment_char in ln:
            ln = ln[: ln.index(comment_char)].strip()
        # skip directly installed dependencies
        if ln.startswith("http"):
            continue
        if ln:  # if requirement is not empty
            reqs.append(ln)
    return reqs


def _prepare_extras():
    extras = {
        "docs": _load_requirements(path_dir=_PATH_REQUIRE, file_name="docs.txt"),
        "test": _load_requirements(path_dir=_PATH_REQUIRE, file_name="test.txt"),
    }
    extras["dev"] = extras["docs"] + extras["test"]
    return extras


about = _load_py_module("__about__.py")
with open(os.path.join(_PATH_REQUIRE, "base.txt")) as fp:
    requirements = list(map(str, parse_requirements(fp.readline())))
with open(os.path.join(_PATH_ROOT, "README.md")) as fp:
    readme = fp.read()

setup(
    name="lightning-devtools",
    version=about.__version__,
    description=about.__docs__,
    author=about.__author__,
    author_email=about.__author_email__,
    url=about.__homepage__,
    download_url="https://github.com/Lightning-AI/devtools",
    license=about.__license__,
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    long_description=readme,
    long_description_content_type="text/markdown",
    include_package_data=True,
    zip_safe=False,
    keywords=["DevOps", "CI/CD"],
    python_requires=">=3.7",
    setup_requires=[],
    install_requires=requirements,
    extras_require=_prepare_extras(),
    project_urls={
        "Bug Tracker": "https://github.com/Lightning-AI/devtools/issues",
        "Documentation": "https://dev-toolbox.rtfd.io/en/latest/",  # TODO: Update domain
        "Source Code": "https://github.com/Lightning-AI/devtools",
    },
    classifiers=[
        "Environment :: Console",
        "Natural Language :: English",
        # How mature is this project? Common values are
        #   3 - Alpha, 4 - Beta, 5 - Production/Stable
        "Development Status :: 3 - Alpha",
        # Indicate who your project is intended for
        "Intended Audience :: Developers",
        # Pick your license as you wish
        # 'License :: OSI Approved :: BSD License',
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
)
