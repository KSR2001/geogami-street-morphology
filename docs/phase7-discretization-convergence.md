# Phase 7 Adaptive Discretization and Convergence QA

## 1. Phase 7 Scope

Phase 7 replaces the Phase 6 display-only samples with a scientifically controlled adaptive polyline approximation of every exact quadratic Bézier. It evaluates numerical convergence and selects one common curve-approximation tolerance for both environments. Each source Bézier remains one provenance-preserving record.

This phase does not reconstruct intersections, snap coordinates, merge endpoints, create topology, build a graph, or calculate final morphology results. The canonical files in `data/raw/` remain immutable.

## 2. Why Fixed Sample Counts Are Rejected

A fixed vertex count does not respond to curve shape: a straight segment receives unnecessary vertices while a strongly curved segment may receive too few. Phase 6's 101 samples per segment remain valid only for display QA and are not reused as analytical linework. Phase 7 instead applies the same explicit geometric error policy to every source curve in both environments.

## 3. Adaptive Quadratic Bézier Algorithm

For `B(t) = (1-t)^2 p0 + 2(1-t)t p1 + t^2 p2`, the implementation recursively tests each current quadratic sub-curve. A sub-curve whose curve-to-chord deviation is within the absolute tolerance contributes only its ordered chord endpoints. Otherwise it is divided at `t=0.5`, and both halves are tested recursively. The returned vertices include exact source p0 and p2 and follow increasing Bézier parameter.

The implementation is in `scripts/bezier_geometry.py`. It validates finite XY inputs and a finite positive tolerance, does not mutate input control points, and includes a recursion-depth safeguard.

## 4. De Casteljau Subdivision

For one midpoint split:

```text
p01 = (p0 + p1) / 2
p12 = (p1 + p2) / 2
pm  = (p01 + p12) / 2

left  = (p0, p01, pm)
right = (pm, p12, p2)
```

Concatenating the left vertices with the right vertices while retaining the shared midpoint once preserves parameter order and source endpoints.

## 5. Flatness / Error Criterion

For a non-zero p0-p2 chord, let `d` be the perpendicular distance from p1 to the infinite endpoint-chord line. The perpendicular component of the quadratic relative to its chord is `2t(1-t)d`, whose maximum occurs at `t=0.5`. Therefore the exact maximum perpendicular curve-to-chord-line deviation is `d/2`. A sub-curve is accepted when:

```text
d / 2 <= absolute_tolerance
```

This is a curve-approximation flatness tolerance. It is not an intersection, topology, or network tolerance.

## 6. Zero-Chord Handling

When p0 equals p2 but p1 differs, an endpoint-chord test is undefined and returning only `[p0, p2]` would erase the curve. The implementation forces an initial de Casteljau split at `t=0.5`; the two resulting non-zero-chord halves are then processed normally. This produces the ordered out-and-back representation `p0 -> excursion -> p0`. A fully coincident p0/p1/p2 curve remains a truly zero-length case.

## 7. Common Reference Scale

Bounds were calculated from all raw world-space p0, p1, and p2 control points.

| Environment | min_x | max_x | min_y | max_y | diagonal |
| --- | ---: | ---: | ---: | ---: | ---: |
| 38 | 2.35858154 | 440.35083 | -164.559021 | 367.160583 | 688.8852930560814 |
| 39 | 0.6841152 | 442.0116 | -171.685287 | 373.797943 | 701.656542085319 |

The common reference scale is the larger diagonal: **701.656542085319 Unity world units**. It is used unchanged for both environments. Unity's physical metre scale remains unverified.

## 8. Candidate Tolerance Series

The candidate series was fixed before results were inspected. No finer levels were required.

| Relative tolerance | Absolute tolerance (Unity world units) |
| ---: | ---: |
| 1e-3 | 0.701656542085319 |
| 5e-4 | 0.350828271042660 |
| 2e-4 | 0.140331308417064 |
| 1e-4 | 0.0701656542085319 |
| 5e-5 | 0.0350828271042659 |
| 2e-5 | 0.0140331308417064 |
| 1e-5 | 0.00701656542085319 |

## 9. High-Accuracy Bézier Length Reference

Each original Bézier reference length is calculated independently by integrating `||B'(t)||` over `[0,1]` with `scipy.integrate.quad`, using `epsabs=1e-12` and `epsrel=1e-12`. Phase 6 display sampling is not involved. This method also measures the non-zero out-and-back path length of the five zero-chord anomalies and avoids division by zero for truly zero-length curves.

## 10. Convergence Diagnostics

The tables show total per-record vertices, aggregate absolute-error/reference-total relative error, change in total polyline length to the next finer level, and worst ordinary-segment relative error. They are approximation QA diagnostics, not final street lengths or morphology results.

### Environment 38

| Relative tolerance | Vertices | Aggregate relative error | Change to next finer | Worst ordinary segment error |
| ---: | ---: | ---: | ---: | ---: |
| 1e-3 | 278 | 1.97539165e-4 | 1.3602000e-4 | 2.12338019e-3 |
| 5e-4 | 314 | 6.15275348e-5 | 1.36219853e-5 | 1.27801136e-3 |
| 2e-4 | 324 | 4.79062021e-5 | 3.37892134e-5 | 6.46186869e-4 |
| 1e-4 | 395 | 1.41174657e-5 | 2.31218041e-6 | 2.10994681e-4 |
| 5e-5 | 413 | 1.18053126e-5 | 8.40765908e-6 | 1.17512758e-4 |
| 2e-5 | 558 | 3.39768209e-6 | 1.36979452e-6 | 4.46383545e-5 |
| 1e-5 | 689 | 2.02789034e-6 | n/a | 2.47988706e-5 |

### Environment 39

| Relative tolerance | Vertices | Aggregate relative error | Change to next finer | Worst ordinary segment error |
| ---: | ---: | ---: | ---: | ---: |
| 1e-3 | 65 | 2.40788688e-6 | 1.04583403e-6 | 1.97065111e-5 |
| 5e-4 | 67 | 1.36205427e-6 | 9.23299385e-7 | 1.97065111e-5 |
| 2e-4 | 73 | 4.38755292e-7 | 2.18026263e-7 | 4.92647511e-6 |
| 1e-4 | 79 | 2.20729076e-7 | 1.11030907e-7 | 4.92647511e-6 |
| 5e-5 | 88 | 1.09698181e-7 | 5.53809773e-8 | 1.23160924e-6 |
| 2e-5 | 102 | 5.43172068e-8 | 2.68861828e-8 | 1.23160924e-6 |
| 1e-5 | 118 | 2.74310249e-8 | n/a | 3.07901713e-7 |

The complete sweep, including vertex distribution, polyline segment counts, total lengths, absolute errors, and maximum segment-level changes, is stored in JSON and CSV.

## 11. Acceptance Rule

The rule was encoded before tolerance selection. The selected level is the coarsest predefined candidate satisfying all of the following for both environments:

1. Aggregate absolute length error divided by aggregate high-accuracy reference length is at most `1e-4`.
2. Aggregate total-polyline-length relative change to the next finer candidate is at most `1e-4`.
3. The maximum per-segment reference-length relative error is at most `1e-3` for an ordinary segment.
4. Every zero-chord anomaly preserves a positive excursion and has absolute reference-length error no greater than the candidate absolute tolerance.

An ordinary segment is defined as having a non-zero endpoint chord and reference length at least `1e-12 * common_reference_scale`. Zero-chord anomalies are evaluated by their explicit absolute-error rule rather than hidden by a relative division. The tolerance is not adjusted using intersection counts, connectivity, or intended morphology.

## 12. Selected Common Tolerance

The selected relative tolerance is **2e-4** and the selected absolute tolerance is **0.140331308417064 Unity world units**. The same absolute value applies to both environments.

The coarser `5e-4` level was rejected because Environment 38's worst ordinary-segment relative error was `1.27801136e-3`, exceeding the predefined `1e-3` threshold. The selected `2e-4` level passes every criterion for both environments.

## 13. Env38 Results

At the selected tolerance, the 120 source records contain 324 vertices and 204 adaptive polyline segments in total. Per-source-curve vertex counts range from 2 to 17 with median 2. The high-accuracy reference total is 5173.411044840865 Unity world units; the adaptive total is 5173.163206365717. Aggregate absolute error is 0.24783847514786422, aggregate relative error is `4.790620211688356e-5`, change to the next finer level is `3.378921341566807e-5`, and worst ordinary-segment relative error is `6.461868694114874e-4`.

## 14. Env39 Results

At the selected tolerance, the 32 source records contain 73 vertices and 41 adaptive polyline segments in total. Per-source-curve vertex counts range from 2 to 5 with median 2. The high-accuracy reference total is 5008.305865176797 Unity world units; the adaptive total is 5008.303667756097. Aggregate absolute error is 0.0021974207000141632, aggregate relative error is `4.387552915433995e-7`, change to the next finer level is `2.180262630607315e-7`, and worst ordinary-segment relative error is `4.926475113466511e-6`.

## 15. Zero-Chord QA

Each anomaly has three adaptive vertices and preserves a positive midpoint excursion.

| Segment | p0 = p2 | p1 | Reference length | Adaptive length | Excursion preserved |
| --- | --- | --- | ---: | ---: | --- |
| `env38_shape_4330855547529842337_segment_0006` | (213.256165, 121.9834) | (213.2562, 121.983459) | 6.860029153709443e-5 | 6.860029155159526e-5 | yes |
| `env38_shape_4330855547529842337_segment_0019` | (331.0658, 207.331726) | (331.065918, 207.331726) | 1.1799999998629573e-4 | 1.1800000004313915e-4 | yes |
| `env38_shape_4330855547829185599_segment_0007` | (117.5127, -53.993515) | (117.51297, -53.99369) | 3.217530108635848e-4 | 3.217530108635848e-4 | yes |
| `env38_shape_4330855547829185599_segment_0011` | (82.70692, 21.4694939) | (82.70704, 21.4688988) | 6.070782568995186e-4 | 6.070782568995186e-4 | yes |
| `env38_shape_4330855547829185599_segment_0012` | (82.70692, 21.4694939) | (82.70692, 21.4687786) | 7.152999999995302e-4 | 7.153000000030829e-4 | yes |

The exact control points, reference lengths, vertex counts, errors, and excursion magnitudes are retained in `outputs/qa/phase7-discretization-convergence.json` and `outputs/qa/phase7-selected-discretization.json`.

## 16. Selected Detailed Linework

The canonical Phase 7 derived representations are:

- `data/processed/env38_detailed_linework.json`
- `data/processed/env39_detailed_linework.json`

Every original Bézier remains a separate record with source identifiers and p0/p1/p2, selected tolerance, ordered adaptive vertices, independent reference length, adaptive length, and approximation errors. No source segment is merged, connected to another Shape, or split at a crossing. The Phase 6 reconstruction JSONs are unchanged. No optional geospatial file was created because JSON fully preserves the required no-CRS planar representation.

## 17. Visual QA

`outputs/qa/env38-adaptive-linework.png` and `outputs/qa/env39-adaptive-linework.png` use equal aspect and unmodified Unity world XY orientation. At normal QA scale both are visually indistinguishable from their Phase 6 reconstructed Bézier figures: Env38 preserves its major loop, branches, and sweeping curves, while Env39 preserves its rectilinear grid. Nothing is visibly missing or duplicated. No rotation, normalization, translation, axis flip, or projection was applied. `outputs/qa/phase7-length-convergence.png` shows decreasing approximation error across the fixed tolerance series.

## 18. Limitations

The selected tolerance controls curve-to-chord approximation only. Phase 7 does not test intersection sensitivity and must not be interpreted as an endpoint snapping or topology tolerance. No intersections have been reconstructed, no snapping has occurred, no topology or graph exists, and no final morphology metrics have been calculated. Units remain Unity world units, physical metre scale remains unverified, geographic north is unknown, and no CRS has been assigned.

## 19. Phase-7 Acceptance Checklist

- [x] Both canonical source hashes verified before derived output.
- [x] Adaptive de Casteljau subdivision and zero-chord policy implemented and tested.
- [x] One raw-control-geometry reference scale applied to both environments.
- [x] Predefined seven-level tolerance sweep completed without post-hoc extension.
- [x] Independent high-accuracy reference lengths calculated with SciPy integration.
- [x] Predefined common acceptance rule applied numerically.
- [x] All 120 and 32 source Béziers retained as separate detailed-linework records.
- [x] All five zero-chord excursions retained.
- [x] Adaptive figures compared against Phase 6 reconstruction figures.
- [x] No raw source modification or Phase 8 processing performed.

## 20. Deferred Phase-8 Work

Geometric crossing detection, intersection sensitivity, splitting curves at crossings, endpoint snapping or tolerance decisions, cross-Shape integration, anomaly treatment for network construction, topology, graph creation, simplification, CRS or unit calibration, and all scientific morphology metrics remain deferred to Phase 8 or later.
