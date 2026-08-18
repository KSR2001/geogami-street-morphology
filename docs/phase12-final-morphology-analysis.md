# Phase 12 Final Morphology Analysis

## 1. Phase 12 Scope

Phase 12 calculates the pre-specified final descriptive street-network indicators for GeoGami Environments 38 and 39. It uses the Phase 11 artifact-excluded analytical graphs and concludes **PHASE 12 PASS**. No inferential statistical test is performed.

## 2. Research Question

The analysis asks to what extent Env38 and Env39 differ quantitatively in street-network orientation, curvature, and topology, and whether those measures support their intended classifications as curvilinear/curvy and grid-like respectively.

The two environments are designed cases, not random replicates from a population. Results therefore describe these environments and do not estimate population effects.

## 3. Pre-Specified Expectations

Before final calculation, Env38 was expected to have higher unweighted orientation entropy `H_o`, higher detailed length-weighted entropy `H_w`, lower orientation order `phi`, and higher aggregate circuity than Env39. Topology indicators had no pre-registered directional hypothesis.

These expectations were not changed after observing the results.

## 4. Analytical Graph Inputs

The authoritative simplified undirected analytical graphs contain 60 nodes/84 edges for Env38 and 51 nodes/70 edges for Env39. Detailed analytical graphs contain 147 nodes/171 edges and 53 nodes/72 edges respectively. Each graph has one component and no self-loop. All 48 Phase 9 validated junctions remain represented.

GraphML hashes were checked against all four analytical manifests, and the Phase 11 round-trip status was verified before calculation. Canonical raw hashes also pass.

## 5. Coordinate and Orientation Convention

Coordinates remain unmodified Unity world X/Y. For `dx = x2-x1` and `dy = y2-y1`, local planar bearing is:

`degrees(atan2(dx, dy)) mod 360`.

Thus 0 degrees is +Unity Y, 90 is +Unity X, 180 is -Unity Y, and 270 is -Unity X. These are **Unity-frame planar orientations**. No geographic north is claimed. The identical convention is used for both environments.

## 6. Why Geographic OSMnx Bearings Are Not Used

The graphs have no CRS, latitude/longitude, verified metre conversion, or verified geographic north. OSMnx geographic bearing, great-circle length, intersection-consolidation, and automatic simplification functions are therefore not used. No CRS is invented to satisfy those APIs.

## 7. Unweighted Orientation Entropy H_o

`H_o` uses the analytical simplified undirected graph. Each simplified edge contributes its endpoint-chord Unity-frame bearing and reciprocal bearing with equal weight. Mid-edge curvature does not affect this measure.

Env38 has `H_o = 3.0131094587621066` nats; Env39 has `1.5143534129805727` nats. The Env38-minus-Env39 difference is `1.498756045781534` nats. Env38 therefore has a substantially broader simplified street-orientation distribution.

## 8. Detailed Length-Weighted Orientation Entropy H_w

`H_w` explodes every analytical detailed geometry into consecutive straight polyline pieces. Every piece contributes its bearing and reciprocal, each weighted by that piece's own Unity-unit length. It does not reduce a curved detailed edge to one endpoint chord.

Env38 has `H_w = 3.1312256499064475` nats; Env39 has `1.381012158514464` nats. The difference is `1.7502134913919834` nats. Independent calculation from the concatenated simplified geometry gives exactly the same values, confirming representation invariance.

## 9. Orientation Binning

Both entropy measures use 36 bins, 10 degrees wide, with canonical centres at 0, 10, ..., 350 degrees and edges offset by -5 degrees. Wrap-around at 0/360 is circular. Shannon entropy uses natural logarithms and is reported in nats. Full canonical tables are saved separately for each environment.

## 10. Bin-Origin Sensitivity

The bin-centre origin was evaluated at 20 pre-specified offsets from 0.0 through 9.5 degrees in 0.5-degree increments. Canonical zero-offset values remain primary.

Across offsets, Env38 `H_o` ranges `2.9844556268480833–3.137905505674299` with mean `3.0551313140725447`; Env39 ranges `1.5143534129805727–2.0106200590986782` with mean `1.5871885449125593`. Env38 is higher at 20/20 offsets.

Env38 `H_w` ranges `3.08632270749412–3.1591970629194774` with mean `3.128948517370688`; Env39 ranges `1.381012158514464–1.8414407753813764` with mean `1.4519280263033374`. Env38 is again higher at 20/20 offsets. The qualitative entropy comparison is therefore robust to the prescribed bin-origin variation.

## 11. Orientation-Order phi

Orientation order is calculated only from canonical `H_o`:

`phi = 1 - ((H_o - ln(4)) / (ln(36) - ln(4)))^2`.

Env38 has `phi = 0.4518145655192265`; Env39 has `0.9966031867759313`. The Env38-minus-Env39 difference is `-0.5447886212567048`. Env39 is consequently very close to the idealized four-direction ordering reference.

## 12. Street-Segment Length

Lengths use full analytical simplified-edge geometries and remain in Unity world units.

Env38 has 84 segments totaling `5173.197186865086`, with mean `61.58568079601293` and median `51.63582671892276`. Env39 has 70 segments totaling `5008.303760229`, with mean `71.5471965747` and median `58.786673719117275`.

No general minimum-length filter is applied. The smallest retained analytical lengths are `0.01877981148047633` in Env38 and `0.0573219415371643` in Env39.

## 13. Topological Indicators

NetworkX degree was verified to equal incident-street count because the simplified analytical graphs contain neither self-loops nor parallel edges. All canonical proportions use every analytical simplified node as denominator.

Env38 has average degree `2.8`, 21 dead ends (`0.35`), no degree-2 nodes, 9 three-way nodes (`0.15`), 30 four-way nodes (`0.5`), and no node of degree 5 or greater. Its complete distribution is degree 1: 21, degree 3: 9, degree 4: 30.

Env39 has average degree `2.7450980392156863`, 19 dead ends (`0.37254901960784315`), no degree-2 nodes, 7 three-way nodes (`0.13725490196078433`), 25 four-way nodes (`0.49019607843137253`), and no node of degree 5 or greater. Its distribution is degree 1: 19, degree 3: 7, degree 4: 25.

The topology proportions are broadly similar; they are supporting descriptions, not failed or supported directional hypotheses.

## 14. Circuity

For each simplified edge, individual circuity is full polyline length divided by the Euclidean distance between its retained topology nodes. Primary aggregate circuity is the sum of all network lengths divided by the sum of all straight distances. Circuity is dimensionless.

Env38 aggregate circuity is `1.0213150770501422`; Env39 is `1.0233180457073998`. The difference is `-0.0020029686572576`, opposite the pre-specified expectation.

Env38 individual-edge circuity has mean `1.0183127736327648`, median `1.002327065680324`, standard deviation `0.03709214380000908`, minimum `0.9999999999958674`, maximum `1.2432551101540879`, q25 `1.0000000000005311`, q75 `1.026793477197241`, q90 `1.043765223595224`, and q95 `1.063983335320957`.

Env39 has mean `1.0093689453989059`, median `1.0`, standard deviation `0.054869283486562385`, minimum `0.9999999998429255`, maximum `1.358318066052315`, q25 `0.999999999999999`, q75 `1.0000000000000842`, q90 `1.0000000000774825`, and q95 `1.0000042464415282`.

Eleven Env38 and 27 Env39 raw ratios are fractionally below one within a documented `1e-9` ratio tolerance. This comes from Phase 8 representative crossing coordinates differing microscopically from preserved analytic curve endpoints; the worst path-minus-chord residual is `-5.9559894793892454e-9` Unity units. Values are retained without clipping, and no coordinate is changed.

## 15. Environment 38 Results

Env38 exhibits high orientation dispersion in both simplified chords and length-weighted detailed geometry, with moderate orientation order. Its curved map appearance is strongly expressed by orientation diversity. It contains 60 nodes and 84 street segments, one component, and topology dominated by four-way nodes plus 21 dead ends. Aggregate circuity is close to one and is not higher than Env39's.

## 16. Environment 39 Results

Env39's entropy is concentrated around two reciprocal axial families, producing low `H_o`, low `H_w`, and `phi` near one. This strongly quantifies its grid-like directional order. It contains 51 nodes and 70 street segments, one component, and a topology distribution similar to Env38's. Two unusually circuitous edges make its aggregate circuity slightly higher despite a median individual circuity of exactly one.

## 17. Direct Env38-vs-Env39 Comparison

The main separation is directional: Env38 entropy exceeds Env39 by about 1.50–1.75 nats, while Env39 orientation order exceeds Env38 by about 0.545. Env38 has 9 more nodes, 14 more segments, and slightly greater total road length, but shorter mean and median simplified segments. Topological proportions differ only modestly.

Circuity is nuanced. Env38 has higher mean and median individual-edge circuity, but the pre-specified aggregate ratio is slightly lower because aggregate circuity weights the summed network and chord lengths rather than averaging edge ratios.

## 18. Hypothesis Assessment

- H1, Env38 `H_o >` Env39 `H_o`: **supported**.
- H2, Env38 `H_w >` Env39 `H_w`: **supported**.
- H3, Env38 `phi <` Env39 `phi`: **supported**.
- H4, Env38 aggregate circuity `>` Env39 aggregate circuity: **not supported**.

No hypothesis is redefined, and topology indicators are not retroactively treated as directional hypotheses.

## 19. Interpretation of Curvilinear vs Grid-Like Classification

The quantitative results strongly support the intended distinction in orientation structure: Env38 is much more directionally diverse, and Env39 is highly ordered along grid axes. This conclusion is insensitive to all prescribed bin origins and appears in both chord-based and detailed length-weighted orientation.

Support is not uniform across every indicator. The aggregate circuity result is slightly reversed, so it does not validate the expectation that Env38 would be more circuitous by that specific network-level formula. Overall, three of four pre-registered expectations support the classifications; the labels are strongly supported by orientation but not by aggregate circuity. This is a descriptive conclusion about these two designed environments.

## 20. Zero-Chord Artifact Policy

The five pre-registered Env38 zero-chord anomalies remain in the Phase 11 provenance graph and are excluded only from analytical graphs. They do not enter any Phase 12 metric. No additional edge is removed based on length or appearance.

## 21. Snapping Policy

Canonical snapping remains exactly zero Unity world units. Phase 12 uses the unmodified selected Phase 10 topology and does not introduce any proximity merge or coordinate adjustment.

## 22. Limitations

There are only two designed environments, so no inferential generalization is made. Street semantics, geographic north, real-world distance scale, traffic direction, and CRS remain unavailable. Orientation depends on the declared Unity frame, although the relative entropy conclusion is robust to the specified bin-origin offsets. Aggregate circuity can be influenced by a small number of long or highly circuitous segments and should be read alongside its individual-edge distribution.

## 23. Reproducibility

Run:

```powershell
conda run -n geogami-morphology pytest
conda run -n geogami-morphology python scripts/analyze_final_morphology.py
```

The script verifies raw hashes, graph manifests and GraphML hashes, Phase 11 round trips, graph counts, connectivity, crossing retention, artifact absence, and canonical zero snapping before generating tables, figures, and `outputs/qa/phase12-final-morphology-results.json`.

Independent cross-checks reproduce entropy directly from probabilities, lengths from geometry, aggregate circuity from output columns, topology from manual degree aggregation, `phi` from its formula, and `H_w` from both detailed and simplified geometry. All errors are zero at recorded precision, except the separately documented benign circuity coordinate residual.

## 24. Phase-12 Acceptance Checklist

- [x] Raw hashes and Phase 11 analytical manifests verified.
- [x] Graph counts, one component each, and all 48 validated crossings verified.
- [x] Five registered artifacts excluded and no short-edge threshold used.
- [x] Canonical snapping remains zero.
- [x] `H_o` uses simplified edge chords and reciprocal observations.
- [x] `H_w` uses detailed polyline pieces and individual piece-length weights.
- [x] Identical canonical 36-bin policy used for both environments.
- [x] `H_w` representation invariance and bin-origin sensitivity pass.
- [x] `phi` derives from canonical `H_o`.
- [x] Aggregate circuity uses summed geometry lengths and planar chord distances.
- [x] Topology uses the simplified analytical undirected graphs.
- [x] All independent numerical cross-checks pass.
- [x] No CRS, geographic north, latitude/longitude, or metre scale is inferred.
- [x] No inferential statistical test is performed.
- [x] Final tables, figures, QA JSON, and documentation are reproducible.
