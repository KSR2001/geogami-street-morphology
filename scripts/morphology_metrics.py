"""Reusable planar street-morphology metrics for Unity world X/Y graphs."""

from __future__ import annotations

import math
from collections import Counter
from typing import Iterable, Sequence

import networkx as nx
import numpy as np


ORIENTATION_BIN_COUNT = 36
ORIENTATION_BIN_WIDTH_DEGREES = 10.0
CIRCUITY_RATIO_NUMERICAL_TOLERANCE = 1e-9


def unity_frame_bearing(x1: float, y1: float, x2: float, y2: float) -> float:
    """Return clockwise planar bearing from +Unity Y in [0, 360)."""

    dx = float(x2) - float(x1)
    dy = float(y2) - float(y1)
    if dx == 0.0 and dy == 0.0:
        raise ValueError("Unity-frame bearing is undefined for coincident points")
    return math.degrees(math.atan2(dx, dy)) % 360.0


def reciprocal_bearing(bearing: float) -> float:
    """Return the opposite direction of a bearing."""

    return (float(bearing) + 180.0) % 360.0


def orientation_histogram(
    bearings: Sequence[float] | np.ndarray,
    *,
    weights: Sequence[float] | np.ndarray | None = None,
    centre_offset_degrees: float = 0.0,
    bin_count: int = ORIENTATION_BIN_COUNT,
) -> dict[str, np.ndarray]:
    """Bin circular bearings into equal-width bins defined by their centres."""

    values = np.asarray(bearings, dtype=float)
    if values.ndim != 1 or not np.all(np.isfinite(values)):
        raise ValueError("Bearings must be a finite one-dimensional sequence")
    width = 360.0 / bin_count
    offset = float(centre_offset_degrees) % width
    indices = np.floor(((values - offset + width / 2.0) % 360.0) / width).astype(int)
    histogram_weights = None if weights is None else np.asarray(weights, dtype=float)
    if histogram_weights is not None:
        if histogram_weights.shape != values.shape:
            raise ValueError("Weights must match bearings")
        if not np.all(np.isfinite(histogram_weights)) or np.any(histogram_weights < 0):
            raise ValueError("Weights must be finite and non-negative")
    totals = np.bincount(indices, weights=histogram_weights, minlength=bin_count).astype(float)
    denominator = float(totals.sum())
    probabilities = totals / denominator if denominator > 0 else np.zeros(bin_count)
    centres = (offset + np.arange(bin_count, dtype=float) * width) % 360.0
    return {
        "centres": centres,
        "lower_edges": centres - width / 2.0,
        "upper_edges": centres + width / 2.0,
        "totals": totals,
        "probabilities": probabilities,
    }


def shannon_entropy(probabilities: Sequence[float] | np.ndarray) -> float:
    """Calculate Shannon entropy with natural logarithms, in nats."""

    probabilities_array = np.asarray(probabilities, dtype=float)
    if np.any(probabilities_array < 0) or not np.all(np.isfinite(probabilities_array)):
        raise ValueError("Probabilities must be finite and non-negative")
    positive = probabilities_array[probabilities_array > 0]
    return float(-np.sum(positive * np.log(positive)))


def orientation_entropy(
    bearings: Sequence[float] | np.ndarray,
    *,
    weights: Sequence[float] | np.ndarray | None = None,
    centre_offset_degrees: float = 0.0,
    bin_count: int = ORIENTATION_BIN_COUNT,
) -> tuple[float, dict[str, np.ndarray]]:
    histogram = orientation_histogram(
        bearings,
        weights=weights,
        centre_offset_degrees=centre_offset_degrees,
        bin_count=bin_count,
    )
    return shannon_entropy(histogram["probabilities"]), histogram


def orientation_order(entropy_nats: float, *, bin_count: int = 36) -> float:
    """Return Boeing orientation order phi, calculated from unweighted H_o."""

    grid_entropy = math.log(4.0)
    maximum_entropy = math.log(float(bin_count))
    return 1.0 - ((float(entropy_nats) - grid_entropy) / (maximum_entropy - grid_entropy)) ** 2


def polyline_length(geometry: Iterable[Iterable[float]]) -> float:
    points = [tuple(map(float, point)) for point in geometry]
    return math.fsum(
        math.hypot(b[0] - a[0], b[1] - a[1])
        for a, b in zip(points, points[1:])
    )


def euclidean_endpoint_distance(
    x1: float, y1: float, x2: float, y2: float
) -> float:
    return math.hypot(float(x2) - float(x1), float(y2) - float(y1))


def edge_circuity(network_length: float, straight_distance: float) -> float:
    if straight_distance <= 0:
        raise ValueError("Circuity requires a positive endpoint distance")
    value = float(network_length) / float(straight_distance)
    if value < 1.0 and not math.isclose(
        value, 1.0, rel_tol=0.0, abs_tol=CIRCUITY_RATIO_NUMERICAL_TOLERANCE
    ):
        raise ValueError("Polyline network length is shorter than its endpoint chord")
    return value


def aggregate_network_circuity(
    network_lengths: Sequence[float], straight_distances: Sequence[float]
) -> float:
    if len(network_lengths) != len(straight_distances) or not network_lengths:
        raise ValueError("Length arrays must be non-empty and equal in size")
    straight_total = math.fsum(map(float, straight_distances))
    if straight_total <= 0:
        raise ValueError("Aggregate circuity requires positive total straight distance")
    return math.fsum(map(float, network_lengths)) / straight_total


def polyline_piece_observations(
    geometry: Iterable[Iterable[float]],
) -> tuple[list[float], list[float]]:
    """Return reciprocal Unity-frame bearings and piece-length weights."""

    points = [tuple(map(float, point)) for point in geometry]
    bearings: list[float] = []
    weights: list[float] = []
    for first, second in zip(points, points[1:]):
        length = euclidean_endpoint_distance(*first, *second)
        if length == 0:
            continue
        bearing = unity_frame_bearing(*first, *second)
        bearings.extend((bearing, reciprocal_bearing(bearing)))
        weights.extend((length, length))
    return bearings, weights


def topology_summary(graph: nx.MultiGraph) -> dict:
    """Return all-node-denominator topology indicators."""

    if graph.is_directed():
        raise ValueError("Topology summary requires an undirected graph")
    if nx.number_of_selfloops(graph):
        raise ValueError("Analytical topology must not contain self-loops")
    for u, v in graph.edges():
        if graph.number_of_edges(u, v) != 1:
            raise ValueError("Incident-street degree is ambiguous with parallel edges")
    node_count = graph.number_of_nodes()
    if node_count == 0:
        raise ValueError("Topology summary requires nodes")
    degree_distribution = Counter(dict(graph.degree()).values())
    degree_sum = sum(degree * count for degree, count in degree_distribution.items())
    intersections = sum(count for degree, count in degree_distribution.items() if degree >= 3)
    result = {
        "node_count": node_count,
        "edge_street_segment_count": graph.number_of_edges(),
        "connected_component_count": nx.number_connected_components(graph),
        "average_incident_streets_per_node": degree_sum / node_count,
        "dead_end_count": degree_distribution.get(1, 0),
        "dead_end_proportion": degree_distribution.get(1, 0) / node_count,
        "degree_2_count": degree_distribution.get(2, 0),
        "degree_2_proportion": degree_distribution.get(2, 0) / node_count,
        "three_way_count": degree_distribution.get(3, 0),
        "three_way_proportion": degree_distribution.get(3, 0) / node_count,
        "four_way_count": degree_distribution.get(4, 0),
        "four_way_proportion": degree_distribution.get(4, 0) / node_count,
        "degree_ge_5_count": sum(
            count for degree, count in degree_distribution.items() if degree >= 5
        ),
        "degree_distribution": {
            str(degree): degree_distribution[degree]
            for degree in sorted(degree_distribution)
        },
        "intersection_node_count_degree_ge_3": intersections,
        "three_way_proportion_among_intersections": (
            degree_distribution.get(3, 0) / intersections if intersections else None
        ),
        "four_way_proportion_among_intersections": (
            degree_distribution.get(4, 0) / intersections if intersections else None
        ),
        "networkx_degree_equals_incident_street_count_verified": True,
    }
    return result
