# Matching policy and AV allocation comparison

Differences are candidate minus reference within matched source/input strata. Units, denominators and time scopes are in `kpi_catalog.json`. No welfare score or automatic best policy is inferred. Rates use percentage-point changes separately from relative percent. Missing/zero-denominator metrics remain unavailable.

## munich, N50, AV target 10%: 209135b1081a517bb195

Reference: `threshold_0`. Simulation source: `e3e70ac0eb6d716b90491ece20701abad3afb61da924464a427a5e952a29dc5c`. Input assumptions stay inside this stratum.

| Policy | Seeds | Completed | Served wait s | AV trips | AV occupied % | Empty km |
| --- | --- | --- | --- | --- | --- | --- |
| all_human | 3 | 583.667 | 327.565 | 0.000 | — | 1063.026 |
| threshold_0 | 3 | 556.667 | 325.165 | 22.667 | 35.795 | 1023.460 |
| threshold_240 | 3 | 548.333 | 327.696 | 25.000 | 38.784 | 1059.879 |

| Candidate | KPI | Mean change | Conditional paired95% interval | Pairs /omitted |
| --- | --- | --- | --- | --- |
| all_human | completed (requests) | 27.000 | [-9.594, 63.594] | 3 /0 |
| all_human | wait_mean_s (s) | 2.400 | [-15.578, 20.378] | 3 /0 |
| all_human | empty_distance_km (km) | 39.566 | [-9.988, 89.119] | 3 /0 |
| all_human | av_completed (requests) | -22.667 | [-31.391, -13.943] | 3 /0 |
| all_human | av_utilization (fraction) | — | [—, —] | 0 /3 |
| threshold_240 | completed (requests) | -8.333 | [-31.415, 14.748] | 3 /0 |
| threshold_240 | wait_mean_s (s) | 2.531 | [-13.082, 18.144] | 3 /0 |
| threshold_240 | empty_distance_km (km) | 36.419 | [-8.203, 81.041] | 3 /0 |
| threshold_240 | av_completed (requests) | 2.333 | [-5.652, 10.319] | 3 /0 |
| threshold_240 | av_utilization (fraction) | 0.030 | [-0.105, 0.165] | 3 /0 |
## chicago, N100, AV target 10%: 59fa6b85d593238c42b2

Reference: `threshold_0`. Simulation source: `e3e70ac0eb6d716b90491ece20701abad3afb61da924464a427a5e952a29dc5c`. Input assumptions stay inside this stratum.

| Policy | Seeds | Completed | Served wait s | AV trips | AV occupied % | Empty km |
| --- | --- | --- | --- | --- | --- | --- |
| all_human | 3 | 558.333 | 319.507 | 0.000 | — | 705.509 |
| threshold_0 | 3 | 537.000 | 314.709 | 33.667 | 45.200 | 674.846 |
| threshold_240 | 3 | 528.667 | 319.854 | 32.667 | 56.095 | 714.347 |

| Candidate | KPI | Mean change | Conditional paired95% interval | Pairs /omitted |
| --- | --- | --- | --- | --- |
| all_human | completed (requests) | 21.333 | [-66.295, 108.962] | 3 /0 |
| all_human | wait_mean_s (s) | 4.798 | [-4.081, 13.676] | 3 /0 |
| all_human | empty_distance_km (km) | 30.663 | [-53.292, 114.619] | 3 /0 |
| all_human | av_completed (requests) | -33.667 | [-36.535, -30.798] | 3 /0 |
| all_human | av_utilization (fraction) | — | [—, —] | 0 /3 |
| threshold_240 | completed (requests) | -8.333 | [-113.208, 96.541] | 3 /0 |
| threshold_240 | wait_mean_s (s) | 5.144 | [-8.925, 19.213] | 3 /0 |
| threshold_240 | empty_distance_km (km) | 39.501 | [24.466, 54.537] | 3 /0 |
| threshold_240 | av_completed (requests) | -1.000 | [-15.905, 13.905] | 3 /0 |
| threshold_240 | av_utilization (fraction) | 0.109 | [-0.023, 0.241] | 3 /0 |
## manhattan, N775, AV target 10%: ce8b5be87031d7df858d

Reference: `threshold_0`. Simulation source: `e3e70ac0eb6d716b90491ece20701abad3afb61da924464a427a5e952a29dc5c`. Input assumptions stay inside this stratum.

| Policy | Seeds | Completed | Served wait s | AV trips | AV occupied % | Empty km |
| --- | --- | --- | --- | --- | --- | --- |
| all_human | 3 | 2452.667 | 246.656 | 0.000 | — | 1398.712 |
| threshold_0 | 3 | 2418.667 | 254.143 | 81.667 | 13.369 | 1417.642 |
| threshold_240 | 3 | 2410.667 | 253.899 | 132.333 | 20.212 | 1429.023 |

| Candidate | KPI | Mean change | Conditional paired95% interval | Pairs /omitted |
| --- | --- | --- | --- | --- |
| all_human | completed (requests) | 34.000 | [10.044, 57.956] | 3 /0 |
| all_human | wait_mean_s (s) | -7.487 | [-11.440, -3.534] | 3 /0 |
| all_human | empty_distance_km (km) | -18.930 | [-55.371, 17.511] | 3 /0 |
| all_human | av_completed (requests) | -81.667 | [-97.637, -65.696] | 3 /0 |
| all_human | av_utilization (fraction) | — | [—, —] | 0 /3 |
| threshold_240 | completed (requests) | -8.000 | [-23.110, 7.110] | 3 /0 |
| threshold_240 | wait_mean_s (s) | -0.245 | [-3.261, 2.772] | 3 /0 |
| threshold_240 | empty_distance_km (km) | 11.381 | [-14.617, 37.380] | 3 /0 |
| threshold_240 | av_completed (requests) | 50.667 | [34.696, 66.637] | 3 /0 |
| threshold_240 | av_utilization (fraction) | 0.068 | [0.044, 0.093] | 3 /0 |

## Interpretation and scope

`kpi_movements.csv` retains every KPI, paired seed interval/status, missing pairs, fraction percentage-point changes and relative changes (unavailable for zero baseline). Three seeds are not population uncertainty. No multiple-testing or policy-superiority claim is made from these exploratory intervals.

Served-only means can change who is served; `common_rider_waits.csv` compares identical request IDs served in both policies. Include completion and unserved counts whenever interpreting waits or promise errors. AV trip share is allocation; utilization can rise with longer journeys. Neither is a welfare score. Driver costs/earnings are model proxies over the full run/tail, not observed wages. Clock-clipped utilization and request-cohort service differ from full-run distance/cost scopes.

City AV assumptions, actual fleet shares/placement anchors, search partitions and source versions remain separate strata in `strata.json`. All-human controls preserve the original declared shadow search groups. No cross-city/year or source-version pooling is performed. Existing windowed, market-calibration and older unsealed AV reports retain their specialized censoring/calibration definitions and are linked in the project guide.

The report is read-only. Raw hashes, physical bookkeeping and named random backgrounds are checked before paired inference. `manifest.json` preserves the reporting source separately from original simulation sources. Historical simulations are never retagged as current-source runs.
