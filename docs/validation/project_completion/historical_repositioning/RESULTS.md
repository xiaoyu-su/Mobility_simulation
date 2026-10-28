# Matching policy and AV allocation comparison

Differences are candidate minus reference within matched source/input strata. Units, denominators and time scopes are in `kpi_catalog.json`. No welfare score or automatic best policy is inferred. Rates use percentage-point changes separately from relative percent. Missing/zero-denominator metrics remain unavailable.

## chicago, N100, AV target 10%: 15256689e8936ad3b086

Reference: `threshold_240`. Simulation source: `649db5e784a7838c98a31d23e21048be09fa4697e2fd5931b25d5897df110a28`. Input assumptions stay inside this stratum.

| Policy | Seeds | Completed | Served wait s | AV trips | AV occupied % | Empty km |
| --- | --- | --- | --- | --- | --- | --- |
| all_human | 3 | 531.333 | 322.478 | 0.000 | — | 680.964 |
| threshold_0 | 3 | 536.000 | 317.824 | 23.000 | 36.182 | 693.069 |
| threshold_0_repo | 3 | 549.333 | 312.290 | 47.667 | 58.060 | 1132.900 |
| threshold_240 | 3 | 547.000 | 319.120 | 29.333 | 53.872 | 727.313 |
| threshold_240_repo | 3 | 549.333 | 319.215 | 40.333 | 59.088 | 1252.749 |

| Candidate | KPI | Mean change | Conditional paired95% interval | Pairs /omitted |
| --- | --- | --- | --- | --- |
| all_human | completed (requests) | -15.667 | [-37.084, 5.751] | 3 /0 |
| all_human | wait_mean_s (s) | 3.359 | [-1.484, 8.201] | 3 /0 |
| all_human | empty_distance_km (km) | -46.349 | [-116.376, 23.679] | 3 /0 |
| all_human | av_completed (requests) | -29.333 | [-38.738, -19.929] | 3 /0 |
| all_human | av_utilization (fraction) | — | [—, —] | 0 /3 |
| threshold_0 | completed (requests) | -11.000 | [-42.715, 20.715] | 3 /0 |
| threshold_0 | wait_mean_s (s) | -1.296 | [-16.151, 13.559] | 3 /0 |
| threshold_0 | empty_distance_km (km) | -34.244 | [-94.530, 26.043] | 3 /0 |
| threshold_0 | av_completed (requests) | -6.333 | [-20.459, 7.792] | 3 /0 |
| threshold_0 | av_utilization (fraction) | -0.177 | [-0.365, 0.011] | 3 /0 |
| threshold_0_repo | completed (requests) | 2.333 | [-50.030, 54.697] | 3 /0 |
| threshold_0_repo | wait_mean_s (s) | -6.830 | [-21.282, 7.623] | 3 /0 |
| threshold_0_repo | empty_distance_km (km) | 405.587 | [276.688, 534.485] | 3 /0 |
| threshold_0_repo | av_completed (requests) | 18.333 | [12.082, 24.585] | 3 /0 |
| threshold_0_repo | av_utilization (fraction) | 0.042 | [-0.086, 0.170] | 3 /0 |
| threshold_240_repo | completed (requests) | 2.333 | [-61.501, 66.168] | 3 /0 |
| threshold_240_repo | wait_mean_s (s) | 0.095 | [-5.293, 5.484] | 3 /0 |
| threshold_240_repo | empty_distance_km (km) | 525.436 | [492.458, 558.414] | 3 /0 |
| threshold_240_repo | av_completed (requests) | 11.000 | [-5.290, 27.290] | 3 /0 |
| threshold_240_repo | av_utilization (fraction) | 0.052 | [-0.098, 0.202] | 3 /0 |
## manhattan, N775, AV target 10%: 94d10acd816bd6a9ab1d

Reference: `threshold_240`. Simulation source: `649db5e784a7838c98a31d23e21048be09fa4697e2fd5931b25d5897df110a28`. Input assumptions stay inside this stratum.

| Policy | Seeds | Completed | Served wait s | AV trips | AV occupied % | Empty km |
| --- | --- | --- | --- | --- | --- | --- |
| all_human | 3 | 2474.333 | 246.465 | 0.000 | — | 1396.867 |
| threshold_0 | 3 | 2436.000 | 253.190 | 83.333 | 13.286 | 1418.575 |
| threshold_0_repo | 3 | 2460.333 | 252.963 | 102.667 | 16.554 | 1777.428 |
| threshold_240 | 3 | 2441.000 | 254.186 | 134.000 | 20.402 | 1438.850 |
| threshold_240_repo | 3 | 2482.333 | 253.013 | 175.667 | 27.013 | 1908.507 |

| Candidate | KPI | Mean change | Conditional paired95% interval | Pairs /omitted |
| --- | --- | --- | --- | --- |
| all_human | completed (requests) | 33.333 | [17.171, 49.496] | 3 /0 |
| all_human | wait_mean_s (s) | -7.722 | [-11.545, -3.898] | 3 /0 |
| all_human | empty_distance_km (km) | -41.983 | [-77.720, -6.247] | 3 /0 |
| all_human | av_completed (requests) | -134.000 | [-140.572, -127.428] | 3 /0 |
| all_human | av_utilization (fraction) | — | [—, —] | 0 /3 |
| threshold_0 | completed (requests) | -5.000 | [-22.913, 12.913] | 3 /0 |
| threshold_0 | wait_mean_s (s) | -0.996 | [-4.001, 2.008] | 3 /0 |
| threshold_0 | empty_distance_km (km) | -20.275 | [-46.263, 5.713] | 3 /0 |
| threshold_0 | av_completed (requests) | -50.667 | [-63.414, -37.919] | 3 /0 |
| threshold_0 | av_utilization (fraction) | -0.071 | [-0.103, -0.040] | 3 /0 |
| threshold_0_repo | completed (requests) | 19.333 | [-6.995, 45.662] | 3 /0 |
| threshold_0_repo | wait_mean_s (s) | -1.224 | [-3.683, 1.235] | 3 /0 |
| threshold_0_repo | empty_distance_km (km) | 338.578 | [281.592, 395.565] | 3 /0 |
| threshold_0_repo | av_completed (requests) | -31.333 | [-42.535, -20.132] | 3 /0 |
| threshold_0_repo | av_utilization (fraction) | -0.038 | [-0.062, -0.015] | 3 /0 |
| threshold_240_repo | completed (requests) | 41.333 | [24.424, 58.243] | 3 /0 |
| threshold_240_repo | wait_mean_s (s) | -1.174 | [-5.263, 2.915] | 3 /0 |
| threshold_240_repo | empty_distance_km (km) | 469.657 | [462.342, 476.972] | 3 /0 |
| threshold_240_repo | av_completed (requests) | 41.667 | [33.681, 49.652] | 3 /0 |
| threshold_240_repo | av_utilization (fraction) | 0.066 | [0.044, 0.088] | 3 /0 |
## munich, N50, AV target 10%: ca3826c8f959e42ae345

Reference: `threshold_240`. Simulation source: `649db5e784a7838c98a31d23e21048be09fa4697e2fd5931b25d5897df110a28`. Input assumptions stay inside this stratum.

| Policy | Seeds | Completed | Served wait s | AV trips | AV occupied % | Empty km |
| --- | --- | --- | --- | --- | --- | --- |
| all_human | 3 | 587.333 | 325.458 | 0.000 | — | 1074.737 |
| threshold_0 | 3 | 557.000 | 325.704 | 23.333 | 36.882 | 1025.298 |
| threshold_0_repo | 3 | 540.000 | 327.709 | 22.333 | 37.450 | 1118.633 |
| threshold_240 | 3 | 556.000 | 325.130 | 25.667 | 39.528 | 1033.371 |
| threshold_240_repo | 3 | 551.667 | 328.100 | 21.000 | 36.896 | 1102.899 |

| Candidate | KPI | Mean change | Conditional paired95% interval | Pairs /omitted |
| --- | --- | --- | --- | --- |
| all_human | completed (requests) | 31.333 | [-0.705, 63.371] | 3 /0 |
| all_human | wait_mean_s (s) | 0.328 | [-30.917, 31.573] | 3 /0 |
| all_human | empty_distance_km (km) | 41.366 | [-132.142, 214.874] | 3 /0 |
| all_human | av_completed (requests) | -25.667 | [-31.404, -19.930] | 3 /0 |
| all_human | av_utilization (fraction) | — | [—, —] | 0 /3 |
| threshold_0 | completed (requests) | 1.000 | [-63.731, 65.731] | 3 /0 |
| threshold_0 | wait_mean_s (s) | 0.573 | [-12.699, 13.846] | 3 /0 |
| threshold_0 | empty_distance_km (km) | -8.073 | [-77.357, 61.211] | 3 /0 |
| threshold_0 | av_completed (requests) | -2.333 | [-14.837, 10.170] | 3 /0 |
| threshold_0 | av_utilization (fraction) | -0.026 | [-0.176, 0.124] | 3 /0 |
| threshold_0_repo | completed (requests) | -16.000 | [-62.408, 30.408] | 3 /0 |
| threshold_0_repo | wait_mean_s (s) | 2.579 | [-5.599, 10.757] | 3 /0 |
| threshold_0_repo | empty_distance_km (km) | 85.262 | [-3.677, 174.202] | 3 /0 |
| threshold_0_repo | av_completed (requests) | -3.333 | [-17.015, 10.348] | 3 /0 |
| threshold_0_repo | av_utilization (fraction) | -0.021 | [-0.092, 0.050] | 3 /0 |
| threshold_240_repo | completed (requests) | -4.333 | [-31.583, 22.917] | 3 /0 |
| threshold_240_repo | wait_mean_s (s) | 2.970 | [-11.130, 17.070] | 3 /0 |
| threshold_240_repo | empty_distance_km (km) | 69.527 | [-32.350, 171.405] | 3 /0 |
| threshold_240_repo | av_completed (requests) | -4.667 | [-10.404, 1.070] | 3 /0 |
| threshold_240_repo | av_utilization (fraction) | -0.026 | [-0.069, 0.016] | 3 /0 |

## Interpretation and scope

`kpi_movements.csv` retains every KPI, paired seed interval/status, missing pairs, fraction percentage-point changes and relative changes (unavailable for zero baseline). Three seeds are not population uncertainty. No multiple-testing or policy-superiority claim is made from these exploratory intervals.

Served-only means can change who is served; `common_rider_waits.csv` compares identical request IDs served in both policies. Include completion and unserved counts whenever interpreting waits or promise errors. AV trip share is allocation; utilization can rise with longer journeys. Neither is a welfare score. Driver costs/earnings are model proxies over the full run/tail, not observed wages. Clock-clipped utilization and request-cohort service differ from full-run distance/cost scopes.

City AV assumptions, actual fleet shares/placement anchors, search partitions and source versions remain separate strata in `strata.json`. All-human controls preserve the original declared shadow search groups. No cross-city/year or source-version pooling is performed. Existing windowed, market-calibration and older unsealed AV reports retain their specialized censoring/calibration definitions and are linked in the project guide.

The report is read-only. Raw hashes, physical bookkeeping and named random backgrounds are checked before paired inference. `manifest.json` preserves the reporting source separately from original simulation sources. Historical simulations are never retagged as current-source runs.
