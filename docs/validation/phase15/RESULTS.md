# Phase 15: rider opt-in robustness

**81 unique conditions**; every accepted booking physically completes. Repetitions are separate replay records.

| City | Fleet | Opt-in % | Policy | Seeds | Completed | AV trips | AV occupied % | Eligible served wait s | Fixed 480s service | Late actual pickups | Empty km |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| chicago | 100 | 0 | all_human | 3 | 531.33 | 0.00 | — | — | 527.67 | 3.67 | 680.96 |
| chicago | 100 | 0 | threshold_0 | 3 | 507.00 | 0.00 | 0.00 | — | 504.33 | 2.67 | 646.46 |
| chicago | 100 | 0 | threshold_240 | 3 | 507.00 | 0.00 | 0.00 | — | 504.33 | 2.67 | 646.46 |
| chicago | 100 | 30 | all_human | 3 | 531.33 | 0.00 | — | 316.74 | 527.67 | 3.67 | 680.96 |
| chicago | 100 | 30 | threshold_0 | 3 | 536.00 | 23.00 | 36.18 | 304.99 | 532.33 | 3.67 | 693.07 |
| chicago | 100 | 30 | threshold_240 | 3 | 547.00 | 29.33 | 53.87 | 311.52 | 543.67 | 3.33 | 727.31 |
| chicago | 100 | 100 | all_human | 3 | 531.33 | 0.00 | — | 325.27 | 527.67 | 3.67 | 680.96 |
| chicago | 100 | 100 | threshold_0 | 3 | 512.00 | 46.67 | 63.72 | 315.15 | 509.33 | 2.67 | 679.61 |
| chicago | 100 | 100 | threshold_240 | 3 | 537.67 | 51.00 | 72.59 | 313.91 | 533.67 | 4.00 | 708.77 |
| manhattan | 775 | 0 | all_human | 3 | 2474.33 | 0.00 | — | — | 2459.33 | 15.00 | 1396.87 |
| manhattan | 775 | 0 | threshold_0 | 3 | 2398.67 | 0.00 | 0.00 | — | 2379.67 | 19.00 | 1419.32 |
| manhattan | 775 | 0 | threshold_240 | 3 | 2398.67 | 0.00 | 0.00 | — | 2379.67 | 19.00 | 1419.32 |
| manhattan | 775 | 30 | all_human | 3 | 2474.33 | 0.00 | — | 227.08 | 2459.33 | 15.00 | 1396.87 |
| manhattan | 775 | 30 | threshold_0 | 3 | 2436.00 | 83.33 | 13.29 | 198.13 | 2417.00 | 19.00 | 1418.57 |
| manhattan | 775 | 30 | threshold_240 | 3 | 2441.00 | 134.00 | 20.40 | 257.34 | 2423.33 | 17.67 | 1438.85 |
| manhattan | 775 | 100 | all_human | 3 | 2474.33 | 0.00 | — | 227.30 | 2459.33 | 15.00 | 1396.87 |
| manhattan | 775 | 100 | threshold_0 | 3 | 2443.00 | 150.67 | 22.83 | 222.06 | 2426.67 | 16.33 | 1389.80 |
| manhattan | 775 | 100 | threshold_240 | 3 | 2464.33 | 250.67 | 34.90 | 258.30 | 2448.67 | 15.67 | 1461.68 |
| munich | 50 | 0 | all_human | 3 | 587.33 | 0.00 | — | — | 586.00 | 1.33 | 1074.74 |
| munich | 50 | 0 | threshold_0 | 3 | 536.67 | 0.00 | 0.00 | — | 535.33 | 1.33 | 965.97 |
| munich | 50 | 0 | threshold_240 | 3 | 536.67 | 0.00 | 0.00 | — | 535.33 | 1.33 | 965.97 |
| munich | 50 | 30 | all_human | 3 | 587.33 | 0.00 | — | 329.82 | 586.00 | 1.33 | 1074.74 |
| munich | 50 | 30 | threshold_0 | 3 | 557.00 | 23.33 | 36.88 | 303.54 | 554.33 | 2.67 | 1025.30 |
| munich | 50 | 30 | threshold_240 | 3 | 556.00 | 25.67 | 39.53 | 302.44 | 554.67 | 1.33 | 1033.37 |
| munich | 50 | 100 | all_human | 3 | 587.33 | 0.00 | — | 325.92 | 586.00 | 1.33 | 1074.74 |
| munich | 50 | 100 | threshold_0 | 3 | 553.33 | 35.67 | 54.42 | 310.28 | 551.33 | 2.00 | 1040.40 |
| munich | 50 | 100 | threshold_240 | 3 | 564.33 | 37.33 | 55.85 | 313.94 | 563.33 | 1.00 | 1054.27 |

## Definitions and interpretation

Only the opt-in parameter changes across strata. A CRC32 request/operator draw fixed across seeds creates nested eligible sets. Zero opt-in keeps the AV replacement vehicles in the roster but makes them ineligible for passenger service; this is distinct from the all-human control. At full opt-in, both endpoints must still be inside the unchanged fence. This per-request flag is not a persistent person-level willingness or a dynamic offer-choice model.

`fixed_group_results.csv` partitions the same evaluation requests into baseline_eligible (inside fence and opted in at 30%), additional_opt_in (inside fence and outside that baseline draw), and outside_fence. These labels remain fixed even at zero opt-in. Their completion denominators are fixed. The ordinary eligible served wait changes membership across opt-in and must not be interpreted as a same-rider effect. `common_rider_effects.csv` retains only identical IDs served in both compared conditions, by fixed group; it does not represent rejected riders.

`paired_effects.csv` separates policy contrasts within fixed opt-in from opt-in contrasts at fixed policy against 30%. `fixed_group_effects.csv` reports both on fixed groups. Missing wait means and AV rates with zero denominators remain missing; paired statistics record omitted pairs rather than replacing them with zero. All-human physical outputs must be invariant across opt-in; its reported eligible-group means can change membership. No policy is selected after observing results.

Trips/waits use evaluation request IDs and later fulfillment; AV occupied utilization clips physical passenger occupancy to the evaluation clock. Empty distance includes warm-up and the fulfillment tail. Promises must meet the original request-clock 480s cutoff. Actual late pickups remain counted, and accepted riders are completed. Human/AV repositioning, driver acceptance and execution noise stay off; cautious AV travel factor1.25, 10% replacement fleet, placement/SOC, source demand/consent and candidate-search budget stay fixed.

Three seeds on one fixed source cohort describe conditional robustness, not empirical AV adoption, cancellation behavior or population confidence. Munich demand is AIMSUN-derived simulation; Chicago is the provided TNC subsample; Manhattan preserves its TLC cohort and pooling consent. Source year, network, fleet load and generation differ across cities. Completion need not increase with opt-in because changed assignments alter later trajectories. Gains and adverse results are retained. Daily AV throughput is not inferred from partial-day service.
