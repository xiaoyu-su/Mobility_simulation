# Phase 16: AV fleet-share robustness

**81 unique conditions**; every accepted booking physically completes. Repetitions are separate replay records.

| City | Fleet | Requested AV % | Policy | Seeds | Completed | AV trips | AV occupied % | Eligible served wait s | Fixed 480s service | Late actual pickups | Empty km |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| chicago | 100 | 5 | all_human | 3 | 529.67 | 0.00 | — | 313.73 | 525.67 | 4.00 | 695.38 |
| chicago | 100 | 5 | threshold_0 | 3 | 526.67 | 15.33 | 47.71 | 306.14 | 523.67 | 3.00 | 667.34 |
| chicago | 100 | 5 | threshold_240 | 3 | 539.67 | 18.33 | 62.36 | 313.68 | 536.33 | 3.33 | 712.03 |
| chicago | 100 | 10 | all_human | 3 | 558.33 | 0.00 | — | 317.31 | 554.33 | 4.00 | 705.51 |
| chicago | 100 | 10 | threshold_0 | 3 | 537.00 | 33.67 | 45.20 | 309.26 | 534.33 | 2.67 | 674.85 |
| chicago | 100 | 10 | threshold_240 | 3 | 528.67 | 32.67 | 56.10 | 316.58 | 525.33 | 3.33 | 714.35 |
| chicago | 100 | 20 | all_human | 3 | 566.33 | 0.00 | — | 318.69 | 563.00 | 3.33 | 697.04 |
| chicago | 100 | 20 | threshold_0 | 3 | 491.00 | 57.33 | 39.10 | 308.01 | 487.00 | 4.00 | 666.87 |
| chicago | 100 | 20 | threshold_240 | 3 | 499.33 | 55.33 | 45.11 | 312.30 | 498.67 | 0.67 | 699.48 |
| manhattan | 775 | 5 | all_human | 3 | 2451.00 | 0.00 | — | 224.65 | 2433.33 | 17.67 | 1398.51 |
| manhattan | 775 | 5 | threshold_0 | 3 | 2439.67 | 46.00 | 14.58 | 215.64 | 2421.33 | 18.33 | 1411.28 |
| manhattan | 775 | 5 | threshold_240 | 3 | 2432.33 | 88.33 | 25.74 | 255.97 | 2411.33 | 21.00 | 1426.23 |
| manhattan | 775 | 10 | all_human | 3 | 2452.67 | 0.00 | — | 224.25 | 2435.00 | 17.67 | 1398.71 |
| manhattan | 775 | 10 | threshold_0 | 3 | 2418.67 | 81.67 | 13.37 | 201.77 | 2401.00 | 17.67 | 1417.64 |
| manhattan | 775 | 10 | threshold_240 | 3 | 2410.67 | 132.33 | 20.21 | 255.98 | 2392.00 | 18.67 | 1429.02 |
| manhattan | 775 | 20 | all_human | 3 | 2452.33 | 0.00 | — | 225.24 | 2434.67 | 17.67 | 1401.57 |
| manhattan | 775 | 20 | threshold_0 | 3 | 2371.00 | 128.67 | 10.38 | 177.46 | 2349.00 | 22.00 | 1432.06 |
| manhattan | 775 | 20 | threshold_240 | 3 | 2376.00 | 179.67 | 14.18 | 215.27 | 2352.33 | 23.67 | 1446.19 |
| munich | 50 | 5 | all_human | 3 | 583.67 | 0.00 | — | 323.39 | 580.00 | 3.67 | 1063.03 |
| munich | 50 | 5 | threshold_0 | 3 | 573.67 | 11.00 | 43.80 | 311.21 | 572.00 | 1.67 | 1048.50 |
| munich | 50 | 5 | threshold_240 | 3 | 569.00 | 12.00 | 46.02 | 303.18 | 566.67 | 2.33 | 1061.10 |
| munich | 50 | 10 | all_human | 3 | 583.67 | 0.00 | — | 323.39 | 580.00 | 3.67 | 1063.03 |
| munich | 50 | 10 | threshold_0 | 3 | 556.67 | 22.67 | 35.79 | 309.86 | 554.67 | 2.00 | 1023.46 |
| munich | 50 | 10 | threshold_240 | 3 | 548.33 | 25.00 | 38.78 | 303.79 | 546.67 | 1.67 | 1059.88 |
| munich | 50 | 20 | all_human | 3 | 583.67 | 0.00 | — | 323.39 | 580.00 | 3.67 | 1063.03 |
| munich | 50 | 20 | threshold_0 | 3 | 516.33 | 40.33 | 33.35 | 294.60 | 514.00 | 2.33 | 946.36 |
| munich | 50 | 20 | threshold_240 | 3 | 508.00 | 43.33 | 33.75 | 289.47 | 506.33 | 1.67 | 984.98 |

## Definitions and interpretation

AV replacement targets5/10/20% use integer rounded counts (minimum one AV and one human); exact roster counts remain in every seed row. Total fleet and fixed20% placement anchor are unchanged. The anchored slots start inside the fence at every share, including when human. AV types replace nested final vehicle IDs. Opt-in stays0.3 and both endpoints must stay inside the unchanged fence.

Candidate-search budgets remain30 positions per group in native studies, but actual-type partitions change with replacement count. All-human shadow partitions follow each share and may change service despite identical geometry. These outcomes are retained explicitly. `paired_effects.csv` separates within-share policy effects from direct share changes at fixed policy. `control_adjusted_share_effects.csv` compares mixed-minus-matched-human responses across shares against10%; this diagnostic does not identify a field effect or remove every search interaction.

`fixed_group_results.csv` and `fixed_group_effects.csv` retain the same request groups/denominators: baseline_eligible means the fixed0.3 opted-in in-fence requests; additional_opt_in means in-fence requests outside that draw (they remain non-opted-in throughout this study); outside_fence never qualifies. `common_rider_effects.csv` conditions on identical IDs served in both conditions. Served-only mean waits can change composition.

`common_human_completed` and `common_human_trips_per_online_hour` use exactly the same first N-minus-anchor vehicle IDs in every stratum and policy. The existing retained-human metric instead uses the actual human roster, which changes membership with share. AV occupied utilization and AV throughput use the actual number of AVs, so allocation gains can coexist with falling per-AV use or changes to fixed human slots.

Trips/waits refer to evaluation requests including later fulfillment. Occupied utilization/online hours use the evaluation clock; empty distance includes warm-up and fulfillment. Accepted promises fit the original480s deadline and every accepted rider completes; actual late pickups remain visible. Human acceptance, repositioning and execution noise stay off; cautious AV factor1.25, fence, demand/pooling consent, patience/service and source traffic stay fixed.

The optional placement anchor leaves legacy initialization unchanged when omitted. Separate fresh legacy10% seed0 bridge runs retain historical byte comparisons; they are not pooled with the anchored grid as replications. Three seeds on one fixed cohort give conditional robustness, not population uncertainty or observed AV market penetration. Munich is AIMSUN-derived demand, Chicago the provided TNC sample and Manhattan the fixed TLC cohort. No geography-only causal comparison or daily throughput extrapolation is made.
