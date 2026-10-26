# Phase 12: demand-based AV repositioning across cities

This implements the per-city AV repositioning follow-up documented in the
supplied plan and [Phase 11](PHASE_11.md). The existing mixed-fleet policy is
compared on Munich, Chicago and Manhattan with AV repositioning off/on and
threshold allowances of 0/240 seconds. Human acceptance and human repositioning
remain off. Fleet replacement, initial positions/SOC, search budgets, type speed,
source demand and assumed opt-in stay matched within a condition.

Final expanded focused validation passes **78 tests and 77 complete physical
simulations**. The full suite passes **424 tests** in **2449.99s**,
covering **306 complete regression simulations and 32 restored windows**.
All **72 real policy runs** pass (63 unique conditions plus nine exact replays).
All 269 historical complete regression cases preserve
**1596 checked tables byte for byte**; 128 window tables retain exact
values. All 26 matched historical real-control conditions preserve
**214 critical file comparisons**. [WORK_LOG.md](WORK_LOG.md) preserves
each change, reason, intended benefit, failed check, correction and actual result.

## Separate-reference spatial weights

The explicit configuration option
`av_repositioning_forecast: reference_od_stationary_v1` enables forecast inputs
in `tools.city_av build`. Existing configurations retain their previous output
shape and default behavior.

The builder retains every approved reference identity, clock and mapped origin/
destination zone. It filters both endpoints through the existing AV fence,
then repeats those relative origin/destination counts in 900-second intervals.
These are stationary spatial weights for target apportionment, **not calibrated
future trip volumes**. Uniform assumed opt-in changes mass and cancels from the
spatial target proportions. No request from warm-up/evaluation contributes to
these weights; tests perturb those rows and require unchanged reference and
forecast bytes. Empty eligible references and invalid/future dates fail closed.

| City | Separate reference | Mapped reference rows | Eligible OD rows |
| --- | --- | --- | --- |
| Munich | Native pickups 00:00–05:00, before warm-up | 88 | 23 |
| Chicago | Native pickups 00:00–05:00, before warm-up | 981 | 651 |
| Manhattan | Verified prior November 2019 Tuesdays | 63441 | 15951 |

Native references are sparse and come from a different clock period than peak
evaluation. Manhattan has much more prior data. Reference-generation, geography,
load and source-year differences prevent a geography-only causal claim. The
framework exposes these assumptions; it does not claim to resolve empirical
patience, fleet supply, adoption or held-out travel-time calibration.

Source data/network provenance, filtering, privacy consent, service durations,
causal request admission and the data-derived fence remain as in
[Phase 10](PHASE_10.md). The immutable old Manhattan dataset is rebuilt into a
new comparison bundle, never retagged. Forecaster/reference files and the native
runtime are hashed; raw inputs remain independently verifiable.

## Passenger service preempts soft AV targets

The first real pilot exposed a planning gap: Chicago recorded **8 occupied
repositioning legs /18.986561km**. Insertion could keep an unlocked empty-vehicle
waypoint between a passenger pickup and drop-off. A positive worker exit and
complete bookings did not establish the intended empty repositioning policy.
The physical audit blocked publication and later studies.

New opt-in `op_av_service_priority` removes cancellable AV target stops from a
**copy** before passenger feasibility, pickup ETA and utility/delta are evaluated.
The selected passenger tour then replaces the old idle target. This applies to
both immediate insertion controllers, including shared insertion in native batch
vehicle copies. Explicit locks, end locks and infeasible-lock flags are retained;
the live plan and its cached utility are not mutated while considering an offer.
The generic policy defaults remain unchanged unless the flag is enabled.

The city runner enables `--av-service-priority on` for its AV-repositioning arms.
No-repositioning/all-human controls receive no such override. The AV audit
records actual committed service preemptions separately from candidate plans.
Tests reproduce the old waypoint behavior, require empty movement with priority,
and combine it with private service, human acceptance/future value/shifts,
forecast noise, retargeting and joint planning on both insertion controllers.
The original source's generic human repositioning behavior is outside this
AV-only safeguard. Global batch threshold dispatch remains unsupported.

## Physical interpretation and comparisons

`city_repositioning_contract.json` checks the loaded forecast hash, every callback,
actual separate-reference weights, fleet target apportionment and unique AV-only
fenced centroid commands. It traces each physical repositioning leg to its
preceding command, requires zero onboard passengers and rejects human movement.
Target arrivals and interrupted legs are recorded separately. A command may be
superseded before movement and is not itself counted as feature exercise. No
passenger-preemption cause is inferred solely from an interrupted endpoint.

Full unique demand, accepted booking completion, actual boarding/alighting,
chronology, physical service, capacity, source privacy, opt-in/fence and accepted
product remain mandatory. Actual movement is checked in addition to intent logs.
Higher occupied utilization is not automatically more completed trips or better
service; absolute empty kilometers and common-served-rider waits are retained.

| Study | Seeds | Conditions | Physical runs |
| --- | --- | --- | --- |
| Main | 0,1,2 | Three cities; all-human and thresholds 0/240 crossed with AV repositioning off/on | 45 |
| Supply | 0,1,2 | Munich100 and Chicago200; all-human and threshold 240 off/on | 18 |
| Pilot/replay | 0 | Three main fleets; all-human and threshold 240 off/on | 9 |

There are 63 distinct city/fleet/seed/policy conditions; nine pilots repeat main
conditions and do not increase the independent sample count. Main total fleets
are 50 Munich,100 Chicago,775 Manhattan. Supply doubles both types at fixed AV
share; across fleet sizes slot IDs/starting layouts also change, so this is a
configured load sensitivity. It is not an identical-background capacity effect.
Three initialization seeds still provide limited uncertainty for one fixed cohort.

## Reproduce

Tracked configurations are in [city_repositioning](city_repositioning/munich.json).
The corresponding Chicago/Manhattan configurations and both policy grids use
the same CLI. Use existing public data roots recorded in Phase10 evidence.
Existing output destinations are refused.

```bash
.venv/bin/python -m tools.city_av build \
  --config docs/city_repositioning/munich.json \
  --data-root /workspace/market_inputs/cross_city/munich/FleetPy_Munich \
  --output /workspace/market_inputs/phase12_run/munich

.venv/bin/python -m tools.city_av run \
  --bundles /workspace/market_inputs/phase12_run/munich \
            /workspace/market_inputs/phase12_run/chicago \
            /workspace/market_inputs/phase12_run/manhattan \
  --policies docs/city_repositioning/policies.json \
  --seeds 0 1 2 --workers 2 --timeout 7200 \
  --output /workspace/market_results/phase12_run/main

.venv/bin/python -m tools.city_av report \
  --experiments /workspace/market_results/phase12_run/main \
                /workspace/market_results/phase12_run/supply \
                /workspace/market_results/phase12_run/pilot \
  --output /workspace/market_results/phase12_run/report
```

Use `--fleet-multiplier 2` to build the supply bundles. Each child is pinned to
one permitted logical CPU with one BLAS/OMP/MKL thread. Source, configurations,
inputs, initial geometry and raw outputs remain guarded throughout comparisons.
CSV tables retain paired effects and identical-served-rider wait differences;
scientific PNG/PDF shows completion, utilization, waits and absolute empty-distance
changes with paired-seed ranges. All gains and adverse outcomes are reported.

## Final measured results

| City | Fleet | Threshold 240 OFF→ON completion | AV trips | AV occupied % | Eligible served wait s | Fleet empty km |
| --- | --- | --- | --- | --- | --- | --- |
| munich | 50 | 556.00→551.67 | 25.67→21.00 | 39.53→36.90 | 302.44→309.73 | 1033.37→1102.90 |
| chicago | 100 | 547.00→549.33 | 29.33→40.33 | 53.87→59.09 | 311.52→320.53 | 727.31→1252.75 |
| manhattan | 775 | 2441.00→2482.33 | 134.00→175.67 | 20.40→27.01 | 257.34→245.70 | 1438.85→1908.51 |
| munich | 100 | 1050.33→1052.33 | 46.67→52.33 | 33.08→36.93 | 303.80→299.78 | 1780.24→1944.97 |
| chicago | 200 | 1208.67→1296.00 | 60.67→107.67 | 48.79→57.07 | 284.79→276.86 | 1218.47→2283.14 |

These are means over three initialization seeds for each fixed source cohort.
Paired uncertainty and identical-served-rider comparisons are retained separately.
Opposite seed/city directions and additional empty driving are part of the result.
Higher utilization does not by itself establish better service, and fixed-fleet
replacement does not add capacity. The screenshot's historical figures remain
reference claims, not fitted acceptance targets.

[Full results](validation/phase12/RESULTS.md) retain every condition, paired
contrasts, actual passenger durations, preemption/physical-movement evidence,
gains and adverse outcomes. [Evidence and restoration](validation/phase12/README.md)
includes failed/corrected checkpoints and immutable source/input/output records.
