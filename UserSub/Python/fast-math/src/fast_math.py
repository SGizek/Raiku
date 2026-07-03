"""
fast-math: High-performance math utilities for numerical computing.

Provides vectorised helpers for common numerical operations without
requiring NumPy as a mandatory dependency.
"""
from __future__ import annotations

import math
from typing import Sequence


# ---------------------------------------------------------------------------
# Basic numeric utilities
# ---------------------------------------------------------------------------

def clamp(value: float, lo: float, hi: float) -> float:
    """Clamp *value* to the range [lo, hi]."""
    if lo > hi:
        raise ValueError(f"clamp: lo ({lo}) must be <= hi ({hi})")
    return max(lo, min(hi, value))


def lerp(a: float, b: float, t: float) -> float:
    """Linear interpolation between *a* and *b* by factor *t* in [0, 1]."""
    return a + (b - a) * t


def sign(x: float) -> int:
    """Return -1, 0, or 1 depending on the sign of *x*."""
    if x > 0:
        return 1
    if x < 0:
        return -1
    return 0


def is_close(a: float, b: float, rel_tol: float = 1e-9, abs_tol: float = 0.0) -> bool:
    """Return True if *a* and *b* are approximately equal."""
    return math.isclose(a, b, rel_tol=rel_tol, abs_tol=abs_tol)


# ---------------------------------------------------------------------------
# Vector operations  (pure Python — no external dependencies)
# ---------------------------------------------------------------------------

Vec = Sequence[float]


def dot(u: Vec, v: Vec) -> float:
    """Dot product of two equal-length vectors."""
    if len(u) != len(v):
        raise ValueError(f"dot: vector length mismatch ({len(u)} vs {len(v)})")
    return sum(a * b for a, b in zip(u, v))


def magnitude(v: Vec) -> float:
    """Euclidean magnitude of a vector."""
    return math.sqrt(sum(x * x for x in v))


def normalise(v: Vec) -> list[float]:
    """Return a unit vector in the direction of *v*."""
    mag = magnitude(v)
    if mag == 0.0:
        raise ZeroDivisionError("Cannot normalise the zero vector")
    return [x / mag for x in v]


def cross3(u: Vec, v: Vec) -> list[float]:
    """Cross product of two 3D vectors."""
    if len(u) != 3 or len(v) != 3:
        raise ValueError("cross3: both vectors must have exactly 3 components")
    return [
        u[1] * v[2] - u[2] * v[1],
        u[2] * v[0] - u[0] * v[2],
        u[0] * v[1] - u[1] * v[0],
    ]


def add(u: Vec, v: Vec) -> list[float]:
    """Element-wise addition of two vectors."""
    if len(u) != len(v):
        raise ValueError("add: vector length mismatch")
    return [a + b for a, b in zip(u, v)]


def scale(v: Vec, s: float) -> list[float]:
    """Multiply every component of *v* by scalar *s*."""
    return [x * s for x in v]


# ---------------------------------------------------------------------------
# Statistics helpers
# ---------------------------------------------------------------------------

def mean(values: Sequence[float]) -> float:
    """Arithmetic mean of a sequence of numbers."""
    if not values:
        raise ValueError("mean: empty sequence")
    return sum(values) / len(values)


def variance(values: Sequence[float]) -> float:
    """Population variance."""
    if len(values) < 2:
        raise ValueError("variance: need at least 2 values")
    m = mean(values)
    return sum((x - m) ** 2 for x in values) / len(values)


def std_dev(values: Sequence[float]) -> float:
    """Population standard deviation."""
    return math.sqrt(variance(values))
