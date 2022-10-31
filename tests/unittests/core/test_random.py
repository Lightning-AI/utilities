import random

from lightning_utilities.core.imports import package_available
from lightning_utilities.core.random import seed_all


def test_seed():
    seed_all(42)

    assert random.randint(0, 1000) == 654

    if package_available("numpy"):
        import numpy

        assert numpy.random.randint(0, 1000) == 102

    if package_available("torch"):
        import torch

        assert torch.randint(0, 1000, size=(2,)).numpy().tolist() == [542, 67]
