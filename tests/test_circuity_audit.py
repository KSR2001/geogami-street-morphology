from __future__ import annotations

import pytest

from scripts.circuity_audit import decompose_circuity_rows, rank_contributors


def sample_rows():
    return [
        {
            "simplified_edge_id": "edge_b",
            "network_length": 3.0,
            "straight_distance": 2.0,
            "individual_circuity": 1.5,
        },
        {
            "simplified_edge_id": "edge_a",
            "network_length": 6.0,
            "straight_distance": 4.0,
            "individual_circuity": 1.5,
        },
    ]


def test_aggregate_circuity_equals_D_weighted_mean():
    _, summary = decompose_circuity_rows(sample_rows())
    assert summary["aggregate_circuity_ratio_of_sums"] == pytest.approx(1.5)
    assert summary["aggregate_circuity_D_weighted_mean"] == pytest.approx(1.5)


def test_excess_length_decomposition():
    rows, summary = decompose_circuity_rows(sample_rows())
    assert [row["excess_length"] for row in rows] == [1.0, 2.0]
    assert summary["total_excess_length"] == 3.0
    assert summary["aggregate_excess_contribution_sum"] == pytest.approx(0.5)


def test_contribution_shares_sum_to_one():
    rows, summary = decompose_circuity_rows(sample_rows())
    assert sum(row["excess_share"] for row in rows) == pytest.approx(1.0)
    assert summary["excess_share_sum"] == pytest.approx(1.0)


def test_top_contributor_sorting_is_deterministic():
    ranked = rank_contributors(sample_rows(), "individual_circuity", 2)
    assert [row["simplified_edge_id"] for row in ranked] == ["edge_a", "edge_b"]
