import re
import warnings
from contextlib import contextmanager
from typing import Type, Optional, Generator


@contextmanager
def no_warning_call(expected_warning: Type[Warning] = Warning, match: Optional[str] = None) -> Generator:
    with warnings.catch_warnings(record=True) as record:
        yield

    for w in record:
        if issubclass(w.category, expected_warning) and (match is None or re.compile(match).search(w.message.args[0])):
            msg = "A warning" if expected_warning is None else f"`{expected_warning.__name__}`"
            raise AssertionError(f"{msg} was raised: {w.message!r}")
