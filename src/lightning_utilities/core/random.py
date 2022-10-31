import random

from lightning_utilities.core.imports import package_available


def seed_all(seed):
    random.seed(seed)
    if package_available("numpy"):
        import numpy

        numpy.random.seed(seed)
    if package_available("torch"):
        import torch

        torch.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
