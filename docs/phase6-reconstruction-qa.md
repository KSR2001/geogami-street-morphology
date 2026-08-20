# Phase 6 Reconstruction and Geometry QA

## 1. Phase 6 Scope

Phase 6 reconstructs every exported quadratic Bézier in Unity world XY and performs lossless geometry and visual QA. It does not interpret the curves as a navigable street network. The canonical exports in `data/raw/` remain immutable; all reconstruction products are derived files.

## 2. Immutable Input Verification

The reconstruction script verifies both canonical files before it creates any output and aborts on a mismatch.

| Environment | Canonical input | Expected and verified SHA-256 |
| --- | --- | --- |
| 38 | `data/raw/env38_bezier.json` | `43ea446a4a88e9f3d594fb8b72742f5d4b2a1ee8a03ebf8350c4c3cce45c5819` |
| 39 | `data/raw/env39_bezier.json` | `e5dbce6b4d88656c9e0f3bbf6a814434f64b0fbe9b3ff1864ea3fafaf0883602` |

The verified source schema is `1.0.0`. Environment 38 contains five Shapes with ordered segment counts 4, 32, 32, 24, and 28. Environment 39 contains one Shape with 32 segments. All source world-coordinate z values were also checked as exactly zero.

## 3. Quadratic Bézier Equation

For source control points `p0`, `p1`, and `p2`, the evaluator implements

```text
B(t) = (1 - t)^2 p0 + 2(1 - t)t p1 + t^2 p2,  0 <= t <= 1
```

The reusable NumPy evaluator supports a scalar or array of parameter values, validates the closed parameter interval, and does not modify its inputs. Independent synthetic tests cover both endpoint identities, a straight-line construction, the midpoint identity, finite output, input preservation, and invalid parameter rejection.

## 4. World-Coordinate Reconstruction

Reconstruction uses only `world.p0`, `world.p1`, and `world.p2`, taking x and y as the planar coordinates. Shape and segment provenance, indices, and all three source world control points are copied into each derived record. Local coordinates are not used. The coordinate space is labelled **Unity world XY**, the units are **Unity world units**, the metre scale is unverified, and no CRS is assigned.

Derived representations are written to:

- `data/processed/env38_bezier_reconstruction.json`
- `data/processed/env39_bezier_reconstruction.json`

## 5. Visualization Sampling Policy

Each curve has 101 evenly spaced parameter samples including `t=0` and `t=1`. This is explicitly **visualization-only dense sampling**. It is not an analytical sampling tolerance, has not been shown sufficient for scientific discretization, and must not justify curve length, intersection detection, topology, entropy, circuity, or any other network metric.

## 6. Reconstruction Completeness

| Check | Environment 38 | Environment 39 |
| --- | ---: | ---: |
| Source/reconstructed segments | 120 / 120 | 32 / 32 |
| First sample exactly equals p0 | PASS | PASS |
| Last sample exactly equals p2 | PASS | PASS |
| All sampled XY values finite | PASS | PASS |
| Source control points and IDs preserved | PASS | PASS |

No source segment was removed. The counts and ordered Shape membership are unchanged in the derived artifacts.

## 7. Exact Endpoint Audit

The endpoint audit compares source p0/p2 positions by exact Unity world XY equality only. It performs no tolerance matching, snapping, merging, or graph construction.

| Descriptive source count | Environment 38 | Environment 39 |
| --- | ---: | ---: |
| Segments / endpoint occurrences | 120 / 240 | 32 / 64 |
| Distinct exact endpoint positions | 119 | 33 |
| Distinct directed p0-p2 pairs | 119 | 32 |
| Distinct undirected p0-p2 pairs | 119 | 32 |
| Positions appearing once | 21 | 19 |
| Positions with multiple occurrences | 98 | 14 |
| Positions shared by multiple source segments | 98 | 14 |
| Maximum endpoint occurrence count | 6 | 4 |

The full position-level evidence is in `outputs/qa/phase6-endpoint-audit.json`. These shared endpoint positions are not labelled final intersections. Crossings may occur inside curves or between different Shapes, so exact endpoint equality is insufficient for final topology.

## 8. Bézier Source Diagnostics

The QA diagnostic measures the perpendicular distance of p1 from the infinite p0-p2 chord line and also records that distance divided by chord magnitude. It uses a strict ratio threshold of `1e-6` to label non-collinear records as near-collinear; zero-chord records are handled separately because their chord direction is undefined.

| Classification | Environment 38 | Environment 39 |
| --- | ---: | ---: |
| Exactly collinear | 1 | 1 |
| Near-collinear at ratio <= 1e-6 | 5 | 7 |
| Control point deviates from chord | 109 | 24 |
| Zero chord / undefined | 5 | 0 |

The defined perpendicular-deviation ranges are 0 to 64.7332620883058 Unity world units for Environment 38 and 0 to 2.688755786942994 Unity world units for Environment 39. As an additional visual-QA interpretation, all 32 defined Environment 39 ratios are at most 0.01, while Environment 38 contains visibly substantial authored curvature. These are source-geometry diagnostics only—not scientific morphology, curvature, street length, or network-circuity metrics. Full segment records are in `outputs/qa/phase6-bezier-source-diagnostics.json`.

## 9. Zero-Chord Source Anomalies

All five known Environment 38 source anomalies remain present, retain their original control points, and are flagged `known_zero_chord_source_anomaly`:

- `env38_shape_4330855547529842337_segment_0006`
- `env38_shape_4330855547529842337_segment_0019`
- `env38_shape_4330855547829185599_segment_0007`
- `env38_shape_4330855547829185599_segment_0011`
- `env38_shape_4330855547829185599_segment_0012`

They were not deleted, filtered, replaced, or repaired. Their analytical treatment is deferred.

## 10. Environment 38 Visual QA

`outputs/qa/env38_reconstructed_beziers.png` retains the curvilinear source character: the large upper circular loop, its internal and external branches, the long vertical elements, and the broad sweeping lower alignments are all visible. The accompanying control-geometry plot shows that the pronounced loop and bends follow the exported p0/p1/p2 geometry. No obvious source road is missing or duplicated in the reconstruction plot.

## 11. Environment 39 Visual QA

`outputs/qa/env39_reconstructed_beziers.png` retains the sparse rectilinear/grid-like arrangement: long near-vertical alignments, major horizontal cross-lines, and the smaller upper-central grid are visible in their source orientation. Minor authored deviations from exact straightness remain visible rather than being straightened. No obvious source grid line is missing or duplicated.

## 12. Unity Reference Comparison

The comparison used the four available reference images without OCR:

- Environment 38: `docs/reference/Env38 complete 2D road map.jpg` and `docs/reference/env38_curvy_unity_baseline.jpg`
- Environment 39: `docs/reference/Env39 complete 2D road map.jpg` and `docs/reference/env39_grid_unity_baseline.jpg`

The reconstructed Environment 38 road layer qualitatively matches the references in orientation, outer arrangement, major circular loop, branches, vertical roads, and sweeping lower roads. The Environment 39 road layer matches the references in orientation, orthogonal layout, principal long lines, and upper grid arrangement. Background terrain, water, and map annotations in the screenshots are not exported road geometry and were excluded from the comparison. No rotation, axis flip, translation, normalization, or projection was applied. On this qualitative road-layer comparison, both reconstructions pass visual QA; this is not a pixel-level registration test.

## 13. Coordinate Extents

The bounds below are exact analytic quadratic-curve bounds, including interior axis extrema rather than relying on the 101 display samples.

| Environment | min_x | max_x | min_y | max_y |
| --- | ---: | ---: | ---: | ---: |
| 38 | 2.35858154 | 440.35083 | -164.559021 | 367.160583 |
| 39 | 0.6841152 | 442.0116 | -171.685287 | 373.797943 |

All values are in Unity world units. The optional side-by-side figure uses a common raw-coordinate scale; it does not rescale either environment to force similarity.

## 14. Limitations

Phase 6 does not establish geographic north, geographic coordinates, a CRS, metres per Unity unit, analytical discretization, or scientific curve-length accuracy. No snapping, endpoint repair, geometric intersection reconstruction, node merging, topology construction, network simplification, NetworkX graph, or OSMnx graph has occurred. No street bearings, orientation entropy/order, circuity, connectivity, final street lengths, statistical comparison, or other scientific morphology metric has been calculated.

## 15. Phase-6 Acceptance Checklist

- [x] Canonical raw hashes verified before output generation.
- [x] All 120 Environment 38 and 32 Environment 39 segments reconstructed from world XY.
- [x] Endpoint identities, finite samples, provenance, and source counts verified.
- [x] All five zero-chord source anomalies retained and flagged.
- [x] Exact endpoint and source-control diagnostics saved as descriptive QA.
- [x] Equal-aspect reconstruction and control-geometry figures generated.
- [x] Both environments compared with identified Unity reference images.
- [x] Visualization sampling explicitly separated from analytical sampling.
- [x] No canonical raw data changed and no Phase 7 processing performed.

## 16. Deferred Phase-7 Work

Any scientific discretization/convergence policy, geometric intersection handling, endpoint tolerance or snapping policy, cross-Shape integration, anomaly treatment, topology construction, graph representation, network simplification, unit calibration, CRS decision, and morphology metric calculation remains explicitly deferred to Phase 7 or later.
