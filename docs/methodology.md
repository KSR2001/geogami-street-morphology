# Methodology and Geometry Provenance

## 1. Research Question

> To what extent do GeoGami Virtual Environments 38 and 39 differ quantitatively in street-network orientation, curvature, and topology, and do these measures support their intended classification as curvilinear and grid-like environments respectively?

The intended classifications are design labels to be evaluated, not results that have already been demonstrated.

## 2. Experimental Environments

| Environment | Condition label | Unity authoring prefab | Road representation | Shape objects | Quadratic Bézier segments |
|---|---|---|---|---:|---:|
| 38 | Curvilinear / Curvy | `2D Map Vir 38` | Shapes2D `Line Path` objects | 5 | 120 |
| 39 | Grid-like / Grid | `2D Map Vir 39` | Shapes2D `Line Path` objects | 1 | 32 |

The difference between five Shape objects in Environment 38 and one Shape object in Environment 39 is **not** a morphological metric. Shapes2D has a maximum of 32 path segments per Shape, which substantially explains the different authoring-object counts. Segment counts are provenance and export-QA facts; they are not by themselves evidence that either morphology is more curvilinear or grid-like.

There are currently only two designed environments, one per condition. They are individual networks rather than independent samples from larger condition populations.

## 3. Authoritative Geometry Source

The authoritative road geometry is the Unity Shapes2D Bézier representation:

`Shapes2D.Shape` → `settings.pathSegments` → `PathSegment[]`

Each path segment contains:

- `p0 : Vector3` — start endpoint
- `p1 : Vector3` — quadratic Bézier control point
- `p2 : Vector3` — end endpoint

Each road segment is a quadratic Bézier curve:

`B(t) = (1-t)^2 p0 + 2(1-t)t p1 + t^2 p2`, for `0 ≤ t ≤ 1`.

The source data is therefore not an ordinary polyline. The eventual Unity exporter will use the original Shape Bézier information, including `GetPathWorldSegments()`. Exporter implementation is outside Phase 0.

The following are explicitly non-authoritative geometry sources:

- screenshots;
- manually traced roads;
- the finished 3D-terrain road texture;
- rasterized road appearance; and
- `Map2D.GetLines()`.

`Map2D.GetLines()` is unsuitable for morphology analysis because it uses `p0` and `p2` while discarding the Bézier control point `p1`. It therefore replaces each curved quadratic segment with a straight chord and loses curvature information.

## 4. Raw Bézier Representation

The raw representation is an immutable archival record derived directly from Unity. It preserves the original `p0`, `p1`, and `p2` values and the provenance needed to associate segments with their source environment and Shape.

No simplification, intersection reconstruction, curve sampling, or OSMnx processing is permitted in this representation. Raw exports should be retained in `data/raw/` when their size is reasonable and must not be overwritten by processed derivatives.

## 5. Detailed Geometry Representation

Quadratic Bézier curves will later be accurately discretized or adaptively densified into detailed line geometry. This representation must preserve local changes in direction along curves and is intended primarily for:

- curvature-sensitive orientation analysis;
- length-weighted orientation entropy;
- detailed orientation rose diagrams; and
- geometric quality assurance.

Curve-sampling vertices are geometry-only vertices. They must not automatically be interpreted as street intersections.

## 6. Topological Representation

The topological representation models the participant-navigable street network. Nodes represent actual navigable street intersections and dead ends; intermediate geometry-only points do not represent intersections. Curved detailed geometry remains attached to its corresponding graph edge rather than being discarded during topology construction.

This representation is intended for:

- intersections and dead ends;
- 3-way and 4-way junctions;
- streets per node;
- segment lengths;
- connectivity;
- circuity; and
- other topological network statistics.

The topological network must be OSMnx-compatible where practical, without allowing OSMnx conventions to override the authoritative Unity geometry or the explicit navigability rules in this methodology.

## 7. Primary Metrics

Four primary metric families are planned:

1. Simplified/unweighted street-orientation entropy, `H_o`.
2. Detailed length-weighted orientation entropy, `H_w`.
3. Orientation-order/griddedness measure, `phi`.
4. Network circuity.

These metrics are not calculated in Phase 0. Their exact mathematical and software implementations will be verified before analysis; this document therefore does not prematurely fix final formulas, bearing conventions, binning rules, normalization choices, or aggregation procedures.

## 8. Supporting Metrics

The following supporting and control measures are planned:

- total street length;
- median street-segment length;
- mean street-segment length;
- intersection count;
- average streets per node;
- dead-end proportion;
- degree/3-way-junction proportion;
- degree/4-way-junction proportion;
- connected component count;
- node count;
- street-segment count; and
- individual-edge circuity distribution.

These measures will aid interpretation and QA; none is calculated in Phase 0.

## 9. Hypotheses

These are directional expectations, not findings.

Environment 38 is expected to have:

- higher orientation entropy;
- higher detailed/weighted orientation entropy;
- lower orientation order; and
- higher circuity.

Environment 39 is expected to have:

- lower orientation entropy;
- lower detailed/weighted orientation entropy;
- higher orientation order;
- lower circuity; and
- potentially a higher proportion of 4-way intersections.

No directional hypothesis is imposed for dead ends, connectivity, or segment length. These are comparison/control measures.

## 10. Definition of an Intersection

An intersection is a navigable connection between streets, not merely a Unity editing or control point.

- Bézier control points `p1` are not intersections.
- Bézier endpoints `p0` and `p2` are not automatically final topological intersections merely because they exist.
- Intermediate curve-sampling vertices are not intersections.

Future processing must consider endpoint-to-endpoint connections, endpoint-to-interior intersections, and interior-to-interior intersections. Ordinary same-level road crossings should normally become intersections. True grade-separated crossings must not become intersections. Final uncertain cases must be checked against the participant-navigable 3D environment.

## 11. Scale and Units

The Unity-world-unit-to-metre conversion has not yet been established. Until it is verified:

- lengths are Unity-derived world units;
- areas are the corresponding squared world units; and
- no metric may be labelled in metres, kilometres, or square kilometres (`km²`).

Dimensionless measures such as entropy, orientation order, and circuity can still be analysed without a uniform metre conversion. Any implementation must nevertheless record the unit status and avoid silently assuming that one Unity unit equals one metre.

## 12. Orientation Reference

The final north/reference direction has not yet been established. A single explicit and consistent reference convention must be applied to both environments before bearings or orientation statistics are compared.

Later sensitivity analysis must assess the influence of entropy-bin alignment and network rotation. This guards against conclusions that are artifacts of an arbitrary bin origin or coordinate orientation.

## 13. Quality-Assurance Gates

All gates are mandatory. Failure pauses downstream analysis until the discrepancy is investigated and resolved.

### Gate A — Raw export

- Environment 38 must export exactly 120 quadratic Bézier segments.
- Environment 39 must export exactly 32 quadratic Bézier segments.
- If either count differs, analysis stops pending investigation.

### Gate B — Geometry reconstruction

Python/GIS reconstructed linework must visually reproduce the Unity road geometry.

### Gate C — Topology

Intersections, dead ends, and junction classifications must visually agree with the intended road network.

### Gate D — 3D navigability

Uncertain 2D connections must be checked against the participant-navigable 3D environment.

### Gate E — Bézier sampling convergence

Increasing reconstruction resolution should no longer materially alter the principal geometry-sensitive metrics.

### Gate F — Sensitivity

The later analysis must test reasonable changes in snapping tolerance, entropy binning and bin alignment, curve discretization, and small-edge handling.

## 14. Planned Sensitivity Analysis

The analysis will evaluate whether the principal conclusions remain stable under reasonable variations in:

- intersection-snapping tolerance;
- orientation-entropy bin count and bin alignment;
- common network rotation/reference orientation;
- Bézier curve discretization or adaptive-sampling tolerance; and
- treatment of very small edges created during topology construction.

Sampling convergence under Gate E must be established before reporting geometry-sensitive results. Sensitivity settings and their effects will be recorded rather than selected post hoc to favor the intended classifications.

## 15. Statistical Scope

The current design contains only two environments: one curvilinear condition and one grid-like condition. The initial analysis is therefore a descriptive quantitative morphological validation of these two designed networks.

A t-test or population-level claim of inferential significance is not appropriate from these two networks. Appropriate outputs include:

- absolute metric differences;
- relative or percentage differences;
- within-network metric distributions where meaningful;
- visual comparisons; and
- robustness and sensitivity analysis.

Inferential analysis may be reconsidered if multiple independent environments per condition become available later.

## 16. Known Unresolved Questions

The following questions must remain open until evidence is collected:

1. What is the Unity-world-unit-to-metre relationship?
2. What is the final common north/reference direction?
3. What Bézier discretization or adaptive-sampling tolerance is appropriate?
4. What intersection-snapping tolerance is appropriate?
5. Does either environment contain any road-road grade-separated crossings?
6. What is the final bearing/orientation-entropy implementation strategy?
   - an OSMnx geographic-coordinate clone; or
   - direct planar bearing computation, with OSMnx used for graph/network statistics.
7. What is the exact final analysis area or boundary if density metrics are required?

No answers are assumed in Phase 0.

## 17. Reproducibility Principles

The project will follow these principles:

- Preserve raw Unity Bézier exports as immutable provenance records.
- Keep raw, detailed-geometric, and topological representations separate and traceable.
- Record environment identifiers, source Shape identifiers, coordinate/reference conventions, units, exporter version, processing parameters, and software versions with derived artifacts.
- Produce processed data, graphs, figures, and tables through scripted steps once implementation begins; do not substitute manual tracing for authoritative geometry.
- Never interpret sampling vertices or Unity control points as intersections without navigability evidence.
- Apply the same documented processing rules to both environments.
- Treat every QA gate as a prerequisite for downstream interpretation.
- Retain small reproducibility-critical result tables and configuration files in version control.
- Report uncertainties, sensitivity results, and deviations from expected segment counts or geometry explicitly.
- Keep hypotheses separate from observed results and avoid population-level inference that the study design cannot support.
