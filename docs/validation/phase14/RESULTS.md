# Phase 14: booking-patience robustness

All **81 unique city/fleet/patience/seed/policy conditions** pass complete physical checks. Fresh-process repetitions are listed separately in the manifest. Every assumption stratum remains distinct.

These are assumed offer/booking limits, not measured rider cancellation behavior. No accepted passenger is silently cancelled when actual execution is late. Accepted promises must fit the source-clock deadline; actual pickups after that deadline are explicitly retained and counted.

| City | Fleet | Cutoff s | Policy | Seeds | Completed | AV trips | Eligible wait s | Within own limit | Within fixed 480s | Late actual pickups | Fleet empty km |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| chicago | 100 | 240 | all_human | 3 | 465.00 | 0.00 | 153.93 | 463.33 | 465.00 | 1.67 | 346.84 |
| chicago | 100 | 240 | threshold_0 | 3 | 449.67 | 19.67 | 147.27 | 448.00 | 449.67 | 1.67 | 342.82 |
| chicago | 100 | 240 | threshold_240 | 3 | 445.67 | 18.00 | 153.57 | 444.33 | 445.67 | 1.33 | 341.54 |
| chicago | 100 | 480 | all_human | 3 | 531.33 | 0.00 | 316.74 | 527.67 | 527.67 | 3.67 | 680.96 |
| chicago | 100 | 480 | threshold_0 | 3 | 536.00 | 23.00 | 304.99 | 532.33 | 532.33 | 3.67 | 693.07 |
| chicago | 100 | 480 | threshold_240 | 3 | 547.00 | 29.33 | 311.52 | 543.67 | 543.67 | 3.33 | 727.31 |
| chicago | 100 | 720 | all_human | 3 | 572.67 | 0.00 | 469.19 | 564.67 | 240.67 | 8.00 | 931.22 |
| chicago | 100 | 720 | threshold_0 | 3 | 538.33 | 31.33 | 463.22 | 532.00 | 229.00 | 6.33 | 858.38 |
| chicago | 100 | 720 | threshold_240 | 3 | 536.67 | 35.00 | 470.42 | 530.00 | 223.33 | 6.67 | 890.68 |
| manhattan | 775 | 240 | all_human | 3 | 1815.00 | 0.00 | 127.31 | 1809.33 | 1815.00 | 5.67 | 681.14 |
| manhattan | 775 | 240 | threshold_0 | 3 | 1745.67 | 59.00 | 122.86 | 1740.00 | 1745.67 | 5.67 | 677.66 |
| manhattan | 775 | 240 | threshold_240 | 3 | 1762.33 | 91.33 | 143.65 | 1755.67 | 1762.33 | 6.67 | 696.24 |
| manhattan | 775 | 480 | all_human | 3 | 2474.33 | 0.00 | 227.08 | 2459.33 | 2459.33 | 15.00 | 1396.87 |
| manhattan | 775 | 480 | threshold_0 | 3 | 2436.00 | 83.33 | 198.13 | 2417.00 | 2417.00 | 19.00 | 1418.57 |
| manhattan | 775 | 480 | threshold_240 | 3 | 2441.00 | 134.00 | 257.34 | 2423.33 | 2423.33 | 17.67 | 1438.85 |
| manhattan | 775 | 720 | all_human | 3 | 2743.00 | 0.00 | 318.67 | 2726.00 | 1962.67 | 17.00 | 1836.66 |
| manhattan | 775 | 720 | threshold_0 | 3 | 2702.33 | 97.00 | 270.38 | 2682.67 | 1915.33 | 19.67 | 1838.06 |
| manhattan | 775 | 720 | threshold_240 | 3 | 2707.33 | 152.67 | 329.28 | 2687.67 | 1924.33 | 19.67 | 1862.68 |
| munich | 50 | 240 | all_human | 3 | 425.00 | 0.00 | 161.50 | 424.00 | 425.00 | 1.00 | 554.49 |
| munich | 50 | 240 | threshold_0 | 3 | 386.33 | 8.67 | 157.52 | 385.00 | 386.33 | 1.33 | 518.42 |
| munich | 50 | 240 | threshold_240 | 3 | 382.67 | 7.33 | 160.05 | 381.33 | 382.67 | 1.33 | 510.54 |
| munich | 50 | 480 | all_human | 3 | 587.33 | 0.00 | 329.82 | 586.00 | 586.00 | 1.33 | 1074.74 |
| munich | 50 | 480 | threshold_0 | 3 | 557.00 | 23.33 | 303.54 | 554.33 | 554.33 | 2.67 | 1025.30 |
| munich | 50 | 480 | threshold_240 | 3 | 556.00 | 25.67 | 302.44 | 554.67 | 554.67 | 1.33 | 1033.37 |
| munich | 50 | 720 | all_human | 3 | 607.00 | 0.00 | 533.74 | 600.67 | 222.33 | 6.33 | 1186.30 |
| munich | 50 | 720 | threshold_0 | 3 | 575.67 | 34.33 | 497.58 | 567.67 | 218.33 | 8.00 | 1184.77 |
| munich | 50 | 720 | threshold_240 | 3 | 581.33 | 31.67 | 487.77 | 573.33 | 213.00 | 8.00 | 1213.54 |

## Interpreting robustness

`paired_effects.csv` distinguishes policy changes at fixed patience from patience changes at a fixed policy. `common_rider_effects.csv` compares the same served request IDs. Aggregate served wait means may change because the served sample changes. Completion need not be monotone: the intervention changes later fleet trajectories and allocation. Retain every seed and adverse direction.

Every city/fleet has the same immutable source cohort, initial distribution, fence, vehicle specifications, service assumptions, routing runtime and exogenous network inputs across cutoffs. Only `op_max_wait_time` and source-clock request deadlines change. Actual placement/SOC and typed random backgrounds are checked across cutoffs. Demand-file audit hashes intentionally change with those deadline bytes; all non-deadline demand fields are verified separately.

The ordinary city summary rejects incompatible input assumptions. This report groups explicitly by patience and refuses other uncontrolled changes. Conditions sharing city/fleet/seed/policy but differing in cutoff are neither pooled seed repetitions nor replay samples.

Trips, waits and late-pickup counts use evaluation request IDs and include later fulfillment. Occupied utilization is clipped to the evaluation clock; empty distance includes warm-up and fulfillment tails. `within_limit_completed` counts served evaluation requests whose actual pickup fits their own assumed cutoff; that deadline differs across strata. `within_480s_completed` holds a common 8-minute actual-pickup target fixed across every stratum. Offered wait and actual wait are distinct.

The 4/8/12-minute main grid is prespecified. Total fleet and 10% AV replacement, 0.3 per-request opt-in, cautious factor1.25, endpoint fence and 0/240-second dispatch thresholds remain fixed within each native city profile. Human acceptance, human/AV repositioning and execution noise remain off. Patience and the source-specific fleet are unverified assumptions; completed-trip data do not identify rejected demand or real cancellations. Provided traffic and replanning can produce timing error; no cause is inferred solely from a late pickup.

Three initialization seeds on one fixed cohort provide conditional sensitivity, not population uncertainty or field calibration. Munich is simulated AIMSUN-derived demand, Chicago is a provided TNC subsample and Manhattan is the fixed TLC cohort. City/year/source-generation/load differences prevent geography-only causal comparisons. No daily AV throughput is extrapolated.
