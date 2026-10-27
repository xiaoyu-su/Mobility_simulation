# Phase 13: Chicago threshold and speed mechanisms

The supplied plan explicitly leaves Chicago's non-monotone AV result open.
This phase adds a read-only diagnostic report and a prespecified matched study
of threshold, cautious speed and fleet load. It improves accounting and
interpretability. It does not change the matching policy or fit the screenshot's
numerical results.

## Study and physical checks

Chicago's provided June 2022 TNC subsample and 2023 network remain the inputs.
The source cohort has 2,690 requests: 639 warm-up and 2,051 evaluation requests.
Evaluation runs from 07:00 to 10:00; warm-up starts at 05:00 in source-clock
seconds. All accepted bookings continue to actual physical fulfillment.

- Total fleets: 100 and 200, with 10% AV replacement.
- Threshold allowances: 0, 120, 240 and 480 seconds.
- AV travel-time factors: 1.0 and 1.25; 1.25 means 25% longer driving time.
- Initialization seeds: 0, 1 and 2. Opt-in remains 0.3 per request.
- Human acceptance, human/AV repositioning and execution noise stay off.
- Source requests, endpoint fence, patience/service assumptions, search budgets,
  actual initial geometry/SOC and named random streams stay matched within a
  fleet/seed. Doubling the fleet changes its roster and initialization; comparisons
  across fleet sizes are a configured load sensitivity.

The main study plans 54 unique conditions: 48 AV cases and six matched all-human
controls. Ten pilot cases repeat main conditions and remain separately checked
fresh-process evidence. They do not increase the independent sample count.

The new integration checks run both immediate insertion controllers and the
native C++ router, complete all bookings, reconstruct actual passenger events,
preserve every raw byte during analysis, and verify deterministic replays.
Changed evidence, duplicate conditions and existing report destinations fail
closed. Full regression and real-study completion are reported below only after
actual gates finish.

## Exact accounting

For each AV, user pickup and dropoff timestamps mark the start of boarding and
alighting. Raw occupancy retains the outgoing passenger through alighting end.
Passenger journey duration and logged passenger-holding duration therefore have
an explicit service-time difference.

The report independently checks two identities:

1. The union of actual pickup-to-alighting-end intervals equals logged occupied
   vehicle time. Their passenger-weighted exposure equals raw occupancy time.
2. Occupied vehicle seconds equal full evaluation-cohort passenger seconds,
   minus pre/post-window portions, plus warm-up passenger seconds inside the
   clock, plus logged alighting dwell, minus logged passenger overlap.

Logged overlap includes shared moving loads, stationary incoming/outgoing event
unions and multi-passenger bookings. It is not solely a pooling effect.
For paired policies, the full evaluation passenger-time product is decomposed
symmetrically into average duration × count change and average count × duration
change. This allocates the interaction exactly; timing/service/overlap terms
then reconcile the actual occupied-utilization change without a residual.
Zero completions use a zero duration factor solely for that algebra, not an
invented observed journey duration.

Per-request rows retain final AV/human/unserved product, eligibility, source
clock, actual pickup/dropoff/alighting endpoint, wait, duration and the last
recorded retained-candidate reason. Nine product transitions partition each
paired evaluation cohort. Common-served wait comparisons use the same request
IDs. The 900-second bins distinguish unique arrivals, actual pickups, occupied
time and decision events; repeated decision events are not unique passengers.

Candidate ETAs describe each policy's own observed fleet history and bounded
retained search. Missing retained candidates do not prove global infeasibility.
An exact accounting contribution is not an identified causal mediator or an
empirical AV deployment effect. Three initialization seeds on one fixed source
cohort provide limited uncertainty. The inherited patience, adoption, fleet,
fence, source-generation/year and empirical calibration limits remain open.

## Reproduce

Tracked inputs are in [city_mechanisms](city_mechanisms/chicago.json).
Build fresh bundles under the current source; do not retag older datasets.
Use `--fleet-multiplier 2` for the second bundle. Existing output paths are
refused by both experiments and diagnostics.

```bash
.venv/bin/python -m tools.city_av build \
  --config docs/city_mechanisms/chicago.json \
  --data-root /workspace/market_inputs/cross_city/chicago/FleetPy_Chicago \
  --output /workspace/market_inputs/phase13_run/chicago100

.venv/bin/python -m tools.city_av run \
  --bundles /workspace/market_inputs/phase13_run/chicago100 \
  --policies docs/city_mechanisms/policies.json --seeds 0 1 2 \
  --workers 1 --output /workspace/market_results/phase13_run/main

.venv/bin/python -m tools.city_av.mechanism \
  --experiments /workspace/market_results/phase13_run/main \
  --output /workspace/market_results/phase13_run/analysis
```

Analyze separate replay studies separately: duplicate conditions are deliberately
rejected by the accounting CLI. The publication audit checks replays against
main raw outputs without treating them as new conditions. Every source/input/
output/configuration/runtime hash, exact command, failure and correction is
retained in the [work log](WORK_LOG.md) and final evidence.

## Validation and measured results

**433 tests pass** in 2188.83 seconds, with no failures,
errors or skips. This covers **324 full regression simulations and 32 restored
windows**. All **64 real physical runs** pass: 54 unique conditions and ten exact
fresh-process replays. All 306 earlier full cases retain
**2234 checked tables byte for byte**, and 128 window tables
retain exact values. All 23 matching historical real controls retain
**195 critical file comparisons**.

The independent event-sweep audit reconciles all occupied/passenger exposure;
all 60 main paired accounting contrasts close. Original module outputs and
supplementary derivatives have separately verified input/output hashes.

The following are means over three initialization seeds. Each arrow compares
threshold 0→240 at the same speed, fleet, source cohort and initialization.

| Fleet | AV travel-time factor | Total completed | AV bookings | AV occupied % | Mean AV pickup-to-dropoff s | Fleet empty km |
| --- | --- | --- | --- | --- | --- | --- |
| 100 | 1.25 | 536.00→547.00 | 23.00→29.33 | 36.18→53.87 | 1691.82→2010.49 | 693.07→727.31 |
| 100 | 1 | 531.67→535.67 | 30.67→44.67 | 40.40→53.03 | 2031.77→1756.41 | 674.64→725.57 |
| 200 | 1.25 | 1212.00→1208.67 | 71.33→60.67 | 41.05→48.79 | 1381.28→1906.93 | 1214.43→1218.47 |
| 200 | 1 | 1269.00→1208.33 | 86.00→96.00 | 37.18→52.88 | 1240.63→1706.25 | 1242.03→1237.43 |

These results retain lower completion and additional empty driving alongside
favorable effects. A utilization increase does not establish a service gain.
See [full results](validation/phase13/RESULTS.md), the
[same-request/selection and moving-overlap analysis](validation/phase13/REQUEST_COMPOSITION.md),
and [complete evidence/restoration](validation/phase13/README.md).
