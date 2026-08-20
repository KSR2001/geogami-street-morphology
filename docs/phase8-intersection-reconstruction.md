# Phase 8 Geometric Intersection Reconstruction

## 1. Phase 8 Scope

Phase 8 inventories pairwise geometric events between original quadratic Bézier street segments. Phase 7 linework provides one candidate path, while every accepted coordinate is checked against the original quadratic equations. The result is an intersection and review inventory—not a street-network topology.

No endpoint snapping, near-miss merging, source-street splitting, graph-node construction, topology, graph analysis, CRS assignment, or metre conversion occurs in this phase. The canonical raw files remain immutable.

## 2. Why Endpoint Equality Alone Is Insufficient

Exact endpoint equality reproduces authored connections but cannot identify an endpoint landing on another curve's interior or two curve interiors crossing. It also cannot determine whether a 2D crossing is navigably connected in the Unity scene. Phase 8 therefore preserves exact authored endpoint evidence while separately solving the original curve equations for interior events.

## 3. Source Representations

The analysis verifies and uses:

- `data/raw/env38_bezier.json`: 120 original quadratic Béziers
- `data/raw/env39_bezier.json`: 32 original quadratic Béziers
- Phase 7 detailed linework for candidate discovery
- `outputs/qa/phase7-selected-discretization.json` for provenance

The accepted Phase 7 tolerance is relative `2e-4`, absolute `0.1403313084170638` Unity world units. It remains a curve-approximation tolerance and is never used to merge or snap coordinates.

## 4. Candidate Pair Discovery

All unique segment pairs are considered within each environment, including same-Shape and cross-Shape pairs. Environment 38 is never compared with Environment 39. Exact analytic quadratic bounds reject disjoint pairs without sampling. The remaining conservative candidates are checked using intersections of regenerated parameter-aware Phase 7 Shapely LineStrings.

Environment 38 has 7,140 possible pairs and 220 analytic-bounds candidates; Environment 39 has 496 possible pairs and 74 candidates. The method does not assume Shapes are disconnected and does not treat close non-intersecting geometry as an event.

## 5. Exact Quadratic Bézier Refinement

The independent source-equation path forms a Sylvester resultant for the two polynomial equations in Bézier parameters `t` and `u`. All real roots in the unit parameter square are enumerated, including multiple roots from one pair. Exact endpoint roots are injected explicitly for degenerate resultant forms. Candidate parameters are then verified with bounded `scipy.optimize.least_squares` against:

```text
B_a(t) - B_b(u) = (0, 0),  0 <= t,u <= 1
```

Accepted event coordinates are evaluated from the original quadratic Béziers, not copied from polyline intersection coordinates. Synthetic tests include a pair with two intersections, a tangency, exact and endpoint-interior contacts, and a zero-chord out-and-back curve.

## 6. Numerical Solver Precision

The root-residual threshold is defined independently as:

```text
1e-10 * 701.656542085319 = 7.01656542085319e-8 Unity world units
```

This value is conservative for double-precision coordinates at the source scale and was verified against synthetic roots and the full inventory. The largest accepted repository root residual is `1.2730026810586e-8`, below the threshold. The threshold is only for mathematical root convergence and same-pair numerical deduplication; it is not a topology snapping tolerance.

The same-pair parameter equivalence is `2e-5`. For known zero-chord curves only, parameters within `1e-3` of an independently proven exact authored endpoint root may be canonicalized to that exact root. This handles their severe parameter ill-conditioning without merging distinct spatial positions.

## 7. Intersection Event Classification

| Event type | Env38 | Env39 | Total |
| --- | ---: | ---: | ---: |
| `endpoint_endpoint` | 137 | 53 | 190 |
| `endpoint_interior` | 0 | 0 | 0 |
| `interior_interior_crossing` | 28 | 20 | 48 |
| `tangent_touch` | 0 | 0 | 0 |
| `overlap_or_coincident` | 0 | 0 | 0 |
| `unresolved_candidate` | 0 | 0 | 0 |
| **Total** | **165** | **73** | **238** |

Each event stores both source IDs and Shape IDs, `t_a`, `t_b`, refined XY, residual, same-Shape status, anomaly involvement, refinement method, status, and navigability review status.

## 8. Exact Endpoint Connections

Endpoint coordinates are grouped by exact numeric equality only—without rounding or tolerance. Environment 38 has 98 shared exact positions producing 137 pairwise endpoint relationships. Environment 39 has 14 shared exact positions producing 53 pairwise relationships. All 190 corresponding events are marked `authored_endpoint_connection`; this label records source authorship and is not a final graph-node decision.

## 9. Endpoint-to-Interior Events

No refined endpoint-to-interior event was found in either environment. The event class remains implemented and synthetic-tested. A future dataset occurrence would require 3D navigability review rather than automatic node construction.

## 10. Interior-to-Interior Events

Environment 38 contains 28 pairwise interior-interior crossings and Environment 39 contains 20, for 48 total. Every one is marked `requires_3d_review`. A 2D geometric crossing is not automatically considered navigably connected because a Unity road may pass above or below another road.

## 11. Tangencies

No source pair was classified as a tangent touch. Tangency detection uses the normalized 2D derivative determinant at the refined root with a documented sine threshold of `1e-4`. The implementation is covered by a synthetic quadratic tangency test.

## 12. Overlaps / Coincidence

No non-zero overlap or coincident source pair was found. Shapely geometry handling covers Point, MultiPoint, LineString, MultiLineString, and GeometryCollection results. Exact identical/reversed control curves and monotone collinear interval overlaps are explicitly detectable; an unproven polyline overlap would remain unresolved rather than causing deletion or merging.

## 13. Cross-Shape Intersections

There are 23 cross-Shape events, all in Environment 38 and all interior-interior crossings. Environment 39 has one Shape and therefore no cross-Shape pair. Cross-Shape events are retained exactly like same-Shape events and all require 3D review.

## 14. Zero-Chord Artifact Handling

Eleven pairwise endpoint events involve one or more of the five known Environment 38 zero-chord segments. They remain in the inventory with `source_anomaly_involved=true`. Their out-and-back parameterization generated 19 redundant numerical representations near already-proven exact authored endpoint roots; these were explicitly canonicalized/deduplicated within the same segment pair. No anomaly was removed, no nearby coordinate was merged, and no fake additional topology decision was created.

## 15. Completeness Cross-Check

The primary Phase 7 Shapely candidate/refinement path was compared against independent original-equation Sylvester-resultant enumeration. Results:

| Diagnostic | Env38 | Env39 |
| --- | ---: | ---: |
| Analytic-bounds candidates | 220 | 74 |
| Phase 7 Shapely intersecting pairs | 165 | 73 |
| Source-resultant pairs with roots | 165 | 73 |
| Independently matched refined roots | 165 | 73 |
| Source-only roots | 0 | 0 |
| Shapely-only roots | 0 | 0 |
| Conclusively rejected bounds candidates | 55 | 1 |
| Unresolved discrepancy pairs | 0 | 0 |

No candidate-method discrepancy was silently discarded. The completeness cross-check passes.

## 16. 3D Navigability Review Requirement

The 48 interior-interior events are exported to `outputs/tables/phase8-3d-crossing-review.csv` with blank `review_notes`. They require explicit future/manual evidence about elevation or same-level connectivity. Phase 8 does not infer navigability from XY geometry or screenshots.

## 17. Env38 QA

`outputs/qa/env38-geometric-intersections.png` shows exact endpoint relationships on the reconstructed roads and 28 interior events at visible curve crossings. The dedicated review figure isolates those crossings. No marker is visibly displaced from the linework, no obvious crossing is missing at normal QA scale, and the 23 cross-Shape events occur where separate authored Shapes geometrically meet.

## 18. Env39 QA

`outputs/qa/env39-geometric-intersections.png` shows 53 pairwise exact endpoint relationships and 20 interior crossings across the rectilinear grid. The review figure places a marker at each visible interior grid crossing. No off-line false event or obvious omitted grid crossing is apparent.

## 19. Visual Reference Comparison

The Phase 8 figures were compared with the Phase 6 reconstruction figures, Phase 7 adaptive figures, and all four Unity baseline images under `docs/reference/`. Event positions correspond qualitatively to visible road geometry and preserve the original orientation and arrangement. Screenshots support geometry-location QA only; they do not establish whether an interior crossing is a same-level navigable junction.

## 20. Unresolved Cases

There are no unresolved candidates after the independent cross-check and explicit zero-chord numerical-root audit. This means the Phase 8 intersection inventory passes its completeness condition; it does not authorize topology construction.

## 21. Limitations

The inventory is pairwise, so several events may occupy one exact authored location when multiple segments meet there. Such records have not been grouped into final nodes. No snapping occurred, no topology or graph nodes were created, no NetworkX or OSMnx graph exists, and no degree, intersection-proportion, connectivity, orientation, entropy, circuity, length, or other final morphology metric was calculated. Physical scale remains unverified, geographic north is not inferred, and no CRS exists.

## 22. Phase-8 Acceptance Checklist

- [x] Canonical hashes and Phase 7 provenance verified before analysis.
- [x] Source counts remain 120 and 32.
- [x] Exact authored endpoint relationships reproduced without tolerance.
- [x] Same-Shape and cross-Shape candidates analyzed.
- [x] Multiple-root, tangency, overlap, endpoint, and zero-chord cases tested.
- [x] All accepted roots satisfy the separate numerical residual criterion.
- [x] Both candidate methods agree with zero unresolved discrepancies.
- [x] Zero-chord involvement is retained and flagged.
- [x] All 48 interior events are assigned to 3D navigability review.
- [x] Raw data remains unchanged and Phase 9 was not started.

## 23. Deferred Phase-9 Work

3D crossing decisions, any snapping/near-miss sensitivity policy, grouping pairwise events into candidate junctions, splitting source curves, final node and edge construction, cross-Shape network integration, anomaly treatment for topology, graph creation, simplification, and all scientific morphology calculations remain deferred to Phase 9 or later.
