# Policy robustness under assumed booking patience

The following are matched three-seed policy contrasts at each fixed assumed cutoff. All 27 combinations are retained. Completion intervals are conditional paired t intervals over three initialization seeds on one cohort; they are not population or cross-city confidence intervals. A mean direction varying across cutoffs is descriptive, not a significance test.

| City | Cutoff s | Candidate minus control | Completion change | Conditional 95% interval | Fixed 480s completion change | AV trips change | Same-served eligible wait change s | Empty km change |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| chicago | 240 | threshold_240 minus threshold_0 | -4.00 | [-102.99, +94.99] | -4.00 | -1.67 | +7.65 | -1.27 |
| chicago | 240 | threshold_0 minus all_human | -15.33 | [-63.78, +33.11] | -15.33 | +19.67 | -2.98 | -4.03 |
| chicago | 240 | threshold_240 minus all_human | -19.33 | [-70.38, +31.72] | -19.33 | +18.00 | +7.30 | -5.30 |
| chicago | 480 | threshold_240 minus threshold_0 | +11.00 | [-20.72, +42.72] | +11.33 | +6.33 | +13.17 | +34.24 |
| chicago | 480 | threshold_0 minus all_human | +4.67 | [-30.84, +40.18] | +4.67 | +23.00 | -17.22 | +12.10 |
| chicago | 480 | threshold_240 minus all_human | +15.67 | [-5.75, +37.08] | +16.00 | +29.33 | +0.18 | +46.35 |
| chicago | 720 | threshold_240 minus threshold_0 | -1.67 | [-77.84, +74.51] | -5.67 | +3.67 | +14.47 | +32.30 |
| chicago | 720 | threshold_0 minus all_human | -34.33 | [-124.50, +55.83] | -11.67 | +31.33 | -27.96 | -72.84 |
| chicago | 720 | threshold_240 minus all_human | -36.00 | [-51.51, -20.49] | -17.33 | +35.00 | -6.69 | -40.55 |
| manhattan | 240 | threshold_240 minus threshold_0 | +16.67 | [-2.63, +35.96] | +16.67 | +32.33 | +22.66 | +18.58 |
| manhattan | 240 | threshold_0 minus all_human | -69.33 | [-76.92, -61.74] | -69.33 | +59.00 | -6.17 | -3.47 |
| manhattan | 240 | threshold_240 minus all_human | -52.67 | [-79.00, -26.34] | -52.67 | +91.33 | +18.50 | +15.11 |
| manhattan | 480 | threshold_240 minus threshold_0 | +5.00 | [-12.91, +22.91] | +6.33 | +50.67 | +61.57 | +20.28 |
| manhattan | 480 | threshold_0 minus all_human | -38.33 | [-52.46, -24.21] | -42.33 | +83.33 | -32.53 | +21.71 |
| manhattan | 480 | threshold_240 minus all_human | -33.33 | [-49.50, -17.17] | -36.00 | +134.00 | +27.97 | +41.98 |
| manhattan | 720 | threshold_240 minus threshold_0 | +5.00 | [-32.10, +42.10] | +9.00 | +55.67 | +62.84 | +24.62 |
| manhattan | 720 | threshold_0 minus all_human | -40.67 | [-60.59, -20.74] | -47.33 | +97.00 | -52.04 | +1.40 |
| manhattan | 720 | threshold_240 minus all_human | -35.67 | [-56.35, -14.98] | -38.33 | +152.67 | +9.89 | +26.02 |
| munich | 240 | threshold_240 minus threshold_0 | -3.67 | [-17.35, +10.01] | -3.67 | -1.33 | +5.27 | -7.88 |
| munich | 240 | threshold_0 minus all_human | -38.67 | [-40.10, -37.23] | -38.67 | +8.67 | -6.12 | -36.07 |
| munich | 240 | threshold_240 minus all_human | -42.33 | [-57.31, -27.36] | -42.33 | +7.33 | -4.79 | -43.94 |
| munich | 480 | threshold_240 minus threshold_0 | -1.00 | [-65.73, +63.73] | +0.33 | +2.33 | +21.55 | +8.07 |
| munich | 480 | threshold_0 minus all_human | -30.33 | [-66.70, +6.03] | -31.67 | +23.33 | -34.04 | -49.44 |
| munich | 480 | threshold_240 minus all_human | -31.33 | [-63.37, +0.70] | -31.33 | +25.67 | -7.61 | -41.37 |
| munich | 720 | threshold_240 minus threshold_0 | +5.67 | [-43.16, +54.49] | -5.33 | -2.67 | +9.71 | +28.77 |
| munich | 720 | threshold_0 minus all_human | -31.33 | [-60.02, -2.65] | -4.00 | +34.33 | -49.81 | -1.53 |
| munich | 720 | threshold_240 minus all_human | -25.67 | [-63.04, +11.71] | -9.33 | +31.67 | -24.21 | +27.24 |

`policy_stability_by_city.csv` records mean-sign changes across cutoffs for completion, fixed-target service, AV allocation, same-served waits and empty distance. Seed ranges and intervals remain in the detailed CSV. A common-served comparison conditions on service in both policies; requests served by only one policy are excluded from its wait contrast.

## Patience changes at a fixed policy

| City | Policy | Cutoff s | Completion mean | Completed within fixed 480s | Late actual pickups | Offered mean wait s | Actual eligible mean wait s |
| --- | --- | --- | --- | --- | --- | --- | --- |
| chicago | all_human | 240 | 465.00 | 465.00 | 1.67 | 154.56 | 153.93 |
| chicago | threshold_0 | 240 | 449.67 | 449.67 | 1.67 | 153.72 | 147.27 |
| chicago | threshold_240 | 240 | 445.67 | 445.67 | 1.33 | 153.35 | 153.57 |
| chicago | all_human | 480 | 531.33 | 527.67 | 3.67 | 320.59 | 316.74 |
| chicago | threshold_0 | 480 | 536.00 | 532.33 | 3.67 | 315.41 | 304.99 |
| chicago | threshold_240 | 480 | 547.00 | 543.67 | 3.33 | 317.23 | 311.52 |
| chicago | all_human | 720 | 572.67 | 240.67 | 8.00 | 469.77 | 469.19 |
| chicago | threshold_0 | 720 | 538.33 | 229.00 | 6.33 | 466.09 | 463.22 |
| chicago | threshold_240 | 720 | 536.67 | 223.33 | 6.67 | 468.94 | 470.42 |
| manhattan | all_human | 240 | 1815.00 | 1815.00 | 5.67 | 132.22 | 127.31 |
| manhattan | threshold_0 | 240 | 1745.67 | 1745.67 | 5.67 | 133.46 | 122.86 |
| manhattan | threshold_240 | 240 | 1762.33 | 1762.33 | 6.67 | 135.73 | 143.65 |
| manhattan | all_human | 480 | 2474.33 | 2459.33 | 15.00 | 245.18 | 227.08 |
| manhattan | threshold_0 | 480 | 2436.00 | 2417.00 | 19.00 | 251.92 | 198.13 |
| manhattan | threshold_240 | 480 | 2441.00 | 2423.33 | 17.67 | 252.94 | 257.34 |
| manhattan | all_human | 720 | 2743.00 | 1962.67 | 17.00 | 335.43 | 318.67 |
| manhattan | threshold_0 | 720 | 2702.33 | 1915.33 | 19.67 | 342.89 | 270.38 |
| manhattan | threshold_240 | 720 | 2707.33 | 1924.33 | 19.67 | 341.51 | 329.28 |
| munich | all_human | 240 | 425.00 | 425.00 | 1.00 | 161.79 | 161.50 |
| munich | threshold_0 | 240 | 386.33 | 386.33 | 1.33 | 162.28 | 157.52 |
| munich | threshold_240 | 240 | 382.67 | 382.67 | 1.33 | 160.96 | 160.05 |
| munich | all_human | 480 | 587.33 | 586.00 | 1.33 | 324.75 | 329.82 |
| munich | threshold_0 | 480 | 557.00 | 554.33 | 2.67 | 323.58 | 303.54 |
| munich | threshold_240 | 480 | 556.00 | 554.67 | 1.33 | 323.75 | 302.44 |
| munich | all_human | 720 | 607.00 | 222.33 | 6.33 | 500.01 | 533.74 |
| munich | threshold_0 | 720 | 575.67 | 218.33 | 8.00 | 496.95 | 497.58 |
| munich | threshold_240 | 720 | 581.33 | 213.00 | 8.00 | 503.85 | 487.77 |

A looser booking cutoff permits a different request/vehicle history. More completed service may coexist with lower service within the fixed 480-second target, larger actual wait or changed AV allocation. Actual late pickups are observed execution outcomes, not invalid accepted offers: all promises fit their own source-clock cutoff and every accepted booking completes. No real cancellation distribution is fitted.
