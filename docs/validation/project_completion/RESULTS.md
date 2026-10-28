# Project completion: verified effects

These results demonstrate the comparison workflow and retain gains and adverse outcomes. They are conditional model effects, not calibrated marketplace predictions. Differences are candidate minus the declared reference.

## Matching examples, three paired seeds

Each example loads100 requests and five human vehicles, seeds0/1/2 and execution-noise sigma0.3. Driver coefficients are illustrative. Multiple changed operator parameters are disclosed in `portfolio/policy_parameters.json`; the combined future/re-offer policies do not isolate one causal lever.

| Controller | Candidate | Completed change | Mean served-wait change s | Whole-run empty-km change |
| --- | --- | --- | --- | --- |
| insertion | future_value | -2.000 | -10.755 | -6.083 |
| insertion | ranked_fallback | 25.667 | 31.057 | 33.392 |
| insertion | ranked_future_value | 25.000 | 34.674 | 35.310 |
| immediate_batch | future_value | 0.000 | -10.067 | -3.357 |
| immediate_batch | ranked_fallback | 22.000 | -6.389 | 10.245 |
| alonso_mora | driver_menus | -1.667 | 11.278 | 0.921 |
| alonso_mora | future_reoffer | 22.000 | 24.802 | 26.764 |
| alonso_mora | future_value | -0.667 | -11.898 | -0.607 |

Re-offers increase completion in these examples, often at additional empty-driving cost. Future value alone does not uniformly improve completion. Driver menus also retain unfavorable results. The full [paired effects](portfolio/kpi_movements.csv) include95% intervals, omission counts and46 KPIs; three seeds are not population uncertainty. [Common-served-ID waits](portfolio/common_rider_waits.csv) supplement coverage and served-only means.

## Fresh city allocation bridge, one paired seed

All-human, threshold0 and threshold240 use native city inputs, fixed total fleets50/100/775, actual AV rosters5/10/78, nominal10% replacement,20% placement anchors,30% opt-in,480s offer cutoff and1.25 AV travel-time factor. This fresh seed0 bridge verifies the new reporter/current source; a one-seed contrast has no inferential interval. AV repositioning is off in this bridge.

| City | T240−T0 completed | Served wait s | AV trips | AV utilization pp | Whole-run empty km |
| --- | --- | --- | --- | --- | --- |
| munich | -11.000 | -3.018 | 6.000 | 8.645 | 24.355 |
| chicago | 40.000 | 8.254 | -7.000 | 7.230 | 39.258 |
| manhattan | -4.000 | -0.280 | 48.000 | 7.198 | 5.124 |

Chicago's higher AV occupied use coincides with fewer AV trips in this seed. Munich/Manhattan gain AV trips while losing total completions. Higher AV use is not itself a welfare or service improvement. See [all-human contrasts](portfolio/RESULTS.md) for the cost of AV replacement under these assumptions.

## Historical allocation and repositioning, read-only

The [three-seed AV report](historical_av/RESULTS.md) reanalyzes27 existing Phase16 records. The [repositioning report](historical_repositioning/RESULTS.md) reanalyzes45 existing Phase12 records with threshold240 as reference. Original simulation sources are retained separately from the current285-file reporting source. These72 records were not rerun in this audit.

## Three-seed historical threshold contrast

These27 historical records use the same recorded Phase16 source, held separate from the fresh source. Each total-completion interval spans zero; the mean directions do not establish service improvement.

| City | T240−T0 completed [paired95% interval] | AV trips | Human trips | AV utilization pp | Empty km |
| --- | --- | --- | --- | --- | --- |
| munich | -8.333 [-31.415, 14.748] | 2.333 | -10.667 | 2.990 | 36.419 |
| chicago | -8.333 [-113.208, 96.541] | -1.000 | -7.333 | 10.895 | 39.501 |
| manhattan | -8.000 [-23.110, 7.110] | 50.667 | -58.667 | 6.843 | 11.381 |

## Three-seed historical repositioning contrast

The next table isolates demand repositioning at threshold240 within the historical city study. It does not compare different source versions or assume that additional AV trips offset empty-driving costs.

| City | Reposition-on−off completed | Served wait s | AV trips | AV utilization pp | Whole-run empty km |
| --- | --- | --- | --- | --- | --- |
| munich | -4.333 | 2.970 | -4.667 | -2.632 | 69.527 |
| chicago | 2.333 | 0.095 | 11.000 | 5.216 | 525.436 |
| manhattan | 41.333 | -1.174 | 41.667 | 6.612 | 469.657 |

Matched backgrounds are necessary but do not identify field causality. The [KPI guide](../../KPI_GUIDE.md) explains original request clocks, activity windows, whole-run/tail distance and modeled earnings. The [proposal audit](../../PROPOSAL_AUDIT.md) retains unresolved online-supply, unmet-demand, refusal/adoption and cancellation calibration.
