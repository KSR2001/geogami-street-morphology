# Phase 9 3D Navigability Validation

## 1. Phase 9 Scope

Phase 9 adds 3D navigability evidence to the 48 Phase 8 `interior_interior_crossing` events. It preserves every Phase 8 event ID, source coordinate, segment and Shape identity, parameter pair, residual, same-Shape flag, and anomaly flag. It does not revise the Phase 8 mathematics.

The result is **PHASE 9 COMPLETE**. Direct researcher inspection of all 48 locations in the 3D Unity environments confirmed every event as `connected_same_level`. No event remains `manual_review_required`. Phase 10 remains outside this phase and was not started.

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

Available static evidence establishes the canonical 2D curves, horizontal affine mapping, terrain, TerrainCollider, and explicit collider-backed bridges. It does not provide an explicit 3D road-centerline dataset, road-specific meshes/colliders, a road connectivity graph, or a serialized association between Phase 8 segment IDs and 3D bridge/road objects. Static classification therefore remained blocked until the researcher directly inspected all review locations in Unity.

## 8. Navigability Classification Policy

`connected_same_level` requires positive evidence that both trajectories meet on one traversable surface. `grade_separated_not_connected` requires positive evidence of vertical or physical non-connection. All other cases remain `manual_review_required`.

The terrain texture cannot by itself prove a semantic junction. In addition, `Map2D.GetLines()` (lines 529–548) uses only each segment's `p0` and `p2` to test bridge creation, omitting the quadratic `p1`. Consequently, the bridge-generation geometry is not a lossless association to the Phase 8 curve and cannot safely decide an individual event from static coordinates alone.

## 9. Env38 Interior Crossings

All 28 Env38 interior crossings were mapped horizontally and retained as distinct review locations `E38-C001` through `E38-C028`. Direct researcher inspection confirmed all 28 as `connected_same_level`; none is grade-separated and none remains unresolved.

## 10. Env38 Cross-Shape Crossings

Env38 contains 23 cross-Shape interior crossings. Their verified decision counts are: 23 connected, 0 grade-separated, and 0 manual. Shape membership was preserved as provenance and was not itself treated as connectivity evidence; the decisions come from direct Unity inspection.

## 11. Env39 Interior Crossings

All 20 grid crossings were evaluated under the same evidence policy and retained as `E39-C001` through `E39-C020`. Their regular appearance did not determine topology. Direct researcher inspection confirmed all 20 as connected, with 0 grade-separated and 0 manual.

## 12. Zero-Chord Artifact Review

None of the 48 Phase 9 events has `source_anomaly_involved=true`. The 11 Phase 8 anomaly-involved pairwise events are endpoint events outside this review inventory. No source segment was deleted or modified.

## 13. Connected Same-Level Events

All 48 events are classified `connected_same_level`. The evidence type is `manual_unity_3d_visual_inspection`: the researcher inspected the corresponding crossings in the actual Env38 and Env39 3D environments and confirmed that both road trajectories meet on the same navigable surface.

## 14. Grade-Separated Events

No event is classified `grade_separated_not_connected`. Static inspection found five collider-backed bridges in each environment but could not reliably associate those bridges with the Phase 8 road-crossing events. Subsequent direct manual inspection confirmed that none of the 48 reviewed road-road crossings has one road passing above or below the other. Bridges still exist; they simply do not invalidate any reviewed junction.

## 15. Manual Review Required

No event remains `manual_review_required`. The original per-location instructions, source coordinates, source segments, Shapes, mapped horizontal locators, and completed decisions remain in [the Phase 9 manual Unity review](phase9-manual-unity-review.md) as an audit trail.

### Manual Unity 3D Review Results

The researcher directly inspected 48 unique crossing locations: 28 in Env38 and 20 in Env39. All 48 were confirmed `connected_same_level`; zero were grade-separated and zero remain unresolved. This includes all 23 Env38 cross-Shape interior crossings. No zero-chord source anomaly participates in the review inventory.

The manual review also established that the collider-backed bridges identified during static inspection do not create road-over-road or road-under-road separation at any reviewed crossing. Phase 8 event IDs and exact mathematical X/Y coordinates were not modified. The classification records future topology eligibility only; it does not itself split a road or create topology.

## 16. Numbered QA Figures

The review figures are:

- `outputs/qa/env38-phase9-navigability-review.png`
- `outputs/qa/env39-phase9-navigability-review.png`

They use the Phase 7 detailed geometry without rotation, projection, translation, normalization, CRS assignment, or metre conversion. Each distinct Phase 8 coordinate has one unique review label. The nearest two Env38 review coordinates are about `0.30145` Unity world units apart—far beyond the Phase 8 numerical residual threshold—so no locations were grouped.

## 17. Limitations

The repository audit was read-only, and the final decisions incorporate the researcher's direct visual inspection of the actual Unity environments. No vertical measurements were made, no vertical coordinates were invented, and no scene-specific transform was added to the dataset. The Unity working tree was already dirty before static inspection; exact status and HEAD provenance are frozen in the machine-readable QA file.

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
- [x] Direct researcher Unity inspection completed for all 48 locations.
- [x] `connected_same_level = 48`.
- [x] `grade_separated_not_connected = 0`.
- [x] `manual_review_required = 0`.

Acceptance status: **PHASE 9 COMPLETE**.

## 19. Deferred Phase-10 Work

All Phase 9 manual items now have evidence-backed decisions, but Phase 10 was not begun as part of this finalization. Endpoint snapping, near-miss analysis, road splitting, topology, graph-node construction, NetworkX/OSMnx graph creation, graph analysis, and scientific morphology metrics remain deferred to separately authorized future work.
