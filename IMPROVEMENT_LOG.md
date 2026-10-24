# Improvement log

## Phase 0 — baseline hygiene

- Recorded independent upstream references at commit
  `c813728b6d188df8dd7fd5d3d36dcb0a55c898a2` for three complete example
  simulations: insertion, immediate insertion with batch optimization, and
  batch assignment. Each executes 100 requests and picks up 93.
- Added exact comparisons of all evaluation cells and per-rider output cells,
  plus a provenance manifest and an explicit reference-capture tool.
- Reproduced five failing unit cases before fixing batch retry/rejection and
  aggregated forecast handling.
- Replaced obsolete `delRequest` with `delete_request`, resolved the current
  request before second-attempt rejection, and corrected `groubpy`.
- Disabled default debug solver dumps in both multistage sampling
  repositioning variants.
- Added test dependency pins and pytest discovery limited to `tests/`.

Validation and reproduction instructions are in `UPSTREAM_COMPARISON.md`.
At the Phase 0 milestone, later phases were not yet implemented.

## Phase 1 — independent streams and paired evaluation

- **What changed:** opt-in stable named random streams for demand, parcels,
  per-request choices, per-vehicle initialization, and the Alonso-Mora batch
  optimizer and solver. Existing scenarios remain in legacy mode.
- **Why:** demand and optimizer constructors previously reset shared global
  randomness, allowing policy-dependent draw order to contaminate comparisons.
- **Benefit:** isolated exogenous draws and verifiable matched starting inputs,
  while the three approved legacy examples retain exact recorded outputs.
- **Evaluation tools:** complete multi-seed policy runs, per-driver time and
  fare/cost proxies, distribution/inequality summaries, paired confidence
  intervals and t/Wilcoxon tests. Seeds, not individual drivers, are replicates.
- **Traceability:** retained configurations, commands, exit codes, logs, loaded
  input/initial-fleet hashes, dependency versions, working-source hashes, and
  report hashes. Incomplete or mismatched experiments fail explicitly.
- **Accounting improvement found end to end:** FleetPy drains pending work
  after the nominal horizon. Include its exact legs and fares, expose per-driver
  tail exposure, and avoid discarding revenue or omitting its associated work.
- **Final verification:** 41 tests passed, including baseline regressions,
  named-stream checks, hand-computed metrics/inference, and complete paired CLI
  experiments. A separate six-simulation, three-seed demonstration also passed
  all pairing checks. Final evidence is archived in `docs/validation/phase1/`
  and recorded step by step in `docs/WORK_LOG.md`.
- **Limits:** single-worker baseline matching workflows first; fare-minus-cost
  is a proxy rather than actual driver pay. No driver acceptance, ETA noise,
  windowed execution, or AV policy is introduced in this phase.

Usage and metric definitions: `docs/PHASE_1.md`. Step-by-step evidence:
`docs/WORK_LOG.md`.

## Phase 2 — promised service and execution uncertainty

- **What changed:** optional `network_tt_noise_sigma` draws a mean-one
  lognormal multiplier per executed driving leg from a private per-vehicle
  stream. Planning/offer estimates retain existing routing times. Arrival and
  replay timestamps use actual wall time; stationary durations are unscaled.
- **Why:** deterministic execution hides service uncertainty, and later offer
  updates cannot reliably reconstruct what a rider originally accepted.
- **Benefit:** frozen selected-operator pickup/dropoff promises and signed
  actual-minus-promised errors expose bias and dispersion. Per-leg multiplier
  records make execution reviewable. Existing keep-feasible behavior retains
  delayed commitments without globally relaxing new-request constraints.
- **Compatibility:** both features default off. Zero noise consumes no
  execution draws. Optional `record_promised_times` adds diagnostics alone;
  original rider/evaluation values retain exact upstream compatibility.
- **Evaluation:** common CLI overrides apply to both paired policies and are
  retained in manifests/configs. Reports include observed and missing error
  counts, mean, population SD, MAE, quantiles, and late fraction.
- **Verification:** **66 tests passed in 101.69s**. Includes the three original
  regressions, all three controllers at sigma 0 and 0.6, delayed committed
  service, and repeatable noisy paired experiments. Separate final runs at
  sigma 0/0.3, seeds 0/1/2, completed all 12 simulations and six pairing audits;
  every booked rider finished. All six sigma-0 runs exactly match the saved
  Phase 1 original rider columns and standard evaluation cells.
- **Limits:** verified single-worker example road trips; PT promise semantics
  and external traffic-simulator noise are rejected. Noise is an explicit
  modeling assumption, not an empirically calibrated travel-time-error fit.
  No driver acceptance or new dispatch/repositioning policy is introduced.

Usage, semantics, and limits: `docs/PHASE_2.md`. Actual final evidence:
`docs/validation/phase2/`. Changes, reasons, benefits, and development checkpoints:
`docs/WORK_LOG.md`.

## Phase 3 — configurable driver acceptance

- **What changed:** off-by-default logistic acceptance based on planned pickup
  minutes and direct-trip kilometers, fixed-probability sanity checks, named
  driver classes, bounded same-driver retries, and decision/class audits.
- **Why:** the original operators assume every driver carries out each new
  assignment. Driver-side declines need a separate decision boundary before
  rider booking and vehicle execution.
- **Benefit:** declined requests cannot execute; committed riders remain
  protected; independent per-request/vehicle draws preserve input pairing and
  repeatability. The always-accept path reproduces baseline results exactly.
- **Matching:** optional probability weighting changes only the uncommitted
  assignment reward in the baseline distance/user-time objective. Costs and
  committed-rider rewards retain their original values. Future fallback value
  and ranked multi-driver offers remain later phases.
- **Integration corrections found end to end:** copied internally reduced
  Alonso-Mora plans preserve optimizer/live-state independence; terminal driver
  declines cannot reopen waiting-window retries. Fixed an existing YAML scenario
  loader constructor mismatch so nested driver-class scenarios run through the
  real CLI.
- **Traceability:** explicit units, supplied coefficients/classes, stream/seed
  metadata, every acceptance/decline attempt, terminal rejection counts, and
  paired seed reports. Included coefficients/shares are illustrative; a
  literature fare-per-USD slope is not relabeled as a distance-per-km slope.
- **Scope:** the three single-worker baseline road-trip controllers. Retries
  immediately reoffer to the same selected driver and assume zero response
  latency. PT/external traffic/multiprocessing and empirical calibration are
  outside this implementation.
- **Final verification:** **107 tests passed in 177.57s**. Two separate
  three-seed experiments completed all 12 simulations, matched all six input
  audits, and completed every accepted booking. The complete raw records,
  decisions, source/config/output hashes, and reports are retained in
  `docs/validation/phase3/`.

Usage and assumptions: `docs/PHASE_3.md`. Full checkpoints, corrections, final
verification, and GitHub publication are recorded in `docs/WORK_LOG.md`;
final machine-readable evidence is archived in `docs/validation/phase3/`.

## Phase 4 — future-value matching

- **What changed:** opt-in assignment value `p + (1 - p) × fallback`, with
  fallback the probability that at least one top-k alternative driver accepts.
  Only uncommitted request rewards change; costs, actual acceptance, retries,
  and booked-rider commitments retain Phase 3 behavior.
- **Why:** immediate probability weighting omits the possibility that another
  nearby driver would accept. The new score exposes that modeling assumption
  for controlled comparisons, without implementing actual fallback dispatch.
- **Selection and optimization:** exact road-network ETA ranking, deterministic
  ties, selected-driver exclusion, colocated-driver handling, and round-scoped
  caches. One full ranking retains k+1 candidates for every driver exclusion;
  repeated plan scoring reuses routes and probabilities without random draws.
- **Traceability:** selected-proposal probabilities, alternative IDs/ETAs,
  served values, settings/limitation audits, and query/cache counters. Formula,
  cache boundaries, partial-edge routing, and full-scan agreement are verified.
- **Measured results:** three-seed insertion completion **44.67 → 42.67** and
  batch completion **76.33 → 71.67**. Neither example improves service; the
  optimistic score does not execute its alternative offers. The feature stays
  off by default, and these outcomes are retained without replacing them with
  the screenshots' results or treating illustrative coefficients as calibration.
- **Optimization evidence:** an actual-road score microbenchmark reduces
  routing calls **59,520 → 348**, with maximum full-scan score difference
  **1.11e-16**. Measured time **93.374s → 1.464s** is descriptive and affected
  by disconnected-route handling; it is not a full-simulation speedup claim.

Configuration, assumptions, and commands: `docs/PHASE_4.md`. Complete stepwise
checks, final verification, author identity, and publication: `docs/WORK_LOG.md`.
Raw experiments and benchmark evidence: `docs/validation/phase4/`.

Final verification: **145 tests passed in 260.74s**. Both final three-seed
experiments and the benchmark match the tested source digest; all accepted
bookings completed, and six Phase 3 control runs match their saved original
rider/evaluation/decision tables exactly.

## Phase 5 — driver choice and conflict resolution

- **What changed:** off-by-default logit choice among request items and an
  outside option; deterministic greedy conflict winners; exact single-item
  compatibility; solver-selected batch menus; full choice/probability audits.
- **Why:** Phase 3 models isolated accept/decline decisions. Menu choice needs
  a normalized outside option, one selected item per driver episode, and an
  explicit rule when drivers compete for the same request.
- **Compatibility:** singleton mode delegates existing request/vehicle random
  draws, outcomes, and retries. The default creates no choice files/draws.
  Actual menus require a single categorical episode and leave booked riders
  outside the menu. Existing plan-removal/copying logic executes only winners.
- **Conflict guarantees:** independent overlap tests enforce unique driver
  and request winners, protected bookings, stable ties, and order invariance.
  Live solver menus already have disjoint request ownership; invalid duplicate
  solver assignments fail before execution. Cross-episode ownership also
  protects uncommitted requests from double acceptance.
- **Traceability:** record base and conditional probabilities, outside mass,
  categorical intervals/draw, selected/accepted distinction, rejection reason,
  delegation, stream scheme, and episode counters. Multi-item acceptance rows
  contain no fabricated independent Bernoulli draw.
- **Limits:** validated BasicRequest baseline controllers with one worker.
  Menus choose at most one new request and use original proposal ETAs. This is
  not calibrated driver behavior or demonstrated service improvement. Ranked
  insertion fallback (5b) and optimizer forbid/rematch (5c) remain later phases.

Usage and assumptions: `docs/PHASE_5.md`. Complete corrections, verification,
results, author identity, and publication: `docs/WORK_LOG.md`. Raw evidence:
`docs/validation/phase5/`.

Final verification: **181 tests passed in 364.62s**. Two final three-seed
experiments completed 12 simulations and six matched input audits. Singleton
results remain exact; actual batch menus complete 53.00 trips on average versus
54.67 for the control, so no service improvement is claimed. Every accepted
booking completes. Ranked insertion fallback (5b) and optimizer rerouting (5c)
remain separate subsequent phases.

## Phase 5b: ranked insertion fallback

- **Problem:** after the best insertion driver declines, the immediate
  controllers reject the request even when another retained driver has a
  feasible plan.
- **Change:** opt-in `op_driver_acceptance_ranked_fallback` freezes feasible
  insertion candidates, orders by existing delta objective with stable ties,
  retains each driver's cheapest plan, and offers once per driver until the
  first acceptance. Only that plan reaches normal booking/execution. Both
  immediate insertion controllers support the feature; optimizer edge
  prohibition/rematching is reserved for Phase 5c.
- **Decision integrity:** reuse isolated request/driver draws, avoid same-driver
  retries, cache winners/outcomes, preserve choice ownership and booked riders,
  and mark only exhausted requests terminal. Disabled and probability-one paths
  retain exact existing rider/evaluation/decision tables in complete runs.
- **Records:** candidate lists/costs/ranks, probabilities, decisions, exhausted
  lists, actual successful fallback, source/config/output hashes, and complete
  raw simulations are preserved. Output suppression and final audit flushing
  continue to work.
- **Measured benefit and tradeoff:** three controlled seed-0/1/2 comparisons
  complete 18 simulations and nine matching-input audits. Mean completed trips
  increase **44.67 → 70.33** for insertion, **49.67 → 71.67** for immediate/batch,
  and **42.67 → 69.67** with future value. Mean served-rider waits rise in the
  first/third cases and fall in the second; all accepted bookings finish.
- **Limits:** bundled single-worker examples and illustrative coefficients;
  retained heuristic-filtered candidates, instantaneous offers, one decision
  per driver (`max_declines=0`), and BasicRequest immediate decisions. Results
  do not establish calibration, city-scale benefits, or Phase 5c support.

Usage and assumptions: `docs/PHASE_5B.md`. Step/checkpoint/final verification
record: `docs/WORK_LOG.md`. Final evidence: `docs/validation/phase5b/`.

Final gate: **213 tests passed**, zero failures/skips, in 818.86s. The suite
completed 126 simulations; the controlled comparisons add 18 for **144**
final-source runs. All outputs were audited, all accepted bookings finished,
and six historical controls matched 24 saved tables exactly.

## Phase 5c: native Alonso-Mora forbid/rematch

- **Problem:** removing a declined request from the chosen batch plan alone
  does not let the optimizer find another driver. Injecting manual alternatives
  risks corrupting its cached trip/assignment state.
- **Change:** opt-in `op_driver_acceptance_forbid_rematch` removes negative
  request/driver edges and their cached trips, then re-solves the retained
  native Gurobi assignment problem at the same simulation time. Exclusions
  persist through graph rebuilds and clear when the request is deleted.
- **Protection:** temporary constraints preserve new accepted request/driver
  pairs. Existing commitments remain mandatory. Actual logit menus keep the
  one-new-acceptance-per-driver limit across all solve passes. No vehicle-state
  replay, new rider wait window, or manually injected fallback tour is needed.
- **Audit integrity:** use one cached decision per pair and buffer genuine
  attempt rows until the solve settles. Only the last real refusal for a
  request still unassigned becomes terminal; recovered riders have no false
  terminal flag. New logs record passes, decisions, removals, and counters.
- **Measured benefit and tradeoff:** three matched seed-0/1/2 comparisons at
  sigma 0.3 complete 18 runs. Mean completed trips increase **54.67 → 77.33**
  for standard batch, **53.00 → 78.67** with menus, and **52.67 → 76.67**
  with future value. Conditional waits increase in all three comparisons.
  Every accepted booking finishes; these are illustrative small-example results.
- **Checks:** actual native-solver graph/constraint tests, complete probability
  boundaries and feature combinations, exact disabled-path comparisons, fresh-
  process replay, and six exact historical controls cover the new path and
  compatibility. Detailed final-suite evidence is retained with the phase.
- **Limits:** single-worker Gurobi, BasicRequest batch simulation, retained
  heuristic-filtered feasible graph and frozen costs, instantaneous driver
  decisions, and illustrative class coefficients. No calibration or city-scale
  benefit is established by these runs.

Usage/assumptions: `docs/PHASE_5C.md`. Complete change/failure/fix/result record:
`docs/WORK_LOG.md`. Final raw evidence: `docs/validation/phase5c/`.

Final gate: **240 passed**, zero failures/skips, in 1039.69s; **151** complete
suite simulations plus **18** controlled runs give **169** final-source runs.
All accepted bookings finish and all outputs are audited. Historical checks
match six controls/24 tables and 22 Phase 5b ranked runs/115 tables exactly.
