# GeoGami Street Morphology

This project provides a reproducible, research-grade quantitative comparison of the street-network morphology of two synthetic GeoGami environments created in Unity:

- Environment 38: curvilinear / curvy (`2D Map Vir 38`)
- Environment 39: grid-like / grid (`2D Map Vir 39`)

The planned workflow is:

`Unity Shapes2D` → `raw quadratic Bézier data` → `detailed GIS geometry and navigable topology` → `OSMnx-compatible morphology analysis`

The analysis will compare street-network orientation, curvature, and topology without assuming in advance that the intended classifications are quantitatively supported. The immutable raw Bézier representation, detailed sampled geometry, and topological network are kept conceptually and operationally distinct.

Phases 0–2 establish the methodology, verified Unity source provenance, and the future exporter's technical contract. No exporter or Python/OSMnx analysis has yet been implemented, and no metric values have been calculated.

## Documentation

- [Methodology and geometry provenance](docs/methodology.md)
- [Phase 1 Unity source-data model and provenance](docs/source-data-model.md)
- [Phase 2 lossless Unity-to-JSON exporter specification](docs/exporter-specification.md)
