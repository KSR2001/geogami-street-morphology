# Phase 13 Results Robustness and Interpretation Audit

## 1. Phase 13 Scope

Phase 13 independently audits and explains the frozen Phase 12 results, especially the difference between mean individual-edge and aggregate circuity. It does not alter topology, geometry, snapping, artifact handling, bins, metric definitions, hypotheses, or primary results.

**Phase 13 does not replace the Phase 12 metrics.** It adds decomposition and interpretation only. H4 remains not supported.

## 2. Frozen Phase-12 Results

The Phase 12 primary CSV, edge-circuity CSV, and QA JSON were loaded and checked exactly. Their hashes are recorded in the machine-readable Phase 13 audit.

| Metric | Env38 | Env39 | Env38 − Env39 |
|---|---:|---:|---:|
| `H_o` (nats) | 3.0131094587621066 | 1.5143534129805727 | 1.4987560457815339 |
| `H_w` (nats) | 3.1312256499064475 | 1.381012158514464 | 1.7502134913919836 |
| `phi` | 0.4518145655192265 | 0.9966031867759313 | -0.5447886212567048 |
| Aggregate circuity | 1.0213150770501422 | 1.0233180457073998 | -0.0020029686572576 |
| Median street length | 51.63582671892276 | 58.786673719117275 | -7.150847000194517 |

Relative to Env39, these descriptive differences are +98.97% for `H_o`, +126.73% for `H_w`, -54.66% for `phi`, -0.196% for aggregate circuity, and -12.16% for median street length. They are communication ratios, not inferential effect sizes.

## 3. Aggregate vs Mean Edge Circuity

Mean individual-edge circuity gives every simplified edge equal weight. Env38's value (`1.0183127736327648`) exceeds Env39's (`1.0093689453989059`) because Env38 has more moderately circuitous edges.

Aggregate circuity is different. For edge `i`, with network length `L_i`, straight distance `D_i`, and individual circuity `C_i = L_i/D_i`:

`ΣL_i / ΣD_i = Σ(D_i × C_i) / ΣD_i`.

It is therefore a straight-distance-weighted mean. A small number of long, highly circuitous edges can dominate it even when most edges are straight and the unweighted mean is low.

## 4. Circuity Decomposition

Env38 totals are `ΣL = 5173.197186865085`, `ΣD = 5065.2313895206535`, and excess `Σ(L−D) = 107.96579734443185` Unity world units. Both ratio-of-sums and weighted-mean calculations equal `1.0213150770501422` exactly at recorded precision.

Env39 totals are `ΣL = 5008.303760229`, `ΣD = 4894.181023424499`, and excess `114.12273680450107`. Both calculations equal `1.0233180457073998` exactly. Excess shares sum to one within floating-point tolerance for each environment.

Each edge's additive contribution above aggregate circuity 1 is `(L_i−D_i)/ΣD`. Ranking by this contribution is consequently identical to ranking by excess length; individual-circuity ranking can differ because it ignores edge scale.

## 5. Env38 High-Circuity Streets

Env38's excess distance is distributed across many curved streets. The five largest aggregate contributors account for `0.4839422340890156` (48.39%) of total excess:

| Edge | `L−D` | Excess share | Circuity | Source segments |
|---|---:|---:|---:|---|
| `env38_simplified_edge_00015` | 17.791605110601324 | 0.1647892716787211 | 1.0844611163296942 | 8 fragments from Shape `4330855547829185599` |
| `env38_simplified_edge_00051` | 11.461177540916978 | 0.1061556328283632 | 1.1452781191432633 | 4 fragments from Shape `4330855547524397474` |
| `env38_simplified_edge_00014` | 9.076488789671004 | 0.08406818652684278 | 1.0644377890250223 | 6 fragments from Shape `4330855547529842337` |
| `env38_simplified_edge_00016` | 7.397903127648448 | 0.06852080297288687 | 1.0415673707655906 | 5 fragments from Shape `4330855547524397474` |
| `env38_simplified_edge_00060` | 6.522034603228505 | 0.06040834008220167 | 1.1474463640428711 | 4 fragments from Shape `4330855547529842337` |

Complete Shape, segment, and fragment provenance is retained in `phase13-circuity-contributions.csv` and the Phase 13 QA JSON. The top ten are highlighted without exclusion or geometry alteration in the Env38 audit figure.

Env38 circuity quantiles are: minimum `0.9999999999958674`, q25 `1.0000000000005311`, median `1.002327065680324`, q75 `1.026793477197241`, q90 `1.043765223595224`, q95 `1.063983335320957`, and maximum `1.2432551101540879`. Of 84 edges, 27 (32.14%) are approximately one within `1e-6`; 27 exceed 1.01, 7 exceed 1.05, 3 exceed 1.10, and 1 exceeds 1.20.

## 6. Env39 High-Circuity Streets

Env39's result is concentrated in two L-shaped simplified streets. The top five technically account for approximately 100% of total excess, but the first two alone account for `0.9999805484288416` (99.9981%):

| Edge | `L−D` | Excess share | Circuity | Source segments |
|---|---:|---:|---:|---|
| `env39_simplified_edge_00015` | 78.80829994420435 | 0.6905573959307301 | 1.358318066052315 | Shape `3305298596651482022`, segments 0021 and 0020 |
| `env39_simplified_edge_00017` | 35.312216993760984 | 0.30942315249811153 | 1.2974848598858721 | Shape `3305298596651482022`, segments 0025 and 0017 |
| `env39_simplified_edge_00062` | 0.0008932910521508575 | 0.0000078274590775 | 1.000014780327228 | Shape `3305298596651482022`, segment 0009 |
| `env39_simplified_edge_00007` | 0.000727392838285823 | 0.0000063737766781 | 1.0000043445212128 | Shape `3305298596651482022`, segment 0007 |
| `env39_simplified_edge_00010` | 0.0005991826476474671 | 0.0000052503354233 | 1.000004126566358 | Shape `3305298596651482022`, segment 0022 |

The first two each merge two source fragments of the same Shape through a suppressed degree-2 continuation node. Their retained geometry makes a substantial L-shaped turn between topological endpoints. This is valid Phase 11 simplification, not an artifact or error, and the edges remain included.

Env39 quantiles are: minimum `0.9999999998429255`, q25 `0.999999999999999`, median `1.0`, q75 `1.0000000000000842`, q90 `1.0000000000774825`, q95 `1.0000042464415282`, and maximum `1.358318066052315`. Of 70 edges, 65 (92.86%) are approximately one within `1e-6`; exactly 2 exceed each threshold 1.01, 1.05, 1.10, and 1.20.

## 7. Why H4 Was Not Supported

H4 predicted Env38 aggregate circuity greater than Env39. It remains **not supported** because Env39's two long L-shaped simplified streets create `114.12051693796534` Unity units of its `114.12273680450107` total excess. Their straight-distance weights and high individual ratios raise Env39's aggregate value above Env38's.

Env38 is more broadly curved: it has higher mean and median individual circuity, and its excess is distributed across many edges. Env39 is mostly straight but has two dominant exceptions. Since aggregate circuity is straight-distance weighted, concentration in those two edges outweighs the difference in unweighted means. No definition, edge, or hypothesis is changed to reverse this result.

The descriptive Spearman correlation between straight distance and individual circuity is `0.4345334522193329` in Env38 and `-0.06692183164921803` in Env39. No p-values are calculated. The Env39 coefficient reinforces that its outcome is not a general monotonic length/circuity pattern; it is driven by the two identified exceptions.

## 8. Orientation Robustness

The frozen Phase 12 sensitivity table is summarized without recomputing or selecting a favorable offset. Env38 `H_o` exceeds Env39 at 20/20 offsets, and Env38 `H_w` exceeds Env39 at 20/20.

- Env38 `H_o`: `2.9844556268480833–3.137905505674299`
- Env39 `H_o`: `1.5143534129805727–2.0106200590986782`
- Env38 `H_w`: `3.08632270749412–3.1591970629194774`
- Env39 `H_w`: `1.381012158514464–1.8414407753813764`

The orientation conclusion is robust to every prescribed bin-origin offset.

## 9. Topological Interpretation

Env38 has 60 nodes, 84 streets, 21 dead ends, 9 three-way nodes, and 30 four-way nodes. Env39 has 51 nodes, 70 streets, 19 dead ends, 7 three-way nodes, and 25 four-way nodes.

Their all-node proportions are close: dead ends 35.00% versus 37.25%, three-way nodes 15.00% versus 13.73%, and four-way nodes 50.00% versus 49.02%. Topology therefore provides descriptive structural differences but no dramatic grid-versus-curvy discrimination. No directional topology hypothesis was preregistered or invented afterward.

## 10. Overall Evidence Matrix

| Metric family | Evidence | Result |
|---|---|---|
| Orientation diversity | `H_o`, `H_w`, 20-offset robustness | Strong support |
| Orientation order | `phi` | Strong support |
| Curvature/circuity | Aggregate circuity and individual-edge distribution | Mixed; H4 not supported |
| Topology | Degree, dead-end, three-way, and four-way distributions | Descriptive differences with limited discriminatory power |

## 11. Research Question Answer

The intended distinction is strongly supported in orientation: Env38 has substantially more diverse simplified and detailed directions, whereas Env39 has near-ideal four-direction order. This result is robust across all tested bin origins.

The evidence is not uniformly supportive. Aggregate circuity is slightly higher in Env39 because two long L-shaped simplified streets dominate its excess distance, so H4 is not supported. Topology is broadly similar and offers limited discrimination. Overall, the labels are strongly supported by orientation diversity and order, while curvature/circuity is mixed and topology is descriptive rather than decisive.

## 12. Limitations

This remains a descriptive comparison of two designed environments. Simplified streets are topological paths between retained nodes, so a degree-2 turn can legitimately become one L-shaped edge. Aggregate and unweighted mean circuity answer different questions and should be reported together. Tiny negative excesses on numerically straight edges reflect previously documented representative-junction residuals and are retained without clipping. No inferential effect size, p-value, or generalization to a population is made.

## 13. Final Analysis Status

Phase 13 passes. Phase 12 outputs and definitions remain frozen, raw data and analytical graphs are unchanged, all decomposition identities pass, H4 remains not supported, and no edge is removed. This is the final robustness/interpretation audit; no new analytical phase is started automatically.
