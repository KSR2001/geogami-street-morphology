"""Deterministic Phase 11 street-graph construction utilities.

The canonical scientific topology is undirected. Coordinates are unmodified
Unity world X/Y values with no CRS and no verified metre conversion.
"""

from __future__ import annotations

import json
import math
from copy import deepcopy
from pathlib import Path
from typing import Any, Iterable

import networkx as nx


REGISTERED_ZERO_CHORD_ANOMALIES = frozenset(
    {
        "env38_shape_4330855547529842337_segment_0006",
        "env38_shape_4330855547529842337_segment_0019",
        "env38_shape_4330855547829185599_segment_0007",
        "env38_shape_4330855547829185599_segment_0011",
        "env38_shape_4330855547829185599_segment_0012",
    }
)

JSON_ATTRIBUTE_PREFIX = "__canonical_json__:"


def polyline_length(geometry: Iterable[Iterable[float]]) -> float:
    """Return planar polyline length in source Unity world units."""

    points = [tuple(point) for point in geometry]
    return math.fsum(
        math.hypot(b[0] - a[0], b[1] - a[1])
        for a, b in zip(points, points[1:])
    )


def topology_to_provenance_multigraph(payload: dict[str, Any]) -> nx.MultiGraph:
    """Create one undirected edge per Phase 10 detailed fragment."""

    environment_id = int(payload["environment_id"])
    graph = nx.MultiGraph(
        environment_id=environment_id,
        graph_variant="provenance_detailed",
        coordinate_system="Unity world XY",
        coordinate_units="Unity world units",
        meters_per_unit=None,
        crs=None,
        canonical_snapping_tolerance=0.0,
        simplified=False,
        directed_street_semantics=False,
    )

    for location in sorted(payload["locations"], key=lambda row: row["topology_location_id"]):
        topology_id = location["topology_location_id"]
        graph.add_node(
            topology_id,
            topology_id=topology_id,
            environment_id=environment_id,
            x=location["x"],
            y=location["y"],
            source_type=location["source_type"],
            validated_interior_crossing=bool(location["phase8_event_ids"]),
            authored_endpoint=bool(location["authored_endpoint_sources"]),
            snapping_involved=False,
            canonical_snapping_displacement=0.0,
            phase8_event_ids=deepcopy(location["phase8_event_ids"]),
            phase9_review_location_ids=deepcopy(location["phase9_review_location_ids"]),
            phase9_validation_provenance=deepcopy(location["phase9_validation"]),
            source_shape_ids=deepcopy(location["source_shape_ids"]),
            source_segment_ids=deepcopy(location["source_segment_ids"]),
            zero_chord_anomaly_related=bool(
                location["zero_chord_source_artifact_involved"]
            ),
            original_phase10_provenance=deepcopy(location),
        )

    for fragment in sorted(payload["fragments"], key=lambda row: row["fragment_id"]):
        start = fragment["start_topology_location_id"]
        end = fragment["end_topology_location_id"]
        fragment_id = fragment["fragment_id"]
        if start not in graph or end not in graph:
            raise ValueError(f"Fragment {fragment_id} references an unknown topology node")
        graph.add_edge(
            start,
            end,
            key=fragment_id,
            fragment_id=fragment_id,
            environment_id=environment_id,
            start_topology_id=start,
            end_topology_id=end,
            source_shape_id=fragment["source_shape_id"],
            source_segment_id=fragment["source_segment_id"],
            source_bezier_provenance=deepcopy(
                fragment["source_original_world_control_points"]
            ),
            split_subcurve_control_points=deepcopy(
                fragment["split_subcurve_control_points"]
            ),
            source_t_interval=deepcopy(fragment["original_t_interval"]),
            geometry=deepcopy(fragment["adaptive_detailed_xy_geometry"]),
            length=float(fragment["length_unity_world_units"]),
            validated_crossing_involvement=bool(
                fragment["validated_crossing_involvement"]
            ),
            snapping_involvement=bool(fragment["snapping_involvement"]),
            zero_chord_anomaly=bool(fragment["zero_chord_source_artifact"]),
            original_phase10_provenance=deepcopy(fragment),
        )

    if graph.number_of_edges() != len(payload["fragments"]):
        raise AssertionError("A Phase 10 fragment was lost during graph construction")
    return graph


def exclude_registered_anomaly_edges(
    provenance_graph: nx.MultiGraph,
    registered_ids: Iterable[str] = REGISTERED_ZERO_CHORD_ANOMALIES,
) -> tuple[nx.MultiGraph, list[dict[str, Any]]]:
    """Exclude only unambiguously mapped, pre-registered anomaly fragments."""

    registered = set(registered_ids)
    mapped: dict[str, list[tuple[str, str, str, dict[str, Any]]]] = {
        segment_id: [] for segment_id in registered
    }
    for u, v, key, data in provenance_graph.edges(keys=True, data=True):
        segment_id = data["source_segment_id"]
        if segment_id in registered:
            mapped[segment_id].append((u, v, key, data))

    problems = {
        segment_id: len(edges)
        for segment_id, edges in mapped.items()
        if len(edges) != 1
    }
    if problems:
        raise ValueError(f"Registered anomaly mapping is not one-to-one: {problems}")

    analytical = deepcopy(provenance_graph)
    analytical.graph["graph_variant"] = "analytical_detailed"
    exclusions: list[dict[str, Any]] = []
    for segment_id in sorted(registered):
        u, v, key, data = mapped[segment_id][0]
        if not data["zero_chord_anomaly"]:
            raise ValueError(f"Registered anomaly lacks its Phase 10 flag: {segment_id}")
        analytical.remove_edge(u, v, key)
        exclusions.append(
            {
                "source_anomaly_id": segment_id,
                "phase10_fragment_id": data["fragment_id"],
                "graph_endpoints": [u, v],
                "geometry_length_unity_world_units": data["length"],
                "reason_for_analytical_exclusion": (
                    "pre-registered Phase 10 zero-chord source anomaly; no length threshold used"
                ),
                "retained_in_provenance_detailed_graph": True,
            }
        )

    unrelated_flagged = [
        data["source_segment_id"]
        for _, _, _, data in analytical.edges(keys=True, data=True)
        if data["zero_chord_anomaly"]
    ]
    if unrelated_flagged:
        raise ValueError(f"Unexpected anomaly fragments remain: {unrelated_flagged}")
    return analytical, exclusions


def _edge_identity(u: str, v: str, key: str) -> tuple[str, str, str]:
    return (u, v, key) if u <= v else (v, u, key)


def _oriented_edge_geometry(
    data: dict[str, Any], current_node: str, next_node: str
) -> list[list[float]]:
    geometry = deepcopy(data["geometry"])
    if (
        current_node == data["start_topology_id"]
        and next_node == data["end_topology_id"]
    ):
        return geometry
    if (
        current_node == data["end_topology_id"]
        and next_node == data["start_topology_id"]
    ):
        return list(reversed(geometry))
    if current_node == next_node == data["start_topology_id"] == data["end_topology_id"]:
        return geometry
    raise ValueError(f"Edge provenance does not match traversal {current_node} -> {next_node}")


def retention_nodes(graph: nx.MultiGraph) -> set[str]:
    """Find nodes that must remain in the simplified analytical graph."""

    retained: set[str] = set()
    for node, data in graph.nodes(data=True):
        neighbors = set(graph.neighbors(node))
        if (
            graph.degree(node) != 2
            or data.get("validated_interior_crossing", False)
            or len(neighbors) != 2
            or graph.number_of_edges(node, node) > 0
        ):
            retained.add(node)

    # An isolated all-degree-2 cycle has no natural retention node. Keep the
    # lexically first node so the cycle becomes a faithful self-loop geometry.
    for component in nx.connected_components(graph):
        if not retained.intersection(component):
            retained.add(min(component))
    return retained


def simplify_analytical_graph(
    detailed_graph: nx.MultiGraph,
) -> tuple[nx.MultiGraph, dict[str, Any]]:
    """Merge maximal degree-2 chains without smoothing or resampling."""

    retained = retention_nodes(detailed_graph)
    simplified = nx.MultiGraph(**deepcopy(detailed_graph.graph))
    simplified.graph["graph_variant"] = "analytical_simplified"
    simplified.graph["simplified"] = True
    for node in sorted(retained):
        simplified.add_node(node, **deepcopy(detailed_graph.nodes[node]))

    visited: set[tuple[str, str, str]] = set()
    chains: list[dict[str, Any]] = []
    for start in sorted(retained):
        incident = sorted(
            detailed_graph.edges(start, keys=True, data=True),
            key=lambda row: _edge_identity(row[0], row[1], row[2]),
        )
        for edge_u, edge_v, edge_key, edge_data in incident:
            identity = _edge_identity(edge_u, edge_v, edge_key)
            if identity in visited:
                continue
            current = start
            next_node = edge_v if edge_u == current else edge_u
            chain_edges: list[tuple[str, str, str, dict[str, Any]]] = []
            while True:
                visited.add(identity)
                chain_edges.append((current, next_node, edge_key, edge_data))
                current = next_node
                if current in retained:
                    break
                candidates = []
                for cand_u, cand_v, cand_key, cand_data in detailed_graph.edges(
                    current, keys=True, data=True
                ):
                    cand_identity = _edge_identity(cand_u, cand_v, cand_key)
                    if cand_identity not in visited:
                        candidates.append(
                            (cand_identity, cand_u, cand_v, cand_key, cand_data)
                        )
                if len(candidates) != 1:
                    raise ValueError(
                        f"Suppressible node {current} has {len(candidates)} continuation edges"
                    )
                identity, cand_u, cand_v, edge_key, edge_data = sorted(candidates)[0]
                next_node = cand_v if cand_u == current else cand_u

            geometry: list[list[float]] = []
            fragment_ids: list[str] = []
            shape_ids: list[str] = []
            segment_ids: list[str] = []
            t_intervals: list[list[float]] = []
            input_lengths: list[float] = []
            for from_node, to_node, _, data in chain_edges:
                part = _oriented_edge_geometry(data, from_node, to_node)
                if geometry:
                    if geometry[-1] != part[0]:
                        raise ValueError(
                            f"Detailed geometry join is not exact at node {from_node}"
                        )
                    geometry.extend(part[1:])
                else:
                    geometry.extend(part)
                fragment_ids.append(data["fragment_id"])
                shape_ids.append(data["source_shape_id"])
                segment_ids.append(data["source_segment_id"])
                interval = list(data["source_t_interval"])
                if from_node == data["end_topology_id"]:
                    interval.reverse()
                t_intervals.append(interval)
                input_lengths.append(float(data["length"]))

            chains.append(
                {
                    "start": start,
                    "end": current,
                    "geometry": geometry,
                    "ordered_source_fragment_ids": fragment_ids,
                    "ordered_source_shape_ids": shape_ids,
                    "ordered_source_segment_ids": segment_ids,
                    "ordered_source_bezier_t_intervals": t_intervals,
                    "input_length": math.fsum(input_lengths),
                    "concatenated_length": polyline_length(geometry),
                    "validated_crossing_involvement": any(
                        data["validated_crossing_involvement"]
                        for _, _, _, data in chain_edges
                    ),
                }
            )

    if len(visited) != detailed_graph.number_of_edges():
        raise AssertionError("Not every analytical detailed edge was simplified")

    environment_id = int(detailed_graph.graph["environment_id"])
    for index, chain in enumerate(chains, start=1):
        edge_id = f"env{environment_id}_simplified_edge_{index:05d}"
        difference = chain["concatenated_length"] - chain["input_length"]
        simplified.add_edge(
            chain["start"],
            chain["end"],
            key=edge_id,
            simplified_edge_id=edge_id,
            environment_id=environment_id,
            start_topology_id=chain["start"],
            end_topology_id=chain["end"],
            ordered_source_fragment_ids=chain["ordered_source_fragment_ids"],
            ordered_source_shape_ids=chain["ordered_source_shape_ids"],
            ordered_source_segment_ids=chain["ordered_source_segment_ids"],
            ordered_source_bezier_t_intervals=chain[
                "ordered_source_bezier_t_intervals"
            ],
            geometry=chain["geometry"],
            length=chain["concatenated_length"],
            input_fragment_length_sum=chain["input_length"],
            length_preservation_difference=difference,
            source_fragment_count=len(chain["ordered_source_fragment_ids"]),
            validated_crossing_involvement=chain[
                "validated_crossing_involvement"
            ],
            snapping_involvement=False,
            zero_chord_anomaly_involvement=False,
        )

    detailed_components = nx.number_connected_components(detailed_graph)
    simplified_components = nx.number_connected_components(simplified)
    if detailed_components != simplified_components:
        raise AssertionError("Simplification changed connected-component count")
    length_error = math.fsum(
        data["length"] for _, _, _, data in simplified.edges(keys=True, data=True)
    ) - math.fsum(
        data["length"] for _, _, _, data in detailed_graph.edges(keys=True, data=True)
    )
    qa = {
        "retained_node_ids": sorted(retained),
        "suppressed_node_ids": sorted(set(detailed_graph) - retained),
        "suppressed_node_count": detailed_graph.number_of_nodes() - len(retained),
        "detailed_component_count": detailed_components,
        "simplified_component_count": simplified_components,
        "total_length_preservation_error_unity_world_units": length_error,
        "maximum_absolute_edge_length_error_unity_world_units": max(
            (
                abs(data["length_preservation_difference"])
                for _, _, _, data in simplified.edges(keys=True, data=True)
            ),
            default=0.0,
        ),
    }
    return simplified, qa


def to_bidirectional_multidigraph(graph: nx.MultiGraph) -> nx.MultiDiGraph:
    """Create two deterministic directed representations of each street edge."""

    directed = nx.MultiDiGraph(**deepcopy(graph.graph))
    directed.graph["graph_variant"] = "osmnx_style_bidirectional"
    directed.graph["bidirectional_adapter"] = True
    for node, data in sorted(graph.nodes(data=True)):
        directed.add_node(node, **deepcopy(data))

    edges = sorted(
        graph.edges(keys=True, data=True),
        key=lambda row: row[3]["simplified_edge_id"],
    )
    for u, v, _, data in edges:
        edge_id = data["simplified_edge_id"]
        forward = deepcopy(data)
        reverse = deepcopy(data)
        forward.update(
            directed_edge_id=f"{edge_id}:forward",
            direction="forward",
            start_topology_id=u,
            end_topology_id=v,
        )
        reverse.update(
            directed_edge_id=f"{edge_id}:reverse",
            direction="reverse",
            start_topology_id=v,
            end_topology_id=u,
            geometry=list(reversed(deepcopy(data["geometry"]))),
            ordered_source_fragment_ids=list(
                reversed(data["ordered_source_fragment_ids"])
            ),
            ordered_source_shape_ids=list(reversed(data["ordered_source_shape_ids"])),
            ordered_source_segment_ids=list(
                reversed(data["ordered_source_segment_ids"])
            ),
            ordered_source_bezier_t_intervals=[
                list(reversed(interval))
                for interval in reversed(data["ordered_source_bezier_t_intervals"])
            ],
        )
        directed.add_edge(u, v, key=forward["directed_edge_id"], **forward)
        directed.add_edge(v, u, key=reverse["directed_edge_id"], **reverse)
    return directed


def graph_to_gdfs(graph: nx.MultiDiGraph):
    """Return CRS-less OSMnx-style node and edge GeoDataFrames."""

    import geopandas as gpd
    from shapely.geometry import LineString, Point

    node_rows = []
    for node, data in sorted(graph.nodes(data=True)):
        row = deepcopy(data)
        row.update(osmid=node, geometry=Point(data["x"], data["y"]))
        node_rows.append(row)
    nodes = gpd.GeoDataFrame(node_rows, geometry="geometry", crs=None).set_index("osmid")
    nodes.index.name = "osmid"

    edge_rows = []
    for u, v, key, data in sorted(
        graph.edges(keys=True, data=True), key=lambda row: (row[0], row[1], row[2])
    ):
        row = deepcopy(data)
        row.update(u=u, v=v, key=key, geometry=LineString(data["geometry"]))
        edge_rows.append(row)
    edges = gpd.GeoDataFrame(edge_rows, geometry="geometry", crs=None)
    edges = edges.set_index(["u", "v", "key"])
    return nodes, edges


def parallel_edge_pair_count(graph: nx.MultiGraph) -> int:
    """Count unordered endpoint pairs represented by more than one edge."""

    pairs = set()
    for u, v in graph.edges():
        pair = tuple(sorted((u, v)))
        if graph.number_of_edges(u, v) > 1:
            pairs.add(pair)
    return len(pairs)


def graph_summary(graph: nx.Graph) -> dict[str, Any]:
    """Return construction QA counts, not scientific morphology metrics."""

    if graph.is_directed():
        components = nx.number_weakly_connected_components(graph)
    else:
        components = nx.number_connected_components(graph)
    return {
        "graph_type": type(graph).__name__,
        "nodes": graph.number_of_nodes(),
        "edges": graph.number_of_edges(),
        "self_loops": nx.number_of_selfloops(graph),
        "parallel_edge_pairs": parallel_edge_pair_count(graph),
        "components": components,
        "validated_crossing_nodes_represented": sum(
            bool(data.get("validated_interior_crossing"))
            for _, data in graph.nodes(data=True)
        ),
        "zero_chord_artifact_edges_represented": sum(
            bool(
                data.get("zero_chord_anomaly")
                or data.get("zero_chord_anomaly_involvement")
            )
            for _, _, data in graph.edges(data=True)
        ),
        "simplified": bool(graph.graph.get("simplified", False)),
        "crs_assigned": graph.graph.get("crs") is not None,
    }


def _graphml_value(value: Any) -> Any:
    if value is None or isinstance(value, (list, dict, tuple)):
        return JSON_ATTRIBUTE_PREFIX + json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )
    if isinstance(value, (str, int, float, bool)):
        return value
    return JSON_ATTRIBUTE_PREFIX + json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str
    )


def _restore_graphml_value(value: Any) -> Any:
    if isinstance(value, str) and value.startswith(JSON_ATTRIBUTE_PREFIX):
        return json.loads(value[len(JSON_ATTRIBUTE_PREFIX) :])
    return value


def graphml_safe_copy(graph: nx.Graph) -> nx.Graph:
    """Copy a graph with deterministic scalar GraphML attributes."""

    safe = graph.__class__()
    safe.graph.update({key: _graphml_value(value) for key, value in graph.graph.items()})
    for node, data in graph.nodes(data=True):
        safe.add_node(node, **{key: _graphml_value(value) for key, value in data.items()})
    if graph.is_multigraph():
        for u, v, key, data in graph.edges(keys=True, data=True):
            attrs = {name: _graphml_value(value) for name, value in data.items()}
            attrs["graphml_edge_id"] = str(key)
            safe.add_edge(u, v, key=key, **attrs)
    else:  # pragma: no cover - Phase 11 graphs are all multigraphs
        for u, v, data in graph.edges(data=True):
            safe.add_edge(u, v, **{key: _graphml_value(value) for key, value in data.items()})
    return safe


def write_graphml(graph: nx.Graph, path: str | Path) -> None:
    """Serialize provenance-rich graph attributes without discarding them."""

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    nx.write_graphml(
        graphml_safe_copy(graph),
        path,
        encoding="utf-8",
        prettyprint=True,
        edge_id_from_attribute="graphml_edge_id",
    )


def read_graphml(path: str | Path) -> nx.Graph:
    """Load a Phase 11 GraphML file and restore JSON-valued attributes."""

    graph = nx.read_graphml(path, force_multigraph=True)
    graph.graph.update(
        {key: _restore_graphml_value(value) for key, value in graph.graph.items()}
    )
    for _, data in graph.nodes(data=True):
        data.update({key: _restore_graphml_value(value) for key, value in data.items()})
    for _, _, _, data in graph.edges(keys=True, data=True):
        data.update({key: _restore_graphml_value(value) for key, value in data.items()})
    return graph


def validate_graphml_roundtrip(original: nx.Graph, loaded: nx.Graph) -> dict[str, Any]:
    """Validate structural and provenance fidelity after GraphML reload."""

    checks = {
        "node_count_matches": original.number_of_nodes() == loaded.number_of_nodes(),
        "edge_count_matches": original.number_of_edges() == loaded.number_of_edges(),
        "directed_matches": original.is_directed() == loaded.is_directed(),
        "multigraph_matches": original.is_multigraph() == loaded.is_multigraph(),
        "node_ids_match": set(original.nodes) == set(loaded.nodes),
        "edge_keys_match": {
            (u, v, str(key)) for u, v, key in original.edges(keys=True)
        }
        == {(u, v, str(key)) for u, v, key in loaded.edges(keys=True)},
    }
    checks["coordinates_match"] = all(
        original.nodes[node]["x"] == loaded.nodes[node]["x"]
        and original.nodes[node]["y"] == loaded.nodes[node]["y"]
        for node in original.nodes
    )
    checks["provenance_ids_match"] = all(
        original.nodes[node]["topology_id"] == loaded.nodes[node]["topology_id"]
        for node in original.nodes
    )
    original_edges = {
        (u, v, str(key)): data for u, v, key, data in original.edges(keys=True, data=True)
    }
    loaded_edges = {
        (u, v, str(key)): data for u, v, key, data in loaded.edges(keys=True, data=True)
    }
    checks["geometry_matches"] = all(
        original_edges[edge]["geometry"] == loaded_edges.get(edge, {}).get("geometry")
        for edge in original_edges
    )
    checks["connectivity_matches"] = graph_summary(original)["components"] == graph_summary(
        loaded
    )["components"]
    checks["zero_chord_policy_matches"] = graph_summary(original)[
        "zero_chord_artifact_edges_represented"
    ] == graph_summary(loaded)["zero_chord_artifact_edges_represented"]
    checks["passed"] = all(checks.values())
    if not checks["passed"]:
        raise AssertionError(f"GraphML round-trip validation failed: {checks}")
    return checks
