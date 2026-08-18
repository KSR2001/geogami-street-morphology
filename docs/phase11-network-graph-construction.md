# Phase 11 Network Graph Construction

## 1. Phase 11 Scope

Phase 11 converts the validated Phase 10 topology into deterministic NetworkX graph representations, explicitly excludes the five pre-registered Env38 zero-chord artifacts from analytical variants, suppresses geometry-only degree-2 nodes, and creates a bidirectional OSMnx-style structural adapter. The result is **PHASE 11 PASS**.

All counts in this document are graph-construction QA. No final morphology metrics or Env38-versus-Env39 scientific interpretation were calculated.

## 2. Phase-10 Topology Input

The inputs are `data/processed/env38_topology.json` and `env39_topology.json`. Their exact counterparts were also checked. The selected and exact locations, fragments, source inventories, and QA counts agree because canonical relative and absolute snapping remain `0`.

Canonical raw SHA-256 values were reverified before graph construction. Env38 contains 147 topology locations, 176 detailed fragments, and 28 validated junctions; Env39 contains 53, 72, and 20. All coordinates remain unchanged Unity world X/Y values.

## 3. Why the Canonical Graph Is Undirected

The Unity source contains no one-way or traffic-direction semantics. The canonical graph is therefore an undirected `networkx.MultiGraph`. A multigraph preserves geometrically distinct streets that may connect the same two topology nodes instead of collapsing them into a simple edge.

## 4. Provenance Detailed Graph

Every Phase 10 topology location becomes a deterministic node whose ID remains its topology-location ID. Attributes retain exact coordinates, source type, authored-endpoint and validated-crossing flags, canonical snapping displacement, Phase 8 event IDs, Phase 9 validation evidence, source IDs, and the full Phase 10 node record.

Every detailed fragment becomes one keyed edge. The key is its Phase 10 fragment ID. Each edge retains source Shape and segment identity, original and split Bezier control points, source `t` interval, adaptive geometry, Unity-unit QA length, crossing/snapping/anomaly flags, and its complete Phase 10 record. This graph is a faithful, unsimplified provenance representation.

## 5. Zero-Chord Artifact Policy

The five pre-registered Env38 source anomalies remain as five self-loops in the provenance graph. They map one-to-one to Phase 10 fragments and are listed in `outputs/qa/phase11-zero-chord-artifact-exclusions.json`.

Only those five exact source IDs are excluded from analytical graphs. No arbitrary short-edge threshold is used, and no other short, curved, unusual, or awkward fragment is removed. The affected topology locations are `env38_topology_location_0028`, `_0034`, `_0065`, and `_0110`; their analytical incident counts decrease by 4, 2, 2, and 2 respectively because a self-loop contributes two to undirected degree.

## 6. Analytical Detailed Graph

The analytical detailed graph is copied from the provenance graph and then has only the registered anomaly fragments removed. Env38 therefore retains all 147 nodes and has 171 edges, no self-loops, and one component. Env39 has no registered artifact, so its analytical and provenance detailed graphs are structurally identical at 53 nodes, 72 edges, no self-loops, and one component.

## 7. Geometry-Only Degree-2 Nodes

A node is suppressible only when its analytical undirected degree is exactly two, it has two distinct neighbours, it is not a validated Phase 9 crossing, and it is not needed to represent a self-loop, parallel-edge structure, or isolated cycle. A Unity source Bezier boundary alone is not a retention reason. Endpoints, branches, validated junctions, and structural safety nodes remain.

Suppressing a continuation node replaces its incident path with one merged edge, so graph connectivity is preserved rather than performing a bare node deletion.

## 8. Topological Simplification

The deterministic algorithm walks every maximal chain outward from retained nodes. It visits every analytical detailed edge exactly once. Internal degree-2 continuation nodes are suppressed, and contributing fragments are merged in traversal order. Node IDs, fragment IDs, and edge iteration are lexically deterministic.

At geometry joins, only the exactly duplicated shared coordinate is removed. Coordinates are not rounded, smoothed, resampled, projected, translated, rotated, normalized, or flipped. Ordered fragment, Shape, source segment, and source-parameter provenance is retained on the merged edge.

## 9. Geometry and Length Preservation

Each simplified edge stores the sum of its detailed-fragment lengths, the length recomputed from concatenated geometry, and their difference. The documented absolute QA tolerance is `1e-10` Unity world units.

For both environments the total simplified-minus-detailed length error is exactly `0.0` in the recorded floating-point summation. The largest absolute per-edge difference is `1.4210854715202004e-14` Unity world units, safely below the QA tolerance. These values validate construction only; they are not final street-length metrics.

## 10. Parallel Edges

The provenance Env38 graph reports one repeated endpoint pair because two registered self-loop artifacts share one topology location. Once the five registered artifacts are excluded, neither current analytical simplified graph contains geometrically distinct parallel edges. The implementation and synthetic tests nevertheless preserve parallel edges and deterministic keys if they occur; no simple-graph collapse is performed.

## 11. Cycle Handling

Traversal records visited keyed edges, preventing infinite walks or arbitrary deletion. If an isolated component consists entirely of degree-2 nodes, the lexically first node is retained and the complete cycle is represented as a self-loop geometry at that node. Synthetic tests verify this behavior.

## 12. Simplified Analytical Graph

Env38 suppresses 87 geometry-only nodes, producing 60 retained nodes and 84 undirected edges. Env39 suppresses 2, producing 51 nodes and 70 edges. Both remain one connected component. All 28 Env38 and 20 Env39 validated Phase 9 junctions remain graph nodes.

These node and edge counts describe the graph-construction result and are not final intersection, dead-end, or street statistics.

## 13. Bidirectional MultiDiGraph Adapter

Each simplified undirected edge is represented twice in a `networkx.MultiDiGraph`: one forward and one reverse directed edge. Length and provenance attributes are identical, while reverse geometry and ordered provenance sequences are reversed. There are no authored one-way semantics.

The resulting QA counts are 60 nodes and 168 directed edges for Env38, and 51 nodes and 140 directed edges for Env39.

## 14. OSMnx Structural Conventions

CRS-less GeoDataFrames are created with a unique node index named `osmid` and edge MultiIndex `(u, v, key)`. Nodes contain `x`, `y`, `topology_id`, provenance, and Point geometry. Directed edges contain LineString geometry, QA length, simplified edge identity, and full ordered provenance.

With OSMnx 2.1.1, `osmnx.convert.graph_from_gdfs` accepted both CRS-less table pairs when supplied explicit Unity coordinate-system graph attributes. Node and edge counts were preserved. This demonstrates structural compatibility only.

## 15. CRS Limitation

No CRS is assigned: graph and GeoDataFrame CRS values are `None`. Unity X/Y is not longitude/latitude. No EPSG code, projection, verified metre conversion, or geographic north is inferred. Consequently, the graphs are not eligible for OSMnx operations that require geographic or projected real-world semantics.

## 16. Why Geographic OSMnx Bearing Functions Are Not Used

OSMnx geographic bearing, orientation-entropy, great-circle edge-length, intersection-consolidation, and automatic graph-simplification functions are not called. Their assumptions would conflict with Unity coordinates, zero canonical snapping, or the authoritative provenance-preserving simplification. A later phase must define any planar orientation convention explicitly.

## 17. GraphML Serialization

Eight GraphML files are saved under `data/graphs/`: provenance detailed, analytical detailed, analytical simplified, and OSMnx-style bidirectional variants for each environment. Complex list, dictionary, tuple, and null attributes are stored as canonical JSON-prefixed strings rather than discarded. Each GraphML file has a companion JSON manifest containing its hash, source topology hash, graph attributes, QA summary, and round-trip result.

## 18. Round-Trip Validation

Every GraphML file is loaded immediately after writing. Validation checks node and edge counts, graph direction and multigraph type, node IDs, edge keys, exact coordinates, topology/provenance IDs, detailed geometry, component count, and zero-chord inclusion policy. All eight round trips pass.

## 19. Env38 Graph QA

| Variant | Nodes | Edges | Self-loops | Components | Validated junctions | Artifact edges |
|---|---:|---:|---:|---:|---:|---:|
| Provenance detailed | 147 | 176 | 5 | 1 | 28 | 5 |
| Analytical detailed | 147 | 171 | 0 | 1 | 28 | 0 |
| Analytical simplified | 60 | 84 | 0 | 1 | 28 | 0 |
| Bidirectional adapter | 60 | 168 | 0 | 1 | 28 | 0 |

Visual QA confirms detailed geometry, retained/suppressed nodes, and validated junction markers are coherent and plotted at equal aspect in unmodified Unity X/Y.

## 20. Env39 Graph QA

| Variant | Nodes | Edges | Self-loops | Components | Validated junctions | Artifact edges |
|---|---:|---:|---:|---:|---:|---:|
| Provenance detailed | 53 | 72 | 0 | 1 | 20 | 0 |
| Analytical detailed | 53 | 72 | 0 | 1 | 20 | 0 |
| Analytical simplified | 51 | 70 | 0 | 1 | 20 | 0 |
| Bidirectional adapter | 51 | 140 | 0 | 1 | 20 | 0 |

Visual QA confirms the same coordinate, aspect, and junction-retention requirements.

## 21. Limitations

The graphs describe validated planar topology and detailed Unity geometry. They do not establish a real-world CRS, distance unit, latitude/longitude, traffic direction, geographic north, or semantic street naming. Artifact exclusion is limited to the five previously registered source IDs. Simplification retains topology and provenance but does not yet define final analytical street units or scientific reporting conventions.

## 22. Phase-11 Acceptance Checklist

- [x] Canonical raw hashes reverified.
- [x] Phase 10 selected/exact consistency and zero snapping verified.
- [x] Provenance graphs contain every Phase 10 node and fragment.
- [x] Five registered Env38 artifacts remain in provenance and only those five are analytically excluded.
- [x] No numerical short-edge filter is used.
- [x] All 48 validated crossings remain nodes.
- [x] Degree-2 simplification preserves geometry, QA length, and component count.
- [x] Parallel-edge and isolated-cycle safety are implemented and tested.
- [x] Bidirectional adapters and CRS-less structural tables are valid.
- [x] All eight GraphML round trips pass with provenance intact.
- [x] No fake CRS or geographic interpretation is assigned.
- [x] No CRS-dependent OSMnx bearing/distance operation is used.
- [x] No final morphology metric is calculated.

## 23. Deferred Phase-12 Metrics

Final orientation, entropy, order, circuity, street-length, dead-end, intersection-proportion, and comparative scientific calculations remain deferred. Phase 11 does not begin Phase 12 or choose its planar orientation convention.
