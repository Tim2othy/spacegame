"""
For the 2d-vector-type, and associated common operations.
"""

from typing import Literal
import numpy as np

Vec = np.ndarray[tuple[int, Literal[2]], np.dtype[np.float64]]


def new_vec(x: float, y: float) -> Vec:
    return np.array([x, y])


def distance(v: Vec, w: Vec) -> float:
    return np.sqrt(np.sum((v - w) ** 2))
