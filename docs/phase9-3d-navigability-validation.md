# Phase 9 3D Navigability Validation

## 1. Phase 9 Scope

Phase 9 adds 3D navigability evidence to the 48 Phase 8 `interior_interior_crossing` events. It preserves every Phase 8 event ID, source coordinate, segment and Shape identity, parameter pair, residual, same-Shape flag, and anomaly flag. It does not revise the Phase 8 mathematics.

The result is **BLOCKED PENDING MANUAL 3D REVIEW**: all 48 events remain `manual_review_required`. This is a conservative validation result, not a failed analysis and not permission to begin Phase 10.

## 2. Reason for 3D Validation

A planar curve crossing says only that two authored quadratic Béziers occupy the same Unity world XY coordinate. It does not show whether the participant-facing 3D roads meet, pass at different elevations, or are separated by a gap or barrier. The morphology labels “curvilinear” and “grid-like” provide no connectivity evidence.

## 3. Phase-8 Input Inventory

The required Phase 8 event table, 3D-review table, machine-readable QA record, Phase 7 detailed linework, and Phase 8 QA figures were present. The review inventory contains 48 events: 28 in Env38 and 20 in Env39. The Phase 8 event and review CSV SHA-256 values are recorded in `outputs/qa/phase9-3d-navigability-validation.json`.

The frozen raw hashes were reverified:

- Env38: `43ea446a4a88e9f3d594fb8b72742f5d4b2a1ee8a03ebf8350c4c3cce45c5819`
- Env39: `e5dbce6b4d88656c9e0f3bbf6a814434f64b0fbe9b3ff1864ea3fafaf0883602`

## 4. Unity 2D Environment Source

The canonical authored road sources are:

- `Assets/Tools/VirtualEnvironmentCreation/2DMapPrefabs/2D Map Vir 38.prefab`
- `Assets/Tools/VirtualEnvironmentCreation/2DMapPrefabs/2D Map Vir 39.prefab`

Each root is a rotated built-in Unity Plane with a `Map2D` component. The Env38 root position/scale is `(220.1124, 100, 265.6392)` / `(44.000023, 1.0000002, 53.100018)`; Env39 uses the same position and `(44, 1, 53.1)`. The roots reference `VirtualEnvironmentNumber` 38 and 39 respectively.

`Assets/Tools/Shapes2D/Scripts/Shape.cs`, class `Shape`, method `GetPathWorldSegments()` (lines 1373–1388 in the inspected working tree) maps all three quadratic control points through `BiLerp`. These Unity world XY values are the Phase 8 coordinate source.

## 5. Unity 3D Environment Source

The corresponding generated 3D assets are:

- `Assets/Prefabs/VIrtualEnvironments/VirEnv_38.prefab`
- `Assets/Prefabs/VIrtualEnvironments/VirEnv_39.prefab`
- `Assets/Terrain Data/Terrain_Data_VirEnv38.asset`
- `Assets/Terrain Data/Terrain_Data_VirEnv39.asset`

Each 3D prefab contains one `Terrain` with a `TerrainCollider`. Each also serializes a `Bridges` hierarchy with five active `Bridge(Clone)` objects. Each bridge has a `MeshFilter`, `MeshRenderer`, and non-trigger `MeshCollider`. No `NavMeshSurface`, `NavMeshData`, `NavMeshAgent`, or `NavMeshObstacle` serialization was found in the two target prefabs or `Map2D.cs`.

## 6. 2D-to-3D Coordinate Relationship

`Assets/Tools/VirtualEnvironmentCreation/Scripts/Map2D.cs`, class `Map2D`, establishes the mapping. `Run()` (lines 122–217) obtains `gameObject.GetComponent<Renderer>().bounds`. `UpdateTerrainTexture()` (lines 335–393) rasterizes each road Shape into the terrain alphamap. `CreateBridges()` (lines 550–603) uses the same normalized bounds fractions to map source X/Y to terrain X/Z.

For a source point `(x, y)`:

```text
X_prefab_local = terrain_local_x + ((x - bounds_min_x) / bounds_size_x) * terrain_size_x
Z_prefab_local = terrain_local_z + ((y - bounds_min_y) / bounds_size_y) * terrain_size_z
```

The generated terrain dimensions in `Map2D` are `440.4167 × 531.4167` in X/Z, and the serialized terrain transform in both prefabs is `(-276.364, -97.85, -283.2021)` relative to the prefab root. The source bounds derived from the serialized rotated Plane are recorded per environment in the Phase 9 JSON. This establishes a prefab-local horizontal XZ locator for every event.

No exact Y is reported. Terrain height data, bridge-deck occupancy, and the later scene-instance transform are separate from the source XY mapping. Inventing a vertical coordinate would overstate the evidence.

## 7. Evidence Hierarchy

The classification hierarchy was:

1. explicit 3D road-centerline/elevation data;
2. 3D road mesh/collider continuity;
3. canonical prefab or scene hierarchy proving a common navigable surface;
4. source proof that relevant crossings share one road plane and cannot be grade-separated;
5. manual Unity visual and movement inspection.

Available evidence establishes the canonical 2D curves, horizontal affine mapping, terrain, TerrainCollider, and explicit collider-backed bridges. It does not provide an explicit 3D road-centerline dataset, road-specific meshes/colliders, a road connectivity graph, or a serialized association between Phase 8 segment IDs and 3D bridge/road objects.

## 8. Navigability Classification Policy

`connected_same_level` requires positive evidence that both trajectories meet on one traversable surface. `grade_separated_not_connected` requires positive evidence of vertical or physical non-connection. All other cases remain `manual_review_required`.

The terrain texture cannot by itself prove a semantic junction. In addition, `Map2D.GetLines()` (lines 529–548) uses only each segment's `p0` and `p2` to test bridge creation, omitting the quadratic `p1`. Consequently, the bridge-generation geometry is not a lossless association to the Phase 8 curve and cannot safely decide an individual event from static coordinates alone.

## 9. Env38 Interior Crossings

All 28 Env38 interior crossings were mapped horizontally and retained as distinct review locations `E38-C001` through `E38-C028`. None received a final connectivity decision from static evidence; all 28 are `manual_review_required`.

## 10. Env38 Cross-Shape Crossings

Env38 contains 23 cross-Shape interior crossings. Their decision counts are: 0 connected, 0 grade-separated, and 23 manual. Shape membership was preserved as provenance and was not treated as connectivity evidence.

## 11. Env39 Interior Crossings

All 20 grid crossings were evaluated under the same evidence policy and retained as `E39-C001` through `E39-C020`. Their regular appearance did not determine topology. Counts are: 0 connected, 0 grade-separated, and 20 manual.

## 12. Zero-Chord Artifact Review

None of the 48 Phase 9 events has `source_anomaly_involved=true`. The 11 Phase 8 anomaly-involved pairwise events are endpoint events outside this review inventory. No source segment was deleted or modified.

## 13. Connected Same-Level Events

No event is currently classified `connected_same_level`. This count is zero because the required positive evidence is absent, not because the crossings were proven disconnected.

## 14. Grade-Separated Events

No event is currently classified `grade_separated_not_connected`. Both target prefabs contain explicit bridges, proving that grade-separated structures are supported and present, but the serialized static evidence does not associate a particular Phase 8 event with both relevant 3D trajectories strongly enough for a final decision.

## 15. Manual Review Required

All 48 events require manual review. Exact per-location instructions, source coordinates, source segments, Shapes, mapped horizontal locators, and decision observations are in [the Phase 9 manual Unity review](phase9-manual-unity-review.md).

## 16. Numbered QA Figures

The review figures are:

- `outputs/qa/env38-phase9-navigability-review.png`
- `outputs/qa/env39-phase9-navigability-review.png`

They use the Phase 7 detailed geometry without rotation, projection, translation, normalization, CRS assignment, or metre conversion. Each distinct Phase 8 coordinate has one unique review label. The nearest two Env38 review coordinates are about `0.30145` Unity world units apart—far beyond the Phase 8 numerical residual threshold—so no locations were grouped.

## 17. Limitations

This is read-only static inspection of the Unity repository. It does not validate runtime player movement, camera-visible continuity, collider contacts at a location, bridge deck membership for a source segment, or a scene-specific transform. The Unity working tree was already dirty before inspection; exact status and HEAD provenance are frozen in the machine-readable QA file.

Physical metre scale remains unverified and no CRS has been assigned.

## 18. Phase-9 Acceptance Checklist

- [x] Raw hashes reverified.
- [x] All 48 Phase 8 interior events preserved and reviewed.
- [x] Env38/Env39 horizontal mapping documented from source.
- [x] Unity bridge and collider support audited.
- [x] Numbered review table, JSON, figures, and manual checklist created.
- [x] No endpoint snapping occurred.
- [x] No final topology was constructed.
- [x] No road line was split.
- [x] No graph node was created.
- [x] No NetworkX or OSMnx graph exists.
- [x] No final morphology metric was calculated.
- [ ] `manual_review_required = 0`.

Acceptance status: **BLOCKED PENDING MANUAL 3D REVIEW**.

## 19. Deferred Phase-10 Work

Phase 10 must not begin until every manual item has an evidence-backed `connected_same_level` or `grade_separated_not_connected` decision. Endpoint snapping, near-miss analysis, road splitting, topology, graph-node construction, NetworkX/OSMnx graph creation, graph analysis, and scientific morphology metrics remain deferred.
