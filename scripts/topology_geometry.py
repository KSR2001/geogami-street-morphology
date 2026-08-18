"""Reusable exact-topology and endpoint-distance helpers for Phase 10.

The functions in this module operate in Unity world XY and never apply a
spatial snapping tolerance unless a caller explicitly requests a sensitivity
test.  No graph-library structures are created.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np
from numpy.typing import ArrayLike, NDArray

try:
    from .bezier_geometry import quadratic_bezier_point
except ImportError:  # pragma: no cover - direct script import path
    from bezier_geometry import quadratic_bezier_point


Curve = tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]]


def _curve(p0: ArrayLike, p1: ArrayLike, p2: ArrayLike) -> Curve:
    values = tuple(np.asarray(point, dtype=np.float64) for point in (p0, p1, p2))
    for point in values:
        if point.shape != (2,) or not np.all(np.isfinite(point)):
            raise ValueError("quadratic control points must be finite XY values")
    return values  # type: ignore[return-value]


def split_quadratic_at_parameter(
    p0: ArrayLike, p1: ArrayLike, p2: ArrayLike, parameter: float
) -> tuple[Curve, Curve]:
    """Split a quadratic Bezier at an arbitrary strict-interior parameter."""
    start, control, end = _curve(p0, p1, p2)
    t = float(parameter)
    if not np.isfinite(t) or not 0.0 < t < 1.0:
        raise ValueError("split parameter must be finite and strictly within (0, 1)")
    first_linear = (1.0 - t) * start + t * control
    second_linear = (1.0 - t) * control + t * end
    split_point = (1.0 - t) * first_linear + t * second_linear
    return (start, first_linear, split_point), (split_point, second_linear, end)


@dataclass(frozen=True)
class QuadraticPiece:
    original_t_start: float
    original_t_end: float
    control_points: Curve


def split_quadratic_at_parameters(
    p0: ArrayLike,
    p1: ArrayLike,
    p2: ArrayLike,
    parameters: Iterable[float],
    *,
    parameter_equivalence: float = 0.0,
) -> list[QuadraticPiece]:
    """Split at sorted original parameters while retaining original t intervals.

    Parameters are sorted internally. Only numerically equivalent parameters
    are deduplicated; this is parameter-root handling, not spatial snapping.
    """
    curve = _curve(p0, p1, p2)
    equivalence = float(parameter_equivalence)
    if not np.isfinite(equivalence) or equivalence < 0.0:
        raise ValueError("parameter_equivalence must be finite and non-negative")
    ordered = sorted(float(value) for value in parameters)
    if any(not np.isfinite(value) or not 0.0 < value < 1.0 for value in ordered):
        raise ValueError("all split parameters must be finite and strictly within (0, 1)")
    distinct: list[float] = []
    for value in ordered:
        if not distinct or abs(value - distinct[-1]) > equivalence:
            distinct.append(value)

    pieces: list[QuadraticPiece] = []
    remainder = curve
    previous = 0.0
    for value in distinct:
        local_parameter = (value - previous) / (1.0 - previous)
        left, remainder = split_quadratic_at_parameter(*remainder, local_parameter)
        pieces.append(QuadraticPiece(previous, value, left))
        previous = value
    pieces.append(QuadraticPiece(previous, 1.0, remainder))
    return pieces


def exact_endpoint_groups(
    endpoint_records: Iterable[Mapping[str, Any]],
) -> dict[tuple[float, float], list[dict[str, Any]]]:
    """Group endpoint records by exact numeric XY equality only."""
    groups: dict[tuple[float, float], list[dict[str, Any]]] = defaultdict(list)
    for record in endpoint_records:
        x, y = float(record["x"]), float(record["y"])
        if not np.isfinite(x) or not np.isfinite(y):
            raise ValueError("endpoint coordinates must be finite")
        groups[(x, y)].append(dict(record))
    return {
        coordinate: sorted(records, key=lambda item: str(item["endpoint_id"]))
        for coordinate, records in sorted(groups.items())
    }


def deterministic_location_ids(
    environment_id: int, coordinates: Iterable[tuple[float, float]]
) -> dict[tuple[float, float], str]:
    """Assign stable IDs from exact coordinates sorted lexicographically."""
    distinct = sorted(set(coordinates))
    return {
        coordinate: f"env{environment_id}_topology_location_{index:04d}"
        for index, coordinate in enumerate(distinct, start=1)
    }


def endpoint_to_endpoint_distance(first: ArrayLike, second: ArrayLike) -> float:
    first_array = np.asarray(first, dtype=np.float64)
    second_array = np.asarray(second, dtype=np.float64)
    if first_array.shape != (2,) or second_array.shape != (2,):
        raise ValueError("endpoint coordinates must have shape (2,)")
    if not np.all(np.isfinite(first_array)) or not np.all(np.isfinite(second_array)):
        raise ValueError("endpoint coordinates must be finite")
    return float(np.linalg.norm(first_array - second_array))


@dataclass(frozen=True)
class NearestBezierPoint:
    parameter: float
    point: NDArray[np.float64]
    distance: float
    strictly_interior: bool


def nearest_point_on_quadratic(
    point: ArrayLike, p0: ArrayLike, p1: ArrayLike, p2: ArrayLike
) -> NearestBezierPoint:
    """Return the global nearest point using roots of the cubic derivative.

    For ``B(t) = a*t^2 + b*t + c``, stationary squared-distance parameters
    solve ``(B(t)-P) dot B'(t) = 0``. All real roots in [0, 1] and both
    endpoints are evaluated, so the reported distance is against the original
    quadratic rather than a polyline approximation.
    """
    target = np.asarray(point, dtype=np.float64)
    if target.shape != (2,) or not np.all(np.isfinite(target)):
        raise ValueError("point must be a finite XY value")
    start, control, end = _curve(p0, p1, p2)
    a = start - 2.0 * control + end
    b = 2.0 * (control - start)
    c = start - target

    derivative_coefficients = np.zeros(4, dtype=np.float64)
    for axis in (0, 1):
        contribution = np.polynomial.polynomial.polymul(
            np.array([c[axis], b[axis], a[axis]], dtype=np.float64),
            np.array([b[axis], 2.0 * a[axis]], dtype=np.float64),
        )
        derivative_coefficients[: len(contribution)] += contribution
    coefficients = np.trim_zeros(derivative_coefficients, trim="b")
    candidates = [0.0, 1.0]
    if len(coefficients) > 1:
        for root in np.roots(coefficients[::-1]):
            if abs(float(root.imag)) <= 1e-12:
                parameter = float(root.real)
                if -1e-12 <= parameter <= 1.0 + 1e-12:
                    candidates.append(min(1.0, max(0.0, parameter)))

    evaluated = []
    for parameter in sorted(set(candidates)):
        coordinate = quadratic_bezier_point(start, control, end, parameter)
        evaluated.append(
            (float(np.linalg.norm(coordinate - target)), parameter, coordinate)
        )
    distance, parameter, coordinate = min(evaluated, key=lambda value: (value[0], value[1]))
    return NearestBezierPoint(
        parameter=parameter,
        point=coordinate,
        distance=distance,
        strictly_interior=0.0 < parameter < 1.0,
    )


class DisjointSet:
    """Small deterministic union-find used for QA components and clusters."""

    def __init__(self, values: Iterable[str] = ()) -> None:
        self.parent: dict[str, str] = {}
        for value in values:
            self.add(value)

    def add(self, value: str) -> None:
        self.parent.setdefault(value, value)

    def find(self, value: str) -> str:
        self.add(value)
        parent = self.parent[value]
        if parent != value:
            self.parent[value] = self.find(parent)
        return self.parent[value]

    def union(self, first: str, second: str) -> None:
        root_first, root_second = self.find(first), self.find(second)
        if root_first == root_second:
            return
        if root_first < root_second:
            self.parent[root_second] = root_first
        else:
            self.parent[root_first] = root_second

    def groups(self) -> dict[str, list[str]]:
        result: dict[str, list[str]] = defaultdict(list)
        for value in sorted(self.parent):
            result[self.find(value)].append(value)
        return dict(result)


def ambiguous_candidate_ids(
    candidates: Sequence[Mapping[str, Any]],
    endpoint_coordinates: Mapping[str, tuple[float, float]],
    tolerance: float,
) -> set[str]:
    """Flag competing targets, wide transitive clusters, conflicts, and anomalies."""
    eligible = [candidate for candidate in candidates if float(candidate["distance"]) <= tolerance]
    ambiguous: set[str] = set()
    by_source: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for candidate in eligible:
        source_id = str(candidate["source_endpoint_location_id"])
        by_source[source_id].append(candidate)
        if candidate["candidate_type"] == "endpoint_endpoint":
            by_source[str(candidate["target_endpoint_location_id"])].append(candidate)
        if bool(candidate.get("source_anomaly_involved", False)):
            ambiguous.add(str(candidate["candidate_id"]))
    for source_id, relationships in by_source.items():
        target_keys = {
            (str(item["candidate_type"]), str(item["target_key"]))
            for item in relationships
        }
        types = {str(item["candidate_type"]) for item in relationships}
        if len(target_keys) > 1 or len(types) > 1:
            ambiguous.update(str(item["candidate_id"]) for item in relationships)

    endpoint_edges = [item for item in eligible if item["candidate_type"] == "endpoint_endpoint"]
    clusters = DisjointSet(endpoint_coordinates)
    edge_ids_by_cluster_member: dict[str, set[str]] = defaultdict(set)
    for item in endpoint_edges:
        first = str(item["source_endpoint_location_id"])
        second = str(item["target_endpoint_location_id"])
        clusters.union(first, second)
        edge_ids_by_cluster_member[first].add(str(item["candidate_id"]))
        edge_ids_by_cluster_member[second].add(str(item["candidate_id"]))
    for members in clusters.groups().values():
        if len(members) < 3:
            continue
        diameter = max(
            endpoint_to_endpoint_distance(endpoint_coordinates[first], endpoint_coordinates[second])
            for index, first in enumerate(members)
            for second in members[index + 1 :]
        )
        if diameter > tolerance:
            for member in members:
                ambiguous.update(edge_ids_by_cluster_member[member])
    return ambiguous
