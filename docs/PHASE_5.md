# Phase 5: driver choice and conflict resolution

This phase adds a logit choice among request offers plus an outside option,
and a deterministic greedy resolver that permits one winner per request and
driver in an episode. It also provides an exact single-item compatibility mode.
All new behavior is off by default.
Bare `off` in YAML/CSV (decoded as `False`) is accepted as disabled as well.

The uploaded plan separates this work from ranked insertion fallback (5b) and
Alonso-Mora forbid/rematch (5c). Phase 5 does not expand the request-vehicle
graph, walk a ranked driver list, or reroute a declined request to another driver.

## Configuration and compatibility

| Operator parameter | Default | Behavior |
| --- | --- | --- |
| `op_driver_choice_model` | absent / `off` | Existing Phase 3/4 path; no choice files or new draws |
| value `singleton` | explicit opt-in | Route each selected request-driver pair through a single-item episode; retain Phase 3 draws and bounded retries exactly |
| value `logit` | explicit opt-in | For batch matching, let each driver choose at most one of its solver-selected new requests or the outside option |

Driver choice requires `op_driver_acceptance=logistic` and `BasicRequest`,
which decides immediately when an offer arrives. The existing batch offer-wait
window is preserved; it need not be zero. Actual `logit` menus require
`op_driver_acceptance_max_declines=0`: one categorical decision, without adding
an undocumented sequence of retries. Singleton mode supports the existing
retry settings. Weighting and Phase 4 future value remain optional.

For insertion controllers, the current immediate-request flow has one selected
proposal, so both modes use the single-item path. The true multi-item integration
is in `RidePoolingBatchAssignmentFleetcontrol` with Alonso-Mora. The validated
scope remains the three single-worker baseline road-trip controllers and
BrokerBasic. PT, external traffic coupling, asynchronous rider decisions, and
multiprocessing are outside the supported configuration.

Singleton mode preserves the rider/evaluation/driver-decision tables, including
stochastic retries. It also preserves Phase 4 selected-score records when future
value is enabled. It can accept multiple new requests for a pooled vehicle in
separate compatibility episodes, exactly as before. In contrast, a multi-item
logit menu permits at most one new request for that driver in that round.
Even if all menu items have base probability 1, it still chooses only one;
the exact p=1 upstream compatibility check uses singleton mode.

## Choice probabilities

For each menu item, the existing Phase 3 model supplies one-offer probability
`p_i` from driver class, pickup ETA, and direct trip kilometers. Its menu utility is

```text
u_i = log(p_i) - log(1 - p_i)
u_outside = 0
P(item i | menu) = exp(u_i) / (1 + sum_j exp(u_j))
P(outside | menu) = 1 / (1 + sum_j exp(u_j))
```

These are odds weights, not normalized raw acceptance probabilities. For
example, base probabilities 0.25 and 0.75 give item probabilities 1/13 and
9/13, and outside probability 3/13. A one-item menu returns `p` and `1-p`
using the exact original arithmetic. Empty/all-impossible menus choose outside
without a draw. Probability-one items share all probability equally; other
items and outside then have zero probability. Stable shifted exponentials
handle extreme finite odds.

Menus are sorted by a canonical request-ID key before sampling. Each driver
chooses once, using a named stream derived from seed, operator, driver, matching
round, and canonical menu digest. Menu input order cannot change its result.
Committed/onboard requests are excluded before constructing menus.

For single-item compatibility, the existing Phase 3 request/vehicle streams,
cached outcomes, and retry count are used directly. No extra choice draw is
made. The final compatibility outcome may include several Bernoulli attempts;
the new choice record's base probability still describes one offer. Actual
attempts remain in the existing driver-decision log.

## Conflict resolution and execution

`choice_model.py` supplies the independent menu model; `conflict_resolution.py`
resolves sampled proposals greedily by lower supplied priority, higher
conditional choice probability, vehicle ID, then request ID. A request and a
driver can each win at most once in an episode. Protected requests and
unavailable drivers cannot win. Conflict losers receive no automatic redraw.

The overlap resolver is tested with explicit competing-driver proposals. Live
batch menus in this phase come from solver-selected plans, whose request
ownership is already unique. A duplicate solver assignment fails before
execution rather than silently normalizing an invalid solution. Alternative
driver candidate generation and rerouting belong to 5b/5c.
The current solver-menu adapter supplies priority zero; the priority field is
available to future offer generators. No cost-based multi-driver rematching is
claimed by this integration.

Resolved results are cached before execution. Unselected, outside-declined,
or losing items are stripped through the existing internally registered,
copied lower-plan path. They never cause a second Bernoulli draw. A separate
ownership check prevents two episodes from accepting the same uncommitted
request. Existing booked/onboard riders are protected; later operator
reassignment of a committed rider remains allowed.

Menu probabilities use the frozen solver-proposal pickup times. After choice,
the rider offer uses the reduced executable plan; shorter resulting routes do
not retroactively change the sampled choice. This is an explicit modeling
assumption, not a jointly optimized menu/tour model. Response latency remains
zero, and the illustrative Phase 3 class coefficients/shares are not calibration.

## Audits and metric interpretation

Enabled operators add:

- `driver_choice_op_N.csv`: time, round/episode, operator/driver/request IDs,
  menu size, original base probability, conditional item/outside probabilities,
  categorical interval/draw, selected/accepted flags, resolution reason, and
  whether sampling was delegated to Phase 3.
- `driver_choice_op_N.json`: mode, seed/stream scheme, utility/outside/priority
  rules, scope, and counters for episodes, offered/accepted items, outside
  choices, multi-item episodes, and conflict rejections.

The actual categorical uniform belongs to the menu, not to separate Bernoulli
trials. Legacy-format acceptance records for multi-item menus therefore store
the conditional item probability and a missing Bernoulli uniform; the choice
file preserves the actual shared draw and intervals. Singleton records retain
their original acceptance draws and schema. The normal `skip_file_writing`
option suppresses both output families; counters still work.

For menu mode, the existing paired `driver_offer_attempts` and `driver_declines`
count offered items and rejected/unselected items. One outside choice can
reject several items; these counts are not the number of categorical draws,
independent personal refusals, or distinct outside decisions. Consult the
choice audit and completion counts together. Matching weights continue to
use one-offer base probabilities or Phase 4's approximate future value;
they are not a joint optimization of conditional menu probabilities.
When future value is enabled, its score diagnostics describe the original
proposal probabilities and fallback estimates. Menu outcomes are recorded
alongside those diagnostics; the categorical sampler uses the base utilities,
not the inflated future-value score.

## Run comparisons

Exact Phase 3 singleton comparison:

```bash
.venv/bin/python -m tools.paired_eval \
  --constant-config studies/example_study/scenarios/constant_config_ir.csv \
  --baseline-scenarios studies/example_study/scenarios/example_ir_driver_acceptance.yaml \
  --candidate-scenarios studies/example_study/scenarios/example_ir_driver_choice.yaml \
  --network-tt-noise-sigma 0.3 --seeds 0 1 2 \
  --output /tmp/fleetpy-phase5-singleton
```

Actual batch menus, with identical single-attempt settings and class parameters
in both arms:

```bash
.venv/bin/python -m tools.paired_eval \
  --constant-config studies/example_study/scenarios/constant_config_pool.csv \
  --baseline-scenarios studies/example_study/scenarios/example_batch_driver_choice_control.yaml \
  --candidate-scenarios studies/example_study/scenarios/example_batch_driver_choice.yaml \
  --network-tt-noise-sigma 0.3 --seeds 0 1 2 \
  --output /tmp/fleetpy-phase5-menus
```

Use a new output directory each time. The additional
`example_ir_future_value_choice.yaml` demonstrates singleton compatibility with
Phase 4. All coefficients/shares are illustrative. This phase does not claim
that driver menus increase service or realize the fallback opportunities in
Phase 4; actual measured results are retained in the work log and evidence.

## Verification

```bash
.venv/bin/python -m pytest -q
```

Checks cover analytical odds/outside probabilities, exact one-item sampling,
permutation invariance, numerical boundaries, conflict winners/ties/protected
requests, cross-episode ownership, cached decisions, no Bernoulli redraw after
categorical selection, output suppression, all-controller complete singleton
comparisons, and actual multi-item batches with and without future value.
Separate-process paired cases verify deterministic menus, exact Phase 3/4
singleton controls, and complete acceptance-to-service accounting.

Complete changes, reasons, benefits, corrections, results, and publication:
[WORK_LOG.md](WORK_LOG.md). Raw evidence: `docs/validation/phase5/`.
