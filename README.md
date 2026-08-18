# GeoGami Street Morphology

This project provides a reproducible, research-grade quantitative comparison of the street-network morphology of two synthetic GeoGami environments created in Unity:

- Environment 38: curvilinear / curvy (`2D Map Vir 38`)
- Environment 39: grid-like / grid (`2D Map Vir 39`)

The planned workflow is:

`Unity Shapes2D` → `raw quadratic Bézier data` → `detailed GIS geometry and navigable topology` → `OSMnx-compatible morphology analysis`

The analysis will compare street-network orientation, curvature, and topology without assuming in advance that the intended classifications are quantitatively supported. The immutable raw Bézier representation, detailed sampled geometry, and topological network are kept conceptually and operationally distinct.

Phases 0–4 establish the methodology, verified Unity source provenance, exporter contract, and frozen canonical raw Bézier exports. Bézier reconstruction and Python/OSMnx analysis have not yet been implemented, and no metric values have been calculated.

The Phase 4 canonical exports in `data/raw/` are frozen immutable research inputs; all later transformations must create new files under `data/processed/`.

## Documentation

- [Methodology and geometry provenance](docs/methodology.md)
- [Phase 1 Unity source-data model and provenance](docs/source-data-model.md)
- [Phase 2 lossless Unity-to-JSON exporter specification](docs/exporter-specification.md)
- [Phase 4 raw-data provenance and integrity record](docs/raw-data-provenance.md)
