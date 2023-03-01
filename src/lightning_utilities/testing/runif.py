# Copyright The PyTorch Lightning team.
# Licensed under the Apache License, Version 2.0 (the "License");
#     http://www.apache.org/licenses/LICENSE-2.0
#
import operator
import os
import platform
import sys
from typing import Any, Optional

from packaging.version import Version

from lightning_utilities.core.imports import compare_version


class RunIf:
    """RunIf wrapper for simple marking specific cases, fully compatible with `pytest.mark`.

    Example:
        @RunIf(min_torch="0.0")
        @pytest.mark.parametrize("arg1", [1, 2.0])
        def test_wrapper(arg1):
            assert arg1 > 0.0
    """

    def __new__(
        cls,
        *args: Any,
        min_torch: Optional[str] = None,
        max_torch: Optional[str] = None,
        min_python: Optional[str] = None,
        skip_windows: bool = False,
        standalone: bool = False,
        min_cuda_gpus: int = 0,
        is_mps_gpu: Optional[bool] = None,
        **kwargs: Any,
    ):
        """Configure the wrapper.

        Args:
            *args: Any :class:`pytest.mark.skipif` arguments.
            min_torch: Require that PyTorch is greater or equal than this version.
            max_torch: Require that PyTorch is less than this version.
            min_python: Require that Python is greater or equal than this version.
            skip_windows: Skip for Windows platform.
            standalone: Mark the test as standalone, our CI will run it in a separate process.
            This requires that the ``RUN_STANDALONE_TESTS=1`` environment variable is set.
            min_cuda_gpus: Require this number of gpus and that the ``PL_RUN_CUDA_TESTS=1`` environment variable is set.
            is_mps_gpu: If True: Require that MPS (Apple Silicon) is available,
            if False: Explicitly Require that MPS is not available
            **kwargs: Any :class:`pytest.mark.skipif` keyword arguments.
        """
        import pytest

        conditions = []
        reasons = []

        if min_torch:
            import torch

            # set use_base_version for nightly support
            conditions.append(compare_version("torch", operator.lt, min_torch, use_base_version=True))
            reasons.append(f"torch>={min_torch}, {torch.__version__} installed")

        if max_torch:
            import torch

            # set use_base_version for nightly support
            conditions.append(compare_version("torch", operator.ge, max_torch, use_base_version=True))
            reasons.append(f"torch<{max_torch}, {torch.__version__} installed")

        if min_python:
            py_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
            conditions.append(Version(py_version) < Version(min_python))
            reasons.append(f"python>={min_python}")

        if skip_windows:
            conditions.append(sys.platform == "win32")
            reasons.append("unimplemented on Windows")

        if standalone:
            env_flag = os.getenv("RUN_STANDALONE_TESTS", "0")
            conditions.append(env_flag != "1")
            reasons.append("Standalone execution")
            # used in conftest.py::pytest_collection_modifyitems
            kwargs["standalone"] = True

        if min_cuda_gpus:
            import torch

            conditions.append(torch.cuda.device_count() < min_cuda_gpus)
            reasons.append(f"GPUs>={min_cuda_gpus}")
            # used in conftest.py::pytest_collection_modifyitems
            kwargs["min_cuda_gpus"] = True

        if is_mps_gpu is not None:
            import torch

            mps = (
                compare_version("torch", operator.lt, "1.12", use_base_version=True)
                and torch.backends.mps.is_available()
                and platform.processor() in ("arm", "arm64")
            )
            if mps:
                conditions.append(not mps)
                reasons.append("Apple MPS graphic card")
            else:
                conditions.append(mps)
                reasons.append("not Apple MPS graphic card")

        reasons = [rs for cond, rs in zip(conditions, reasons) if cond]
        return pytest.mark.skipif(
            *args, condition=any(conditions), reason=f"Requires: [{' + '.join(reasons)}]", **kwargs
        )
