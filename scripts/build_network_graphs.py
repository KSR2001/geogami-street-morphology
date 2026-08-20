"""Build and validate Phase 11 provenance and analytical street graphs."""

from __future__ import annotations

import csv
import hashlib
import importlib.metadata
import json
import os
import platform
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import networkx as nx

os.environ.setdefault(
    "MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "geogami-matplotlib")
)
import matplotlib.pyplot as plt

try:
    from .network_graph import (
        REGISTERED_ZERO_CHORD_ANOMALIES,
        exclude_registered_anomaly_edges,
        graph_summary,
        graph_to_gdfs,
        read_graphml,
        simplify_analytical_graph,
        to_bidirectional_multidigraph,
        topology_to_provenance_multigraph,
        validate_graphml_roundtrip,
        write_graphml,
    )
except ImportError:  # pragma: no cover - direct script execution
    from network_graph import (
        REGISTERED_ZERO_CHORD_ANOMALIES,
        exclude_registered_anomaly_edges,
        graph_summary,
        graph_to_gdfs,
        read_graphml,
        simplify_analytical_graph,
        to_bidirectional_multidigraph,
        topology_to_provenance_multigraph,
        validate_graphml_roundtrip,
        write_graphml,
    )


ROOT = Path(__file__).resolve().parents[1]
GRAPHS = ROOT / "data/graphs"
QA = ROOT / "outputs/qa"
TABLES = ROOT / "outputs/tables"
RAW_HASHES = {
    38: "43ea446a4a88e9f3d594fb8b72742f5d4b2a1ee8a03ebf8350c4c3cce45c5819",
    39: "e5dbce6b4d88656c9e0f3bbf6a814434f64b0fbe9b3ff1864ea3fafaf0883602",
}
EXPECTED = {
    38: {"locations": 147, "fragments": 176, "crossings": 28},
    39: {"locations": 53, "fragments": 72, "crossings": 20},
}
LENGTH_QA_ABSOLUTE_TOLERANCE = 1e-10


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def verify_inputs() -> tuple[dict[int, dict[str, Any]], dict[str, Any]]:
    raw_results = {}
    payloads = {}
    topology_hashes = {}
    for environment_id in (38, 39):
        raw_path = ROOT / f"data/raw/env{environment_id}_bezier.json"
        actual_hash = sha256(raw_path)
        if actual_hash != RAW_HASHES[environment_id]:
            raise ValueError(f"Env{environment_id} canonical raw hash mismatch")
        raw_results[str(environment_id)] = {
            "path": raw_path.relative_to(ROOT).as_posix(),
            "sha256": actual_hash,
            "verified": True,
        }

        selected_path = ROOT / f"data/processed/env{environment_id}_topology.json"
        exact_path = ROOT / f"data/processed/env{environment_id}_topology_exact.json"
        selected = load_json(selected_path)
        exact = load_json(exact_path)
        expected = EXPECTED[environment_id]
        if selected["snapping_policy"]["relative_tolerance"] != 0:
            raise ValueError(f"Env{environment_id} selected topology is not zero-snapping")
        if selected["snapping_policy"]["absolute_tolerance_unity_world_units"] != 0:
            raise ValueError(f"Env{environment_id} selected topology is not zero-snapping")
        for field in ("locations", "fragments", "source_segment_inventory", "qa_counts"):
            if selected[field] != exact[field]:
                raise ValueError(
                    f"Env{environment_id} selected/exact mismatch at canonical snapping zero: {field}"
                )
        if len(selected["locations"]) != expected["locations"]:
            raise ValueError(f"Env{environment_id} topology location count mismatch")
        if len(selected["fragments"]) != expected["fragments"]:
            raise ValueError(f"Env{environment_id} topology fragment count mismatch")
        if selected["validated_interior_crossing_count"] != expected["crossings"]:
            raise ValueError(f"Env{environment_id} validated crossing count mismatch")
        payloads[environment_id] = selected
        topology_hashes[str(environment_id)] = {
            "selected_path": selected_path.relative_to(ROOT).as_posix(),
            "selected_sha256": sha256(selected_path),
            "exact_path": exact_path.relative_to(ROOT).as_posix(),
            "exact_sha256": sha256(exact_path),
            "selected_exact_structural_consistency_at_zero_snapping": True,
        }
    return payloads, {"raw": raw_results, "phase10_topology": topology_hashes}


def incident_changes(before: nx.MultiGraph, after: nx.MultiGraph) -> list[dict[str, Any]]:
    changes = []
    for node in sorted(before.nodes):
        if before.degree(node) != after.degree(node):
            changes.append(
                {
                    "topology_id": node,
                    "provenance_incident_count": before.degree(node),
                    "analytical_incident_count": after.degree(node),
                    "incident_count_change": after.degree(node) - before.degree(node),
                }
            )
    return changes


def count_parallel_edges(graph: nx.MultiGraph) -> list[dict[str, Any]]:
    pairs = []
    seen = set()
    for u, v in graph.edges():
        pair = tuple(sorted((u, v)))
        if pair in seen:
            continue
        seen.add(pair)
        keys = sorted(str(key) for key in graph[pair[0]][pair[1]])
        if len(keys) > 1:
            pairs.append({"nodes": list(pair), "edge_count": len(keys), "edge_keys": keys})
    return pairs


def plot_graphs(
    environment_id: int,
    detailed: nx.MultiGraph,
    simplified: nx.MultiGraph,
    suppressed: set[str],
) -> None:
    QA.mkdir(parents=True, exist_ok=True)
    for variant, graph in (("detailed", detailed), ("simplified", simplified)):
        fig, ax = plt.subplots(figsize=(10, 8), constrained_layout=True)
        for _, _, data in graph.edges(data=True):
            geometry = data["geometry"]
            ax.plot(
                [point[0] for point in geometry],
                [point[1] for point in geometry],
                color="#486581",
                linewidth=1.0,
                zorder=1,
            )
        if variant == "detailed" and suppressed:
            ax.scatter(
                [detailed.nodes[node]["x"] for node in sorted(suppressed)],
                [detailed.nodes[node]["y"] for node in sorted(suppressed)],
                s=9,
                c="#b8c2cc",
                label="suppressed geometry-only node",
                zorder=2,
            )
        retained = sorted(simplified.nodes)
        ax.scatter(
            [detailed.nodes[node]["x"] for node in retained],
            [detailed.nodes[node]["y"] for node in retained],
            s=15,
            facecolors="white",
            edgecolors="#102a43",
            linewidths=0.7,
            label="retained graph node",
            zorder=3,
        )
        crossings = [
            node
            for node in retained
            if detailed.nodes[node]["validated_interior_crossing"]
        ]
        ax.scatter(
            [detailed.nodes[node]["x"] for node in crossings],
            [detailed.nodes[node]["y"] for node in crossings],
            s=34,
            marker="x",
            c="#d64545",
            linewidths=1.2,
            label="Phase 9 validated junction",
            zorder=4,
        )
        ax.set_title(f"Env{environment_id} Phase 11 {variant} analytical graph QA")
        ax.set_xlabel("Unity world X")
        ax.set_ylabel("Unity world Y")
        ax.set_aspect("equal", adjustable="box")
        ax.legend(loc="best", fontsize=8)
        ax.grid(alpha=0.15)
        fig.savefig(QA / f"env{environment_id}-phase11-{variant}-graph.png", dpi=180)
        plt.close(fig)


def graphml_artifact(
    environment_id: int,
    variant: str,
    graph: nx.Graph,
    source_topology_sha256: str,
) -> dict[str, Any]:
    path = GRAPHS / f"env{environment_id}_{variant}.graphml"
    write_graphml(graph, path)
    loaded = read_graphml(path)
    roundtrip = validate_graphml_roundtrip(graph, loaded)
    manifest = {
        "phase11_graph_manifest_schema_version": "1.0.0",
        "environment_id": environment_id,
        "graph_variant": variant,
        "graphml_path": path.relative_to(ROOT).as_posix(),
        "graphml_sha256": sha256(path),
        "source_phase10_topology_sha256": source_topology_sha256,
        "coordinate_system": "Unity world XY",
        "coordinate_units": "Unity world units",
        "crs": None,
        "meters_per_unit": None,
        "canonical_snapping_tolerance": 0.0,
        "summary": graph_summary(graph),
        "graph_attributes": dict(graph.graph),
        "round_trip_validation": roundtrip,
    }
    manifest_path = path.with_suffix(".manifest.json")
    write_json(manifest_path, manifest)
    return manifest


def main() -> None:
    GRAPHS.mkdir(parents=True, exist_ok=True)
    QA.mkdir(parents=True, exist_ok=True)
    TABLES.mkdir(parents=True, exist_ok=True)
    payloads, input_verification = verify_inputs()

    all_graphs: dict[int, dict[str, nx.Graph]] = {}
    environment_qa: dict[str, Any] = {}
    all_exclusions = []
    manifests = []
    osmnx_results = {}

    import osmnx as ox

    for environment_id in (38, 39):
        provenance = topology_to_provenance_multigraph(payloads[environment_id])
        registered = REGISTERED_ZERO_CHORD_ANOMALIES if environment_id == 38 else ()
        analytical, exclusions = exclude_registered_anomaly_edges(
            provenance, registered
        )
        simplified, simplification_qa = simplify_analytical_graph(analytical)
        bidirectional = to_bidirectional_multidigraph(simplified)
        all_exclusions.extend(exclusions)

        expected = EXPECTED[environment_id]
        if provenance.number_of_edges() != expected["fragments"]:
            raise AssertionError("Provenance graph does not match Phase 10 fragments")
        if graph_summary(simplified)["validated_crossing_nodes_represented"] != expected[
            "crossings"
        ]:
            raise AssertionError("A validated crossing was lost during simplification")
        if abs(
            simplification_qa["total_length_preservation_error_unity_world_units"]
        ) > LENGTH_QA_ABSOLUTE_TOLERANCE:
            raise AssertionError("Simplification did not preserve total geometry length")

        nodes_gdf, edges_gdf = graph_to_gdfs(bidirectional)
        graph_attrs = {
            "coordinate_system": "Unity world XY",
            "coordinate_units": "Unity world units",
            "meters_per_unit": None,
            "canonical_snapping_tolerance": 0.0,
            "simplified": True,
            "crs": None,
        }
        try:
            osmnx_graph = ox.convert.graph_from_gdfs(
                nodes_gdf, edges_gdf, graph_attrs=graph_attrs
            )
            osmnx_result = {
                "graph_from_gdfs_accepted_crs_less_tables": True,
                "result_graph_type": type(osmnx_graph).__name__,
                "nodes": osmnx_graph.number_of_nodes(),
                "edges": osmnx_graph.number_of_edges(),
                "crs": osmnx_graph.graph.get("crs"),
                "structurally_osmnx_compatible": True,
                "eligible_for_crs_dependent_osmnx_functions": False,
                "limitation": (
                    "Unity world XY has no CRS, latitude/longitude, verified metre scale, or geographic north."
                ),
            }
        except Exception as error:  # documented compatibility limitation, not graph failure
            osmnx_result = {
                "graph_from_gdfs_accepted_crs_less_tables": False,
                "error_type": type(error).__name__,
                "error": str(error),
                "structurally_osmnx_compatible": True,
                "eligible_for_crs_dependent_osmnx_functions": False,
                "limitation": (
                    "OSMnx rejected CRS-less input; no CRS was fabricated. NetworkX graph and structural tables remain valid."
                ),
            }
        osmnx_results[str(environment_id)] = osmnx_result

        graphs = {
            "provenance_detailed": provenance,
            "analytical_detailed": analytical,
            "analytical_simplified": simplified,
            "osmnx_style_bidirectional": bidirectional,
        }
        all_graphs[environment_id] = graphs
        topology_sha = input_verification["phase10_topology"][str(environment_id)][
            "selected_sha256"
        ]
        for variant, graph in graphs.items():
            manifests.append(
                graphml_artifact(environment_id, variant, graph, topology_sha)
            )

        changes = incident_changes(provenance, analytical)
        environment_qa[str(environment_id)] = {
            "provenance_detailed_graph": graph_summary(provenance),
            "analytical_detailed_graph": graph_summary(analytical),
            "artifact_exclusion_incident_count_changes": changes,
            "simplification": simplification_qa,
            "simplified_analytical_graph": graph_summary(simplified),
            "parallel_edges": count_parallel_edges(simplified),
            "bidirectional_multidigraph": graph_summary(bidirectional),
        }
        plot_graphs(
            environment_id,
            analytical,
            simplified,
            set(simplification_qa["suppressed_node_ids"]),
        )

    if len(all_exclusions) != 5:
        raise AssertionError("Exactly five registered anomaly fragments must be excluded")
    write_json(
        QA / "phase11-zero-chord-artifact-exclusions.json",
        {
            "phase11_artifact_exclusion_schema_version": "1.0.0",
            "policy": (
                "Exclude only the five explicitly pre-registered Env38 zero-chord source anomalies from analytical graphs; use no numerical length threshold."
            ),
            "exclusion_count": len(all_exclusions),
            "exclusions": all_exclusions,
        },
    )

    table_path = TABLES / "phase11-graph-construction-qa.csv"
    fields = [
        "environment_id",
        "graph_variant",
        "graph_type",
        "nodes",
        "edges",
        "self_loops",
        "parallel_edge_pairs",
        "components",
        "validated_crossing_nodes_represented",
        "zero_chord_artifact_edges_represented",
        "simplified",
        "crs_assigned",
    ]
    with table_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for environment_id, graphs in all_graphs.items():
            for variant, graph in graphs.items():
                writer.writerow(
                    {
                        "environment_id": environment_id,
                        "graph_variant": variant,
                        **graph_summary(graph),
                    }
                )

    roundtrips = {
        f"env{manifest['environment_id']}_{manifest['graph_variant']}": manifest[
            "round_trip_validation"
        ]
        for manifest in manifests
    }
    qa_payload = {
        "phase11_graph_construction_schema_version": "1.0.0",
        "phase11_analysis_version": "1.0.0",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "acceptance_status": "PASS",
        "input_verification": input_verification,
        "canonical_snapping": {
            "relative_tolerance": 0.0,
            "absolute_tolerance_unity_world_units": 0.0,
            "verified": True,
        },
        "coordinate_policy": {
            "coordinate_system": "Unity world XY",
            "coordinate_units": "Unity world units",
            "crs": None,
            "meters_per_unit": None,
            "latitude_longitude_inferred": False,
            "geographic_north_inferred": False,
        },
        "artifact_policy": {
            "registered_source_anomaly_ids": sorted(REGISTERED_ZERO_CHORD_ANOMALIES),
            "provenance_graph_retains_all": True,
            "analytical_graph_exclusion_count": 5,
            "arbitrary_short_edge_threshold_used": False,
        },
        "simplification_algorithm": (
            "Deterministic maximal-chain traversal suppressing only non-validated degree-2 nodes with two distinct neighbors; geometry is concatenated without smoothing or resampling."
        ),
        "simplification_node_retention_rule": [
            "analytical undirected degree is not 2",
            "Phase 9 validated interior crossing",
            "network endpoint or branch",
            "required for parallel-edge, self-loop, or isolated-cycle representation",
            "required to preserve component connectivity",
        ],
        "length_qa_absolute_tolerance_unity_world_units": LENGTH_QA_ABSOLUTE_TOLERANCE,
        "environments": environment_qa,
        "all_48_validated_crossings_retained": (
            environment_qa["38"]["simplified_analytical_graph"][
                "validated_crossing_nodes_represented"
            ]
            + environment_qa["39"]["simplified_analytical_graph"][
                "validated_crossing_nodes_represented"
            ]
            == 48
        ),
        "graphml_round_trip_results": roundtrips,
        "all_graphml_round_trips_passed": all(
            result["passed"] for result in roundtrips.values()
        ),
        "osmnx_structural_compatibility": osmnx_results,
        "osmnx_crs_dependent_functions_used": False,
        "osmnx_automatic_simplification_used": False,
        "final_morphology_metrics_calculated": False,
        "software_versions": {
            "python": platform.python_version(),
            "networkx": importlib.metadata.version("networkx"),
            "osmnx": importlib.metadata.version("osmnx"),
            "geopandas": importlib.metadata.version("geopandas"),
            "shapely": importlib.metadata.version("shapely"),
            "matplotlib": importlib.metadata.version("matplotlib"),
        },
    }
    if not qa_payload["all_48_validated_crossings_retained"]:
        raise AssertionError("Not all 48 validated crossings were retained")
    if not qa_payload["all_graphml_round_trips_passed"]:
        raise AssertionError("At least one GraphML round trip failed")
    write_json(QA / "phase11-graph-construction.json", qa_payload)

    print("Canonical raw SHA-256 verification: PASS")
    print("Phase 10 selected/exact consistency and zero snapping: PASS")
    for environment_id in (38, 39):
        env = environment_qa[str(environment_id)]
        print(f"Env{environment_id} provenance: {env['provenance_detailed_graph']}")
        print(f"Env{environment_id} analytical detailed: {env['analytical_detailed_graph']}")
        print(f"Env{environment_id} simplified: {env['simplified_analytical_graph']}")
        print(f"Env{environment_id} bidirectional: {env['bidirectional_multidigraph']}")
    print("Registered anomaly exclusions: 5 exact fragments / no length threshold: PASS")
    print("All eight GraphML round trips: PASS")
    print("Phase 11: PASS")


if __name__ == "__main__":
    main()
