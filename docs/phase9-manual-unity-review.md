# Phase 9 Manual Unity Review

Phase 9 is **COMPLETE**. Static repository evidence initially could not establish a final navigability decision for the 48 locations, so the checklist below was used for direct researcher inspection in Unity. All 48 reviews are now resolved. This document remains the audit trail; it must not be used to edit Unity assets or construct topology.

## Review procedure

1. Open the matching canonical `2D Map Vir 38` or `2D Map Vir 39` prefab and the corresponding `VirEnv_38` or `VirEnv_39` prefab without saving changes.
2. Use the Phase 9 figure and source XY coordinate to identify both trajectories. The recorded prefab-local XZ value may be used as a horizontal locator; its Y is intentionally unavailable.
3. Inspect the location from side, top, and perspective views. Check Terrain, TerrainCollider, bridge MeshCollider objects, visible continuity, and actual participant movement across each approach where safe to do so.
4. Record `connected_same_level` only if both trajectories meet on one traversable surface. Record `grade_separated_not_connected` only if one passes above/below the other or a physical barrier/gap prevents the junction. Otherwise retain `manual_review_required` and describe the missing evidence.
5. Do not move objects, rebake navigation, save prefabs/scenes, snap coordinates, split roads, or create graph nodes during review.

## Completed review result

The researcher manually inspected all 48 locations in the 3D Unity environments. All 48 were confirmed `connected_same_level`; none was road-over-road or road-under-road grade-separated. The five collider-backed bridges found in each environment during static inspection do not invalidate any reviewed road-road junction.

## Reviewed locations

### E38-C001

- Environment: Env38
- Source XY: `(262.281728747816, 113.515507045923)`
- Mapped 3D locator: `VirEnv_38 prefab-local XZ (-13.946407045, -3.967641302); Y unavailable`
- Segments: `env38_shape_4330855546755831596_segment_0001` and `env38_shape_4330855547524397474_segment_0006`
- Shapes: `env38_shape_4330855546755831596` and `env38_shape_4330855547524397474`
- Same Shape: `false`
- Source anomaly involved: `false`
- Check in 3D: follow both road trajectories through the labelled coordinate; inspect vertical separation, bridge/deck membership, TerrainCollider continuity, barriers, and whether movement can transfer between the two roads.
- `connected_same_level` observation: both approaches visibly meet at one elevation and a participant can traverse from either trajectory onto the other.
- `grade_separated_not_connected` observation: one trajectory passes above or below the other, or a physical separation prevents transfer at the crossing.
- Review status: `completed`
- Decision: `connected_same_level`
- Evidence: `manual Unity 3D visual inspection`
- Evidence summary: Researcher manually inspected the corresponding crossing in the 3D Unity environment and confirmed both road trajectories meet on the same navigable surface with no road-over-road or road-under-road grade separation.

### E38-C002

- Environment: Env38
- Source XY: `(213.263398577937, 122.856242792482)`
- Mapped 3D locator: `VirEnv_38 prefab-local XZ (-63.011134154, 5.380421378); Y unavailable`
- Segments: `env38_shape_4330855546755831596_segment_0001` and `env38_shape_4330855547529842337_segment_0007`
- Shapes: `env38_shape_4330855546755831596` and `env38_shape_4330855547529842337`
- Same Shape: `false`
- Source anomaly involved: `false`
- Check in 3D: follow both road trajectories through the labelled coordinate; inspect vertical separation, bridge/deck membership, TerrainCollider continuity, barriers, and whether movement can transfer between the two roads.
- `connected_same_level` observation: both approaches visibly meet at one elevation and a participant can traverse from either trajectory onto the other.
- `grade_separated_not_connected` observation: one trajectory passes above or below the other, or a physical separation prevents transfer at the crossing.
- Review status: `completed`
- Decision: `connected_same_level`
- Evidence: `manual Unity 3D visual inspection`
- Evidence summary: Researcher manually inspected the corresponding crossing in the 3D Unity environment and confirmed both road trajectories meet on the same navigable surface with no road-over-road or road-under-road grade separation.

### E38-C003

- Environment: Env38
- Source XY: `(160.787711367493, 171.921630640138)`
- Mapped 3D locator: `VirEnv_38 prefab-local XZ (-115.536490769, 54.484296436); Y unavailable`
- Segments: `env38_shape_4330855546755831596_segment_0001` and `env38_shape_4330855547529842337_segment_0024`
- Shapes: `env38_shape_4330855546755831596` and `env38_shape_4330855547529842337`
- Same Shape: `false`
- Source anomaly involved: `false`
- Check in 3D: follow both road trajectories through the labelled coordinate; inspect vertical separation, bridge/deck membership, TerrainCollider continuity, barriers, and whether movement can transfer between the two roads.
- `connected_same_level` observation: both approaches visibly meet at one elevation and a participant can traverse from either trajectory onto the other.
- `grade_separated_not_connected` observation: one trajectory passes above or below the other, or a physical separation prevents transfer at the crossing.
- Review status: `completed`
- Decision: `connected_same_level`
- Evidence: `manual Unity 3D visual inspection`
- Evidence summary: Researcher manually inspected the corresponding crossing in the 3D Unity environment and confirmed both road trajectories meet on the same navigable surface with no road-over-road or road-under-road grade separation.

### E38-C004

- Environment: Env38
- Source XY: `(154.783925629774, 232.212356643854)`
- Mapped 3D locator: `VirEnv_38 prefab-local XZ (-121.545959224, 114.822314878); Y unavailable`
- Segments: `env38_shape_4330855546755831596_segment_0002` and `env38_shape_4330855547456548042_segment_0024`
- Shapes: `env38_shape_4330855546755831596` and `env38_shape_4330855547456548042`
- Same Shape: `false`
- Source anomaly involved: `false`
- Check in 3D: follow both road trajectories through the labelled coordinate; inspect vertical separation, bridge/deck membership, TerrainCollider continuity, barriers, and whether movement can transfer between the two roads.
- `connected_same_level` observation: both approaches visibly meet at one elevation and a participant can traverse from either trajectory onto the other.
- `grade_separated_not_connected` observation: one trajectory passes above or below the other, or a physical separation prevents transfer at the crossing.
- Review status: `completed`
- Decision: `connected_same_level`
- Evidence: `manual Unity 3D visual inspection`
- Evidence summary: Researcher manually inspected the corresponding crossing in the 3D Unity environment and confirmed both road trajectories meet on the same navigable surface with no road-over-road or road-under-road grade separation.

### E38-C005

- Environment: Env38
- Source XY: `(168.969198072388, 265.554461860193)`
- Mapped 3D locator: `VirEnv_38 prefab-local XZ (-107.347260105, 148.190573858); Y unavailable`
- Segments: `env38_shape_4330855546755831596_segment_0002` and `env38_shape_4330855547456548042_segment_0029`
- Shapes: `env38_shape_4330855546755831596` and `env38_shape_4330855547456548042`
- Same Shape: `false`
- Source anomaly involved: `false`
- Check in 3D: follow both road trajectories through the labelled coordinate; inspect vertical separation, bridge/deck membership, TerrainCollider continuity, barriers, and whether movement can transfer between the two roads.
- `connected_same_level` observation: both approaches visibly meet at one elevation and a participant can traverse from either trajectory onto the other.
- `grade_separated_not_connected` observation: one trajectory passes above or below the other, or a physical separation prevents transfer at the crossing.
- Review status: `completed`
- Decision: `connected_same_level`
- Evidence: `manual Unity 3D visual inspection`
- Evidence summary: Researcher manually inspected the corresponding crossing in the 3D Unity environment and confirmed both road trajectories meet on the same navigable surface with no road-over-road or road-under-road grade separation.

### E38-C006

- Environment: Env38
- Source XY: `(248.302464479447, 309.184296405748)`
- Mapped 3D locator: `VirEnv_38 prefab-local XZ (-27.938902998, 191.854631930); Y unavailable`
- Segments: `env38_shape_4330855546755831596_segment_0002` and `env38_shape_4330855547524397474_segment_0009`
- Shapes: `env38_shape_4330855546755831596` and `env38_shape_4330855547524397474`
- Same Shape: `false`
- Source anomaly involved: `false`
- Check in 3D: follow both road trajectories through the labelled coordinate; inspect vertical separation, bridge/deck membership, TerrainCollider continuity, barriers, and whether movement can transfer between the two roads.
- `connected_same_level` observation: both approaches visibly meet at one elevation and a participant can traverse from either trajectory onto the other.
- `grade_separated_not_connected` observation: one trajectory passes above or below the other, or a physical separation prevents transfer at the crossing.
- Review status: `completed`
- Decision: `connected_same_level`
- Evidence: `manual Unity 3D visual inspection`
- Evidence summary: Researcher manually inspected the corresponding crossing in the 3D Unity environment and confirmed both road trajectories meet on the same navigable surface with no road-over-road or road-under-road grade separation.

### E38-C007

- Environment: Env38
- Source XY: `(329.380500436057, 285.511978270034)`
- Mapped 3D locator: `VirEnv_38 prefab-local XZ (53.215875122, 168.163745074); Y unavailable`
- Segments: `env38_shape_4330855546755831596_segment_0003` and `env38_shape_4330855547456548042_segment_0012`
- Shapes: `env38_shape_4330855546755831596` and `env38_shape_4330855547456548042`
- Same Shape: `false`
- Source anomaly involved: `false`
- Check in 3D: follow both road trajectories through the labelled coordinate; inspect vertical separation, bridge/deck membership, TerrainCollider continuity, barriers, and whether movement can transfer between the two roads.
- `connected_same_level` observation: both approaches visibly meet at one elevation and a participant can traverse from either trajectory onto the other.
- `grade_separated_not_connected` observation: one trajectory passes above or below the other, or a physical separation prevents transfer at the crossing.
- Review status: `completed`
- Decision: `connected_same_level`
- Evidence: `manual Unity 3D visual inspection`
- Evidence summary: Researcher manually inspected the corresponding crossing in the 3D Unity environment and confirmed both road trajectories meet on the same navigable surface with no road-over-road or road-under-road grade separation.

### E38-C008

- Environment: Env38
- Source XY: `(355.000516175866, 253.097946)`
- Mapped 3D locator: `VirEnv_38 prefab-local XZ (78.860140777, 135.724287026); Y unavailable`
- Segments: `env38_shape_4330855546755831596_segment_0003` and `env38_shape_4330855547456548042_segment_0019`
- Shapes: `env38_shape_4330855546755831596` and `env38_shape_4330855547456548042`
- Same Shape: `false`
- Source anomaly involved: `false`
- Check in 3D: follow both road trajectories through the labelled coordinate; inspect vertical separation, bridge/deck membership, TerrainCollider continuity, barriers, and whether movement can transfer between the two roads.
- `connected_same_level` observation: both approaches visibly meet at one elevation and a participant can traverse from either trajectory onto the other.
- `grade_separated_not_connected` observation: one trajectory passes above or below the other, or a physical separation prevents transfer at the crossing.
- Review status: `completed`
- Decision: `connected_same_level`
- Evidence: `manual Unity 3D visual inspection`
- Evidence summary: Researcher manually inspected the corresponding crossing in the 3D Unity environment and confirmed both road trajectories meet on the same navigable surface with no road-over-road or road-under-road grade separation.

### E38-C009

- Environment: Env38
- Source XY: `(338.479044421742, 146.692200440169)`
- Mapped 3D locator: `VirEnv_38 prefab-local XZ (62.323031082, 29.235076106); Y unavailable`
- Segments: `env38_shape_4330855546755831596_segment_0004` and `env38_shape_4330855547456548042_segment_0007`
- Shapes: `env38_shape_4330855546755831596` and `env38_shape_4330855547456548042`
- Same Shape: `false`
- Source anomaly involved: `false`
- Check in 3D: follow both road trajectories through the labelled coordinate; inspect vertical separation, bridge/deck membership, TerrainCollider continuity, barriers, and whether movement can transfer between the two roads.
- `connected_same_level` observation: both approaches visibly meet at one elevation and a participant can traverse from either trajectory onto the other.
- `grade_separated_not_connected` observation: one trajectory passes above or below the other, or a physical separation prevents transfer at the crossing.
- Review status: `completed`
- Decision: `connected_same_level`
- Evidence: `manual Unity 3D visual inspection`
- Evidence summary: Researcher manually inspected the corresponding crossing in the 3D Unity environment and confirmed both road trajectories meet on the same navigable surface with no road-over-road or road-under-road grade separation.

### E38-C010

- Environment: Env38
- Source XY: `(337.369355924969, 145.527924451464)`
- Mapped 3D locator: `VirEnv_38 prefab-local XZ (61.212292241, 28.069886852); Y unavailable`
- Segments: `env38_shape_4330855546755831596_segment_0004` and `env38_shape_4330855547524397474_segment_0016`
- Shapes: `env38_shape_4330855546755831596` and `env38_shape_4330855547524397474`
- Same Shape: `false`
- Source anomaly involved: `false`
- Check in 3D: follow both road trajectories through the labelled coordinate; inspect vertical separation, bridge/deck membership, TerrainCollider continuity, barriers, and whether movement can transfer between the two roads.
- `connected_same_level` observation: both approaches visibly meet at one elevation and a participant can traverse from either trajectory onto the other.
- `grade_separated_not_connected` observation: one trajectory passes above or below the other, or a physical separation prevents transfer at the crossing.
- Review status: `completed`
- Decision: `connected_same_level`
- Evidence: `manual Unity 3D visual inspection`
- Evidence summary: Researcher manually inspected the corresponding crossing in the 3D Unity environment and confirmed both road trajectories meet on the same navigable surface with no road-over-road or road-under-road grade separation.

### E38-C011

- Environment: Env38
- Source XY: `(358.343447340357, 178.833617153432)`
- Mapped 3D locator: `VirEnv_38 prefab-local XZ (82.206236100, 61.401704756); Y unavailable`
- Segments: `env38_shape_4330855546755831596_segment_0004` and `env38_shape_4330855547529842337_segment_0022`
- Shapes: `env38_shape_4330855546755831596` and `env38_shape_4330855547529842337`
- Same Shape: `false`
- Source anomaly involved: `false`
- Check in 3D: follow both road trajectories through the labelled coordinate; inspect vertical separation, bridge/deck membership, TerrainCollider continuity, barriers, and whether movement can transfer between the two roads.
- `connected_same_level` observation: both approaches visibly meet at one elevation and a participant can traverse from either trajectory onto the other.
- `grade_separated_not_connected` observation: one trajectory passes above or below the other, or a physical separation prevents transfer at the crossing.
- Review status: `completed`
- Decision: `connected_same_level`
- Evidence: `manual Unity 3D visual inspection`
- Evidence summary: Researcher manually inspected the corresponding crossing in the 3D Unity environment and confirmed both road trajectories meet on the same navigable surface with no road-over-road or road-under-road grade separation.

### E38-C012

- Environment: Env38
- Source XY: `(401.646470776022, -60.7965747550928)`
- Mapped 3D locator: `VirEnv_38 prefab-local XZ (125.550246810, -178.416454636); Y unavailable`
- Segments: `env38_shape_4330855547456548042_segment_0003` and `env38_shape_4330855547524397474_segment_0004`
- Shapes: `env38_shape_4330855547456548042` and `env38_shape_4330855547524397474`
- Same Shape: `false`
- Source anomaly involved: `false`
- Check in 3D: follow both road trajectories through the labelled coordinate; inspect vertical separation, bridge/deck membership, TerrainCollider continuity, barriers, and whether movement can transfer between the two roads.
- `connected_same_level` observation: both approaches visibly meet at one elevation and a participant can traverse from either trajectory onto the other.
- `grade_separated_not_connected` observation: one trajectory passes above or below the other, or a physical separation prevents transfer at the crossing.
- Review status: `completed`
- Decision: `connected_same_level`
- Evidence: `manual Unity 3D visual inspection`
- Evidence summary: Researcher manually inspected the corresponding crossing in the 3D Unity environment and confirmed both road trajectories meet on the same navigable surface with no road-over-road or road-under-road grade separation.

### E38-C013

- Environment: Env38
- Source XY: `(401.570905348889, -101.769142270889)`
- Mapped 3D locator: `VirEnv_38 prefab-local XZ (125.474609858, -219.421161300); Y unavailable`
- Segments: `env38_shape_4330855547456548042_segment_0003` and `env38_shape_4330855547829185599_segment_0002`
- Shapes: `env38_shape_4330855547456548042` and `env38_shape_4330855547829185599`
- Same Shape: `false`
- Source anomaly involved: `false`
- Check in 3D: follow both road trajectories through the labelled coordinate; inspect vertical separation, bridge/deck membership, TerrainCollider continuity, barriers, and whether movement can transfer between the two roads.
- `connected_same_level` observation: both approaches visibly meet at one elevation and a participant can traverse from either trajectory onto the other.
- `grade_separated_not_connected` observation: one trajectory passes above or below the other, or a physical separation prevents transfer at the crossing.
- Review status: `completed`
- Decision: `connected_same_level`
- Evidence: `manual Unity 3D visual inspection`
- Evidence summary: Researcher manually inspected the corresponding crossing in the 3D Unity environment and confirmed both road trajectories meet on the same navigable surface with no road-over-road or road-under-road grade separation.

### E38-C014

- Environment: Env38
- Source XY: `(392.952391429524, 322.378123350775)`
- Mapped 3D locator: `VirEnv_38 prefab-local XZ (116.847938324, 205.058808199); Y unavailable`
- Segments: `env38_shape_4330855547456548042_segment_0004` and `env38_shape_4330855547456548042_segment_0014`
- Shapes: `env38_shape_4330855547456548042` and `env38_shape_4330855547456548042`
- Same Shape: `true`
- Source anomaly involved: `false`
- Check in 3D: follow both road trajectories through the labelled coordinate; inspect vertical separation, bridge/deck membership, TerrainCollider continuity, barriers, and whether movement can transfer between the two roads.
- `connected_same_level` observation: both approaches visibly meet at one elevation and a participant can traverse from either trajectory onto the other.
- `grade_separated_not_connected` observation: one trajectory passes above or below the other, or a physical separation prevents transfer at the crossing.
- Review status: `completed`
- Decision: `connected_same_level`
- Evidence: `manual Unity 3D visual inspection`
- Evidence summary: Researcher manually inspected the corresponding crossing in the 3D Unity environment and confirmed both road trajectories meet on the same navigable surface with no road-over-road or road-under-road grade separation.

### E38-C015

- Environment: Env38
- Source XY: `(323.700959742902, 206.337800310839)`
- Mapped 3D locator: `VirEnv_38 prefab-local XZ (47.530958618, 88.927462374); Y unavailable`
- Segments: `env38_shape_4330855547456548042_segment_0009` and `env38_shape_4330855547529842337_segment_0018`
- Shapes: `env38_shape_4330855547456548042` and `env38_shape_4330855547529842337`
- Same Shape: `false`
- Source anomaly involved: `false`
- Check in 3D: follow both road trajectories through the labelled coordinate; inspect vertical separation, bridge/deck membership, TerrainCollider continuity, barriers, and whether movement can transfer between the two roads.
- `connected_same_level` observation: both approaches visibly meet at one elevation and a participant can traverse from either trajectory onto the other.
- `grade_separated_not_connected` observation: one trajectory passes above or below the other, or a physical separation prevents transfer at the crossing.
- Review status: `completed`
- Decision: `connected_same_level`
- Evidence: `manual Unity 3D visual inspection`
- Evidence summary: Researcher manually inspected the corresponding crossing in the 3D Unity environment and confirmed both road trajectories meet on the same navigable surface with no road-over-road or road-under-road grade separation.

### E38-C016

- Environment: Env38
- Source XY: `(320.046535853057, 239.994534789858)`
- Mapped 3D locator: `VirEnv_38 prefab-local XZ (43.873075734, 122.610597415); Y unavailable`
- Segments: `env38_shape_4330855547456548042_segment_0010` and `env38_shape_4330855547456548042_segment_0020`
- Shapes: `env38_shape_4330855547456548042` and `env38_shape_4330855547456548042`
- Same Shape: `true`
- Source anomaly involved: `false`
- Check in 3D: follow both road trajectories through the labelled coordinate; inspect vertical separation, bridge/deck membership, TerrainCollider continuity, barriers, and whether movement can transfer between the two roads.
- `connected_same_level` observation: both approaches visibly meet at one elevation and a participant can traverse from either trajectory onto the other.
- `grade_separated_not_connected` observation: one trajectory passes above or below the other, or a physical separation prevents transfer at the crossing.
- Review status: `completed`
- Decision: `connected_same_level`
- Evidence: `manual Unity 3D visual inspection`
- Evidence summary: Researcher manually inspected the corresponding crossing in the 3D Unity environment and confirmed both road trajectories meet on the same navigable surface with no road-over-road or road-under-road grade separation.

### E38-C017

- Environment: Env38
- Source XY: `(267.369223963434, 225.678759783257)`
- Mapped 3D locator: `VirEnv_38 prefab-local XZ (-8.854096402, 108.283593021); Y unavailable`
- Segments: `env38_shape_4330855547456548042_segment_0022` and `env38_shape_4330855547524397474_segment_0007`
- Shapes: `env38_shape_4330855547456548042` and `env38_shape_4330855547524397474`
- Same Shape: `false`
- Source anomaly involved: `false`
- Check in 3D: follow both road trajectories through the labelled coordinate; inspect vertical separation, bridge/deck membership, TerrainCollider continuity, barriers, and whether movement can transfer between the two roads.
- `connected_same_level` observation: both approaches visibly meet at one elevation and a participant can traverse from either trajectory onto the other.
- `grade_separated_not_connected` observation: one trajectory passes above or below the other, or a physical separation prevents transfer at the crossing.
- Review status: `completed`
- Decision: `connected_same_level`
- Evidence: `manual Unity 3D visual inspection`
- Evidence summary: Researcher manually inspected the corresponding crossing in the 3D Unity environment and confirmed both road trajectories meet on the same navigable surface with no road-over-road or road-under-road grade separation.

### E38-C018

- Environment: Env38
- Source XY: `(189.157933781744, 232.143912988943)`
- Mapped 3D locator: `VirEnv_38 prefab-local XZ (-87.139415309, 114.753817535); Y unavailable`
- Segments: `env38_shape_4330855547456548042_segment_0024` and `env38_shape_4330855547456548042_segment_0031`
- Shapes: `env38_shape_4330855547456548042` and `env38_shape_4330855547456548042`
- Same Shape: `true`
- Source anomaly involved: `false`
- Check in 3D: follow both road trajectories through the labelled coordinate; inspect vertical separation, bridge/deck membership, TerrainCollider continuity, barriers, and whether movement can transfer between the two roads.
- `connected_same_level` observation: both approaches visibly meet at one elevation and a participant can traverse from either trajectory onto the other.
- `grade_separated_not_connected` observation: one trajectory passes above or below the other, or a physical separation prevents transfer at the crossing.
- Review status: `completed`
- Decision: `connected_same_level`
- Evidence: `manual Unity 3D visual inspection`
- Evidence summary: Researcher manually inspected the corresponding crossing in the 3D Unity environment and confirmed both road trajectories meet on the same navigable surface with no road-over-road or road-under-road grade separation.

### E38-C019

- Environment: Env38
- Source XY: `(190.791806238746, 232.140675866932)`
- Mapped 3D locator: `VirEnv_38 prefab-local XZ (-85.503996355, 114.750577874); Y unavailable`
- Segments: `env38_shape_4330855547456548042_segment_0024` and `env38_shape_4330855547529842337_segment_0012`
- Shapes: `env38_shape_4330855547456548042` and `env38_shape_4330855547529842337`
- Same Shape: `false`
- Source anomaly involved: `false`
- Check in 3D: follow both road trajectories through the labelled coordinate; inspect vertical separation, bridge/deck membership, TerrainCollider continuity, barriers, and whether movement can transfer between the two roads.
- `connected_same_level` observation: both approaches visibly meet at one elevation and a participant can traverse from either trajectory onto the other.
- `grade_separated_not_connected` observation: one trajectory passes above or below the other, or a physical separation prevents transfer at the crossing.
- Review status: `completed`
- Decision: `connected_same_level`
- Evidence: `manual Unity 3D visual inspection`
- Evidence summary: Researcher manually inspected the corresponding crossing in the 3D Unity environment and confirmed both road trajectories meet on the same navigable surface with no road-over-road or road-under-road grade separation.

### E38-C020

- Environment: Env38
- Source XY: `(70.4633046696523, 220.90083941202)`
- Mapped 3D locator: `VirEnv_38 prefab-local XZ (-205.946391526, 103.501924818); Y unavailable`
- Segments: `env38_shape_4330855547456548042_segment_0025` and `env38_shape_4330855547829185599_segment_0017`
- Shapes: `env38_shape_4330855547456548042` and `env38_shape_4330855547829185599`
- Same Shape: `false`
- Source anomaly involved: `false`
- Check in 3D: follow both road trajectories through the labelled coordinate; inspect vertical separation, bridge/deck membership, TerrainCollider continuity, barriers, and whether movement can transfer between the two roads.
- `connected_same_level` observation: both approaches visibly meet at one elevation and a participant can traverse from either trajectory onto the other.
- `grade_separated_not_connected` observation: one trajectory passes above or below the other, or a physical separation prevents transfer at the crossing.
- Review status: `completed`
- Decision: `connected_same_level`
- Evidence: `manual Unity 3D visual inspection`
- Evidence summary: Researcher manually inspected the corresponding crossing in the 3D Unity environment and confirmed both road trajectories meet on the same navigable surface with no road-over-road or road-under-road grade separation.

### E38-C021

- Environment: Env38
- Source XY: `(41.8827456088867, 220.149483369921)`
- Mapped 3D locator: `VirEnv_38 prefab-local XZ (-234.554002721, 102.749979407); Y unavailable`
- Segments: `env38_shape_4330855547456548042_segment_0026` and `env38_shape_4330855547829185599_segment_0027`
- Shapes: `env38_shape_4330855547456548042` and `env38_shape_4330855547829185599`
- Same Shape: `false`
- Source anomaly involved: `false`
- Check in 3D: follow both road trajectories through the labelled coordinate; inspect vertical separation, bridge/deck membership, TerrainCollider continuity, barriers, and whether movement can transfer between the two roads.
- `connected_same_level` observation: both approaches visibly meet at one elevation and a participant can traverse from either trajectory onto the other.
- `grade_separated_not_connected` observation: one trajectory passes above or below the other, or a physical separation prevents transfer at the crossing.
- Review status: `completed`
- Decision: `connected_same_level`
- Evidence: `manual Unity 3D visual inspection`
- Evidence summary: Researcher manually inspected the corresponding crossing in the 3D Unity environment and confirmed both road trajectories meet on the same navigable surface with no road-over-road or road-under-road grade separation.

### E38-C022

- Environment: Env38
- Source XY: `(258.277081054884, 270.8893559378)`
- Mapped 3D locator: `VirEnv_38 prefab-local XZ (-17.954845226, 153.529652662); Y unavailable`
- Segments: `env38_shape_4330855547456548042_segment_0028` and `env38_shape_4330855547524397474_segment_0008`
- Shapes: `env38_shape_4330855547456548042` and `env38_shape_4330855547524397474`
- Same Shape: `false`
- Source anomaly involved: `false`
- Check in 3D: follow both road trajectories through the labelled coordinate; inspect vertical separation, bridge/deck membership, TerrainCollider continuity, barriers, and whether movement can transfer between the two roads.
- `connected_same_level` observation: both approaches visibly meet at one elevation and a participant can traverse from either trajectory onto the other.
- `grade_separated_not_connected` observation: one trajectory passes above or below the other, or a physical separation prevents transfer at the crossing.
- Review status: `completed`
- Decision: `connected_same_level`
- Evidence: `manual Unity 3D visual inspection`
- Evidence summary: Researcher manually inspected the corresponding crossing in the 3D Unity environment and confirmed both road trajectories meet on the same navigable surface with no road-over-road or road-under-road grade separation.

### E38-C023

- Environment: Env38
- Source XY: `(196.507063639584, 266.352511122499)`
- Mapped 3D locator: `VirEnv_38 prefab-local XZ (-79.783329336, 148.989249116); Y unavailable`
- Segments: `env38_shape_4330855547456548042_segment_0029` and `env38_shape_4330855547456548042_segment_0032`
- Shapes: `env38_shape_4330855547456548042` and `env38_shape_4330855547456548042`
- Same Shape: `true`
- Source anomaly involved: `false`
- Check in 3D: follow both road trajectories through the labelled coordinate; inspect vertical separation, bridge/deck membership, TerrainCollider continuity, barriers, and whether movement can transfer between the two roads.
- `connected_same_level` observation: both approaches visibly meet at one elevation and a participant can traverse from either trajectory onto the other.
- `grade_separated_not_connected` observation: one trajectory passes above or below the other, or a physical separation prevents transfer at the crossing.
- Review status: `completed`
- Decision: `connected_same_level`
- Evidence: `manual Unity 3D visual inspection`
- Evidence summary: Researcher manually inspected the corresponding crossing in the 3D Unity environment and confirmed both road trajectories meet on the same navigable surface with no road-over-road or road-under-road grade separation.

### E38-C024

- Environment: Env38
- Source XY: `(190.802386937984, 231.839408040241)`
- Mapped 3D locator: `VirEnv_38 prefab-local XZ (-85.493405641, 114.449073731); Y unavailable`
- Segments: `env38_shape_4330855547456548042_segment_0030` and `env38_shape_4330855547529842337_segment_0012`
- Shapes: `env38_shape_4330855547456548042` and `env38_shape_4330855547529842337`
- Same Shape: `false`
- Source anomaly involved: `false`
- Check in 3D: follow both road trajectories through the labelled coordinate; inspect vertical separation, bridge/deck membership, TerrainCollider continuity, barriers, and whether movement can transfer between the two roads.
- `connected_same_level` observation: both approaches visibly meet at one elevation and a participant can traverse from either trajectory onto the other.
- `grade_separated_not_connected` observation: one trajectory passes above or below the other, or a physical separation prevents transfer at the crossing.
- Review status: `completed`
- Decision: `connected_same_level`
- Evidence: `manual Unity 3D visual inspection`
- Evidence summary: Researcher manually inspected the corresponding crossing in the 3D Unity environment and confirmed both road trajectories meet on the same navigable surface with no road-over-road or road-under-road grade separation.

### E38-C025

- Environment: Env38
- Source XY: `(266.241688974308, -29.2881186677869)`
- Mapped 3D locator: `VirEnv_38 prefab-local XZ (-9.982698628, -146.883283110); Y unavailable`
- Segments: `env38_shape_4330855547524397474_segment_0005` and `env38_shape_4330855547524397474_segment_0020`
- Shapes: `env38_shape_4330855547524397474` and `env38_shape_4330855547524397474`
- Same Shape: `true`
- Source anomaly involved: `false`
- Check in 3D: follow both road trajectories through the labelled coordinate; inspect vertical separation, bridge/deck membership, TerrainCollider continuity, barriers, and whether movement can transfer between the two roads.
- `connected_same_level` observation: both approaches visibly meet at one elevation and a participant can traverse from either trajectory onto the other.
- `grade_separated_not_connected` observation: one trajectory passes above or below the other, or a physical separation prevents transfer at the crossing.
- Review status: `completed`
- Decision: `connected_same_level`
- Evidence: `manual Unity 3D visual inspection`
- Evidence summary: Researcher manually inspected the corresponding crossing in the 3D Unity environment and confirmed both road trajectories meet on the same navigable surface with no road-over-road or road-under-road grade separation.

### E38-C026

- Environment: Env38
- Source XY: `(265.147976206715, 188.956149619555)`
- Mapped 3D locator: `VirEnv_38 prefab-local XZ (-11.077446619, 71.532177403); Y unavailable`
- Segments: `env38_shape_4330855547524397474_segment_0007` and `env38_shape_4330855547529842337_segment_0015`
- Shapes: `env38_shape_4330855547524397474` and `env38_shape_4330855547529842337`
- Same Shape: `false`
- Source anomaly involved: `false`
- Check in 3D: follow both road trajectories through the labelled coordinate; inspect vertical separation, bridge/deck membership, TerrainCollider continuity, barriers, and whether movement can transfer between the two roads.
- `connected_same_level` observation: both approaches visibly meet at one elevation and a participant can traverse from either trajectory onto the other.
- `grade_separated_not_connected` observation: one trajectory passes above or below the other, or a physical separation prevents transfer at the crossing.
- Review status: `completed`
- Decision: `connected_same_level`
- Evidence: `manual Unity 3D visual inspection`
- Evidence summary: Researcher manually inspected the corresponding crossing in the 3D Unity environment and confirmed both road trajectories meet on the same navigable surface with no road-over-road or road-under-road grade separation.

### E38-C027

- Environment: Env38
- Source XY: `(90.082806529435, -3.93613048610397)`
- Mapped 3D locator: `VirEnv_38 prefab-local XZ (-186.308319372, -121.511408664); Y unavailable`
- Segments: `env38_shape_4330855547524397474_segment_0024` and `env38_shape_4330855547829185599_segment_0010`
- Shapes: `env38_shape_4330855547524397474` and `env38_shape_4330855547829185599`
- Same Shape: `false`
- Source anomaly involved: `false`
- Check in 3D: follow both road trajectories through the labelled coordinate; inspect vertical separation, bridge/deck membership, TerrainCollider continuity, barriers, and whether movement can transfer between the two roads.
- `connected_same_level` observation: both approaches visibly meet at one elevation and a participant can traverse from either trajectory onto the other.
- `grade_separated_not_connected` observation: one trajectory passes above or below the other, or a physical separation prevents transfer at the crossing.
- Review status: `completed`
- Decision: `connected_same_level`
- Evidence: `manual Unity 3D visual inspection`
- Evidence summary: Researcher manually inspected the corresponding crossing in the 3D Unity environment and confirmed both road trajectories meet on the same navigable surface with no road-over-road or road-under-road grade separation.

### E38-C028

- Environment: Env38
- Source XY: `(275.15530341636, -104.539061425077)`
- Mapped 3D locator: `VirEnv_38 prefab-local XZ (-1.060647252, -222.193253197); Y unavailable`
- Segments: `env38_shape_4330855547524397474_segment_0029` and `env38_shape_4330855547829185599_segment_0001`
- Shapes: `env38_shape_4330855547524397474` and `env38_shape_4330855547829185599`
- Same Shape: `false`
- Source anomaly involved: `false`
- Check in 3D: follow both road trajectories through the labelled coordinate; inspect vertical separation, bridge/deck membership, TerrainCollider continuity, barriers, and whether movement can transfer between the two roads.
- `connected_same_level` observation: both approaches visibly meet at one elevation and a participant can traverse from either trajectory onto the other.
- `grade_separated_not_connected` observation: one trajectory passes above or below the other, or a physical separation prevents transfer at the crossing.
- Review status: `completed`
- Decision: `connected_same_level`
- Evidence: `manual Unity 3D visual inspection`
- Evidence summary: Researcher manually inspected the corresponding crossing in the 3D Unity environment and confirmed both road trajectories meet on the same navigable surface with no road-over-road or road-under-road grade separation.

### E39-C001

- Environment: Env39
- Source XY: `(322.691830338892, 113.809477006633)`
- Mapped 3D locator: `VirEnv_39 prefab-local XZ (46.520927722, -3.673436065); Y unavailable`
- Segments: `env39_shape_3305298596651482022_segment_0001` and `env39_shape_3305298596651482022_segment_0011`
- Shapes: `env39_shape_3305298596651482022` and `env39_shape_3305298596651482022`
- Same Shape: `true`
- Source anomaly involved: `false`
- Check in 3D: follow both road trajectories through the labelled coordinate; inspect vertical separation, bridge/deck membership, TerrainCollider continuity, barriers, and whether movement can transfer between the two roads.
- `connected_same_level` observation: both approaches visibly meet at one elevation and a participant can traverse from either trajectory onto the other.
- `grade_separated_not_connected` observation: one trajectory passes above or below the other, or a physical separation prevents transfer at the crossing.
- Review status: `completed`
- Decision: `connected_same_level`
- Evidence: `manual Unity 3D visual inspection`
- Evidence summary: Researcher manually inspected the corresponding crossing in the 3D Unity environment and confirmed both road trajectories meet on the same navigable surface with no road-over-road or road-under-road grade separation.

### E39-C002

- Environment: Env39
- Source XY: `(263.536095331648, 113.800363734199)`
- Mapped 3D locator: `VirEnv_39 prefab-local XZ (-12.690830455, -3.682556489); Y unavailable`
- Segments: `env39_shape_3305298596651482022_segment_0001` and `env39_shape_3305298596651482022_segment_0014`
- Shapes: `env39_shape_3305298596651482022` and `env39_shape_3305298596651482022`
- Same Shape: `true`
- Source anomaly involved: `false`
- Check in 3D: follow both road trajectories through the labelled coordinate; inspect vertical separation, bridge/deck membership, TerrainCollider continuity, barriers, and whether movement can transfer between the two roads.
- `connected_same_level` observation: both approaches visibly meet at one elevation and a participant can traverse from either trajectory onto the other.
- `grade_separated_not_connected` observation: one trajectory passes above or below the other, or a physical separation prevents transfer at the crossing.
- Review status: `completed`
- Decision: `connected_same_level`
- Evidence: `manual Unity 3D visual inspection`
- Evidence summary: Researcher manually inspected the corresponding crossing in the 3D Unity environment and confirmed both road trajectories meet on the same navigable surface with no road-over-road or road-under-road grade separation.

### E39-C003

- Environment: Env39
- Source XY: `(72.7708365353398, 113.771327218419)`
- Mapped 3D locator: `VirEnv_39 prefab-local XZ (-203.636752623, -3.711615791); Y unavailable`
- Segments: `env39_shape_3305298596651482022_segment_0001` and `env39_shape_3305298596651482022_segment_0022`
- Shapes: `env39_shape_3305298596651482022` and `env39_shape_3305298596651482022`
- Same Shape: `true`
- Source anomaly involved: `false`
- Check in 3D: follow both road trajectories through the labelled coordinate; inspect vertical separation, bridge/deck membership, TerrainCollider continuity, barriers, and whether movement can transfer between the two roads.
- `connected_same_level` observation: both approaches visibly meet at one elevation and a participant can traverse from either trajectory onto the other.
- `grade_separated_not_connected` observation: one trajectory passes above or below the other, or a physical separation prevents transfer at the crossing.
- Review status: `completed`
- Decision: `connected_same_level`
- Evidence: `manual Unity 3D visual inspection`
- Evidence summary: Researcher manually inspected the corresponding crossing in the 3D Unity environment and confirmed both road trajectories meet on the same navigable surface with no road-over-road or road-under-road grade separation.

### E39-C004

- Environment: Env39
- Source XY: `(388.006764163102, -63.3483298935652)`
- Mapped 3D locator: `VirEnv_39 prefab-local XZ (111.897717758, -180.970266803); Y unavailable`
- Segments: `env39_shape_3305298596651482022_segment_0003` and `env39_shape_3305298596651482022_segment_0012`
- Shapes: `env39_shape_3305298596651482022` and `env39_shape_3305298596651482022`
- Same Shape: `true`
- Source anomaly involved: `false`
- Check in 3D: follow both road trajectories through the labelled coordinate; inspect vertical separation, bridge/deck membership, TerrainCollider continuity, barriers, and whether movement can transfer between the two roads.
- `connected_same_level` observation: both approaches visibly meet at one elevation and a participant can traverse from either trajectory onto the other.
- `grade_separated_not_connected` observation: one trajectory passes above or below the other, or a physical separation prevents transfer at the crossing.
- Review status: `completed`
- Decision: `connected_same_level`
- Evidence: `manual Unity 3D visual inspection`
- Evidence summary: Researcher manually inspected the corresponding crossing in the 3D Unity environment and confirmed both road trajectories meet on the same navigable surface with no road-over-road or road-under-road grade separation.

### E39-C005

- Environment: Env39
- Source XY: `(38.6022260714872, 224.957425966775)`
- Mapped 3D locator: `VirEnv_39 prefab-local XZ (-237.837722314, 107.561735777); Y unavailable`
- Segments: `env39_shape_3305298596651482022_segment_0004` and `env39_shape_3305298596651482022_segment_0006`
- Shapes: `env39_shape_3305298596651482022` and `env39_shape_3305298596651482022`
- Same Shape: `true`
- Source anomaly involved: `false`
- Check in 3D: follow both road trajectories through the labelled coordinate; inspect vertical separation, bridge/deck membership, TerrainCollider continuity, barriers, and whether movement can transfer between the two roads.
- `connected_same_level` observation: both approaches visibly meet at one elevation and a participant can traverse from either trajectory onto the other.
- `grade_separated_not_connected` observation: one trajectory passes above or below the other, or a physical separation prevents transfer at the crossing.
- Review status: `completed`
- Decision: `connected_same_level`
- Evidence: `manual Unity 3D visual inspection`
- Evidence summary: Researcher manually inspected the corresponding crossing in the 3D Unity environment and confirmed both road trajectories meet on the same navigable surface with no road-over-road or road-under-road grade separation.

### E39-C006

- Environment: Env39
- Source XY: `(320.508842819834, 224.204469243554)`
- Mapped 3D locator: `VirEnv_39 prefab-local XZ (44.335872815, 106.808188175); Y unavailable`
- Segments: `env39_shape_3305298596651482022_segment_0004` and `env39_shape_3305298596651482022_segment_0011`
- Shapes: `env39_shape_3305298596651482022` and `env39_shape_3305298596651482022`
- Same Shape: `true`
- Source anomaly involved: `false`
- Check in 3D: follow both road trajectories through the labelled coordinate; inspect vertical separation, bridge/deck membership, TerrainCollider continuity, barriers, and whether movement can transfer between the two roads.
- `connected_same_level` observation: both approaches visibly meet at one elevation and a participant can traverse from either trajectory onto the other.
- `grade_separated_not_connected` observation: one trajectory passes above or below the other, or a physical separation prevents transfer at the crossing.
- Review status: `completed`
- Decision: `connected_same_level`
- Evidence: `manual Unity 3D visual inspection`
- Evidence summary: Researcher manually inspected the corresponding crossing in the 3D Unity environment and confirmed both road trajectories meet on the same navigable surface with no road-over-road or road-under-road grade separation.

### E39-C007

- Environment: Env39
- Source XY: `(261.852632524452, 224.361204828945)`
- Mapped 3D locator: `VirEnv_39 prefab-local XZ (-14.375887578, 106.965046757); Y unavailable`
- Segments: `env39_shape_3305298596651482022_segment_0004` and `env39_shape_3305298596651482022_segment_0014`
- Shapes: `env39_shape_3305298596651482022` and `env39_shape_3305298596651482022`
- Same Shape: `true`
- Source anomaly involved: `false`
- Check in 3D: follow both road trajectories through the labelled coordinate; inspect vertical separation, bridge/deck membership, TerrainCollider continuity, barriers, and whether movement can transfer between the two roads.
- `connected_same_level` observation: both approaches visibly meet at one elevation and a participant can traverse from either trajectory onto the other.
- `grade_separated_not_connected` observation: one trajectory passes above or below the other, or a physical separation prevents transfer at the crossing.
- Review status: `completed`
- Decision: `connected_same_level`
- Evidence: `manual Unity 3D visual inspection`
- Evidence summary: Researcher manually inspected the corresponding crossing in the 3D Unity environment and confirmed both road trajectories meet on the same navigable surface with no road-over-road or road-under-road grade separation.

### E39-C008

- Environment: Env39
- Source XY: `(70.9978655446908, 224.870941098947)`
- Mapped 3D locator: `VirEnv_39 prefab-local XZ (-205.411402697, 107.475183041); Y unavailable`
- Segments: `env39_shape_3305298596651482022_segment_0004` and `env39_shape_3305298596651482022_segment_0022`
- Shapes: `env39_shape_3305298596651482022` and `env39_shape_3305298596651482022`
- Same Shape: `true`
- Source anomaly involved: `false`
- Check in 3D: follow both road trajectories through the labelled coordinate; inspect vertical separation, bridge/deck membership, TerrainCollider continuity, barriers, and whether movement can transfer between the two roads.
- `connected_same_level` observation: both approaches visibly meet at one elevation and a participant can traverse from either trajectory onto the other.
- `grade_separated_not_connected` observation: one trajectory passes above or below the other, or a physical separation prevents transfer at the crossing.
- Review status: `completed`
- Decision: `connected_same_level`
- Evidence: `manual Unity 3D visual inspection`
- Evidence summary: Researcher manually inspected the corresponding crossing in the 3D Unity environment and confirmed both road trajectories meet on the same navigable surface with no road-over-road or road-under-road grade separation.

### E39-C009

- Environment: Env39
- Source XY: `(149.999059104571, 224.659990133847)`
- Mapped 3D locator: `VirEnv_39 prefab-local XZ (-126.335391416, 107.264066533); Y unavailable`
- Segments: `env39_shape_3305298596651482022_segment_0004` and `env39_shape_3305298596651482022_segment_0026`
- Shapes: `env39_shape_3305298596651482022` and `env39_shape_3305298596651482022`
- Same Shape: `true`
- Source anomaly involved: `false`
- Check in 3D: follow both road trajectories through the labelled coordinate; inspect vertical separation, bridge/deck membership, TerrainCollider continuity, barriers, and whether movement can transfer between the two roads.
- `connected_same_level` observation: both approaches visibly meet at one elevation and a participant can traverse from either trajectory onto the other.
- `grade_separated_not_connected` observation: one trajectory passes above or below the other, or a physical separation prevents transfer at the crossing.
- Review status: `completed`
- Decision: `connected_same_level`
- Evidence: `manual Unity 3D visual inspection`
- Evidence summary: Researcher manually inspected the corresponding crossing in the 3D Unity environment and confirmed both road trajectories meet on the same navigable surface with no road-over-road or road-under-road grade separation.

### E39-C010

- Environment: Env39
- Source XY: `(202.532302896301, 224.519678592086)`
- Mapped 3D locator: `VirEnv_39 prefab-local XZ (-73.752396255, 107.123644882); Y unavailable`
- Segments: `env39_shape_3305298596651482022_segment_0004` and `env39_shape_3305298596651482022_segment_0031`
- Shapes: `env39_shape_3305298596651482022` and `env39_shape_3305298596651482022`
- Same Shape: `true`
- Source anomaly involved: `false`
- Check in 3D: follow both road trajectories through the labelled coordinate; inspect vertical separation, bridge/deck membership, TerrainCollider continuity, barriers, and whether movement can transfer between the two roads.
- `connected_same_level` observation: both approaches visibly meet at one elevation and a participant can traverse from either trajectory onto the other.
- `grade_separated_not_connected` observation: one trajectory passes above or below the other, or a physical separation prevents transfer at the crossing.
- Review status: `completed`
- Decision: `connected_same_level`
- Evidence: `manual Unity 3D visual inspection`
- Evidence summary: Researcher manually inspected the corresponding crossing in the 3D Unity environment and confirmed both road trajectories meet on the same navigable surface with no road-over-road or road-under-road grade separation.

### E39-C011

- Environment: Env39
- Source XY: `(40.5150119190416, 4.32365778368631)`
- Mapped 3D locator: `VirEnv_39 prefab-local XZ (-235.923124971, -113.245173820); Y unavailable`
- Segments: `env39_shape_3305298596651482022_segment_0007` and `env39_shape_3305298596651482022_segment_0024`
- Shapes: `env39_shape_3305298596651482022` and `env39_shape_3305298596651482022`
- Same Shape: `true`
- Source anomaly involved: `false`
- Check in 3D: follow both road trajectories through the labelled coordinate; inspect vertical separation, bridge/deck membership, TerrainCollider continuity, barriers, and whether movement can transfer between the two roads.
- `connected_same_level` observation: both approaches visibly meet at one elevation and a participant can traverse from either trajectory onto the other.
- `grade_separated_not_connected` observation: one trajectory passes above or below the other, or a physical separation prevents transfer at the crossing.
- Review status: `completed`
- Decision: `connected_same_level`
- Evidence: `manual Unity 3D visual inspection`
- Evidence summary: Researcher manually inspected the corresponding crossing in the 3D Unity environment and confirmed both road trajectories meet on the same navigable surface with no road-over-road or road-under-road grade separation.

### E39-C012

- Environment: Env39
- Source XY: `(324.896499680759, 4.31240095305283)`
- Mapped 3D locator: `VirEnv_39 prefab-local XZ (48.727684986, -113.256439485); Y unavailable`
- Segments: `env39_shape_3305298596651482022_segment_0011` and `env39_shape_3305298596651482022_segment_0023`
- Shapes: `env39_shape_3305298596651482022` and `env39_shape_3305298596651482022`
- Same Shape: `true`
- Source anomaly involved: `false`
- Check in 3D: follow both road trajectories through the labelled coordinate; inspect vertical separation, bridge/deck membership, TerrainCollider continuity, barriers, and whether movement can transfer between the two roads.
- `connected_same_level` observation: both approaches visibly meet at one elevation and a participant can traverse from either trajectory onto the other.
- `grade_separated_not_connected` observation: one trajectory passes above or below the other, or a physical separation prevents transfer at the crossing.
- Review status: `completed`
- Decision: `connected_same_level`
- Evidence: `manual Unity 3D visual inspection`
- Evidence summary: Researcher manually inspected the corresponding crossing in the 3D Unity environment and confirmed both road trajectories meet on the same navigable surface with no road-over-road or road-under-road grade separation.

### E39-C013

- Environment: Env39
- Source XY: `(319.663001343777, 267.540889089394)`
- Mapped 3D locator: `VirEnv_39 prefab-local XZ (43.489230288, 150.178616092); Y unavailable`
- Segments: `env39_shape_3305298596651482022_segment_0011` and `env39_shape_3305298596651482022_segment_0028`
- Shapes: `env39_shape_3305298596651482022` and `env39_shape_3305298596651482022`
- Same Shape: `true`
- Source anomaly involved: `false`
- Check in 3D: follow both road trajectories through the labelled coordinate; inspect vertical separation, bridge/deck membership, TerrainCollider continuity, barriers, and whether movement can transfer between the two roads.
- `connected_same_level` observation: both approaches visibly meet at one elevation and a participant can traverse from either trajectory onto the other.
- `grade_separated_not_connected` observation: one trajectory passes above or below the other, or a physical separation prevents transfer at the crossing.
- Review status: `completed`
- Decision: `connected_same_level`
- Evidence: `manual Unity 3D visual inspection`
- Evidence summary: Researcher manually inspected the corresponding crossing in the 3D Unity environment and confirmed both road trajectories meet on the same navigable surface with no road-over-road or road-under-road grade separation.

### E39-C014

- Environment: Env39
- Source XY: `(321.554425408318, 171.073882184169)`
- Mapped 3D locator: `VirEnv_39 prefab-local XZ (45.382445617, 53.635907112); Y unavailable`
- Segments: `env39_shape_3305298596651482022_segment_0011` and `env39_shape_3305298596651482022_segment_0030`
- Shapes: `env39_shape_3305298596651482022` and `env39_shape_3305298596651482022`
- Same Shape: `true`
- Source anomaly involved: `false`
- Check in 3D: follow both road trajectories through the labelled coordinate; inspect vertical separation, bridge/deck membership, TerrainCollider continuity, barriers, and whether movement can transfer between the two roads.
- `connected_same_level` observation: both approaches visibly meet at one elevation and a participant can traverse from either trajectory onto the other.
- `grade_separated_not_connected` observation: one trajectory passes above or below the other, or a physical separation prevents transfer at the crossing.
- Review status: `completed`
- Decision: `connected_same_level`
- Evidence: `manual Unity 3D visual inspection`
- Evidence summary: Researcher manually inspected the corresponding crossing in the 3D Unity environment and confirmed both road trajectories meet on the same navigable surface with no road-over-road or road-under-road grade separation.

### E39-C015

- Environment: Env39
- Source XY: `(260.559135479696, 309.316328972293)`
- Mapped 3D locator: `VirEnv_39 prefab-local XZ (-15.670609623, 191.986839075); Y unavailable`
- Segments: `env39_shape_3305298596651482022_segment_0014` and `env39_shape_3305298596651482022_segment_0017`
- Shapes: `env39_shape_3305298596651482022` and `env39_shape_3305298596651482022`
- Same Shape: `true`
- Source anomaly involved: `false`
- Check in 3D: follow both road trajectories through the labelled coordinate; inspect vertical separation, bridge/deck membership, TerrainCollider continuity, barriers, and whether movement can transfer between the two roads.
- `connected_same_level` observation: both approaches visibly meet at one elevation and a participant can traverse from either trajectory onto the other.
- `grade_separated_not_connected` observation: one trajectory passes above or below the other, or a physical separation prevents transfer at the crossing.
- Review status: `completed`
- Decision: `connected_same_level`
- Evidence: `manual Unity 3D visual inspection`
- Evidence summary: Researcher manually inspected the corresponding crossing in the 3D Unity environment and confirmed both road trajectories meet on the same navigable surface with no road-over-road or road-under-road grade separation.

### E39-C016

- Environment: Env39
- Source XY: `(265.203171792603, 4.32316023361248)`
- Mapped 3D locator: `VirEnv_39 prefab-local XZ (-11.022175197, -113.245671761); Y unavailable`
- Segments: `env39_shape_3305298596651482022_segment_0014` and `env39_shape_3305298596651482022_segment_0023`
- Shapes: `env39_shape_3305298596651482022` and `env39_shape_3305298596651482022`
- Same Shape: `true`
- Source anomaly involved: `false`
- Check in 3D: follow both road trajectories through the labelled coordinate; inspect vertical separation, bridge/deck membership, TerrainCollider continuity, barriers, and whether movement can transfer between the two roads.
- `connected_same_level` observation: both approaches visibly meet at one elevation and a participant can traverse from either trajectory onto the other.
- `grade_separated_not_connected` observation: one trajectory passes above or below the other, or a physical separation prevents transfer at the crossing.
- Review status: `completed`
- Decision: `connected_same_level`
- Evidence: `manual Unity 3D visual inspection`
- Evidence summary: Researcher manually inspected the corresponding crossing in the 3D Unity environment and confirmed both road trajectories meet on the same navigable surface with no road-over-road or road-under-road grade separation.

### E39-C017

- Environment: Env39
- Source XY: `(261.186585809054, 268.10568696134)`
- Mapped 3D locator: `VirEnv_39 prefab-local XZ (-15.042565070, 150.743857187); Y unavailable`
- Segments: `env39_shape_3305298596651482022_segment_0014` and `env39_shape_3305298596651482022_segment_0028`
- Shapes: `env39_shape_3305298596651482022` and `env39_shape_3305298596651482022`
- Same Shape: `true`
- Source anomaly involved: `false`
- Check in 3D: follow both road trajectories through the labelled coordinate; inspect vertical separation, bridge/deck membership, TerrainCollider continuity, barriers, and whether movement can transfer between the two roads.
- `connected_same_level` observation: both approaches visibly meet at one elevation and a participant can traverse from either trajectory onto the other.
- `grade_separated_not_connected` observation: one trajectory passes above or below the other, or a physical separation prevents transfer at the crossing.
- Review status: `completed`
- Decision: `connected_same_level`
- Evidence: `manual Unity 3D visual inspection`
- Evidence summary: Researcher manually inspected the corresponding crossing in the 3D Unity environment and confirmed both road trajectories meet on the same navigable surface with no road-over-road or road-under-road grade separation.

### E39-C018

- Environment: Env39
- Source XY: `(262.668083741362, 170.805780030999)`
- Mapped 3D locator: `VirEnv_39 prefab-local XZ (-13.559664092, 53.367594567); Y unavailable`
- Segments: `env39_shape_3305298596651482022_segment_0014` and `env39_shape_3305298596651482022_segment_0030`
- Shapes: `env39_shape_3305298596651482022` and `env39_shape_3305298596651482022`
- Same Shape: `true`
- Source anomaly involved: `false`
- Check in 3D: follow both road trajectories through the labelled coordinate; inspect vertical separation, bridge/deck membership, TerrainCollider continuity, barriers, and whether movement can transfer between the two roads.
- `connected_same_level` observation: both approaches visibly meet at one elevation and a participant can traverse from either trajectory onto the other.
- `grade_separated_not_connected` observation: one trajectory passes above or below the other, or a physical separation prevents transfer at the crossing.
- Review status: `completed`
- Decision: `connected_same_level`
- Evidence: `manual Unity 3D visual inspection`
- Evidence summary: Researcher manually inspected the corresponding crossing in the 3D Unity environment and confirmed both road trajectories meet on the same navigable surface with no road-over-road or road-under-road grade separation.

### E39-C019

- Environment: Env39
- Source XY: `(266.194019866704, -105.224868894307)`
- Mapped 3D locator: `VirEnv_39 prefab-local XZ (-10.030388745, -222.879668241); Y unavailable`
- Segments: `env39_shape_3305298596651482022_segment_0016` and `env39_shape_3305298596651482022_segment_0020`
- Shapes: `env39_shape_3305298596651482022` and `env39_shape_3305298596651482022`
- Same Shape: `true`
- Source anomaly involved: `false`
- Check in 3D: follow both road trajectories through the labelled coordinate; inspect vertical separation, bridge/deck membership, TerrainCollider continuity, barriers, and whether movement can transfer between the two roads.
- `connected_same_level` observation: both approaches visibly meet at one elevation and a participant can traverse from either trajectory onto the other.
- `grade_separated_not_connected` observation: one trajectory passes above or below the other, or a physical separation prevents transfer at the crossing.
- Review status: `completed`
- Decision: `connected_same_level`
- Evidence: `manual Unity 3D visual inspection`
- Evidence summary: Researcher manually inspected the corresponding crossing in the 3D Unity environment and confirmed both road trajectories meet on the same navigable surface with no road-over-road or road-under-road grade separation.

### E39-C020

- Environment: Env39
- Source XY: `(202.01727329069, 268.293065909609)`
- Mapped 3D locator: `VirEnv_39 prefab-local XZ (-74.267913617, 150.931383180); Y unavailable`
- Segments: `env39_shape_3305298596651482022_segment_0028` and `env39_shape_3305298596651482022_segment_0031`
- Shapes: `env39_shape_3305298596651482022` and `env39_shape_3305298596651482022`
- Same Shape: `true`
- Source anomaly involved: `false`
- Check in 3D: follow both road trajectories through the labelled coordinate; inspect vertical separation, bridge/deck membership, TerrainCollider continuity, barriers, and whether movement can transfer between the two roads.
- `connected_same_level` observation: both approaches visibly meet at one elevation and a participant can traverse from either trajectory onto the other.
- `grade_separated_not_connected` observation: one trajectory passes above or below the other, or a physical separation prevents transfer at the crossing.
- Review status: `completed`
- Decision: `connected_same_level`
- Evidence: `manual Unity 3D visual inspection`
- Evidence summary: Researcher manually inspected the corresponding crossing in the 3D Unity environment and confirmed both road trajectories meet on the same navigable surface with no road-over-road or road-under-road grade separation.
