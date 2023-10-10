import os
import subprocess
import sys

from scripts import _PATH_DATA, _PATH_SCRIPTS


def test_adjust_torch_versions_call():
    path_script = os.path.join(_PATH_SCRIPTS, "adjust-torch-versions.py")
    path_req_file = os.path.join(_PATH_DATA, "req_input.txt")
    path_expectation = os.path.join(_PATH_DATA, "req_expected.txt")
    # save the input so it can be restored in test end
    with open(path_req_file) as fopen:
        req_input = fopen.read()

    return_code = subprocess.call([sys.executable, path_script, path_req_file, "1.10.0"])  # noqa: S603
    assert return_code == 0
    with open(path_req_file) as fopen:
        req_result = fopen.read()
    with open(path_expectation) as fopen:
        req_expected = fopen.read()
    assert req_result == req_expected

    # restoring input data
    with open(path_req_file, "w") as fopen:
        fopen.write(req_input)
