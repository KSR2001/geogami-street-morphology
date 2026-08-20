"""Construct Phase 10 exact topology and endpoint-based snapping sensitivity QA."""

from __future__ import annotations

import csv
import hashlib
import importlib.metadata
import json
import os
import platform
import tempfile
from collections import Counter, defaultdict
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

os.environ.setdefault(
    "MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "geogami-matplotlib")
)
import matplotlib.pyplot as plt

try:
    from .bezier_geometry import adaptive_quadratic_bezier_polyline
    from .topology_geometry import (
        DisjointSet,
        ambiguous_candidate_ids,
        deterministic_location_ids,
        endpoint_to_endpoint_distance,
        exact_endpoint_groups,
        nearest_point_on_quadratic,
        split_quadratic_at_parameters,
    )
except ImportError:  # pragma: no cover - direct script execution
    from bezier_geometry import adaptive_quadratic_bezier_polyline
    from topology_geometry import (
        DisjointSet,
        ambiguous_candidate_ids,
        deterministic_location_ids,
        endpoint_to_endpoint_distance,
        exact_endpoint_groups,
        nearest_point_on_quadratic,
        split_quadratic_at_parameters,
    )


ROOT = Path(__file__).resolve().parents[1]
RAW_HASHES = {
    38: "43ea446a4a88e9f3d594fb8b72742f5d4b2a1ee8a03ebf8350c4c3cce45c5819",
    39: "e5dbce6b4d88656c9e0f3bbf6a814434f64b0fbe9b3ff1864ea3fafaf0883602",
}
SOURCE_COUNTS = {38: 120, 39: 32}
CURVE_TOLERANCE = 0.140331308417064
REFERENCE_SCALE = 701.656542085319
ROOT_PARAMETER_EQUIVALENCE = 2e-5
ROOT_COORDINATE_EQUIVALENCE = 7.01656542085319e-8
RELATIVE_TOLERANCES = [
    0.0,
    1e-8,
    2e-8,
    5e-8,
    1e-7,
    2e-7,
    5e-7,
    1e-6,
    2e-6,
    5e-6,
    1e-5,
    2e-5,
    5e-5,
    1e-4,
    2e-4,
    5e-4,
    1e-3,
]
ABSOLUTE_TOLERANCES = [value * REFERENCE_SCALE for value in RELATIVE_TOLERANCES]
ZERO_CHORD_IDS = {
    "env38_shape_4330855547529842337_segment_0006",
    "env38_shape_4330855547529842337_segment_0019",
    "env38_shape_4330855547829185599_segment_0007",
    "env38_shape_4330855547829185599_segment_0011",
    "env38_shape_4330855547829185599_segment_0012",
}

PROCESSED = ROOT / "data/processed"
TABLES = ROOT / "outputs/tables"
QA = ROOT / "outputs/qa"
PHASE9_JSON = QA / "phase9-3d-navigability-validation.json"
PHASE9_CSV = TABLES / "phase9-3d-navigability-review.csv"
PHASE8_CSV = TABLES / "phase8-3d-crossing-review.csv"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def load_and_verify_inputs() -> tuple[dict[int, dict[str, Any]], list[dict[str, str]], dict[str, Any]]:
    sources: dict[int, dict[str, Any]] = {}
    for environment_id, expected_hash in RAW_HASHES.items():
        path = ROOT / f"data/raw/env{environment_id}_bezier.json"
        actual_hash = sha256(path)
        if actual_hash != expected_hash:
            raise ValueError(
                f"Env{environment_id} raw hash changed: expected {expected_hash}, found {actual_hash}"
            )
        source = json.loads(path.read_text(encoding="utf-8"))
        if int(source["total_segment_count"]) != SOURCE_COUNTS[environment_id]:
            raise ValueError(f"Unexpected Env{environment_id} source segment count")
        sources[environment_id] = source

    phase9 = json.loads(PHASE9_JSON.read_text(encoding="utf-8"))
    with PHASE9_CSV.open(encoding="utf-8", newline="") as source:
        decisions = list(csv.DictReader(source))
    if len(decisions) != 48:
        raise ValueError("Phase 9 must contain exactly 48 review decisions")
    counts = Counter(row["navigability_decision"] for row in decisions)
    if counts != Counter({"connected_same_level": 48}):
        raise ValueError(f"Phase 9 decisions are not final: {dict(counts)}")
    environment_counts = Counter(int(row["environment_id"]) for row in decisions)
    if environment_counts != Counter({38: 28, 39: 20}):
        raise ValueError(f"Unexpected Phase 9 environment counts: {dict(environment_counts)}")
    if not phase9.get("manual_review_completed") or phase9.get("acceptance_status") != "COMPLETE":
        raise ValueError("Phase 9 machine-readable acceptance is not complete")

    with PHASE8_CSV.open(encoding="utf-8", newline="") as source:
        phase8_rows = {row["event_id"]: row for row in csv.DictReader(source)}
    for row in decisions:
        original = phase8_rows.get(row["event_id"])
        if original is None or row["x"] != original["x"] or row["y"] != original["y"]:
            raise ValueError(f"Phase 9 changed Phase 8 identity/coordinates for {row['event_id']}")
    return sources, decisions, phase9


def flatten_segments(source: dict[str, Any]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for shape in source["shapes"]:
        for segment in shape["segments"]:
            world = segment["world"]
            p0 = np.array([world["p0"]["x"], world["p0"]["y"]], dtype=np.float64)
            p1 = np.array([world["p1"]["x"], world["p1"]["y"]], dtype=np.float64)
            p2 = np.array([world["p2"]["x"], world["p2"]["y"]], dtype=np.float64)
            zero_chord = bool(np.array_equal(p0, p2) and not np.array_equal(p0, p1))
            if zero_chord != (segment["segment_id"] in ZERO_CHORD_IDS):
                raise ValueError(f"Zero-chord baseline mismatch for {segment['segment_id']}")
            records.append(
                {
                    "environment_id": int(source["environment_id"]),
                    "shape_id": shape["shape_id"],
                    "shape_index": int(shape["shape_index"]),
                    "segment_id": segment["segment_id"],
                    "segment_index": int(segment["segment_index"]),
                    "p0": p0,
                    "p1": p1,
                    "p2": p2,
                    "zero_chord_source_artifact": zero_chord,
                }
            )
    return sorted(records, key=lambda item: item["segment_id"])


def endpoint_records(segments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    records = []
    for segment in segments:
        for side in ("p0", "p2"):
            point = segment[side]
            records.append(
                {
                    "endpoint_id": f"{segment['segment_id']}:{side}",
                    "endpoint_side": side,
                    "x": float(point[0]),
                    "y": float(point[1]),
                    "shape_id": segment["shape_id"],
                    "segment_id": segment["segment_id"],
                    "zero_chord_source_artifact": segment["zero_chord_source_artifact"],
                }
            )
    return records


def split_records_for_environment(
    environment_id: int, decisions: list[dict[str, str]]
) -> dict[str, list[dict[str, Any]]]:
    result: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in decisions:
        if int(row["environment_id"]) != environment_id:
            continue
        coordinate = (float(row["x"]), float(row["y"]))
        for segment_field, parameter_field in (("segment_a_id", "t_a"), ("segment_b_id", "t_b")):
            result[row[segment_field]].append(
                {
                    "parameter": float(row[parameter_field]),
                    "coordinate": coordinate,
                    "event_id": row["event_id"],
                    "review_location_id": row["review_location_id"],
                    "phase9_decision": row["navigability_decision"],
                    "phase9_evidence_type": row["evidence_type"],
                }
            )
    for segment_id, values in result.items():
        values.sort(key=lambda item: (item["parameter"], item["event_id"]))
        deduplicated: list[dict[str, Any]] = []
        for value in values:
            if deduplicated:
                previous = deduplicated[-1]
                parameter_equivalent = (
                    abs(value["parameter"] - previous["parameter"])
                    <= ROOT_PARAMETER_EQUIVALENCE
                )
                coordinate_equivalent = (
                    endpoint_to_endpoint_distance(value["coordinate"], previous["coordinate"])
                    <= ROOT_COORDINATE_EQUIVALENCE
                )
                if parameter_equivalent and coordinate_equivalent:
                    previous.setdefault("additional_event_ids", []).append(value["event_id"])
                    continue
            deduplicated.append(value)
        result[segment_id] = deduplicated
    return dict(result)


def polyline_length(vertices: np.ndarray) -> float:
    if len(vertices) < 2:
        return 0.0
    return float(np.linalg.norm(np.diff(vertices, axis=0), axis=1).sum())


def topology_components(locations: list[dict[str, Any]], fragments: list[dict[str, Any]]) -> DisjointSet:
    components = DisjointSet(location["topology_location_id"] for location in locations)
    for fragment in fragments:
        components.union(
            fragment["start_topology_location_id"], fragment["end_topology_location_id"]
        )
    return components


def build_exact_topology(
    environment_id: int,
    source: dict[str, Any],
    decisions: list[dict[str, str]],
    phase9: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    segments = flatten_segments(source)
    segment_by_id = {segment["segment_id"]: segment for segment in segments}
    endpoints = endpoint_records(segments)
    endpoint_groups = exact_endpoint_groups(endpoints)
    split_records = split_records_for_environment(environment_id, decisions)
    environment_decisions = [
        row for row in decisions if int(row["environment_id"]) == environment_id
    ]

    coordinates = set(endpoint_groups)
    coordinates.update((float(row["x"]), float(row["y"])) for row in environment_decisions)
    location_ids = deterministic_location_ids(environment_id, coordinates)
    crossing_by_coordinate: dict[tuple[float, float], list[dict[str, str]]] = defaultdict(list)
    for row in environment_decisions:
        crossing_by_coordinate[(float(row["x"]), float(row["y"]))].append(row)

    locations_by_id: dict[str, dict[str, Any]] = {}
    for coordinate in sorted(coordinates):
        endpoint_sources = endpoint_groups.get(coordinate, [])
        crossing_sources = crossing_by_coordinate.get(coordinate, [])
        if endpoint_sources and crossing_sources:
            source_type = "multiple_sources"
        elif crossing_sources:
            source_type = "validated_interior_crossing"
        else:
            source_type = "authored_exact_endpoint"
        location_id = location_ids[coordinate]
        locations_by_id[location_id] = {
            "topology_location_id": location_id,
            "environment_id": environment_id,
            "x": coordinate[0],
            "y": coordinate[1],
            "source_type": source_type,
            "authored_endpoint_sources": endpoint_sources,
            "phase8_event_ids": sorted(row["event_id"] for row in crossing_sources),
            "phase9_review_location_ids": sorted(
                row["review_location_id"] for row in crossing_sources
            ),
            "phase9_validation": [
                {
                    "event_id": row["event_id"],
                    "review_location_id": row["review_location_id"],
                    "decision": row["navigability_decision"],
                    "evidence_type": row["evidence_type"],
                }
                for row in sorted(crossing_sources, key=lambda item: item["event_id"])
            ],
            "incident_fragment_ids": [],
            "incident_fragment_ends": [],
            "source_shape_ids": [],
            "source_segment_ids": [],
            "zero_chord_source_artifact_involved": any(
                item["zero_chord_source_artifact"] for item in endpoint_sources
            ),
        }

    fragments: list[dict[str, Any]] = []
    source_inventory: list[dict[str, Any]] = []
    fragments_by_segment: dict[str, list[dict[str, Any]]] = defaultdict(list)
    fragment_counter = 0
    for segment in segments:
        junctions = split_records.get(segment["segment_id"], [])
        parameters = [item["parameter"] for item in junctions]
        pieces = split_quadratic_at_parameters(
            segment["p0"],
            segment["p1"],
            segment["p2"],
            parameters,
            parameter_equivalence=ROOT_PARAMETER_EQUIVALENCE,
        )
        if len(pieces) != len(junctions) + 1:
            raise ValueError(f"Unexpected split-piece count for {segment['segment_id']}")
        boundary_locations = [
            location_ids[(float(segment["p0"][0]), float(segment["p0"][1]))],
            *(location_ids[item["coordinate"]] for item in junctions),
            location_ids[(float(segment["p2"][0]), float(segment["p2"][1]))],
        ]
        segment_fragment_ids = []
        for piece_index, piece in enumerate(pieces, start=1):
            fragment_counter += 1
            fragment_id = f"env{environment_id}_topology_fragment_{fragment_counter:05d}"
            start_location_id = boundary_locations[piece_index - 1]
            end_location_id = boundary_locations[piece_index]
            vertices = adaptive_quadratic_bezier_polyline(
                *piece.control_points, CURVE_TOLERANCE
            )
            start_location = locations_by_id[start_location_id]
            end_location = locations_by_id[end_location_id]
            start_residual = endpoint_to_endpoint_distance(
                vertices[0], (start_location["x"], start_location["y"])
            )
            end_residual = endpoint_to_endpoint_distance(
                vertices[-1], (end_location["x"], end_location["y"])
            )
            fragment = {
                "fragment_id": fragment_id,
                "environment_id": environment_id,
                "start_topology_location_id": start_location_id,
                "end_topology_location_id": end_location_id,
                "source_shape_id": segment["shape_id"],
                "source_segment_id": segment["segment_id"],
                "source_segment_index": segment["segment_index"],
                "source_original_world_control_points": {
                    "p0": segment["p0"].tolist(),
                    "p1": segment["p1"].tolist(),
                    "p2": segment["p2"].tolist(),
                },
                "split_subcurve_control_points": {
                    "p0": piece.control_points[0].tolist(),
                    "p1": piece.control_points[1].tolist(),
                    "p2": piece.control_points[2].tolist(),
                },
                "original_t_interval": [piece.original_t_start, piece.original_t_end],
                "adaptive_detailed_xy_geometry": vertices.tolist(),
                "length_unity_world_units": polyline_length(vertices),
                "curve_discretization_tolerance_unity_world_units": CURVE_TOLERANCE,
                "zero_chord_source_artifact": segment["zero_chord_source_artifact"],
                "self_loop_like": start_location_id == end_location_id,
                "snapping_involvement": False,
                "validated_crossing_involvement": bool(
                    start_location["phase8_event_ids"] or end_location["phase8_event_ids"]
                ),
                "start_analytic_residual_to_topology_location": start_residual,
                "end_analytic_residual_to_topology_location": end_residual,
            }
            fragments.append(fragment)
            fragments_by_segment[segment["segment_id"]].append(fragment)
            segment_fragment_ids.append(fragment_id)
            for side, location in (("start", start_location), ("end", end_location)):
                location["incident_fragment_ids"].append(fragment_id)
                location["incident_fragment_ends"].append(
                    {"fragment_id": fragment_id, "fragment_side": side}
                )
                location["source_shape_ids"].append(segment["shape_id"])
                location["source_segment_ids"].append(segment["segment_id"])
                if segment["zero_chord_source_artifact"]:
                    location["zero_chord_source_artifact_involved"] = True
        source_inventory.append(
            {
                "source_segment_id": segment["segment_id"],
                "source_shape_id": segment["shape_id"],
                "zero_chord_source_artifact": segment["zero_chord_source_artifact"],
                "split_parameters_original_t": parameters,
                "split_event_ids": [item["event_id"] for item in junctions],
                "fragment_ids": segment_fragment_ids,
            }
        )

    locations = list(locations_by_id.values())
    for location in locations:
        location["incident_fragment_ids"] = sorted(set(location["incident_fragment_ids"]))
        location["source_shape_ids"] = sorted(set(location["source_shape_ids"]))
        location["source_segment_ids"] = sorted(set(location["source_segment_ids"]))
        incident_count = len(location["incident_fragment_ids"])
        location["incident_fragment_count"] = incident_count
        location["incident_fragment_end_count"] = len(location["incident_fragment_ends"])
        if location["phase8_event_ids"]:
            location["qa_role"] = "validated_interior_junction"
        elif incident_count <= 1:
            location["qa_role"] = "dead_end_or_self_loop_artifact"
        elif incident_count == 2:
            location["qa_role"] = "source_geometry_continuation"
        else:
            location["qa_role"] = "authored_exact_branch"

    components = topology_components(locations, fragments)
    incident_counts = Counter(location["incident_fragment_count"] for location in locations)
    validated_locations = [location for location in locations if location["phase8_event_ids"]]
    qa_counts = {
        "exact_topology_location_count": len(locations),
        "detailed_split_fragment_count": len(fragments),
        "locations_with_one_incident_fragment": incident_counts[1],
        "locations_with_two_incident_fragments": incident_counts[2],
        "locations_with_three_or_more_incident_fragments": sum(
            count for degree, count in incident_counts.items() if degree >= 3
        ),
        "validated_interior_junction_count": len(validated_locations),
        "zero_chord_source_segment_count": sum(
            segment["zero_chord_source_artifact"] for segment in segments
        ),
        "zero_chord_self_loop_like_fragment_count": sum(
            fragment["zero_chord_source_artifact"] and fragment["self_loop_like"]
            for fragment in fragments
        ),
        "self_loop_like_fragment_count": sum(fragment["self_loop_like"] for fragment in fragments),
        "connected_component_count": len(components.groups()),
    }
    payload = {
        "topology_schema_version": "1.0.0",
        "phase10_analysis_version": "1.0.0",
        "topology_variant": "exact_zero_snapping_baseline",
        "environment_id": environment_id,
        "coordinate_space": "Unity world XY",
        "units": "Unity world units",
        "meter_scale_verified": False,
        "crs": None,
        "source_file": f"data/raw/env{environment_id}_bezier.json",
        "source_file_sha256": RAW_HASHES[environment_id],
        "source_bezier_count": len(segments),
        "phase9_validation_path": "outputs/qa/phase9-3d-navigability-validation.json",
        "phase9_validation_sha256": sha256(PHASE9_JSON),
        "phase9_acceptance_status": phase9["acceptance_status"],
        "validated_interior_crossing_count": len(environment_decisions),
        "curve_discretization": {
            "method": "Phase 7 recursive quadratic de Casteljau subdivision",
            "absolute_tolerance_unity_world_units": CURVE_TOLERANCE,
            "not_a_snapping_tolerance": True,
        },
        "snapping_policy": {
            "relative_tolerance": 0.0,
            "absolute_tolerance_unity_world_units": 0.0,
            "snapping_performed": False,
        },
        "locations": sorted(locations, key=lambda item: item["topology_location_id"]),
        "fragments": fragments,
        "source_segment_inventory": source_inventory,
        "qa_counts": qa_counts,
        "networkx_graph_created": False,
        "osmnx_graph_created": False,
        "final_morphology_metrics_calculated": False,
    }
    context = {
        "segments": segments,
        "segment_by_id": segment_by_id,
        "endpoints": endpoints,
        "endpoint_groups": endpoint_groups,
        "location_ids": location_ids,
        "locations_by_id": locations_by_id,
        "fragments_by_segment": dict(fragments_by_segment),
        "components": components,
    }
    return payload, context


def first_tolerance(distance: float) -> tuple[float | None, float | None]:
    for relative, absolute in zip(RELATIVE_TOLERANCES[1:], ABSOLUTE_TOLERANCES[1:], strict=True):
        if distance <= absolute:
            return relative, absolute
    return None, None


def audit_near_misses(
    environment_id: int, context: dict[str, Any]
) -> list[dict[str, Any]]:
    maximum_distance = ABSOLUTE_TOLERANCES[-1]
    groups = context["endpoint_groups"]
    location_ids = context["location_ids"]
    locations_by_id = context["locations_by_id"]
    segment_by_id = context["segment_by_id"]
    candidates: list[dict[str, Any]] = []
    coordinates = sorted(groups)

    for first_index, first_coordinate in enumerate(coordinates):
        first_records = groups[first_coordinate]
        first_location_id = location_ids[first_coordinate]
        for second_coordinate in coordinates[first_index + 1 :]:
            distance = endpoint_to_endpoint_distance(first_coordinate, second_coordinate)
            if distance == 0.0 or distance > maximum_distance:
                continue
            second_records = groups[second_coordinate]
            second_location_id = location_ids[second_coordinate]
            relative, absolute = first_tolerance(distance)
            source_record = first_records[0]
            target_record = second_records[0]
            candidates.append(
                {
                    "environment_id": environment_id,
                    "candidate_type": "endpoint_endpoint",
                    "source_endpoint_id": source_record["endpoint_id"],
                    "target_endpoint_or_segment_id": target_record["endpoint_id"],
                    "source_shape_id": source_record["shape_id"],
                    "target_shape_id": target_record["shape_id"],
                    "distance": distance,
                    "closest_t_if_applicable": None,
                    "closest_x": second_coordinate[0],
                    "closest_y": second_coordinate[1],
                    "already_connected": False,
                    "source_anomaly_involved": any(
                        record["zero_chord_source_artifact"]
                        for record in (*first_records, *second_records)
                    ),
                    "ambiguous": False,
                    "first_candidate_relative_tolerance": relative,
                    "first_candidate_absolute_tolerance": absolute,
                    "review_notes": "",
                    "source_endpoint_location_id": first_location_id,
                    "target_endpoint_location_id": second_location_id,
                    "target_key": second_location_id,
                    "source_endpoint_all_ids": [record["endpoint_id"] for record in first_records],
                    "target_endpoint_all_ids": [record["endpoint_id"] for record in second_records],
                    "source_endpoint_already_confirmed_junction": (
                        locations_by_id[first_location_id]["incident_fragment_count"] >= 3
                    ),
                    "target_endpoint_already_confirmed_junction": (
                        locations_by_id[second_location_id]["incident_fragment_count"] >= 3
                    ),
                }
            )

    for coordinate in coordinates:
        source_records = groups[coordinate]
        source_location_id = location_ids[coordinate]
        incident_segment_ids = {record["segment_id"] for record in source_records}
        for segment_id, segment in segment_by_id.items():
            if segment_id in incident_segment_ids:
                continue
            nearest = nearest_point_on_quadratic(
                coordinate, segment["p0"], segment["p1"], segment["p2"]
            )
            if (
                nearest.distance == 0.0
                or nearest.distance > maximum_distance
                or not nearest.strictly_interior
            ):
                continue
            relative, absolute = first_tolerance(nearest.distance)
            source_record = source_records[0]
            target_key = f"{segment_id}@{nearest.parameter:.17g}"
            candidates.append(
                {
                    "environment_id": environment_id,
                    "candidate_type": "endpoint_interior",
                    "source_endpoint_id": source_record["endpoint_id"],
                    "target_endpoint_or_segment_id": segment_id,
                    "source_shape_id": source_record["shape_id"],
                    "target_shape_id": segment["shape_id"],
                    "distance": nearest.distance,
                    "closest_t_if_applicable": nearest.parameter,
                    "closest_x": float(nearest.point[0]),
                    "closest_y": float(nearest.point[1]),
                    "already_connected": False,
                    "source_anomaly_involved": any(
                        record["zero_chord_source_artifact"] for record in source_records
                    )
                    or segment["zero_chord_source_artifact"],
                    "ambiguous": False,
                    "first_candidate_relative_tolerance": relative,
                    "first_candidate_absolute_tolerance": absolute,
                    "review_notes": "",
                    "source_endpoint_location_id": source_location_id,
                    "target_endpoint_location_id": None,
                    "target_key": target_key,
                    "source_endpoint_all_ids": [record["endpoint_id"] for record in source_records],
                    "target_segment_id": segment_id,
                    "source_endpoint_already_confirmed_junction": (
                        locations_by_id[source_location_id]["incident_fragment_count"] >= 3
                    ),
                    "target_point_strictly_inside_bezier": True,
                }
            )

    candidates.sort(
        key=lambda item: (
            item["environment_id"],
            item["candidate_type"],
            item["distance"],
            item["source_endpoint_id"],
            item["target_endpoint_or_segment_id"],
        )
    )
    for index, candidate in enumerate(candidates, start=1):
        candidate["candidate_id"] = f"env{environment_id}_near_miss_{index:04d}"
    endpoint_coordinates = {
        location_ids[coordinate]: coordinate for coordinate in coordinates
    }
    ambiguous = ambiguous_candidate_ids(candidates, endpoint_coordinates, maximum_distance)
    for candidate in candidates:
        candidate["ambiguous"] = candidate["candidate_id"] in ambiguous
    return candidates


def target_fragment_endpoints(
    candidate: dict[str, Any], context: dict[str, Any]
) -> tuple[str, str]:
    parameter = float(candidate["closest_t_if_applicable"])
    fragments = context["fragments_by_segment"][candidate["target_segment_id"]]
    for fragment in fragments:
        start, end = fragment["original_t_interval"]
        if start < parameter < end:
            return (
                fragment["start_topology_location_id"],
                fragment["end_topology_location_id"],
            )
    raise ValueError(f"No target fragment contains {candidate['candidate_id']}")


def sensitivity_rows(
    environment_id: int,
    exact: dict[str, Any],
    context: dict[str, Any],
    candidates: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    endpoint_coordinates = {
        context["location_ids"][coordinate]: coordinate
        for coordinate in context["endpoint_groups"]
    }
    baseline_location_count = exact["qa_counts"]["exact_topology_location_count"]
    baseline_fragment_count = exact["qa_counts"]["detailed_split_fragment_count"]
    baseline_component_count = exact["qa_counts"]["connected_component_count"]
    rows: list[dict[str, Any]] = []
    for relative, absolute in zip(RELATIVE_TOLERANCES, ABSOLUTE_TOLERANCES, strict=True):
        eligible = [candidate for candidate in candidates if candidate["distance"] <= absolute]
        ambiguous_ids = ambiguous_candidate_ids(candidates, endpoint_coordinates, absolute)
        applied = [
            candidate for candidate in eligible if candidate["candidate_id"] not in ambiguous_ids
        ]
        affected_endpoints = set()
        for candidate in eligible:
            affected_endpoints.add(candidate["source_endpoint_location_id"])
            if candidate["candidate_type"] == "endpoint_endpoint":
                affected_endpoints.add(candidate["target_endpoint_location_id"])

        snap_locations = DisjointSet(
            location["topology_location_id"] for location in exact["locations"]
        )
        components = DisjointSet(
            location["topology_location_id"] for location in exact["locations"]
        )
        for fragment in exact["fragments"]:
            components.union(
                fragment["start_topology_location_id"], fragment["end_topology_location_id"]
            )
        unique_interior_targets = set()
        for candidate in applied:
            source_id = candidate["source_endpoint_location_id"]
            if candidate["candidate_type"] == "endpoint_endpoint":
                target_id = candidate["target_endpoint_location_id"]
                snap_locations.union(source_id, target_id)
                components.union(source_id, target_id)
            else:
                virtual_id = f"virtual::{candidate['target_key']}"
                snap_locations.add(virtual_id)
                snap_locations.union(source_id, virtual_id)
                first, second = target_fragment_endpoints(candidate, context)
                components.union(source_id, first)
                components.union(source_id, second)
                unique_interior_targets.add(candidate["target_key"])

        provisional_locations = len(snap_locations.groups())
        provisional_fragments = baseline_fragment_count + len(unique_interior_targets)
        provisional_components = len(components.groups())
        rows.append(
            {
                "environment_id": environment_id,
                "relative_tolerance": relative,
                "absolute_tolerance_unity_world_units": absolute,
                "endpoint_endpoint_candidate_merges": sum(
                    item["candidate_type"] == "endpoint_endpoint" for item in eligible
                ),
                "endpoint_interior_candidate_merges": sum(
                    item["candidate_type"] == "endpoint_interior" for item in eligible
                ),
                "applied_unambiguous_endpoint_endpoint_merges": sum(
                    item["candidate_type"] == "endpoint_endpoint" for item in applied
                ),
                "applied_unambiguous_endpoint_interior_merges": sum(
                    item["candidate_type"] == "endpoint_interior" for item in applied
                ),
                "unique_affected_endpoints": len(affected_endpoints),
                "ambiguous_candidates": len(ambiguous_ids),
                "maximum_proposed_displacement": max(
                    (float(item["distance"]) for item in eligible), default=0.0
                ),
                "resulting_provisional_topology_location_count": provisional_locations,
                "resulting_provisional_fragment_count": provisional_fragments,
                "provisional_connected_component_count": provisional_components,
                "topology_location_change_vs_zero": provisional_locations
                - baseline_location_count,
                "fragment_change_vs_zero": provisional_fragments - baseline_fragment_count,
                "component_change_vs_zero": provisional_components - baseline_component_count,
                "ambiguity_policy": "ambiguous candidates flagged and not provisionally applied",
            }
        )
    return rows


def distance_gap_analysis(candidates: list[dict[str, Any]]) -> dict[str, Any]:
    distances = sorted(float(candidate["distance"]) for candidate in candidates)
    unique_distances = sorted(set(distances))
    ratios = [
        {
            "lower_distance": first,
            "upper_distance": second,
            "ratio": second / first,
        }
        for first, second in zip(unique_distances, unique_distances[1:], strict=False)
        if first > 0.0
    ]
    largest = max(ratios, key=lambda item: item["ratio"], default=None)
    natural_gap = bool(largest and largest["ratio"] >= 10.0)
    return {
        "candidate_count": len(candidates),
        "sorted_distances_unity_world_units": distances,
        "unique_sorted_distances_unity_world_units": unique_distances,
        "minimum_positive_distance_unity_world_units": min(distances, default=None),
        "maximum_candidate_distance_unity_world_units": max(distances, default=None),
        "largest_adjacent_distance_ratio": largest,
        "natural_gap_found": natural_gap,
        "natural_gap_rule": (
            "An adjacent positive-distance ratio of at least 10 is reported as an observable "
            "order-of-magnitude gap; this diagnostic alone does not prove intended connectivity."
        ),
    }


NEAR_MISS_FIELDS = [
    "candidate_id",
    "environment_id",
    "candidate_type",
    "source_endpoint_id",
    "target_endpoint_or_segment_id",
    "source_shape_id",
    "target_shape_id",
    "distance",
    "closest_t_if_applicable",
    "closest_x",
    "closest_y",
    "already_connected",
    "source_anomaly_involved",
    "ambiguous",
    "first_candidate_relative_tolerance",
    "first_candidate_absolute_tolerance",
    "review_notes",
]


def write_near_miss_table(candidates: list[dict[str, Any]]) -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    with (TABLES / "phase10-near-miss-candidates.csv").open(
        "w", encoding="utf-8", newline=""
    ) as destination:
        writer = csv.DictWriter(destination, fieldnames=NEAR_MISS_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(candidates)


def write_sensitivity_table(rows: list[dict[str, Any]]) -> None:
    with (TABLES / "phase10-snapping-sensitivity.csv").open(
        "w", encoding="utf-8", newline=""
    ) as destination:
        writer = csv.DictWriter(destination, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def validate_topology(payload: dict[str, Any], expected_crossings: int) -> None:
    locations = payload["locations"]
    fragments = payload["fragments"]
    location_ids = [item["topology_location_id"] for item in locations]
    fragment_ids = [item["fragment_id"] for item in fragments]
    if len(location_ids) != len(set(location_ids)):
        raise ValueError("Duplicate topology-location IDs")
    if len(fragment_ids) != len(set(fragment_ids)):
        raise ValueError("Duplicate topology-fragment IDs")
    location_set = set(location_ids)
    for fragment in fragments:
        if fragment["start_topology_location_id"] not in location_set or fragment[
            "end_topology_location_id"
        ] not in location_set:
            raise ValueError(f"Fragment endpoint lacks a topology location: {fragment['fragment_id']}")
        interval = fragment["original_t_interval"]
        if not 0.0 <= interval[0] < interval[1] <= 1.0:
            raise ValueError(f"Invalid source t interval: {fragment['fragment_id']}")
        geometry = np.asarray(fragment["adaptive_detailed_xy_geometry"], dtype=np.float64)
        if geometry.ndim != 2 or geometry.shape[1] != 2 or not np.all(np.isfinite(geometry)):
            raise ValueError(f"Non-finite fragment geometry: {fragment['fragment_id']}")
    validated_event_ids = {
        event_id for location in locations for event_id in location["phase8_event_ids"]
    }
    if len(validated_event_ids) != expected_crossings:
        raise ValueError("Not every validated Phase 9 crossing is represented")
    inventory = payload["source_segment_inventory"]
    if len(inventory) != payload["source_bezier_count"]:
        raise ValueError("A source Bezier disappeared from the topology inventory")
    for source_segment in inventory:
        intervals = [
            fragment["original_t_interval"]
            for fragment in fragments
            if fragment["source_segment_id"] == source_segment["source_segment_id"]
        ]
        if not intervals or intervals[0][0] != 0.0 or intervals[-1][1] != 1.0:
            raise ValueError(f"Incomplete source coverage: {source_segment['source_segment_id']}")
        for first, second in zip(intervals, intervals[1:], strict=False):
            if first[1] != second[0]:
                raise ValueError(f"Unordered/gapped split intervals: {source_segment['source_segment_id']}")


def selected_zero_topology(exact: dict[str, Any]) -> dict[str, Any]:
    selected = deepcopy(exact)
    selected["topology_variant"] = "selected_canonical_topology"
    selected["canonical_snapping_selection"] = {
        "relative_tolerance": 0.0,
        "absolute_tolerance_unity_world_units": 0.0,
        "snapping_performed": False,
        "affected_topology_location_count": 0,
        "maximum_displacement_unity_world_units": 0.0,
        "reason": (
            "Zero snapping retained because the combined endpoint-based candidate distances "
            "do not form one unambiguous extremely-close class clearly separated from larger "
            "gaps across both environments. Proximity alone does not prove intended connection."
        ),
    }
    selected["snapping_policy"] = {
        "relative_tolerance": 0.0,
        "absolute_tolerance_unity_world_units": 0.0,
        "snapping_performed": False,
    }
    return selected


def plot_topology(environment_id: int, payload: dict[str, Any]) -> None:
    figure, axis = plt.subplots(figsize=(10, 10))
    for fragment in payload["fragments"]:
        geometry = np.asarray(fragment["adaptive_detailed_xy_geometry"])
        axis.plot(geometry[:, 0], geometry[:, 1], color="#9b9b9b", linewidth=1.0, zorder=1)
    endpoints = [
        location for location in payload["locations"] if location["authored_endpoint_sources"]
    ]
    crossings = [
        location for location in payload["locations"] if location["phase8_event_ids"]
    ]
    anomalies = [
        location
        for location in payload["locations"]
        if location["zero_chord_source_artifact_involved"]
    ]
    axis.scatter(
        [item["x"] for item in endpoints],
        [item["y"] for item in endpoints],
        s=16,
        marker="o",
        facecolors="white",
        edgecolors="#2563eb",
        linewidths=0.8,
        label=f"authored exact endpoint locations ({len(endpoints)})",
        zorder=3,
    )
    axis.scatter(
        [item["x"] for item in crossings],
        [item["y"] for item in crossings],
        s=38,
        marker="x",
        color="#15803d",
        linewidths=1.3,
        label=f"Phase-9 validated interior junctions ({len(crossings)})",
        zorder=4,
    )
    if anomalies:
        axis.scatter(
            [item["x"] for item in anomalies],
            [item["y"] for item in anomalies],
            s=40,
            marker="^",
            color="#dc2626",
            label=f"zero-chord artifact locations ({len(anomalies)})",
            zorder=5,
        )
    axis.set_title(f"Environment {environment_id}: Phase 10 selected topology (zero snapping)")
    axis.set_xlabel("Unity world X")
    axis.set_ylabel("Unity world Y")
    axis.set_aspect("equal", adjustable="box")
    axis.legend(loc="best", fontsize=8)
    figure.tight_layout()
    figure.savefig(QA / f"env{environment_id}-phase10-topology.png", dpi=190, bbox_inches="tight")
    plt.close(figure)


def plot_near_misses(
    environment_id: int,
    exact: dict[str, Any],
    context: dict[str, Any],
    candidates: list[dict[str, Any]],
) -> None:
    figure, axis = plt.subplots(figsize=(10, 10))
    for fragment in exact["fragments"]:
        geometry = np.asarray(fragment["adaptive_detailed_xy_geometry"])
        axis.plot(geometry[:, 0], geometry[:, 1], color="#b0b0b0", linewidth=0.9, zorder=1)
    for candidate in candidates:
        source = context["locations_by_id"][candidate["source_endpoint_location_id"]]
        color = "#dc2626" if candidate["ambiguous"] else "#f59e0b"
        axis.plot(
            [source["x"], candidate["closest_x"]],
            [source["y"], candidate["closest_y"]],
            color=color,
            linewidth=1.1,
            linestyle="--",
            zorder=3,
        )
        axis.scatter([source["x"]], [source["y"]], color=color, s=22, zorder=4)
    ambiguous_count = sum(candidate["ambiguous"] for candidate in candidates)
    axis.plot([], [], color="#f59e0b", linestyle="--", label="unambiguous candidate")
    axis.plot(
        [], [], color="#dc2626", linestyle="--", label=f"ambiguous candidate ({ambiguous_count})"
    )
    axis.set_title(
        f"Environment {environment_id}: endpoint-based near misses within "
        f"{ABSOLUTE_TOLERANCES[-1]:.6g} Unity units"
    )
    axis.set_xlabel("Unity world X")
    axis.set_ylabel("Unity world Y")
    axis.set_aspect("equal", adjustable="box")
    axis.legend(loc="best", fontsize=8)
    figure.tight_layout()
    figure.savefig(QA / f"env{environment_id}-phase10-near-misses.png", dpi=190, bbox_inches="tight")
    plt.close(figure)


def plot_distance_distribution(candidates: list[dict[str, Any]]) -> None:
    ordered = sorted(candidates, key=lambda item: item["distance"])
    figure, axis = plt.subplots(figsize=(9, 5.5))
    for environment_id, marker, color in ((38, "o", "#7c3aed"), (39, "s", "#0284c7")):
        indices = [index + 1 for index, item in enumerate(ordered) if item["environment_id"] == environment_id]
        distances = [item["distance"] for item in ordered if item["environment_id"] == environment_id]
        if distances:
            axis.scatter(indices, distances, marker=marker, color=color, label=f"Env{environment_id}")
    axis.set_yscale("log")
    axis.set_xlabel("Candidate rank by ascending distance")
    axis.set_ylabel("Exact nearest distance (Unity world units, log scale)")
    axis.set_title("Phase 10 endpoint-based near-miss distance distribution")
    axis.legend(loc="best")
    axis.grid(axis="y", which="both", alpha=0.25)
    figure.tight_layout()
    figure.savefig(QA / "phase10-near-miss-distance-distribution.png", dpi=190, bbox_inches="tight")
    plt.close(figure)


def main() -> int:
    sources, decisions, phase9 = load_and_verify_inputs()
    PROCESSED.mkdir(parents=True, exist_ok=True)
    TABLES.mkdir(parents=True, exist_ok=True)
    QA.mkdir(parents=True, exist_ok=True)

    exact_by_environment: dict[int, dict[str, Any]] = {}
    selected_by_environment: dict[int, dict[str, Any]] = {}
    contexts: dict[int, dict[str, Any]] = {}
    candidates_by_environment: dict[int, list[dict[str, Any]]] = {}
    sensitivity: list[dict[str, Any]] = []
    gaps: dict[int, dict[str, Any]] = {}
    for environment_id in (38, 39):
        exact, context = build_exact_topology(
            environment_id, sources[environment_id], decisions, phase9
        )
        validate_topology(exact, 28 if environment_id == 38 else 20)
        candidates = audit_near_misses(environment_id, context)
        rows = sensitivity_rows(environment_id, exact, context, candidates)
        selected = selected_zero_topology(exact)
        validate_topology(selected, 28 if environment_id == 38 else 20)

        exact_by_environment[environment_id] = exact
        selected_by_environment[environment_id] = selected
        contexts[environment_id] = context
        candidates_by_environment[environment_id] = candidates
        sensitivity.extend(rows)
        gaps[environment_id] = distance_gap_analysis(candidates)

        write_json(PROCESSED / f"env{environment_id}_topology_exact.json", exact)
        write_json(PROCESSED / f"env{environment_id}_topology.json", selected)
        plot_topology(environment_id, selected)
        if candidates:
            plot_near_misses(environment_id, exact, context, candidates)

    all_candidates = [
        candidate
        for environment_id in (38, 39)
        for candidate in candidates_by_environment[environment_id]
    ]
    write_near_miss_table(all_candidates)
    write_sensitivity_table(sensitivity)
    plot_distance_distribution(all_candidates)

    overall_gap = distance_gap_analysis(all_candidates)
    maximum_ambiguity = max(row["ambiguous_candidates"] for row in sensitivity)
    sensitivity_payload = {
        "phase10_snapping_sensitivity_schema_version": "1.0.0",
        "phase10_analysis_version": "1.0.0",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "coordinate_space": "Unity world XY",
        "units": "Unity world units",
        "meter_scale_verified": False,
        "crs": None,
        "source_hashes": {str(key): value for key, value in RAW_HASHES.items()},
        "phase9_validation": {
            "path": "outputs/qa/phase9-3d-navigability-validation.json",
            "sha256": sha256(PHASE9_JSON),
            "acceptance_status": phase9["acceptance_status"],
            "connected_same_level": phase9["counts"]["connected_same_level"],
            "grade_separated_not_connected": phase9["counts"][
                "grade_separated_not_connected"
            ],
            "manual_review_required": phase9["counts"]["manual_review_required"],
        },
        "curve_discretization_tolerance_unity_world_units": CURVE_TOLERANCE,
        "curve_discretization_tolerance_is_not_snapping_tolerance": True,
        "phase8_numerical_root_tolerance_is_not_snapping_tolerance": True,
        "common_reference_scale_unity_world_units": REFERENCE_SCALE,
        "predefined_tolerance_series": [
            {
                "relative_tolerance": relative,
                "absolute_tolerance_unity_world_units": absolute,
            }
            for relative, absolute in zip(
                RELATIVE_TOLERANCES, ABSOLUTE_TOLERANCES, strict=True
            )
        ],
        "exact_topology_qa": {
            str(environment_id): exact_by_environment[environment_id]["qa_counts"]
            for environment_id in (38, 39)
        },
        "near_miss_counts": {
            str(environment_id): {
                "endpoint_endpoint": sum(
                    item["candidate_type"] == "endpoint_endpoint"
                    for item in candidates_by_environment[environment_id]
                ),
                "endpoint_interior": sum(
                    item["candidate_type"] == "endpoint_interior"
                    for item in candidates_by_environment[environment_id]
                ),
                "ambiguous_at_maximum_tolerance": sum(
                    item["ambiguous"] for item in candidates_by_environment[environment_id]
                ),
            }
            for environment_id in (38, 39)
        },
        "distance_gap_analysis": {
            "by_environment": {str(key): value for key, value in gaps.items()},
            "combined": overall_gap,
            "interpretation": (
                "Env38 has one local order-of-magnitude adjacent gap, but Env39 and the "
                "combined candidate inventory do not show one consistent clearly separated "
                "extremely-close class. No natural global snapping class is established."
            ),
        },
        "ambiguity_safeguards": {
            "maximum_ambiguous_candidate_count": maximum_ambiguity,
            "ambiguous_candidates_are_not_provisionally_applied": True,
            "checks": [
                "endpoint with multiple possible targets",
                "transitive endpoint cluster diameter exceeds tolerance",
                "endpoint-to-endpoint versus endpoint-to-interior conflict",
                "zero-chord anomaly involvement",
                "closer competing feature before a proposed target",
            ],
        },
        "sensitivity_rows": sensitivity,
        "canonical_snapping_selection": {
            "relative_tolerance": 0.0,
            "absolute_tolerance_unity_world_units": 0.0,
            "affected_topology_location_count": 0,
            "maximum_displacement_unity_world_units": 0.0,
            "natural_global_distance_gap_found": overall_gap["natural_gap_found"],
            "reason": selected_by_environment[38]["canonical_snapping_selection"]["reason"],
        },
        "manual_topology_review_required": False,
        "manual_review_rationale": (
            "No candidate is classified as a likely intended connection from geometry alone. "
            "Near misses remain documented for sensitivity interpretation; zero snapping avoids "
            "guessing or arbitrary conflict resolution."
        ),
        "phase10_acceptance_status": "PASS",
        "networkx_graph_created": False,
        "osmnx_graph_created": False,
        "final_morphology_metrics_calculated": False,
        "software_versions": {
            "python": platform.python_version(),
            "numpy": importlib.metadata.version("numpy"),
            "scipy": importlib.metadata.version("scipy"),
            "matplotlib": importlib.metadata.version("matplotlib"),
        },
    }
    write_json(QA / "phase10-snapping-sensitivity.json", sensitivity_payload)

    print("Canonical raw SHA-256 verification: PASS")
    print("Phase 9 validation: 48 connected / 0 grade-separated / 0 manual: PASS")
    for environment_id in (38, 39):
        print(f"Env{environment_id} exact QA: {exact_by_environment[environment_id]['qa_counts']}")
        print(
            f"Env{environment_id} near misses: "
            f"{Counter(item['candidate_type'] for item in candidates_by_environment[environment_id])}"
        )
    print("Canonical snapping tolerance: relative=0, absolute=0 Unity world units")
    print("Manual topology review required: no")
    print("Phase 10: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
