# Matching policy and AV allocation comparison

Differences are candidate minus reference within matched source/input strata. Units, denominators and time scopes are in `kpi_catalog.json`. No welfare score or automatic best policy is inferred. Rates use percentage-point changes separately from relative percent. Missing/zero-denominator metrics remain unavailable.

## insertion: 1a798d3b59f0f4d2b200

Reference: `acceptance_weighted`. Simulation source: `7cdb1f6cd12b9a1fa0b9c951ed4aa7779d13e61cc65d1b6d37b4eca6c0ed7418`. Input assumptions stay inside this stratum.

| Policy | Seeds | Completed | Served wait s | AV trips | AV occupied % | Empty km |
| --- | --- | --- | --- | --- | --- | --- |
| acceptance_weighted | 3 | 44.667 | 118.608 | 0.000 | — | 45.190 |
| future_value | 3 | 42.667 | 107.852 | 0.000 | — | 39.106 |
| ranked_fallback | 3 | 70.333 | 149.665 | 0.000 | — | 78.582 |
| ranked_future_value | 3 | 69.667 | 153.282 | 0.000 | — | 80.499 |

| Candidate | KPI | Mean change | Conditional paired95% interval | Pairs /omitted |
| --- | --- | --- | --- | --- |
| future_value | completed (requests) | -2.000 | [-23.656, 19.656] | 3 /0 |
| future_value | wait_mean_s (s) | -10.755 | [-17.394, -4.116] | 3 /0 |
| future_value | empty_distance_km (km) | -6.083 | [-29.232, 17.066] | 3 /0 |
| future_value | av_completed (requests) | 0.000 | [0.000, 0.000] | 3 /0 |
| future_value | av_utilization (fraction) | — | [—, —] | 0 /3 |
| ranked_fallback | completed (requests) | 25.667 | [11.541, 39.792] | 3 /0 |
| ranked_fallback | wait_mean_s (s) | 31.057 | [-13.978, 76.092] | 3 /0 |
| ranked_fallback | empty_distance_km (km) | 33.392 | [25.954, 40.830] | 3 /0 |
| ranked_fallback | av_completed (requests) | 0.000 | [0.000, 0.000] | 3 /0 |
| ranked_fallback | av_utilization (fraction) | — | [—, —] | 0 /3 |
| ranked_future_value | completed (requests) | 25.000 | [12.092, 37.908] | 3 /0 |
| ranked_future_value | wait_mean_s (s) | 34.674 | [13.668, 55.680] | 3 /0 |
| ranked_future_value | empty_distance_km (km) | 35.310 | [27.043, 43.576] | 3 /0 |
| ranked_future_value | av_completed (requests) | 0.000 | [0.000, 0.000] | 3 /0 |
| ranked_future_value | av_utilization (fraction) | — | [—, —] | 0 /3 |
## alonso_mora: 4f83c080dcebbbfcbaca

Reference: `acceptance_weighted`. Simulation source: `7cdb1f6cd12b9a1fa0b9c951ed4aa7779d13e61cc65d1b6d37b4eca6c0ed7418`. Input assumptions stay inside this stratum.

| Policy | Seeds | Completed | Served wait s | AV trips | AV occupied % | Empty km |
| --- | --- | --- | --- | --- | --- | --- |
| acceptance_weighted | 3 | 54.667 | 125.024 | 0.000 | — | 56.193 |
| driver_menus | 3 | 53.000 | 136.302 | 0.000 | — | 57.114 |
| future_reoffer | 3 | 76.667 | 149.826 | 0.000 | — | 82.957 |
| future_value | 3 | 54.000 | 113.126 | 0.000 | — | 55.586 |

| Candidate | KPI | Mean change | Conditional paired95% interval | Pairs /omitted |
| --- | --- | --- | --- | --- |
| driver_menus | completed (requests) | -1.667 | [-5.461, 2.128] | 3 /0 |
| driver_menus | wait_mean_s (s) | 11.278 | [-42.529, 65.084] | 3 /0 |
| driver_menus | empty_distance_km (km) | 0.921 | [-16.473, 18.314] | 3 /0 |
| driver_menus | av_completed (requests) | 0.000 | [0.000, 0.000] | 3 /0 |
| driver_menus | av_utilization (fraction) | — | [—, —] | 0 /3 |
| future_reoffer | completed (requests) | 22.000 | [10.616, 33.384] | 3 /0 |
| future_reoffer | wait_mean_s (s) | 24.802 | [-3.363, 52.966] | 3 /0 |
| future_reoffer | empty_distance_km (km) | 26.764 | [8.200, 45.327] | 3 /0 |
| future_reoffer | av_completed (requests) | 0.000 | [0.000, 0.000] | 3 /0 |
| future_reoffer | av_utilization (fraction) | — | [—, —] | 0 /3 |
| future_value | completed (requests) | -0.667 | [-4.461, 3.128] | 3 /0 |
| future_value | wait_mean_s (s) | -11.898 | [-44.045, 20.249] | 3 /0 |
| future_value | empty_distance_km (km) | -0.607 | [-17.602, 16.387] | 3 /0 |
| future_value | av_completed (requests) | 0.000 | [0.000, 0.000] | 3 /0 |
| future_value | av_utilization (fraction) | — | [—, —] | 0 /3 |
## chicago, N100, AV target 10%: 7ddc0f7a635ef3bb8833

Reference: `all_human`. Simulation source: `7cdb1f6cd12b9a1fa0b9c951ed4aa7779d13e61cc65d1b6d37b4eca6c0ed7418`. Input assumptions stay inside this stratum.

| Policy | Seeds | Completed | Served wait s | AV trips | AV occupied % | Empty km |
| --- | --- | --- | --- | --- | --- | --- |
| all_human | 1 | 578.000 | 319.325 | 0.000 | — | 687.413 |
| threshold_0 | 1 | 516.000 | 311.217 | 35.000 | 46.409 | 653.520 |
| threshold_240 | 1 | 556.000 | 319.471 | 28.000 | 53.639 | 692.778 |

| Candidate | KPI | Mean change | Conditional paired95% interval | Pairs /omitted |
| --- | --- | --- | --- | --- |
| threshold_0 | completed (requests) | -62.000 | [—, —] | 1 /0 |
| threshold_0 | wait_mean_s (s) | -8.108 | [—, —] | 1 /0 |
| threshold_0 | empty_distance_km (km) | -33.893 | [—, —] | 1 /0 |
| threshold_0 | av_completed (requests) | 35.000 | [—, —] | 1 /0 |
| threshold_0 | av_utilization (fraction) | — | [—, —] | 0 /1 |
| threshold_240 | completed (requests) | -22.000 | [—, —] | 1 /0 |
| threshold_240 | wait_mean_s (s) | 0.146 | [—, —] | 1 /0 |
| threshold_240 | empty_distance_km (km) | 5.364 | [—, —] | 1 /0 |
| threshold_240 | av_completed (requests) | 28.000 | [—, —] | 1 /0 |
| threshold_240 | av_utilization (fraction) | — | [—, —] | 0 /1 |
## munich, N50, AV target 10%: b18708394be1908584f6

Reference: `all_human`. Simulation source: `7cdb1f6cd12b9a1fa0b9c951ed4aa7779d13e61cc65d1b6d37b4eca6c0ed7418`. Input assumptions stay inside this stratum.

| Policy | Seeds | Completed | Served wait s | AV trips | AV occupied % | Empty km |
| --- | --- | --- | --- | --- | --- | --- |
| all_human | 1 | 590.000 | 325.250 | 0.000 | — | 1052.968 |
| threshold_0 | 1 | 550.000 | 331.106 | 19.000 | 29.247 | 1013.662 |
| threshold_240 | 1 | 539.000 | 328.088 | 25.000 | 37.892 | 1038.016 |

| Candidate | KPI | Mean change | Conditional paired95% interval | Pairs /omitted |
| --- | --- | --- | --- | --- |
| threshold_0 | completed (requests) | -40.000 | [—, —] | 1 /0 |
| threshold_0 | wait_mean_s (s) | 5.856 | [—, —] | 1 /0 |
| threshold_0 | empty_distance_km (km) | -39.306 | [—, —] | 1 /0 |
| threshold_0 | av_completed (requests) | 19.000 | [—, —] | 1 /0 |
| threshold_0 | av_utilization (fraction) | — | [—, —] | 0 /1 |
| threshold_240 | completed (requests) | -51.000 | [—, —] | 1 /0 |
| threshold_240 | wait_mean_s (s) | 2.838 | [—, —] | 1 /0 |
| threshold_240 | empty_distance_km (km) | -14.951 | [—, —] | 1 /0 |
| threshold_240 | av_completed (requests) | 25.000 | [—, —] | 1 /0 |
| threshold_240 | av_utilization (fraction) | — | [—, —] | 0 /1 |
## manhattan, N775, AV target 10%: b315490022c3ea774dba

Reference: `all_human`. Simulation source: `7cdb1f6cd12b9a1fa0b9c951ed4aa7779d13e61cc65d1b6d37b4eca6c0ed7418`. Input assumptions stay inside this stratum.

| Policy | Seeds | Completed | Served wait s | AV trips | AV occupied % | Empty km |
| --- | --- | --- | --- | --- | --- | --- |
| all_human | 1 | 2438.000 | 247.952 | 0.000 | — | 1389.357 |
| threshold_0 | 1 | 2408.000 | 256.155 | 79.000 | 12.041 | 1418.793 |
| threshold_240 | 1 | 2404.000 | 255.875 | 127.000 | 19.239 | 1423.917 |

| Candidate | KPI | Mean change | Conditional paired95% interval | Pairs /omitted |
| --- | --- | --- | --- | --- |
| threshold_0 | completed (requests) | -30.000 | [—, —] | 1 /0 |
| threshold_0 | wait_mean_s (s) | 8.204 | [—, —] | 1 /0 |
| threshold_0 | empty_distance_km (km) | 29.436 | [—, —] | 1 /0 |
| threshold_0 | av_completed (requests) | 79.000 | [—, —] | 1 /0 |
| threshold_0 | av_utilization (fraction) | — | [—, —] | 0 /1 |
| threshold_240 | completed (requests) | -34.000 | [—, —] | 1 /0 |
| threshold_240 | wait_mean_s (s) | 7.923 | [—, —] | 1 /0 |
| threshold_240 | empty_distance_km (km) | 34.561 | [—, —] | 1 /0 |
| threshold_240 | av_completed (requests) | 127.000 | [—, —] | 1 /0 |
| threshold_240 | av_utilization (fraction) | — | [—, —] | 0 /1 |
## immediate_batch: eeaadb3bc7e8348ae255

Reference: `acceptance_weighted`. Simulation source: `7cdb1f6cd12b9a1fa0b9c951ed4aa7779d13e61cc65d1b6d37b4eca6c0ed7418`. Input assumptions stay inside this stratum.

| Policy | Seeds | Completed | Served wait s | AV trips | AV occupied % | Empty km |
| --- | --- | --- | --- | --- | --- | --- |
| acceptance_weighted | 3 | 49.667 | 113.456 | 0.000 | — | 48.307 |
| future_value | 3 | 49.667 | 103.389 | 0.000 | — | 44.949 |
| ranked_fallback | 3 | 71.667 | 107.067 | 0.000 | — | 58.552 |

| Candidate | KPI | Mean change | Conditional paired95% interval | Pairs /omitted |
| --- | --- | --- | --- | --- |
| future_value | completed (requests) | 0.000 | [-21.656, 21.656] | 3 /0 |
| future_value | wait_mean_s (s) | -10.067 | [-33.926, 13.792] | 3 /0 |
| future_value | empty_distance_km (km) | -3.357 | [-33.046, 26.332] | 3 /0 |
| future_value | av_completed (requests) | 0.000 | [0.000, 0.000] | 3 /0 |
| future_value | av_utilization (fraction) | — | [—, —] | 0 /3 |
| ranked_fallback | completed (requests) | 22.000 | [15.428, 28.572] | 3 /0 |
| ranked_fallback | wait_mean_s (s) | -6.389 | [-66.505, 53.727] | 3 /0 |
| ranked_fallback | empty_distance_km (km) | 10.245 | [-24.174, 44.664] | 3 /0 |
| ranked_fallback | av_completed (requests) | 0.000 | [0.000, 0.000] | 3 /0 |
| ranked_fallback | av_utilization (fraction) | — | [—, —] | 0 /3 |

## Interpretation and scope

`kpi_movements.csv` retains every KPI, paired seed interval/status, missing pairs, fraction percentage-point changes and relative changes (unavailable for zero baseline). Three seeds are not population uncertainty. No multiple-testing or policy-superiority claim is made from these exploratory intervals.

Served-only means can change who is served; `common_rider_waits.csv` compares identical request IDs served in both policies. Include completion and unserved counts whenever interpreting waits or promise errors. AV trip share is allocation; utilization can rise with longer journeys. Neither is a welfare score. Driver costs/earnings are model proxies over the full run/tail, not observed wages. Clock-clipped utilization and request-cohort service differ from full-run distance/cost scopes.

City AV assumptions, actual fleet shares/placement anchors, search partitions and source versions remain separate strata in `strata.json`. All-human controls preserve the original declared shadow search groups. No cross-city/year or source-version pooling is performed. Existing windowed, market-calibration and older unsealed AV reports retain their specialized censoring/calibration definitions and are linked in the project guide.

The report is read-only. Raw hashes, physical bookkeeping and named random backgrounds are checked before paired inference. `manifest.json` preserves the reporting source separately from original simulation sources. Historical simulations are never retagged as current-source runs.
