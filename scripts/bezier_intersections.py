"""Numerically refined intersections between planar quadratic Bézier curves."""

from __future__ import annotations

import itertools
from typing import Iterable

import numpy as np
from numpy.typing import ArrayLike, NDArray
from scipy.optimize import least_squares

try:  # Support both package import in tests and direct script execution.
    from .bezier_geometry import (
        quadratic_bezier_derivative,
        quadratic_bezier_point,
        subdivide_quadratic_bezier,
    )
except ImportError:  # pragma: no cover - exercised by the Phase 8 CLI
    from bezier_geometry import (  # type: ignore[no-redef]
        quadratic_bezier_derivative,
        quadratic_bezier_point,
        subdivide_quadratic_bezier,
    )


Curve = tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]]


def cross_2d(first: NDArray[np.float64], second: NDArray[np.float64]) -> float:
    return float(first[0] * second[1] - first[1] * second[0])


def _curve(points: Iterable[ArrayLike]) -> Curve:
    values = tuple(np.asarray(point, dtype=np.float64) for point in points)
    if len(values) != 3:
        raise ValueError("a quadratic Bézier requires exactly three XY control points")
    for point in values:
        if point.shape != (2,) or not np.all(np.isfinite(point)):
            raise ValueError("quadratic Bézier control points must be finite XY values")
    return values  # type: ignore[return-value]


def analytic_quadratic_bounds(points: Iterable[ArrayLike]) -> tuple[float, float, float, float]:
    """Return exact axis-aligned bounds, including interior quadratic extrema."""
    p0, p1, p2 = _curve(points)
    candidates = [p0, p2]
    denominator = p0 - 2.0 * p1 + p2
    for axis in (0, 1):
        if denominator[axis] == 0.0:
            continue
        parameter = (p0[axis] - p1[axis]) / denominator[axis]
        if 0.0 < parameter < 1.0:
            candidates.append(quadratic_bezier_point(p0, p1, p2, parameter))
    coordinates = np.vstack(candidates)
    return (
        float(np.min(coordinates[:, 0])),
        float(np.min(coordinates[:, 1])),
        float(np.max(coordinates[:, 0])),
        float(np.max(coordinates[:, 1])),
    )


def bounds_overlap(
    first: tuple[float, float, float, float],
    second: tuple[float, float, float, float],
    padding: float = 0.0,
) -> bool:
    return not (
        first[2] < second[0] - padding
        or second[2] < first[0] - padding
        or first[3] < second[1] - padding
        or second[3] < first[1] - padding
    )


def _control_bounds(curve: Curve) -> tuple[float, float, float, float]:
    points = np.vstack(curve)
    return (
        float(np.min(points[:, 0])),
        float(np.min(points[:, 1])),
        float(np.max(points[:, 0])),
        float(np.max(points[:, 1])),
    )


def recursive_intersection_seeds(
    curve_a: Iterable[ArrayLike],
    curve_b: Iterable[ArrayLike],
    *,
    parameter_box_tolerance: float = 2.0**-12,
    maximum_states: int = 200_000,
) -> list[tuple[float, float]]:
    """Discover root seeds using independent conservative control-box subdivision.

    Quadratic curves lie within the convex hull of their control points, so
    disjoint control-point boxes safely reject a parameter-box pair. Remaining
    boxes are bisected by de Casteljau until both parameter intervals are small.
    """
    first = _curve(curve_a)
    second = _curve(curve_b)
    tolerance = float(parameter_box_tolerance)
    if not np.isfinite(tolerance) or tolerance <= 0.0 or tolerance >= 1.0:
        raise ValueError("parameter_box_tolerance must be finite and within (0, 1)")
    if maximum_states < 1:
        raise ValueError("maximum_states must be positive")

    stack = [(first, 0.0, 1.0, second, 0.0, 1.0)]
    seeds: list[tuple[float, float]] = []
    processed = 0
    while stack:
        processed += 1
        if processed > maximum_states:
            raise RuntimeError("recursive intersection isolation exceeded maximum_states")
        controls_a, ta0, ta1, controls_b, ub0, ub1 = stack.pop()
        box_a = _control_bounds(controls_a)
        box_b = _control_bounds(controls_b)
        if not bounds_overlap(box_a, box_b):
            continue
        width_a = ta1 - ta0
        width_b = ub1 - ub0
        if width_a <= tolerance and width_b <= tolerance:
            seeds.append(((ta0 + ta1) / 2.0, (ub0 + ub1) / 2.0))
            continue

        diagonal_a = float(np.hypot(box_a[2] - box_a[0], box_a[3] - box_a[1]))
        diagonal_b = float(np.hypot(box_b[2] - box_b[0], box_b[3] - box_b[1]))
        if width_a > tolerance and (
            width_b <= tolerance or diagonal_a >= diagonal_b
        ):
            left, right = subdivide_quadratic_bezier(*controls_a)
            midpoint = (ta0 + ta1) / 2.0
            stack.append((right, midpoint, ta1, controls_b, ub0, ub1))
            stack.append((left, ta0, midpoint, controls_b, ub0, ub1))
        else:
            left, right = subdivide_quadratic_bezier(*controls_b)
            midpoint = (ub0 + ub1) / 2.0
            stack.append((controls_a, ta0, ta1, right, midpoint, ub1))
            stack.append((controls_a, ta0, ta1, left, ub0, midpoint))

    deduplicated: list[tuple[float, float]] = []
    for seed in sorted(seeds):
        if not any(
            abs(seed[0] - existing[0]) <= tolerance
            and abs(seed[1] - existing[1]) <= tolerance
            for existing in deduplicated
        ):
            deduplicated.append(seed)
    return deduplicated


def refine_intersection_seeds(
    curve_a: Iterable[ArrayLike],
    curve_b: Iterable[ArrayLike],
    seeds: Iterable[tuple[float, float]],
    residual_tolerance: float,
    *,
    root_parameter_equivalence: float = 1e-8,
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    """Bound-refine seeds and return distinct accepted roots plus rejected attempts."""
    first = _curve(curve_a)
    second = _curve(curve_b)
    residual_limit = float(residual_tolerance)
    if not np.isfinite(residual_limit) or residual_limit <= 0.0:
        raise ValueError("residual_tolerance must be finite and greater than zero")
    if root_parameter_equivalence <= 0.0:
        raise ValueError("root_parameter_equivalence must be greater than zero")
    all_controls = np.vstack([*first, *second])
    characteristic_scale = max(float(np.ptp(all_controls, axis=0).max()), residual_limit)
    effective_parameter_equivalence = max(
        root_parameter_equivalence,
        2.0 * float(np.sqrt(residual_limit / characteristic_scale)),
    )

    roots: list[dict[str, object]] = []
    rejected: list[dict[str, object]] = []

    def residual(parameters: NDArray[np.float64]) -> NDArray[np.float64]:
        return quadratic_bezier_point(*first, parameters[0]) - quadratic_bezier_point(
            *second, parameters[1]
        )

    for raw_seed in seeds:
        seed = np.asarray(raw_seed, dtype=np.float64)
        if seed.shape != (2,) or not np.all(np.isfinite(seed)):
            rejected.append({"seed": list(raw_seed), "reason": "invalid_seed"})
            continue
        seed = np.clip(seed, 0.0, 1.0)
        initial_difference = residual(seed)
        initial_residual = float(np.linalg.norm(initial_difference))
        if initial_residual <= residual_limit:
            parameters = seed
            result_status = 0
            result_message = "seed already satisfies residual tolerance"
            residual_norm = initial_residual
        else:
            result = least_squares(
                residual,
                seed,
                bounds=([0.0, 0.0], [1.0, 1.0]),
                xtol=1e-14,
                ftol=1e-14,
                gtol=1e-14,
                max_nfev=1000,
            )
            parameters = result.x
            difference = residual(parameters)
            residual_norm = float(np.linalg.norm(difference))
            result_status = int(result.status)
            result_message = result.message
            if (
                not result.success
                or not np.isfinite(residual_norm)
                or residual_norm > residual_limit
            ):
                rejected.append(
                    {
                        "seed": seed.tolist(),
                        "parameters": parameters.tolist(),
                        "residual": residual_norm,
                        "reason": "not_converged_within_residual",
                    }
                )
                continue
        point_a = quadratic_bezier_point(*first, parameters[0])
        point_b = quadratic_bezier_point(*second, parameters[1])
        point = (point_a + point_b) / 2.0
        candidate = {
            "t_a": float(parameters[0]),
            "t_b": float(parameters[1]),
            "point": point,
            "residual": residual_norm,
            "solver_status": result_status,
            "solver_message": result_message,
        }
        duplicate_index = next((
            index
            for index, root in enumerate(roots)
            if
            abs(candidate["t_a"] - root["t_a"]) <= effective_parameter_equivalence
            and abs(candidate["t_b"] - root["t_b"]) <= effective_parameter_equivalence
        ), None)
        if duplicate_index is None:
            roots.append(candidate)
        elif candidate["residual"] < roots[duplicate_index]["residual"]:
            roots[duplicate_index] = candidate

    roots.sort(key=lambda root: (root["t_a"], root["t_b"]))
    return roots, rejected


def parameters_for_point_on_curve(
    curve: Iterable[ArrayLike], point: ArrayLike, residual_tolerance: float
) -> list[float]:
    """Solve quadratic coordinate polynomials and retain full-XY point roots."""
    controls = _curve(curve)
    target = np.asarray(point, dtype=np.float64)
    if target.shape != (2,) or not np.all(np.isfinite(target)):
        raise ValueError("point must be finite XY")
    p0, p1, p2 = controls
    quadratic = p0 - 2.0 * p1 + p2
    linear = 2.0 * (p1 - p0)
    constant = p0 - target
    axis = int(np.argmax(np.maximum(np.abs(quadratic), np.abs(linear))))
    coefficients = np.trim_zeros(
        np.array([quadratic[axis], linear[axis], constant[axis]], dtype=np.float64),
        trim="f",
    )
    if len(coefficients) <= 1:
        return [0.0, 1.0] if np.linalg.norm(p0 - target) <= residual_tolerance else []
    candidates = np.roots(coefficients)
    accepted = []
    for candidate in candidates:
        if abs(float(candidate.imag)) > 1e-10:
            continue
        parameter = float(candidate.real)
        if -1e-12 <= parameter <= 1.0 + 1e-12:
            parameter = min(max(parameter, 0.0), 1.0)
            if (
                np.linalg.norm(quadratic_bezier_point(*controls, parameter) - target)
                <= residual_tolerance
            ):
                accepted.append(parameter)
    return sorted(
        parameter
        for index, parameter in enumerate(accepted)
        if not any(abs(parameter - earlier) <= 1e-10 for earlier in accepted[:index])
    )


def _permutation_sign(permutation: tuple[int, ...]) -> int:
    inversions = sum(
        permutation[i] > permutation[j]
        for i in range(len(permutation))
        for j in range(i + 1, len(permutation))
    )
    return -1 if inversions % 2 else 1


def _polynomial_determinant(
    matrix: list[list[np.polynomial.Polynomial]],
) -> np.polynomial.Polynomial:
    size = len(matrix)
    result = np.polynomial.Polynomial([0.0])
    for permutation in itertools.permutations(range(size)):
        term = np.polynomial.Polynomial([float(_permutation_sign(permutation))])
        for row, column in enumerate(permutation):
            term *= matrix[row][column]
        result += term
    return result


def algebraic_intersection_seeds(
    curve_a: Iterable[ArrayLike],
    curve_b: Iterable[ArrayLike],
    residual_tolerance: float,
) -> tuple[list[tuple[float, float]], dict[str, object]]:
    """Find all real unit-square root seeds using a Sylvester resultant.

    The two XY equations are treated as polynomials in ``u`` whose
    coefficients are polynomials in ``t``. The determinant of their Sylvester
    matrix eliminates ``u``. Candidate real ``t`` roots are mapped back to all
    matching ``u`` roots and subsequently require bounded residual refinement.
    """
    first = _curve(curve_a)
    second = _curve(curve_b)
    if residual_tolerance <= 0.0 or not np.isfinite(residual_tolerance):
        raise ValueError("residual_tolerance must be finite and greater than zero")

    a0, a1, a2 = first[0], 2.0 * (first[1] - first[0]), first[0] - 2.0 * first[1] + first[2]
    b0, b1, b2 = second[0], 2.0 * (second[1] - second[0]), second[0] - 2.0 * second[1] + second[2]
    endpoint_seeds = []
    for parameter_t in (0.0, 1.0):
        point = quadratic_bezier_point(*first, parameter_t)
        endpoint_seeds.extend(
            (parameter_t, parameter_u)
            for parameter_u in parameters_for_point_on_curve(
                second, point, residual_tolerance
            )
        )
    for parameter_u in (0.0, 1.0):
        point = quadratic_bezier_point(*second, parameter_u)
        endpoint_seeds.extend(
            (parameter_t, parameter_u)
            for parameter_t in parameters_for_point_on_curve(
                first, point, residual_tolerance
            )
        )
    equations = []
    for axis in (0, 1):
        coefficients = [
            np.polynomial.Polynomial([-b2[axis]]),
            np.polynomial.Polynomial([-b1[axis]]),
            np.polynomial.Polynomial([a0[axis] - b0[axis], a1[axis], a2[axis]]),
        ]
        while len(coefficients) > 1 and np.all(coefficients[0].coef == 0.0):
            coefficients.pop(0)
        equations.append(coefficients)

    degree_first = len(equations[0]) - 1
    degree_second = len(equations[1]) - 1
    size = degree_first + degree_second
    if size == 0:
        return endpoint_seeds, {"status": "both_coordinate_equations_independent_of_u"}
    zero = np.polynomial.Polynomial([0.0])
    matrix = [[zero for _ in range(size)] for _ in range(size)]
    for row in range(degree_second):
        for offset, coefficient in enumerate(equations[0]):
            matrix[row][row + offset] = coefficient
    for local_row in range(degree_first):
        row = degree_second + local_row
        for offset, coefficient in enumerate(equations[1]):
            matrix[row][local_row + offset] = coefficient
    resultant = _polynomial_determinant(matrix)
    coefficients = np.trim_zeros(resultant.coef, trim="b")
    coefficient_scale = max(
        1.0,
        float(np.max(np.abs(np.vstack([*first, *second])))) ** max(1, size),
    )
    if len(coefficients) == 0 or np.max(np.abs(coefficients)) <= np.finfo(float).eps * coefficient_scale * 100.0:
        return endpoint_seeds, {
            "status": "degenerate_or_coincident_resultant",
            "resultant_coefficients": resultant.coef.tolist(),
        }

    roots_t = np.polynomial.Polynomial(coefficients).roots()
    seeds = list(endpoint_seeds)
    for root_t in roots_t:
        if abs(float(root_t.imag)) > 1e-7:
            continue
        parameter_t = float(root_t.real)
        if not -1e-10 <= parameter_t <= 1.0 + 1e-10:
            continue
        parameter_t = min(max(parameter_t, 0.0), 1.0)
        point = quadratic_bezier_point(*first, parameter_t)
        u_quadratic = second[0] - 2.0 * second[1] + second[2]
        u_linear = 2.0 * (second[1] - second[0])
        u_constant = second[0] - point
        axis = int(np.argmax(np.maximum(np.abs(u_quadratic), np.abs(u_linear))))
        u_coefficients = np.trim_zeros(
            np.array(
                [u_quadratic[axis], u_linear[axis], u_constant[axis]],
                dtype=np.float64,
            ),
            trim="f",
        )
        if len(u_coefficients) > 1:
            for root_u in np.roots(u_coefficients):
                if abs(float(root_u.imag)) <= 1e-7 and -1e-10 <= root_u.real <= 1.0 + 1e-10:
                    seeds.append(
                        (parameter_t, min(max(float(root_u.real), 0.0), 1.0))
                    )


    seeds.sort()
    unique = []
    for seed in seeds:
        if not any(
            abs(seed[0] - existing[0]) <= 1e-8
            and abs(seed[1] - existing[1]) <= 1e-8
            for existing in unique
        ):
            unique.append(seed)
    return unique, {
        "status": "resultant_roots_enumerated",
        "resultant_coefficients": resultant.coef.tolist(),
        "real_unit_square_seed_count": len(unique),
    }


def algebraic_quadratic_bezier_intersections(
    curve_a: Iterable[ArrayLike],
    curve_b: Iterable[ArrayLike],
    residual_tolerance: float,
) -> dict[str, object]:
    """Enumerate resultant roots and verify them with bounded refinement."""
    seeds, diagnostics = algebraic_intersection_seeds(
        curve_a, curve_b, residual_tolerance
    )
    roots, rejected = refine_intersection_seeds(
        curve_a, curve_b, seeds, residual_tolerance
    )
    first = _curve(curve_a)
    second = _curve(curve_b)
    for root in roots:
        derivative_a = quadratic_bezier_derivative(*first, root["t_a"])
        derivative_b = quadratic_bezier_derivative(*second, root["t_b"])
        denominator = float(np.linalg.norm(derivative_a) * np.linalg.norm(derivative_b))
        root["tangent_sine"] = (
            abs(cross_2d(derivative_a, derivative_b)) / denominator
            if denominator > 0.0
            else 0.0
        )
    return {"roots": roots, "diagnostics": diagnostics, "rejected_attempts": rejected}


def find_quadratic_bezier_intersections(
    curve_a: Iterable[ArrayLike],
    curve_b: Iterable[ArrayLike],
    residual_tolerance: float,
    *,
    additional_seeds: Iterable[tuple[float, float]] = (),
) -> dict[str, object]:
    """Discover and refine all isolated pair roots visible to recursive isolation."""
    first = _curve(curve_a)
    second = _curve(curve_b)
    recursive_seeds = recursive_intersection_seeds(first, second)
    endpoint_seeds = []
    for t_a in (0.0, 1.0):
        point = quadratic_bezier_point(*first, t_a)
        endpoint_seeds.extend(
            (t_a, t_b)
            for t_b in parameters_for_point_on_curve(second, point, residual_tolerance)
        )
    for t_b in (0.0, 1.0):
        point = quadratic_bezier_point(*second, t_b)
        endpoint_seeds.extend(
            (t_a, t_b)
            for t_a in parameters_for_point_on_curve(first, point, residual_tolerance)
        )
    roots, rejected = refine_intersection_seeds(
        first,
        second,
        [*endpoint_seeds, *recursive_seeds, *additional_seeds],
        residual_tolerance,
    )
    for root in roots:
        derivative_a = quadratic_bezier_derivative(*first, root["t_a"])
        derivative_b = quadratic_bezier_derivative(*second, root["t_b"])
        denominator = float(np.linalg.norm(derivative_a) * np.linalg.norm(derivative_b))
        root["tangent_sine"] = (
            abs(cross_2d(derivative_a, derivative_b)) / denominator
            if denominator > 0.0
            else 0.0
        )
    return {
        "roots": roots,
        "recursive_seed_count": len(recursive_seeds),
        "rejected_attempts": rejected,
    }


def coincident_overlap_evidence(
    curve_a: Iterable[ArrayLike],
    curve_b: Iterable[ArrayLike],
) -> dict[str, object] | None:
    """Detect exact full-curve or monotone collinear interval coincidence."""
    first = _curve(curve_a)
    second = _curve(curve_b)
    if all(np.array_equal(a, b) for a, b in zip(first, second, strict=True)):
        return {
            "kind": "identical_control_points",
            "representative_point": quadratic_bezier_point(*first, 0.5),
            "t_a": 0.5,
            "t_b": 0.5,
        }
    if all(np.array_equal(a, b) for a, b in zip(first, reversed(second), strict=True)):
        return {
            "kind": "reversed_identical_control_points",
            "representative_point": quadratic_bezier_point(*first, 0.5),
            "t_a": 0.5,
            "t_b": 0.5,
        }

    directions = [first[2] - first[0], second[2] - second[0]]
    if np.linalg.norm(directions[0]) == 0.0 or np.linalg.norm(directions[1]) == 0.0:
        return None
    direction = directions[0] / np.linalg.norm(directions[0])
    origin = first[0]

    def exact_collinear(curve: Curve) -> bool:
        return all(
            cross_2d(directions[0], point - origin) == 0.0 for point in curve
        )

    if not exact_collinear(first) or not exact_collinear(second):
        return None
    projections = [[float(np.dot(point - origin, direction)) for point in curve] for curve in (first, second)]
    # Restrict this special case to monotone straight traces with controls inside endpoints.
    intervals = []
    for values in projections:
        endpoint_min, endpoint_max = sorted((values[0], values[2]))
        if not endpoint_min <= values[1] <= endpoint_max:
            return None
        intervals.append((endpoint_min, endpoint_max))
    overlap_start = max(intervals[0][0], intervals[1][0])
    overlap_end = min(intervals[0][1], intervals[1][1])
    if overlap_end <= overlap_start:
        return None
    midpoint_projection = (overlap_start + overlap_end) / 2.0
    representative = origin + midpoint_projection * direction

    def parameter_at_projection(curve: Curve) -> float:
        coefficients = [
            float(np.dot(curve[0] - 2.0 * curve[1] + curve[2], direction)),
            float(np.dot(2.0 * (curve[1] - curve[0]), direction)),
            float(np.dot(curve[0] - representative, direction)),
        ]
        roots = np.roots(np.trim_zeros(coefficients, trim="f"))
        valid = [float(root.real) for root in roots if abs(root.imag) <= 1e-12 and -1e-12 <= root.real <= 1.0 + 1e-12]
        if not valid:
            raise RuntimeError("could not parameterize detected collinear overlap")
        return min(max(valid[0], 0.0), 1.0)

    return {
        "kind": "monotone_collinear_interval",
        "representative_point": representative,
        "t_a": parameter_at_projection(first),
        "t_b": parameter_at_projection(second),
        "overlap_projection_interval": [overlap_start, overlap_end],
    }
