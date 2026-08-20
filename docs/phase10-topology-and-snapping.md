# Phase 10 Topology and Snapping

## 1. Phase 10 Scope

Phase 10 constructs a detailed topology from exact authored endpoint equality and the 48 Phase-9-validated same-level crossings. It separately audits endpoint-based near misses and evaluates a predefined snapping-tolerance series. The accepted result is **PHASE 10 PASS** with zero canonical snapping.

No NetworkX or OSMnx graph was built, and no final morphology metric was calculated. The coordinate space remains unmodified Unity world XY: no CRS exists, units remain Unity world units, and the metre scale remains unverified.

## 2. Inputs and Provenance

The immutable inputs are the 120 Env38 and 32 Env39 quadratic Bezier source segments in `data/raw/`, the Phase 8 refined intersection events and parameters, and the Phase 9 navigability decisions. Before processing, the raw files matched their canonical SHA-256 values:

- Env38: `43ea446a4a88e9f3d594fb8b72742f5d4b2a1ee8a03ebf8350c4c3cce45c5819`
- Env39: `e5dbce6b4d88656c9e0f3bbf6a814434f64b0fbe9b3ff1864ea3fafaf0883602`

The Phase 7 value `0.140331308417064` is only the accepted curve-discretization tolerance. It is not a snapping tolerance. Likewise, the Phase 8 numerical root/equivalence tolerances are not snapping tolerances.

## 3. Phase-9 Validated Junctions

The Phase 9 JSON and review CSV were verified before topology construction. They contain 48 `connected_same_level` decisions: 28 in Env38 and 20 in Env39. There are zero `grade_separated_not_connected` and zero `manual_review_required` decisions. Phase 10 retains the Phase 8 event IDs, coordinates, source identities, and refined `t_a`/`t_b` parameters without recalculating or changing them.

## 4. Exact Zero-Snapping Baseline

The authoritative baseline uses only bit-for-bit equality of authored `p0`/`p2` coordinate pairs plus the 48 validated crossing locations. It uses no rounding, distance threshold, near-point merge, or snapping. Deterministic location IDs are assigned after coordinate/source ordering, and each location records whether it comes from an `authored_exact_endpoint`, a `validated_interior_crossing`, or multiple sources.

Independent exact files are saved as `data/processed/env38_topology_exact.json` and `data/processed/env39_topology_exact.json`.

## 5. Exact Endpoint Grouping

Authored segment endpoints group only when their parsed world-space `(x, y)` tuples compare exactly equal. Non-equal endpoints remain separate even at extremely small distances. Each exact endpoint location retains all incident endpoint IDs, Shape IDs, and segment IDs, allowing later work to distinguish source segmentation points from branches, junctions, and dead ends.

## 6. Analytical Bezier Splitting

Original quadratic Beziers are split analytically with de Casteljau subdivision at the Phase 8 refined source parameters. Multiple parameters on one source segment are sorted in original-parameter order. Roots are deduplicated only when both the documented Phase 8 parameter-equivalence (`2e-5`) and coordinate-equivalence (`7.01656542085319e-8` Unity world units) conditions hold. Every resulting piece records its original source control points and original source-parameter interval.

## 7. Detailed Topological Fragments

Each analytical sub-curve becomes one detailed fragment between successive topology locations. The sub-curve is adaptively discretized using the already accepted Phase 7 absolute curve tolerance of `0.140331308417064` Unity world units. Fragment records retain deterministic IDs, endpoint location IDs, environment, Shape and source segment identity, original control points, original `t` interval, adaptive XY geometry, QA length, zero-chord status, snapping involvement, and validated-crossing involvement.

All 120 Env38 and 32 Env39 source segments remain traceable. Their ordered fragment intervals cover `[0, 1]`; no source geometry disappears. Source segment boundaries are deliberately not simplified.

## 8. Zero-Chord Artifact Handling

All five known Env38 segments with `p0 == p2` and a non-zero tiny Bezier excursion are preserved and flagged. They produce five self-loop-like detailed fragments at four exact endpoint locations. They do not alter or corrupt connectivity, and their future inclusion in scientific metrics remains deferred. Env39 has no such source segment.

## 9. Why Snapping Requires Separate Validation

Nearness is not topological equality and does not by itself establish authorial intent. The near-miss inventory and provisional sensitivity calculations are therefore separate from the exact topology. Neither the intended environment class nor a desired count, component structure, entropy, circuity, or other future metric was used to justify a connection.

## 10. Endpoint-to-Endpoint Near-Miss Audit

The audit found three unique non-exact endpoint-to-endpoint candidates, all in Env38. Env39 has none. Existing exact relationships and validated crossings are excluded. Each CSV row records both endpoint identities, source Shapes and segments, exact Euclidean distance, confirmed-junction status, anomaly status, ambiguity, and the first predefined tolerance that includes it.

## 11. Endpoint-to-Interior Near-Miss Audit

The audit found ten endpoint-to-Bezier-interior candidates in Env38 and four in Env39. The final nearest point is calculated against the original quadratic, not its polyline approximation. The implementation minimizes squared distance analytically: differentiating `||B(t)-P||^2` yields a cubic polynomial; all real roots in `[0,1]` and both interval endpoints are evaluated, and the minimum is selected. A candidate requires the resulting parameter to lie strictly inside the target Bezier and no existing exact or validated connection.

Arbitrary interior-to-interior near approaches are outside this phase and are not snapping candidates.

## 12. Candidate Snapping Tolerance Series

The common reference scale is `701.656542085319` Unity world units. The complete predefined relative series was evaluated without extension:

`0, 1e-8, 2e-8, 5e-8, 1e-7, 2e-7, 5e-7, 1e-6, 2e-6, 5e-6, 1e-5, 2e-5, 5e-5, 1e-4, 2e-4, 5e-4, 1e-3`.

The corresponding absolute series is:

`0, 0.000007016565420853189, 0.000014033130841706379, 0.000035082827104265944, 0.00007016565420853189, 0.00014033130841706377, 0.0003508282710426595, 0.000701656542085319, 0.001403313084170638, 0.003508282710426595, 0.00701656542085319, 0.01403313084170638, 0.03508282710426595, 0.0701656542085319, 0.1403313084170638, 0.3508282710426595, 0.701656542085319` Unity world units.

## 13. Ambiguity Safeguards

At each tolerance the analysis flags endpoints with multiple targets, transitive endpoint clusters whose diameter exceeds the tolerance, endpoint-to-endpoint versus endpoint-to-interior conflicts, zero-chord involvement, and a proposed target preceded by a closer competing feature. Ambiguous candidates are never provisionally applied or resolved by iteration order. The maximum observed ambiguous-candidate count is eight, all in Env38 at the upper part of the series; no near-miss involves a known zero-chord anomaly.

## 14. Snapping Sensitivity Results

The full environment-by-tolerance results are in `outputs/tables/phase10-snapping-sensitivity.csv` and the machine-readable QA JSON. At the maximum tolerance, Env38 has 3 endpoint-endpoint and 10 endpoint-interior candidates; 8 are ambiguous, so only 1 and 4 respectively are provisionally applied. This diagnostic gives 146 locations, 180 fragments, and one component versus the exact 147, 176, and one. Env39 has 4 endpoint-interior candidates, all provisionally unambiguous, giving 53 locations, 76 fragments, and one component versus 53, 72, and one.

These are sensitivity diagnostics, not accepted connections or final morphology metrics.

## 15. Distance Distribution / Gap Analysis

Env38 candidate distances range from `0.016782323415295446` to `0.5721400055331666`; its first two sorted values have a local ratio of `10.022544998350986`. Env39 distances range from `0.057321383705410955` to `0.24569058862524276`, with a largest adjacent ratio of only `2.10397432809999`. Across all 17 candidates, the largest adjacent ratio is `3.415580923268832`.

Using the predefined diagnostic rule of an adjacent ratio of at least 10, Env38 has one local order-of-magnitude gap. Env39 and the combined inventory do not establish a consistent, clearly separated global extremely-close class. The local observation alone does not prove intended connectivity. Sorted values are retained in the QA JSON and plotted in `outputs/qa/phase10-near-miss-distance-distribution.png`.

## 16. Canonical Snapping Decision

The canonical relative and absolute snapping tolerances are both **0**. No topology location is affected and maximum canonical displacement is `0.0`.

This follows the specified default because the combined endpoint-based distances do not form one unambiguous extremely-close class clearly separated from larger gaps across both environments. Proximity alone does not prove intent, and a non-zero selection would not satisfy all six acceptance conditions. No candidate is classifiable as a likely intended connection from geometry alone; consequently, manual topology review is not required. All cases remain available for sensitivity interpretation.

The selected files `data/processed/env38_topology.json` and `data/processed/env39_topology.json` are structurally equivalent to their exact baselines and explicitly record the zero-snapping policy.

## 17. Env38 Topology QA

The selected/exact Env38 topology contains 147 locations and 176 detailed fragments. Of the locations, 21 have one incident fragment, 83 have two, and 43 have three or more. It represents all 28 validated interior junctions, preserves five zero-chord/self-loop-like fragments, and has one connected component. These are descriptive topology QA counts only.

## 18. Env39 Topology QA

The selected/exact Env39 topology contains 53 locations and 72 detailed fragments. Of the locations, 19 have one incident fragment, 2 have two, and 32 have three or more. It represents all 20 validated interior junctions, has no zero-chord/self-loop-like fragment, and has one connected component. These are descriptive topology QA counts only.

## 19. Limitations

The audit stops at `1e-3` of the reference scale and considers only endpoint-endpoint and endpoint-interior candidates. It does not infer intended connectivity from visual semantics or Unity 3D inspection beyond the completed Phase 9 decisions. The detailed topology preserves source segmentation and artifact curves, so its incidence counts must not be interpreted as simplified graph metrics. No CRS exists, no geographic north is inferred, and Unity world units cannot yet be stated in metres.

## 20. Phase-10 Acceptance Checklist

- [x] Canonical raw hashes and source counts verified.
- [x] Phase 9 verified as 48 connected, zero grade-separated, zero unresolved.
- [x] Exact zero-snapping baselines created.
- [x] All 48 validated crossings represented without coordinate or decision changes.
- [x] Original Beziers split analytically at refined parameters and adaptively discretized.
- [x] Every source segment and all five anomalies remain traceable.
- [x] Endpoint-based near-miss audit and full predefined sensitivity series completed.
- [x] Ambiguities explicitly identified and excluded from provisional application.
- [x] Canonical zero-snapping decision follows the required evidence rule.
- [x] Integrity checks and focused tests pass.
- [x] No unresolved likely-connection candidate requires manual review.
- [x] No NetworkX/OSMnx graph, CRS, metre conversion, or final morphology metric was created.

## 21. Deferred Phase-11 Work

Graph construction, degree-2 simplification, treatment of zero-chord artifacts in scientific metrics, NetworkX/OSMnx representations, and final morphology calculations remain deferred. Phase 10 makes no Env38-versus-Env39 scientific interpretation and does not begin Phase 11.
