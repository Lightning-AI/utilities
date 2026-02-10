from pathlib import Path

import pytest

from lightning_utilities.install.requirements import (
    _parse_requirements,
    _RequirementWithComment,
    load_requirements,
    yield_lines,
)

_PATH_ROOT = Path(__file__).parent.parent.parent.parent


def test_yield_lines_from_list():
    assert list(yield_lines(["foo", "  bar  ", "", "# comment", "baz"])) == ["foo", "bar", "baz"]


def test_yield_lines_from_string():
    assert list(yield_lines("foo\n  bar  \n\n# comment\nbaz")) == ["foo", "bar", "baz"]


def test_yield_lines_empty():
    assert list(yield_lines([])) == []
    assert list(yield_lines("")) == []


def test_requirement_with_comment_attributes():
    req = _RequirementWithComment("arrow>=1.0", comment="# my comment")
    assert req.name == "arrow"
    assert req.comment == "# my comment"
    assert req.pip_argument is None
    assert req.strict is False


def test_requirement_with_comment_strict():
    assert _RequirementWithComment("arrow>=1.0", comment="# strict").strict is True
    assert _RequirementWithComment("arrow>=1.0", comment="# Strict pinning").strict is True


def test_requirement_with_comment_pip_argument():
    req = _RequirementWithComment("arrow>=1.0", pip_argument="--extra-index-url https://x")
    assert req.pip_argument == "--extra-index-url https://x"

    with pytest.raises(RuntimeError, match="wrong pip argument"):
        _RequirementWithComment("arrow>=1.0", pip_argument="")


def test_adjust_none():
    assert _RequirementWithComment("arrow<=1.2,>=1.0").adjust("none") == "arrow<=1.2,>=1.0"
    assert (
        _RequirementWithComment("arrow<=1.2,>=1.0", comment="# strict").adjust("none") == "arrow<=1.2,>=1.0  # strict"
    )


def test_adjust_all():
    assert _RequirementWithComment("arrow<=1.2,>=1.0").adjust("all") == "arrow>=1.0"
    assert _RequirementWithComment("arrow>=1.0,<=1.2").adjust("all") == "arrow>=1.0"
    assert _RequirementWithComment("arrow<=1.2").adjust("all") == "arrow"
    assert _RequirementWithComment("arrow<=1.2,>=1.0", comment="# strict").adjust("all") == "arrow<=1.2,>=1.0  # strict"
    assert _RequirementWithComment("arrow").adjust("all") == "arrow"


def test_adjust_major():
    assert _RequirementWithComment("arrow>=1.2.0, <=1.2.2").adjust("major") == "arrow<2.0,>=1.2.0"
    assert _RequirementWithComment("lib>=0.5, <=0.9").adjust("major") == "lib<1.0,>=0.5"
    assert (
        _RequirementWithComment("arrow>=1.2.0, <=1.2.2", comment="# strict").adjust("major")
        == "arrow<=1.2.2,>=1.2.0  # strict"
    )
    assert _RequirementWithComment("arrow>=1.2.0").adjust("major") == "arrow>=1.2.0"


def test_adjust_invalid_unfreeze():
    with pytest.raises(ValueError, match="Unexpected unfreeze"):
        _RequirementWithComment("arrow>=1.0").adjust("invalid")


def test_parse_requirements_basic():
    reqs = list(_parse_requirements(["# comment", "", "numpy>=1.0", "pandas<2.0"]))
    assert [str(r) for r in reqs] == ["numpy>=1.0", "pandas<2.0"]


def test_parse_requirements_from_string():
    reqs = list(_parse_requirements("# comment\n\nnumpy>=1.0\npandas<2.0"))
    assert [str(r) for r in reqs] == ["numpy>=1.0", "pandas<2.0"]


def test_parse_requirements_preserves_comments():
    reqs = list(_parse_requirements(["arrow>=1.0 # strict"]))
    assert len(reqs) == 1
    assert reqs[0].comment == " # strict"
    assert reqs[0].strict is True


def test_parse_requirements_pip_argument():
    reqs = list(_parse_requirements(["--extra-index-url https://x", "torch>=2.0"]))
    assert len(reqs) == 1
    assert reqs[0].pip_argument == "--extra-index-url https://x"


def test_parse_requirements_skips():
    reqs = list(_parse_requirements(["-r other.txt", "pesq @ git+https://github.com/foo/bar", "numpy"]))
    assert len(reqs) == 1
    assert reqs[0].name == "numpy"


def test_load_requirements_core():
    path_req = str(_PATH_ROOT / "requirements")
    reqs = load_requirements(path_req, "core.txt", unfreeze="all")
    assert len(reqs) > 0
    # Verify that load_requirements returns a cleaned list of requirement strings
    assert all(isinstance(r, str) for r in reqs)
    assert all(r for r in reqs)  # no empty strings
    assert all(not r.lstrip().startswith("#") for r in reqs)  # no comment lines
    assert all(r == r.strip() for r in reqs)  # no leading/trailing whitespace


def test_load_requirements_nonexistent(tmpdir):
    with pytest.raises(FileNotFoundError):
        load_requirements(str(tmpdir), "nonexistent.txt")


def test_load_requirements_invalid_unfreeze(tmpdir):
    with pytest.raises(ValueError, match="unsupported"):
        load_requirements(str(tmpdir), "x.txt", unfreeze="bad")


def test_load_requirements_unfreeze_strategies(tmpdir):
    req_file = tmpdir / "test.txt"
    req_file.write("arrow>=1.2.0, <=1.2.2\n")

    assert load_requirements(str(tmpdir), "test.txt", unfreeze="none") == ["arrow<=1.2.2,>=1.2.0"]
    assert load_requirements(str(tmpdir), "test.txt", unfreeze="major") == ["arrow<2.0,>=1.2.0"]
    assert load_requirements(str(tmpdir), "test.txt", unfreeze="all") == ["arrow>=1.2.0"]
