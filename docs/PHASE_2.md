# Phase 2: promised service times and uncertain execution

Operators plan routes and quote travel times using the existing routing engine.
Vehicles can now execute those routes with independent travel-time variation.
The accepted offer is frozen so its promised pickup/dropoff can be compared
with actual service, even after a plan or offer changes.

## Settings and compatibility

| Scenario parameter | Default | Behavior |
| --- | --- | --- |
| `network_tt_noise_sigma` | `0` | Nonnegative, finite log-scale standard deviation of executed driving time |
| `record_promised_times` | `False` | Record accepted promises and signed timing errors even without noise |

Positive sigma automatically enables promised-time recording. At zero sigma,
no execution generator is created, no execution draws occur, and the original
movement arithmetic is retained. With both settings absent, rider and vehicle
output schemas retain their original columns. Recording alone adds diagnostics
without changing dispatch, travel times, or the original output values.

These are scenario parameters, not operator parameters. Put them in constant
configuration rows or scenario columns. Existing `random_stream_mode` defaults
to `legacy`; use `independent` for paired experiments as described in Phase 1.

## Execution model

At the start of each moving vehicle route leg, draw

```text
M = LogNormal(mu = -sigma² / 2, standard_deviation = sigma)
E[M] = 1
Var[M] = exp(sigma²) - 1
executed driving time = routing travel time × M
```

The draw remains fixed across simulation ticks, route recalculation, and
reassignment of an equal current leg. Ending/interruption of that leg followed
by a different leg produces a new draw. Stationary waiting, boarding, charging,
and other service durations are unscaled. The multiplier is not drawn per edge
or per request; riders sharing a vehicle leg share its execution conditions.

Each vehicle uses Phase 1's SHA-256/SeedSequence/PCG64 scheme and stream name
`execution/{operator_id}/{vehicle_id}`, derived from `random_seed`. This private
stream is used even when other components remain in legacy random mode.
Noise never consumes demand, initialization, traveler-choice, or optimizer
randomness. Zero sigma constructs no stream. Pathological sigma values that
produce a zero or nonfinite sampled multiplier fail explicitly.

Movement receives `wall_clock_budget / M` routing-time seconds. Router arrival
and replay-node timestamps are translated back to absolute wall-clock times.
The remainder of the tick is then available for subsequent service or travel.
Distance and energy consumption retain their per-meter definitions. Noise does
not multiply the distance, fare, service duration, or planning cost.

Existing keep-feasible handling retains committed stops when observed delays
violate their original time windows. New insertions continue to use existing
feasibility checks. We did not relax all requests' deadlines or rewrite the
matching algorithm. A delayed rider can still board and complete service.

## Rider and vehicle records

When recording is enabled, `1_user-stats.csv` adds:

| Column | Meaning |
| --- | --- |
| `promise_operator_id` | Operator whose offer was accepted at booking |
| `promised_pickup_time` | Request time plus accepted offered waiting time |
| `promised_dropoff_time` | Promised pickup plus accepted offered driving time |
| `pickup_error_s` | Actual pickup minus promised pickup, in seconds |
| `dropoff_error_s` | Actual dropoff minus promised dropoff, in seconds |

Actual `pickup_time` and `dropoff_time` remain the existing simulation records
(start of boarding and start of alighting). Promises use simulation-clock
seconds. Offer wait is relative to request time, not booking/offer arrival time.
Negative error means early, positive means late. Unselected operators' offers
never supply promises. A later update cannot overwrite a captured promise.
The serving operator is checked against the captured operator at boarding.
Rejected/no-offer requests have missing promises; uncompleted events have
missing errors, not zero errors. The existing final `offers` string is retained
but is not used to reconstruct the accepted promise after the run.

With positive sigma, operator activity files add `travel_time_multiplier` on
every recorded leg. Nonmoving legs have multiplier 1. Interrupted driving legs
retain their sampled multiplier in their record.

## Paired evaluation

From the repository root, this runs insertion against immediate/batch matching
under the same noise setting, with complete config/source/input provenance:

```bash
.venv/bin/python -m tools.paired_eval \
  --constant-config studies/example_study/scenarios/constant_config_ir.csv \
  --baseline-scenarios studies/example_study/scenarios/example_ir_only.csv \
  --candidate-scenarios studies/example_study/scenarios/example_ir_batch.csv \
  --network-tt-noise-sigma 0.3 \
  --seeds 0 1 2 \
  --output /tmp/fleetpy-phase2-noise
```

Use a new output path on every run. To diagnose promises without noise, use
`--network-tt-noise-sigma 0 --record-promised-times`. CLI overrides apply to
both policies and are recorded in the manifest and each simulation's config.
Different exogenous noise settings between the two policies are rejected.

When promise columns exist, the existing seed and paired-comparison reports
also include `promised_requests`, and pickup/dropoff promise-error count,
missing count, mean, population SD, MAE, p10/p50/p90, and late fraction. Late
fraction uses error greater than one microsecond to avoid float-roundoff ties.
Errors are conditional on observed service with a recorded promise; always
inspect completion counts alongside them. Confidence intervals and tests
continue to use paired seeds, not individual riders or drivers, as replicates.

The private streams reproduce draws for each vehicle's leg sequence. Different
policies can start different legs or interrupt them differently, so this does
not promise identical realized shocks for corresponding riders. Mean-one noise
does not imply zero mean rider error: reoptimization, waiting, selection, and
shared rides also affect outcomes. Noiseless promise errors need not all be zero
because accepted plans can change even under deterministic driving times.

## Validation and scope

```bash
.venv/bin/python -m pytest -q
```

Tests check settings, isolation, mean-one parameterization, early/late travel
across ticks, replay timestamps, distance/energy, unscaled stationary duration,
one draw per leg, correct chosen-operator snapshots, and missing-event metrics.
They exercise a delayed committed plan and full insertion, immediate/batch,
and batch examples at sigma 0 and 0.6. Zero-noise runs with recording match all
original rider columns and standard evaluation cells exactly. Default runs
still match the independent Phase 0 references. Paired CLI tests verify exact
repeatability for identical policies under noise and audited different-policy
runs, including report generation and refusal to overwrite evidence.

Validated scope is the example road network, BasicRequest trips, and the three
baseline controllers, with one worker. Recording currently requires the default
BrokerBasic; multimodal PT brokers are rejected. External MATSim/SUMO movement
cannot be controlled by this noise model and is rejected when noise is enabled.
No city calibration, observed travel-time error fit, driver acceptance model,
spatial/temporal shock correlation, or new repositioning policy is introduced.
The preexisting four-hour tail-drain limit still applies to extreme delays.

The step-by-step changes, reasons, benefits, development corrections, and actual
verification results are retained in [WORK_LOG.md](WORK_LOG.md). Final run
manifests and reports are archived in `docs/validation/phase2/`.
