"""Reusable explanatory decomposition for fixed edge-circuity results."""

from __future__ import annotations

import math
from copy import deepcopy
from typing import Any, Iterable


def decompose_circuity_rows(rows: Iterable[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, float]]:
    """Add straight-distance weights and excess-distance contributions."""

    source = [deepcopy(row) for row in rows]
    if not source:
        raise ValueError("Circuity decomposition requires at least one edge")
    total_network = math.fsum(float(row["network_length"]) for row in source)
    total_straight = math.fsum(float(row["straight_distance"]) for row in source)
    if total_straight <= 0:
        raise ValueError("Total straight distance must be positive")
    total_excess = total_network - total_straight
    if total_excess <= 0:
        raise ValueError("Total excess network length must be positive")

    enriched = []
    for row in source:
        network = float(row["network_length"])
        straight = float(row["straight_distance"])
        circuity = float(row["individual_circuity"])
        if straight <= 0:
            raise ValueError("Every edge straight distance must be positive")
        excess = network - straight
        row.update(
            excess_length=excess,
            excess_share=excess / total_excess,
            straight_distance_weight=straight / total_straight,
            aggregate_circuity_excess_contribution=excess / total_straight,
        )
        enriched.append(row)

    aggregate = total_network / total_straight
    weighted_mean = math.fsum(
        row["straight_distance_weight"] * float(row["individual_circuity"])
        for row in enriched
    )
    summary = {
        "total_network_length": total_network,
        "total_straight_distance": total_straight,
        "total_excess_length": total_excess,
        "aggregate_circuity_ratio_of_sums": aggregate,
        "aggregate_circuity_D_weighted_mean": weighted_mean,
        "aggregate_identity_absolute_error": abs(aggregate - weighted_mean),
        "excess_share_sum": math.fsum(row["excess_share"] for row in enriched),
        "straight_distance_weight_sum": math.fsum(
            row["straight_distance_weight"] for row in enriched
        ),
        "aggregate_excess_contribution_sum": math.fsum(
            row["aggregate_circuity_excess_contribution"] for row in enriched
        ),
    }
    return enriched, summary


def rank_contributors(
    rows: Iterable[dict[str, Any]], field: str, count: int
) -> list[dict[str, Any]]:
    """Rank descending by a numerical field with deterministic ID tie-breaking."""

    return sorted(
        (deepcopy(row) for row in rows),
        key=lambda row: (-float(row[field]), str(row["simplified_edge_id"])),
    )[:count]
