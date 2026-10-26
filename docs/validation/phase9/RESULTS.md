# Phase 9 measured Manhattan results

All **56 physical runs** completed on source `66fe97b5ab63c89a440583da274cb3e1e87841f070285cb322e2b95f0a5ad939`: 36 six-seed dispatch runs, 18 three-seed follow-ups (including three exact control replays), and two full-demand runs. All independent physical booking, product, timing-factor, chronology, capacity, service-duration, fence, opt-in and joint-demand bounds checks pass. The three replay pairs have byte-identical user, vehicle, dispatch, product, human repositioning and random audit records.

These are conditional counterfactual model outcomes, not field AV measurements. Assumptions include 30% opt-in, a 10% replacement AV fleet, training-derived 19-zone fence, and cautious AV travel time ×1.25. Opt-in is keyed per simulated request, not a persistent rider identity; the opt-in/fence conjunction leaves 224 sampled and 2,377 full-demand evaluation requests eligible. Human acceptance is off, with both AV demand repositioning and human HiGHS repositioning on in all experiments. Every grid arm has the same separate human/AV search budget. The threshold is a dispatch-time ETA comparison, not an actual pickup guarantee.

## main

| Arm | Seeds | Completed | AV trips | AV served share | AV utilization | Eligible wait s | Other wait s | Human trips/online h | AV empty distance share | AV repo km |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| cost_control | 6 | 3124.5 | 14.7 | 0.47% | 2.4% | 252.9 | 297.0 | 1.487 | 94.3% | 670.8 |
| threshold_0 | 6 | 3132.2 | 53.3 | 1.70% | 9.8% | 226.6 | 292.2 | 1.472 | 80.1% | 717.5 |
| threshold_120 | 6 | 3138.0 | 135.7 | 4.32% | 23.5% | 226.0 | 287.1 | 1.436 | 62.4% | 801.7 |
| threshold_240 | 6 | 3133.5 | 180.5 | 5.76% | 29.5% | 249.8 | 285.1 | 1.412 | 58.2% | 842.5 |
| threshold_480 | 6 | 3138.5 | 210.0 | 6.69% | 33.7% | 288.6 | 284.8 | 1.401 | 56.2% | 848.5 |
| equal_speed_240 | 6 | 3136.8 | 204.0 | 6.50% | 27.7% | 227.2 | 284.0 | 1.403 | 56.8% | 865.4 |

## followup

| Arm | Seeds | Completed | AV trips | AV served share | AV utilization | Eligible wait s | Other wait s | Human trips/online h | AV empty distance share | AV repo km |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| threshold_240 | 3 | 3134.7 | 183.3 | 5.85% | 29.7% | 252.7 | 282.2 | 1.411 | 58.1% | 855.5 |
| forecast_noise | 3 | 3140.3 | 174.3 | 5.55% | 29.1% | 249.7 | 283.9 | 1.418 | 67.8% | 1264.7 |
| joint | 3 | 3139.0 | 176.0 | 5.61% | 28.7% | 251.0 | 286.5 | 1.417 | 61.9% | 965.6 |
| retarget_control_300 | 3 | 3135.7 | 180.7 | 5.76% | 30.0% | 248.9 | 283.1 | 1.413 | 63.3% | 1055.1 |
| retarget_300 | 3 | 3135.7 | 187.7 | 5.98% | 31.4% | 261.5 | 288.2 | 1.410 | 56.6% | 808.7 |
| combined | 3 | 3137.7 | 178.3 | 5.68% | 28.8% | 249.4 | 285.6 | 1.415 | 73.5% | 1749.8 |

## full

| Arm | Seeds | Completed | AV trips | AV served share | AV utilization | Eligible wait s | Other wait s | Human trips/online h | AV empty distance share | AV repo km |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| threshold_0 | 1 | 31720.0 | 317.0 | 1.00% | 5.4% | 166.0 | 208.8 | 1.466 | 77.6% | 3652.3 |
| threshold_240 | 1 | 31831.0 | 2139.0 | 6.72% | 35.2% | 180.8 | 205.8 | 1.386 | 42.4% | 5243.7 |

## Measured changes and costs

At cautious speeds, threshold 240 versus same-search cost control changes mean completion from 3124.50 to 3133.50, AV trips from 14.67 to 180.50, and AV occupied utilization from 2.42% to 29.46%. Human trips per online hour fall 5.04%. The +9.0 mean completion change has conditional six-seed t interval [−0.003,18.003], including zero; it is not a demonstrated completion gain.

Threshold 240 versus threshold 0 adds 127.17 AV trips but only 1.33 total completions on average (interval [−4.88,7.55]); eligible served mean wait rises 23.17 seconds (interval [11.66,34.68]). Threshold 480 raises AV share further while worsening eligible-rider wait. Threshold 120 has a lower eligible wait and higher mean completion than 240 in this fixed cohort; no configuration is chosen after inspecting the held-out outcomes. Equal speed at threshold 240 raises mean AV completions from 180.50 to 204.00 relative to cautious speed, showing that the physical speed assumption materially changes allocation.

At the same 300-second callback, retargeting averages 196.67 actual changed empty targets per run. Mean completion remains 3135.67; AV trips increase 180.67→187.67 and AV empty-distance share falls 63.32%→56.59%, while eligible served wait rises 248.91→261.52 seconds. Seed completion changes are +8/−2/−6, so this is not a robust completion improvement. Joint planning gives 3139.00 completions versus 3134.67 in its three-seed control but fewer AV completions 176.00 versus 183.33. The combined treatment increases AV empty-distance share to 73.51% versus 58.13% in the ordinary threshold 240 control. These adverse outcomes remain in the results. The forecast-noise arm tests sensitivity to assumed errors; a favorable draw is not evidence that inaccurate forecasts are beneficial.

The single-seed full-demand pair changes completion **31720→31831**, AV completed trips **317→2139**, eligible served wait **165.99→180.85s**, and human trips/online hour **1.4663→1.3864**. This is a complete scale check, with no replicated full-demand uncertainty estimate.

## Scope and interpretation

The sample cohort has 3,150 evaluation requests plus 751 warm-up requests, 78 AVs and 697 humans; full demand has 32,192 plus 7,315 requests, 793 AVs and 7,139 humans. Both evaluate November 26, 2019, 07:00–10:00, with 05:00–07:00 warm-up, training November 5/12/19, a causal 60-second request grid and later physical completion tail. The full-demand comparison is one seed, not a full-day or replicated scale result. Sample/full bundles have distinct request IDs, fitted proxies and CRC32 opt-in sets; cross-bundle differences are not an isolated density effect.

All seed outcomes and ranges are retained in `seed_results.csv` and `configuration_summary.csv`. `paired_effects.csv` retains paired changes and t intervals conditional on simulation seeds and this fixed source cohort. These intervals do not measure population or cross-city uncertainty. `common_rider_effects.csv` compares identical served rider identities; aggregate served-only wait means can change composition.

Utilization/online time is clipped to the evaluation clock. Trips/waits use the fixed request cohort and retain later completion. Empty/reposition distance and illustrative financial values include warm-up plus the fulfillment tail; empty distance includes pickup and empty routing, not only repositioning. AV and human vehicle costs use copied base-vehicle assumptions, not measured AV economics. Nearest-idle-AV proximity does not establish alternative full-plan feasibility. Expected AV coverage is bounded forecast mass, not observed completed trips. No daily-trip extrapolation or verified external numerical benchmark is claimed.

## Absolute empty driving at full demand

Although the AV empty-distance **share** falls from 77.59% to 42.42%, actual whole-run empty AV distance **increases from 3715.15 to 6010.40 km (61.78%)**. AV reposition distance increases from 3652.32 to 5243.74 km. More occupied travel changes the denominator, so a lower empty fraction must not be described as fewer empty kilometers. Human trips per online hour fall 5.45%; eligible served mean wait rises 14.86 seconds. Total completion rises by 111, an observed one-seed model outcome with no replicated scale confidence claim.

Across both vehicle classes, whole-run empty distance changes 55159.55→55348.77 km (+0.34%): the AV increase is partly offset by less human empty driving. This fleet-total measure has the same warm-up/completion-tail domain as the per-class distances.
