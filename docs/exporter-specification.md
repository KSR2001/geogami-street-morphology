# Phase 2: Lossless Unity-to-JSON Exporter Specification

Status: frozen design contract for Phase 3. Phase 2 defines the extraction boundary and JSON format only; it does not implement the exporter or create export files.

## 1. Purpose and Scope

The future exporter is a lossless extraction layer between the authoritative Unity authoring data and the external street-morphology workflow. Its sole transformation is:

`Unity source geometry` → `reproducible raw JSON`

It must preserve source geometry and provenance without interpreting the road network. Responsibilities remain separated as follows:

- **Unity exporter:** source extraction of Shapes2D quadratic Bézier segments and their provenance.
- **Later Python/GIS processing:** reconstruction and validation of detailed curve geometry.
- **Later NetworkX/OSMnx processing:** topology and network analysis after geometry and navigability QA.

The exporter must not sample curves, reconstruct intersections, build a graph, or calculate scientific metrics. Its output is the immutable raw representation defined by the methodology.

## 2. Authoritative Input

The authoritative inputs are the 2D authoring prefabs:

`2D Map Vir 38` → `Roads` → `Line Path` → `Shapes2D.Shape`

`2D Map Vir 39` → `Roads` → `Line Path` → `Shapes2D.Shape`

Their verified Unity asset paths are:

- `Assets/Tools/VirtualEnvironmentCreation/2DMapPrefabs/2D Map Vir 38.prefab`
- `Assets/Tools/VirtualEnvironmentCreation/2DMapPrefabs/2D Map Vir 39.prefab`

The exporter must select `Shapes2D.Shape` Path components under the exact `Roads` hierarchy and iterate each Shape's `PathSegment[]`. A `Line Path` or Shape is a Shapes2D geometry container, not one semantic street. It may contain connected or branching geometry, and its object count is constrained by Shapes2D's declared 32-segment maximum. The exporter must not assign street semantics to these containers.

Screenshots, manual traces, terrain textures, generated 3D meshes, and `Map2D.GetLines()` are not authoritative inputs.

## 3. Bézier Geometry Contract

Every source segment is a quadratic Bézier defined by three `Vector3` values:

- `p0`: start endpoint;
- `p1`: quadratic control point; and
- `p2`: end endpoint.

For `0 ≤ t ≤ 1`, its mathematical geometry is:

`B(t) = (1-t)^2 p0 + 2(1-t)t p1 + t^2 p2`.

The JSON must preserve all three vectors in both original/local and transformed/world forms. The three values are curve parameters, not the vertices of an ordinary three-point polyline. The exporter must neither convert them into such a polyline nor reduce the curve to the straight chord `p0 → p2`.

## 4. Extraction APIs

The future exporter must read original/local segments through the verified public accessor:

`shape.settings.pathSegments`

It must retrieve Shapes2D-transformed segments through:

`shape.GetPathWorldSegments()`

The two arrays must have identical lengths, and segment at index `i` in the local array must be paired with segment at index `i` in the world array. Any length mismatch is a validation failure.

`GetPathWorldSegments()` is preferred over manually reconstructing coordinates because it implements Shapes2D's own normalized-coordinate conversion, parent-aware Transform handling, and RectTransform handling. The exporter must preserve Transform metadata for auditability but must not substitute an independently recreated transform for this API.

The current verified implementation maps through a `Vector2` helper and returns planar values in `Vector3` fields. The exporter must serialize the returned `x`, `y`, and `z` values exactly as supplied, including `z`; it must not invent a different world-space z value.

The exporter must not use `Map2D.GetLines()`. That method creates endpoint-only NetTopologySuite LineStrings from `p0` and `p2` and omits `p1`, thereby linearizing each quadratic curve. No existing source class may be altered to expose or extract the data.

## 5. Export Hierarchy

The raw hierarchy is fixed as:

`Environment` → `Shape` → `Segment` → `local p0/p1/p2` + `world p0/p1/p2`

The exporter must preserve:

- environment identity;
- Shape identity;
- segment identity;
- deterministic Shape ordering; and
- Unity `PathSegment[]` array ordering.

Only qualifying `Shapes2D.Shape` Path components are included. For the canonical prefabs, Shapes are ordered by their stable prefab-local Shape component file IDs, compared numerically in ascending order. This reproduces the Phase 1 inventory sequence for Environment 38 (`4, 32, 32, 24, 28`); Transform sibling order does not reproduce that sequence and therefore is not the canonical Shape order.

The exporter must preserve both the GameObject and Shape component prefab-local file IDs as decimal strings. Strings are required because the verified 64-bit values exceed JSON's universally safe integer range. Each exported Shape receives a one-based `shape_index` after the file-ID sort; each segment receives a one-based `segment_index` matching its position in the source array plus one.

Deterministic IDs are derived as follows:

- `shape_id`: `env<environment_id>_shape_<source_shape_component_file_id>`, for example `env38_shape_4330855546755831596`.
- `segment_id`: `<shape_id>_segment_` plus a four-digit, zero-padded `segment_index`, for example `env38_shape_4330855546755831596_segment_0001`.

`hierarchy_path` must include GameObject names and Transform sibling indices so duplicate `Line Path` names remain distinguishable. Its canonical form is slash-separated `Name[siblingIndex]` components from the prefab root through the Shape GameObject. Sibling indices are Unity's zero-based `Transform.GetSiblingIndex()` values.

The exporter must not merge Shapes, infer streets, invent street names, reorder geometry according to connectivity, or classify junctions.

## 6. JSON Schema

### Schema version

The first exporter contract uses `schema_version: "1.0.0"`. Phase 3 must emit exactly this version unless the contract is deliberately revised. Backward-incompatible field or semantic changes require a new major version.

Each environment is exported as one UTF-8 JSON object. The following JSON is the normative field structure; numeric placeholders illustrate types and are not example geometry or calculated results:

```json
{
  "schema_version": "1.0.0",
  "exporter_name": "GeoGami Road Bézier Exporter",
  "exporter_version": "1.0.0",
  "export_timestamp_utc": "YYYY-MM-DDTHH:MM:SS.fffZ",
  "environment_id": 38,
  "environment_label": "Curvilinear / Curvy",
  "source_prefab_name": "2D Map Vir 38",
  "source_prefab_asset_path": "Assets/Tools/VirtualEnvironmentCreation/2DMapPrefabs/2D Map Vir 38.prefab",
  "source_unity_version": "2022.3.62f3",
  "source_git_branch": "analysis/osmnx-env38-env39",
  "source_git_commit": "b4f10aede3cf7b825e9cf9ee25bbc42c0fa0a55e",
  "source_git_worktree_dirty": true,
  "coordinate_space": {
    "local": "shapes2d_normalized_local",
    "world": "shapes2d_get_path_world_segments"
  },
  "units": {
    "local": "normalized_shape_units",
    "world": "unity_world_units"
  },
  "meter_scale_verified": false,
  "meters_per_unity_world_unit": null,
  "shape_count": 5,
  "segment_count": 120,
  "shapes": [
    {
      "shape_index": 1,
      "shape_id": "env38_shape_4330855546755831596",
      "source_game_object_file_id": "4330855546755831761",
      "source_shape_component_file_id": "4330855546755831596",
      "game_object_name": "Line Path",
      "hierarchy_path": "2D Map Vir 38[0]/Roads[0]/Line Path[4]",
      "segment_count": 4,
      "path_thickness": 0.0,
      "fill_path_loops": false,
      "transform": {
        "local_position": { "x": 0.0, "y": 0.0, "z": 0.0 },
        "local_rotation_quaternion": { "x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0 },
        "local_scale": { "x": 1.0, "y": 1.0, "z": 1.0 },
        "local_to_world_matrix": {
          "m00": 0.0, "m01": 0.0, "m02": 0.0, "m03": 0.0,
          "m10": 0.0, "m11": 0.0, "m12": 0.0, "m13": 0.0,
          "m20": 0.0, "m21": 0.0, "m22": 0.0, "m23": 0.0,
          "m30": 0.0, "m31": 0.0, "m32": 0.0, "m33": 0.0
        }
      },
      "segments": [
        {
          "segment_index": 1,
          "segment_id": "env38_shape_4330855546755831596_segment_0001",
          "local": {
            "p0": { "x": 0.0, "y": 0.0, "z": 0.0 },
            "p1": { "x": 0.0, "y": 0.0, "z": 0.0 },
            "p2": { "x": 0.0, "y": 0.0, "z": 0.0 }
          },
          "world": {
            "p0": { "x": 0.0, "y": 0.0, "z": 0.0 },
            "p1": { "x": 0.0, "y": 0.0, "z": 0.0 },
            "p2": { "x": 0.0, "y": 0.0, "z": 0.0 }
          }
        }
      ]
    }
  ]
}
```

### Field rules

- `export_timestamp_utc` is an RFC 3339 UTC timestamp ending in `Z`. It is provenance, not geometry.
- `environment_id` is the integer `38` or `39`.
- `environment_label` is exactly `Curvilinear / Curvy` for 38 or `Grid-like / Grid` for 39.
- `source_prefab_asset_path` is required for the two canonical exports and must be a Unity project-relative asset path, never a user-specific absolute path.
- `source_unity_version` records the version used for the export, not an assumed version from an older commit.
- `source_git_commit` is a 40-character SHA when it can be established reliably. If it cannot, the field is `null` and the exporter must issue a provenance warning rather than invent a value.
- `source_git_branch` is a string when reliably available and otherwise `null`.
- `source_git_worktree_dirty` is a Boolean when reliably available and otherwise `null`.
- `meter_scale_verified` must remain `false`, and `meters_per_unity_world_unit` must remain `null`, until a later phase validates physical scale.
- `shape_count` equals `shapes.length`; top-level `segment_count` equals the sum of per-Shape `segment_count` values.
- `source_game_object_file_id` and `source_shape_component_file_id` are required decimal strings containing stable prefab-local identifiers obtained through Unity Editor serialization APIs. They must never be emitted as JSON numbers.
- `path_thickness` is the unrounded source value from `shape.settings.pathThickness`.
- `fill_path_loops` is the Boolean source value from `shape.settings.fillPathLoops`.
- `local_rotation_quaternion` stores the Transform's local quaternion, not Euler angles.
- `local_to_world_matrix` stores all 16 `Matrix4x4` components using Unity's `m<row><column>` names.
- Every vector and matrix component is a JSON number. JSON strings such as `"NaN"` or `"Infinity"` are forbidden; encountering a non-finite value is an export validation failure.
- `shapes` and `segments` are arrays whose order is part of the contract.

No sampled points, intersections, graph-node IDs, inferred street IDs, bearings, or calculated geometry fields are permitted in schema version 1.0.0.

## 7. Coordinate Policy

- Original Shapes2D values are serialized as local/normalized Shape coordinates.
- Transformed values are taken directly from `GetPathWorldSegments()` and labelled as Shapes2D API-derived Unity world coordinates.
- All `x`, `y`, and `z` components of every local and world `p0`, `p1`, and `p2` must be emitted. No component may be omitted merely because current data are planar or zero.
- Later analysis may establish which planar axes are appropriate, but the exporter must not make that analytical decision.
- World values use Unity world units. They must not be labelled metres, kilometres, or another physical unit.
- No coordinate reference system is established in Phase 2. The exporter must not invent a CRS, WGS84 coordinates, synthetic latitude/longitude, or a projection.

The Phase 1 finding that the present Shapes2D world-segment implementation uses a `Vector2` interpolation helper is retained. Serializing its returned `Vector3.z` is required; replacing the API result with an independently inferred 3D coordinate is forbidden.

## 8. Transform Provenance

Each Shape must retain its Transform local position, local rotation quaternion, local scale, and complete local-to-world matrix even though transformed control points are also exported. This redundant provenance is intentional: it allows later audits to diagnose unexpected local/world discrepancies, hierarchy changes, scaling, rotations, or API behavior without modifying the raw coordinates.

Transform metadata is evidence, not an instruction for the exporter to recompute the world points. The authoritative transformed segment values remain those returned by `GetPathWorldSegments()`.

## 9. Precision Policy

All source floats must be serialized using an invariant culture and a round-trip representation sufficient to recover the original Unity single-precision value. Coordinates, Transform values, matrices, path thickness, and other source floats must not be intentionally rounded, truncated, reformatted to a fixed number of decimal places, or converted through a lower-precision intermediate representation.

The JSON writer may use the shortest decimal representation that round-trips to the identical IEEE 754 binary32 value. Presentation rounding belongs only in later figures and result tables, never in raw exports.

## 10. Prohibited Operations

The future Unity exporter is forbidden from performing:

- Bézier discretization;
- Bézier sampling;
- curve densification;
- `p0 → p2` linearization;
- snapping;
- endpoint merging;
- endpoint deduplication;
- geometric intersection detection;
- topology reconstruction;
- road splitting;
- road simplification;
- junction classification;
- NetworkX graph creation;
- OSMnx graph creation;
- CRS transformation;
- synthetic latitude/longitude generation;
- bearing calculation;
- street-length research calculations;
- orientation entropy;
- orientation order;
- circuity;
- connectivity metrics; or
- any final scientific metric.

It must not infer semantic streets, connectivity, intersections, dead ends, or navigability. The exporter is a source-data extraction tool only.

## 11. Output Files

The two primary filenames are fixed as:

- `env38_bezier.json`
- `env39_bezier.json`

The implementation must not hard-code `F:\GitHub\geogami-street-morphology` or any other machine- or user-specific absolute destination. It must either ask the user to select an output directory or write to a clearly isolated Unity-project-relative export location. It must not write into a source prefab or runtime asset directory.

After Phase 3 validation, the two validated files will be copied deliberately into `geogami-street-morphology/data/raw/`. Phase 2 creates neither JSON file.

## 12. Quality-Control Assertions

Before reporting an export as successful or replacing a canonical output file, the exporter must validate:

| Environment | Expected Shapes | Expected per-Shape segment counts | Expected total segments |
|---|---:|---|---:|
| 38 | 5 | `4, 32, 32, 24, 28` | 120 |
| 39 | 1 | `32` | 32 |

It must additionally assert that:

- every selected component is a `Shapes2D.Shape` Path under `Roads`;
- local and world segment arrays have equal lengths;
- each segment contains finite local and world `p0`, `p1`, and `p2` components;
- the per-Shape counts equal their `segments` array lengths; and
- aggregate counts equal the sum of per-Shape counts.

If the current source disagrees with expected inventory, the exporter must report the environment, actual Shape count, actual per-Shape counts, and actual total clearly, mark validation as failed, and abort the canonical output write. It must not silently continue as though QA passed, edit source geometry, discard segments, add segments, or otherwise force the expected values. The source remains authoritative; these expectations are discrepancy detectors, not transformation rules.

## 13. Determinism Requirement

Two exports from the same unchanged Unity source and exporter version must contain geometrically identical:

- Shape membership and ordering;
- segment membership and ordering;
- IDs and hierarchy paths;
- local `p0`, `p1`, and `p2`;
- world `p0`, `p1`, and `p2`; and
- Transform metadata.

Only genuinely variable provenance, such as `export_timestamp_utc`, may differ. Shape discovery must not determine output order. After discovery, Shapes must be sorted by their stable prefab-local Shape component file IDs using a numeric, locale-independent comparison. Ordering must not depend on Transform sibling order, object discovery order, dictionary/hash iteration, transient Unity instance IDs, filesystem enumeration order, or a locale-sensitive name sort. Segment order must be the original `PathSegment[]` array order. JSON field ordering should also be stable to support transparent file diffs, although object-member order does not change JSON semantics.

Repeated-export acceptance compares the complete parsed structures after excluding only explicitly variable provenance fields. It must not use rounded coordinates for comparison.

## 14. Safety Requirements

The future exporter must be:

- Unity Editor-only;
- non-destructive;
- read-only with respect to source road geometry;
- isolated from runtime gameplay;
- isolated from networking;
- isolated from environment generation; and
- implemented as new analysis tooling.

The exporter must never call `SetPathWorldSegments()`, assign to `shape.settings.pathSegments`, change a Transform, mark a source object dirty, save a source prefab, or invoke any other geometry-changing operation.

It must not modify:

- `Shape.cs`;
- `Map2D.cs`;
- `ShapeEditor.cs`;
- Environment 38 or Environment 39 prefabs; or
- runtime networking or gameplay scripts.

Selection and export must not invoke `Map2D.Run()` or any environment-generation path.

## 15. Planned Unity Implementation Location

The preferred Phase 3 location is:

`GeoGami-Vir-Env/Assets/Editor/StreetNetworkAnalysis/RoadBezierExporter.cs`

It must be a new Editor-only file in an isolated analysis-tooling directory. A separate new serializable data-contract file may be added beside it only if implementation clarity requires it. No existing Shapes2D, GeoGami runtime, networking, gameplay, generation, or prefab file may need modification.

No C# file is created in Phase 2.

## 16. Dirty Unity Working-Tree Policy

The Unity repository already contains unrelated deleted, modified, and untracked files. They must intentionally remain untouched: do not clean, reset, stash, restore, delete, or reformat them as part of exporter work.

Before and after Phase 3 implementation:

- record `git status --short` without changing it;
- use path-specific `git status --short -- <paths>` and `git diff -- <paths>` for exporter verification;
- isolate all analysis additions under the planned Editor tooling path;
- inspect the exact exporter diff before staging; and
- stage only explicit exporter-related paths.

Broad staging such as `git add .`, `git add -A`, or staging the Unity project root is prohibited in the dirty Unity repository. Any future exporter commit must name only the new exporter-related files. Existing unrelated modifications must not be included.

## 17. Phase-3 Acceptance Criteria

Phase 3 is successful only when all of the following hold:

- [ ] An Editor-only exporter is implemented as isolated new tooling.
- [ ] `env38_bezier.json` is exported.
- [ ] `env39_bezier.json` is exported.
- [ ] Environment 38 Shape count is 5.
- [ ] Environment 38 total segment count is 120.
- [ ] Environment 38 per-Shape counts are `4, 32, 32, 24, 28`.
- [ ] Environment 39 Shape count is 1.
- [ ] Environment 39 total segment count is 32.
- [ ] Both JSON files parse successfully as schema version 1.0.0.
- [ ] Every segment has local `p0`, `p1`, and `p2` with all x/y/z components.
- [ ] Every segment has world `p0`, `p1`, and `p2` with all x/y/z components.
- [ ] Every Shape has the required Transform metadata.
- [ ] No source Shape was modified.
- [ ] No source prefab was modified.
- [ ] No existing runtime file was modified.
- [ ] Repeated export from unchanged input produces identical geometry and stable ordering.
- [ ] Git diff/status inspection shows only intentional exporter-related additions.
- [ ] Validated JSON files are copied deliberately into `geogami-street-morphology/data/raw/`.

Passing count checks alone is insufficient; schema completeness, source immutability, determinism, and successful JSON parsing are also mandatory.

## 18. Explicitly Deferred Work

All of the following remain outside Phase 2 documentation work and outside Phase 3 extraction logic:

- Bézier reconstruction in Python;
- adaptive curve sampling;
- convergence analysis;
- physical scale verification;
- plotting reconstructed geometry;
- Shapely;
- GeoPandas;
- intersection reconstruction;
- snapping-tolerance selection;
- topology reconstruction;
- NetworkX;
- OSMnx;
- geographic-coordinate strategy;
- bearings;
- entropy;
- orientation order;
- circuity;
- connectivity metrics; and
- the final Environment 38 versus Environment 39 comparison.

These operations belong to later validated processing and analysis phases. They must not leak into the raw export contract.
