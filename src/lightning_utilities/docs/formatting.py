# Licensed under the Apache License, Version 2.0 (the "License");
#     http://www.apache.org/licenses/LICENSE-2.0
#
import glob
import os
import re


def _transform_changelog(path_in: str, path_out: str) -> None:
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


def _convert_markdown(path_in: str, path_out: str, path_root: str) -> None:
    with open(path_in) as fp:
        readme = fp.read()
    # TODO: temp fix removing SVG badges and GIF, because PDF cannot show them
    readme = re.sub(r"(\[!\[.*\))", "", readme)
    readme = re.sub(r"(!\[.*.gif\))", "", readme)
    folder_names = (os.path.basename(p) for p in glob.glob(os.path.join(path_root, "*")) if os.path.isdir(p))
    for dir_name in folder_names:
        readme = readme.replace("](%s/" % dir_name, "](%s/" % os.path.join(path_root, dir_name))
    with open(path_out, "w") as fp:
        fp.write(readme)