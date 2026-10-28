# Phase 16: AV fleet-share robustness

This follow-up tests requested AV replacement shares of **5%, 10% and 20%** at
fixed total fleet size in Munich, Chicago and Manhattan. Opt-in stays 0.3,
patience480s, AV travel factor1.25, endpoint fence, traffic, demand/cohort/pooling
consent, service durations and matching rules remain fixed. Human acceptance,
human/AV repositioning and execution noise stay off. These are assumed supply
profiles, not observed city AV penetration.

The [prespecified study](fleet_share/study.json) uses three initialization seeds
(0/1/2), all-human and threshold0/240 arms. The anchored grid has81 unique
settings, nine extra seed0 pilot/replays and nine separate legacy10% seed0
bridge records:99 physical runs /90 distinct settings in total. Bridge records
are not pooled as anchored replications.

## Keep placement fixed; retain search-partition effects

Legacy placement fences actual replacement slots, so changing AV share also
changes starting positions. An optional `placement_av_share: 0.2` anchors one
fixed superset of final vehicle IDs inside the fence in every main profile,
including when those slots remain human. Each ID keeps exactly the same
position and state of charge across shares, and AV conversion uses nested final
IDs. Omitting the option preserves legacy placement and output bytes.
`city_placement_anchor.json` records anchor slots and designated replacement
slots (also in all-human controls); actual loaded vehicle types are verified
separately from the roster and initialization audit.

Candidate-search budgets stay fixed, but their actual-type partitions change
with replacement count. Matched all-human shadow partitions follow each share;
their trajectories may therefore change despite identical geometry. The report
retains that effect. Direct share changes, within-share policy effects and
changes in mixed-minus-matched-human responses are separate contrasts. Adjusted
responses are diagnostics and do not remove every search interaction or
identify a field causal effect. The legacy placement bridge compares old/new
geometry at fixed10% and one seed; it has no three-seed uncertainty claim.

AV counts follow existing integer rounding, with at least one AV and one human:

| City | Total fleet | Requested5% | Requested10% | Requested20% | Fixed human IDs |
| --- | --- | --- | --- | --- | --- |
| Munich | 50 | 2 | 5 | 10 | 0–39 |
| Chicago | 100 | 5 | 10 | 20 | 0–79 |
| Manhattan | 775 | 39 | 78 | 155 | 0–619 |

Requested shares can differ from realized rounded percentages. AV utilization
and trips per online hour use the actual AV count. Existing retained-human
metrics change driver membership with share; the new `common_human_completed`
and `common_human_trips_per_online_hour` always use the fixed human IDs above.
The evaluation-clock denominator is fixed; trip counts include later
fulfillment of evaluation requests.

Fixed request groups/denominators and identical-served-ID waits retain
allocation and spillovers. `baseline_eligible` is the unchanged0.3 opted-in,
in-fence set; `additional_opt_in` is the in-fence non-opted set throughout this
study; `outside_fence` never qualifies. Served-only waits can change composition.
Accepted promises must fit the original request-clock480s cutoff, every accepted
rider completes, and actual late pickup outcomes remain recorded. Occupied
utilization clips physical occupancy to evaluation time; empty distance includes
warm-up and fulfillment tails.

## Reproduce

Build the nine tracked [anchored city configs](fleet_share), then run each share:

```bash
.venv/bin/python -m tools.city_av build \
  --config docs/fleet_share/chicago_s5.json \
  --data-root /workspace/market_inputs/cross_city/chicago/FleetPy_Chicago \
  --output /workspace/market_inputs/share_run/chicago_s5

.venv/bin/python -m tools.city_av run \
  --bundles /workspace/market_inputs/share_run/munich_s5 \
            /workspace/market_inputs/share_run/chicago_s5 \
            /workspace/market_inputs/share_run/manhattan_s5 \
  --policies docs/fleet_share/policies.json --seeds 0 1 2 --workers 1 \
  --output /workspace/market_results/share_run/s5

.venv/bin/python -m tools.city_av.fleet_share \
  --experiments /workspace/market_results/share_run/s5 \
                /workspace/market_results/share_run/s10 \
                /workspace/market_results/share_run/s20 \
  --output /workspace/market_results/share_run/report
```

Build corresponding s10/s20 and separate legacy configs with the same source
roots declared in the work log. Manhattan uses the immutable Phase9 parent
recorded in its config. Build fresh manifests under frozen source; existing
outputs and retagged historical data are refused. The ordinary summary rejects
mixed fleet-share/input assumptions. Exact commands, statuses, dependencies,
native/source/input/output hashes and all physical raw histories are retained in
the [work log](WORK_LOG.md) and final evidence.

Three seeds on fixed source cohorts establish conditional sensitivity, not
population uncertainty, calibrated AV supply or daily throughput. Munich is
AIMSUN-derived simulated demand, Chicago the supplied TNC subsample and
Manhattan the fixed TLC cohort with its source pooling consent. City, year,
source generation, load and network differ; no geography-only effect is claimed.

## Validation and measured results

**465 tests pass** in 2371.99s, with no failures,
errors or skips. This includes **441 complete regression simulations and32
restored windows**. All396 previous full cases preserve **3074 checked
tables byte for byte**, and128 window tables retain exact values.

All **99 real physical runs** pass:81 anchored settings, nine anchor pilot/
replay records and nine separate legacy bridge settings. All nine legacy
controls reproduce84 historical files including reports. The anchored90 records
pass independent event sweeps; legacy raw trajectories reproduce previously
sweep-verified bytes. All60 within-study and54 cross-share background checks
pass; actual positions/SOC match across shares, and18 all-human comparisons
retain search-partition outcomes. All270 physical fixed-group rows match
independent calculations. All accepted bookings complete, valid promises fit
the480s source-clock cutoff and actual late pickups remain recorded.

The following threshold240 means use three initialization seeds on each fixed
source cohort. Per-driver metrics use the same human IDs at every share.

| City | Requested AV % | AV count | Completed | AV trips | AV occupied % | Eligible served wait s | Fixed human trips/hour | Fleet empty km |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| chicago | 5 | 5 | 539.67 | 18.33 | 62.36 | 313.68 | 1.93 | 712.03 |
| chicago | 10 | 10 | 528.67 | 32.67 | 56.10 | 316.58 | 1.89 | 714.35 |
| chicago | 20 | 20 | 499.33 | 55.33 | 45.11 | 312.30 | 1.85 | 699.48 |
| manhattan | 5 | 39 | 2432.33 | 88.33 | 25.74 | 255.97 | 1.09 | 1426.23 |
| manhattan | 10 | 78 | 2410.67 | 132.33 | 20.21 | 255.98 | 1.10 | 1429.02 |
| manhattan | 20 | 155 | 2376.00 | 179.67 | 14.18 | 215.27 | 1.18 | 1446.19 |
| munich | 5 | 2 | 569.00 | 12.00 | 46.02 | 303.18 | 3.89 | 1061.10 |
| munich | 10 | 5 | 548.33 | 25.00 | 38.78 | 303.79 | 3.91 | 1059.88 |
| munich | 20 | 10 | 508.00 | 43.33 | 33.75 | 289.47 | 3.87 | 984.98 |

Changes in mixed-minus-matched-human completion, relative to anchored10%:

| City | Requested AV % | Policy | Adjusted completion change | Conditional paired95% interval |
| --- | --- | --- | --- | --- |
| chicago | 5 | threshold_0 | +18.33 | [-70.03, +106.70] |
| chicago | 5 | threshold_240 | +39.67 | [+17.96, +61.37] |
| chicago | 20 | threshold_0 | -54.00 | [-105.33, -2.67] |
| chicago | 20 | threshold_240 | -37.33 | [-186.39, +111.72] |
| manhattan | 5 | threshold_0 | +22.67 | [+5.04, +40.29] |
| manhattan | 5 | threshold_240 | +23.33 | [+19.54, +27.13] |
| manhattan | 20 | threshold_0 | -47.33 | [-89.07, -5.59] |
| manhattan | 20 | threshold_240 | -34.33 | [-55.02, -13.65] |
| munich | 5 | threshold_0 | +17.00 | [+1.49, +32.51] |
| munich | 5 | threshold_240 | +20.67 | [-8.34, +49.67] |
| munich | 20 | threshold_0 | -40.33 | [-90.53, +9.86] |
| munich | 20 | threshold_240 | -40.33 | [-58.98, -21.69] |

These conditional intervals describe three initialization seeds, not population
uncertainty. Human-only outcomes retain changing shadow-search partitions;
adjusted comparisons do not remove every interaction. Direct composition
changes, within-share threshold contrasts, fixed human/request groups,
same-served-ID waits and the separate one-seed placement bridge remain in the
[full results](validation/phase16/RESULTS.md) and
[robustness assessment](validation/phase16/ROBUSTNESS.md).
[Complete evidence/restoration](validation/phase16/README.md) and the
[work log](WORK_LOG.md) record every command, change, reason, benefit, adverse
outcome and source/input/output hash. This phase improves experimental control
and robustness evidence; no optimal observed AV supply or field superiority is
established.
