# Phase 5: Python and Geospatial Software Environment

## 1. Phase 5 Scope

Phase 5 establishes the reproducible software environment for later GeoGami street-morphology processing. It installs and verifies the required packages and confirms read-only access to the frozen raw inputs.

Phase 5 does not reconstruct or sample Bézier curves, create geometry or graphs, infer topology, or calculate scientific metrics.

## 2. Environment Manager

Miniconda provides Conda. The installed Conda version used for Phase 5 is `26.5.3`.

Conda base is located at `F:\Miniconda` but must not be used for project analysis or project package installation. The dedicated environment was created from `environment.yml` using the `conda-forge` channel with `nodefaults`; all 168 resolved packages report `conda-forge` as their channel.

## 3. Environment Name

The analysis environment is named:

`geogami-morphology`

Its observed prefix on the Phase 5 Windows system is:

`F:\Miniconda\envs\geogami-morphology`

The prefix is machine-specific and is intentionally absent from committed environment specifications.

## 4. Python Version

The requested Python constraint is `python=3.12`. Conda resolved Python `3.12.13`, and the smoke test explicitly verifies that the interpreter major/minor pair is `(3, 12)`.

Validation uses `conda run -n geogami-morphology ...` so results do not depend on shell activation.

## 5. Direct Dependencies

`environment.yml` is the human-maintained declaration of direct dependencies:

- `python=3.12`
- `osmnx=2.1.1`
- `geopandas`
- `shapely`
- `networkx`
- `pandas`
- `numpy`
- `scipy`
- `matplotlib`
- `pyproj`
- `pytest`

It declares only `conda-forge` and `nodefaults`, contains no `pip` dependency section, and contains no machine-specific prefix.

## 6. Resolved Package Versions

The successfully solved environment reports:

| Software | Resolved version |
|---|---:|
| Python | `3.12.13` |
| OSMnx | `2.1.1` |
| GeoPandas | `1.1.4` |
| Shapely | `2.1.2` |
| NetworkX | `3.6.1` |
| NumPy | `2.5.2` |
| pandas | `3.0.5` |
| SciPy | `1.18.0` |
| Matplotlib | `3.11.1` |
| pyproj | `3.7.2` |
| pytest | `9.1.1` |

Transitive packages and exact build strings are recorded in `environment-lock.yml` and `environment-win-64-explicit.txt`. The solved environment, rather than a guessed transitive version set, is authoritative for Phase 5.

## 7. Creation Procedure

From the repository root, create the dedicated environment with:

```powershell
conda env create -f environment.yml
```

Do not install these packages into base and do not install the direct dependencies one by one. The Phase 5 environment was created cleanly from this command after the user explicitly authorized removal of an earlier incomplete environment with the same name.

## 8. Environment Verification

All required imports succeeded through the dedicated environment:

- NumPy
- pandas
- SciPy
- Matplotlib
- Shapely
- GeoPandas
- NetworkX
- pyproj
- OSMnx

Python major/minor equals `3.12`, and OSMnx equals the required `2.1.1`. The reusable verification command is:

```powershell
conda run -n geogami-morphology python scripts/check_environment.py
```

Phase 5 result: **PASS**.

## 9. Raw-Input Smoke Test

`scripts/check_environment.py` locates the repository relative to its own path, imports the required packages, and parses these files with Python's standard `json` module:

- `data/raw/env38_bezier.json`
- `data/raw/env39_bezier.json`
- `data/raw/manifest.json`

It checks only the frozen inventory baseline:

- Environment 38: ID 38, 5 Shapes, 120 total segments.
- Environment 39: ID 39, 1 Shape, 32 total segments.

The script does not evaluate a Bézier equation, inspect or sample coordinates, create a Shapely object, create a GeoDataFrame, create a NetworkX/OSMnx graph, or calculate a scientific quantity.

## 10. Canonical Raw-Input Hash Verification

The smoke test calculates file hashes with Python standard-library `hashlib` and reports **PASS** for:

| Canonical input | Expected and verified SHA-256 |
|---|---|
| `data/raw/env38_bezier.json` | `43ea446a4a88e9f3d594fb8b72742f5d4b2a1ee8a03ebf8350c4c3cce45c5819` |
| `data/raw/env39_bezier.json` | `e5dbce6b4d88656c9e0f3bbf6a814434f64b0fbe9b3ff1864ea3fafaf0883602` |

A mismatch causes a nonzero exit status.

## 11. Reproducibility Files

- `environment.yml` is the human-maintained direct dependency declaration used to solve the environment.
- `environment-lock.yml` is the complete resolved environment snapshot, including exact versions and builds. It was generated with Conda's supported environment export using explicit `conda-forge`/`nodefaults` channel override; only the machine-specific `prefix:` line was removed.
- `environment-win-64-explicit.txt` records the exact Windows package artifacts installed in the accepted environment.
- `scripts/check_environment.py` verifies imports, required versions, raw-file parsing, inventories, and canonical hashes.

The lock and explicit export must be regenerated from a successfully verified environment rather than edited to guess package versions.

## 12. Windows Explicit Environment Export

`environment-win-64-explicit.txt` was generated from:

```powershell
conda list -n geogami-morphology --explicit
```

It records 168 exact `win-64`/`noarch` artifact URLs, all from `conda-forge`, and contains no authentication credentials. It is Windows-specific and intended for compatible exact recreation, for example:

```powershell
conda create -n geogami-morphology --file environment-win-64-explicit.txt
```

The portable first choice remains `conda env create -f environment.yml`; the explicit export is the platform-specific artifact snapshot.

## 13. Environment Update Policy

Once Phase 5 is accepted, scientific package upgrades must not be performed casually. OSMnx, GeoPandas, Shapely, NetworkX, NumPy, SciPy, and pyproj must not be automatically upgraded during the study.

If a dependency must change later:

1. Document why the change is required.
2. Intentionally update `environment.yml`.
3. Recreate or re-solve the dedicated environment.
4. Regenerate `environment-lock.yml` and `environment-win-64-explicit.txt`.
5. Rerun `scripts/check_environment.py`.
6. Rerun all relevant analysis tests.
7. Document whether any result changed.

An environment change and a scientific result change must remain traceable to one another.

## 14. Data-Immutability Policy

The canonical files under `data/raw/` are immutable. Environment creation and verification read them but must not rewrite them.

All later cleaning, filtering, curve reconstruction, sampling, snapping, coordinate conversion, topology reconstruction, or anomaly handling must write new outputs under `data/processed/`. The five documented Environment 38 zero-chord source anomalies remain unchanged in the canonical raw data.

## 15. Phase-5 Acceptance Checklist

- [x] Conda `26.5.3` was verified from Miniconda.
- [x] A dedicated `geogami-morphology` environment exists outside base.
- [x] The environment was created from the committed direct-dependency specification.
- [x] Python resolves to `3.12.13`, satisfying the required 3.12 major/minor version.
- [x] OSMnx resolves exactly to `2.1.1`.
- [x] All required packages import successfully.
- [x] All installed Conda packages report the `conda-forge` channel.
- [x] The raw JSON files and manifest parse successfully.
- [x] Environment 38 and Environment 39 inventory smoke checks pass.
- [x] Both canonical raw SHA-256 checks pass.
- [x] The reusable smoke test exits successfully.
- [x] The complete resolved YAML snapshot contains no machine-specific prefix.
- [x] The Windows explicit export contains only `conda-forge` artifact URLs and no credentials.
- [x] Canonical raw inputs remain unchanged.
- [x] No geometry reconstruction or scientific analysis was performed.

## 16. Deferred Phase-6 Work

Phase 6 may begin derived geometry processing only under its own reviewed specification. Deferred work includes Bézier evaluation and sampling, convergence testing, Shapely/GeoPandas object creation, plotting, coordinate/reference decisions, anomaly handling, intersection detection, snapping, topology and graph construction, OSMnx processing, bearings, entropy, orientation order, circuity, connectivity, and final environment comparison.

None of that work is part of Phase 5.
