# Phase 8 real Manhattan results

All 18 full physical simulations completed on frozen source
`890505b3db913cbab61c12c3c79b29659de0e296bec1c4dce9499ea7d4f4aeee`. All 15 comparisons of background audit records pass:
within each seed, every policy has identical loaded demand, network and initial
fleet state. Every accepted booking finishes; independent checks find zero
early pickups, private-pooling, AV opt-in/fence, human-shift or human-repositioning
violations. Vehicle chronology, capacity and physical service minima also pass.

These are counterfactual policy experiments, not observed AV deployment
measurements. Inputs are November 26, 2019, 07:00–10:00, with two-hour warm-up,
10% fixed source sampling and a causal 60-second grid. Training uses only
November 5/12/19. The initial workload-derived total fleet remains fixed;
AVs replace humans. Actual counts, fence selection and assumptions are below.
Human acceptance is off, human HiGHS repositioning on in every arm, to isolate
the AV policy levers. Human acceptance/future-value/shift coexistence is tested
separately in full fixtures. All seeds use the same assumed rider opt-in set.

```json
{
  "requested_share": 0.1,
  "av_count": 78,
  "human_count": 697,
  "fence_zones": [
    48,
    68,
    79,
    107,
    140,
    142,
    161,
    162,
    163,
    164,
    170,
    230,
    231,
    234,
    236,
    237,
    239,
    246,
    249
  ],
  "fence_selection": "densest training-day pickup zones",
  "opt_in_share": 0.5,
  "preference_seconds": 0,
  "repositioning": false,
  "interpretation": "Fixed total fleet; AVs replace human vehicles. Adoption, fence and fleet split are scenario assumptions."
}

```

## Across three simulation seeds

Values are means of per-seed statistics. Complete seeds and ranges are retained
in `seed_results.csv` and `configuration_summary.csv`; no configurations are
discarded based on their outcomes. Waits describe served passengers in a fixed
eligibility group. `common_rider_effects.csv` separately compares exactly the
same served identities to the zero-preference/no-AV-repositioning control.

| Preference (s) | AV repo | Completed | AV trips | Human trips | AV served share | AV utilization | AV idle share | Eligible wait mean (s) | Other wait mean (s) | Human trips/online h | AV reposition km |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| -300 | False | 3128.3 | 25.3 | 3103.0 | 0.81% | 4.0% | 95.5% | 232.1 | 300.0 | 1.484 | 0.0 |
| 0 | False | 3133.7 | 102.7 | 3031.0 | 3.28% | 13.9% | 84.7% | 247.2 | 291.7 | 1.450 | 0.0 |
| 300 | False | 3126.3 | 180.0 | 2946.3 | 5.76% | 21.8% | 74.2% | 266.8 | 293.2 | 1.409 | 0.0 |
| -300 | True | 3127.7 | 26.3 | 3101.3 | 0.84% | 4.9% | 81.4% | 255.4 | 303.7 | 1.483 | 705.0 |
| 0 | True | 3142.0 | 109.0 | 3033.0 | 3.47% | 14.9% | 67.9% | 225.4 | 286.8 | 1.451 | 742.8 |
| 300 | True | 3144.0 | 305.0 | 2839.0 | 9.70% | 40.6% | 36.1% | 243.4 | 273.6 | 1.358 | 827.1 |


Utilization/idle/online time is clipped to the evaluation clock. Trips/waits use
the fixed request cohort and retain later completion. Reposition distance and
model financial values include warm-up plus the fulfillment tail. Both products
use copied base-vehicle cost specifications; these omit observed AV-specific
hardware/labor economics and are not observed wages or profits.

## Limits and interpretation

Raising AV share of served trips is a change in allocation, not automatically
a gain in completion, rider service or human income. The tables retain adverse
waits, human trip transfers and empty driving. Nearest-idle-AV diagnostics
measure proximity, not a proof of alternative full-plan feasibility. They can
explain placement disadvantages but must not be called guaranteed missed trips.

Three seeds measure simulation variability conditional on one demand sample.
The sample, opt-in share, fence, fixed AV fleet split, supply and patience are
assumptions. This phase does not reproduce the screenshot's numerical claims,
resolve Phase 7 calibration, establish field benefits, or claim full-demand or
cross-city validation. Cautious AV speeds, ETA-threshold dispatch and joint
human/AV demand accounting remain later rounds.
