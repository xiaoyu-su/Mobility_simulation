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
