"""Phase 7 adaptive quadratic Bézier discretization and convergence QA.

This script performs curve-approximation analysis only. It does not detect
intersections, snap or merge coordinates, construct topology or graphs, assign
a CRS, convert units, or calculate final morphology metrics.
"""

from __future__ import annotations

import csv
import hashlib
import importlib.metadata
import json
import math
import os
import platform
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
from scipy.integrate import quad

os.environ.setdefault(
    "MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "geogami-morphology-matplotlib")
)
import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from bezier_geometry import adaptive_quadratic_bezier_polyline


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
RAW_DIRECTORY = REPOSITORY_ROOT / "data" / "raw"
PROCESSED_DIRECTORY = REPOSITORY_ROOT / "data" / "processed"
QA_DIRECTORY = REPOSITORY_ROOT / "outputs" / "qa"
TABLE_DIRECTORY = REPOSITORY_ROOT / "outputs" / "tables"

ANALYSIS_VERSION = "1.0.0"
RELATIVE_TOLERANCES = (1e-3, 5e-4, 2e-4, 1e-4, 5e-5, 2e-5, 1e-5)
AGGREGATE_REFERENCE_ERROR_THRESHOLD = 1e-4
SUCCESSIVE_LENGTH_CHANGE_THRESHOLD = 1e-4
ORDINARY_SEGMENT_RELATIVE_ERROR_THRESHOLD = 1e-3
ORDINARY_LENGTH_SCALE_FLOOR_FACTOR = 1e-12
QUAD_EPSABS = 1e-12
QUAD_EPSREL = 1e-12

SOURCE_CONFIG = {
    38: {
        "filename": "env38_bezier.json",
        "sha256": "43ea446a4a88e9f3d594fb8b72742f5d4b2a1ee8a03ebf8350c4c3cce45c5819",
        "shape_counts": [4, 32, 32, 24, 28],
        "total_segments": 120,
    },
    39: {
        "filename": "env39_bezier.json",
        "sha256": "e5dbce6b4d88656c9e0f3bbf6a814434f64b0fbe9b3ff1864ea3fafaf0883602",
        "shape_counts": [32],
        "total_segments": 32,
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


def load_source(environment_id: int) -> tuple[dict[str, Any], Path, str]:
    config = SOURCE_CONFIG[environment_id]
    path = RAW_DIRECTORY / config["filename"]
    actual_hash = sha256_file(path)
    if actual_hash != config["sha256"]:
        raise RuntimeError(
            f"Canonical raw hash mismatch for {path}: {actual_hash}; "
            f"expected {config['sha256']}"
        )
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != "1.0.0":
        raise ValueError(f"Unexpected schema in {path}")
    if data.get("environment_id") != environment_id:
        raise ValueError(f"Unexpected environment_id in {path}")
    if [shape["segment_count"] for shape in data["shapes"]] != config["shape_counts"]:
        raise ValueError(f"Unexpected ordered Shape counts in {path}")
    if data.get("total_segment_count") != config["total_segments"]:
        raise ValueError(f"Unexpected total segment count in {path}")
    for shape in data["shapes"]:
        if len(shape["segments"]) != shape["segment_count"]:
            raise ValueError(f"Segment array mismatch for {shape['shape_id']}")
        for segment in shape["segments"]:
            for name in ("p0", "p1", "p2"):
                if segment["world"][name]["z"] != 0:
                    raise ValueError(f"Non-planar world point in {segment['segment_id']}")
                world_xy(segment["world"][name])
    return data, path, actual_hash


def flatten_segments(source: dict[str, Any]) -> list[dict[str, Any]]:
    records = []
    for shape in source["shapes"]:
        for segment in shape["segments"]:
            records.append(
                {
                    "environment_id": source["environment_id"],
                    "shape_id": shape["shape_id"],
                    "shape_index": shape["shape_index"],
                    "segment_id": segment["segment_id"],
                    "segment_index": segment["segment_index"],
                    "p0": world_xy(segment["world"]["p0"]),
                    "p1": world_xy(segment["world"]["p1"]),
                    "p2": world_xy(segment["world"]["p2"]),
                    "source_world": segment["world"],
                }
            )
    return records


def control_geometry_bounds(segments: list[dict[str, Any]]) -> dict[str, float]:
    points = np.vstack(
        [segment[name] for segment in segments for name in ("p0", "p1", "p2")]
    )
    min_x, min_y = np.min(points, axis=0)
    max_x, max_y = np.max(points, axis=0)
    return {
        "min_x": float(min_x),
        "max_x": float(max_x),
        "min_y": float(min_y),
        "max_y": float(max_y),
        "diagonal": float(math.hypot(max_x - min_x, max_y - min_y)),
    }


def quadratic_bezier_reference_length(
    p0: np.ndarray, p1: np.ndarray, p2: np.ndarray
) -> float:
    """Integrate ||B'(t)|| with strict adaptive SciPy quadrature."""
    first = 2.0 * (p1 - p0)
    change = 2.0 * (p2 - 2.0 * p1 + p0)

    def speed(parameter: float) -> float:
        return float(np.linalg.norm(first + parameter * change))

    length, _ = quad(
        speed,
        0.0,
        1.0,
        epsabs=QUAD_EPSABS,
        epsrel=QUAD_EPSREL,
        limit=100,
    )
    return float(length)


def polyline_length(vertices: np.ndarray) -> float:
    return float(np.sum(np.linalg.norm(np.diff(vertices, axis=0), axis=1)))


def analyze_tolerance(
    segments: list[dict[str, Any]],
    relative_tolerance: float,
    absolute_tolerance: float,
    ordinary_length_floor: float,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    details = []
    vertex_counts = []
    reference_total = 0.0
    polyline_total = 0.0
    aggregate_absolute_error = 0.0
    ordinary_relative_errors = []
    nonzero_relative_errors = []

    for segment in segments:
        vertices = adaptive_quadratic_bezier_polyline(
            segment["p0"], segment["p1"], segment["p2"], absolute_tolerance
        )
        adaptive_length = polyline_length(vertices)
        reference_length = segment["reference_length"]
        absolute_error = abs(adaptive_length - reference_length)
        relative_error = (
            absolute_error / reference_length if reference_length > 0.0 else None
        )
        zero_chord = bool(np.array_equal(segment["p0"], segment["p2"]))
        ordinary = (
            not zero_chord and reference_length >= ordinary_length_floor
        )
        if relative_error is not None:
            nonzero_relative_errors.append(relative_error)
        if ordinary and relative_error is not None:
            ordinary_relative_errors.append(relative_error)
        vertex_counts.append(len(vertices))
        reference_total += reference_length
        polyline_total += adaptive_length
        aggregate_absolute_error += absolute_error
        details.append(
            {
                "segment_id": segment["segment_id"],
                "vertex_count": len(vertices),
                "polyline_segment_count": len(vertices) - 1,
                "reference_length": reference_length,
                "polyline_length": adaptive_length,
                "absolute_length_error": absolute_error,
                "relative_length_error": relative_error,
                "zero_chord": zero_chord,
                "ordinary_segment_for_acceptance": ordinary,
                "vertices": vertices,
            }
        )

    summary = {
        "relative_tolerance": relative_tolerance,
        "absolute_tolerance_unity_world_units": absolute_tolerance,
        "total_polyline_vertex_count": int(sum(vertex_counts)),
        "total_polyline_segment_count": int(sum(count - 1 for count in vertex_counts)),
        "minimum_vertices_per_bezier": int(min(vertex_counts)),
        "maximum_vertices_per_bezier": int(max(vertex_counts)),
        "median_vertices_per_bezier": float(np.median(vertex_counts)),
        "reference_total_length_unity_world_units": reference_total,
        "total_polyline_length_unity_world_units": polyline_total,
        "aggregate_absolute_length_error_unity_world_units": aggregate_absolute_error,
        "aggregate_relative_length_error": (
            aggregate_absolute_error / reference_total if reference_total > 0.0 else None
        ),
        "maximum_nonzero_segment_relative_length_error": (
            max(nonzero_relative_errors) if nonzero_relative_errors else None
        ),
        "maximum_ordinary_segment_relative_length_error": (
            max(ordinary_relative_errors) if ordinary_relative_errors else None
        ),
        "maximum_segment_length_change_to_next_finer_unity_world_units": None,
        "maximum_segment_relative_length_change_to_next_finer": None,
        "aggregate_total_length_relative_change_to_next_finer": None,
    }
    return summary, details


def add_successive_comparisons(
    sweep: list[dict[str, Any]], details: list[list[dict[str, Any]]]
) -> None:
    for index in range(len(sweep) - 1):
        current = details[index]
        finer = details[index + 1]
        absolute_changes = [
            abs(left["polyline_length"] - right["polyline_length"])
            for left, right in zip(current, finer, strict=True)
        ]
        relative_changes = [
            change / right["polyline_length"]
            if right["polyline_length"] > 0.0
            else 0.0
            for change, right in zip(absolute_changes, finer, strict=True)
        ]
        finer_total = sweep[index + 1]["total_polyline_length_unity_world_units"]
        sweep[index][
            "maximum_segment_length_change_to_next_finer_unity_world_units"
        ] = max(absolute_changes)
        sweep[index][
            "maximum_segment_relative_length_change_to_next_finer"
        ] = max(relative_changes)
        sweep[index]["aggregate_total_length_relative_change_to_next_finer"] = (
            abs(
                sweep[index]["total_polyline_length_unity_world_units"] - finer_total
            )
            / finer_total
            if finer_total > 0.0
            else 0.0
        )


def tolerance_passes(summary: dict[str, Any]) -> bool:
    values = (
        summary["aggregate_relative_length_error"],
        summary["aggregate_total_length_relative_change_to_next_finer"],
        summary["maximum_ordinary_segment_relative_length_error"],
    )
    return (
        all(value is not None for value in values)
        and values[0] <= AGGREGATE_REFERENCE_ERROR_THRESHOLD
        and values[1] <= SUCCESSIVE_LENGTH_CHANGE_THRESHOLD
        and values[2] <= ORDINARY_SEGMENT_RELATIVE_ERROR_THRESHOLD
    )


def selected_linework_artifact(
    source: dict[str, Any],
    source_path: Path,
    source_hash: str,
    selected_relative: float,
    selected_absolute: float,
    segment_records: list[dict[str, Any]],
    selected_details: list[dict[str, Any]],
    common_reference_scale: float,
) -> dict[str, Any]:
    detail_by_id = {detail["segment_id"]: detail for detail in selected_details}
    record_by_id = {record["segment_id"]: record for record in segment_records}
    output_shapes = []
    for shape in source["shapes"]:
        output_segments = []
        for source_segment in shape["segments"]:
            segment_id = source_segment["segment_id"]
            record = record_by_id[segment_id]
            detail = detail_by_id[segment_id]
            output_segments.append(
                {
                    "environment_id": source["environment_id"],
                    "shape_id": shape["shape_id"],
                    "shape_index": shape["shape_index"],
                    "segment_id": segment_id,
                    "segment_index": source_segment["segment_index"],
                    "original_world_control_points": source_segment["world"],
                    "selected_relative_tolerance": selected_relative,
                    "selected_absolute_tolerance_unity_world_units": selected_absolute,
                    "adaptive_vertices_xy": detail["vertices"].tolist(),
                    "adaptive_vertex_count": detail["vertex_count"],
                    "bezier_reference_length_unity_world_units": detail[
                        "reference_length"
                    ],
                    "adaptive_polyline_length_unity_world_units": detail[
                        "polyline_length"
                    ],
                    "absolute_length_error_unity_world_units": detail[
                        "absolute_length_error"
                    ],
                    "relative_length_error": detail["relative_length_error"],
                    "zero_chord": detail["zero_chord"],
                }
            )
            if not np.array_equal(detail["vertices"][0], record["p0"]):
                raise ValueError(f"Adaptive p0 mismatch for {segment_id}")
            if not np.array_equal(detail["vertices"][-1], record["p2"]):
                raise ValueError(f"Adaptive p2 mismatch for {segment_id}")
        output_shapes.append(
            {
                "shape_id": shape["shape_id"],
                "shape_index": shape["shape_index"],
                "segment_count": len(output_segments),
                "segments": output_segments,
            }
        )

    return {
        "detailed_linework_schema_version": "1.0.0",
        "phase7_analysis_version": ANALYSIS_VERSION,
        "source_schema_version": source["schema_version"],
        "source_file": source_path.relative_to(REPOSITORY_ROOT).as_posix(),
        "source_file_sha256": source_hash,
        "environment_id": source["environment_id"],
        "environment_label": source["environment_label"],
        "coordinate_space": "Unity world XY",
        "units": "Unity world units",
        "meter_scale_verified": False,
        "crs": None,
        "algorithm": "recursive quadratic de Casteljau subdivision at t=0.5",
        "flatness_criterion": (
            "maximum curve-to-chord perpendicular deviation = "
            "0.5 * distance(p1, infinite p0-p2 line)"
        ),
        "zero_chord_policy": "mandatory initial de Casteljau split when p0 == p2 and p1 differs",
        "common_reference_scale_unity_world_units": common_reference_scale,
        "selected_relative_tolerance": selected_relative,
        "selected_absolute_tolerance_unity_world_units": selected_absolute,
        "source_bezier_record_count": len(segment_records),
        "topology_constructed": False,
        "intersections_detected": False,
        "snapping_performed": False,
        "shapes": output_shapes,
    }


def zero_chord_report(
    records: list[dict[str, Any]], details: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    detail_by_id = {detail["segment_id"]: detail for detail in details}
    report = []
    for record in records:
        if record["segment_id"] not in KNOWN_ZERO_CHORD_ANOMALIES:
            continue
        detail = detail_by_id[record["segment_id"]]
        excursion = float(
            np.max(np.linalg.norm(detail["vertices"] - record["p0"], axis=1))
        )
        report.append(
            {
                "segment_id": record["segment_id"],
                "p0": record["p0"].tolist(),
                "p1": record["p1"].tolist(),
                "p2": record["p2"].tolist(),
                "high_accuracy_reference_bezier_length_unity_world_units": detail[
                    "reference_length"
                ],
                "adaptive_vertex_count": detail["vertex_count"],
                "adaptive_polyline_length_unity_world_units": detail[
                    "polyline_length"
                ],
                "absolute_length_error_unity_world_units": detail[
                    "absolute_length_error"
                ],
                "maximum_vertex_excursion_from_p0_unity_world_units": excursion,
                "excursion_preserved": bool(
                    detail["vertex_count"] >= 3 and excursion > 0.0
                ),
            }
        )
    return sorted(report, key=lambda item: item["segment_id"])


def plot_linework(environment_id: int, details: list[dict[str, Any]]) -> None:
    figure, axis = plt.subplots(figsize=(8, 8))
    for detail in details:
        vertices = detail["vertices"]
        axis.plot(vertices[:, 0], vertices[:, 1], color="#c96f5b", linewidth=1.6)
    axis.set_title(f"Environment {environment_id}: selected adaptive linework")
    axis.set_xlabel("Unity world X")
    axis.set_ylabel("Unity world Y")
    axis.set_aspect("equal", adjustable="box")
    axis.grid(False)
    figure.tight_layout()
    figure.savefig(
        QA_DIRECTORY / f"env{environment_id}-adaptive-linework.png",
        dpi=180,
        bbox_inches="tight",
    )
    plt.close(figure)


def plot_convergence(sweeps: dict[int, list[dict[str, Any]]]) -> None:
    figure, axis = plt.subplots(figsize=(8, 5.5))
    for environment_id, sweep in sweeps.items():
        axis.loglog(
            [item["absolute_tolerance_unity_world_units"] for item in sweep],
            [item["aggregate_relative_length_error"] for item in sweep],
            marker="o",
            label=f"Environment {environment_id}",
        )
    axis.axhline(
        AGGREGATE_REFERENCE_ERROR_THRESHOLD,
        color="black",
        linestyle="--",
        linewidth=1.0,
        label="aggregate acceptance threshold",
    )
    axis.invert_xaxis()
    axis.set_xlabel("Absolute flatness tolerance (Unity world units; finer →)")
    axis.set_ylabel("Aggregate relative length error")
    axis.set_title("Phase 7 adaptive linework length convergence")
    axis.grid(True, which="both", alpha=0.25)
    axis.legend()
    figure.tight_layout()
    figure.savefig(QA_DIRECTORY / "phase7-length-convergence.png", dpi=180)
    plt.close(figure)


def write_csv(sweeps: dict[int, list[dict[str, Any]]]) -> None:
    TABLE_DIRECTORY.mkdir(parents=True, exist_ok=True)
    rows = []
    for environment_id, sweep in sweeps.items():
        for item in sweep:
            rows.append({"environment_id": environment_id, **item})
    fieldnames = list(rows[0])
    with (TABLE_DIRECTORY / "phase7-discretization-convergence.csv").open(
        "w", encoding="utf-8", newline=""
    ) as destination:
        writer = csv.DictWriter(destination, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    # Both immutable inputs are hash-gated before any derived output is written.
    loaded = {environment_id: load_source(environment_id) for environment_id in (38, 39)}
    records = {
        environment_id: flatten_segments(source)
        for environment_id, (source, _, _) in loaded.items()
    }
    bounds = {
        environment_id: control_geometry_bounds(environment_records)
        for environment_id, environment_records in records.items()
    }
    common_reference_scale = max(item["diagonal"] for item in bounds.values())
    ordinary_length_floor = common_reference_scale * ORDINARY_LENGTH_SCALE_FLOOR_FACTOR

    for environment_records in records.values():
        for segment in environment_records:
            segment["reference_length"] = quadratic_bezier_reference_length(
                segment["p0"], segment["p1"], segment["p2"]
            )

    sweeps: dict[int, list[dict[str, Any]]] = {}
    all_details: dict[int, list[list[dict[str, Any]]]] = {}
    for environment_id, environment_records in records.items():
        summaries = []
        detail_levels = []
        for relative_tolerance in RELATIVE_TOLERANCES:
            summary, details = analyze_tolerance(
                environment_records,
                relative_tolerance,
                relative_tolerance * common_reference_scale,
                ordinary_length_floor,
            )
            summaries.append(summary)
            detail_levels.append(details)
        add_successive_comparisons(summaries, detail_levels)
        sweeps[environment_id] = summaries
        all_details[environment_id] = detail_levels

    selected_index = next(
        (
            index
            for index in range(len(RELATIVE_TOLERANCES) - 1)
            if all(tolerance_passes(sweeps[env][index]) for env in (38, 39))
        ),
        None,
    )
    if selected_index is None:
        raise RuntimeError(
            "No pre-defined tolerance satisfies the Phase 7 common acceptance rule; "
            "append systematically finer tolerances and document the extension."
        )

    selected_relative = RELATIVE_TOLERANCES[selected_index]
    selected_absolute = selected_relative * common_reference_scale
    selected_details = {
        environment_id: all_details[environment_id][selected_index]
        for environment_id in (38, 39)
    }
    zero_chords = zero_chord_report(records[38], selected_details[38])
    if {item["segment_id"] for item in zero_chords} != KNOWN_ZERO_CHORD_ANOMALIES:
        raise ValueError("Known zero-chord source anomaly set was not preserved")
    if not all(item["excursion_preserved"] for item in zero_chords):
        raise ValueError("A known zero-chord source excursion was collapsed")
    if not all(
        item["absolute_length_error_unity_world_units"] <= selected_absolute
        for item in zero_chords
    ):
        raise ValueError("A zero-chord absolute length error exceeds selected tolerance")

    acceptance_rule = {
        "selection_policy": (
            "coarsest pre-defined tolerance satisfying every criterion for both environments"
        ),
        "aggregate_relative_length_error_maximum": AGGREGATE_REFERENCE_ERROR_THRESHOLD,
        "aggregate_total_length_relative_change_to_next_finer_maximum": SUCCESSIVE_LENGTH_CHANGE_THRESHOLD,
        "ordinary_segment_relative_length_error_maximum": ORDINARY_SEGMENT_RELATIVE_ERROR_THRESHOLD,
        "ordinary_segment_definition": (
            "non-zero p0-p2 chord and reference length >= "
            f"{ORDINARY_LENGTH_SCALE_FLOOR_FACTOR} * common_reference_scale"
        ),
        "zero_chord_rule": (
            "excursion must be preserved and absolute reference-length error must not "
            "exceed the candidate absolute tolerance"
        ),
    }
    convergence_payload = {
        "convergence_schema_version": "1.0.0",
        "phase7_analysis_version": ANALYSIS_VERSION,
        "purpose": "adaptive curve-approximation convergence QA only",
        "coordinate_space": "Unity world XY",
        "units": "Unity world units",
        "meter_scale_verified": False,
        "crs": None,
        "source_hashes": {
            str(environment_id): source_hash
            for environment_id, (_, _, source_hash) in loaded.items()
        },
        "control_geometry_bounds": {str(key): value for key, value in bounds.items()},
        "common_reference_scale_unity_world_units": common_reference_scale,
        "candidate_relative_tolerances": list(RELATIVE_TOLERANCES),
        "candidate_absolute_tolerances_unity_world_units": [
            value * common_reference_scale for value in RELATIVE_TOLERANCES
        ],
        "reference_length_method": {
            "integrand": "norm(B'(t))",
            "interval": [0.0, 1.0],
            "implementation": "scipy.integrate.quad adaptive quadrature",
            "epsabs": QUAD_EPSABS,
            "epsrel": QUAD_EPSREL,
        },
        "acceptance_rule_defined_before_selection": acceptance_rule,
        "environments": {str(key): value for key, value in sweeps.items()},
        "selected_relative_tolerance": selected_relative,
        "selected_absolute_tolerance_unity_world_units": selected_absolute,
        "zero_chord_selected_tolerance_report": zero_chords,
        "not_final_morphology_results": True,
        "intersections_detected": False,
        "snapping_performed": False,
        "topology_constructed": False,
        "graph_constructed": False,
    }

    tested_at = datetime.now(timezone.utc).isoformat()
    selected_payload = {
        "selection_schema_version": "1.0.0",
        "phase7_analysis_version": ANALYSIS_VERSION,
        "algorithm": "recursive quadratic de Casteljau subdivision at t=0.5",
        "flatness_error_criterion": (
            "0.5 * perpendicular distance of p1 from the infinite p0-p2 chord line"
        ),
        "zero_chord_policy": "mandatory initial split before ordinary adaptive testing",
        "selected_relative_tolerance": selected_relative,
        "selected_absolute_tolerance_unity_world_units": selected_absolute,
        "common_reference_scale_unity_world_units": common_reference_scale,
        "acceptance_rule": acceptance_rule,
        "convergence_result": {
            str(environment_id): sweeps[environment_id][selected_index]
            for environment_id in (38, 39)
        },
        "zero_chord_report": zero_chords,
        "tested_at_utc": tested_at,
        "software_versions": {
            "python": platform.python_version(),
            "numpy": importlib.metadata.version("numpy"),
            "scipy": importlib.metadata.version("scipy"),
            "matplotlib": importlib.metadata.version("matplotlib"),
        },
        "source_hashes": convergence_payload["source_hashes"],
        "coordinate_space": "Unity world XY",
        "units": "Unity world units",
        "meter_scale_verified": False,
        "crs": None,
        "selected_tolerance_purpose": "curve approximation, not topology",
    }

    QA_DIRECTORY.mkdir(parents=True, exist_ok=True)
    write_json(QA_DIRECTORY / "phase7-discretization-convergence.json", convergence_payload)
    write_json(QA_DIRECTORY / "phase7-selected-discretization.json", selected_payload)
    write_csv(sweeps)

    for environment_id in (38, 39):
        source, source_path, source_hash = loaded[environment_id]
        artifact = selected_linework_artifact(
            source,
            source_path,
            source_hash,
            selected_relative,
            selected_absolute,
            records[environment_id],
            selected_details[environment_id],
            common_reference_scale,
        )
        write_json(
            PROCESSED_DIRECTORY / f"env{environment_id}_detailed_linework.json",
            artifact,
        )
        plot_linework(environment_id, selected_details[environment_id])
    plot_convergence(sweeps)

    print("Canonical raw SHA-256 verification: PASS")
    print(f"Common reference scale: {common_reference_scale:.15g} Unity world units")
    print(
        "Candidate absolute tolerances: "
        + ", ".join(
            f"{value * common_reference_scale:.15g}" for value in RELATIVE_TOLERANCES
        )
    )
    print(
        f"Selected tolerance: relative={selected_relative:.15g}, "
        f"absolute={selected_absolute:.15g} Unity world units"
    )
    for environment_id in (38, 39):
        result = sweeps[environment_id][selected_index]
        print(
            f"Environment {environment_id}: vertices={result['total_polyline_vertex_count']}, "
            f"aggregate_relative_error={result['aggregate_relative_length_error']:.15g}, "
            "successive_relative_change="
            f"{result['aggregate_total_length_relative_change_to_next_finer']:.15g}, "
            "worst_ordinary_segment_relative_error="
            f"{result['maximum_ordinary_segment_relative_length_error']:.15g}"
        )
    print(f"Zero-chord excursions preserved: {len(zero_chords)}/5")
    print("Phase 7 adaptive discretization and convergence artifacts: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
