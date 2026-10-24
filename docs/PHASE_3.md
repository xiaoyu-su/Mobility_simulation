# Phase 3: logistic driver acceptance

Drivers can accept or decline a newly proposed request before the operator
offers it to the rider. The feature defaults off. Insertion and Alonso-Mora
batch matching support bounded retries, optional acceptance-weighted rewards,
driver classes, isolated random draws, and reviewable decision logs.

## Model and units

```text
pickup_eta_minutes = max(0, planned_pickup_time - decision_time) / 60
trip_km = direct_request_distance_m / 1000
p = sigmoid(intercept + beta_eta × pickup_eta_minutes + beta_value × trip_km)
```

Pickup ETA is the remaining planned delay when the driver decides, including
preceding work in that candidate plan. It is not the elapsed wait since the
rider requested. Trip distance is the routing engine's direct request distance,
not deadheading, vehicle tour distance, realized noisy distance, or fare.
The sigmoid is evaluated stably at extreme utilities.

The model requires explicit coefficients or an explicit probability override.
No coefficient default is represented as empirically calibrated. The original
plan cites Ashkrof et al. (2022), Transportation Research Part C 142:103783,
including a fare slope per USD. That fare slope is not interchangeable with
this model's distance slope per km. The plan's reported utilization/class-share
anchors and example outcomes are not fitted parameters or expected test values.
The included example coefficients and shares are labeled illustrative.

## Configuration

These are operator parameters. They may be placed in constant configuration
or a scenario file, as with other `op_` parameters.

| Parameter | Default | Meaning |
| --- | --- | --- |
| `op_driver_acceptance` | absent / `off` | Set `logistic` to enable |
| `op_driver_acceptance_intercept` | required when no classes/override | Constant logit utility |
| `op_driver_acceptance_beta_eta` | required when no classes/override | Utility per pickup minute |
| `op_driver_acceptance_beta_value` | required when no classes/override | Utility per direct passenger km |
| `op_driver_acceptance_probability` | absent | Optional fixed probability in [0,1], useful for sanity checks |
| `op_driver_acceptance_max_declines` | `2` | Retry allowance after the first attempt; `0` means one attempt |
| `op_driver_acceptance_weight_objective` | `False` | Replace only uncommitted assignment reward by probability-weighted reward |
| `op_driver_acceptance_classes` | absent | Named coefficient/share mappings replacing the single coefficient set |

Every class requires `share`, `intercept`, `beta_eta`, and `beta_value`; shares
must be positive and sum to one. Classes are assigned once per vehicle ID via
the isolated `driver_class/{operator_id}/{vehicle_id}` stream. Changing class
dictionary order cannot change assignments. A five-vehicle sample need not
exactly reproduce the population shares. Class parameters and the actual
vehicle-to-class roster are written to the audit file.

See the checked-in, runnable scenarios:

- `studies/example_study/scenarios/example_ir_driver_acceptance.yaml`
- `studies/example_study/scenarios/example_ir_driver_classes.yaml`
- `studies/example_study/scenarios/example_batch_driver_classes.yaml`

## Proposal, retry, and commitment behavior

Insertion first computes its best candidate plan. Driver acceptance is checked
before creating a rider offer or assigning that proposal to the vehicle. A
terminal decline removes the temporary insertion proposal and sends a rider
rejection with reason `driver_declined`.

Batch matching first selects solver plans. Each new request's driver decision
is checked before those plans execute. Terminally declined requests are removed
through Alonso-Mora's lower-trip-plan API; other requests and committed riders
remain. The live controller receives a copy of the optimizer's stored plan so
vehicle status updates cannot mutate its next-round state. Terminal driver
declines do not trigger the controller's unrelated second waiting-window retry.

A request can receive at most `1 + max_declines` attempts. These are immediate
reoffers to the same selected driver in that matching round. They consume no
simulated response time. A proposal remains unexecuted during retries. After
exhaustion it is rejected. Each attempt is logged; repeated processing of the
same request/driver uses its cached final outcome rather than new draws.
This is a bounded selected-driver acceptance model. It does not walk a ranked
list of other drivers or forbid/rematch declined request-driver edges. Those
belong to the later multi-offer phases. The retry/zero-response-time assumptions
should be changed explicitly before representing real offer-response dynamics.

Once a rider has accepted the operator's offer, the operator retains that
commitment. Later optimization, movement updates, or reassignment cannot run
a fresh acceptance draw that abandons that rider. Existing capacity, route,
time-window, and keep-feasible handling still apply. Execution noise from Phase
2 remains a separate vehicle process; it can make accepted trips early or late.

## Optional matching reward

The supported objective is `distance_and_user_times_with_walk`, used by the
three baseline examples. Its original cost is

```text
operating/traveler cost - R × number_of_requests
```

With acceptance weighting, it becomes

```text
operating/traveler cost - R × sum(request_acceptance_probabilities)
```

Committed/onboard requests retain probability 1 in this reward. Cost terms are
not multiplied by probability. Scoring never draws an accept/decline outcome.
Unsupported objectives fail explicitly if weighting is enabled. With fixed
probability 1, the original arithmetic and exact simulation outputs are retained.
This is the immediate probability weighting in Phase 3; future fallback value
is a later phase.

## Randomness and records

Stochastic acceptance uses the Phase 1 named stream scheme, with one stream per
`driver_acceptance/{operator_id}/{vehicle_id}/{request_id}`. Unrelated requests,
driver-class sampling, optimizer construction, scoring, and execution noise
cannot consume that stream. Probabilities exactly 0 or 1 draw no random number.
With the feature off, no model/stream or additional acceptance output is created.

Each enabled operator writes:

- `driver_acceptance_op_N.csv`: simulation time, operator/vehicle/request IDs,
  class, attempt, pickup ETA in seconds, direct distance in meters, probability,
  uniform draw, accepted flag, cumulative decline count, and terminal-decline flag.
- `driver_acceptance_op_N.json`: model units, coefficients, class assignments,
  seed/stream scheme, fixed-probability override, retry limit, reward-weighting
  setting, and coefficient provenance status.

The existing `skip_file_writing` setting suppresses these files as well. Every
attempt is written immediately when recording is enabled, including attempts
that end in rejection. The rider-output schema remains unchanged by acceptance
alone; Phase 2's promise columns appear when its recording/noise is enabled.

Paired reports always include `driver_offer_attempts`, `driver_acceptances`,
`driver_declines`, `driver_terminal_declines`, and `driver_offered_requests`.
They are zero when the feature is off, so enabled-versus-disabled policies share
a comparable metric set. A decline count includes retries; it is not a count
of distinct rejected riders. Inspect terminal declines and completed-request
counts alongside it. Decision logs are validated before summarization.

## Run an audited experiment

This compares the original insertion policy against the illustrative weighted
acceptance policy, using the same demand, initial vehicles, network, and noise:

```bash
.venv/bin/python -m tools.paired_eval \
  --constant-config studies/example_study/scenarios/constant_config_ir.csv \
  --baseline-scenarios studies/example_study/scenarios/example_ir_only.csv \
  --candidate-scenarios studies/example_study/scenarios/example_ir_driver_acceptance.yaml \
  --network-tt-noise-sigma 0.3 \
  --seeds 0 1 2 \
  --output /tmp/fleetpy-phase3-acceptance
```

Use the classes YAML as the candidate to try different driver types. Use a new
output directory each time. Configuration snapshots, commands, dependencies,
source and input audits, raw decisions, vehicle/rider results, and paired
statistical reports are retained. Use paired seeds as the statistical replicates.
Illustrative model experiments do not establish general policy superiority or
an empirically calibrated acceptance rate.

For batch matching, use `constant_config_pool.csv`, `example_pool.csv`, and
`example_batch_driver_classes.yaml` for the constant, baseline, and candidate
arguments respectively.

## Validation and scope

```bash
.venv/bin/python -m pytest -q
```

Validation checks sigmoid signs/units, extreme values, invalid parameters,
bounded retries and eventual acceptance, fixed class identity, isolated draws,
committed-rider protection, objective reward/cost separation, output suppression,
decision summaries, and isolation between live and optimizer-held reduced plans.
All three full examples run at p=1, p=0, and weighted logistic acceptance plus
travel-time noise. p=1 reproduces every original rider/evaluation cell exactly;
p=0 serves none; stochastic runs serve exactly the accepted requests. Separate
paired CLI cases exercise repeated identical policies and heterogeneous classes.

Supported scope is single-worker, immediate road-trip requests in the three
baseline controllers, with BrokerBasic and Alonso-Mora where batch optimization
is used. Multimodal/PT brokers, external traffic coupling, other controllers or
batch optimizers, and multiprocessing are rejected. Reservation/future-request
behavior, observed wage/fare utility, response latency, driver learning, and
calibrated class shares are not validated here.

Actual checkpoints and the optimizer lifecycle corrections are in
[WORK_LOG.md](WORK_LOG.md). Final test and run evidence is archived under
`docs/validation/phase3/`.
