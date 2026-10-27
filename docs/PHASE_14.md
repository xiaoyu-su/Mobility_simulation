# Phase 14: booking-patience robustness across cities

The supplied plan identifies unverified rider patience as a major completion
assumption. This phase adds matched 4/8/12-minute sensitivity reporting across
Munich, Chicago and Manhattan. It strengthens input-contract checks, distinguishes
accepted-offer limits from actual timing, and measures robustness without fitting
observed cancellation behavior or changing a matching policy.

## Prespecified study

| City | Total fleet | Designated AVs | Warm-up requests | Evaluation requests |
| --- | --- | --- | --- | --- |
| Munich | 50 | 5 | 631 | 1892 |
| Chicago | 100 | 10 | 639 | 2051 |
| Manhattan | 775 | 78 | 751 | 3150 |

Source, fleet and native load assumptions remain those of the prior city studies.
For each city, assumed booking cutoffs are 240/480/720 seconds; initialization
seeds are 0/1/2; policies are all-human and cautious AV threshold0/240. AV opt-in
is 0.3 per request and travel-time factor is 1.25. Human acceptance, human/AV
repositioning and execution noise remain off. The rounded AV slots replace
human slots at fixed total fleet; they do not add supply.

There are 81 unique city/patience/seed/policy conditions. Nine seed0 baseline480s
pilots repeat main conditions and are verified separately as exact fresh-process
replays. These repetitions do not increase the independent condition count.
The grid and fixed 480-second actual-pickup target were declared before new real
outcomes. Source-generation/year, geography and fleet/load differ across cities;
this is not a geography-only causal experiment.

## What patience means here

The existing traveler/planning model bounds an accepted offer by the request's
latest pickup time, anchored to original source time. Actual traffic/execution
and later plans can produce timing error after acceptance. All accepted bookings
must still physically complete; this phase does not silently cancel committed
passengers or relabel a late arrival as on-time service.

The report requires all recorded accepted pickup promises to fit the declared
source-clock deadline. It separately records actual pickup lateness, excess
seconds, actual and offered wait, and full versus evaluation-cohort late counts.
A baseline exploratory check found late actual pickups despite valid offers;
the nine real pilots retain 65 late evaluation pickup records (115 including
warm-up), across counterfactual runs rather than unique real-world passengers.

`within_limit_completed` uses each stratum's own cutoff. The additional
`within_480s_completed` fixes one common actual-pickup target across every
stratum, so relaxing the cutoff does not redefine the service-quality target.
Neither metric identifies a real rider's willingness to wait. Completed-trip
records lack unserved requests, online supply and cancellation observations.

## Controlled inputs and physical validation

Across cutoffs, every byte of the source cohort, initial distribution, vehicle
specification, source consent/service, fence/mapping, network and runtime must
match. Only `op_max_wait_time` and source-clock request deadline values change.
Actual starting geometry/SOC and typed named-stream backgrounds are checked.
Demand-file audit hashes intentionally differ because deadline bytes change;
non-deadline demand columns are independently compared exactly.

The ordinary city summary now rejects incompatible input assumptions for a
city/fleet and verifies its input snapshot. Use `tools.city_av.patience` to report
explicit cutoff strata. Different cutoffs are not seed repetitions or replays.
Valid ordinary reports keep their previous output format.

Physical checks include unique complete demand, accepted pickup/dropoff and
fulfillment tails, actual boarding/alighting, chronological vehicle activity,
capacity before/after exchanges, privacy, opt-in/fence/product, loaded effective
travel-time factors, and independent time accounting. A zero exit code or an
intent log alone is insufficient. Both immediate controllers and native C++
routing are exercised, including deterministic cutoff and replay probes.

The controlled probe is unreachable within 240 seconds but feasible under
480/720 seconds. Its cohort and initial states are identical across cutoffs.
It completes one evaluation request at 240s and two at 480/720s, for all three
policies on both controllers and C++ routing. Analysis preserves raw bytes and
rejects tampered inputs, uncontrolled assumptions and existing output targets.

## Reproduce

Tracked [configurations](patience/study.json) list all nine city/cutoff bundles,
the fixed policy grid and seeds. Build fresh bundles under the tested source;
never retag an older dataset. For example:

```bash
.venv/bin/python -m tools.city_av build \
  --config docs/patience/chicago_p240.json \
  --data-root /workspace/market_inputs/cross_city/chicago/FleetPy_Chicago \
  --output /workspace/market_inputs/patience_run/chicago_p240

.venv/bin/python -m tools.city_av run \
  --bundles /workspace/market_inputs/patience_run/munich_p240 \
            /workspace/market_inputs/patience_run/chicago_p240 \
            /workspace/market_inputs/patience_run/manhattan_p240 \
  --policies docs/patience/policies.json --seeds 0 1 2 --workers 1 \
  --output /workspace/market_results/patience_run/p240

.venv/bin/python -m tools.city_av.patience \
  --experiments /workspace/market_results/patience_run/p240 \
                /workspace/market_results/patience_run/p480 \
                /workspace/market_results/patience_run/p720 \
  --output /workspace/market_results/patience_run/report
```

Build the corresponding 480/720-second and other-city inputs with their tracked
configs. Manhattan uses the immutable Phase9 parent declared in its config;
Munich uses the existing public FleetPy Munich source root. Exact build/run
commands, data provenance, dependency/native hashes, statuses, CPU/thread
settings, source snapshots, raw histories and failures are retained in the
[work log](WORK_LOG.md) and final evidence. Existing outputs are refused.

Policy effects are compared within a fixed cutoff. Cutoff effects hold policy
fixed against the baseline480s assumption. Both retain paired seed uncertainty
and waits for the same served request IDs. Aggregate served-only waits can
change composition. Non-monotone completion or worse waits/empty driving are
reported, not tuned away. Three seeds on one cohort do not establish population
uncertainty or empirical AV/patience calibration; daily AV throughput is not
extrapolated from these partial-day benchmarks.

## Validation and measured results

**442 tests pass** in 2117.93 seconds, with no failures,
errors or skips. This covers **360 complete regression simulations and 32
restored windows**. All **90 real physical records** pass: 81 unique conditions
and nine exact fresh-process replays. All 324 previous full cases preserve
**2402 checked tables byte for byte**; 128 window tables retain
exact values. All 27 historical default-cutoff controls preserve
**225 critical file comparisons**.

All accepted promises fit their source-clock booking cutoff and all accepted
bookings physically complete. Actual late pickups remain visible. Independent
event sweeps, controlled-input checks, native runtime and raw hashes pass.

The following threshold240 results are means of three initialization seeds on
one fixed source cohort per city. The 480-second actual-pickup target is fixed
across every row, while the assumed offer cutoff varies.

| City | Booking cutoff s | Completed | Within fixed 480s | AV trips | Eligible served wait s | Late actual pickups | Fleet empty km |
| --- | --- | --- | --- | --- | --- | --- | --- |
| munich | 240 | 382.67 | 382.67 | 7.33 | 160.05 | 1.33 | 510.54 |
| munich | 480 | 556.00 | 554.67 | 25.67 | 302.44 | 1.33 | 1033.37 |
| munich | 720 | 581.33 | 213.00 | 31.67 | 487.77 | 8.00 | 1213.54 |
| chicago | 240 | 445.67 | 445.67 | 18.00 | 153.57 | 1.33 | 341.54 |
| chicago | 480 | 547.00 | 543.67 | 29.33 | 311.52 | 3.33 | 727.31 |
| chicago | 720 | 536.67 | 223.33 | 35.00 | 470.42 | 6.67 | 890.68 |
| manhattan | 240 | 1762.33 | 1762.33 | 91.33 | 143.65 | 6.67 | 696.24 |
| manhattan | 480 | 2441.00 | 2423.33 | 134.00 | 257.34 | 17.67 | 1438.85 |
| manhattan | 720 | 2707.33 | 1924.33 | 152.67 | 329.28 | 19.67 | 1862.68 |

Threshold0→240 at each fixed booking cutoff:

| City | Cutoff s | Completion change | Fixed 480s service change | AV trip change | Same-served eligible wait change s | Empty km change |
| --- | --- | --- | --- | --- | --- | --- |
| chicago | 240 | -4.00 | -4.00 | -1.67 | +7.65 | -1.27 |
| chicago | 480 | +11.00 | +11.33 | +6.33 | +13.17 | +34.24 |
| chicago | 720 | -1.67 | -5.67 | +3.67 | +14.47 | +32.30 |
| manhattan | 240 | +16.67 | +16.67 | +32.33 | +22.66 | +18.58 |
| manhattan | 480 | +5.00 | +6.33 | +50.67 | +61.57 | +20.28 |
| manhattan | 720 | +5.00 | +9.00 | +55.67 | +62.84 | +24.62 |
| munich | 240 | -3.67 | -3.67 | -1.33 | +5.27 | -7.88 |
| munich | 480 | -1.00 | +0.33 | +2.33 | +21.55 | +8.07 |
| munich | 720 | +5.67 | -5.33 | -2.67 | +9.71 | +28.77 |

All favorable and adverse directions, paired seed intervals, actual lateness
and common-served counts remain in [full results](validation/phase14/RESULTS.md)
and the [robustness assessment](validation/phase14/ROBUSTNESS.md).
[Evidence/restoration](validation/phase14/README.md) and the
[work log](WORK_LOG.md) retain every source/input/output/command and checkpoint.
More completed trips under a looser assumption do not establish more service
within a common timing target or empirically calibrated patience.
