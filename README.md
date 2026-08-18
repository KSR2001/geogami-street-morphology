# GeoGami Street Morphology

This project provides a reproducible, research-grade quantitative comparison of the street-network morphology of two synthetic GeoGami environments created in Unity:

- Environment 38: curvilinear / curvy (`2D Map Vir 38`)
- Environment 39: grid-like / grid (`2D Map Vir 39`)

The planned workflow is:

`Unity Shapes2D` → `raw quadratic Bézier data` → `detailed GIS geometry and navigable topology` → `OSMnx-compatible morphology analysis`

The analysis will compare street-network orientation, curvature, and topology without assuming in advance that the intended classifications are quantitatively supported. The immutable raw Bézier representation, detailed sampled geometry, and topological network are kept conceptually and operationally distinct.

Phases 0–8 establish the methodology, verified Unity source provenance, exporter contract, frozen canonical raw Bézier exports, reproducible Python environment, converged adaptive linework, and a refined pairwise geometric-intersection inventory. **Phase 9 is COMPLETE:** direct researcher inspection confirmed all 48 interior crossings as same-level connected road junctions. **Phase 10 is COMPLETE:** exact detailed topology, endpoint-based near-miss auditing, and snapping sensitivity selected the zero-snapping baseline. Graph construction and scientific morphology metrics remain deferred.

The Phase 4 canonical exports in `data/raw/` are frozen immutable research inputs; all later transformations must create new files under `data/processed/`.

## Python environment

Create the dedicated Conda environment:

```powershell
conda env create -f environment.yml
```

Run the environment and raw-input smoke test:

```powershell
conda run -n geogami-morphology python scripts/check_environment.py
```

Run the Phase 6 mathematical tests and reconstruction QA:

```powershell
conda run -n geogami-morphology pytest
conda run -n geogami-morphology python scripts/reconstruct_bezier_geometry.py
```

Run the Phase 7 adaptive-discretization tests and convergence analysis:

```powershell
conda run -n geogami-morphology pytest
conda run -n geogami-morphology python scripts/analyze_discretization_convergence.py
```

Run the Phase 8 geometric-intersection tests and inventory:

```powershell
conda run -n geogami-morphology pytest
conda run -n geogami-morphology python scripts/analyze_geometric_intersections.py
```

Generate the Phase 9 read-only Unity navigability review package (replace the Unity project path if needed):

```powershell
conda run -n geogami-morphology python scripts/validate_3d_navigability.py --unity-project "F:\GitHub\geogami-virtual-environment-dev\GeoGami-Vir-Env"
```

Run the Phase 10 topology tests and exact-topology/snapping analysis:

```powershell
conda run -n geogami-morphology pytest
conda run -n geogami-morphology python scripts/analyze_topology_and_snapping.py
```

## Documentation

- [Methodology and geometry provenance](docs/methodology.md)
- [Phase 1 Unity source-data model and provenance](docs/source-data-model.md)
- [Phase 2 lossless Unity-to-JSON exporter specification](docs/exporter-specification.md)
- [Phase 4 raw-data provenance and integrity record](docs/raw-data-provenance.md)
- [Phase 5 Python environment and reproducibility](docs/python-environment.md)
- [Phase 6 lossless Bézier reconstruction and geometry QA](docs/phase6-reconstruction-qa.md)
- [Phase 7 adaptive Bézier discretization and convergence QA](docs/phase7-discretization-convergence.md)
- [Phase 8 geometric intersection reconstruction and QA](docs/phase8-intersection-reconstruction.md)
- [Phase 9 3D navigability validation](docs/phase9-3d-navigability-validation.md)
- [Phase 9 manual Unity review checklist](docs/phase9-manual-unity-review.md)
- [Phase 10 exact topology and snapping sensitivity](docs/phase10-topology-and-snapping.md)
