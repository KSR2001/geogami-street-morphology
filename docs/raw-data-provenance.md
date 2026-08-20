# Phase 4: Raw Bézier Data Provenance and Integrity

## 1. Phase 4 Scope

Phase 4 freezes the validated Unity road extraction as immutable research input. It validates provenance, schema completeness, inventory, exact repeat-export determinism, file integrity, coordinate planarity, and known source-data anomalies.

All checks were performed with standard-library JSON, mathematics, and SHA-256 tooling. No GIS dependency was installed or used. Phase 4 does not reconstruct or sample Bézier curves, create linework or graphs, infer topology, or calculate morphology metrics. No coordinate or metadata value in the four exporter-produced JSON files was changed.

## 2. Canonical Raw Files

The canonical research inputs are:

- `data/raw/env38_bezier.json`
- `data/raw/env39_bezier.json`

| File | Environment | Source export timestamp (UTC) | Shapes | Ordered segment counts | Total segments |
|---|---:|---|---:|---|---:|
| `env38_bezier.json` | 38 | `2026-08-18T18:27:10.401Z` | 5 | `4, 32, 32, 24, 28` | 120 |
| `env39_bezier.json` | 39 | `2026-08-18T18:27:10.401Z` | 1 | `32` | 32 |

After Phase 4, these two files are immutable canonical research inputs. Corrections or alternative processing must not overwrite them; they require newly named/versioned source exports or derived files, with the change documented explicitly.

## 3. Independent Determinism Run

The independent second export is retained at:

- `outputs/qa/export-determinism/run2/env38_bezier.json`
- `outputs/qa/export-determinism/run2/env39_bezier.json`

Both run-2 files record `export_timestamp_utc = 2026-08-18T18:30:26.120Z`. Each passed the same schema, inventory, segment-completeness, ID, finite-coordinate, component-ID, provenance, and planarity checks as its canonical counterpart.

The run-2 exports are QA evidence. The files in `data/raw/` remain the canonical inputs.

## 4. Source Unity Provenance

The canonical JSON records:

- Unity version: `2022.3.62f3`
- Git branch: `analysis/osmnx-env38-env39`
- source Git commit: `b4f10aede3cf7b825e9cf9ee25bbc42c0fa0a55e`
- `source_git_worktree_dirty = true`
- `meter_scale_verified = false`
- `meters_per_unity_world_unit = null`

The dirty-state flag is material provenance and must not be hidden. Phase 1 independently established that unrelated, pre-existing working-tree changes were present elsewhere in the Unity checkout. It also verified with path-specific Git status checks that the authoritative `Shape.cs`, `Map2D.cs`, Environment 38 prefab, and Environment 39 prefab used for this analysis were clean relative to the recorded HEAD commit.

No metre conversion is inferred. Coordinate lengths remain in Unity-derived world units, and no geographic coordinate reference system is assigned.

## 5. Schema and Inventory Validation

All four files parse successfully as UTF-8 JSON and declare `schema_version = 1.0.0`.

| Dataset | Environment ID | Shape count | Ordered per-Shape counts | `segment_count` | `total_segment_count` | Result |
|---|---:|---:|---|---:|---:|---|
| Canonical Environment 38 | 38 | 5 | `4, 32, 32, 24, 28` | 120 | 120 | PASS |
| Run 2 Environment 38 | 38 | 5 | `4, 32, 32, 24, 28` | 120 | 120 | PASS |
| Canonical Environment 39 | 39 | 1 | `32` | 32 | 32 | PASS |
| Run 2 Environment 39 | 39 | 1 | `32` | 32 | 32 | PASS |

Every segment in every file has local and world `p0`, `p1`, and `p2`; every point has exactly `x`, `y`, and `z`; and every coordinate is a finite JSON number. Segment indices are sequential and every segment ID equals its Shape ID plus `_segment_` and the four-digit segment index. Shape indices are sequential.

The canonical Shape component IDs are unique and numerically ascending:

- Environment 38: `4330855546755831596`, `4330855547456548042`, `4330855547524397474`, `4330855547529842337`, `4330855547829185599`
- Environment 39: `3305298596651482022`

The run-2 files contain the identical ordered component IDs.

## 6. Determinism Result

**PASS for Environment 38 and Environment 39.**

For each environment, Phase 4 parsed the canonical and run-2 JSON, removed only the top-level `export_timestamp_utc`, and compared deterministic canonical serializations without a coordinate tolerance. The remaining complete structures were byte-for-byte identical after canonical serialization. No other metadata or data field was excluded.

## 7. File Hashes

These SHA-256 values cover the canonical files exactly as stored on disk, including their original formatting and `export_timestamp_utc`:

| Canonical file | SHA-256 |
|---|---|
| `data/raw/env38_bezier.json` | `43ea446a4a88e9f3d594fb8b72742f5d4b2a1ee8a03ebf8350c4c3cce45c5819` |
| `data/raw/env39_bezier.json` | `e5dbce6b4d88656c9e0f3bbf6a814434f64b0fbe9b3ff1864ea3fafaf0883602` |

Any byte-level change to a canonical file—including whitespace or metadata—will change its file hash and must be investigated.

## 8. Timestamp-Independent Fingerprints

The timestamp-independent fingerprint procedure is:

1. Decode the stored file as UTF-8 and parse it as JSON.
2. Remove only the top-level `export_timestamp_utc` member.
3. Serialize with object keys sorted lexicographically, arrays unchanged, no insignificant whitespace (`','` and `':'` separators), Unicode emitted directly rather than ASCII-escaped, and non-finite numbers forbidden.
4. Encode that serialization as UTF-8 without a byte-order mark.
5. Calculate SHA-256 over those bytes.

This is the Phase 4 canonicalization procedure; it is not presented as a general JSON Canonicalization Scheme standard.

| Environment | Recomputed fingerprint | Independent-review expectation | Result |
|---:|---|---|---|
| 38 | `8480876d91fd62e86077755d37ef59c0a2b1db32feb79947f56012ed64453d4d` | `8480876d91fd62e86077755d37ef59c0a2b1db32feb79947f56012ed64453d4d` | MATCH |
| 39 | `9a09801089782ded7fa63061a8b3164d56d39ae9985ed02face9f61538788151` | `9a09801089782ded7fa63061a8b3164d56d39ae9985ed02face9f61538788151` | MATCH |

Each run-2 file produces the same fingerprint as its canonical counterpart.

## 9. Coordinate-Space Observations

All local and world `p0`, `p1`, and `p2` z values in all four files were checked exactly and equal zero.

> The road Bézier control geometry exported for both environments lies in the XY plane (all segment control-point z coordinates equal zero).

This is an observed extraction fact, not evidence of geographic north, a projected coordinate system, or a metre conversion. Phase 4 creates no CRS and makes no directional-reference inference.

## 10. Known Raw-Source Anomalies

Five Environment 38 segments have exactly equal world `p0` and world `p2`, producing a zero-length endpoint chord. Independent validation found precisely the expected IDs:

| Segment ID | World-space `p1` displacement from `p0` |
|---|---:|
| `env38_shape_4330855547529842337_segment_0006` | `0.00006860029153709445` |
| `env38_shape_4330855547529842337_segment_0019` | `0.00011799999998629573` |
| `env38_shape_4330855547829185599_segment_0007` | `0.0003217530108635848` |
| `env38_shape_4330855547829185599_segment_0011` | `0.0006070782568995186` |
| `env38_shape_4330855547829185599_segment_0012` | `0.0007152999999995302` |

Displacements are Euclidean distances in Unity world units calculated only for anomaly QA. They are extremely small, and Environment 39 has no zero-chord segment.

These segments are preserved unchanged as raw-source authoring artifacts. They are not deleted, filtered, deduplicated, or removed from the count of 120. Their treatment must be an explicit, documented decision during later derived-geometry QA, with any resulting data written outside `data/raw/`.

## 11. Immutability Policy

`data/raw/env38_bezier.json` and `data/raw/env39_bezier.json` are immutable canonical research inputs after Phase 4.

Any cleaning, filtering, sampling, snapping, topology reconstruction, coordinate conversion, anomaly handling, or other transformation must create new files under `data/processed/`. Processing code must read from `data/raw/` without rewriting it. The canonical file hashes in this document and `data/raw/manifest.json` are the integrity checks for future work.

The manifest summarizes the frozen dataset and may be versioned separately if provenance documentation is corrected; it must never be used to replace or duplicate the road geometry.

## 12. Deferred Processing Decisions

Phase 4 intentionally leaves the following for later phases:

- Bézier reconstruction and adaptive sampling;
- sampling-convergence thresholds;
- explicit handling of zero-chord source artifacts in derived geometry;
- Unity-world-unit-to-metre validation;
- common north/reference direction and planar-axis interpretation;
- intersection detection and snapping tolerance;
- grade-separated crossing validation;
- topology reconstruction and road splitting;
- Shapely, GeoPandas, NetworkX, and OSMnx processing;
- bearings, entropy, orientation order, circuity, connectivity, and other morphology metrics; and
- final comparison of Environment 38 and Environment 39.

No decision about these operations is encoded by the raw freeze.

## 13. Phase-4 Acceptance Checklist

- [x] Both canonical raw JSON files exist and parse successfully.
- [x] Both run-2 QA JSON files exist and parse successfully.
- [x] Schema version, environment IDs, Shape counts, ordered per-Shape counts, and total counts pass.
- [x] Every segment has complete finite local and world `p0`/`p1`/`p2` x/y/z values.
- [x] Segment indices and IDs pass sequential consistency checks.
- [x] Shape component IDs are unique and numerically ascending.
- [x] Canonical and run-2 structures are exactly equal after excluding only `export_timestamp_utc`.
- [x] Canonical byte-level SHA-256 hashes are recorded.
- [x] Timestamp-independent fingerprints match the independent-review expectations.
- [x] All exported control-point z coordinates equal zero.
- [x] The five expected Environment 38 zero-chord anomalies are independently verified and retained.
- [x] Dirty Unity working-tree provenance and the Phase 1 path-specific cleanliness finding are recorded.
- [x] Metre scale remains explicitly unverified.
- [x] Canonical raw geometry and metadata remain unchanged.
- [x] No later-phase geometry or network analysis was started.
