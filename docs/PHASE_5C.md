# Phase 5c: Alonso-Mora forbid/rematch

When a driver declines an optimizer-selected request, this opt-in feature
removes that request/driver edge and its cached trip variables, then solves the
retained native assignment problem again. It stops once the selected new
requests are accepted or no further driver decisions are proposed.

Re-solving occurs at the same simulation time. There is no extra rider wait
window, vehicle-state update, replay of completed legs, or injected fallback
plan. The controller executes plans only after the sequence settles.

## Configuration

| Parameter | Requirement |
| --- | --- |
| `op_driver_acceptance_forbid_rematch` | Boolean, default false |
| `op_driver_acceptance` | `logistic` when enabled |
| `op_driver_acceptance_max_declines` | 0: one decision per request/driver pair |
| `op_module` | `RidePoolingBatchAssignmentFleetcontrol` |
| optimizer/solver | Single-worker `AlonsoMora`, Gurobi (including its normal implicit default) |
| simulation/traveler | `BatchOfferSimulation`, `BasicRequest` |

Driver classes, choice off/singleton/logit, execution noise, reward weighting,
and future value are supported combinations. Phase 5b remains the separate
ranked insertion path. CPLEX and multiprocessing are outside the validated
enabled scope. With the flag absent or false, existing sampling and solver
constraints remain unchanged.

## Graph and acceptance lifecycle

1. Build the normal RV/RTV graph and compute the initial optimizer solution.
2. Evaluate new requests through the existing driver/choice model; never redraw
   committed riders or a previously sampled pair.
3. Remove each negative pair from both RV indexes and all cached trips that
   contain it. Prune exclusions before later graph construction and guard
   against forbidden variables in the native solver. Request deletion clears
   its exclusion set.
4. Require accepted new request/driver pairs in subsequent solves. Existing
   mandatory-booking constraints remain intact. The solver may change a pending
   tour while preserving the accepting driver and feasibility. An inconsistent
   retained graph or solution that loses an accepted pair fails before execution.
5. Solve the surviving ILP again, using the same vehicle snapshot and stored
   feasible trip costs. Do not rerun the simulation-state setup or manufacture
   tours. Every repeated pass removes at least one previously eligible edge,
   giving a finite request-count times vehicle-count bound.
6. Once no selected request is declined, apply only the settled plans through
   the existing internal assignment API. Requests that were refused and remain
   unassigned receive the terminal driver-decline rejection. Requests never
   offered retain the existing no-assignment behavior.

The retained graph respects configured search/trip heuristics. Re-solving can
leave a request unassigned because of capacity or cost without offering to
every fleet vehicle; terminal rejection does not imply all fleet drivers
personally refused. Cached refusal edges remain excluded for that request,
including later graph rebuilds. Accepted/boarded riders cannot be newly
forbidden.

Decision probabilities use the first proposed tour for each pair and are
cached. The rider's final promise uses the settled serving tour, before booking.
The existing future-value reachability proxy and trip costs are frozen for
the initial graph; they are not recomputed as conditional posterior values
after observing each refusal. Coefficients remain illustrative assumptions.

## Actual logit menus

Outside/unselected menu items are negative decisions for their offered edges;
they are not separate independent Bernoulli refusals. Chosen requests retain
their accepting drivers. Temporary solver restrictions prevent a driver who
already accepted one new item from accepting another in a later pass of the
same round. Existing booked riders do not count against this new-item limit.

This preserves Phase 5's one-new-item-per-driver rule across the entire solve
sequence. Choice streams retain the same round and canonical menu identities;
only previously unoffered pairs can produce fresh decisions.

## Logs and interpretation

- `forbid_rematch_op_N.csv`: simulation time, matching round, solve pass,
  request/driver, base one-offer probability, outcome, edge removal, and
  singleton/menu decision kind. For actual menus, conditional probabilities and
  categorical draws remain in the choice and driver-decision records.
- `forbid_rematch_op_N.json`: scope, constraints, and counters for solver
  re-solves, offered/forbidden pairs, accepted/recovered/terminal requests, and
  removed cached trip variables.
- Existing acceptance rows retain real attempts and draws, with sequential
  attempt numbers across distinct drivers. They are buffered until the solve
  settles; only the last genuine refusal for a terminal request is flagged.
  Recovered riders therefore have no false terminal flag. No synthetic offer
  is added to announce rejection.
- Existing choice/future logs continue recording the actual feature events;
  future-score files may contain several offered drivers for the same request.
  All new outputs respect `skip_file_writing` and final audit flushing.

With probability zero and acceptance-weighted rewards, the optimizer can
correctly propose no service at all. That produces empty decision tables and
zero re-solves; complete demand and driver accounting still validate. The
separate unweighted always-decline check forces genuine offers so edge removal
and terminal rejection are exercised.

## Example commands

Three matched seed-0/1/2 comparisons at noise sigma 0.3 produced the following
actual example results. Both arms have identical settings except scenario name
and the rematch flag, and all nine input-pair audits matched.

| Batch configuration | Mean completed: control → rematch | Mean served-rider wait: control → rematch |
| --- | --- | --- |
| Standard single-offer decisions | 54.67 → 77.33 | 125.02s → 151.18s |
| Actual logit menus | 53.00 → 78.67 | 136.30s → 157.00s |
| Future-value scoring | 52.67 → 76.67 | 107.79s → 149.83s |

All accepted requests in these 18 simulations completed. Waiting-time means
are conditional on service and compare different served populations. These
are illustrative small-example gains with higher waits, not calibrated
marketplace predictions or a city-scale result. Original reports retain the
seed values, confidence intervals, driver-offer counts, and other metrics.

Reproduce the standard comparison with:

```bash
.venv/bin/python -m tools.paired_eval \
  --constant-config studies/example_study/scenarios/constant_config_pool.csv \
  --baseline-scenarios studies/example_study/scenarios/example_batch_driver_choice_control.yaml \
  --candidate-scenarios studies/example_study/scenarios/example_batch_forbid_rematch.yaml \
  --network-tt-noise-sigma 0.3 --seeds 0 1 2 \
  --output /tmp/fleetpy-phase5c-comparison
```

Use a new output directory. `example_batch_forbid_rematch_menus.yaml` pairs
with the existing actual-menu control. The future-value pair is
`example_batch_rematch_future_control.yaml` versus
`example_batch_forbid_rematch_future.yaml`; both use the same single-attempt
settings and top-k value.

Run the complete gate with `.venv/bin/python -m pytest -q`. The complete step
record, failures/fixes, measured results, and publication are in
[WORK_LOG.md](WORK_LOG.md), with final raw evidence under
`docs/validation/phase5c/`.
