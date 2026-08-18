from __future__ import annotations

import math

import networkx as nx
import numpy as np
import pytest

from scripts.morphology_metrics import (
    aggregate_network_circuity,
    edge_circuity,
    orientation_entropy,
    orientation_histogram,
    orientation_order,
    polyline_length,
    polyline_piece_observations,
    reciprocal_bearing,
    shannon_entropy,
    topology_summary,
    unity_frame_bearing,
)


@pytest.mark.parametrize(
    ("endpoint", "expected"),
    [((0, 1), 0), ((1, 0), 90), ((0, -1), 180), ((-1, 0), 270)],
)
def test_unity_frame_cardinal_bearings(endpoint, expected):
    assert unity_frame_bearing(0, 0, *endpoint) == expected


def test_reciprocal_bearing():
    assert reciprocal_bearing(350) == 170
    assert reciprocal_bearing(180) == 0


def test_histogram_wraps_zero_and_360():
    histogram = orientation_histogram([359.9, 0.0, 0.1])
    assert histogram["totals"][0] == 3


def test_shifted_36_bin_boundaries():
    canonical = orientation_histogram([5.25], centre_offset_degrees=0)
    shifted = orientation_histogram([5.25], centre_offset_degrees=0.5)
    assert np.argmax(canonical["totals"]) == 1
    assert np.argmax(shifted["totals"]) == 0


def test_known_shannon_entropy_distribution():
    assert shannon_entropy([0.5, 0.5]) == pytest.approx(math.log(2))


def test_equal_four_direction_grid_entropy():
    entropy, _ = orientation_entropy([0, 90, 180, 270])
    assert entropy == pytest.approx(math.log(4))


def test_uniform_36_bin_entropy():
    entropy, _ = orientation_entropy(np.arange(0, 360, 10))
    assert entropy == pytest.approx(math.log(36))


def test_orientation_order_grid_entropy_is_one():
    assert orientation_order(math.log(4)) == pytest.approx(1)


def test_orientation_order_maximum_entropy_is_zero():
    assert orientation_order(math.log(36)) == pytest.approx(0)


def test_weighted_entropy():
    entropy, histogram = orientation_entropy([0, 90], weights=[3, 1])
    assert histogram["probabilities"][0] == pytest.approx(0.75)
    assert entropy == pytest.approx(-(0.75 * math.log(0.75) + 0.25 * math.log(0.25)))


def test_straight_polyline_length():
    assert polyline_length([[0, 0], [3, 4]]) == 5


def test_curved_polyline_length():
    assert polyline_length([[0, 0], [3, 4], [6, 4]]) == 8


def test_individual_circuity_is_at_least_one():
    assert edge_circuity(8, math.hypot(6, 4)) >= 1


def test_circuity_accepts_but_does_not_clip_numerical_residual():
    value = edge_circuity(1.0 - 1e-10, 1.0)
    assert value == 1.0 - 1e-10


def test_aggregate_circuity_is_ratio_of_sums():
    assert aggregate_network_circuity([2, 4], [1, 2]) == 2


def topology_fixture() -> nx.MultiGraph:
    graph = nx.MultiGraph()
    graph.add_edges_from(
        [
            ("centre", "a"),
            ("centre", "b"),
            ("centre", "c"),
            ("centre", "d"),
            ("c", "tail"),
        ]
    )
    return graph


def test_simple_topology_degree_distribution():
    summary = topology_summary(topology_fixture())
    assert summary["degree_distribution"] == {"1": 4, "2": 1, "4": 1}


def test_dead_end_proportion_uses_all_nodes():
    summary = topology_summary(topology_fixture())
    assert summary["dead_end_proportion"] == pytest.approx(4 / 6)


def test_three_way_proportion_uses_all_nodes():
    graph = nx.MultiGraph([(0, 1), (0, 2), (0, 3)])
    assert topology_summary(graph)["three_way_proportion"] == pytest.approx(1 / 4)


def test_four_way_proportion_uses_all_nodes():
    summary = topology_summary(topology_fixture())
    assert summary["four_way_proportion"] == pytest.approx(1 / 6)


def test_bidirectional_piece_bearing_symmetry():
    bearings, weights = polyline_piece_observations([[0, 0], [1, 1]])
    assert len(bearings) == len(weights) == 2
    assert bearings[1] == reciprocal_bearing(bearings[0])
    assert weights[0] == weights[1]


def test_no_short_edge_filtering_occurs():
    graph = nx.MultiGraph()
    graph.add_edge("a", "b", length=1e-15)
    summary = topology_summary(graph)
    assert summary["edge_street_segment_count"] == 1
