# Phase 13: Chicago threshold and speed mechanisms

All **54 physical runs / 54 unique conditions** pass the raw booking, event, capacity, chronology, matched-background and exact occupied-time checks. This report excludes separate replay studies from its independent condition count.

This is a matched benchmark sensitivity, not empirical AV calibration. Each policy changes later fleet availability and retained candidate sets. A same-request comparison across policies does not hold those histories fixed. Absence of a retained AV candidate is not proof that no AV was physically feasible.

## Actual outcomes

| City | Fleet | Policy | Seeds | Completed | AV trips | AV occupied % | Mean AV pickup-to-dropoff s | Fleet empty km |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| chicago | 100 | all_human | 3 | 531.33 | 0.00 | — | — | 680.96 |
| chicago | 100 | equal_speed_0 | 3 | 531.67 | 30.67 | 40.40 | 2031.77 | 674.64 |
| chicago | 100 | equal_speed_120 | 3 | 534.33 | 51.67 | 55.71 | 1676.64 | 707.55 |
| chicago | 100 | equal_speed_240 | 3 | 535.67 | 44.67 | 53.03 | 1756.41 | 725.57 |
| chicago | 100 | equal_speed_480 | 3 | 535.00 | 50.33 | 60.41 | 1822.47 | 720.84 |
| chicago | 100 | threshold_0 | 3 | 536.00 | 23.00 | 36.18 | 1691.82 | 693.07 |
| chicago | 100 | threshold_120 | 3 | 518.33 | 29.33 | 45.45 | 1824.66 | 719.32 |
| chicago | 100 | threshold_240 | 3 | 547.00 | 29.33 | 53.87 | 2010.49 | 727.31 |
| chicago | 100 | threshold_480 | 3 | 538.00 | 31.00 | 55.91 | 2076.58 | 729.31 |
| chicago | 200 | all_human | 3 | 1320.00 | 0.00 | — | — | 1275.26 |
| chicago | 200 | equal_speed_0 | 3 | 1269.00 | 86.00 | 37.18 | 1240.63 | 1242.03 |
| chicago | 200 | equal_speed_120 | 3 | 1247.00 | 91.33 | 47.84 | 1563.18 | 1259.39 |
| chicago | 200 | equal_speed_240 | 3 | 1208.33 | 96.00 | 52.88 | 1706.25 | 1237.43 |
| chicago | 200 | equal_speed_480 | 3 | 1228.00 | 85.33 | 48.71 | 1786.94 | 1265.59 |
| chicago | 200 | threshold_0 | 3 | 1212.00 | 71.33 | 41.05 | 1381.28 | 1214.43 |
| chicago | 200 | threshold_120 | 3 | 1219.33 | 62.67 | 44.23 | 1654.08 | 1255.71 |
| chicago | 200 | threshold_240 | 3 | 1208.67 | 60.67 | 48.79 | 1906.93 | 1218.47 |
| chicago | 200 | threshold_480 | 3 | 1209.00 | 60.33 | 47.59 | 1876.91 | 1272.90 |

## Exact bridge between trips and utilization

Occupied vehicle seconds equal full evaluation-cohort passenger seconds, minus time before/after the evaluation clock, plus warm-up passenger seconds inside the clock, plus logged alighting dwell, minus logged passenger overlap. Every per-run bridge is independently checked against the union of actual passenger-holding intervals and raw vehicle occupancy.

User pickup and dropoff timestamps mark boarding/alighting start. Raw vehicle occupancy retains outgoing passengers until alighting ends. The extra dwell is explicit; it is not mislabeled passenger journey time. Logged overlap includes moving shared occupancy, stationary incoming/outgoing unions and multi-passenger bookings, so it is not solely a pooling effect.

The evaluation passenger-time product is decomposed symmetrically: average duration × count change plus average count × duration change. This allocates the interaction exactly. With zero completions, the duration factor used in that identity is zero by convention; a zero factor is not an observed trip duration.

| Fleet | Candidate minus control | AV count change | Utilization change pp | Count pp | Duration pp | Pre-window pp | Post-window pp | Warm-up pp | Alighting pp | Overlap pp |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 100 | threshold_240 minus equal_speed_240 | -15.33 | +0.845 | -26.463 | +8.664 | +0.000 | +0.229 | +1.747 | -0.306 | +16.973 |
| 100 | threshold_240 minus threshold_0 | +6.33 | +17.689 | +11.258 | +7.715 | +0.000 | -3.897 | +6.461 | +0.093 | -3.939 |
| 200 | threshold_240 minus equal_speed_240 | -35.33 | -4.085 | -29.768 | +7.160 | +0.000 | -0.386 | +0.308 | -0.478 | +19.080 |
| 200 | threshold_240 minus threshold_0 | -10.67 | +7.742 | -7.920 | +17.115 | +0.000 | -1.813 | +3.662 | -0.241 | -3.061 |

The terms sum to the actual utilization change before rounding. All seeds and contrasts remain in `paired_accounting.csv`, including results that contradict the earlier two-seed direction. These accounting identities explain which recorded time quantities changed; they do not identify a causal duration or pooling intervention.

## Request-level feedback and limits

`request_mechanisms.csv` retains every warm-up/evaluation request, final product, actual pickup/dropoff/alighting endpoint, duration, wait, eligibility and last recorded retained-candidate reason. `product_transitions.csv` partitions each paired evaluation cohort into all nine AV/human/unserved transitions and compares wait for the same served IDs. `time_bins.csv` separates arrivals, actual pickups, occupied seconds and decision-event counts; repeated offer events are not unique requests.

Threshold0/120/240/480 and equal/cautious speed are prespecified. Human acceptance, human/AV repositioning and execution noise stay off; opt-in, service area, source cohort, placement/SOC, candidate budgets and total fleet remain fixed within a seed/regime. Fleet100 versus200 is a load sensitivity with different roster/initialization, not an identical-background pair. Three initialization seeds on one provided cohort do not establish population uncertainty or reproduce the screenshot's load regime.
