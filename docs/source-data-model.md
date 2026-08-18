# Phase 1: Unity Source-Data Model and Provenance

Verification date: 2026-08-18. This document records a read-only inspection of the Unity source checkout. It does not implement an exporter, reconstruct geometry, or calculate morphology metrics.

## 1. Source Repository Provenance

- Unity repository checkout: `F:\GitHub\geogami-virtual-environment-dev`
- Unity project root: `F:\GitHub\geogami-virtual-environment-dev\GeoGami-Vir-Env`
- Git branch: `analysis/osmnx-env38-env39`
- HEAD commit: `b4f10aede3cf7b825e9cf9ee25bbc42c0fa0a55e`
- Working tree: **dirty** at inspection time.

The working tree contained pre-existing deleted, modified, and untracked files. No attempt was made to clean, restore, or otherwise modify them. The source files and two 2D authoring prefabs used for the road-model verification were individually clean relative to HEAD:

- `GeoGami-Vir-Env/Assets/Tools/Shapes2D/Scripts/Shape.cs`
- `GeoGami-Vir-Env/Assets/Tools/Shapes2D/Shaders/Path.cginc`
- `GeoGami-Vir-Env/Assets/Tools/VirtualEnvironmentCreation/Scripts/Map2D.cs`
- `GeoGami-Vir-Env/Assets/Tools/VirtualEnvironmentCreation/2DMapPrefabs/2D Map Vir 38.prefab`
- `GeoGami-Vir-Env/Assets/Tools/VirtualEnvironmentCreation/2DMapPrefabs/2D Map Vir 39.prefab`

The dirty paths reported by `git status --short` were:

```text
 D GeoGami-Vir-Env/Assets/AddressableAssetsData/link.xml
 D GeoGami-Vir-Env/Assets/AddressableAssetsData/link.xml.meta
 D GeoGami-Vir-Env/Assets/Prefabs/Animals/Animals_FREE/Render_Pipeline_Convert/Unity_2021_Built-In_source.unitypackage.meta
 D GeoGami-Vir-Env/Assets/Prefabs/Animals/Animals_FREE/Render_Pipeline_Convert/Unity_2021_HDRP_source.unitypackage.meta
 D GeoGami-Vir-Env/Assets/Prefabs/Animals/Animals_FREE/Render_Pipeline_Convert/Unity_2021_URP_source.unitypackage.meta
 M GeoGami-Vir-Env/Assets/Scripts/InputMaster.cs
 M GeoGami-Vir-Env/Assets/Settings/ForwardRenderer.asset
 M GeoGami-Vir-Env/Packages/manifest.json
 M GeoGami-Vir-Env/ProjectSettings/Packages/com.unity.probuilder/Settings.json
 M GeoGami-Vir-Env/ProjectSettings/ProjectVersion.txt
 M GeoGami-Vir-Env/ProjectSettings/ShaderGraphSettings.asset
 M GeoGami-Vir-Env/UserSettings/EditorUserSettings.asset
 M GeoGami-Vir-Env/UserSettings/Layouts/default-2022.dwlt
?? GeoGami-Vir-Env/Assets/Editor/BuildInfoGenerator.cs.meta
?? GeoGami-Vir-Env/Assets/Scripts/Generated.meta
?? GeoGami-Vir-Env/Assets/Scripts/Generated/BuildInfo.cs.meta
?? GeoGami-Vir-Env/Assets/Terrain Data/TerrainLayers/TerrainLayer_0_for_env_0.asset
?? GeoGami-Vir-Env/Assets/Terrain Data/TerrainLayers/TerrainLayer_0_for_env_0.asset.meta
?? GeoGami-Vir-Env/Assets/Terrain Data/TerrainLayers/TerrainLayer_1_for_env_0.asset
?? GeoGami-Vir-Env/Assets/Terrain Data/TerrainLayers/TerrainLayer_1_for_env_0.asset.meta
?? GeoGami-Vir-Env/Assets/Terrain Data/TerrainLayers/TerrainLayer_2_for_env_0.asset
?? GeoGami-Vir-Env/Assets/Terrain Data/TerrainLayers/TerrainLayer_2_for_env_0.asset.meta
?? GeoGami-Vir-Env/Assets/Terrain Data/Terrain_Data_VirEnv0.asset
?? GeoGami-Vir-Env/Assets/Terrain Data/Terrain_Data_VirEnv0.asset.meta
```

Because the checkout is dirty, the commit SHA alone does not describe every file in the working directory. For the verified geometry sources and prefabs, however, a path-scoped status check returned no changes, so those files match the recorded HEAD commit.

## 2. Unity Project Version

The authoritative project settings file is:

`GeoGami-Vir-Env/ProjectSettings/ProjectVersion.txt`

The inspected working-tree file declares:

```text
m_EditorVersion: 2022.3.62f3
m_EditorVersionWithRevision: 2022.3.62f3 (96770f904ca7)
```

This file is modified relative to HEAD. At commit `b4f10aede3cf7b825e9cf9ee25bbc42c0fa0a55e`, it instead declares Unity `2022.3.58f1` with revision `ed7f6eacb62e`. Phase 1 therefore records `2022.3.62f3 (96770f904ca7)` as the version in the inspected working tree while retaining the HEAD version distinction for reproducibility.

## 3. Authoritative Road Component

The road component is `Shapes2D.Shape`, declared at:

`GeoGami-Vir-Env/Assets/Tools/Shapes2D/Scripts/Shape.cs:98`

Its Unity asset GUID is `409a53c2fc720400bb482962c5563548`, from `Shape.cs.meta`. The authoritative environment prefabs reference this GUID on their `Line Path` GameObjects.

The source and serialization chain is:

`Shapes2D.Shape` → public `settings` field (`Shape.UserProps`) → public `pathSegments` property → private serialized `_pathSegments` field → `PathSegment[]`

Supporting declarations are in `Shape.cs`:

- `UserProps` is serializable at lines 207–210.
- `settings` is a public `UserProps` field at line 622.
- `_pathSegments` is a `[SerializeField] private PathSegment[]` at lines 404–407.
- `pathSegments` exposes that array at lines 415–425.

The prefab YAML confirms the serialized nesting as `settings:` followed by `_pathSegments:`. This is visible, for example, in `2D Map Vir 38.prefab:48-69` and `2D Map Vir 39.prefab:665-686`.

## 4. PathSegment Data Structure

`PathSegment` is declared in namespace `Shapes2D` at `Shape.cs:58-75` as a serializable value type:

```csharp
[System.SerializableAttribute]
public struct PathSegment {
    public Vector3 p0, p1, p2;
    // constructors omitted
}
```

All three stored fields—`p0`, `p1`, and `p2`—are `UnityEngine.Vector3`. Constructors accept `Vector2` for some arguments and rely on Unity conversions, but the serialized fields themselves are `Vector3`. Prefab YAML correspondingly stores each as `{x, y, z}`; all inspected road-path values have planar `z: 0` serialization.

## 5. Quadratic Bézier Geometry

The source explicitly states that a `PathSegment` describes a quadratic Bézier curve (`Shape.cs:58-63`) and that each path curve comprises three points (`Shape.cs:408-412`). The Shapes2D path shader also computes distance to a quadratic Bézier using `b0`, `b1`, and `b2` (`Assets/Tools/Shapes2D/Shaders/Path.cginc:59-71`).

The mathematical interpretation is therefore:

- `p0`: start endpoint;
- `p1`: quadratic Bézier control point; and
- `p2`: end endpoint.

For `0 ≤ t ≤ 1`, the curve is:

`B(t) = (1-t)^2 p0 + 2(1-t)t p1 + t^2 p2`.

The representation is not a simple polyline. Removing `p1` changes a curved segment into the straight chord from `p0` to `p2`.

## 6. Coordinate Representation

The serialized `_pathSegments` points are normalized coordinates in the Shape's own rectangular frame, not world coordinates. `Shape.cs:409-412` states that segment endpoints are clamped to the range `-0.5` to `0.5`; `PathSegment.Clamp()` implements this for the x/y coordinates of `p0` and `p2` at lines 77–82. The control point `p1` is not clamped by that method and can extend outside the nominal rectangle.

For non-UI Shapes, `GetWorldCorners()` constructs the normalized rectangle corners and calls `transform.TransformPoint(...)` (`Shape.cs:1650-1664`). Unity's Transform operation incorporates the Shape GameObject's position, rotation, and scale, including its parent hierarchy. For UI Shapes, the method instead uses the `RectTransform` world corners.

`BiLerp()` maps a normalized point into the computed world-corner frame (`Shape.cs:1300-1304`). Its return type is `Vector2`; therefore the world-segment API returns the transformed planar x/y values in `Vector3` fields through Unity's `Vector2`-to-`Vector3` conversion. No metres-per-world-unit conclusion follows from this coordinate conversion.

## 7. GetPathWorldSegments

`GetPathWorldSegments()` exists at:

`GeoGami-Vir-Env/Assets/Tools/Shapes2D/Scripts/Shape.cs:1369-1388`

The method:

1. obtains the Shape's world corners with `GetWorldCorners()`;
2. allocates a `PathSegment[]` matching `settings.pathSegments.Length`;
3. bilinearly maps every segment's `p0`, `p1`, and `p2` through those corners; and
4. returns the transformed segments.

This API should be preferred by the future exporter for world-space values because it applies Shapes2D's own coordinate semantics and handles both ordinary Transform and RectTransform cases. Manually reproducing only a GameObject's local transform could omit parent transforms, Shape normalization, or the component's special UI handling. The exporter should still preserve source identifiers and original serialized values for provenance, but it should not independently reinvent the world-coordinate conversion.

## 8. Environment 38 Source Inventory

Authoritative 2D authoring prefab:

`GeoGami-Vir-Env/Assets/Tools/VirtualEnvironmentCreation/2DMapPrefabs/2D Map Vir 38.prefab`

The prefab hierarchy contains a `Roads` GameObject and five child `Line Path` GameObjects with the Shapes2D component. Reading them in prefab serialization order gives:

| Road Shape | GameObject fileID | Shape component fileID | Serialized segments |
|---:|---:|---:|---:|
| 1 | `4330855546755831761` | `4330855546755831596` | 4 |
| 2 | `4330855547456548047` | `4330855547456548042` | 32 |
| 3 | `4330855547524397479` | `4330855547524397474` | 32 |
| 4 | `4330855547529842338` | `4330855547529842337` | 24 |
| 5 | `4330855547829185568` | `4330855547829185599` | 28 |
| **Total** |  |  | **120** |

The relevant `_pathSegments` arrays begin at prefab lines 69, 799, 1034, 1269, and 1631. The current repository therefore agrees with the expected `4 + 32 + 32 + 24 + 28 = 120` inventory.

Other Shapes2D components in the prefab belong to water or terrain-element polygons. They were excluded by following the Unity Transform hierarchy and selecting only Shape components whose GameObject is a child of `Roads`.

## 9. Environment 39 Source Inventory

Authoritative 2D authoring prefab:

`GeoGami-Vir-Env/Assets/Tools/VirtualEnvironmentCreation/2DMapPrefabs/2D Map Vir 39.prefab`

The prefab hierarchy contains one `Line Path` child under `Roads`:

| Road Shape | GameObject fileID | Shape component fileID | Serialized segments | Unique serialized `p0`/`p2` positions |
|---:|---:|---:|---:|---:|
| 1 | `3305298596651482019` | `3305298596651482022` | 32 | 33 |

Its `_pathSegments` array begins at prefab line 686. The unique-position count was obtained directly from the exact serialized `{x, y, z}` values across the 32 segments' `p0` and `p2` fields; it is not a derived topological node count. The current repository agrees with all three expectations: one road Shape, 32 Bézier segments, and 33 unique serialized endpoint positions.

## 10. Shapes2D Segment Limit

`Shape.MaxPathSegments` is still declared as `32` at `Shape.cs:141-144`. The source comments specify a range of one through `MaxPathSegments`, shader storage is allocated from that maximum, and the editor checks it when adding segments. The `pathSegments` setter also contains a range guard at `Shape.cs:415-423`; strictly as written, however, that guard tests the existing `_pathSegments.Length` before assigning `value`, rather than testing `value.Length`. Phase 1 therefore verifies the declared Shapes2D limit of 32 without claiming more about that setter than the implementation supports.

Consequently, Environment 38's five Shape objects versus Environment 39's one Shape object cannot be interpreted as a street-network morphology metric. Environment 38 requires multiple authoring objects in substantial part because its 120 segments cannot fit within a single 32-segment Shape. Shape-object count reflects a software/storage constraint, not directly the number of streets, intersections, or any measure of curvilinearity.

## 11. Connectivity Representation

Shapes2D stores an ordered array of geometric curve segments; it does not store an explicit street-network graph or authoritative intersection-node table. The source says that connected path segments are made by setting the points of connected segments equal (`Shape.cs:409-412`). Thus endpoint equality may encode geometric continuity within or across arrays, but it is not sufficient by itself to classify all navigable intersections.

The 33 unique serialized endpoint positions in Environment 39 must therefore remain an inventory fact, not be relabelled as 33 topological nodes. Endpoint-to-interior and interior-to-interior crossings require later geometric reconstruction, while grade separation and navigability require environment validation. Control points `p1` are never connectivity nodes merely because they are present.

## 12. Why Map2D.GetLines Is Rejected

`Map2D.GetLines(Shape shape)` is located at:

`GeoGami-Vir-Env/Assets/Tools/VirtualEnvironmentCreation/Scripts/Map2D.cs:529-548`

It calls `shape.GetPathWorldSegments()`, but for each returned segment creates a NetTopologySuite `LineString` from only:

```csharp
new Coordinate(lineSegment.p0.x, lineSegment.p0.y),
new Coordinate(lineSegment.p2.x, lineSegment.p2.y)
```

The method never reads `lineSegment.p1`. It therefore replaces every quadratic Bézier with its endpoint chord. This is unsuitable as the authoritative extractor for a curvy-versus-grid comparison because it systematically discards the control information that determines curvature and local direction along each segment. It may remain fit for its existing generation-related use, but its LineStrings cannot serve as the scientific source geometry.

## 13. Relationship Between 2D Source and 3D Environment

`Map2D.Run()` iterates the child whose name contains `Road`, retrieves each child's `Shape`, and calls both `GetLines(shape)` and `UpdateTerrainTexture(shape, ...)` (`Map2D.cs:122-153`). `UpdateTerrainTexture()` obtains a rendered `Texture2D` for the Shape and writes non-white pixels into the Unity Terrain alphamap (`Map2D.cs:335-393`). `GetTexture2D()` renders Shapes through an orthographic camera and render texture before reading the result into a `Texture2D` (`Map2D.cs:1040-1109`).

This code establishes that the 2D Shapes2D road paths are upstream inputs to the generated/rasterized terrain road appearance. The terrain appearance is a downstream pixel representation and cannot recover the original Bézier control points exactly. The 2D Bézier paths are therefore the primary quantitative geometry source; the participant-navigable 3D environment remains important for later validation of actual connections, crossings, and topology. Phase 1 does not extract 3D terrain geometry.

## 14. Implications for the Future Exporter

The future exporter should:

- operate on the authoritative `2D Map Vir 38` and `2D Map Vir 39` prefabs;
- select `Shapes2D.Shape` components under each prefab's `Roads` hierarchy;
- preserve environment, GameObject, Shape-component, Shape-order, and segment-order identifiers;
- preserve original serialized/local `p0`, `p1`, and `p2` values as immutable provenance;
- use `GetPathWorldSegments()` for Shapes2D-consistent transformed planar coordinates;
- export all three points rather than the `p0`/`p2` chord;
- enforce the Phase-0 raw-count gate of 120 segments for Environment 38 and 32 for Environment 39; and
- record the Unity repository branch, commit, dirty-state status, project version, and exporter version with the export.

The exporter must not use screenshots, terrain textures, manually traced roads, or `Map2D.GetLines()` as the authoritative geometry. No exporter is implemented in Phase 1.

## 15. Phase-1 Verification Checklist

- [x] Recorded Unity checkout path, project root, branch, HEAD SHA, and dirty state.
- [x] Read the working-tree Unity version from authoritative project settings and recorded its difference from HEAD.
- [x] Verified the exact `Shapes2D.Shape` source path and Unity asset GUID.
- [x] Verified `Shape → settings → pathSegments → _pathSegments → PathSegment[]`.
- [x] Verified `p0`, `p1`, and `p2` are serialized `Vector3` fields.
- [x] Verified the segments are quadratic Bézier curves.
- [x] Verified normalized serialization and Transform/RectTransform world conversion.
- [x] Verified `GetPathWorldSegments()` exists and transforms all three points.
- [x] Verified Environment 38 has five road Shapes with `4, 32, 32, 24, 28` segments, total 120.
- [x] Verified Environment 39 has one road Shape with 32 segments and 33 unique serialized endpoint positions.
- [x] Verified `MaxPathSegments = 32`.
- [x] Verified `Map2D.GetLines()` uses `p0` and `p2` but omits `p1`.
- [x] Verified the 2D Shapes are upstream of the rasterized 3D terrain road appearance.
- [x] Confirmed the Unity repository was inspected read-only.
- [x] Confirmed no exporter, Python analysis, graph construction, or metric calculation was implemented.

## 16. Remaining Unresolved Questions

Phase 1 does not establish:

1. metres per Unity world unit;
2. the final common north/reference direction;
3. the Bézier discretization or adaptive-sampling tolerance;
4. the topology snapping tolerance;
5. whether either network contains grade-separated road-road crossings; or
6. the final OSMnx bearing/orientation-entropy implementation strategy.

These questions remain for later phases and must not be inferred from the source inventory above.
