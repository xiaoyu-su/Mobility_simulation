# Policy robustness and fixed-group spillovers under fleet-share assumptions

All27 matched policy contrasts are retained. Conditional paired t intervals use three initialization seeds on one fixed cohort, not population or cross-city uncertainty. Descriptive mean-sign changes are not significance tests.

| City | Fleet-share % | Candidate minus control | Completion change | Conditional 95% interval | Fixed480s service change | AV trip change | Same-served baseline-group wait change s | Empty km change |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| chicago | 5 | threshold_240 minus threshold_0 | +13.00 | [-21.15, +47.15] | +12.67 | +3.00 | +2.07 | +44.69 |
| chicago | 5 | threshold_0 minus all_human | -3.00 | [-10.45, +4.45] | -2.00 | +15.33 | -14.83 | -28.05 |
| chicago | 5 | threshold_240 minus all_human | +10.00 | [-22.48, +42.48] | +10.67 | +18.33 | -3.91 | +16.64 |
| chicago | 10 | threshold_240 minus threshold_0 | -8.33 | [-113.21, +96.54] | -9.00 | -1.00 | +14.35 | +39.50 |
| chicago | 10 | threshold_0 minus all_human | -21.33 | [-108.96, +66.29] | -20.00 | +33.67 | -12.73 | -30.66 |
| chicago | 10 | threshold_240 minus all_human | -29.67 | [-54.55, -4.78] | -29.00 | +32.67 | -4.41 | +8.84 |
| chicago | 20 | threshold_240 minus threshold_0 | +8.33 | [-8.58, +25.24] | +11.67 | -2.00 | +14.34 | +32.61 |
| chicago | 20 | threshold_0 minus all_human | -75.33 | [-185.24, +34.57] | -76.00 | +57.33 | -9.67 | -30.17 |
| chicago | 20 | threshold_240 minus all_human | -67.00 | [-192.61, +58.61] | -64.33 | +55.33 | -8.10 | +2.43 |
| manhattan | 5 | threshold_240 minus threshold_0 | -7.33 | [-15.32, +0.65] | -10.00 | +42.33 | +46.31 | +14.96 |
| manhattan | 5 | threshold_0 minus all_human | -11.33 | [-23.84, +1.17] | -12.00 | +46.00 | -15.24 | +12.77 |
| manhattan | 5 | threshold_240 minus all_human | -18.67 | [-37.64, +0.31] | -22.00 | +88.33 | +33.05 | +27.73 |
| manhattan | 10 | threshold_240 minus threshold_0 | -8.00 | [-23.11, +7.11] | -9.00 | +50.67 | +57.40 | +11.38 |
| manhattan | 10 | threshold_0 minus all_human | -34.00 | [-57.96, -10.04] | -34.00 | +81.67 | -27.85 | +18.93 |
| manhattan | 10 | threshold_240 minus all_human | -42.00 | [-61.87, -22.13] | -43.00 | +132.33 | +31.71 | +30.31 |
| manhattan | 20 | threshold_240 minus threshold_0 | +5.00 | [-30.22, +40.22] | +3.33 | +51.00 | +40.67 | +14.13 |
| manhattan | 20 | threshold_0 minus all_human | -81.33 | [-144.68, -17.98] | -85.67 | +128.67 | -55.00 | +30.49 |
| manhattan | 20 | threshold_240 minus all_human | -76.33 | [-108.27, -44.39] | -82.33 | +179.67 | -12.66 | +44.61 |
| munich | 5 | threshold_240 minus threshold_0 | -4.67 | [-12.26, +2.92] | -5.33 | +1.00 | +19.72 | +12.59 |
| munich | 5 | threshold_0 minus all_human | -10.00 | [-40.22, +20.22] | -8.00 | +11.00 | -10.21 | -14.52 |
| munich | 5 | threshold_240 minus all_human | -14.67 | [-37.61, +8.28] | -13.33 | +12.00 | -4.73 | -1.93 |
| munich | 10 | threshold_240 minus threshold_0 | -8.33 | [-31.41, +14.75] | -8.00 | +2.33 | +3.89 | +36.42 |
| munich | 10 | threshold_0 minus all_human | -27.00 | [-63.59, +9.59] | -25.33 | +22.67 | -28.29 | -39.57 |
| munich | 10 | threshold_240 minus all_human | -35.33 | [-69.06, -1.61] | -33.33 | +25.00 | -12.56 | -3.15 |
| munich | 20 | threshold_240 minus threshold_0 | -8.33 | [-43.14, +26.47] | -7.67 | +3.00 | +8.68 | +38.62 |
| munich | 20 | threshold_0 minus all_human | -67.33 | [-81.01, -53.65] | -66.00 | +40.33 | -36.83 | -116.67 |
| munich | 20 | threshold_240 minus all_human | -75.67 | [-96.79, -54.54] | -73.67 | +43.33 | -16.75 | -78.05 |

## 10% to20% AV replacement at fixed threshold240

These groups use the same request IDs and denominators in both conditions. Served wait can still change which group members are served; the separate common-rider CSV addresses that selection.

| City | Fixed group | Requests | Completion change | AV trip change | Fixed480s service change | Served wait change s |
| --- | --- | --- | --- | --- | --- | --- |
| chicago | additional_opt_in | 860 | -11.67 | +0.00 | -10.00 | -1.43 |
| chicago | baseline_eligible | 370 | -7.00 | +22.67 | -6.00 | -4.28 |
| chicago | outside_fence | 821 | -10.67 | +0.00 | -10.67 | +14.23 |
| manhattan | additional_opt_in | 525 | -12.67 | +0.00 | -14.67 | +10.22 |
| manhattan | baseline_eligible | 224 | +11.00 | +47.33 | +12.33 | -40.71 |
| manhattan | outside_fence | 2401 | -33.00 | +0.00 | -37.33 | +8.18 |
| munich | additional_opt_in | 191 | -7.67 | +0.00 | -7.67 | -1.50 |
| munich | baseline_eligible | 113 | +14.00 | +18.33 | +14.00 | -14.32 |
| munich | outside_fence | 1588 | -46.67 | +0.00 | -46.67 | +6.61 |

`fixed_group_spillovers.csv` also retains 5%-share contrasts and both other policies. `fixed_group_effects.csv` includes paired uncertainty and omitted-pair counts for all fixed-group contrasts. `policy_stability_by_city.csv` retains all direction changes and ranges. All-human shadow-search partitions follow actual replacement slots; their physical outcomes may change at identical placement/SOC. Direct share effects and mixed-minus-matched-human changes are distinct. Use fixed-human-prefix metrics to hold driver IDs fixed.

Higher AV share replaces more human slots; rider opt-in and endpoint eligibility remain fixed. It changes search partitions, assignments and subsequent fleet positions. It can reduce completion or shift waits for existing riders or outside-fence requests. These are controlled simulation sensitivities, not proof of observed AV market penetration or a field causal effect. All accepted promises satisfy480s and actual late pickup outcomes are preserved. Original analysis artifacts and their manifest are unchanged.

## Legacy placement bridge

The nine separate seed0 legacy10% runs reproduce historical raw files exactly. `placement_profile_bridge.csv` compares them with anchored10% at the same seed/arm: this changes placement, not AV share. These one-seed records are not pooled as extra replications and have no three-seed uncertainty claim. The new anchor avoids changing geometry across the main5/10/20% grid but differs from historical10% initialization.
