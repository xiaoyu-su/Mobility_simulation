# Phase 5b: ranked insertion fallback

This opt-in phase implements the next dispatch step from the uploaded plan:
walk the feasible insertion candidates cheapest-first, offer once to each
distinct driver, and execute the first accepted plan. A declined proposal is
never assigned. If all retained drivers decline, reject the request once.

Alonso-Mora request/vehicle edge prohibition and optimizer rematching remain
Phase 5c. This phase does not inject alternative plans into a batch solution.
The immediate-insertion controller that periodically reoptimizes its existing
bookings uses its normal supported booking/assignment path.

## Configuration

| Parameter | Requirement |
| --- | --- |
| `op_driver_acceptance_ranked_fallback` | Boolean, default false; explicit opt-in |
| `op_driver_acceptance` | `logistic` when fallback is enabled |
| `op_driver_acceptance_max_declines` | Must be 0: one offer per candidate driver |
| `op_driver_choice_model` | Optional: off, singleton, or logit; insertion offers are singletons |
| `op_module` | `PoolingIRSOnly` or `PoolingIRSAssignmentBatchOptimization` |
| simulation/traveler | `ImmediateDecisionsSimulation` and `BasicRequest` |

Driver classes, probability-weighted objectives, Phase 4 future value, and
execution noise remain optional and can be combined with fallback. Coefficients
and class shares in the examples are illustrative, not empirically calibrated.
Reservations and delayed traveler decisions are outside this phase's scope.

The legacy `max_declines` setting bounds repeated offers to a selected driver.
Ranked fallback instead requires no same-driver retries. Its total offer count
is bounded by the number of retained distinct drivers, rather than sharing the
legacy request-level retry budget across drivers. Unsupported combinations
fail explicitly instead of silently truncating fallback.

## Candidate order and execution

1. Run the existing routing, vehicle-search, insertion, and configured heuristic
   filters against the current plans.
2. Freeze those feasible proposals. Sort by their existing delta objective,
   keeping original insertion order for equal costs, and keep the cheapest
   retained plan for each distinct driver.
3. Compute each offered driver's probability from its own proposed pickup ETA,
   direct passenger trip distance, and fixed driver class. Reuse the existing
   `driver_acceptance/{operator}/{vehicle}/{request}` stream for exactly one
   draw. Probabilities 0 and 1 consume no draw.
4. Continue after a refusal. Stop immediately on acceptance; do not draw for
   lower-ranked drivers. Cache the decision and winning driver, so offer
   creation or episode replay cannot redraw it or double-serve the request.
5. Store only the winning temporary plan and follow normal rider booking,
   commitment protection, execution, and promised-time recording.

This preserves existing vehicle-search exclusions and heuristic candidate
limits. It is not an exhaustive all-fleet search if the operator config limits
the insertion list. Multiple plans for one driver do not become multiple
offers. An empty feasible list is `no_vehicle_available`; exhausting a nonempty
list is `driver_declined`. Only the last unsuccessful candidate is marked as a
terminal request decline. Earlier refusals can belong to a later-served rider.

Candidate costs and order are frozen before sampling. Future-value scores
remain the existing optimistic reachability estimates; the queue is not
rescored after observing a refusal. When future value is enabled, its selected
score file can now contain several rows for one request, one per offered
driver. It is diagnostic and does not replace actual fallback feasibility.

With fallback absent/false, the original stable minimum, retry path, files,
and random draws are retained. With probability one, the first driver accepts,
so the enabled path also reproduces the existing first-driver result.

## Records and metrics

- `ranked_insertion_op_N.csv`: request/driver, candidate rank/count, delta
  objective, one-offer probability, decision, terminal status, and the full
  retained vehicle/cost ordering.
- `ranked_insertion_op_N.json`: ordering/scope/stream assumptions and counters
  for requests, candidates, offers, refusals, accepted requests, acceptances
  after rank one, exhausted lists, and empty feasible lists.
- Existing acceptance logs retain actual draws and sequential request-level
  attempt numbers across drivers. `max_attempts=1` in their model audit refers
  to each driver; the added ranked-fallback metadata explains the changed
  total-request bound. Intermediate refusals are not terminal request rejects.
- Optional choice logs contain singleton episodes, one per offered driver;
  cached offer creation adds no extra episode. All output families respect
  `skip_file_writing` and final counter flushing.

Paired evaluation continues reporting real offer/refusal counts and completed
service. The ranked audit distinguishes actual successful fallback from the
Phase 4 forecast. Successful dispatch and improved service are separate claims;
use the recorded controlled results rather than the screenshot's example totals.

## Measured controlled examples

At seeds 0, 1, and 2 with execution noise sigma 0.3, the two arms differ only
by scenario name and enabling ranked fallback. All nine input-pair audits
matched, and all accepted requests in the 18 simulations completed.

| Matching configuration | Mean completed trips: control → fallback | Mean served-rider wait: control → fallback |
| --- | --- | --- |
| Insertion | 44.67 → 70.33 | 118.61s → 149.66s |
| Immediate insertion + batch reoptimization | 49.67 → 71.67 | 113.46s → 107.07s |
| Insertion with future-value scoring | 42.67 → 69.67 | 107.85s → 153.28s |

These are gains on the bundled small example with illustrative coefficients.
Waiting-time means are conditional on service and involve different served
populations. They do not establish a city-scale gain or lower waits for every
rider. Full seed results, uncertainty reports, driver-offer counts, and raw
outputs are retained with the phase evidence.

## Examples and verification

Example scenarios cover basic insertion, insertion followed by periodic batch
reoptimization, future-value combinations, and illustrative driver classes:
`example_ir_ranked_fallback.yaml`, `example_ir_batch_ranked_fallback.yaml`,
`example_ir_ranked_future_value.yaml`, and `example_ir_ranked_classes.yaml`.

For a matched baseline comparison, use the single-attempt Phase 5 scenario:

```bash
.venv/bin/python -m tools.paired_eval \
  --constant-config studies/example_study/scenarios/constant_config_ir.csv \
  --baseline-scenarios studies/example_study/scenarios/example_ir_driver_choice.yaml \
  --candidate-scenarios studies/example_study/scenarios/example_ir_ranked_fallback.yaml \
  --network-tt-noise-sigma 0.3 --seeds 0 1 2 \
  --output /tmp/fleetpy-phase5b-comparison
```

Use a new output path for every experiment. Run the full completion gate with:

```bash
.venv/bin/python -m pytest -q
```

Tests exercise ordering, stable ties, deduplication, per-driver ETA, independent
draws, cached replay, exhaustion, exact disabled-path and probability-one
compatibility, both insertion controllers, classes, noise/future combinations,
and fresh-process paired replay. The step record and final measured results
are in [WORK_LOG.md](WORK_LOG.md); final evidence is under
`docs/validation/phase5b/`.
