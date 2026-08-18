"""Focused mathematical helpers for quadratic Bézier geometry."""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike, NDArray


def quadratic_bezier_point(
    p0: ArrayLike,
    p1: ArrayLike,
    p2: ArrayLike,
    t: ArrayLike,
) -> NDArray[np.float64]:
    """Evaluate a planar quadratic Bézier curve without mutating inputs.

    Parameters
    ----------
    p0, p1, p2
        Finite XY control coordinates, each with shape ``(2,)``.
    t
        A finite scalar or array of parameters in the closed interval [0, 1].

    Returns
    -------
    numpy.ndarray
        For scalar ``t``, an XY array with shape ``(2,)``. For array ``t``,
        an array with shape ``t.shape + (2,)``.
    """
    control_points = tuple(np.asarray(point, dtype=np.float64) for point in (p0, p1, p2))
    for name, point in zip(("p0", "p1", "p2"), control_points, strict=True):
        if point.shape != (2,):
            raise ValueError(f"{name} must have shape (2,), received {point.shape}")
        if not np.all(np.isfinite(point)):
            raise ValueError(f"{name} must contain only finite values")

    parameter = np.asarray(t, dtype=np.float64)
    if not np.all(np.isfinite(parameter)):
        raise ValueError("t must contain only finite values")
    if np.any((parameter < 0.0) | (parameter > 1.0)):
        raise ValueError("t must be within the closed interval [0, 1]")

    p0_array, p1_array, p2_array = control_points
    one_minus_t = 1.0 - parameter
    return (
        one_minus_t[..., np.newaxis] ** 2 * p0_array
        + 2.0 * one_minus_t[..., np.newaxis] * parameter[..., np.newaxis] * p1_array
        + parameter[..., np.newaxis] ** 2 * p2_array
    )
