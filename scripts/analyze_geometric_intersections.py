"""Phase 8 geometric intersection inventory and exact Bézier refinement.

No snapping, topology, graph construction, CRS assignment, unit conversion, or
final morphology metric calculation is performed here.
"""

from __future__ import annotations

import csv
import hashlib
import importlib.metadata
import itertools
import json
import math
import os
import platform
import tempfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import numpy as np
from shapely.geometry import GeometryCollection, LineString, MultiLineString, MultiPoint, Point

os.environ.setdefault(
    "MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "geogami-morphology-matplotlib")
)
import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from bezier_geometry import (
    adaptive_quadratic_bezier_samples,
    quadratic_bezier_derivative,
    quadratic_bezier_point,
)
from bezier_intersections import (
    algebraic_quadratic_bezier_intersections,
    analytic_quadratic_bounds,
    bounds_overlap,
    coincident_overlap_evidence,
    cross_2d,
    refine_intersection_seeds,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
RAW_DIRECTORY = REPOSITORY_ROOT / "data" / "raw"
PROCESSED_DIRECTORY = REPOSITORY_ROOT / "data" / "processed"
QA_DIRECTORY = REPOSITORY_ROOT / "outputs" / "qa"
TABLE_DIRECTORY = REPOSITORY_ROOT / "outputs" / "tables"

ANALYSIS_VERSION = "1.0.0"
COMMON_REFERENCE_SCALE = 701.656542085319
PHASE7_RELATIVE_TOLERANCE = 2e-4
PHASE7_ABSOLUTE_TOLERANCE = 0.1403313084170638
NUMERICAL_RESIDUAL_RELATIVE = 1e-10
NUMERICAL_RESIDUAL_TOLERANCE = COMMON_REFERENCE_SCALE * NUMERICAL_RESIDUAL_RELATIVE
ROOT_PARAMETER_EQUIVALENCE = 2e-5
ANOMALY_ENDPOINT_PARAMETER_EQUIVALENCE = 1e-3
TANGENT_SINE_THRESHOLD = 1e-4

SOURCE_CONFIG = {
    38: {
        "filename": "env38_bezier.json",
        "sha256": "43ea446a4a88e9f3d594fb8b72742f5d4b2a1ee8a03ebf8350c4c3cce45c5819",
        "total_segments": 120,
        "shape_counts": [4, 32, 32, 24, 28],
    },
    39: {
        "filename": "env39_bezier.json",
        "sha256": "e5dbce6b4d88656c9e0f3bbf6a814434f64b0fbe9b3ff1864ea3fafaf0883602",
        "total_segments": 32,
        "shape_counts": [32],
    },
}

KNOWN_ZERO_CHORD_ANOMALIES = {
    "env38_shape_4330855547529842337_segment_0006",
    "env38_shape_4330855547529842337_segment_0019",
    "env38_shape_4330855547829185599_segment_0007",
    "env38_shape_4330855547829185599_segment_0011",
    "env38_shape_4330855547829185599_segment_0012",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def world_xy(point: dict[str, Any]) -> np.ndarray:
    result = np.array([point["x"], point["y"]], dtype=np.float64)
    if not np.all(np.isfinite(result)):
        raise ValueError(f"Non-finite world coordinate: {point}")
    return result


def load_inputs() -> tuple[dict[int, dict[str, Any]], dict[int, str], dict[str, Any]]:
    sources: dict[int, dict[str, Any]] = {}
    hashes: dict[int, str] = {}
    for environment_id, config in SOURCE_CONFIG.items():
        path = RAW_DIRECTORY / config["filename"]
        actual_hash = sha256_file(path)
        if actual_hash != config["sha256"]:
            raise RuntimeError(
                f"Canonical raw hash mismatch for {path}: {actual_hash}; "
                f"expected {config['sha256']}"
            )
        source = json.loads(path.read_text(encoding="utf-8"))
        if source.get("schema_version") != "1.0.0":
            raise ValueError(f"Unexpected source schema in {path}")
        if source.get("total_segment_count") != config["total_segments"]:
            raise ValueError(f"Unexpected source segment count in {path}")
        if [shape["segment_count"] for shape in source["shapes"]] != config["shape_counts"]:
            raise ValueError(f"Unexpected ordered Shape counts in {path}")
        sources[environment_id] = source
        hashes[environment_id] = actual_hash

    selection_path = QA_DIRECTORY / "phase7-selected-discretization.json"
    selection = json.loads(selection_path.read_text(encoding="utf-8"))
    if not math.isclose(
        selection["selected_relative_tolerance"], PHASE7_RELATIVE_TOLERANCE,
        rel_tol=0.0, abs_tol=1e-15,
    ):
        raise ValueError("Unexpected Phase 7 relative tolerance")
    if not math.isclose(
        selection["selected_absolute_tolerance_unity_world_units"],
        PHASE7_ABSOLUTE_TOLERANCE,
        rel_tol=0.0, abs_tol=1e-12,
    ):
        raise ValueError("Unexpected Phase 7 absolute tolerance")
    if not math.isclose(
        selection["common_reference_scale_unity_world_units"], COMMON_REFERENCE_SCALE,
        rel_tol=0.0, abs_tol=1e-12,
    ):
        raise ValueError("Unexpected Phase 7 common reference scale")
    if selection["source_hashes"] != {str(key): value for key, value in hashes.items()}:
        raise ValueError("Phase 7 source-hash provenance mismatch")

    for environment_id, config in SOURCE_CONFIG.items():
        detailed_path = PROCESSED_DIRECTORY / f"env{environment_id}_detailed_linework.json"
        detailed = json.loads(detailed_path.read_text(encoding="utf-8"))
        if detailed["source_file_sha256"] != hashes[environment_id]:
            raise ValueError(f"Detailed linework hash provenance mismatch for Env{environment_id}")
        if detailed["source_bezier_record_count"] != config["total_segments"]:
            raise ValueError(f"Detailed linework count mismatch for Env{environment_id}")
        if not math.isclose(
            detailed["selected_absolute_tolerance_unity_world_units"],
            PHASE7_ABSOLUTE_TOLERANCE,
            rel_tol=0.0, abs_tol=1e-12,
        ):
            raise ValueError(f"Detailed linework tolerance mismatch for Env{environment_id}")
    return sources, hashes, selection


def segment_records(source: dict[str, Any]) -> list[dict[str, Any]]:
    records = []
    for shape in source["shapes"]:
        for segment in shape["segments"]:
            p0 = world_xy(segment["world"]["p0"])
            p1 = world_xy(segment["world"]["p1"])
            p2 = world_xy(segment["world"]["p2"])
            samples = adaptive_quadratic_bezier_samples(
                p0, p1, p2, PHASE7_ABSOLUTE_TOLERANCE
            )
            records.append(
                {
                    "environment_id": source["environment_id"],
                    "shape_id": shape["shape_id"],
                    "shape_index": shape["shape_index"],
                    "segment_id": segment["segment_id"],
                    "segment_index": segment["segment_index"],
                    "p0": p0,
                    "p1": p1,
                    "p2": p2,
                    "curve": (p0, p1, p2),
                    "bounds": analytic_quadratic_bounds((p0, p1, p2)),
                    "samples": samples,
                    "line": LineString(samples[:, 1:]),
                    "source_anomaly": segment["segment_id"] in KNOWN_ZERO_CHORD_ANOMALIES,
                }
            )
    return records


def exact_endpoint_inventory(records: list[dict[str, Any]]) -> dict[str, Any]:
    grouped: defaultdict[tuple[float, float], list[dict[str, str]]] = defaultdict(list)
    for segment in records:
        for side in ("p0", "p2"):
            point = segment[side]
            grouped[(float(point[0]), float(point[1]))].append(
                {
                    "segment_id": segment["segment_id"],
                    "endpoint_side": side,
                    "shape_id": segment["shape_id"],
                }
            )
    groups = []
    pairwise_relationships = []
    for coordinate, references in sorted(grouped.items()):
        distinct_segments = sorted({reference["segment_id"] for reference in references})
        if len(distinct_segments) < 2:
            continue
        groups.append(
            {
                "coordinate_xy": list(coordinate),
                "involved_segment_ids": distinct_segments,
                "references": references,
            }
        )
        references_by_segment = defaultdict(list)
        for reference in references:
            references_by_segment[reference["segment_id"]].append(reference)
        for first_id, second_id in itertools.combinations(distinct_segments, 2):
            pairwise_relationships.append(
                {
                    "coordinate_xy": list(coordinate),
                    "segment_a_id": first_id,
                    "segment_b_id": second_id,
                    "segment_a_references": references_by_segment[first_id],
                    "segment_b_references": references_by_segment[second_id],
                }
            )
    return {
        "distinct_shared_exact_endpoint_positions": len(groups),
        "pairwise_exact_endpoint_relationship_count": len(pairwise_relationships),
        "groups": groups,
        "pairwise_relationships": pairwise_relationships,
    }


def geometry_points_and_overlap(geometry: Any) -> tuple[list[np.ndarray], list[dict[str, Any]]]:
    points: list[np.ndarray] = []
    overlaps: list[dict[str, Any]] = []
    if geometry.is_empty:
        return points, overlaps
    if isinstance(geometry, Point):
        points.append(np.array(geometry.coords[0], dtype=np.float64))
    elif isinstance(geometry, MultiPoint):
        for item in geometry.geoms:
            child_points, child_overlaps = geometry_points_and_overlap(item)
            points.extend(child_points)
            overlaps.extend(child_overlaps)
    elif isinstance(geometry, (LineString, MultiLineString)):
        lines = [geometry] if isinstance(geometry, LineString) else list(geometry.geoms)
        for line in lines:
            overlaps.append(
                {
                    "geometry_type": line.geom_type,
                    "length": float(line.length),
                    "coordinates": [list(coordinate) for coordinate in line.coords],
                }
            )
    elif isinstance(geometry, GeometryCollection):
        for item in geometry.geoms:
            child_points, child_overlaps = geometry_points_and_overlap(item)
            points.extend(child_points)
            overlaps.extend(child_overlaps)
    else:
        overlaps.append({"geometry_type": geometry.geom_type, "wkt": geometry.wkt})
    return points, overlaps


def nearest_sample_parameter(samples: np.ndarray, point: np.ndarray) -> float:
    best_distance = math.inf
    best_parameter = 0.0
    for first, second in zip(samples[:-1], samples[1:], strict=True):
        vector = second[1:] - first[1:]
        denominator = float(np.dot(vector, vector))
        fraction = (
            float(np.clip(np.dot(point - first[1:], vector) / denominator, 0.0, 1.0))
            if denominator > 0.0
            else 0.0
        )
        projected = first[1:] + fraction * vector
        distance = float(np.linalg.norm(projected - point))
        if distance < best_distance:
            best_distance = distance
            best_parameter = float(first[0] + fraction * (second[0] - first[0]))
    return best_parameter


def roots_match(first: dict[str, Any], second: dict[str, Any]) -> bool:
    return (
        abs(first["t_a"] - second["t_a"]) <= ROOT_PARAMETER_EQUIVALENCE
        and abs(first["t_b"] - second["t_b"]) <= ROOT_PARAMETER_EQUIVALENCE
    ) or np.linalg.norm(first["point"] - second["point"]) <= NUMERICAL_RESIDUAL_TOLERANCE


def exact_relationships_by_pair(inventory: dict[str, Any]) -> dict[tuple[str, str], list[dict[str, Any]]]:
    result: defaultdict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for relationship in inventory["pairwise_relationships"]:
        pair = tuple(sorted((relationship["segment_a_id"], relationship["segment_b_id"])))
        result[pair].append(relationship)
    return result


def endpoint_side_parameter(side: str) -> float:
    return 0.0 if side == "p0" else 1.0


def classify_root(
    first: dict[str, Any],
    second: dict[str, Any],
    root: dict[str, Any],
    exact_relationships: list[dict[str, Any]],
) -> tuple[str, np.ndarray, float, float, str]:
    point = np.asarray(root["point"], dtype=np.float64)
    for relationship in exact_relationships:
        coordinate = np.asarray(relationship["coordinate_xy"], dtype=np.float64)
        if np.linalg.norm(point - coordinate) <= NUMERICAL_RESIDUAL_TOLERANCE:
            ref_a = relationship["segment_a_references"][0]
            ref_b = relationship["segment_b_references"][0]
            if ref_a["segment_id"] == first["segment_id"]:
                side_a, side_b = ref_a["endpoint_side"], ref_b["endpoint_side"]
            else:
                side_a, side_b = ref_b["endpoint_side"], ref_a["endpoint_side"]
            return (
                "endpoint_endpoint",
                coordinate,
                endpoint_side_parameter(side_a),
                endpoint_side_parameter(side_b),
                "authored_endpoint_connection",
            )

    t_a = float(root["t_a"])
    t_b = float(root["t_b"])
    endpoint_a = next(
        (
            (side, first[side])
            for side in ("p0", "p2")
            if np.linalg.norm(point - first[side]) <= NUMERICAL_RESIDUAL_TOLERANCE
        ),
        None,
    )
    endpoint_b = next(
        (
            (side, second[side])
            for side in ("p0", "p2")
            if np.linalg.norm(point - second[side]) <= NUMERICAL_RESIDUAL_TOLERANCE
        ),
        None,
    )
    if endpoint_a is not None and endpoint_b is None:
        return (
            "endpoint_interior",
            endpoint_a[1],
            endpoint_side_parameter(endpoint_a[0]),
            t_b,
            "requires_3d_review",
        )
    if endpoint_b is not None and endpoint_a is None:
        return (
            "endpoint_interior",
            endpoint_b[1],
            t_a,
            endpoint_side_parameter(endpoint_b[0]),
            "requires_3d_review",
        )
    if endpoint_a is not None and endpoint_b is not None:
        # Distinct authored endpoints within solver precision are not merged.
        return "unresolved_candidate", point, t_a, t_b, "requires_3d_review"

    derivative_a = quadratic_bezier_derivative(*first["curve"], t_a)
    derivative_b = quadratic_bezier_derivative(*second["curve"], t_b)
    derivative_product = float(np.linalg.norm(derivative_a) * np.linalg.norm(derivative_b))
    tangent_sine = (
        abs(cross_2d(derivative_a, derivative_b)) / derivative_product
        if derivative_product > 0.0
        else 0.0
    )
    if tangent_sine <= TANGENT_SINE_THRESHOLD:
        return "tangent_touch", point, t_a, t_b, "requires_3d_review"
    return "interior_interior_crossing", point, t_a, t_b, "requires_3d_review"


def event_record(
    environment_id: int,
    first: dict[str, Any],
    second: dict[str, Any],
    event_type: str,
    point: np.ndarray,
    t_a: float | None,
    t_b: float | None,
    residual: float | None,
    refinement_method: str,
    status: str,
    navigability_status: str,
    evidence: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "environment_id": environment_id,
        "event_id": None,
        "event_type": event_type,
        "x": float(point[0]),
        "y": float(point[1]),
        "segment_a_id": first["segment_id"],
        "segment_b_id": second["segment_id"],
        "shape_a_id": first["shape_id"],
        "shape_b_id": second["shape_id"],
        "t_a": t_a,
        "t_b": t_b,
        "residual": residual,
        "residual_unity_world_units": residual,
        "same_shape": first["shape_id"] == second["shape_id"],
        "source_anomaly_involved": first["source_anomaly"] or second["source_anomaly"],
        "refinement_method": refinement_method,
        "status": status,
        "navigability_status": navigability_status,
        "review_notes": "",
        "evidence": evidence,
    }


def unresolved_from_pair(
    environment_id: int,
    first: dict[str, Any],
    second: dict[str, Any],
    seed: tuple[float, float],
    reason: str,
    evidence: dict[str, Any],
) -> dict[str, Any]:
    point_a = quadratic_bezier_point(*first["curve"], seed[0])
    point_b = quadratic_bezier_point(*second["curve"], seed[1])
    return event_record(
        environment_id,
        first,
        second,
        "unresolved_candidate",
        (point_a + point_b) / 2.0,
        seed[0],
        seed[1],
        float(np.linalg.norm(point_a - point_b)),
        "candidate-method discrepancy",
        "unresolved",
        "requires_3d_review",
        {"reason": reason, **evidence},
    )


def analyze_environment(
    environment_id: int, records: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    endpoint_inventory = exact_endpoint_inventory(records)
    endpoint_pairs = exact_relationships_by_pair(endpoint_inventory)
    events: list[dict[str, Any]] = []
    diagnostics: dict[str, Any] = {
        "total_unique_source_pairs": len(records) * (len(records) - 1) // 2,
        "analytic_bounds_candidate_pairs": 0,
        "phase7_shapely_intersecting_pairs": 0,
        "source_resultant_pairs_with_roots": 0,
        "matched_refined_roots": 0,
        "source_only_refined_roots": 0,
        "shapely_only_refined_roots": 0,
        "shapely_overlap_candidate_pairs": 0,
        "conclusively_rejected_analytic_candidates": 0,
        "anomaly_parameter_roots_consolidated": 0,
        "unresolved_discrepancy_pairs": 0,
    }

    for first, second in itertools.combinations(records, 2):
        if not bounds_overlap(first["bounds"], second["bounds"]):
            continue
        diagnostics["analytic_bounds_candidate_pairs"] += 1
        pair_key = tuple(sorted((first["segment_id"], second["segment_id"])))
        exact_for_pair = endpoint_pairs.get(pair_key, [])

        overlap_evidence = coincident_overlap_evidence(first["curve"], second["curve"])
        shapely_geometry = first["line"].intersection(second["line"])
        shapely_points, shapely_overlaps = geometry_points_and_overlap(shapely_geometry)
        if not shapely_geometry.is_empty:
            diagnostics["phase7_shapely_intersecting_pairs"] += 1
        if shapely_overlaps:
            diagnostics["shapely_overlap_candidate_pairs"] += 1

        if overlap_evidence is not None:
            point = np.asarray(overlap_evidence["representative_point"], dtype=np.float64)
            point_b = quadratic_bezier_point(
                *second["curve"], float(overlap_evidence["t_b"])
            )
            residual = float(np.linalg.norm(point - point_b))
            events.append(
                event_record(
                    environment_id,
                    first,
                    second,
                    "overlap_or_coincident",
                    (point + point_b) / 2.0,
                    float(overlap_evidence["t_a"]),
                    float(overlap_evidence["t_b"]),
                    residual,
                    "exact control/monotone-collinear overlap analysis",
                    "refined",
                    "requires_3d_review",
                    {"source_overlap": overlap_evidence, "phase7_overlap": shapely_overlaps},
                )
            )
            continue
        if shapely_overlaps:
            seed = (
                nearest_sample_parameter(first["samples"], shapely_points[0])
                if shapely_points else 0.5,
                nearest_sample_parameter(second["samples"], shapely_points[0])
                if shapely_points else 0.5,
            )
            events.append(
                unresolved_from_pair(
                    environment_id,
                    first,
                    second,
                    seed,
                    "Phase 7 polylines overlap but source-curve coincidence was not proven",
                    {"phase7_overlap": shapely_overlaps},
                )
            )
            diagnostics["unresolved_discrepancy_pairs"] += 1
            continue

        shapely_seeds = [
            (
                nearest_sample_parameter(first["samples"], point),
                nearest_sample_parameter(second["samples"], point),
            )
            for point in shapely_points
        ]
        shapely_roots, shapely_rejected = refine_intersection_seeds(
            first["curve"], second["curve"], shapely_seeds, NUMERICAL_RESIDUAL_TOLERANCE
        )
        source_result = algebraic_quadratic_bezier_intersections(
            first["curve"], second["curve"], NUMERICAL_RESIDUAL_TOLERANCE
        )
        source_roots = source_result["roots"]
        if source_roots:
            diagnostics["source_resultant_pairs_with_roots"] += 1

        # Prevent zero-chord parameter multiplicity from becoming duplicate geometric events.
        if first["source_anomaly"] or second["source_anomaly"]:
            filtered_roots = []
            for root in source_roots:
                expected_parameter_pairs = []
                for relationship in exact_for_pair:
                    references_a = relationship["segment_a_references"]
                    references_b = relationship["segment_b_references"]
                    if references_a[0]["segment_id"] == first["segment_id"]:
                        first_references, second_references = references_a, references_b
                    else:
                        first_references, second_references = references_b, references_a
                    for first_reference, second_reference in itertools.product(
                        first_references, second_references
                    ):
                        expected_parameter_pairs.append(
                            (
                                endpoint_side_parameter(first_reference["endpoint_side"]),
                                endpoint_side_parameter(second_reference["endpoint_side"]),
                                np.asarray(relationship["coordinate_xy"], dtype=np.float64),
                            )
                        )
                exact_parameter_root = any(
                    root["t_a"] == expected_a and root["t_b"] == expected_b
                    for expected_a, expected_b, _ in expected_parameter_pairs
                )
                near_authored_root = next((
                    (expected_a, expected_b, coordinate)
                    for expected_a, expected_b, coordinate in expected_parameter_pairs
                    if abs(root["t_a"] - expected_a)
                            <= ANOMALY_ENDPOINT_PARAMETER_EQUIVALENCE
                    and abs(root["t_b"] - expected_b)
                    <= ANOMALY_ENDPOINT_PARAMETER_EQUIVALENCE
                ), None)
                if near_authored_root is not None and not exact_parameter_root:
                    diagnostics["anomaly_parameter_roots_consolidated"] += 1
                    canonical_root = dict(root)
                    canonical_root["t_a"] = near_authored_root[0]
                    canonical_root["t_b"] = near_authored_root[1]
                    canonical_root["point"] = near_authored_root[2]
                    canonical_root["residual"] = 0.0
                    canonical_root["solver_message"] = (
                        "canonicalized to independently proven exact authored endpoint root"
                    )
                    filtered_roots.append(canonical_root)
                else:
                    filtered_roots.append(root)
            source_roots = filtered_roots
            consolidated = []
            for root in source_roots:
                duplicate = next(
                    (
                        existing
                        for existing in consolidated
                        if np.linalg.norm(root["point"] - existing["point"])
                        <= NUMERICAL_RESIDUAL_TOLERANCE
                    ),
                    None,
                )
                if duplicate is None:
                    consolidated.append(root)
                else:
                    diagnostics["anomaly_parameter_roots_consolidated"] += 1
                    if root["residual"] < duplicate["residual"]:
                        consolidated[consolidated.index(duplicate)] = root
            source_roots = consolidated

        unmatched_shapely = set(range(len(shapely_roots)))
        unmatched_source = []
        matched = []
        for source_root in source_roots:
            match_index = next(
                (
                    index
                    for index in unmatched_shapely
                    if roots_match(source_root, shapely_roots[index])
                ),
                None,
            )
            if match_index is None:
                unmatched_source.append(source_root)
            else:
                unmatched_shapely.remove(match_index)
                matched.append(source_root)

        diagnostics["matched_refined_roots"] += len(matched)
        diagnostics["source_only_refined_roots"] += len(unmatched_source)
        diagnostics["shapely_only_refined_roots"] += len(unmatched_shapely)

        if unmatched_source or unmatched_shapely or (
            shapely_points and not shapely_roots and not source_roots
        ):
            diagnostics["unresolved_discrepancy_pairs"] += 1
            discrepancy_roots = unmatched_source + [
                shapely_roots[index] for index in sorted(unmatched_shapely)
            ]
            if discrepancy_roots:
                for root in discrepancy_roots:
                    events.append(
                        unresolved_from_pair(
                            environment_id,
                            first,
                            second,
                            (float(root["t_a"]), float(root["t_b"])),
                            "refined root was not independently matched by both candidate methods",
                            {
                                "source_root_present": root in unmatched_source,
                                "phase7_root_present": root not in unmatched_source,
                                "shapely_rejected_attempts": shapely_rejected,
                                "source_rejected_attempt_count": len(source_result["rejected_attempts"]),
                            },
                        )
                    )
            else:
                events.append(
                    unresolved_from_pair(
                        environment_id,
                        first,
                        second,
                        shapely_seeds[0],
                        "Phase 7 candidate could not be refined or independently reproduced",
                        {"shapely_rejected_attempts": shapely_rejected},
                    )
                )

        for root in matched:
            event_type, point, t_a, t_b, navigability = classify_root(
                first, second, root, exact_for_pair
            )
            events.append(
                event_record(
                    environment_id,
                    first,
                    second,
                    event_type,
                    point,
                    t_a,
                    t_b,
                    float(root["residual"]),
                    "Phase 7 Shapely seed + bounded SciPy refinement; independent source-equation resultant confirmation",
                    "refined" if event_type != "unresolved_candidate" else "unresolved",
                    navigability,
                    {
                        "source_resultant_diagnostics": source_result["diagnostics"],
                        "tangent_sine": root.get("tangent_sine"),
                    },
                )
            )

        if not (
            matched
            or unmatched_source
            or unmatched_shapely
            or shapely_points
            or shapely_overlaps
        ):
            diagnostics["conclusively_rejected_analytic_candidates"] += 1

    events.sort(
        key=lambda event: (
            event["segment_a_id"],
            event["segment_b_id"],
            -1.0 if event["t_a"] is None else event["t_a"],
            -1.0 if event["t_b"] is None else event["t_b"],
            event["event_type"],
        )
    )
    for index, event in enumerate(events, start=1):
        event["event_id"] = f"env{environment_id}_intersection_event_{index:04d}"
    return events, endpoint_inventory, diagnostics


CSV_FIELDS = [
    "event_id", "environment_id", "event_type", "x", "y", "segment_a_id",
    "segment_b_id", "shape_a_id", "shape_b_id", "t_a", "t_b",
    "residual", "residual_unity_world_units", "same_shape", "source_anomaly_involved",
    "navigability_status", "refinement_method", "status", "review_notes",
]


def write_event_tables(events: list[dict[str, Any]]) -> None:
    TABLE_DIRECTORY.mkdir(parents=True, exist_ok=True)
    with (TABLE_DIRECTORY / "phase8-intersection-events.csv").open(
        "w", encoding="utf-8", newline=""
    ) as destination:
        writer = csv.DictWriter(destination, fieldnames=CSV_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(events)
    review = [event for event in events if event["navigability_status"] == "requires_3d_review"]
    with (TABLE_DIRECTORY / "phase8-3d-crossing-review.csv").open(
        "w", encoding="utf-8", newline=""
    ) as destination:
        writer = csv.DictWriter(destination, fieldnames=CSV_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(review)


EVENT_STYLES = {
    "endpoint_endpoint": ("o", "#1b9e77"),
    "endpoint_interior": ("s", "#d95f02"),
    "interior_interior_crossing": ("x", "#7570b3"),
    "tangent_touch": ("^", "#e7298a"),
    "overlap_or_coincident": ("D", "#66a61e"),
    "unresolved_candidate": ("P", "#e6ab02"),
}


def plot_events(
    environment_id: int,
    records: list[dict[str, Any]],
    events: list[dict[str, Any]],
    review_only: bool,
) -> None:
    figure, axis = plt.subplots(figsize=(9, 9))
    for segment in records:
        coordinates = segment["samples"][:, 1:]
        axis.plot(coordinates[:, 0], coordinates[:, 1], color="#a0a0a0", linewidth=1.0)
    selected_events = (
        [event for event in events if event["navigability_status"] == "requires_3d_review"]
        if review_only else events
    )
    for event_type, (marker, color) in EVENT_STYLES.items():
        subset = [event for event in selected_events if event["event_type"] == event_type]
        if not subset:
            continue
        axis.scatter(
            [event["x"] for event in subset],
            [event["y"] for event in subset],
            marker=marker,
            color=color,
            s=34,
            linewidths=1.3,
            label=f"{event_type} ({len(subset)})",
            zorder=4,
        )
    qualifier = "interior/ambiguous crossings for 3D review" if review_only else "pairwise geometric events"
    axis.set_title(f"Environment {environment_id}: {qualifier}")
    axis.set_xlabel("Unity world X")
    axis.set_ylabel("Unity world Y")
    axis.set_aspect("equal", adjustable="box")
    axis.grid(False)
    if selected_events:
        axis.legend(loc="best", fontsize=8)
    figure.tight_layout()
    filename = (
        f"env{environment_id}-interior-crossings-review.png"
        if review_only
        else f"env{environment_id}-geometric-intersections.png"
    )
    figure.savefig(QA_DIRECTORY / filename, dpi=180, bbox_inches="tight")
    plt.close(figure)


def main() -> int:
    sources, hashes, phase7_selection = load_inputs()
    records_by_environment = {
        environment_id: segment_records(source)
        for environment_id, source in sources.items()
    }
    events_by_environment = {}
    endpoint_inventories = {}
    diagnostics = {}
    for environment_id, records in records_by_environment.items():
        events, endpoint_inventory, environment_diagnostics = analyze_environment(
            environment_id, records
        )
        events_by_environment[environment_id] = events
        endpoint_inventories[environment_id] = endpoint_inventory
        diagnostics[environment_id] = environment_diagnostics

    all_events = [
        event
        for environment_id in (38, 39)
        for event in events_by_environment[environment_id]
    ]
    counts_by_environment = {
        environment_id: dict(sorted(Counter(event["event_type"] for event in events).items()))
        for environment_id, events in events_by_environment.items()
    }
    unresolved_count = sum(
        event["event_type"] == "unresolved_candidate" for event in all_events
    )
    accepted_residuals = [
        event["residual_unity_world_units"]
        for event in all_events
        if event["status"] == "refined"
        and event["residual_unity_world_units"] is not None
    ]
    if any(residual > NUMERICAL_RESIDUAL_TOLERANCE for residual in accepted_residuals):
        raise ValueError("Accepted refined root exceeds numerical residual threshold")

    QA_DIRECTORY.mkdir(parents=True, exist_ok=True)
    tested_at = datetime.now(timezone.utc).isoformat()
    payload = {
        "intersection_reconstruction_schema_version": "1.0.0",
        "phase8_analysis_version": ANALYSIS_VERSION,
        "algorithm": (
            "Phase 7 Shapely polyline candidates plus independent exact source-equation "
            "Sylvester-resultant enumeration and bounded SciPy least-squares refinement"
        ),
        "coordinate_space": "Unity world XY",
        "units": "Unity world units",
        "meter_scale_verified": False,
        "crs": None,
        "source_hashes": {str(key): value for key, value in hashes.items()},
        "source_segment_counts": {"38": len(records_by_environment[38]), "39": len(records_by_environment[39])},
        "phase7_selected_curve_tolerance": {
            "relative": phase7_selection["selected_relative_tolerance"],
            "absolute_unity_world_units": phase7_selection[
                "selected_absolute_tolerance_unity_world_units"
            ],
            "warning": "curve approximation tolerance only; not used for snapping",
        },
        "numerical_refinement": {
            "common_reference_scale_unity_world_units": COMMON_REFERENCE_SCALE,
            "relative_residual_threshold": NUMERICAL_RESIDUAL_RELATIVE,
            "absolute_residual_threshold_unity_world_units": NUMERICAL_RESIDUAL_TOLERANCE,
            "root_parameter_equivalence": ROOT_PARAMETER_EQUIVALENCE,
            "zero_chord_authored_endpoint_parameter_equivalence": ANOMALY_ENDPOINT_PARAMETER_EQUIVALENCE,
            "tangent_sine_threshold": TANGENT_SINE_THRESHOLD,
            "purpose": "root convergence and same-pair numerical-root deduplication only",
            "not_a_snapping_tolerance": True,
        },
        "tested_at_utc": tested_at,
        "software_versions": {
            "python": platform.python_version(),
            "numpy": importlib.metadata.version("numpy"),
            "scipy": importlib.metadata.version("scipy"),
            "shapely": importlib.metadata.version("shapely"),
            "matplotlib": importlib.metadata.version("matplotlib"),
        },
        "counts": {
            "total_pairwise_events": len(all_events),
            "by_environment": {str(key): len(value) for key, value in events_by_environment.items()},
            "by_environment_and_type": {str(key): value for key, value in counts_by_environment.items()},
            "exact_endpoint_endpoint_events": sum(event["event_type"] == "endpoint_endpoint" for event in all_events),
            "endpoint_interior_events": sum(event["event_type"] == "endpoint_interior" for event in all_events),
            "interior_interior_crossing_events": sum(event["event_type"] == "interior_interior_crossing" for event in all_events),
            "tangent_touch_events": sum(event["event_type"] == "tangent_touch" for event in all_events),
            "overlap_or_coincident_events": sum(event["event_type"] == "overlap_or_coincident" for event in all_events),
            "unresolved_candidate_events": unresolved_count,
            "cross_shape_events": sum(not event["same_shape"] for event in all_events),
            "source_anomaly_involved_events": sum(event["source_anomaly_involved"] for event in all_events),
            "requires_3d_review_events": sum(event["navigability_status"] == "requires_3d_review" for event in all_events),
        },
        "maximum_accepted_root_residual_unity_world_units": max(accepted_residuals, default=0.0),
        "exact_endpoint_connectivity": {str(key): value for key, value in endpoint_inventories.items()},
        "completeness_cross_check": {
            "methods": {
                "A": "Phase 7 adaptive Shapely LineString intersection candidates",
            "B": "original quadratic Sylvester-resultant root enumeration",
            },
            "environment_diagnostics": {str(key): value for key, value in diagnostics.items()},
            "unresolved_candidates_retained": unresolved_count,
            "no_candidate_discrepancy_silently_discarded": True,
            "result": "PASS" if unresolved_count == 0 else "REVIEW_REQUIRED",
        },
        "topology_status": (
            "BLOCKED_PENDING_UNRESOLVED_REVIEW" if unresolved_count else "NOT_CONSTRUCTED_PHASE_BOUNDARY"
        ),
        "snapping_performed": False,
        "topology_constructed": False,
        "graph_nodes_created": False,
        "networkx_graph_created": False,
        "osmnx_graph_created": False,
        "final_morphology_metrics_calculated": False,
        "events": all_events,
    }
    write_json(QA_DIRECTORY / "phase8-intersection-reconstruction.json", payload)
    write_event_tables(all_events)
    for environment_id in (38, 39):
        plot_events(
            environment_id,
            records_by_environment[environment_id],
            events_by_environment[environment_id],
            review_only=False,
        )
        plot_events(
            environment_id,
            records_by_environment[environment_id],
            events_by_environment[environment_id],
            review_only=True,
        )

    print("Canonical raw SHA-256 and Phase 7 provenance verification: PASS")
    print(
        f"Numerical residual threshold: {NUMERICAL_RESIDUAL_TOLERANCE:.15g} "
        "Unity world units"
    )
    for environment_id in (38, 39):
        print(
            f"Environment {environment_id}: events={len(events_by_environment[environment_id])}, "
            f"types={counts_by_environment[environment_id]}, "
            f"diagnostics={diagnostics[environment_id]}"
        )
    print(f"Maximum accepted root residual: {max(accepted_residuals, default=0.0):.15g}")
    print(f"Events requiring 3D review: {payload['counts']['requires_3d_review_events']}")
    print(f"Unresolved candidates: {unresolved_count}")
    print(
        "Phase 8 intersection inventory: "
        + ("PASS" if unresolved_count == 0 else "REVIEW REQUIRED; topology remains blocked")
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
