"""Synthetic mathematical tests for the quadratic Bézier evaluator."""

from __future__ import annotations

import numpy as np
import pytest

from scripts.bezier_geometry import (
    adaptive_quadratic_bezier_polyline,
    quadratic_bezier_point,
)


def test_startpoint_identity() -> None:
    p0 = np.array([1.25, -3.5])
    result = quadratic_bezier_point(p0, [8.0, 2.0], [4.5, 9.0], 0.0)
    np.testing.assert_array_equal(result, p0)


def test_endpoint_identity() -> None:
    p2 = np.array([4.5, 9.0])
    result = quadratic_bezier_point([1.25, -3.5], [8.0, 2.0], p2, 1.0)
    np.testing.assert_array_equal(result, p2)


def test_midpoint_control_point_produces_straight_line() -> None:
    p0 = np.array([-2.0, 1.0])
    p2 = np.array([6.0, 5.0])
    p1 = (p0 + p2) / 2.0
    t = np.linspace(0.0, 1.0, 17)

    result = quadratic_bezier_point(p0, p1, p2, t)
    expected = p0 + t[:, np.newaxis] * (p2 - p0)

    np.testing.assert_allclose(result, expected)


def test_known_midpoint_identity() -> None:
    p0 = np.array([0.0, 2.0])
    p1 = np.array([3.0, 8.0])
    p2 = np.array([10.0, -2.0])
    expected = 0.25 * p0 + 0.5 * p1 + 0.25 * p2

    np.testing.assert_allclose(quadratic_bezier_point(p0, p1, p2, 0.5), expected)


def test_finite_output_and_input_immutability() -> None:
    p0 = np.array([0.0, 0.0])
    p1 = np.array([1.0, 2.0])
    p2 = np.array([3.0, 1.0])
    originals = tuple(point.copy() for point in (p0, p1, p2))

    result = quadratic_bezier_point(p0, p1, p2, np.linspace(0.0, 1.0, 11))

    assert np.all(np.isfinite(result))
    for point, original in zip((p0, p1, p2), originals, strict=True):
        np.testing.assert_array_equal(point, original)


@pytest.mark.parametrize("invalid_t", [-0.0001, 1.0001, [0.0, 0.5, 1.1]])
def test_rejects_parameter_outside_closed_unit_interval(invalid_t: object) -> None:
    with pytest.raises(ValueError, match=r"closed interval \[0, 1\]"):
        quadratic_bezier_point([0.0, 0.0], [0.5, 0.5], [1.0, 1.0], invalid_t)


def test_adaptive_straight_curve_uses_only_endpoints() -> None:
    vertices = adaptive_quadratic_bezier_polyline(
        [0.0, 0.0], [5.0, 0.0], [10.0, 0.0], 1e-6
    )
    np.testing.assert_array_equal(vertices, [[0.0, 0.0], [10.0, 0.0]])


def test_adaptive_curved_curve_preserves_endpoints_and_is_finite() -> None:
    p0 = np.array([0.0, 0.0])
    p2 = np.array([10.0, 0.0])
    vertices = adaptive_quadratic_bezier_polyline(p0, [5.0, 8.0], p2, 0.05)

    assert len(vertices) > 2
    np.testing.assert_array_equal(vertices[0], p0)
    np.testing.assert_array_equal(vertices[-1], p2)
    assert np.all(np.isfinite(vertices))


def test_adaptive_vertices_follow_increasing_curve_parameter() -> None:
    vertices = adaptive_quadratic_bezier_polyline(
        [0.0, 0.0], [4.0, 8.0], [10.0, 1.0], 0.01
    )
    assert np.all(np.diff(vertices[:, 0]) > 0.0)


def test_tighter_tolerance_is_never_coarser() -> None:
    curve = ([0.0, 0.0], [4.0, 12.0], [10.0, 0.0])
    loose = adaptive_quadratic_bezier_polyline(*curve, 0.5)
    tight = adaptive_quadratic_bezier_polyline(*curve, 0.01)
    assert len(tight) >= len(loose)


def test_zero_chord_excursion_is_not_collapsed() -> None:
    p0 = np.array([2.0, -1.0])
    p1 = np.array([2.2, -0.7])
    vertices = adaptive_quadratic_bezier_polyline(p0, p1, p0, 0.01)

    assert len(vertices) >= 3
    np.testing.assert_array_equal(vertices[0], p0)
    np.testing.assert_array_equal(vertices[-1], p0)
    assert np.max(np.linalg.norm(vertices - p0, axis=1)) > 0.0
    assert np.all(np.isfinite(vertices))


@pytest.mark.parametrize("invalid_tolerance", [0.0, -1.0, np.inf, np.nan])
def test_adaptive_rejects_invalid_tolerance(invalid_tolerance: float) -> None:
    with pytest.raises(ValueError, match="greater than zero"):
        adaptive_quadratic_bezier_polyline(
            [0.0, 0.0], [0.5, 1.0], [1.0, 0.0], invalid_tolerance
        )
