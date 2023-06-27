# Licensed under the Apache License, Version 2.0 (the "License");
#     http://www.apache.org/licenses/LICENSE-2.0
#
import glob
import logging
import os
import re
import urllib.request
from typing import List, Tuple


def _download_file(file_url: str, folder: str) -> str:
    fname = os.path.basename(file_url)
    file_path = os.path.join(folder, fname)
    if os.path.isfile(file_path):
        logging.warning(f'given file "{file_path}" already exists and will be overwritten with {file_url}')
    urllib.request.urlretrieve(file_url, file_path)
    return fname


def _search_all_occurrences(list_files: List[str], pattern: str) -> List[str]:
    collected = []
    for file_path in list_files:
        with open(file_path, encoding="UTF-8") as fo:
            body = fo.read()
        found = re.findall(pattern, body)
        collected += found
    return collected


def _replace_remote_with_local(file_path: str, pairs_url_path: List[Tuple[str, str]], base_depth: int = 2) -> None:
    depth = len(file_path.split(os.path.sep)) - base_depth - 1
    with open(file_path, encoding="UTF-8") as fo:
        body = fo.read()
    for url, fpath in pairs_url_path:
        if depth:
            path_up = [".."] * depth
            fpath = os.path.join(*path_up, fpath)
        body = body.replace(url, fpath)
    with open(file_path, "w", encoding="UTF-8") as fw:
        fw.write(body)


def fetch_external_assets(
    docs_folder: str = "docs/source",
    assets_folder: str = "_static/fetched_assets",
    file_pattern: str = "*.rst",
    retrieve_pattern: str = r"http[s]?://.*\.s3\..*",
) -> None:
    list_files = glob.glob(os.path.join(docs_folder, "**", file_pattern), recursive=True)

    urls = _search_all_occurrences(list_files, pattern=retrieve_pattern)
    target_folder = os.path.join(docs_folder, assets_folder)
    os.makedirs(target_folder, exist_ok=True)
    pairs_url_file = []
    for i, url in enumerate(set(urls)):
        logging.info(f" >> downloading ({i}/{len(urls)}): {url}")
        fname = _download_file(url, target_folder)
        pairs_url_file.append((url, os.path.join(assets_folder, fname)))

    for fpath in list_files:
        _replace_remote_with_local(fpath, pairs_url_file)
