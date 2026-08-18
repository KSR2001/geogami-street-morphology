# GeoGami Street Morphology

This project provides a reproducible, research-grade quantitative comparison of the street-network morphology of two synthetic GeoGami environments created in Unity:

- Environment 38: curvilinear / curvy (`2D Map Vir 38`)
- Environment 39: grid-like / grid (`2D Map Vir 39`)

The planned workflow is:

`Unity Shapes2D` → `raw quadratic Bézier data` → `detailed GIS geometry and navigable topology` → `OSMnx-compatible morphology analysis`

The analysis will compare street-network orientation, curvature, and topology without assuming in advance that the intended classifications are quantitatively supported. The immutable raw Bézier representation, detailed sampled geometry, and topological network are kept conceptually and operationally distinct.

Phases 0–8 establish the methodology, verified Unity source provenance, exporter contract, frozen canonical raw Bézier exports, reproducible Python environment, converged adaptive linework, and a refined pairwise geometric-intersection inventory. Phases 9–11 validate all 48 junctions, select zero canonical snapping, and construct provenance-preserving analytical graphs. **Phase 12 is COMPLETE:** the final descriptive orientation, length, topology, and circuity metrics quantify a strong orientation-based distinction between Env38 and Env39, while the pre-specified aggregate-circuity expectation is not supported.

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

Run the Phase 11 graph tests and graph-construction pipeline:

```powershell
conda run -n geogami-morphology pytest
conda run -n geogami-morphology python scripts/build_network_graphs.py
```

Reproduce the Phase 12 final morphology tables and figures:

```powershell
conda run -n geogami-morphology pytest
conda run -n geogami-morphology python scripts/analyze_final_morphology.py
```

Primary results are in `outputs/tables/phase12-primary-morphology-metrics.csv`; final figures are under `outputs/figures/`.

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
- [Phase 11 network graph construction](docs/phase11-network-graph-construction.md)
- [Phase 12 final morphology analysis](docs/phase12-final-morphology-analysis.md)
