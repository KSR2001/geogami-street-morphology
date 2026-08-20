import numpy as np
import pytest

from scripts.bezier_geometry import quadratic_bezier_point
from scripts.topology_geometry import (
    ambiguous_candidate_ids,
    deterministic_location_ids,
    endpoint_to_endpoint_distance,
    exact_endpoint_groups,
    nearest_point_on_quadratic,
    split_quadratic_at_parameter,
    split_quadratic_at_parameters,
)


def test_exact_grouping_of_identical_endpoints():
    records = [
        {"endpoint_id": "b", "x": 1.0, "y": 2.0},
        {"endpoint_id": "a", "x": 1.0, "y": 2.0},
    ]
    groups = exact_endpoint_groups(records)
    assert list(groups) == [(1.0, 2.0)]
    assert [item["endpoint_id"] for item in groups[(1.0, 2.0)]] == ["a", "b"]


def test_non_equal_endpoints_remain_separate_at_zero_tolerance():
    groups = exact_endpoint_groups(
        [
            {"endpoint_id": "a", "x": 1.0, "y": 2.0},
            {"endpoint_id": "b", "x": 1.0 + 1e-14, "y": 2.0},
        ]
    )
    assert len(groups) == 2


def test_quadratic_split_at_one_parameter():
    curve = (np.array([0.0, 0.0]), np.array([1.0, 2.0]), np.array([2.0, 0.0]))
    left, right = split_quadratic_at_parameter(*curve, 0.25)
    expected = quadratic_bezier_point(*curve, 0.25)
    assert left[2] == pytest.approx(expected)
    assert right[0] == pytest.approx(expected)


def test_quadratic_split_at_multiple_ordered_parameters():
    pieces = split_quadratic_at_parameters(
        [0.0, 0.0], [1.0, 2.0], [2.0, 0.0], [0.75, 0.25, 0.5]
    )
    assert [(piece.original_t_start, piece.original_t_end) for piece in pieces] == [
        (0.0, 0.25),
        (0.25, 0.5),
        (0.5, 0.75),
        (0.75, 1.0),
    ]


def test_reconstructed_subcurves_join_exactly():
    pieces = split_quadratic_at_parameters(
        [0.0, 0.0], [3.0, 4.0], [8.0, 1.0], [0.2, 0.6, 0.9]
    )
    for first, second in zip(pieces, pieces[1:], strict=False):
        assert np.array_equal(first.control_points[2], second.control_points[0])


def test_original_curve_endpoints_are_preserved():
    pieces = split_quadratic_at_parameters(
        [2.0, 3.0], [5.0, 9.0], [11.0, 4.0], [0.4]
    )
    assert np.array_equal(pieces[0].control_points[0], [2.0, 3.0])
    assert np.array_equal(pieces[-1].control_points[2], [11.0, 4.0])


def test_endpoint_to_endpoint_distance():
    assert endpoint_to_endpoint_distance([0.0, 0.0], [3.0, 4.0]) == 5.0


def test_endpoint_to_bezier_nearest_distance_on_straight_quadratic():
    nearest = nearest_point_on_quadratic(
        [1.0, 3.0], [0.0, 0.0], [1.0, 0.0], [2.0, 0.0]
    )
    assert nearest.parameter == pytest.approx(0.5)
    assert nearest.point == pytest.approx([1.0, 0.0])
    assert nearest.distance == pytest.approx(3.0)


def test_endpoint_to_interior_candidate_on_curved_quadratic():
    curve = ([0.0, 0.0], [1.0, 2.0], [2.0, 0.0])
    target = quadratic_bezier_point(*curve, 0.5) + np.array([0.0, 0.25])
    nearest = nearest_point_on_quadratic(target, *curve)
    assert nearest.strictly_interior
    assert nearest.parameter == pytest.approx(0.5)
    assert nearest.distance == pytest.approx(0.25)


def test_ambiguous_multi_target_snapping():
    candidates = [
        {
            "candidate_id": "c1",
            "candidate_type": "endpoint_endpoint",
            "source_endpoint_location_id": "a",
            "target_endpoint_location_id": "b",
            "target_key": "b",
            "distance": 0.1,
            "source_anomaly_involved": False,
        },
        {
            "candidate_id": "c2",
            "candidate_type": "endpoint_interior",
            "source_endpoint_location_id": "a",
            "target_key": "segment:0.5",
            "distance": 0.2,
            "source_anomaly_involved": False,
        },
    ]
    assert ambiguous_candidate_ids(
        candidates, {"a": (0.0, 0.0), "b": (0.1, 0.0)}, 0.25
    ) == {"c1", "c2"}


def test_deterministic_topology_ids_ignore_input_order():
    expected = {
        (1.0, 5.0): "env38_topology_location_0001",
        (2.0, 0.0): "env38_topology_location_0002",
    }
    assert deterministic_location_ids(38, [(2.0, 0.0), (1.0, 5.0)]) == expected
    assert deterministic_location_ids(38, [(1.0, 5.0), (2.0, 0.0)]) == expected


def test_validated_interior_crossing_becomes_deterministic_location():
    crossing = (0.5, 0.75)
    identifiers = deterministic_location_ids(39, [(0.0, 0.0), crossing, (1.0, 1.0)])
    assert crossing in identifiers


def test_zero_chord_curve_remains_traceable_without_splits():
    pieces = split_quadratic_at_parameters([1.0, 1.0], [1.001, 1.002], [1.0, 1.0], [])
    assert len(pieces) == 1
    assert np.array_equal(pieces[0].control_points[0], pieces[0].control_points[2])
    assert not np.array_equal(pieces[0].control_points[0], pieces[0].control_points[1])


def test_no_source_geometry_disappears_after_splitting():
    pieces = split_quadratic_at_parameters(
        [0.0, 0.0], [2.0, 3.0], [5.0, 1.0], [0.1, 0.4, 0.8]
    )
    assert sum(piece.original_t_end - piece.original_t_start for piece in pieces) == pytest.approx(1.0)
    assert pieces[0].original_t_start == 0.0
    assert pieces[-1].original_t_end == 1.0
