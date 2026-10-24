# Phase 4: future-value matching

Phase 3 weights a proposed request's assignment reward by its selected driver's
acceptance probability. Phase 4 optionally includes an estimate of the chance
that another nearby driver would accept if the first declines. It changes
matching value without sending offers to those alternative drivers.

## Score and configuration

```text
fallback_i = 1 - product(1 - p_j) over the top-k other candidate drivers
served_value_i = p_i + (1 - p_i) × fallback_i
objective = original operating/traveler cost - R × sum(served_value_i)
```

`p_i` uses the selected plan's pickup time and Phase 3 driver coefficients.
Each `p_j` uses the alternative driver's direct pickup ETA, direct passenger
trip distance, and that driver's own class coefficients. Probabilities are for
one offer each. Chaining assumes conditional independence. Phase 3's existing
retry policy remains unchanged; this score is not an exact service probability
under multiple retries, pooled-route constraints, or competing requests.

Only uncommitted requests receive this reward change. Committed/onboard riders
keep the full original reward. Operating/traveler cost terms are unchanged.
The score is bounded between `p_i` and 1. Stable `log1p`/`expm1` arithmetic
preserves very small fallback probabilities and handles probability 0 or 1.

| Operator parameter | Default | Meaning |
| --- | --- | --- |
| `op_driver_acceptance_future_value` | `False` | Enable the fallback-value reward |
| `op_driver_acceptance_future_value_top_k` | `5` | Nonnegative number of other drivers used in the estimate |

Enabling requires `op_driver_acceptance=logistic` and
`op_driver_acceptance_weight_objective=True`. As in Phase 3, reward weighting
supports `distance_and_user_times_with_walk`, used by the three baseline
controllers. Missing prerequisites and invalid enabled top-k values fail clearly.

The default keeps Phase 3's exact path, without extra future-value files or
routing calls. `top_k=0` reproduces the Phase 3 score and decisions exactly.
Fixed acceptance probability 1 retains upstream results and makes no fallback
routing queries. Fixed probability 0 gives zero reward and no fallback queries.

## Candidate definition and exact selection

Each matching round freezes live vehicle IDs, positions, status, and total
passenger capacity. A potential alternative must have a position, be active
(not `OUT_OF_SERVICE`), have sufficient total passenger capacity, and be
reachable by the request's latest pickup time. Its pickup delay is

```text
eta_j = max(0, road_travel_time(current_position_j, pickup), earliest_pickup - now)
```

Candidates are ranked by `(eta_j, vehicle_id)`. Ties are deterministic, and
colocated drivers remain distinct. The selected driver is excluded before
taking k alternatives. No Euclidean/geographic prefilter is used. Road-network
travel times include partial-edge positions; unreachable or invalid negative
route-time results are excluded.

This is a reachability proxy. For busy drivers, direct pickup time ignores
their outstanding tour, capacity changes at intermediate stops, charging/depot
constraints, and possible conflicts with other requests. The method therefore
can be optimistic. It neither proves that each alternative has a feasible
insertion nor reserves that driver. Feasibility of the actually selected plan
continues to use the existing matcher. Actual multi-driver offer dispatch,
conflict resolution, and forbid/rematch behavior remain later phases.

## Cache and runtime behavior

The first relevant query ranks all eligible vehicle positions using exact
one-to-one road-routing times. Colocated vehicles share that route query.
`heapq.nsmallest(k+1, ...)` retains enough candidates for every possible
selected-driver exclusion. Later evaluations reuse this shortlist and cached
fallback probabilities rather than scanning/routing the fleet for every plan.

Matching-round boundaries explicitly clear the cache and refresh the fleet,
including successive requests at the same simulation time. A new simulation
time/routing-engine context also refreshes automatically. Candidate cache keys
include pickup position, earliest/latest pickup, and request size. Fallback
keys additionally include direct trip distance and the excluded driver.
The cache does not retain every fleet route for every request across the day.

The first query still scans the fleet; this is not a sublinear routing index.
The optimization removes repeated full scans across candidate-plan evaluations.
Exactness is tested against an independent full scan/sort, including partial-edge
positions on the actual example road network. A benchmark records query counts,
score differences, and wall time separately; timing is descriptive and is not
a test assertion or a city-scale runtime claim.

Reproduce the recorded microbenchmark with a fresh output path:

```bash
.venv/bin/python -m tools.benchmark_future_value \
  --vehicles 32 --requests 12 --repetitions 5 --top-k 5 \
  --output /tmp/fleetpy-phase4-benchmark.json
```

The sampled workload includes disconnected routes. The existing router
recalculates infinite-path results in repeated full scans, which affects the
measured timing ratio. Route-query counts and score agreement are the primary
evidence; the runtime ratio should not be generalized to other workloads.

## Actual decisions and audit files

Scoring is deterministic and consumes no acceptance, demand, initialization,
optimizer, or execution-noise draws. Actual driver acceptance continues to use
`p_i`, not the inflated served value. Alternative drivers receive no offers.
Existing terminal-decline handling and committed-rider protection remain intact.

Enabled operators add:

- `future_value_op_N.csv`: one row at the first selected-driver decision,
  before acceptance sampling. Records matching round/time, operator/vehicle/
  request IDs, selected-plan pickup delay, `p_i`, fallback, served value, and
  alternative IDs/ETAs. It does not log every optimizer candidate plan.
- `future_value_op_N.json`: settings, formula, candidate definition, modeling
  limits, and counters for rounds, value evaluations, candidate queries/cache
  hits, fallback cache hits, and routing queries. Final counters are flushed
  with the operator's forced final statistics record.

At `p_i=1`, fallback is not evaluated because it cannot change the score; its
record is missing, with `fallback_evaluated=False`. A known zero fallback is
recorded as zero. The normal `skip_file_writing` option suppresses these files.
The existing paired reports continue to measure completed requests, driver
decisions, service times, accounting, and distributions. Internal score/counter
diagnostics are retained separately from these realized outcomes.

## Run a matched comparison

The supplied candidate differs from the Phase 3 insertion example only by
scenario name and future-value settings. Both use the same explicitly
illustrative coefficients; this is not an empirical calibration.

```bash
.venv/bin/python -m tools.paired_eval \
  --constant-config studies/example_study/scenarios/constant_config_ir.csv \
  --baseline-scenarios studies/example_study/scenarios/example_ir_driver_acceptance.yaml \
  --candidate-scenarios studies/example_study/scenarios/example_ir_future_value.yaml \
  --network-tt-noise-sigma 0.3 \
  --seeds 0 1 2 \
  --output /tmp/fleetpy-phase4-insertion
```

For heterogeneous-class batch matching, substitute `constant_config_pool.csv`,
`example_batch_driver_classes.yaml`, and `example_batch_future_value.yaml`
for the corresponding files. Use a new output directory every time. Check
completion counts alongside conditional wait/error metrics; estimates of future
value are not evidence that the fallback opportunities actually execute.

## Verification and scope

```bash
.venv/bin/python -m pytest -q
```

Checks cover analytical scores/costs, committed riders, exact top-k versus
full scans, exclusion/ties/colocation, earliest/latest pickup, unavailable and
unreachable candidates, snapshot refresh, cache reuse, partial-edge routing,
numerical boundaries, and output suppression. The full examples exercise all
three controllers at p=1, k=0, and noisy logistic acceptance. Paired CLI runs
check identical-policy repeatability and controlled Phase 3/4 comparisons for
insertion and heterogeneous-class Alonso-Mora matching.

Validated scope remains the three single-worker baseline road-trip controllers
on example data. The model is a matching-value approximation, not calibrated
long-run value, actual fallback dispatch, a joint allocation probability, or a
new repositioning policy. Complete checkpoints, results, changes, reasons, and
benefits are in [WORK_LOG.md](WORK_LOG.md); evidence is archived under
`docs/validation/phase4/`.
