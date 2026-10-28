# Matching policy and AV allocation comparison

Differences are candidate minus reference within matched source/input strata. Units, denominators and time scopes are in `kpi_catalog.json`. No welfare score or automatic best policy is inferred. Rates use percentage-point changes separately from relative percent. Missing/zero-denominator metrics remain unavailable.

## chicago, N100, AV target 10%: 7ddc0f7a635ef3bb8833

Reference: `threshold_0`. Simulation source: `7cdb1f6cd12b9a1fa0b9c951ed4aa7779d13e61cc65d1b6d37b4eca6c0ed7418`. Input assumptions stay inside this stratum.

| Policy | Seeds | Completed | Served wait s | AV trips | AV occupied % | Empty km |
| --- | --- | --- | --- | --- | --- | --- |
| all_human | 1 | 578.000 | 319.325 | 0.000 | — | 687.413 |
| threshold_0 | 1 | 516.000 | 311.217 | 35.000 | 46.409 | 653.520 |
| threshold_240 | 1 | 556.000 | 319.471 | 28.000 | 53.639 | 692.778 |

| Candidate | KPI | Mean change | Conditional paired95% interval | Pairs /omitted |
| --- | --- | --- | --- | --- |
| all_human | completed (requests) | 62.000 | [—, —] | 1 /0 |
| all_human | wait_mean_s (s) | 8.108 | [—, —] | 1 /0 |
| all_human | empty_distance_km (km) | 33.893 | [—, —] | 1 /0 |
| all_human | av_completed (requests) | -35.000 | [—, —] | 1 /0 |
| all_human | av_utilization (fraction) | — | [—, —] | 0 /1 |
| threshold_240 | completed (requests) | 40.000 | [—, —] | 1 /0 |
| threshold_240 | wait_mean_s (s) | 8.254 | [—, —] | 1 /0 |
| threshold_240 | empty_distance_km (km) | 39.258 | [—, —] | 1 /0 |
| threshold_240 | av_completed (requests) | -7.000 | [—, —] | 1 /0 |
| threshold_240 | av_utilization (fraction) | 0.072 | [—, —] | 1 /0 |
## munich, N50, AV target 10%: b18708394be1908584f6

Reference: `threshold_0`. Simulation source: `7cdb1f6cd12b9a1fa0b9c951ed4aa7779d13e61cc65d1b6d37b4eca6c0ed7418`. Input assumptions stay inside this stratum.

| Policy | Seeds | Completed | Served wait s | AV trips | AV occupied % | Empty km |
| --- | --- | --- | --- | --- | --- | --- |
| all_human | 1 | 590.000 | 325.250 | 0.000 | — | 1052.968 |
| threshold_0 | 1 | 550.000 | 331.106 | 19.000 | 29.247 | 1013.662 |
| threshold_240 | 1 | 539.000 | 328.088 | 25.000 | 37.892 | 1038.016 |

| Candidate | KPI | Mean change | Conditional paired95% interval | Pairs /omitted |
| --- | --- | --- | --- | --- |
| all_human | completed (requests) | 40.000 | [—, —] | 1 /0 |
| all_human | wait_mean_s (s) | -5.856 | [—, —] | 1 /0 |
| all_human | empty_distance_km (km) | 39.306 | [—, —] | 1 /0 |
| all_human | av_completed (requests) | -19.000 | [—, —] | 1 /0 |
| all_human | av_utilization (fraction) | — | [—, —] | 0 /1 |
| threshold_240 | completed (requests) | -11.000 | [—, —] | 1 /0 |
| threshold_240 | wait_mean_s (s) | -3.018 | [—, —] | 1 /0 |
| threshold_240 | empty_distance_km (km) | 24.355 | [—, —] | 1 /0 |
| threshold_240 | av_completed (requests) | 6.000 | [—, —] | 1 /0 |
| threshold_240 | av_utilization (fraction) | 0.086 | [—, —] | 1 /0 |
## manhattan, N775, AV target 10%: b315490022c3ea774dba

Reference: `threshold_0`. Simulation source: `7cdb1f6cd12b9a1fa0b9c951ed4aa7779d13e61cc65d1b6d37b4eca6c0ed7418`. Input assumptions stay inside this stratum.

| Policy | Seeds | Completed | Served wait s | AV trips | AV occupied % | Empty km |
| --- | --- | --- | --- | --- | --- | --- |
| all_human | 1 | 2438.000 | 247.952 | 0.000 | — | 1389.357 |
| threshold_0 | 1 | 2408.000 | 256.155 | 79.000 | 12.041 | 1418.793 |
| threshold_240 | 1 | 2404.000 | 255.875 | 127.000 | 19.239 | 1423.917 |

| Candidate | KPI | Mean change | Conditional paired95% interval | Pairs /omitted |
| --- | --- | --- | --- | --- |
| all_human | completed (requests) | 30.000 | [—, —] | 1 /0 |
| all_human | wait_mean_s (s) | -8.204 | [—, —] | 1 /0 |
| all_human | empty_distance_km (km) | -29.436 | [—, —] | 1 /0 |
| all_human | av_completed (requests) | -79.000 | [—, —] | 1 /0 |
| all_human | av_utilization (fraction) | — | [—, —] | 0 /1 |
| threshold_240 | completed (requests) | -4.000 | [—, —] | 1 /0 |
| threshold_240 | wait_mean_s (s) | -0.280 | [—, —] | 1 /0 |
| threshold_240 | empty_distance_km (km) | 5.124 | [—, —] | 1 /0 |
| threshold_240 | av_completed (requests) | 48.000 | [—, —] | 1 /0 |
| threshold_240 | av_utilization (fraction) | 0.072 | [—, —] | 1 /0 |

## Interpretation and scope

`kpi_movements.csv` retains every KPI, paired seed interval/status, missing pairs, fraction percentage-point changes and relative changes (unavailable for zero baseline). Three seeds are not population uncertainty. No multiple-testing or policy-superiority claim is made from these exploratory intervals.

Served-only means can change who is served; `common_rider_waits.csv` compares identical request IDs served in both policies. Include completion and unserved counts whenever interpreting waits or promise errors. AV trip share is allocation; utilization can rise with longer journeys. Neither is a welfare score. Driver costs/earnings are model proxies over the full run/tail, not observed wages. Clock-clipped utilization and request-cohort service differ from full-run distance/cost scopes.

City AV assumptions, actual fleet shares/placement anchors, search partitions and source versions remain separate strata in `strata.json`. All-human controls preserve the original declared shadow search groups. No cross-city/year or source-version pooling is performed. Existing windowed, market-calibration and older unsealed AV reports retain their specialized censoring/calibration definitions and are linked in the project guide.

The report is read-only. Raw hashes, physical bookkeeping and named random backgrounds are checked before paired inference. `manifest.json` preserves the reporting source separately from original simulation sources. Historical simulations are never retagged as current-source runs.
