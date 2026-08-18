"""Phase 13 audit of frozen Phase 12 morphology results."""

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
from scipy.stats import rankdata

os.environ.setdefault(
    "MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "geogami-matplotlib")
)
import matplotlib.pyplot as plt

try:
    from .circuity_audit import decompose_circuity_rows, rank_contributors
    from .network_graph import read_graphml
except ImportError:  # pragma: no cover - direct execution
    from circuity_audit import decompose_circuity_rows, rank_contributors
    from network_graph import read_graphml


ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "outputs/tables"
QA = ROOT / "outputs/qa"
GRAPHS = ROOT / "data/graphs"
NUMERICAL_TOLERANCE = 1e-12
EXPECTED_PRIMARY = {
    38: {
        "H_o_nats": 3.0131094587621066,
        "H_w_nats": 3.1312256499064475,
        "phi": 0.4518145655192265,
        "aggregate_circuity": 1.0213150770501422,
        "mean_edge_circuity": 1.0183127736327648,
        "median_edge_circuity": 1.002327065680324,
        "node_count": 60,
        "street_segment_count": 84,
        "dead_end_count": 21,
        "three_way_count": 9,
        "four_way_count": 30,
    },
    39: {
        "H_o_nats": 1.5143534129805727,
        "H_w_nats": 1.381012158514464,
        "phi": 0.9966031867759313,
        "aggregate_circuity": 1.0233180457073998,
        "mean_edge_circuity": 1.0093689453989059,
        "median_edge_circuity": 1.0,
        "node_count": 51,
        "street_segment_count": 70,
        "dead_end_count": 19,
        "three_way_count": 7,
        "four_way_count": 25,
    },
}
RAW_HASHES = {
    38: "43ea446a4a88e9f3d594fb8b72742f5d4b2a1ee8a03ebf8350c4c3cce45c5819",
    39: "e5dbce6b4d88656c9e0f3bbf6a814434f64b0fbe9b3ff1864ea3fafaf0883602",
}
EXPECTED_MAX_EDGE_CIRCUITY = {
    38: 1.2432551101540879,
    39: 1.358318066052315,
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def verify_phase12() -> tuple[dict[int, dict[str, float]], dict[str, Any]]:
    primary_path = TABLES / "phase12-primary-morphology-metrics.csv"
    edge_path = TABLES / "phase12-edge-circuity.csv"
    qa_path = QA / "phase12-final-morphology-results.json"
    primary_rows = load_csv(primary_path)
    phase12_qa = load_json(qa_path)
    if len(primary_rows) != 2 or phase12_qa["acceptance_status"] != "PASS":
        raise ValueError("Frozen Phase 12 acceptance record is invalid")

    primary: dict[int, dict[str, float]] = {}
    for row in primary_rows:
        environment_id = int(row["environment_id"])
        primary[environment_id] = {}
        for field, expected in EXPECTED_PRIMARY[environment_id].items():
            observed = float(row[field])
            if observed != expected:
                raise ValueError(
                    f"Frozen Phase 12 value changed: Env{environment_id} {field}={observed}"
                )
            primary[environment_id][field] = observed
            qa_value = phase12_qa["results"][str(environment_id)]
            if field in qa_value and float(qa_value[field]) != expected:
                raise ValueError(f"Phase 12 QA disagrees for Env{environment_id} {field}")

    if phase12_qa["hypothesis_assessment"]["H4"]["assessment"] != "not_supported":
        raise ValueError("Frozen H4 outcome changed")
    for environment_id, expected in EXPECTED_MAX_EDGE_CIRCUITY.items():
        observed = phase12_qa["results"][str(environment_id)][
            "individual_edge_circuity_summary"
        ]["maximum"]
        if observed != expected:
            raise ValueError(f"Frozen Env{environment_id} maximum circuity changed")
    edge_rows = load_csv(edge_path)
    if len(edge_rows) != 154:
        raise ValueError("Frozen Phase 12 edge-circuity row count changed")

    provenance = {
        "phase12_files": {
            primary_path.relative_to(ROOT).as_posix(): sha256(primary_path),
            edge_path.relative_to(ROOT).as_posix(): sha256(edge_path),
            qa_path.relative_to(ROOT).as_posix(): sha256(qa_path),
        },
        "raw_hashes": {},
    }
    for environment_id, expected_hash in RAW_HASHES.items():
        path = ROOT / f"data/raw/env{environment_id}_bezier.json"
        actual = sha256(path)
        if actual != expected_hash:
            raise ValueError(f"Env{environment_id} raw hash changed")
        provenance["raw_hashes"][str(environment_id)] = actual
    return primary, {"provenance": provenance, "phase12_qa": phase12_qa, "edge_rows": edge_rows, "primary_rows": primary_rows}


def spearman_without_p_value(x: list[float], y: list[float]) -> float:
    """Calculate Spearman rank correlation without inferential output."""

    x_rank = rankdata(np.asarray(x, dtype=float), method="average")
    y_rank = rankdata(np.asarray(y, dtype=float), method="average")
    return float(np.corrcoef(x_rank, y_rank)[0, 1])


def distribution_audit(values: list[float]) -> dict[str, Any]:
    array = np.asarray(values, dtype=float)
    return {
        "minimum": float(np.min(array)),
        "q25": float(np.quantile(array, 0.25)),
        "median": float(np.median(array)),
        "q75": float(np.quantile(array, 0.75)),
        "q90": float(np.quantile(array, 0.90)),
        "q95": float(np.quantile(array, 0.95)),
        "maximum": float(np.max(array)),
        "approximately_one_within_1e-6_count": int(np.sum(np.abs(array - 1.0) <= 1e-6)),
        "approximately_one_within_1e-6_proportion": float(np.mean(np.abs(array - 1.0) <= 1e-6)),
        "greater_than_1_01_count": int(np.sum(array > 1.01)),
        "greater_than_1_01_proportion": float(np.mean(array > 1.01)),
        "greater_than_1_05_count": int(np.sum(array > 1.05)),
        "greater_than_1_05_proportion": float(np.mean(array > 1.05)),
        "greater_than_1_10_count": int(np.sum(array > 1.10)),
        "greater_than_1_10_proportion": float(np.mean(array > 1.10)),
        "greater_than_1_20_count": int(np.sum(array > 1.20)),
        "greater_than_1_20_proportion": float(np.mean(array > 1.20)),
    }


def plot_high_contributors(
    environment_id: int,
    graph,
    ranked: list[dict[str, Any]],
) -> None:
    top_ids = {row["simplified_edge_id"] for row in ranked[:10]}
    label_ids = {row["simplified_edge_id"] for row in ranked[:5]}
    fig, ax = plt.subplots(figsize=(10, 8), constrained_layout=True)
    for _, _, data in graph.edges(data=True):
        geometry = data["geometry"]
        edge_id = data["simplified_edge_id"]
        highlighted = edge_id in top_ids
        ax.plot(
            [point[0] for point in geometry],
            [point[1] for point in geometry],
            color="#d64545" if highlighted else "#b8c2cc",
            linewidth=2.4 if highlighted else 0.8,
            alpha=1.0 if highlighted else 0.7,
            zorder=2 if highlighted else 1,
        )
        if edge_id in label_ids:
            midpoint = geometry[len(geometry) // 2]
            ax.annotate(
                edge_id,
                xy=midpoint,
                xytext=(4, 4),
                textcoords="offset points",
                fontsize=6.5,
                color="#7b1e1e",
                bbox={"boxstyle": "round,pad=0.15", "facecolor": "white", "alpha": 0.8, "edgecolor": "none"},
                zorder=3,
            )
    ax.set_title(f"Env{environment_id} top 10 edges by excess length (top 5 labelled)")
    ax.set_xlabel("Unity world X")
    ax.set_ylabel("Unity world Y")
    ax.set_aspect("equal", adjustable="box")
    ax.grid(alpha=0.15)
    fig.savefig(QA / f"env{environment_id}-phase13-high-circuity-edges.png", dpi=220)
    plt.close(fig)


def compact_rank_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    fields = [
        "simplified_edge_id", "network_length", "straight_distance",
        "individual_circuity", "excess_length", "excess_share",
        "straight_distance_weight", "aggregate_circuity_excess_contribution",
        "source_fragment_count", "source_shape_ids", "source_segment_ids",
        "source_fragment_ids",
    ]
    return [{field: row[field] for field in fields} for row in rows]


def main() -> None:
    primary, frozen = verify_phase12()
    phase12_qa = frozen["phase12_qa"]
    all_contributions: list[dict[str, Any]] = []
    audits: dict[str, Any] = {}

    for environment_id in (38, 39):
        graph_path = GRAPHS / f"env{environment_id}_analytical_simplified.graphml"
        graph = read_graphml(graph_path)
        graph_by_edge_id = {
            data["simplified_edge_id"]: data
            for _, _, data in graph.edges(data=True)
        }
        raw_rows = []
        for row in frozen["edge_rows"]:
            if int(row["environment_id"]) != environment_id:
                continue
            edge_id = row["simplified_edge_id"]
            graph_data = graph_by_edge_id[edge_id]
            raw_rows.append(
                {
                    "environment_id": environment_id,
                    "simplified_edge_id": edge_id,
                    "network_length": float(row["network_length"]),
                    "straight_distance": float(row["straight_distance"]),
                    "individual_circuity": float(row["circuity"]),
                    "source_fragment_count": int(row["source_fragment_count"]),
                    "source_shape_ids": graph_data["ordered_source_shape_ids"],
                    "source_segment_ids": graph_data["ordered_source_segment_ids"],
                    "source_fragment_ids": graph_data["ordered_source_fragment_ids"],
                }
            )
        enriched, decomposition = decompose_circuity_rows(raw_rows)
        if not math.isclose(
            decomposition["aggregate_circuity_ratio_of_sums"],
            primary[environment_id]["aggregate_circuity"],
            rel_tol=0.0,
            abs_tol=NUMERICAL_TOLERANCE,
        ):
            raise AssertionError("Aggregate circuity does not reproduce Phase 12")
        if decomposition["aggregate_identity_absolute_error"] > NUMERICAL_TOLERANCE:
            raise AssertionError("D-weighted aggregate identity failed")
        if not math.isclose(decomposition["excess_share_sum"], 1.0, abs_tol=NUMERICAL_TOLERANCE):
            raise AssertionError("Excess contribution shares do not sum to one")

        by_circuity = rank_contributors(enriched, "individual_circuity", 10)
        by_excess = rank_contributors(enriched, "excess_length", 10)
        by_aggregate = rank_contributors(
            enriched, "aggregate_circuity_excess_contribution", 10
        )
        top5_excess_share = math.fsum(row["excess_share"] for row in by_excess[:5])
        top10_excess_share = math.fsum(row["excess_share"] for row in by_excess[:10])
        top2_excess_share = math.fsum(row["excess_share"] for row in by_excess[:2])
        correlations = spearman_without_p_value(
            [row["straight_distance"] for row in enriched],
            [row["individual_circuity"] for row in enriched],
        )
        distribution = distribution_audit(
            [row["individual_circuity"] for row in enriched]
        )
        audits[str(environment_id)] = {
            "decomposition": decomposition,
            "top_5_excess_share": top5_excess_share,
            "top_10_excess_share": top10_excess_share,
            "top_2_excess_share": top2_excess_share,
            "rankings": {
                "top_5_by_individual_circuity": compact_rank_rows(by_circuity[:5]),
                "top_10_by_individual_circuity": compact_rank_rows(by_circuity),
                "top_5_by_excess_length": compact_rank_rows(by_excess[:5]),
                "top_10_by_excess_length": compact_rank_rows(by_excess),
                "top_5_by_aggregate_contribution": compact_rank_rows(by_aggregate[:5]),
                "top_10_by_aggregate_contribution": compact_rank_rows(by_aggregate),
            },
            "individual_circuity_distribution": distribution,
            "spearman_straight_distance_vs_individual_circuity": {
                "rho": correlations,
                "descriptive_only": True,
                "p_value_calculated": False,
            },
        }
        all_contributions.extend(enriched)
        plot_high_contributors(environment_id, graph, by_excess)

    contribution_fields = [
        "environment_id", "simplified_edge_id", "network_length", "straight_distance",
        "individual_circuity", "excess_length", "excess_share",
        "straight_distance_weight", "aggregate_circuity_excess_contribution",
        "source_fragment_count", "source_provenance",
    ]
    with (TABLES / "phase13-circuity-contributions.csv").open(
        "w", newline="", encoding="utf-8"
    ) as stream:
        writer = csv.DictWriter(stream, fieldnames=contribution_fields)
        writer.writeheader()
        for row in all_contributions:
            writer.writerow(
                {
                    **{field: row[field] for field in contribution_fields if field != "source_provenance"},
                    "source_provenance": json.dumps(
                        {
                            "shape_ids": row["source_shape_ids"],
                            "segment_ids": row["source_segment_ids"],
                            "fragment_ids": row["source_fragment_ids"],
                        },
                        separators=(",", ":"),
                    ),
                }
            )

    sensitivity_rows = load_csv(TABLES / "phase12-orientation-bin-origin-sensitivity.csv")
    if len(sensitivity_rows) != 20:
        raise ValueError("Frozen orientation sensitivity row count changed")
    orientation_robustness: dict[str, Any] = {"offset_count": 20}
    for environment_id in (38, 39):
        for metric in ("H_o", "H_w"):
            values = [float(row[f"env{environment_id}_{metric}"]) for row in sensitivity_rows]
            orientation_robustness[f"env{environment_id}_{metric}_range"] = [min(values), max(values)]
    orientation_robustness["Env38_H_o_greater_count"] = sum(
        float(row["env38_H_o"]) > float(row["env39_H_o"]) for row in sensitivity_rows
    )
    orientation_robustness["Env38_H_w_greater_count"] = sum(
        float(row["env38_H_w"]) > float(row["env39_H_w"]) for row in sensitivity_rows
    )

    primary_row_map = {int(row["environment_id"]): row for row in frozen["primary_rows"]}
    descriptive_differences = {}
    for field in (
        "H_o_nats", "H_w_nats", "phi", "aggregate_circuity",
        "median_street_length_unity",
    ):
        env38 = float(primary_row_map[38][field])
        env39 = float(primary_row_map[39][field])
        descriptive_differences[field] = {
            "Env38": env38,
            "Env39": env39,
            "difference_Env38_minus_Env39": env38 - env39,
            "percentage_difference_relative_to_Env39": (env38 - env39) / env39 * 100.0,
            "statistical_effect_size": False,
        }

    env39_top = audits["39"]["rankings"]["top_5_by_excess_length"]
    cause_assessment = {
        "classification": "concentrated in two L-shaped simplified streets",
        "basis": (
            f"Env39's top two edges contribute {audits['39']['top_2_excess_share']:.9f} "
            "of total excess length. Each merges two source fragments of the same Shape across a suppressed degree-2 node, "
            "producing an L-shaped topological street; nearly all other Env39 edges are straight within 1e-6."
        ),
        "top_edge": env39_top[0],
        "metric_definition_changed": False,
    }

    evidence_matrix = [
        {
            "metric_family": "Orientation diversity",
            "evidence": ["H_o", "H_w", "20-offset bin-origin robustness"],
            "result": "strong support",
        },
        {
            "metric_family": "Orientation order",
            "evidence": ["phi"],
            "result": "strong support",
        },
        {
            "metric_family": "Curvature/circuity",
            "evidence": ["aggregate circuity", "individual-edge distribution"],
            "result": "mixed / H4 not supported",
        },
        {
            "metric_family": "Topology",
            "evidence": ["degree", "dead-end", "3-way", "4-way distributions"],
            "result": "descriptive structural differences but limited discriminatory power",
        },
    ]
    audit_payload = {
        "phase13_results_audit_schema_version": "1.0.0",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "acceptance_status": "PASS",
        "phase12_output_verification": {
            "passed": True,
            **frozen["provenance"],
        },
        "original_phase12_metrics": {
            str(environment_id): EXPECTED_PRIMARY[environment_id]
            for environment_id in (38, 39)
        },
        "circuity_audits": audits,
        "env39_aggregate_circuity_explanation": cause_assessment,
        "orientation_robustness": orientation_robustness,
        "topology_interpretation": {
            "env38": {"nodes": 60, "streets": 84, "dead_ends": 21, "three_way": 9, "four_way": 30},
            "env39": {"nodes": 51, "streets": 70, "dead_ends": 19, "three_way": 7, "four_way": 25},
            "conclusion": "Topology shows descriptive structural differences but no dramatic grid-versus-curvy separation.",
            "directional_hypothesis_preregistered": False,
        },
        "descriptive_scalar_differences": descriptive_differences,
        "evidence_matrix": evidence_matrix,
        "research_question_answer": (
            "The intended distinction is strongly supported by orientation diversity and order, robust across all bin offsets. "
            "Circuity evidence is mixed and H4 remains not supported; topology has limited discriminatory power."
        ),
        "confirmations": {
            "phase13_replaces_phase12_metrics": False,
            "metric_definition_changed": False,
            "H4_assessment": "not_supported",
            "inferential_p_values_calculated": False,
            "edges_deleted_or_excluded": False,
            "analytical_graphs_modified": False,
        },
        "software_versions": {
            "python": platform.python_version(),
            "numpy": importlib.metadata.version("numpy"),
            "scipy": importlib.metadata.version("scipy"),
            "matplotlib": importlib.metadata.version("matplotlib"),
        },
    }
    write_json(QA / "phase13-results-audit.json", audit_payload)

    print("Frozen Phase 12 results and canonical raw hashes: PASS")
    for environment_id in (38, 39):
        decomposition = audits[str(environment_id)]["decomposition"]
        print(
            f"Env{environment_id}: aggregate={decomposition['aggregate_circuity_ratio_of_sums']:.15f}; "
            f"D-weighted={decomposition['aggregate_circuity_D_weighted_mean']:.15f}; "
            f"top5 excess share={audits[str(environment_id)]['top_5_excess_share']:.6f}"
        )
    print("H4 remains NOT SUPPORTED")
    print("Phase 13: PASS")


if __name__ == "__main__":
    main()
