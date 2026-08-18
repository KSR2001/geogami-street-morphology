"""Create the conservative Phase 9 Unity navigability-review package.

This phase preserves Phase 8 intersection mathematics.  It adds only an
evidence record, a source-derived horizontal mapping into each 3D prefab, and
manual-review identifiers.  It deliberately does not construct topology.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import subprocess
import tempfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

os.environ.setdefault(
    "MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "geogami-matplotlib")
)
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[1]
RAW_HASHES = {
    38: "43ea446a4a88e9f3d594fb8b72742f5d4b2a1ee8a03ebf8350c4c3cce45c5819",
    39: "e5dbce6b4d88656c9e0f3bbf6a814434f64b0fbe9b3ff1864ea3fafaf0883602",
}
REVIEW_INPUT = ROOT / "outputs/tables/phase8-3d-crossing-review.csv"
EVENT_INPUT = ROOT / "outputs/tables/phase8-intersection-events.csv"
PHASE8_QA = ROOT / "outputs/qa/phase8-intersection-reconstruction.json"
TABLE_OUTPUT = ROOT / "outputs/tables/phase9-3d-navigability-review.csv"
QA_OUTPUT = ROOT / "outputs/qa/phase9-3d-navigability-validation.json"
MANUAL_OUTPUT = ROOT / "docs/phase9-manual-unity-review.md"
DECISIONS = (
    "connected_same_level",
    "grade_separated_not_connected",
    "manual_review_required",
)
MANUAL_REVIEW_METHOD = "direct researcher inspection of the 3D Unity environments"
MANUAL_EVIDENCE_SUMMARY = (
    "Researcher manually inspected the corresponding crossing in the 3D Unity "
    "environment and confirmed both road trajectories meet on the same navigable "
    "surface with no road-over-road or road-under-road grade separation."
)

# Map2D.cs obtains Renderer.bounds from a rotated built-in Unity Plane (10 x 10)
# and maps those bounds affinely to the generated TerrainData dimensions.  The
# tiny Env38 scale difference is retained rather than rounded away.
MAPPING = {
    38: {
        "map_bounds_min_x": 0.112285,
        "map_bounds_min_y": -165.50009,
        "map_bounds_size_x": 440.00023,
        "map_bounds_size_y": 531.00018,
        "terrain_size_x": 440.4167,
        "terrain_size_z": 531.4167,
        "terrain_prefab_local_x": -276.364,
        "terrain_prefab_local_z": -283.2021,
    },
    39: {
        "map_bounds_min_x": 0.1124,
        "map_bounds_min_y": -165.5,
        "map_bounds_size_x": 440.0,
        "map_bounds_size_y": 531.0,
        "terrain_size_x": 440.4167,
        "terrain_size_z": 531.4167,
        "terrain_prefab_local_x": -276.364,
        "terrain_prefab_local_z": -283.2021,
    },
}

CSV_FIELDS = [
    "event_id",
    "review_location_id",
    "environment_id",
    "event_type",
    "x",
    "y",
    "segment_a_id",
    "segment_b_id",
    "shape_a_id",
    "shape_b_id",
    "t_a",
    "t_b",
    "residual",
    "same_shape",
    "source_anomaly_involved",
    "mapped_3d_position_if_available",
    "navigability_decision",
    "evidence_type",
    "unity_source_path",
    "unity_object_or_hierarchy_if_available",
    "evidence_summary",
    "manual_review_notes",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_output(repository: Path, *arguments: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repository), *arguments],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return result.stdout.rstrip()


def bool_value(value: str) -> bool:
    if value == "True":
        return True
    if value == "False":
        return False
    raise ValueError(f"Unexpected boolean CSV value: {value!r}")


def affine_map_to_prefab_local_xz(
    mapping: dict[str, float], x: float, y: float
) -> tuple[float, float]:
    """Map source XY to prefab-local XZ using documented Map2D parameters."""
    mapped_x = mapping["terrain_prefab_local_x"] + (
        (x - mapping["map_bounds_min_x"])
        / mapping["map_bounds_size_x"]
        * mapping["terrain_size_x"]
    )
    mapped_z = mapping["terrain_prefab_local_z"] + (
        (y - mapping["map_bounds_min_y"])
        / mapping["map_bounds_size_y"]
        * mapping["terrain_size_z"]
    )
    return mapped_x, mapped_z


def mapped_prefab_local_xz(environment_id: int, x: float, y: float) -> tuple[float, float]:
    return affine_map_to_prefab_local_xz(MAPPING[environment_id], x, y)


def required_paths(unity_project: Path) -> list[Path]:
    paths = [
        REVIEW_INPUT,
        EVENT_INPUT,
        PHASE8_QA,
        ROOT / "data/processed/env38_detailed_linework.json",
        ROOT / "data/processed/env39_detailed_linework.json",
        ROOT / "outputs/qa/env38-interior-crossings-review.png",
        ROOT / "outputs/qa/env39-interior-crossings-review.png",
        unity_project / "Assets/Tools/VirtualEnvironmentCreation/2DMapPrefabs/2D Map Vir 38.prefab",
        unity_project / "Assets/Tools/VirtualEnvironmentCreation/2DMapPrefabs/2D Map Vir 39.prefab",
        unity_project / "Assets/Prefabs/VIrtualEnvironments/VirEnv_38.prefab",
        unity_project / "Assets/Prefabs/VIrtualEnvironments/VirEnv_39.prefab",
        unity_project / "Assets/Terrain Data/Terrain_Data_VirEnv38.asset",
        unity_project / "Assets/Terrain Data/Terrain_Data_VirEnv39.asset",
        unity_project / "Assets/Tools/VirtualEnvironmentCreation/Scripts/Map2D.cs",
        unity_project / "ProjectSettings/ProjectVersion.txt",
    ]
    missing = [path for path in paths if not path.is_file()]
    if missing:
        raise FileNotFoundError("Missing Phase 9 inputs:\n" + "\n".join(map(str, missing)))
    return paths


def load_review_events() -> list[dict[str, Any]]:
    with REVIEW_INPUT.open(encoding="utf-8", newline="") as source:
        rows = list(csv.DictReader(source))
    if len(rows) != 48:
        raise ValueError(f"Expected 48 Phase 8 review events, found {len(rows)}")
    if any(row["event_type"] != "interior_interior_crossing" for row in rows):
        raise ValueError("Phase 8 review input contains a non-interior crossing")
    counts = Counter(int(row["environment_id"]) for row in rows)
    if counts != Counter({38: 28, 39: 20}):
        raise ValueError(f"Unexpected Phase 8 environment counts: {dict(counts)}")
    if len({row["event_id"] for row in rows}) != len(rows):
        raise ValueError("Phase 8 review event IDs are not unique")
    return rows


def label_events(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    labelled: list[dict[str, Any]] = []
    counters = Counter()
    for row in rows:
        environment_id = int(row["environment_id"])
        counters[environment_id] += 1
        review_id = f"E{environment_id}-C{counters[environment_id]:03d}"
        mapped_x, mapped_z = mapped_prefab_local_xz(
            environment_id, float(row["x"]), float(row["y"])
        )
        unity_paths = (
            f"Assets/Tools/VirtualEnvironmentCreation/2DMapPrefabs/2D Map Vir {environment_id}.prefab; "
            f"Assets/Prefabs/VIrtualEnvironments/VirEnv_{environment_id}.prefab; "
            f"Assets/Terrain Data/Terrain_Data_VirEnv{environment_id}.asset; "
            "Assets/Tools/VirtualEnvironmentCreation/Scripts/Map2D.cs"
        )
        labelled.append(
            {
                **row,
                "environment_id": environment_id,
                "x": float(row["x"]),
                "y": float(row["y"]),
                "t_a": float(row["t_a"]),
                "t_b": float(row["t_b"]),
                "residual": float(row["residual"]),
                "review_location_id": review_id,
                "same_shape": bool_value(row["same_shape"]),
                "source_anomaly_involved": bool_value(row["source_anomaly_involved"]),
                "mapped_3d_position_if_available": (
                    f"VirEnv_{environment_id} prefab-local XZ "
                    f"({mapped_x:.9f}, {mapped_z:.9f}); Y unavailable"
                ),
                "mapped_prefab_local_x": mapped_x,
                "mapped_prefab_local_y": None,
                "mapped_prefab_local_z": mapped_z,
                "navigability_decision": "connected_same_level",
                "evidence_type": "manual_unity_3d_visual_inspection",
                "unity_source_path": unity_paths,
                "unity_object_or_hierarchy_if_available": (
                    f"VirEnv_{environment_id}/Terrain; Bridges hierarchy present, "
                    "but no canonical road-segment association is serialized"
                ),
                "evidence_summary": MANUAL_EVIDENCE_SUMMARY,
                "manual_review_notes": (
                    "Manual review completed by the researcher. Both road trajectories were "
                    "observed to meet on the same navigable surface; no road-over-road or "
                    "road-under-road grade separation was observed."
                ),
            }
        )
    return labelled


def write_csv(rows: list[dict[str, Any]]) -> None:
    TABLE_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with TABLE_OUTPUT.open("w", encoding="utf-8", newline="") as destination:
        writer = csv.DictWriter(destination, fieldnames=CSV_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_manual_review(rows: list[dict[str, Any]]) -> None:
    lines = [
        "# Phase 9 Manual Unity Review",
        "",
        "Phase 9 is **COMPLETE**. Static repository evidence initially could not establish "
        "a final navigability decision for the 48 locations, so the checklist below was used "
        "for direct researcher inspection in Unity. All 48 reviews are now resolved. This "
        "document remains the audit trail; it must not be used to edit Unity assets or "
        "construct topology.",
        "",
        "## Review procedure",
        "",
        "1. Open the matching canonical `2D Map Vir 38` or `2D Map Vir 39` prefab and "
        "the corresponding `VirEnv_38` or `VirEnv_39` prefab without saving changes.",
        "2. Use the Phase 9 figure and source XY coordinate to identify both trajectories. "
        "The recorded prefab-local XZ value may be used as a horizontal locator; its Y is "
        "intentionally unavailable.",
        "3. Inspect the location from side, top, and perspective views. Check Terrain, "
        "TerrainCollider, bridge MeshCollider objects, visible continuity, and actual "
        "participant movement across each approach where safe to do so.",
        "4. Record `connected_same_level` only if both trajectories meet on one traversable "
        "surface. Record `grade_separated_not_connected` only if one passes above/below the "
        "other or a physical barrier/gap prevents the junction. Otherwise retain "
        "`manual_review_required` and describe the missing evidence.",
        "5. Do not move objects, rebake navigation, save prefabs/scenes, snap coordinates, "
        "split roads, or create graph nodes during review.",
        "",
        "## Completed review result",
        "",
        "The researcher manually inspected all 48 locations in the 3D Unity environments. "
        "All 48 were confirmed `connected_same_level`; none was road-over-road or "
        "road-under-road grade-separated. The five collider-backed bridges found in each "
        "environment during static inspection do not invalidate any reviewed road-road junction.",
        "",
        "## Reviewed locations",
        "",
    ]
    for row in rows:
        lines.extend(
            [
                f"### {row['review_location_id']}",
                "",
                f"- Environment: Env{row['environment_id']}",
                f"- Source XY: `({row['x']:.15g}, {row['y']:.15g})`",
                f"- Mapped 3D locator: `{row['mapped_3d_position_if_available']}`",
                f"- Segments: `{row['segment_a_id']}` and `{row['segment_b_id']}`",
                f"- Shapes: `{row['shape_a_id']}` and `{row['shape_b_id']}`",
                f"- Same Shape: `{str(row['same_shape']).lower()}`",
                f"- Source anomaly involved: `{str(row['source_anomaly_involved']).lower()}`",
                "- Check in 3D: follow both road trajectories through the labelled coordinate; "
                "inspect vertical separation, bridge/deck membership, TerrainCollider continuity, "
                "barriers, and whether movement can transfer between the two roads.",
                "- `connected_same_level` observation: both approaches visibly meet at one "
                "elevation and a participant can traverse from either trajectory onto the other.",
                "- `grade_separated_not_connected` observation: one trajectory passes above or "
                "below the other, or a physical separation prevents transfer at the crossing.",
                "- Review status: `completed`",
                "- Decision: `connected_same_level`",
                "- Evidence: `manual Unity 3D visual inspection`",
                f"- Evidence summary: {row['evidence_summary']}",
                "",
            ]
        )
    MANUAL_OUTPUT.write_text("\n".join(lines), encoding="utf-8")


def linework(environment_id: int) -> list[list[list[float]]]:
    path = ROOT / f"data/processed/env{environment_id}_detailed_linework.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    return [
        segment["adaptive_vertices_xy"]
        for shape in payload["shapes"]
        for segment in shape["segments"]
    ]


def plot_review(environment_id: int, rows: list[dict[str, Any]]) -> None:
    selected = [row for row in rows if int(row["environment_id"]) == environment_id]
    figure, axis = plt.subplots(figsize=(12, 10))
    for vertices in linework(environment_id):
        axis.plot(
            [point[0] for point in vertices],
            [point[1] for point in vertices],
            color="#9b9b9b",
            linewidth=1.05,
            zorder=1,
        )
    axis.scatter(
        [float(row["x"]) for row in selected],
        [float(row["y"]) for row in selected],
        marker="o",
        facecolors="#22c55e",
        edgecolors="#14532d",
        linewidths=1.0,
        s=42,
        label=f"connected_same_level ({len(selected)})",
        zorder=3,
    )
    axis.set_title(
        f"Environment {environment_id}: Phase 9 numbered 3D navigability review locations"
    )
    axis.set_xlabel("Unity world X")
    axis.set_ylabel("Unity world Y")
    axis.set_aspect("equal", adjustable="box")
    axis.legend(loc="best", fontsize=9)
    axis.margins(0.05)
    figure.tight_layout()
    figure.canvas.draw()

    # Place full review IDs without label-on-label collisions.  This is a
    # display-space operation only; it does not alter any source coordinate.
    directions = [
        (1, 1), (1, -1), (-1, 1), (-1, -1),
        (1, 0), (-1, 0), (0, 1), (0, -1),
    ]
    candidates = [
        (direction[0] * radius, direction[1] * radius)
        for radius in (8, 14, 22, 32, 44, 58, 76, 96)
        for direction in directions
    ]
    renderer = figure.canvas.get_renderer()
    axes_box = axis.get_window_extent(renderer=renderer).shrunk(0.98, 0.98)
    occupied = []
    def nearest_distance(row: dict[str, Any]) -> float:
        return min(
            (
                (float(row["x"]) - float(other["x"])) ** 2
                + (float(row["y"]) - float(other["y"])) ** 2
            ) ** 0.5
            for other in selected
            if other is not row
        )

    # Give the most crowded crossings first choice of nearby label positions.
    for row in sorted(selected, key=nearest_distance):
        accepted = None
        for offset in candidates:
            horizontal = "left" if offset[0] >= 0 else "right"
            vertical = "bottom" if offset[1] >= 0 else "top"
            annotation = axis.annotate(
                row["review_location_id"],
                (float(row["x"]), float(row["y"])),
                xytext=offset,
                textcoords="offset points",
                fontsize=7.2,
                ha=horizontal,
                va=vertical,
                color="#14532d",
                zorder=4,
            )
            figure.canvas.draw()
            box = annotation.get_window_extent(renderer=renderer).expanded(1.04, 1.12)
            if axes_box.contains(*box.get_points()[0]) and axes_box.contains(
                *box.get_points()[1]
            ) and not any(box.overlaps(existing) for existing in occupied):
                accepted = box
                axis.annotate(
                    "",
                    (float(row["x"]), float(row["y"])),
                    xytext=offset,
                    textcoords="offset points",
                    arrowprops={"arrowstyle": "-", "color": "#15803d", "lw": 0.55},
                    zorder=3,
                )
                break
            annotation.remove()
        if accepted is None:
            raise RuntimeError(
                f"Could not place non-overlapping figure label {row['review_location_id']}"
            )
        occupied.append(accepted)

    output = ROOT / f"outputs/qa/env{environment_id}-phase9-navigability-review.png"
    figure.savefig(output, dpi=200, bbox_inches="tight")
    plt.close(figure)


def write_json(
    rows: list[dict[str, Any]],
    unity_repository: Path,
    unity_project: Path,
    unity_head: str,
    unity_status: str,
    unity_version: dict[str, str],
) -> None:
    decisions = Counter(row["navigability_decision"] for row in rows)
    def complete_counts(selected_rows: list[dict[str, Any]]) -> dict[str, int]:
        selected_decisions = Counter(row["navigability_decision"] for row in selected_rows)
        return {decision: selected_decisions[decision] for decision in DECISIONS}

    environment_counts = {
        str(environment_id): complete_counts(
            [row for row in rows if int(row["environment_id"]) == environment_id]
        )
        for environment_id in (38, 39)
    }
    cross_shape = [row for row in rows if not row["same_shape"]]
    anomaly = [row for row in rows if row["source_anomaly_involved"]]
    payload = {
        "phase9_validation_schema_version": "1.0.0",
        "phase9_analysis_version": "1.1.0",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_hashes": {str(key): value for key, value in RAW_HASHES.items()},
        "phase8_event_inventory": {
            "path": "outputs/tables/phase8-intersection-events.csv",
            "sha256": sha256(EVENT_INPUT),
        },
        "phase8_review_inventory": {
            "path": "outputs/tables/phase8-3d-crossing-review.csv",
            "sha256": sha256(REVIEW_INPUT),
        },
        "unity_provenance": {
            "repository": str(unity_repository),
            "project_root": str(unity_project),
            "head": unity_head,
            "working_tree_dirty": bool(unity_status),
            "git_status_short": unity_status.splitlines(),
            "unity_version": unity_version,
            "inspection_mode": "read_only_static_repository_inspection",
        },
        "coordinate_mapping": {
            "source_coordinate_space": "Unity world XY from Shapes2D.GetPathWorldSegments()",
            "target_coordinate_space": "VirEnv prefab-local XZ; vertical Y not derived",
            "method": (
                "Map2D.Run obtains the 2D root Renderer.bounds; Map2D maps x/y fractions "
                "affinely to TerrainData size.x/size.z and adds the Terrain transform position."
            ),
            "formula": {
                "X_prefab_local": "terrain_local_x + ((x - bounds_min_x) / bounds_size_x) * terrain_size_x",
                "Z_prefab_local": "terrain_local_z + ((y - bounds_min_y) / bounds_size_y) * terrain_size_z",
                "Y_prefab_local": None,
            },
            "parameters_by_environment": {str(key): value for key, value in MAPPING.items()},
            "limitations": (
                "The static mapping establishes horizontal placement only. Terrain height, bridge "
                "deck occupancy, and navigable continuity at each crossing are not derivable from "
                "the Phase 8 event row or a serialized road-object hierarchy."
            ),
        },
        "evidence_policy": {
            "hierarchy": [
                "explicit 3D road centerline/elevation data",
                "3D mesh/collider continuity",
                "canonical prefab/scene hierarchy",
                "source proof of a common road plane with no relevant grade separation",
                "manual Unity visual and movement inspection",
            ],
            "available": [
                "canonical 2D Shapes2D prefabs",
                "Map2D affine horizontal mapping source",
                "generated 3D prefabs and TerrainCollider",
                "five serialized MeshCollider bridge objects in each environment",
            ],
            "insufficient_for_final_decision": [
                "roads are encoded as terrain alphamap texture, not semantic road meshes",
                "no road-segment-to-3D-object association is serialized",
                "no road connectivity graph or road-specific nav surface is present",
                "bridge generation uses endpoint chords rather than lossless quadratic curves",
            ],
            "static_classification_result": (
                "Static repository evidence was insufficient for all 48 events; direct "
                "manual Unity inspection was required."
            ),
            "final_classification_result": (
                "All 48 events are connected_same_level based on completed direct "
                "researcher inspection of the 3D Unity environments."
            ),
        },
        "manual_review_completed": True,
        "manual_review_method": MANUAL_REVIEW_METHOD,
        "manual_review_scope": {
            "unique_locations": len({row["review_location_id"] for row in rows}),
            "environment_38": sum(int(row["environment_id"]) == 38 for row in rows),
            "environment_39": sum(int(row["environment_id"]) == 39 for row in rows),
        },
        "bridge_evidence_clarification": (
            "Static inspection found five collider-backed bridges in each environment but "
            "could not reliably associate them with Phase 8 crossing events. Subsequent "
            "direct manual Unity inspection confirmed that none of the 48 reviewed road-road "
            "crossings is road-over-road or road-under-road grade-separated."
        ),
        "counts": {
            "total_events_reviewed": len(rows),
            "connected_same_level": decisions["connected_same_level"],
            "grade_separated_not_connected": decisions["grade_separated_not_connected"],
            "manual_review_required": decisions["manual_review_required"],
            "by_environment": environment_counts,
            "cross_shape_event_count": len(cross_shape),
            "cross_shape": complete_counts(cross_shape),
            "source_anomaly_involved_event_count": len(anomaly),
            "source_anomaly_involved": complete_counts(anomaly),
            "unique_review_locations": len({row["review_location_id"] for row in rows}),
        },
        "review_location_grouping": {
            "policy": (
                "Only numerically equivalent Phase 8 mathematical coordinates may share an ID; "
                "no snapping or near-coordinate merge is permitted."
            ),
            "result": "all 48 coordinates are distinct under the Phase 8 numerical policy",
            "topology_node_semantics": False,
        },
        "individual_event_decisions": rows,
        "evidence_paths": [
            "Assets/Tools/VirtualEnvironmentCreation/2DMapPrefabs/2D Map Vir 38.prefab",
            "Assets/Tools/VirtualEnvironmentCreation/2DMapPrefabs/2D Map Vir 39.prefab",
            "Assets/Prefabs/VIrtualEnvironments/VirEnv_38.prefab",
            "Assets/Prefabs/VIrtualEnvironments/VirEnv_39.prefab",
            "Assets/Terrain Data/Terrain_Data_VirEnv38.asset",
            "Assets/Terrain Data/Terrain_Data_VirEnv39.asset",
            "Assets/Tools/VirtualEnvironmentCreation/Scripts/Map2D.cs",
            "ProjectSettings/ProjectVersion.txt",
        ],
        "acceptance_status": "COMPLETE",
        "acceptance_reason": (
            "All 48 mathematically reconstructed interior road crossings have evidence-backed "
            "3D navigability decisions; all are confirmed connected_same_level and none remains "
            "unresolved."
        ),
        "snapping_performed": False,
        "topology_constructed": False,
        "road_lines_split": False,
        "graph_nodes_created": False,
        "networkx_graph_created": False,
        "osmnx_graph_created": False,
        "final_morphology_metrics_calculated": False,
        "meter_scale_verified": False,
        "crs": None,
    }
    QA_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    QA_OUTPUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def validate_final_outputs(source_rows: list[dict[str, str]]) -> None:
    """Validate final Phase 9 decisions without recomputing Phase 8 geometry."""
    with TABLE_OUTPUT.open(encoding="utf-8", newline="") as source:
        csv_rows = list(csv.DictReader(source))
    qa = json.loads(QA_OUTPUT.read_text(encoding="utf-8"))
    json_rows = qa["individual_event_decisions"]

    expected_review_ids = {
        *(f"E38-C{index:03d}" for index in range(1, 29)),
        *(f"E39-C{index:03d}" for index in range(1, 21)),
    }
    if len(csv_rows) != 48 or len(json_rows) != 48:
        raise ValueError("Final Phase 9 output must contain exactly 48 decisions")
    if {row["review_location_id"] for row in csv_rows} != expected_review_ids:
        raise ValueError("Final Phase 9 review-location inventory is incomplete")
    if Counter(row["review_location_id"] for row in csv_rows).most_common(1)[0][1] != 1:
        raise ValueError("A final review_location_id maps to more than one event")

    source_by_id = {row["event_id"]: row for row in source_rows}
    csv_by_id = {row["event_id"]: row for row in csv_rows}
    json_by_id = {row["event_id"]: row for row in json_rows}
    if set(source_by_id) != set(csv_by_id) or set(source_by_id) != set(json_by_id):
        raise ValueError("Final Phase 9 event IDs differ from the Phase 8 review inventory")
    for event_id, source_row in source_by_id.items():
        csv_row = csv_by_id[event_id]
        json_row = json_by_id[event_id]
        if csv_row["x"] != source_row["x"] or csv_row["y"] != source_row["y"]:
            raise ValueError(f"Phase 8 CSV coordinates changed for {event_id}")
        if float(json_row["x"]) != float(source_row["x"]) or float(
            json_row["y"]
        ) != float(source_row["y"]):
            raise ValueError(f"Phase 8 JSON coordinates changed for {event_id}")
        if csv_row["navigability_decision"] != json_row["navigability_decision"]:
            raise ValueError(f"CSV/JSON decision mismatch for {event_id}")

    decision_counts = Counter(row["navigability_decision"] for row in csv_rows)
    if decision_counts != Counter({"connected_same_level": 48}):
        raise ValueError(f"Unexpected final decision counts: {dict(decision_counts)}")
    environment_counts = Counter(
        int(row["environment_id"])
        for row in csv_rows
        if row["navigability_decision"] == "connected_same_level"
    )
    if environment_counts != Counter({38: 28, 39: 20}):
        raise ValueError(f"Unexpected final environment counts: {dict(environment_counts)}")
    cross_shape_count = sum(row["same_shape"] == "False" for row in csv_rows)
    if cross_shape_count != 23:
        raise ValueError(
            f"Phase 8 inventory yielded {cross_shape_count} cross-Shape review events, expected 23"
        )
    if any(row["source_anomaly_involved"] != "False" for row in csv_rows):
        raise ValueError("Unexpected source anomaly in the Phase 9 review inventory")
    if not qa["manual_review_completed"] or qa["acceptance_status"] != "COMPLETE":
        raise ValueError("Phase 9 QA does not record completed manual review and acceptance")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--unity-project",
        type=Path,
        required=True,
        help="read-only path to the GeoGami-Vir-Env Unity project root",
    )
    arguments = parser.parse_args()
    unity_project = arguments.unity_project.resolve()
    unity_repository = unity_project.parent
    required_paths(unity_project)

    for environment_id, expected in RAW_HASHES.items():
        actual = sha256(ROOT / f"data/raw/env{environment_id}_bezier.json")
        if actual != expected:
            raise ValueError(
                f"Env{environment_id} raw hash changed: expected {expected}, found {actual}"
            )

    phase8 = json.loads(PHASE8_QA.read_text(encoding="utf-8"))
    threshold = phase8["numerical_refinement"][
        "absolute_residual_threshold_unity_world_units"
    ]
    source_rows = load_review_events()
    rows = label_events(source_rows)
    for index, first in enumerate(rows):
        for second in rows[index + 1 :]:
            if first["environment_id"] != second["environment_id"]:
                continue
            distance = (
                (float(first["x"]) - float(second["x"])) ** 2
                + (float(first["y"]) - float(second["y"])) ** 2
            ) ** 0.5
            if distance <= threshold:
                raise ValueError(
                    "Review-location grouping is required but was not assigned for "
                    f"{first['event_id']} and {second['event_id']}"
                )

    unity_head = git_output(unity_repository, "rev-parse", "HEAD")
    unity_status = git_output(unity_repository, "status", "--short")
    version_lines = (
        unity_project / "ProjectSettings/ProjectVersion.txt"
    ).read_text(encoding="utf-8").splitlines()
    unity_version = {
        line.split(":", 1)[0]: line.split(":", 1)[1].strip()
        for line in version_lines
        if ":" in line
    }
    write_csv(rows)
    write_manual_review(rows)
    for environment_id in (38, 39):
        plot_review(environment_id, rows)
    write_json(
        rows,
        unity_repository,
        unity_project,
        unity_head,
        unity_status,
        unity_version,
    )
    validate_final_outputs(source_rows)
    print("Canonical raw SHA-256 verification: PASS")
    print(f"Phase 8 interior events preserved: {len(rows)}")
    print("Unique review locations: 48")
    print("Decisions: connected=48, grade-separated=0, manual=0")
    print("CSV/JSON decision and Phase 8 coordinate validation: PASS")
    print("Phase 9: COMPLETE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
