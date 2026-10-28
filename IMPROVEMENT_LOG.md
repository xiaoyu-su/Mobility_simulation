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

## Phase 6: windowed parallel evaluation

- **Problem:** rerunning the full history for every policy/time window is
  expensive. Comparing arbitrary time slices can double-count requests or
  falsely treat riders still in progress as rejected.
- **Change:** opt-in `tools/windowed_eval/` captures each seed's complete
  baseline at window starts, then launches bounded fresh workers for baseline
  and candidate interventions from the same state. Closure-aware snapshots
  retain live routes, noisy legs, plans, optimizer caches, driver decisions,
  commitments and RNG state. No new serialization dependency is needed.
- **Benefit:** reuse the lead-in and run independent windows concurrently while
  preserving state. Every baseline window must exactly match the corresponding
  observation of the full baseline. Ordinary simulation and paired evaluation
  remain unchanged.
- **Accounting:** disjoint request-time cohorts, strict observation horizons,
  explicit unfinished states, actual-driver completed gross-fare credit, and
  paired statistics across seeds within each window avoid misleading attribution
  and inflated sample counts. Local interventions start baseline histories;
  they do not represent a continuous full-day candidate trajectory.
- **Integrity:** interpreter/dependency/source/payload/prefix checks, isolated
  outputs, immutable-baseline checks, actual-model flags, per-worker logs,
  timeouts and cancellation retain successful and failed execution evidence.
- **Scope:** same-controller acceptance/choice/reward/dispatch interventions for
  the three baseline controllers, BasicRequest, two Python road routers and
  single-worker Gurobi. Incompatible controller/fleet/search changes are rejected.

Usage/assumptions: `docs/PHASE_6.md`. Step, correction and verification record:
`docs/WORK_LOG.md`. Final tests, measured timings, cohort outcomes and raw evidence:
`docs/validation/phase6/`.

Final gate: **270 passed**, zero failures/skips, in 1243.77s. Independent audits
cover **182 full simulations +144 bounded restored windows**; all accepted
full-run bookings finish. All 151 corresponding historical simulations match
849 saved tables exactly. One → two workers measures **1.78–2.00×** faster
window execution and **1.43–1.61×** faster total execution including baseline/
snapshot overhead. Conditional waits increase in the measured dispatch
interventions; window censoring remains explicit. These are local baseline-
history comparisons and descriptive small-example timings.

## Phase 7: market-data preparation and HiGHS repositioning

- **Problem:** city experiments need reproducible source-to-demand conversion,
  independent training/held-out evaluation, explicit supply/patience assumptions
  and a repositioning optimizer that fits beyond a restricted commercial license.
- **Change:** add chunked TLC CSV/Parquet preparation, deterministic sampling,
  auditable filters, mapped road centroids, training-only travel/noise fitting,
  historical forecasts, workload-based supply profiles and optional existing
  TimeBasedFS. Private hashed bundles include vehicle specifications and costs.
- **Repositioning:** opt-in PavoneFCHiGHS uses SciPy MILP, integer-safe excess
  targets, idle-capacity/conservation checks, isolated vehicle draws and native
  plan assignment. Existing strategies and default simulation behavior remain.
- **Reporting integrity:** verify actual loaded patience and complete bookings;
  compare matched inputs across complete policy runs; reject duplicate joins;
  keep raw parked-leg records while explicitly bounding initial inactivity for
  accounting. Unknown observed waits/completion/utilization remain unavailable.
- **Scope:** complete fixture checks exercise all three matching controllers,
  all three supported routers, driver classes, execution noise, future value,
  changing fleets, repositioning and exact replay. Full source and regression
  evidence accompany final results.
- **At initial delivery:** public downloads were blocked by the cloud proxy.
  The follow-up below records verified public sources and real experiments.
  Real calibration remains incomplete. No fixture result is presented as a
  real NYC measurement; the plan's numbers are not claimed as reproduced.

Commands/assumptions: `docs/PHASE_7.md`. Complete correction/verification record:
`docs/WORK_LOG.md`. Final source, fixtures, data-access diagnostics, raw runs,
reports and regression comparisons: `docs/validation/phase7/`.

Final gate: **310 tests passed**, zero failures/skips, in 1506.82s. Independent
audits cover **219 complete simulations +32 restored windows**, including 56
new market-pipeline full runs. Historical checks match 163 full runs/921 tables
and 128 window tables exactly. All accepted full-run bookings finish.

The 24 additional fixture comparisons retain actual tradeoffs: empty driving
increases, waits decrease, completion is unchanged in two configurations and
slightly higher in two, and modeled net earnings fall in two. These are fixture
outcomes. The real-data follow-up below does not change those historical results.

## Real Manhattan investigation after Phase 7 delivery

- **Change and purpose:** resolve public host access, verify actual trip/road/
  zone inputs, then test why real waiting times differ. Preserve simulator code
  and original inputs while deriving separate hashed experimental bundles.
- **Measured defects:** flooring request time produces early pickups; centroid
  co-location produces instant service; the training window omits carry-in;
  reports compare arrival with passenger pickup; pooling and curb assumptions
  differ from the observed cohort. A rare noisy trip also exceeds the finite
  four-hour tail and fails the booked-completion guard.
- **Benefit and limits:** causal admission eliminates early pickups in tested
  alternatives; spatial/event corrections improve parts of the wait comparison.
  Training-only curb sensitivity improves total-wait fit but reduces completion
  and worsens arrival fit. These trade-offs remain visible. This is an input/
  measurement investigation, not a completed calibration or production default
  change.
- **Record:** [full investigation](docs/REAL_MANHATTAN_INVESTIGATION.md), including
  exact cohorts, all configurations, actual runs, failures, source hashes,
  matched event definitions and outstanding work.

## Phase 7 production corrections

- **Problem:** the real-data investigation exposed early admission, missing
  source pooling consent, pickup/drop-off service coupling, truncated noisy
  bookings and comparisons between different event definitions.
- **Change:** causal grid admission with horizon retention, training-only
  patience, historical carry-in, separate warm-up IDs, deterministic road-node
  imputation with polygon constraints, source consent in plan feasibility,
  separate physical service durations, bounded audited completion and matched
  event/cohort reports. Existing operators keep their opt-in defaults.
- **Benefit:** requests cannot be served before their source clock; private
  riders remain exclusive; accepted bookings finish physically; wait comparisons
  disclose the event and observed coverage. Repaired original failed cases
  preserve original assignments and completed trip times/fares.
- **Validation:** 327 tests pass, with independent checks of 201 complete
  simulations and 32 restored windows. Real multi-seed, second-date, warm-up,
  changing-fleet and full-demand comparisons retain both improvements and
  residual errors. The TUM 24-hour control matches five files byte for byte;
  original commercial-solver repositioning remains license-limited.
- **Limits:** remaining real calibration errors are measured, not declared
  solved. Online fleet exposure, unserved demand and true driver coefficients
  are unavailable in these public completed-trip records. Financial outcomes
  are illustrative whole-run model values, not observed NYC driver wages.
- **Record:** [production corrections and results](docs/PHASE_7_COMPLETION.md),
  [step-by-step log](docs/WORK_LOG.md) and
  [complete validation records](docs/validation/phase7-completion/).

## Phase 8: mixed human/AV product, Round 1

- **Problem:** a shared matching platform needs explicit rules for a distinct AV
  product, rather than treating AVs as human drivers with a different label.
  Allocation incentives can otherwise violate service areas or silently change
  supply, shifts and rider consent.
- **Change:** opt-in loaded AV types, both-endpoint geofence, deterministic
  nested rider opt-in, rider-second matching preference, probability-one AV
  acceptance, fenced initial placement, human shift/reposition exclusion,
  committed-dispatch proximity diagnostics and historical-demand Hungarian
  AV repositioning. Shared plan feasibility enforces constraints under insertion
  and native batch matching; actual executed service is independently checked.
- **Benefit measured:** in 18 matched-seed sampled Manhattan runs, +300s
  preference plus AV demand repositioning raises AV served share **3.28%→9.70%**
  and productive utilization **13.9%→40.6%** relative to preference 0/repo off.
  All accepted bookings finish and AV rule violations are zero. Total fleet
  stays fixed: 78 AVs and 697 humans.
- **Tradeoffs:** total mean completion rises only **3,133.7→3,144.0 of 3,150**;
  human trips/online hour fall **6.33%** and whole-run empty AV repositioning
  averages **827.1 km**. Preference alone worsens completion and eligible-rider
  wait. Repositioning alone offers a better eligible-rider wait than the combined
  high-preference policy. Lower idle time may mean more empty driving.
- **Validation:** the focused gate passes 12 tests/16 full physical simulations,
  including all three controllers, actual type/config loaders, human acceptance,
  future value, private consent, physical service, dynamic human shifts and
  exact replay. The final full suite passes **339 tests** in 1874.71s, with
  independent checks of **217 full simulations +32 restored windows**.
  **201** historical full runs match **930 byte-identical tables**, and restored
  windows match **128 exact tables**. All 18 real runs pass independent checks.
- **Scope:** 10% public demand, three simulation seeds, 60s grid, explicit
  unobserved adoption/fence/supply assumptions; no field-benefit, full-demand AV
  or cross-city claim. Cautious speeds and threshold dispatch are later rounds.
- **Record:** [Phase 8 guide and results](docs/PHASE_8.md),
  [step-by-step log](docs/WORK_LOG.md), [complete evidence](docs/validation/phase8/).

## Phase 9: cautious AV policy experiments, Round 2

- **Problem:** vehicle-type speed declarations must survive the actual CSV
  loader and affect both planning and movement. A matching bonus alone does
  not express a rider pickup-ETA allowance; later batch reoptimization can also
  silently change an accepted service product.
- **Change:** validated per-type travel-time factors in loaded vehicles, plans,
  native vehicle copies, fallback ETAs and physical execution; AV-first feasible
  ETA thresholds with identical per-class candidate search in controls;
  accepted human/AV product protection; moving-empty retargeting; isolated
  forecast-error streams; training-only eligible forecasts and bounded residual
  human demand in joint repositioning. Existing settings retain old behavior.
- **Benefit verified:** the real loader/physical-route tests cover all three
  controllers; the two insertion controllers support threshold dispatch and
  combined human acceptance, future value and shift cases. A discovered
  insertion-plus-batch bug changes from 34 AV choices /11 AV completions to
  **34 /34** after accepted-product protection. Actual service is checked in
  addition to proposal logs.
- **Validation:** **370 tests pass** in 2045.38 seconds; independent inspection
  covers **234 full simulations +32 restored windows**. Historical non-AV
  behavior matches **201 full runs /930 byte-identical tables** and **128 exact
  restored-window tables**. Failed/interrupted candidates remain preserved.
- **Measured allocation gains and costs:** across six sampled seeds, cautious
  threshold 240 versus the same-search cost control raises AV served share
  **0.47%→5.76%** and occupied utilization **2.42%→29.46%**, while human trips
  per online hour fall **5.04%**. Mean completion rises by 9 of 3150 requests,
  but its conditional interval includes zero. Relative to threshold 0, the
  larger threshold increases eligible served wait by **23.17s**. Retargeting
  reduces empty-distance share against its callback-matched control, with no
  mean completion gain and worse eligible wait. These are conditional model
  tradeoffs, not a claim of universally better service.
- **Real validation:** all **56 physical policy runs** pass independent output
  checks, with three exact seven-file control replays. **14 historical AV-default
  cases /93 tables** also match byte for byte. The single-seed full-demand pair completes **31720→31831 of 32,192 evaluation requests**, with actual AV completions **317→2139**, AV served share **1.00%→6.72%**, and AV occupied utilization **5.44%→35.23%**. Eligible served mean arrival wait changes **165.99→180.85s**; human trips per online hour change **1.4663→1.3864**. Whole-run AV empty-distance share changes **77.59%→42.42%**, while absolute empty AV distance increases **3715.15→6010.40km**. A lower empty share is not an absolute empty-driving reduction. Both runs clear every accepted booking and all physical/product checks. This is a one-seed scale check, with no replicated full-demand interval or full-day claim.
- **Scope:** empirical trips/network are available; .3 opt-in and 1.25 travel
  time are explicit assumptions. Thresholds apply to retained feasible plans at
  dispatch, not actual pickup guarantees. Native global-batch threshold dispatch,
  mixed multi-item human menus, daily AV benchmarks and cross-city validation
  are outside this profile. Inaccessible external reference figures are not
  presented as verified field targets.
- **Record:** [Phase 9 implementation and experiment design](docs/PHASE_9.md),
  [data and assumptions](docs/AV_DATA.md), [step-by-step log](docs/WORK_LOG.md)
  and [complete validation evidence](docs/validation/phase9/).


## Phase 10: cross-city AV policy comparison, Round 3

- **Problem:** city-specific pipelines and unmatched vehicle placement/search
  confound transfer of the AV policy findings. Native map ambiguities and raw
  boarding unions also need explicit interpretation before trusting results.
- **Change:** generic native-data builder/runner/reporter, immutable parent
  adaptation, audited Munich map tie rule, hashed C++ runtime, common physical
  all-human/AV placement and benchmark-only shadow search groups. Capacity
  checks use moving and pre/post-stop occupancy with actual vehicle limits.
  Isolated pinned workers and source/input/output guards support reproducibility.
- **Benefit verified:** full unique demand, completed accepted bookings,
  chronology, actual capacities, service durations, consent, fence, product,
  speed factors and common placement pass in all66 real physical runs. Six
  fresh-process repeats match critical files byte for byte;60 conditions remain
  independent of those repeats. All53 within-study background checks pass.
- **Regression:**389 tests pass in2129.86s, covering257 complete physical
  simulations and32 restored windows. All234 historical physical cases retain
 1171 byte-identical checked tables;128 window tables retain exact values.
  Failed candidates and their corrections are preserved, not counted as passes.
- **Measured transfer and costs:** threshold0→240 raises main AV utilization
 33.64→52.80% Chicago100 and13.12→20.00% Manhattan775; Munich50 stays
 38.75→38.66%. Completion changes+16.5/+6/+7.5; Manhattan eligible wait
  rises62.72s. Against all-human controls, completion is+19.5/−30/−29.5.
  With doubled fleets, threshold completion changes−14 Chicago200/−12 Munich100.
  Chicago200 AV trips fall79.5→56 despite higher occupied utilization and longer
  completed passenger trips. Gains and regressions are both retained.
- **Scope:** two seeds, fixed replacement fleets, assumed adoption/speed/service
  settings, unequal/sparse references and native source-generation differences.
  These demo/load settings do not reproduce the screenshot's numerical regimes;
  there is no universal policy gain, daily AV claim or geography-only causality.
- **Record:** [implementation and assumptions](docs/PHASE_10.md),
  [complete results](docs/validation/phase10/RESULTS.md),
  [evidence and restoration](docs/validation/phase10/README.md),
  [step-by-step record](docs/WORK_LOG.md).


## Phase 11: native upstream fidelity and consolidated validation

- **Problem:** small bundled references alone do not prove native-city
  compatibility, reference import isolation or clean-source repeatability.
- **Change:** reusable `tools.native_fidelity` runner and neutral worker,
  immutable upstream Git archive, verified shared vehicle/native runtime inputs,
  one CPU/thread, explicit legacy-profile adaptations and isolated imports.
  Full cells/columns/rows/missing values in four output tables are compared;
  no reference is silently regenerated or approved.
- **Benefit verified:** all three bundled controllers and original native
  city profiles retain exact outputs. Upstream/fork pairs match24 complete
  tables byte for byte, fresh-process repeats match24 more and a clean
  published archive matches12. Every accepted rider completes, with full unique
  demand, actual initialization/SOC, chronology, capacity and physical boarding/
  alighting verified. The improvement is validation coverage, not policy service.
- **Validation:**403 tests pass;269 complete regression simulations,32 restored
  windows and15 native physical runs pass. All257 historical full cases retain
  1548 byte-identical checked tables;128 window tables retain exact values.
  Initial invalid-CPU launches occurred before Python/simulation startup and
  are retained separately. Both focused successful source snapshots are saved.
- **Measured native service, unchanged on both sources:**617/1788 Munich,
  5106/12753 Chicago,5399/10700 Manhattan. Native profiles have their original
  clocks/fleets/data and explicit no-repositioning/router/timeout adaptations;
  no direct Phase10 gain, screenshot-total replication or field calibration
  claim is made. Original route warnings are retained with verified completion.
- **Record:**[phase guide](docs/PHASE_11.md),
  [results](docs/validation/phase11/RESULTS.md),
  [complete evidence](docs/validation/phase11/README.md),
  [work log](docs/WORK_LOG.md).


## Phase12: separate-reference AV demand repositioning across cities

- **Problem:** cross-city dispatch experiments left idle AV location fixed.
  A real Chicago pilot also exposes unlocked rebalancing waypoints surviving
  between passenger pickup/dropoff:8 moving occupied reposition legs /18.986561km.
- **Change:** optional strict reference OD exports/weights, matched AV demand
  repositioning on/off, actual command-to-movement auditing, and opt-in service
  priority that removes only cancellable AV targets from copied plans before
  feasibility, ETA and utility evaluation. Hard locks/live plans are retained.
  Existing profiles keep their previous behavior. No actual output is relabeled
  to hide the pilot gap.
- **Verified benefit:** corrected Chicago pilot occupied repositioning legs8→0,
  actual service-preemption auditing, all accepted bookings physically complete,
  private riders protected, and targeted legacy/priority counterexamples.
  Both controllers/native C++ and combinations with acceptance, future value,
  shifts, retargeting, joint planning and forecast noise pass complete checks.
- **Validation:**424 tests,306 full regression simulations,32 restored windows
  and 72 real runs pass. All 269 historical full cases retain
  1596 byte-identical checked tables;128 window tables retain exact
  values. All 26 comparable historical real controls retain
  214 critical file comparisons. Failed tests, real pilot
  evidence, lock-copy correction and result-collector bookkeeping are preserved.
- **Measured policy effects:** three seeds, main fleets50/100/775 and a
  doubled-supply sensitivity;63 unique conditions plus nine exact replays.
  Completion/allocation/wait/empty-distance effects vary across seeds and
  regimes. Keep gains and adverse outcomes together; empty-distance fraction
  and occupied utilization alone do not establish service improvements.
- **Scope:** stationary relative OD weights, sparse native night reference,
  historical Manhattan context, assumed opt-in/speed/patience/fleet and different
  source years/generation. No calibrated future-volume, geography-only causal,
  field AV throughput or universal gain claim.
- **Record:**[phase guide](docs/PHASE_12.md),
  [full results](docs/validation/phase12/RESULTS.md),
  [evidence](docs/validation/phase12/README.md),[work log](docs/WORK_LOG.md).


## Phase 13: Chicago threshold/speed mechanism accounting

- **Problem:** higher occupied AV utilization can coexist with fewer AV trips;
  count, passenger duration, clock clipping, service dwell and shared exposure
  have different domains and previously lacked an exact reconciliation.
- **Change:** add read-only SHA-guarded event/interval accounting and a fixed
  threshold0/120/240/480 × speed1/1.25 × fleet100/200 × three-seed study.
  Preserve original module reports and separately hash supplementary analysis.
- **Verified benefit:** all 64 physical runs pass independent event-sweep
  exposure reconstruction; 60 main paired identities close exactly. Same-request
  time changes are separated from gained/lost AV selection. Moving passenger
  overlap is distinguished from stationary exchange unions and group size.
  No existing simulation policy/source/default changes.
- **Validation:** 433 passing tests, 324 full regression simulations, 32 windows;
  all 306 previous full cases preserve 2234 checked tables byte for byte,
  128 window tables remain exact, and 23 old real controls preserve
  195 critical comparisons. Ten replays supplement 54 unique conditions.
- **Measured effects:** completion, waits, AV allocation, passenger duration,
  utilization and empty-driving costs are retained, including adverse directions.
  Exact time contributions explain recorded arithmetic; they do not identify a
  causal mediation effect or empirically calibrate AV deployment.
- **Records:** [guide](docs/PHASE_13.md),
  [results](docs/validation/phase13/RESULTS.md),
  [same-request analysis](docs/validation/phase13/REQUEST_COMPOSITION.md),
  [evidence](docs/validation/phase13/README.md), [work log](docs/WORK_LOG.md).


## Phase 14: booking-patience sensitivity and input-stratum safety

- **Problem:** the latest-start/patience assumption can materially determine
  completion; offered deadlines and realized lateness have different meanings.
  City/fleet labels alone do not identify a comparable input regime.
- **Change:** enforce compatible input contracts in ordinary city summaries;
  add explicit patience strata, controlled-input checks, accepted-offer bounds,
  preserved actual late pickups and a fixed 480-second service target. Run the
  prespecified three-city/three-seed/three-cutoff matched policy study.
- **Verified benefit:** all 90 physical records pass independent deadline,
  event-sweep, capacity, privacy, service, product and completion checks. Nine
  replays supplement81 unique conditions. Source-clock feasibility probes work
  on both controllers and C++ routing. Generic reports reject input conflation.
- **Validation:**442 tests,360 full regressions,32 restored windows; all 324
  prior full cases preserve 2402 checked tables byte for byte and 128
  window tables retain exact values. All 27 default-cutoff controls preserve
  225 critical file comparisons. Matching-policy code is unchanged.
- **Measured results:** completions, a common actual-service target, AV
  allocation/utilization, same-served waits, late pickups and empty driving are
  retained at every cutoff, including adverse and non-monotone directions.
  Sensitivity is not fitted cancellation behavior or field AV calibration.
- **Records:**[guide](docs/PHASE_14.md),
  [results](docs/validation/phase14/RESULTS.md),
  [robustness](docs/validation/phase14/ROBUSTNESS.md),
  [evidence](docs/validation/phase14/README.md),[work log](docs/WORK_LOG.md).


## Phase 15 — rider opt-in robustness

- **What changed:** read-only opt-in strata/report/figures and loaded regression
  tests for nested0/30/100% eligibility. Fixed baseline/additional/outside-fence
  groups retain request IDs and denominators; paired effects preserve omitted
  zero-denominator waits and common-served selection.
- **Why/benefit:** adoption is unobserved in the completed-trip sources. Report
  expanding eligibility separately from changes to the served rider mix and
  external effects on riders who never enter the fence. Verify all-human
  invariance and zero-opt-in threshold equivalence physically.
- **Validation:**452 tests,396 complete regression simulations,32 windows and90
  real physical records /81 unique conditions /nine exact replays pass. All269
  previous source files and all360 previous full cases remain unchanged.
- **Measured effects:** every city/seed/assumption and adverse outcome remains in
  [results](docs/validation/phase15/ROBUSTNESS.md); source demand, fleet, fence,
  speed,480s offer cutoff and actual lateness are held fixed or retained. This
  adds sensitivity evidence, not estimated real adoption or a new dispatch rule.

Exact commands, initial reporting failures/fixes, changes/benefits and complete
source/input/output evidence are in [Phase15](docs/PHASE_15.md) and the work log.
