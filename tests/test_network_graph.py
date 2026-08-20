from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import networkx as nx
import pytest

from scripts.network_graph import (
    REGISTERED_ZERO_CHORD_ANOMALIES,
    exclude_registered_anomaly_edges,
    read_graphml,
    retention_nodes,
    simplify_analytical_graph,
    to_bidirectional_multidigraph,
    topology_to_provenance_multigraph,
    validate_graphml_roundtrip,
    write_graphml,
)


def location(node_id: str, x: float, *, validated: bool = False) -> dict:
    return {
        "topology_location_id": node_id,
        "environment_id": 1,
        "x": x,
        "y": 0.0,
        "source_type": (
            "validated_interior_crossing" if validated else "authored_exact_endpoint"
        ),
        "authored_endpoint_sources": [] if validated else [{"endpoint_id": f"{node_id}:p0"}],
        "phase8_event_ids": [f"event-{node_id}"] if validated else [],
        "phase9_review_location_ids": [f"review-{node_id}"] if validated else [],
        "phase9_validation": (
            [{"decision": "connected_same_level"}] if validated else []
        ),
        "source_shape_ids": ["shape"],
        "source_segment_ids": ["segment"],
        "zero_chord_source_artifact_involved": False,
    }


def fragment(
    fragment_id: str,
    start: str,
    end: str,
    x0: float,
    x1: float,
    *,
    segment_id: str | None = None,
    anomaly: bool = False,
    geometry: list[list[float]] | None = None,
) -> dict:
    points = geometry or [[x0, 0.0], [x1, 0.0]]
    return {
        "fragment_id": fragment_id,
        "environment_id": 1,
        "start_topology_location_id": start,
        "end_topology_location_id": end,
        "source_shape_id": "shape",
        "source_segment_id": segment_id or f"segment-{fragment_id}",
        "source_original_world_control_points": {
            "p0": points[0],
            "p1": points[0],
            "p2": points[-1],
        },
        "split_subcurve_control_points": {
            "p0": points[0],
            "p1": points[0],
            "p2": points[-1],
        },
        "original_t_interval": [0.0, 1.0],
        "adaptive_detailed_xy_geometry": points,
        "length_unity_world_units": sum(
            ((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2) ** 0.5
            for a, b in zip(points, points[1:])
        ),
        "validated_crossing_involvement": False,
        "snapping_involvement": False,
        "zero_chord_source_artifact": anomaly,
    }


def payload(locations: list[dict], fragments: list[dict]) -> dict:
    return {"environment_id": 1, "locations": locations, "fragments": fragments}


def chain_payload(*, middle_validated: bool = False) -> dict:
    return payload(
        [location("a", 0), location("b", 1, validated=middle_validated), location("c", 2)],
        [fragment("f1", "a", "b", 0, 1), fragment("f2", "b", "c", 1, 2)],
    )


def test_topology_json_to_multigraph():
    graph = topology_to_provenance_multigraph(chain_payload())
    assert isinstance(graph, nx.MultiGraph)
    assert (graph.number_of_nodes(), graph.number_of_edges()) == (3, 2)


def test_parallel_edges_are_preserved():
    source = payload(
        [location("a", 0), location("b", 1)],
        [fragment("f1", "a", "b", 0, 1), fragment("f2", "a", "b", 0, 1)],
    )
    graph = topology_to_provenance_multigraph(source)
    simplified, _ = simplify_analytical_graph(graph)
    assert graph.number_of_edges("a", "b") == simplified.number_of_edges("a", "b") == 2


def test_self_loop_provenance_is_preserved():
    source = payload(
        [location("a", 0)],
        [fragment("loop", "a", "a", 0, 0, geometry=[[0, 0], [0.1, 0], [0, 0]])],
    )
    graph = topology_to_provenance_multigraph(source)
    assert nx.number_of_selfloops(graph) == 1
    assert graph.edges["a", "a", "loop"]["original_phase10_provenance"]["fragment_id"] == "loop"


def test_registered_five_anomaly_edges_are_explicitly_excluded():
    locations = [location(f"n{i}", i) for i in range(5)]
    fragments = [
        fragment(f"f{i}", f"n{i}", f"n{i}", i, i, segment_id=segment, anomaly=True,
                 geometry=[[i, 0], [i, 0.1], [i, 0]])
        for i, segment in enumerate(sorted(REGISTERED_ZERO_CHORD_ANOMALIES))
    ]
    graph = topology_to_provenance_multigraph(payload(locations, fragments))
    analytical, exclusions = exclude_registered_anomaly_edges(graph)
    assert graph.number_of_edges() == 5
    assert analytical.number_of_edges() == 0
    assert len(exclusions) == 5


def test_unrelated_short_edge_is_not_excluded():
    registered = sorted(REGISTERED_ZERO_CHORD_ANOMALIES)
    locations = [location(f"n{i}", i) for i in range(7)]
    fragments = [
        fragment(f"f{i}", f"n{i}", f"n{i}", i, i, segment_id=segment, anomaly=True,
                 geometry=[[i, 0], [i, 0.1], [i, 0]])
        for i, segment in enumerate(registered)
    ]
    fragments.append(fragment("tiny", "n5", "n6", 5, 5.000000001))
    graph = topology_to_provenance_multigraph(payload(locations, fragments))
    analytical, _ = exclude_registered_anomaly_edges(graph)
    assert analytical.has_edge("n5", "n6", "tiny")


def test_degree_two_chain_simplification():
    simplified, qa = simplify_analytical_graph(topology_to_provenance_multigraph(chain_payload()))
    assert (simplified.number_of_nodes(), simplified.number_of_edges()) == (2, 1)
    assert qa["suppressed_node_ids"] == ["b"]


def test_geometry_concatenation_order():
    simplified, _ = simplify_analytical_graph(topology_to_provenance_multigraph(chain_payload()))
    data = next(iter(simplified.edges(data=True)))[2]
    assert data["geometry"] == [[0, 0.0], [1, 0.0], [2, 0.0]]
    assert data["ordered_source_fragment_ids"] == ["f1", "f2"]


def test_bidirectional_adapter_reverses_geometry():
    simplified, _ = simplify_analytical_graph(topology_to_provenance_multigraph(chain_payload()))
    directed = to_bidirectional_multidigraph(simplified)
    forward = next(data for _, _, data in directed.edges(data=True) if data["direction"] == "forward")
    reverse = next(data for _, _, data in directed.edges(data=True) if data["direction"] == "reverse")
    assert reverse["geometry"] == list(reversed(forward["geometry"]))


def test_validated_crossing_node_is_retained():
    graph = topology_to_provenance_multigraph(chain_payload(middle_validated=True))
    assert "b" in retention_nodes(graph)


def test_branch_node_is_retained():
    source = payload(
        [location("a", 0), location("b", 1), location("c", 2), location("d", 1)],
        [fragment("f1", "a", "b", 0, 1), fragment("f2", "b", "c", 1, 2),
         fragment("f3", "b", "d", 1, 1, geometry=[[1, 0], [1, 1]])],
    )
    graph = topology_to_provenance_multigraph(source)
    assert "b" in retention_nodes(graph)


def test_dead_end_is_retained():
    graph = topology_to_provenance_multigraph(chain_payload())
    assert {"a", "c"}.issubset(retention_nodes(graph))


def test_source_geometry_boundary_may_be_suppressed():
    simplified, qa = simplify_analytical_graph(topology_to_provenance_multigraph(chain_payload()))
    assert "b" not in simplified
    assert "b" in qa["suppressed_node_ids"]


def test_cycle_safe_simplification():
    source = payload(
        [location("a", 0), location("b", 1), location("c", 2)],
        [
            fragment("f1", "a", "b", 0, 1),
            fragment("f2", "b", "c", 1, 2),
            fragment("f3", "c", "a", 2, 0, geometry=[[2, 0], [1, 1], [0, 0]]),
        ],
    )
    simplified, _ = simplify_analytical_graph(topology_to_provenance_multigraph(source))
    assert (simplified.number_of_nodes(), simplified.number_of_edges()) == (1, 1)
    assert nx.number_of_selfloops(simplified) == 1


def test_length_preservation():
    simplified, qa = simplify_analytical_graph(topology_to_provenance_multigraph(chain_payload()))
    assert qa["total_length_preservation_error_unity_world_units"] == pytest.approx(0)
    assert next(iter(simplified.edges(data=True)))[2]["length"] == pytest.approx(2)


def test_connected_component_preservation():
    graph = topology_to_provenance_multigraph(chain_payload())
    simplified, _ = simplify_analytical_graph(graph)
    assert nx.number_connected_components(graph) == nx.number_connected_components(simplified)


def test_deterministic_node_ids():
    source = chain_payload()
    assert list(topology_to_provenance_multigraph(source)) == list(
        topology_to_provenance_multigraph(deepcopy(source))
    )


def test_deterministic_edge_ids_and_keys():
    source = chain_payload()
    first, _ = simplify_analytical_graph(topology_to_provenance_multigraph(source))
    second, _ = simplify_analytical_graph(topology_to_provenance_multigraph(deepcopy(source)))
    assert list(first.edges(keys=True)) == list(second.edges(keys=True))


def test_graphml_round_trip():
    graph, _ = simplify_analytical_graph(topology_to_provenance_multigraph(chain_payload()))
    path = Path("outputs/qa/.phase11-test-graph.graphml")
    try:
        write_graphml(graph, path)
        loaded = read_graphml(path)
        assert validate_graphml_roundtrip(graph, loaded)["passed"]
    finally:
        path.unlink(missing_ok=True)


def test_provenance_serialization_deserialization():
    graph = topology_to_provenance_multigraph(chain_payload())
    path = Path("outputs/qa/.phase11-test-provenance.graphml")
    try:
        write_graphml(graph, path)
        loaded = read_graphml(path)
        original = graph.edges["a", "b", "f1"]["original_phase10_provenance"]
        restored = loaded.edges["a", "b", "f1"]["original_phase10_provenance"]
        assert restored == original
    finally:
        path.unlink(missing_ok=True)
