"""Synthetic tests for refined quadratic Bézier pair intersections."""

from __future__ import annotations

import numpy as np
import pytest

from scripts.bezier_intersections import (
    algebraic_quadratic_bezier_intersections,
    coincident_overlap_evidence,
    find_quadratic_bezier_intersections,
    refine_intersection_seeds,
)


TOLERANCE = 1e-10


def straight(start: tuple[float, float], end: tuple[float, float]):
    p0 = np.array(start, dtype=float)
    p2 = np.array(end, dtype=float)
    return p0, (p0 + p2) / 2.0, p2


def roots(curve_a, curve_b):
    return find_quadratic_bezier_intersections(curve_a, curve_b, TOLERANCE)["roots"]


def test_two_straight_curves_cross_interior() -> None:
    result = roots(straight((-1.0, 0.0), (1.0, 0.0)), straight((0.0, -1.0), (0.0, 1.0)))
    assert len(result) == 1
    np.testing.assert_allclose(result[0]["point"], [0.0, 0.0], atol=TOLERANCE)
    assert 0.0 < result[0]["t_a"] < 1.0
    assert 0.0 < result[0]["t_b"] < 1.0


def test_exact_shared_endpoint() -> None:
    result = roots(straight((0.0, 0.0), (1.0, 0.0)), straight((1.0, 0.0), (1.0, 1.0)))
    assert len(result) == 1
    np.testing.assert_allclose(result[0]["point"], [1.0, 0.0], atol=TOLERANCE)


def test_endpoint_to_interior() -> None:
    result = roots(straight((0.0, 0.0), (1.0, 0.0)), straight((0.5, 0.0), (0.5, 1.0)))
    assert len(result) == 1
    np.testing.assert_allclose(result[0]["point"], [0.5, 0.0], atol=TOLERANCE)


def test_nonintersecting_and_parallel_curves() -> None:
    assert roots(straight((0.0, 0.0), (1.0, 0.0)), straight((0.0, 1.0), (1.0, 1.0))) == []
    assert roots(straight((0.0, 0.0), (1.0, 0.0)), straight((2.0, 0.0), (3.0, 0.0))) == []


def test_tangent_contact() -> None:
    arch = (np.array([-1.0, 0.0]), np.array([0.0, 2.0]), np.array([1.0, 0.0]))
    result = roots(arch, straight((-1.0, 1.0), (1.0, 1.0)))
    assert len(result) == 1
    np.testing.assert_allclose(result[0]["point"], [0.0, 1.0], atol=1e-7)
    assert result[0]["tangent_sine"] <= 1e-4


def test_one_pair_with_two_intersections() -> None:
    arch = (np.array([-1.0, 0.0]), np.array([0.0, 2.0]), np.array([1.0, 0.0]))
    result = roots(arch, straight((-1.0, 0.5), (1.0, 0.5)))
    assert len(result) == 2
    assert result[0]["t_a"] < result[1]["t_a"]


def test_zero_chord_anomaly_like_curve_retains_two_roots() -> None:
    out_and_back = (np.array([0.0, 0.0]), np.array([1.0, 0.0]), np.array([0.0, 0.0]))
    result = roots(out_and_back, straight((0.25, -1.0), (0.25, 1.0)))
    assert len(result) == 2


def test_duplicate_seeds_are_deduplicated() -> None:
    first = straight((-1.0, 0.0), (1.0, 0.0))
    second = straight((0.0, -1.0), (0.0, 1.0))
    accepted, rejected = refine_intersection_seeds(
        first, second, [(0.4, 0.4), (0.5, 0.5), (0.6, 0.6)], TOLERANCE
    )
    assert len(accepted) == 1
    assert rejected == []


def test_invalid_seed_is_reported_and_invalid_tolerance_rejected() -> None:
    first = straight((-1.0, 0.0), (1.0, 0.0))
    second = straight((0.0, -1.0), (0.0, 1.0))
    accepted, rejected = refine_intersection_seeds(
        first, second, [(float("nan"), 0.5)], TOLERANCE
    )
    assert accepted == []
    assert rejected[0]["reason"] == "invalid_seed"
    with pytest.raises(ValueError, match="greater than zero"):
        refine_intersection_seeds(first, second, [(0.5, 0.5)], 0.0)


def test_exact_coincident_and_collinear_overlap_evidence() -> None:
    first = straight((0.0, 0.0), (2.0, 0.0))
    assert coincident_overlap_evidence(first, first)["kind"] == "identical_control_points"
    second = straight((1.0, 0.0), (3.0, 0.0))
    assert coincident_overlap_evidence(first, second)["kind"] == "monotone_collinear_interval"


def test_algebraic_resultant_finds_two_roots_and_endpoint_root() -> None:
    arch = (np.array([-1.0, 0.0]), np.array([0.0, 2.0]), np.array([1.0, 0.0]))
    two = algebraic_quadratic_bezier_intersections(
        arch, straight((-1.0, 0.5), (1.0, 0.5)), TOLERANCE
    )
    assert len(two["roots"]) == 2
    endpoint = algebraic_quadratic_bezier_intersections(
        straight((0.0, 0.0), (1.0, 0.0)),
        straight((1.0, 0.0), (1.0, 1.0)),
        TOLERANCE,
    )
    assert len(endpoint["roots"]) == 1
