# Licensed under the Apache License, Version 2.0 (the "License");
#     http://www.apache.org/licenses/LICENSE-2.0
#
import glob
import importlib
import inspect
import logging
import os
import re
import sys
from typing import Iterable, Optional, Tuple, Union


def _transform_changelog(path_in: str, path_out: str) -> None:
    """Adjust changelog titles so not to be duplicated.

    Args:
        path_in: input MD file
        path_out: output also MD file

    """
    with open(path_in) as fp:
        chlog_lines = fp.readlines()
    # enrich short subsub-titles to be unique
    chlog_ver = ""
    for i, ln in enumerate(chlog_lines):
        if ln.startswith("## "):
            chlog_ver = ln[2:].split("-")[0].strip()
        elif ln.startswith("### "):
            ln = ln.replace("###", f"### {chlog_ver} -")
            chlog_lines[i] = ln
    with open(path_out, "w") as fp:
        fp.writelines(chlog_lines)


def _linkcode_resolve(domain: str, github_user: str, github_repo: str, info: dict) -> str:
    def find_source() -> Tuple[str, int, int]:
        # try to find the file and line number, based on code from numpy:
        # https://github.com/numpy/numpy/blob/master/doc/source/conf.py#L286
        obj = sys.modules[info["module"]]
        for part in info["fullname"].split("."):
            obj = getattr(obj, part)
        fname = str(inspect.getsourcefile(obj))
        # https://github.com/rtfd/readthedocs.org/issues/5735
        if any(s in fname for s in ("readthedocs", "rtfd", "checkouts")):
            # /home/docs/checkouts/readthedocs.org/user_builds/pytorch_lightning/checkouts/
            #  devel/pytorch_lightning/utilities/cls_experiment.py#L26-L176
            path_top = os.path.abspath(os.path.join("..", "..", ".."))
            fname = str(os.path.relpath(fname, start=path_top))
        else:
            # Local build, imitate master
            fname = f'master/{os.path.relpath(fname, start=os.path.abspath(".."))}'
        source, line_start = inspect.getsourcelines(obj)
        return fname, line_start, line_start + len(source) - 1

    if domain != "py" or not info["module"]:
        return ""
    try:
        filename = "%s#L%d-L%d" % find_source()
    except Exception:
        filename = info["module"].replace(".", "/") + ".py"
    # import subprocess
    # tag = subprocess.Popen(['git', 'rev-parse', 'HEAD'], stdout=subprocess.PIPE,
    #                        universal_newlines=True).communicate()[0][:-1]
    branch = filename.split("/")[0]
    # do mapping from latest tags to master
    branch = {"latest": "master", "stable": "master"}.get(branch, branch)
    filename = "/".join([branch] + filename.split("/")[1:])
    return f"https://github.com/{github_user}/{github_repo}/blob/{filename}"


def _update_link_based_imported_package(link: str, pkg_ver: str, version_digits: Optional[int]) -> str:
    """Adjust the linked external docs to be local.

    Args:
        link: the source link to be replaced
        pkg_ver: the target link to be replaced, if ``{package.version}`` is included it will be replaced accordingly
        version_digits: for semantic versioning, how many digits to be considered

    """
    pkg_att = pkg_ver.split(".")
    # load the package with all additional sub-modules
    module = importlib.import_module(".".join(pkg_att[:-1]))
    # load the attribute
    ver = getattr(module, pkg_att[-1])
    # drop any additional context after `+`
    ver = ver.split("+")[0]
    # crop the version to the number of digits
    ver = ".".join(ver.split(".")[:version_digits])
    # replace the version
    return link.replace(f"{{{pkg_ver}}}", ver)


def _adjust_linked_external_docs(
    source_link: str,
    target_link: str,
    browse_folder: Union[str, Iterable[str]],
    file_extensions: Iterable[str] = (".rst", ".py"),
    version_digits: int = 2,
) -> None:
    r"""Adjust the linked external docs to be local.

    Args:
        source_link: the link to be replaced
        target_link: the link to be replaced, if ``{package.version}`` is included it will be replaced accordingly
        browse_folder: the location of the browsable folder
        file_extensions: what kind of files shall be scanned
        version_digits: for semantic versioning, how many digits to be considered

    Examples:
        >>> _adjust_linked_external_docs(
        ...     "https://numpy.org/doc/stable/",
        ...     "https://numpy.org/doc/{numpy.__version__}/",
        ...     "docs/source",
        ... )

    """
    list_files = []
    if isinstance(browse_folder, str):
        browse_folder = [browse_folder]
    for folder in browse_folder:
        for ext in file_extensions:
            list_files += glob.glob(os.path.join(folder, "**", f"*{ext}"), recursive=True)
    if not list_files:
        logging.warning(f'no files were listed in folder "{browse_folder}" and pattern "{file_extensions}"')
        return

    # find the expression for package version in {} brackets if any, use re to find it
    pkg_ver_all = re.findall(r"{([\w.]+)}", target_link)
    for pkg_ver in pkg_ver_all:
        target_link = _update_link_based_imported_package(target_link, pkg_ver, version_digits)

    # replace the source link with target link
    for fpath in set(list_files):
        with open(fpath, encoding="UTF-8") as fopen:
            body = fopen.read()
        body = body.replace(source_link, target_link)
        with open(fpath, "w", encoding="UTF-8") as fw:
            fw.write(body)
