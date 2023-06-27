import os.path

from unittests import _PATH_ROOT
from lightning_utilities.docs import fetch_external_assets


def test_retriever_s3():
    path_docs = os.path.join(_PATH_ROOT, "docs", "source")
    fetch_external_assets(docs_folder=path_docs)
    with open(os.path.join(path_docs, "index.rst"), encoding="UTF-8") as fo:
        page = fo.read()
    # that the image exists~
    assert "Lightning.gif" in page
    # but it is not sourced from S3
    assert ".s3." not in page