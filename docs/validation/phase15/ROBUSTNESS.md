# Policy robustness and fixed-group spillovers under opt-in assumptions

All27 matched policy contrasts are retained. Conditional paired t intervals use three initialization seeds on one fixed cohort, not population or cross-city uncertainty. Descriptive mean-sign changes are not significance tests.

| City | Opt-in % | Candidate minus control | Completion change | Conditional 95% interval | Fixed480s service change | AV trip change | Same-served baseline-group wait change s | Empty km change |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| chicago | 0 | threshold_240 minus threshold_0 | +0.00 | [+0.00, +0.00] | +0.00 | +0.00 | +0.00 | +0.00 |
| chicago | 0 | threshold_0 minus all_human | -24.33 | [-79.56, +30.90] | -23.33 | +0.00 | -1.29 | -34.50 |
| chicago | 0 | threshold_240 minus all_human | -24.33 | [-79.56, +30.90] | -23.33 | +0.00 | -1.29 | -34.50 |
| chicago | 30 | threshold_240 minus threshold_0 | +11.00 | [-20.72, +42.72] | +11.33 | +6.33 | +13.17 | +34.24 |
| chicago | 30 | threshold_0 minus all_human | +4.67 | [-30.84, +40.18] | +4.67 | +23.00 | -17.22 | +12.10 |
| chicago | 30 | threshold_240 minus all_human | +15.67 | [-5.75, +37.08] | +16.00 | +29.33 | +0.18 | +46.35 |
| chicago | 100 | threshold_240 minus threshold_0 | +25.67 | [-76.22, +127.56] | +24.33 | +4.33 | +4.54 | +29.16 |
| chicago | 100 | threshold_0 minus all_human | -19.33 | [-66.09, +27.43] | -18.33 | +46.67 | -5.97 | -1.36 |
| chicago | 100 | threshold_240 minus all_human | +6.33 | [-49.51, +62.18] | +6.00 | +51.00 | +5.96 | +27.80 |
| manhattan | 0 | threshold_240 minus threshold_0 | +0.00 | [+0.00, +0.00] | +0.00 | +0.00 | +0.00 | +0.00 |
| manhattan | 0 | threshold_0 minus all_human | -75.67 | [-111.18, -40.16] | -79.67 | +0.00 | +20.43 | +22.45 |
| manhattan | 0 | threshold_240 minus all_human | -75.67 | [-111.18, -40.16] | -79.67 | +0.00 | +20.43 | +22.45 |
| manhattan | 30 | threshold_240 minus threshold_0 | +5.00 | [-12.91, +22.91] | +6.33 | +50.67 | +61.57 | +20.28 |
| manhattan | 30 | threshold_0 minus all_human | -38.33 | [-52.46, -24.21] | -42.33 | +83.33 | -32.53 | +21.71 |
| manhattan | 30 | threshold_240 minus all_human | -33.33 | [-49.50, -17.17] | -36.00 | +134.00 | +27.97 | +41.98 |
| manhattan | 100 | threshold_240 minus threshold_0 | +21.33 | [-4.04, +46.71] | +22.00 | +100.00 | +37.40 | +71.88 |
| manhattan | 100 | threshold_0 minus all_human | -31.33 | [-49.64, -13.02] | -32.67 | +150.67 | -10.51 | -7.07 |
| manhattan | 100 | threshold_240 minus all_human | -10.00 | [-26.29, +6.29] | -10.67 | +250.67 | +26.16 | +64.81 |
| munich | 0 | threshold_240 minus threshold_0 | +0.00 | [+0.00, +0.00] | +0.00 | +0.00 | +0.00 | +0.00 |
| munich | 0 | threshold_0 minus all_human | -50.67 | [-70.75, -30.59] | -50.67 | +0.00 | -6.41 | -108.76 |
| munich | 0 | threshold_240 minus all_human | -50.67 | [-70.75, -30.59] | -50.67 | +0.00 | -6.41 | -108.76 |
| munich | 30 | threshold_240 minus threshold_0 | -1.00 | [-65.73, +63.73] | +0.33 | +2.33 | +21.55 | +8.07 |
| munich | 30 | threshold_0 minus all_human | -30.33 | [-66.70, +6.03] | -31.67 | +23.33 | -34.04 | -49.44 |
| munich | 30 | threshold_240 minus all_human | -31.33 | [-63.37, +0.70] | -31.33 | +25.67 | -7.61 | -41.37 |
| munich | 100 | threshold_240 minus threshold_0 | +11.00 | [-3.90, +25.90] | +12.00 | +1.67 | -13.05 | +13.87 |
| munich | 100 | threshold_0 minus all_human | -34.00 | [-36.48, -31.52] | -34.67 | +35.67 | -8.33 | -34.34 |
| munich | 100 | threshold_240 minus all_human | -23.00 | [-40.39, -5.61] | -22.67 | +37.33 | -29.52 | -20.47 |

## 30% to full opt-in at fixed threshold240

These groups use the same request IDs and denominators in both conditions. Served wait can still change which group members are served; the separate common-rider CSV addresses that selection.

| City | Fixed group | Requests | Completion change | AV trip change | Fixed480s service change | Served wait change s |
| --- | --- | --- | --- | --- | --- | --- |
| chicago | additional_opt_in | 860 | -1.00 | +38.00 | -0.67 | -3.77 |
| chicago | baseline_eligible | 370 | +0.00 | -16.33 | -1.33 | -1.67 |
| chicago | outside_fence | 821 | -8.33 | +0.00 | -8.00 | -10.87 |
| manhattan | additional_opt_in | 525 | +16.67 | +185.67 | +17.00 | +22.95 |
| manhattan | baseline_eligible | 224 | -3.00 | -69.00 | -2.33 | -3.35 |
| manhattan | outside_fence | 2401 | +9.67 | +0.00 | +10.67 | -5.59 |
| munich | additional_opt_in | 191 | +16.67 | +19.00 | +16.67 | -2.32 |
| munich | baseline_eligible | 113 | -4.33 | -7.33 | -4.00 | +1.46 |
| munich | outside_fence | 1588 | -4.00 | +0.00 | -4.00 | +0.76 |

`fixed_group_spillovers.csv` also retains zero-opt-in contrasts and both other policies. `fixed_group_effects.csv` includes paired uncertainty and omitted-pair counts for all fixed-group contrasts. `policy_stability_by_city.csv` retains all direction changes and ranges. Zero opt-in may reduce service because AV replacement vehicles cannot serve; it does not restore human drivers. All-human physical trajectories are invariant.

Higher opt-in expands eligibility within the fence but changes assignments and subsequent fleet positions. It can reduce completion or shift waits for existing riders or outside-fence requests. These are controlled simulation sensitivities, not proof of real rider willingness, AV adoption or a dynamic offer-choice response. All accepted promises satisfy480s and actual late pickup outcomes are preserved. Original analysis artifacts and their manifest are unchanged.
