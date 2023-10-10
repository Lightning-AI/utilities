import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from scripts import _PATH_DATA, _PATH_SCRIPTS


@pytest.fixture()
def _backup_req_file(tmp_path) -> None:
    """Fixture restore input file after test ends."""
    req_file = "requirements_sample.txt"
    # save the input, so it can be restored in test end
    shutil.copy(Path(_PATH_DATA) / req_file, Path(tmp_path) / req_file)
    # this is where the testing happens
    yield
    # Teardown: restoring input data
    shutil.copy(Path(tmp_path) / req_file, Path(_PATH_DATA) / req_file)


def test_adjust_torch_versions_call(_backup_req_file):  # noqa: PT019
    path_script = os.path.join(_PATH_SCRIPTS, "adjust-torch-versions.py")
    path_req_file = os.path.join(_PATH_DATA, "requirements_sample.txt")
    path_expectation = os.path.join(_PATH_DATA, "requirements_expected.txt")

    return_code = subprocess.call([sys.executable, path_script, path_req_file, "1.10.0"])  # noqa: S603
    assert return_code == 0
    with open(path_req_file, encoding="utf8") as fopen:
        req_result = fopen.readlines()
    with open(path_expectation, encoding="utf8") as fopen:
        req_expected = fopen.readlines()
    assert req_result == req_expected
