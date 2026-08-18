"""Reconstruct exported quadratic Béziers for Phase 6 geometry QA only.

This script intentionally performs no snapping, intersection detection,
topology construction, graph creation, CRS assignment, or scientific metric
calculation.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import tempfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np

os.environ.setdefault(
    "MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "geogami-morphology-matplotlib")
)
import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

from bezier_geometry import quadratic_bezier_point


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
RAW_DIRECTORY = REPOSITORY_ROOT / "data" / "raw"
PROCESSED_DIRECTORY = REPOSITORY_ROOT / "data" / "processed"
QA_DIRECTORY = REPOSITORY_ROOT / "outputs" / "qa"

RECONSTRUCTION_VERSION = "1.0.0"
VISUALIZATION_SAMPLES_PER_SEGMENT = 101
NEAR_STRAIGHT_RATIO_THRESHOLD = 1e-6

SOURCE_CONFIG = {
    38: {
        "filename": "env38_bezier.json",
        "sha256": "43ea446a4a88e9f3d594fb8b72742f5d4b2a1ee8a03ebf8350c4c3cce45c5819",
        "shape_counts": [4, 32, 32, 24, 28],
        "total_segments": 120,
        "output_filename": "env38_bezier_reconstruction.json",
    },
    39: {
        "filename": "env39_bezier.json",
        "sha256": "e5dbce6b4d88656c9e0f3bbf6a814434f64b0fbe9b3ff1864ea3fafaf0883602",
        "shape_counts": [32],
        "total_segments": 32,
        "output_filename": "env39_bezier_reconstruction.json",
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
    text = json.dumps(payload, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    path.write_text(text, encoding="utf-8")


def world_xy(point: dict[str, Any]) -> np.ndarray:
    coordinates = np.array([point["x"], point["y"]], dtype=np.float64)
    if not np.all(np.isfinite(coordinates)):
        raise ValueError(f"Non-finite world XY coordinate: {point}")
    return coordinates


def load_and_validate_source(environment_id: int) -> tuple[dict[str, Any], Path, str]:
    config = SOURCE_CONFIG[environment_id]
    path = RAW_DIRECTORY / config["filename"]
    actual_hash = sha256_file(path)
    if actual_hash != config["sha256"]:
        raise RuntimeError(
            f"Canonical raw hash mismatch for {path}: {actual_hash}; "
            f"expected {config['sha256']}"
        )

    with path.open("r", encoding="utf-8") as source:
        data = json.load(source)

    if data.get("schema_version") != "1.0.0":
        raise ValueError(f"Unexpected source schema for Environment {environment_id}")
    if data.get("environment_id") != environment_id:
        raise ValueError(f"Unexpected environment_id in {path}")
    if data.get("shape_count") != len(config["shape_counts"]):
        raise ValueError(f"Unexpected Shape count in {path}")
    actual_shape_counts = [shape["segment_count"] for shape in data["shapes"]]
    if actual_shape_counts != config["shape_counts"]:
        raise ValueError(
            f"Unexpected ordered Shape counts in {path}: {actual_shape_counts}"
        )
    if data.get("total_segment_count") != config["total_segments"]:
        raise ValueError(f"Unexpected total segment count in {path}")

    for shape in data["shapes"]:
        if len(shape["segments"]) != shape["segment_count"]:
            raise ValueError(f"Segment array mismatch for {shape['shape_id']}")
        for segment in shape["segments"]:
            for point_name in ("p0", "p1", "p2"):
                point = segment["world"][point_name]
                if point["z"] != 0:
                    raise ValueError(
                        f"Expected planar world z=0 in {segment['segment_id']} {point_name}"
                    )
                world_xy(point)

    return data, path, actual_hash


def source_world_points(segment: dict[str, Any]) -> dict[str, dict[str, float]]:
    return {
        point_name: {
            axis: float(segment["world"][point_name][axis])
            for axis in ("x", "y", "z")
        }
        for point_name in ("p0", "p1", "p2")
    }


def exact_quadratic_bounds(curves: list[dict[str, Any]]) -> dict[str, float]:
    candidates: list[np.ndarray] = []
    for curve in curves:
        p0, p1, p2 = curve["p0"], curve["p1"], curve["p2"]
        candidates.extend((p0, p2))
        denominator = p0 - 2.0 * p1 + p2
        for axis in (0, 1):
            if denominator[axis] == 0.0:
                continue
            t = (p0[axis] - p1[axis]) / denominator[axis]
            if 0.0 < t < 1.0:
                candidates.append(quadratic_bezier_point(p0, p1, p2, float(t)))

    all_candidates = np.vstack(candidates)
    return {
        "min_x": float(np.min(all_candidates[:, 0])),
        "max_x": float(np.max(all_candidates[:, 0])),
        "min_y": float(np.min(all_candidates[:, 1])),
        "max_y": float(np.max(all_candidates[:, 1])),
    }


def reconstruct_environment(
    source_data: dict[str, Any], source_path: Path, source_hash: str
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    environment_id = source_data["environment_id"]
    t_values = np.linspace(0.0, 1.0, VISUALIZATION_SAMPLES_PER_SEGMENT)
    output_shapes: list[dict[str, Any]] = []
    curves: list[dict[str, Any]] = []
    reconstructed_count = 0
    retained_anomalies: list[str] = []

    for shape in source_data["shapes"]:
        output_segments: list[dict[str, Any]] = []
        for segment in shape["segments"]:
            segment_id = segment["segment_id"]
            p0 = world_xy(segment["world"]["p0"])
            p1 = world_xy(segment["world"]["p1"])
            p2 = world_xy(segment["world"]["p2"])
            samples = quadratic_bezier_point(p0, p1, p2, t_values)

            if not np.array_equal(samples[0], p0):
                raise ValueError(f"First sample does not equal p0 for {segment_id}")
            if not np.array_equal(samples[-1], p2):
                raise ValueError(f"Last sample does not equal p2 for {segment_id}")
            if not np.all(np.isfinite(samples)):
                raise ValueError(f"Non-finite visualization sample for {segment_id}")

            source_points = source_world_points(segment)
            if source_points != {
                name: {axis: float(segment["world"][name][axis]) for axis in ("x", "y", "z")}
                for name in ("p0", "p1", "p2")
            }:
                raise ValueError(f"Source control-point preservation failed for {segment_id}")

            qa_flags: list[str] = []
            if segment_id in KNOWN_ZERO_CHORD_ANOMALIES:
                if not np.array_equal(p0, p2):
                    raise ValueError(f"Expected zero chord not found for {segment_id}")
                qa_flags.append("known_zero_chord_source_anomaly")
                retained_anomalies.append(segment_id)

            output_segment = {
                "environment_id": environment_id,
                "shape_id": shape["shape_id"],
                "shape_index": shape["shape_index"],
                "segment_id": segment_id,
                "segment_index": segment["segment_index"],
                "source_world_control_points": source_points,
                "visualization_samples_xy": samples.tolist(),
                "qa_flags": qa_flags,
            }
            output_segments.append(output_segment)
            curves.append(
                {
                    "shape_index": shape["shape_index"],
                    "shape_id": shape["shape_id"],
                    "segment_id": segment_id,
                    "p0": p0,
                    "p1": p1,
                    "p2": p2,
                    "samples": samples,
                }
            )
            reconstructed_count += 1

        output_shapes.append(
            {
                "shape_id": shape["shape_id"],
                "shape_index": shape["shape_index"],
                "segment_count": len(output_segments),
                "segments": output_segments,
            }
        )

    expected_count = SOURCE_CONFIG[environment_id]["total_segments"]
    if reconstructed_count != expected_count:
        raise ValueError(
            f"Environment {environment_id} reconstructed {reconstructed_count}; "
            f"expected {expected_count}"
        )
    expected_anomalies = (
        sorted(KNOWN_ZERO_CHORD_ANOMALIES) if environment_id == 38 else []
    )
    if sorted(retained_anomalies) != expected_anomalies:
        raise ValueError(
            f"Environment {environment_id} anomaly retention mismatch: {retained_anomalies}"
        )

    bounds = exact_quadratic_bounds(curves)
    artifact = {
        "reconstruction_schema_version": "1.0.0",
        "phase6_reconstruction_version": RECONSTRUCTION_VERSION,
        "source_schema_version": source_data["schema_version"],
        "source_file": source_path.relative_to(REPOSITORY_ROOT).as_posix(),
        "source_file_sha256": source_hash,
        "environment_id": environment_id,
        "environment_label": source_data["environment_label"],
        "coordinate_space": "Unity world XY",
        "units": "Unity world units",
        "meter_scale_verified": False,
        "meters_per_unity_world_unit": None,
        "crs": None,
        "sampling": {
            "purpose": "visualization-only dense sampling",
            "samples_per_segment": VISUALIZATION_SAMPLES_PER_SEGMENT,
            "includes_t0_and_t1": True,
            "analytical_sampling_tolerance": None,
            "warning": (
                "These samples are for Phase 6 visual QA only and must not be used "
                "to justify analytical length, intersections, topology, entropy, "
                "circuity, or other network metrics."
            ),
        },
        "shape_count": len(output_shapes),
        "reconstructed_segment_count": reconstructed_count,
        "exact_quadratic_xy_bounds": bounds,
        "completeness_qa": {
            "all_source_segments_retained": True,
            "all_first_samples_equal_p0": True,
            "all_last_samples_equal_p2": True,
            "all_visualization_xy_finite": True,
            "source_control_points_preserved": True,
            "retained_known_zero_chord_anomaly_ids": expected_anomalies,
        },
        "shapes": output_shapes,
    }
    return artifact, curves


def endpoint_audit(source_data: dict[str, Any]) -> dict[str, Any]:
    position_references: defaultdict[tuple[float, float], list[dict[str, str]]] = defaultdict(list)
    directed_pairs: set[tuple[tuple[float, float], tuple[float, float]]] = set()
    undirected_pairs: set[tuple[tuple[float, float], tuple[float, float]]] = set()
    total_segments = 0

    for shape in source_data["shapes"]:
        for segment in shape["segments"]:
            total_segments += 1
            p0_array = world_xy(segment["world"]["p0"])
            p2_array = world_xy(segment["world"]["p2"])
            p0 = (float(p0_array[0]), float(p0_array[1]))
            p2 = (float(p2_array[0]), float(p2_array[1]))
            position_references[p0].append(
                {"segment_id": segment["segment_id"], "endpoint": "p0"}
            )
            position_references[p2].append(
                {"segment_id": segment["segment_id"], "endpoint": "p2"}
            )
            directed_pairs.add((p0, p2))
            undirected_pairs.add(tuple(sorted((p0, p2))))

    occurrence_distribution = Counter(len(refs) for refs in position_references.values())
    records = []
    for position, references in sorted(position_references.items()):
        distinct_segments = {reference["segment_id"] for reference in references}
        records.append(
            {
                "position_xy": [position[0], position[1]],
                "endpoint_occurrence_count": len(references),
                "distinct_source_segment_count": len(distinct_segments),
                "references": references,
            }
        )

    return {
        "environment_id": source_data["environment_id"],
        "total_source_segments": total_segments,
        "total_endpoint_occurrences": total_segments * 2,
        "distinct_exact_endpoint_positions": len(position_references),
        "distinct_directed_p0_p2_pairs": len(directed_pairs),
        "distinct_undirected_p0_p2_pairs": len(undirected_pairs),
        "endpoint_positions_appearing_once": sum(
            len(refs) == 1 for refs in position_references.values()
        ),
        "endpoint_positions_with_multiple_occurrences": sum(
            len(refs) > 1 for refs in position_references.values()
        ),
        "endpoint_positions_shared_by_multiple_source_segments": sum(
            len({reference["segment_id"] for reference in refs}) > 1
            for refs in position_references.values()
        ),
        "maximum_endpoint_occurrence_count": max(map(len, position_references.values())),
        "endpoint_occurrence_frequency": {
            str(count): positions
            for count, positions in sorted(occurrence_distribution.items())
        },
        "exact_endpoint_positions": records,
    }


def source_diagnostics(source_data: dict[str, Any]) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    classifications: Counter[str] = Counter()
    defined_deviations: list[float] = []
    zero_chord_ids: list[str] = []

    for shape in source_data["shapes"]:
        for segment in shape["segments"]:
            p0 = world_xy(segment["world"]["p0"])
            p1 = world_xy(segment["world"]["p1"])
            p2 = world_xy(segment["world"]["p2"])
            chord = p2 - p0
            chord_magnitude = float(np.linalg.norm(chord))
            segment_id = segment["segment_id"]

            if np.array_equal(p0, p2):
                classification = "zero_chord_undefined"
                deviation = None
                ratio = None
                p1_displacement = float(np.linalg.norm(p1 - p0))
                zero_chord_ids.append(segment_id)
            else:
                signed_cross = float(chord[0] * (p1[1] - p0[1]) - chord[1] * (p1[0] - p0[0]))
                deviation = abs(signed_cross) / chord_magnitude
                ratio = deviation / chord_magnitude
                p1_displacement = None
                if signed_cross == 0.0:
                    classification = "exactly_collinear"
                elif ratio <= NEAR_STRAIGHT_RATIO_THRESHOLD:
                    classification = "near_collinear"
                else:
                    classification = "control_point_deviates_from_chord"
                defined_deviations.append(deviation)

            classifications[classification] += 1
            records.append(
                {
                    "shape_id": shape["shape_id"],
                    "shape_index": shape["shape_index"],
                    "segment_id": segment_id,
                    "segment_index": segment["segment_index"],
                    "classification": classification,
                    "control_point_perpendicular_deviation_world_units": deviation,
                    "control_point_deviation_ratio_to_chord": ratio,
                    "zero_chord_control_point_displacement_from_p0_world_units": p1_displacement,
                }
            )

    return {
        "environment_id": source_data["environment_id"],
        "source_segment_count": len(records),
        "classification_counts": dict(sorted(classifications.items())),
        "near_straight_ratio_threshold": NEAR_STRAIGHT_RATIO_THRESHOLD,
        "defined_perpendicular_deviation_range_world_units": {
            "minimum": min(defined_deviations) if defined_deviations else None,
            "maximum": max(defined_deviations) if defined_deviations else None,
        },
        "zero_chord_segment_ids": sorted(zero_chord_ids),
        "segments": records,
    }


def configure_axis(axis: plt.Axes, title: str) -> None:
    axis.set_title(title)
    axis.set_xlabel("Unity world X")
    axis.set_ylabel("Unity world Y")
    axis.set_aspect("equal", adjustable="box")
    axis.grid(False)


def plot_reconstructed(environment_id: int, curves: list[dict[str, Any]]) -> None:
    figure, axis = plt.subplots(figsize=(8, 8))
    for curve in curves:
        samples = curve["samples"]
        axis.plot(samples[:, 0], samples[:, 1], color="#c96f5b", linewidth=1.6)
    configure_axis(axis, f"Environment {environment_id}: reconstructed quadratic Béziers")
    figure.tight_layout()
    figure.savefig(
        QA_DIRECTORY / f"env{environment_id}_reconstructed_beziers.png",
        dpi=180,
        bbox_inches="tight",
    )
    plt.close(figure)


def plot_control_geometry(environment_id: int, curves: list[dict[str, Any]]) -> None:
    figure, axis = plt.subplots(figsize=(9, 9))
    for curve in curves:
        p0, p1, p2 = curve["p0"], curve["p1"], curve["p2"]
        samples = curve["samples"]
        control = np.vstack((p0, p1, p2))
        axis.plot(control[:, 0], control[:, 1], color="#999999", linewidth=0.5, alpha=0.45)
        axis.plot(samples[:, 0], samples[:, 1], color="#3268a8", linewidth=1.2)
        axis.scatter([p0[0], p2[0]], [p0[1], p2[1]], color="#202020", s=7, zorder=3)
        axis.scatter([p1[0]], [p1[1]], color="#d1495b", s=8, zorder=3)

    configure_axis(axis, f"Environment {environment_id}: Bézier control geometry QA")
    axis.legend(
        handles=[
            Line2D([0], [0], color="#3268a8", label="Reconstructed curve"),
            Line2D([0], [0], color="#999999", label="Control polygon"),
            Line2D([0], [0], marker="o", color="none", markerfacecolor="#202020", label="p0 / p2"),
            Line2D([0], [0], marker="o", color="none", markerfacecolor="#d1495b", label="p1"),
        ],
        loc="best",
        fontsize="small",
    )
    figure.tight_layout()
    figure.savefig(
        QA_DIRECTORY / f"env{environment_id}_bezier_control_geometry.png",
        dpi=180,
        bbox_inches="tight",
    )
    plt.close(figure)


def plot_combined(curves_by_environment: dict[int, list[dict[str, Any]]]) -> None:
    all_samples = np.vstack(
        [curve["samples"] for curves in curves_by_environment.values() for curve in curves]
    )
    min_x, max_x = np.min(all_samples[:, 0]), np.max(all_samples[:, 0])
    min_y, max_y = np.min(all_samples[:, 1]), np.max(all_samples[:, 1])
    margin_x = max((max_x - min_x) * 0.03, 1.0)
    margin_y = max((max_y - min_y) * 0.03, 1.0)

    figure, axes = plt.subplots(1, 2, figsize=(14, 7), sharex=True, sharey=True)
    for axis, environment_id in zip(axes, (38, 39), strict=True):
        for curve in curves_by_environment[environment_id]:
            samples = curve["samples"]
            axis.plot(samples[:, 0], samples[:, 1], color="#c96f5b", linewidth=1.2)
        configure_axis(axis, f"Environment {environment_id}")
        axis.set_xlim(min_x - margin_x, max_x + margin_x)
        axis.set_ylim(min_y - margin_y, max_y + margin_y)
    figure.suptitle("Phase 6 reconstructed world-XY geometry (common raw coordinate scale)")
    figure.tight_layout()
    figure.savefig(
        QA_DIRECTORY / "env38-vs-env39-reconstructed.png",
        dpi=180,
        bbox_inches="tight",
    )
    plt.close(figure)


def main() -> int:
    PROCESSED_DIRECTORY.mkdir(parents=True, exist_ok=True)
    QA_DIRECTORY.mkdir(parents=True, exist_ok=True)

    artifacts: dict[int, dict[str, Any]] = {}
    curves_by_environment: dict[int, list[dict[str, Any]]] = {}
    endpoint_audits = []
    diagnostic_audits = []

    # Validate both immutable sources before writing any derived artifact.
    loaded = {
        environment_id: load_and_validate_source(environment_id)
        for environment_id in (38, 39)
    }

    for environment_id, (source_data, source_path, source_hash) in loaded.items():
        artifact, curves = reconstruct_environment(source_data, source_path, source_hash)
        artifacts[environment_id] = artifact
        curves_by_environment[environment_id] = curves
        endpoint_audits.append(endpoint_audit(source_data))
        diagnostic_audits.append(source_diagnostics(source_data))

    actual_zero_chords = {
        segment_id
        for audit in diagnostic_audits
        if audit["environment_id"] == 38
        for segment_id in audit["zero_chord_segment_ids"]
    }
    if actual_zero_chords != KNOWN_ZERO_CHORD_ANOMALIES:
        raise ValueError(
            f"Environment 38 zero-chord anomaly mismatch: {sorted(actual_zero_chords)}"
        )

    for environment_id, artifact in artifacts.items():
        output_path = PROCESSED_DIRECTORY / SOURCE_CONFIG[environment_id]["output_filename"]
        write_json(output_path, artifact)

    write_json(
        QA_DIRECTORY / "phase6-endpoint-audit.json",
        {
            "audit_schema_version": "1.0.0",
            "phase6_reconstruction_version": RECONSTRUCTION_VERSION,
            "coordinate_space": "Unity world XY",
            "comparison": "exact coordinate equality only",
            "snapping_performed": False,
            "topology_constructed": False,
            "warning": (
                "This is source endpoint QA, not final topology. Crossings may occur "
                "inside Bézier curves and across different Shapes; endpoint equality "
                "alone is insufficient to identify navigable intersections."
            ),
            "environments": endpoint_audits,
        },
    )
    write_json(
        QA_DIRECTORY / "phase6-bezier-source-diagnostics.json",
        {
            "diagnostic_schema_version": "1.0.0",
            "phase6_reconstruction_version": RECONSTRUCTION_VERSION,
            "coordinate_space": "Unity world XY",
            "units": "Unity world units",
            "purpose": "source-geometry QA only",
            "not_a_scientific_morphology_metric": True,
            "not_network_circuity": True,
            "method": (
                "Perpendicular distance from p1 to the infinite p0-p2 chord line; "
                "zero-chord segments are reported separately because chord direction "
                "is undefined."
            ),
            "environments": diagnostic_audits,
        },
    )

    for environment_id, curves in curves_by_environment.items():
        plot_reconstructed(environment_id, curves)
        plot_control_geometry(environment_id, curves)
    plot_combined(curves_by_environment)

    print("Canonical raw SHA-256 verification: PASS")
    for environment_id in (38, 39):
        artifact = artifacts[environment_id]
        endpoint = next(
            audit for audit in endpoint_audits if audit["environment_id"] == environment_id
        )
        diagnostics = next(
            audit for audit in diagnostic_audits if audit["environment_id"] == environment_id
        )
        print(
            f"Environment {environment_id}: reconstructed_segments="
            f"{artifact['reconstructed_segment_count']}, "
            f"bounds={artifact['exact_quadratic_xy_bounds']}"
        )
        print(
            f"Environment {environment_id} endpoint audit: "
            f"distinct_positions={endpoint['distinct_exact_endpoint_positions']}, "
            f"shared_by_multiple_segments="
            f"{endpoint['endpoint_positions_shared_by_multiple_source_segments']}, "
            f"appearing_once={endpoint['endpoint_positions_appearing_once']}"
        )
        print(
            f"Environment {environment_id} diagnostic summary: "
            f"classifications={diagnostics['classification_counts']}, "
            f"deviation_range={diagnostics['defined_perpendicular_deviation_range_world_units']}"
        )
    print(f"Retained zero-chord anomalies: {sorted(actual_zero_chords)}")
    print("Phase 6 reconstruction and QA artifacts: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
