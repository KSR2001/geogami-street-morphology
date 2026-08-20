"""Calculate the pre-specified Phase 12 descriptive morphology metrics."""

from __future__ import annotations

import csv
import hashlib
import importlib.metadata
import json
import math
import os
import platform
import tempfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import networkx as nx
import numpy as np

os.environ.setdefault(
    "MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "geogami-matplotlib")
)
import matplotlib.pyplot as plt

try:
    from .morphology_metrics import (
        CIRCUITY_RATIO_NUMERICAL_TOLERANCE,
        aggregate_network_circuity,
        edge_circuity,
        euclidean_endpoint_distance,
        orientation_entropy,
        orientation_order,
        polyline_length,
        polyline_piece_observations,
        reciprocal_bearing,
        topology_summary,
        unity_frame_bearing,
    )
    from .network_graph import read_graphml
except ImportError:  # pragma: no cover - direct script execution
    from morphology_metrics import (
        CIRCUITY_RATIO_NUMERICAL_TOLERANCE,
        aggregate_network_circuity,
        edge_circuity,
        euclidean_endpoint_distance,
        orientation_entropy,
        orientation_order,
        polyline_length,
        polyline_piece_observations,
        reciprocal_bearing,
        topology_summary,
        unity_frame_bearing,
    )
    from network_graph import read_graphml


ROOT = Path(__file__).resolve().parents[1]
GRAPHS = ROOT / "data/graphs"
TABLES = ROOT / "outputs/tables"
FIGURES = ROOT / "outputs/figures"
QA = ROOT / "outputs/qa"
RAW_HASHES = {
    38: "43ea446a4a88e9f3d594fb8b72742f5d4b2a1ee8a03ebf8350c4c3cce45c5819",
    39: "e5dbce6b4d88656c9e0f3bbf6a814434f64b0fbe9b3ff1864ea3fafaf0883602",
}
EXPECTED = {
    38: {"detailed_nodes": 147, "detailed_edges": 171, "nodes": 60, "edges": 84, "crossings": 28},
    39: {"detailed_nodes": 53, "detailed_edges": 72, "nodes": 51, "edges": 70, "crossings": 20},
}
INTENDED_CLASS = {38: "curvilinear/curvy", 39: "grid-like"}
BIN_OFFSETS = [index * 0.5 for index in range(20)]
NUMERICAL_TOLERANCE = 1e-12


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
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def verify_inputs() -> tuple[dict[int, dict[str, nx.MultiGraph]], dict[str, Any]]:
    graphs: dict[int, dict[str, nx.MultiGraph]] = {}
    provenance: dict[str, Any] = {"raw_hashes": {}, "graph_manifests": {}}
    for environment_id in (38, 39):
        raw_path = ROOT / f"data/raw/env{environment_id}_bezier.json"
        actual_raw_hash = sha256(raw_path)
        if actual_raw_hash != RAW_HASHES[environment_id]:
            raise ValueError(f"Env{environment_id} raw hash mismatch")
        provenance["raw_hashes"][str(environment_id)] = {
            "path": raw_path.relative_to(ROOT).as_posix(),
            "sha256": actual_raw_hash,
            "verified": True,
        }

        topology = load_json(ROOT / f"data/processed/env{environment_id}_topology.json")
        if topology["snapping_policy"]["relative_tolerance"] != 0 or topology[
            "snapping_policy"
        ]["absolute_tolerance_unity_world_units"] != 0:
            raise ValueError("Phase 12 requires the canonical zero-snapping topology")

        graphs[environment_id] = {}
        for variant in ("analytical_detailed", "analytical_simplified"):
            graphml_path = GRAPHS / f"env{environment_id}_{variant}.graphml"
            manifest_path = graphml_path.with_suffix(".manifest.json")
            manifest = load_json(manifest_path)
            if sha256(graphml_path) != manifest["graphml_sha256"]:
                raise ValueError(f"GraphML hash mismatch: {graphml_path.name}")
            if not manifest["round_trip_validation"]["passed"]:
                raise ValueError(f"Phase 11 round-trip status failed: {graphml_path.name}")
            graph = read_graphml(graphml_path)
            if graph.is_directed() or not graph.is_multigraph():
                raise ValueError("Analytical metrics require undirected MultiGraph inputs")
            if graph.graph.get("crs") is not None:
                raise ValueError("A CRS must not be assigned to Unity coordinates")
            graphs[environment_id][variant] = graph
            provenance["graph_manifests"][f"env{environment_id}_{variant}"] = {
                "manifest_path": manifest_path.relative_to(ROOT).as_posix(),
                "manifest_sha256": sha256(manifest_path),
                "graphml_path": graphml_path.relative_to(ROOT).as_posix(),
                "graphml_sha256": manifest["graphml_sha256"],
                "round_trip_passed": True,
            }

        detailed = graphs[environment_id]["analytical_detailed"]
        simplified = graphs[environment_id]["analytical_simplified"]
        expected = EXPECTED[environment_id]
        observed = (
            detailed.number_of_nodes(), detailed.number_of_edges(),
            simplified.number_of_nodes(), simplified.number_of_edges(),
        )
        required = (
            expected["detailed_nodes"], expected["detailed_edges"],
            expected["nodes"], expected["edges"],
        )
        if observed != required:
            raise ValueError(f"Env{environment_id} Phase 11 graph counts changed: {observed}")
        for graph in (detailed, simplified):
            if nx.number_connected_components(graph) != 1 or nx.number_of_selfloops(graph) != 0:
                raise ValueError("Analytical graph connectivity/self-loop QA failed")
            if any(
                data.get("zero_chord_anomaly")
                or data.get("zero_chord_anomaly_involvement")
                for _, _, data in graph.edges(data=True)
            ):
                raise ValueError("A registered zero-chord artifact entered an analytical graph")
        crossing_count = sum(
            bool(data.get("validated_interior_crossing"))
            for _, data in simplified.nodes(data=True)
        )
        if crossing_count != expected["crossings"]:
            raise ValueError("A validated Phase 9 crossing is missing")
    return graphs, provenance


def simplified_bearings(graph: nx.MultiGraph) -> list[float]:
    bearings = []
    for u, v, _ in graph.edges(keys=True):
        first, second = graph.nodes[u], graph.nodes[v]
        bearing = unity_frame_bearing(first["x"], first["y"], second["x"], second["y"])
        bearings.extend((bearing, reciprocal_bearing(bearing)))
    return bearings


def detailed_piece_observations(graph: nx.MultiGraph) -> tuple[list[float], list[float]]:
    bearings: list[float] = []
    weights: list[float] = []
    for _, _, data in graph.edges(data=True):
        edge_bearings, edge_weights = polyline_piece_observations(data["geometry"])
        bearings.extend(edge_bearings)
        weights.extend(edge_weights)
    return bearings, weights


def descriptive(values: list[float]) -> dict[str, float | int]:
    array = np.asarray(values, dtype=float)
    return {
        "count": int(array.size),
        "total": float(array.sum()),
        "mean": float(array.mean()),
        "median": float(np.median(array)),
        "minimum": float(array.min()),
        "maximum": float(array.max()),
        "standard_deviation_population": float(array.std(ddof=0)),
        "q25": float(np.quantile(array, 0.25)),
        "q75": float(np.quantile(array, 0.75)),
        "q90": float(np.quantile(array, 0.90)),
        "q95": float(np.quantile(array, 0.95)),
    }


def write_orientation_table(
    environment_id: int,
    unweighted: dict[str, np.ndarray],
    weighted: dict[str, np.ndarray],
) -> None:
    path = TABLES / f"phase12-env{environment_id}-orientation-bins.csv"
    with path.open("w", newline="", encoding="utf-8") as stream:
        fields = [
            "environment_id", "bin_centre_degrees", "bin_lower_edge_degrees",
            "bin_upper_edge_degrees", "unweighted_observation_count",
            "unweighted_probability", "weighted_detailed_length_unity",
            "weighted_probability",
        ]
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for index in range(36):
            writer.writerow(
                {
                    "environment_id": environment_id,
                    "bin_centre_degrees": unweighted["centres"][index],
                    "bin_lower_edge_degrees": unweighted["lower_edges"][index],
                    "bin_upper_edge_degrees": unweighted["upper_edges"][index],
                    "unweighted_observation_count": int(unweighted["totals"][index]),
                    "unweighted_probability": unweighted["probabilities"][index],
                    "weighted_detailed_length_unity": weighted["totals"][index],
                    "weighted_probability": weighted["probabilities"][index],
                }
            )


def rose_plot(environment_id: int, histogram: dict[str, np.ndarray], weighted: bool) -> None:
    probabilities = histogram["probabilities"]
    theta = np.deg2rad(histogram["centres"])
    fig, ax = plt.subplots(figsize=(7.2, 7.2), subplot_kw={"projection": "polar"}, constrained_layout=True)
    ax.bar(theta, probabilities, width=np.deg2rad(10), align="center", color="#486581", edgecolor="white", linewidth=0.5)
    ax.set_theta_zero_location("N")
    ax.set_theta_direction(-1)
    ax.set_title(
        f"Env{environment_id} {'length-weighted detailed' if weighted else 'unweighted simplified'} orientation\nUnity-frame: 0° = +Unity Y",
        pad=22,
    )
    ax.set_ylabel("Probability", labelpad=28)
    suffix = "weighted" if weighted else "unweighted"
    fig.savefig(FIGURES / f"env{environment_id}-orientation-rose-{suffix}.png", dpi=220)
    plt.close(fig)


def network_map(environment_id: int, graph: nx.MultiGraph) -> None:
    fig, ax = plt.subplots(figsize=(8, 8), constrained_layout=True)
    for _, _, data in graph.edges(data=True):
        geometry = data["geometry"]
        ax.plot([p[0] for p in geometry], [p[1] for p in geometry], color="#334e68", linewidth=1.2)
    ax.scatter(
        [data["x"] for _, data in graph.nodes(data=True)],
        [data["y"] for _, data in graph.nodes(data=True)],
        s=8, c="#d64545", alpha=0.65, zorder=3,
    )
    ax.set_aspect("equal", adjustable="box")
    ax.set_axis_off()
    ax.set_title(f"Env{environment_id} final analytical network\nUnity world X/Y (unrotated)")
    fig.savefig(FIGURES / f"env{environment_id}-final-analytical-network.png", dpi=220)
    plt.close(fig)


def comparison_figures(results: dict[int, dict[str, Any]], sensitivity: list[dict[str, Any]]) -> None:
    environments = [38, 39]
    colors = ["#486581", "#d64545"]
    fig, axes = plt.subplots(2, 2, figsize=(10, 8), constrained_layout=True)
    panels = [
        ("H_o_nats", "Unweighted entropy H_o (nats)"),
        ("H_w_nats", "Weighted entropy H_w (nats)"),
        ("phi", "Orientation order phi"),
        ("aggregate_circuity", "Aggregate circuity (dimensionless)"),
    ]
    for ax, (field, title) in zip(axes.flat, panels):
        ax.bar(["Env38", "Env39"], [results[e][field] for e in environments], color=colors)
        ax.set_title(title)
        ax.grid(axis="y", alpha=0.2)
    fig.savefig(FIGURES / "env38-vs-env39-primary-metrics.png", dpi=220)
    plt.close(fig)

    for field, filename, xlabel in (
        ("edge_circuities", "env38-vs-env39-circuity-distribution.png", "Individual-edge circuity (dimensionless)"),
        ("street_lengths", "env38-vs-env39-street-length-distribution.png", "Simplified street-segment length (Unity world units)"),
    ):
        fig, ax = plt.subplots(figsize=(8, 5), constrained_layout=True)
        combined = np.concatenate([results[e][field] for e in environments])
        bins = np.histogram_bin_edges(combined, bins="auto")
        for environment_id, color in zip(environments, colors):
            ax.hist(results[environment_id][field], bins=bins, alpha=0.55, label=f"Env{environment_id}", color=color)
        ax.set_xlabel(xlabel)
        ax.set_ylabel("Street-segment count")
        ax.legend()
        ax.grid(alpha=0.2)
        fig.savefig(FIGURES / filename, dpi=220)
        plt.close(fig)

    degrees = sorted(
        {int(degree) for e in environments for degree in results[e]["topology"]["degree_distribution"]}
    )
    x = np.arange(len(degrees))
    fig, ax = plt.subplots(figsize=(8, 5), constrained_layout=True)
    for index, (environment_id, color) in enumerate(zip(environments, colors)):
        values = [results[environment_id]["topology"]["degree_distribution"].get(str(d), 0) for d in degrees]
        ax.bar(x + (index - 0.5) * 0.35, values, width=0.35, label=f"Env{environment_id}", color=color)
    ax.set_xticks(x, degrees)
    ax.set_xlabel("Analytical node degree / incident street count")
    ax.set_ylabel("Node count")
    ax.legend()
    ax.grid(axis="y", alpha=0.2)
    fig.savefig(FIGURES / "env38-vs-env39-node-degree-distribution.png", dpi=220)
    plt.close(fig)

    offsets = [row["bin_centre_origin_offset_degrees"] for row in sensitivity]
    fig, axes = plt.subplots(2, 1, figsize=(9, 7), sharex=True, constrained_layout=True)
    for ax, field, ylabel in (
        (axes[0], "H_o", "H_o (nats)"), (axes[1], "H_w", "H_w (nats)"),
    ):
        for environment_id, color in zip(environments, colors):
            ax.plot(offsets, [row[f"env{environment_id}_{field}"] for row in sensitivity], marker="o", ms=3, label=f"Env{environment_id}", color=color)
        ax.set_ylabel(ylabel)
        ax.grid(alpha=0.2)
        ax.legend()
    axes[1].set_xlabel("Bin-centre origin offset (degrees from canonical Unity frame)")
    fig.savefig(FIGURES / "phase12-bin-origin-sensitivity.png", dpi=220)
    plt.close(fig)


def main() -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    FIGURES.mkdir(parents=True, exist_ok=True)
    QA.mkdir(parents=True, exist_ok=True)
    graphs, input_provenance = verify_inputs()
    results: dict[int, dict[str, Any]] = {}
    circuity_rows: list[dict[str, Any]] = []

    for environment_id in (38, 39):
        detailed = graphs[environment_id]["analytical_detailed"]
        simplified = graphs[environment_id]["analytical_simplified"]
        chord_bearings = simplified_bearings(simplified)
        detailed_bearings, detailed_weights = detailed_piece_observations(detailed)
        simplified_piece_bearings, simplified_piece_weights = detailed_piece_observations(simplified)
        h_o, unweighted_histogram = orientation_entropy(chord_bearings)
        h_w, weighted_histogram = orientation_entropy(detailed_bearings, weights=detailed_weights)
        h_w_simplified, _ = orientation_entropy(
            simplified_piece_bearings, weights=simplified_piece_weights
        )
        if not math.isclose(h_w, h_w_simplified, rel_tol=0.0, abs_tol=NUMERICAL_TOLERANCE):
            raise AssertionError("H_w is not invariant to Phase 11 geometry concatenation")
        phi = orientation_order(h_o)
        write_orientation_table(environment_id, unweighted_histogram, weighted_histogram)
        rose_plot(environment_id, unweighted_histogram, weighted=False)
        rose_plot(environment_id, weighted_histogram, weighted=True)
        network_map(environment_id, simplified)

        street_lengths = [float(data["length"]) for _, _, data in simplified.edges(data=True)]
        length_summary = descriptive(street_lengths)
        recomputed_lengths = [polyline_length(data["geometry"]) for _, _, data in simplified.edges(data=True)]
        maximum_length_error = max(abs(a - b) for a, b in zip(street_lengths, recomputed_lengths))
        if maximum_length_error > NUMERICAL_TOLERANCE:
            raise AssertionError("Stored and recomputed simplified lengths disagree")

        network_lengths: list[float] = []
        straight_distances: list[float] = []
        edge_circularities: list[float] = []
        sorted_edges = sorted(
            simplified.edges(keys=True, data=True), key=lambda row: row[3]["simplified_edge_id"]
        )
        for u, v, _, data in sorted_edges:
            first, second = simplified.nodes[u], simplified.nodes[v]
            straight = euclidean_endpoint_distance(first["x"], first["y"], second["x"], second["y"])
            if straight == 0:
                raise ValueError(f"Zero endpoint distance on analytical edge {data['simplified_edge_id']}")
            network = float(data["length"])
            circularity = edge_circuity(network, straight)
            network_lengths.append(network)
            straight_distances.append(straight)
            edge_circularities.append(circularity)
            circuity_rows.append(
                {
                    "environment_id": environment_id,
                    "simplified_edge_id": data["simplified_edge_id"],
                    "u": u,
                    "v": v,
                    "network_length": network,
                    "straight_distance": straight,
                    "circuity": circularity,
                    "source_fragment_count": data["source_fragment_count"],
                    "source_shape_provenance": json.dumps(data["ordered_source_shape_ids"], separators=(",", ":")),
                }
            )
        aggregate_circuity = aggregate_network_circuity(network_lengths, straight_distances)
        circuity_summary = descriptive(edge_circularities)
        circuity_summary["values_below_one_within_numerical_tolerance"] = sum(
            value < 1.0 for value in edge_circularities
        )
        circuity_summary["ratio_numerical_tolerance"] = CIRCUITY_RATIO_NUMERICAL_TOLERANCE
        circuity_summary["minimum_network_length_minus_straight_distance_unity"] = min(
            network - straight
            for network, straight in zip(network_lengths, straight_distances)
        )
        topology = topology_summary(simplified)
        direct_degree_distribution = Counter(dict(simplified.degree()).values())
        if topology["degree_distribution"] != {
            str(degree): direct_degree_distribution[degree]
            for degree in sorted(direct_degree_distribution)
        }:
            raise AssertionError("Manual and NetworkX degree distributions disagree")

        entropy_crosscheck = -math.fsum(
            probability * math.log(probability)
            for probability in unweighted_histogram["probabilities"]
            if probability > 0
        )
        phi_crosscheck = 1.0 - (
            (h_o - math.log(4.0)) / (math.log(36.0) - math.log(4.0))
        ) ** 2
        circuity_crosscheck = math.fsum(network_lengths) / math.fsum(straight_distances)
        crosschecks = {
            "entropy_absolute_error": abs(h_o - entropy_crosscheck),
            "maximum_stored_vs_recomputed_length_error_unity": maximum_length_error,
            "aggregate_circuity_absolute_error": abs(aggregate_circuity - circuity_crosscheck),
            "topology_degree_distribution_matches": True,
            "phi_absolute_error": abs(phi - phi_crosscheck),
            "H_w_detailed_vs_simplified_absolute_error": abs(h_w - h_w_simplified),
        }
        if any(
            value > NUMERICAL_TOLERANCE
            for key, value in crosschecks.items()
            if isinstance(value, float)
        ):
            raise AssertionError(f"Independent formula cross-check failed: {crosschecks}")

        results[environment_id] = {
            "environment_id": environment_id,
            "intended_class": INTENDED_CLASS[environment_id],
            "H_o_nats": h_o,
            "H_w_nats": h_w,
            "H_w_from_simplified_geometry_nats": h_w_simplified,
            "phi": phi,
            "street_lengths": street_lengths,
            "street_length_summary": length_summary,
            "edge_circuities": edge_circularities,
            "aggregate_circuity": aggregate_circuity,
            "individual_edge_circuity_summary": circuity_summary,
            "topology": topology,
            "formula_crosschecks": crosschecks,
        }

    with (TABLES / "phase12-edge-circuity.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(circuity_rows[0]))
        writer.writeheader()
        writer.writerows(circuity_rows)

    sensitivity_rows = []
    for offset in BIN_OFFSETS:
        row: dict[str, Any] = {"bin_centre_origin_offset_degrees": offset}
        for environment_id in (38, 39):
            simplified = graphs[environment_id]["analytical_simplified"]
            detailed = graphs[environment_id]["analytical_detailed"]
            h_o, _ = orientation_entropy(
                simplified_bearings(simplified), centre_offset_degrees=offset
            )
            bearings, weights = detailed_piece_observations(detailed)
            h_w, _ = orientation_entropy(
                bearings, weights=weights, centre_offset_degrees=offset
            )
            row[f"env{environment_id}_H_o"] = h_o
            row[f"env{environment_id}_H_w"] = h_w
        row["H_o_difference_env38_minus_env39"] = row["env38_H_o"] - row["env39_H_o"]
        row["H_w_difference_env38_minus_env39"] = row["env38_H_w"] - row["env39_H_w"]
        sensitivity_rows.append(row)
    with (TABLES / "phase12-orientation-bin-origin-sensitivity.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(sensitivity_rows[0]))
        writer.writeheader()
        writer.writerows(sensitivity_rows)

    sensitivity_summary: dict[str, Any] = {}
    for environment_id in (38, 39):
        sensitivity_summary[str(environment_id)] = {}
        for metric in ("H_o", "H_w"):
            values = [row[f"env{environment_id}_{metric}"] for row in sensitivity_rows]
            sensitivity_summary[str(environment_id)][metric] = {
                "minimum": min(values), "maximum": max(values), "mean": float(np.mean(values))
            }
    h_o_support = sum(row["H_o_difference_env38_minus_env39"] > 0 for row in sensitivity_rows)
    h_w_support = sum(row["H_w_difference_env38_minus_env39"] > 0 for row in sensitivity_rows)
    sensitivity_summary["comparison_consistency"] = {
        "offset_count": len(BIN_OFFSETS),
        "Env38_H_o_greater_count": h_o_support,
        "Env38_H_o_greater_proportion": h_o_support / len(BIN_OFFSETS),
        "Env38_H_w_greater_count": h_w_support,
        "Env38_H_w_greater_proportion": h_w_support / len(BIN_OFFSETS),
    }

    primary_fields = [
        "environment_id", "intended_class", "H_o_nats", "H_w_nats", "phi",
        "node_count", "street_segment_count", "component_count",
        "total_street_length_unity", "mean_street_length_unity", "median_street_length_unity",
        "average_streets_per_node", "dead_end_count", "dead_end_proportion",
        "three_way_count", "three_way_proportion", "four_way_count", "four_way_proportion",
        "degree_ge_5_count", "aggregate_circuity", "mean_edge_circuity",
        "median_edge_circuity", "canonical_snapping_tolerance", "crs", "meter_scale_verified",
    ]
    primary_rows = []
    for environment_id in (38, 39):
        result = results[environment_id]
        topo = result["topology"]
        lengths = result["street_length_summary"]
        circularities = result["individual_edge_circuity_summary"]
        primary_rows.append(
            {
                "environment_id": environment_id, "intended_class": result["intended_class"],
                "H_o_nats": result["H_o_nats"], "H_w_nats": result["H_w_nats"], "phi": result["phi"],
                "node_count": topo["node_count"], "street_segment_count": topo["edge_street_segment_count"],
                "component_count": topo["connected_component_count"],
                "total_street_length_unity": lengths["total"], "mean_street_length_unity": lengths["mean"],
                "median_street_length_unity": lengths["median"],
                "average_streets_per_node": topo["average_incident_streets_per_node"],
                "dead_end_count": topo["dead_end_count"], "dead_end_proportion": topo["dead_end_proportion"],
                "three_way_count": topo["three_way_count"], "three_way_proportion": topo["three_way_proportion"],
                "four_way_count": topo["four_way_count"], "four_way_proportion": topo["four_way_proportion"],
                "degree_ge_5_count": topo["degree_ge_5_count"],
                "aggregate_circuity": result["aggregate_circuity"],
                "mean_edge_circuity": circularities["mean"], "median_edge_circuity": circularities["median"],
                "canonical_snapping_tolerance": 0.0, "crs": None, "meter_scale_verified": False,
            }
        )
    with (TABLES / "phase12-primary-morphology-metrics.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=primary_fields)
        writer.writeheader()
        writer.writerows(primary_rows)

    row_by_env = {row["environment_id"]: row for row in primary_rows}
    comparison_rows = []
    conceptually_nonrelative = {"H_o_nats", "H_w_nats", "phi", "canonical_snapping_tolerance"}
    for metric in primary_fields:
        if metric in {"environment_id", "intended_class", "crs", "meter_scale_verified"}:
            continue
        env38, env39 = row_by_env[38][metric], row_by_env[39][metric]
        difference = env38 - env39
        relative = None if metric in conceptually_nonrelative or env39 == 0 else difference / env39
        comparison_rows.append(
            {"metric": metric, "Env38": env38, "Env39": env39, "absolute_difference_env38_minus_env39": difference, "relative_difference_vs_env39": relative}
        )
    with (TABLES / "phase12-env38-vs-env39-comparison.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(comparison_rows[0]))
        writer.writeheader()
        writer.writerows(comparison_rows)

    def assess(first: float, second: float, relation: str) -> str:
        if math.isclose(first, second, rel_tol=0.0, abs_tol=NUMERICAL_TOLERANCE):
            return "equal_within_reported_precision"
        supported = first > second if relation == ">" else first < second
        return "supported" if supported else "not_supported"

    hypotheses = {
        "H1": {"expectation": "Env38 H_o > Env39 H_o", "assessment": assess(results[38]["H_o_nats"], results[39]["H_o_nats"], ">")},
        "H2": {"expectation": "Env38 H_w > Env39 H_w", "assessment": assess(results[38]["H_w_nats"], results[39]["H_w_nats"], ">")},
        "H3": {"expectation": "Env38 phi < Env39 phi", "assessment": assess(results[38]["phi"], results[39]["phi"], "<")},
        "H4": {"expectation": "Env38 aggregate circuity > Env39 aggregate circuity", "assessment": assess(results[38]["aggregate_circuity"], results[39]["aggregate_circuity"], ">")},
    }
    supported_count = sum(value["assessment"] == "supported" for value in hypotheses.values())
    interpretation = (
        f"{supported_count} of 4 pre-registered directional expectations are supported. "
        "Orientation, curvature, and topology are interpreted descriptively for these two designed environments without inferential testing."
    )

    comparison_figures(results, sensitivity_rows)
    qa_payload = {
        "phase12_final_morphology_schema_version": "1.0.0",
        "analysis_version": "1.0.0",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "acceptance_status": "PASS",
        "input_provenance": input_provenance,
        "software_versions": {
            "python": platform.python_version(), "numpy": importlib.metadata.version("numpy"),
            "scipy": importlib.metadata.version("scipy"), "networkx": importlib.metadata.version("networkx"),
            "matplotlib": importlib.metadata.version("matplotlib"),
        },
        "coordinate_convention": {
            "name": "Unity-frame local planar bearing", "formula": "degrees(atan2(dx, dy)) mod 360",
            "zero_degrees": "+Unity Y", "90_degrees": "+Unity X", "180_degrees": "-Unity Y",
            "270_degrees": "-Unity X", "geographic_north_claimed": False, "crs": None,
            "units": "Unity world units", "meter_scale_verified": False,
        },
        "orientation_bin_configuration": {
            "bin_count": 36, "bin_width_degrees": 10.0,
            "canonical_bin_centres_degrees": [float(v) for v in np.arange(0, 360, 10)],
            "canonical_edge_shift_degrees": -5.0, "logarithm_base": "natural",
        },
        "results": {
            str(environment_id): {
                key: value for key, value in results[environment_id].items()
                if key not in {"street_lengths", "edge_circuities"}
            }
            for environment_id in (38, 39)
        },
        "orientation_bin_origin_sensitivity": {
            "offsets_degrees": BIN_OFFSETS, "summary": sensitivity_summary, "rows": sensitivity_rows,
        },
        "hypothesis_assessment": hypotheses,
        "overall_interpretation": interpretation,
        "qa_checks": {
            "raw_hashes_pass": True, "phase11_manifests_and_round_trips_pass": True,
            "graph_counts_pass": True, "one_component_each": True,
            "all_48_validated_crossings_retained": True,
            "zero_chord_artifacts_absent_from_analytical_metrics": True,
            "H_w_representation_invariance_pass": True,
            "all_formula_crosschecks_pass": True,
            "numerical_tolerance": NUMERICAL_TOLERANCE,
            "inferential_tests_performed": False,
        },
        "artifact_exclusion_policy": {
            "registered_env38_artifact_count": 5, "retained_in_provenance_graph": True,
            "excluded_from_analytical_graph": True, "arbitrary_short_edge_threshold_used": False,
        },
        "canonical_snapping_tolerance_unity_world_units": 0.0,
        "crs": None, "meter_scale_verified": False,
    }
    write_json(QA / "phase12-final-morphology-results.json", qa_payload)

    print("Canonical raw SHA-256 verification: PASS")
    print("Phase 11 manifests, GraphML hashes/round trips, counts, and zero snapping: PASS")
    for environment_id in (38, 39):
        result = results[environment_id]
        print(
            f"Env{environment_id}: H_o={result['H_o_nats']:.15f}, H_w={result['H_w_nats']:.15f}, "
            f"phi={result['phi']:.15f}, circuity={result['aggregate_circuity']:.15f}"
        )
    print(f"Bin-origin support: H_o {h_o_support}/20; H_w {h_w_support}/20")
    print("Independent formula cross-checks: PASS")
    print("Phase 12: PASS")


if __name__ == "__main__":
    main()
