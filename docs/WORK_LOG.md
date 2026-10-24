# Development work log

Records describe work actually performed. Planned benefits are separated from
measured outcomes; source screenshots are not evidence of implemented results.
All dates below use America/Los_Angeles.

## Phase 0 — baseline hygiene (2026-10-23)

- Preserved upstream commit `c813728b6d188df8dd7fd5d3d36dcb0a55c898a2`
  through independent Git archives and approved CSV references.
- Added three complete simulation regressions and five focused unit cases;
  reproduced the five unit failures before making fixes.
- Fixed batch retry/rejection, aggregate forecast grouping, and default solver
  dumps. Reason: establish a trustworthy starting point for later policies.
- Verification: `python -m pytest -q` → **8 passed**; independently regenerated
  references compared identically; an intentional 93→92 served-count mutation
  caused the regression to fail and was restored byte for byte.
- Benefit demonstrated: unchanged bundled rider/evaluation outputs and a test
  that detects drift. Broader parity is not established.

## Phase 1 — independent streams and paired evaluation (2026-10-23)

### Step 1: inspect and establish the compatibility contract

- Found global NumPy reseeding in passenger demand, parcel demand, and batch
  optimizer initialization; traveler choice and vehicle placement also use
  global randomness.
- Preserve `random_stream_mode=legacy` as the default. Add an explicit
  `independent` mode rather than silently changing existing seeded outputs.
- Planned benefit: policy-dependent random draws cannot perturb the isolated
  demand, initial-state, traveler, or optimizer streams.
- Scope: single-worker bundled matching workflows first. Advanced stochastic
  repositioning/forecast modules and optimizer worker processes need separate
  isolation work before paired causal comparisons are claimed for them.
- Baseline checkpoint command: `.venv/bin/python -m pytest -q` → **8 passed**
  in 12.74 seconds before Phase 1 edits.

### Step 2: implement named streams and check compatibility

- Added SHA-256-name-derived NumPy `SeedSequence`/PCG64 generators. Stream
  creation order, unrelated draws, and Python's process hash salt do not affect
  a named stream. The default path retains the original global draw calls.
- Isolated passenger/parcel class assignment, per-request choices, per-vehicle
  placement/SOC, and Alonso-Mora shuffling/solver seed. Added startup input,
  network, and initial-fleet fingerprints in independent mode.
- The first focused run found that parcel earliest-start times can be null;
  corrected the audit serialization and retained a parcel interference test.
  A second failure was a test fixture missing `nr_mod_operators`; corrected
  that fixture to use the traveler model's required scenario parameters.
- Verification: `python -m pytest tests/unit tests/regression -q` → **19 passed**
  in 13.31 seconds, including all three exact Phase 0 simulation references.
- Benefit demonstrated: isolated input draws with unchanged legacy outputs.

### Step 3: metrics, inference, and the first full evaluator run

- Added per-driver time/fare/cost accounting, distribution summaries, and
  paired-seed tests with confidence intervals. Unit examples independently
  specify expected time totals, cents, quantiles, Gini, and statistical values.
- First focused metrics run: **13 passed**. The first actual CLI experiment
  then failed because existing FleetPy outputs include trips finishing after
  `end_time`; rejecting those records was an incorrect evaluator assumption.
- Diagnosis: `FleetSimulationBase.record_remaining_assignments()` drains
  pending work after the configured horizon. Revised accounting to include
  exact tail legs/fares, record each vehicle's `tail_time_s` and accounting end,
  and extend only that vehicle's time/cost exposure. Added a tail-work case.
- Benefit: no discarded tail revenue, no uncounted work, and no invented
  proportional allocation of distance within partially observed legs.

### Step 4: validate real paired runs and failure handling

- Corrected tail accounting passed **14 focused cases** in 0.56 seconds.
- Ran the CLI on insertion versus immediate/batch matching at seeds 0, 1, 2.
  All six simulations completed; demand, network, and initial-state audit
  records matched in all three pairs.
- Added complete CLI integration cases for identical policies and different
  policies at seeds 3 and 9. Identical policies reproduce exact rider/evaluation
  cells and zero finite paired differences. Changing the seed changes the
  starting-fleet fingerprint. Each run includes five roster vehicles.
- Negative checks reject mismatched demand/network/initial state/seed,
  unsupported workflows, duplicate riders, overlapping or malformed activity,
  and existing output directories. An overwrite attempt leaves the existing
  experiment manifest unchanged.
- Full checkpoint: `python -m pytest -q` → **39 passed** in 45.69 seconds.
- Benefit demonstrated: the evaluator measures actual end-to-end policy runs,
  verifies their exogenous pairing, and retains auditable failure records.

### Step 5: finalize source provenance, accounting checks, and reproducibility

- Added an exact loaded-request/output-count check to the worker, nonfinite or
  negative vehicle-cost rejection, and source-change detection across a run.
  Source fingerprints include uncommitted and untracked Python files.
- Configuration snapshots retain CSV/YAML suffixes rather than relabeling
  formats. Seed-range checks fail before creating an experiment directory.
- Final command: `.venv/bin/python -m pytest -q` → **41 passed**, **0 failed**,
  **0 skipped**, in **45.67 seconds**. This includes the three unchanged
  Phase 0 reference comparisons and both complete paired CLI integration cases.
- Re-ran the final CLI implementation on insertion versus immediate/batch
  matching, seeds 0/1/2, at `/workspace/.setup/phase1/verified-comparison`.
  All six simulations exited zero and all three input audits matched.
- Mean completed requests: 93 versus 93. Mean rider wait: 150.81 versus
  141.35 seconds; candidate-minus-baseline -9.46 seconds, 95% paired t interval
  [-16.16, -2.76], t-test p=0.026, Wilcoxon p=0.25. This small development
  demonstration is not a general policy finding or a multiple-testing-adjusted
  inference. It verifies that the reporting path preserves statistical detail.
- Archived the actual final manifest, four CSV reports, source/config/output
  hashes, and machine-readable test evidence in `docs/validation/phase1/`.
  Full simulation artifacts and stdout/stderr remain in the recorded local run
  directory. Failed development attempts remain separately identifiable.

### Delivered changes, reasons, and benefits

| Change | Why | Benefit/evidence |
| --- | --- | --- |
| Named, opt-in streams | Global reseeding couples unrelated components | Isolation tests pass; legacy references unchanged |
| Per-request and per-vehicle streams | Policy-dependent iteration can shift shared draws | Stable request choices and matching initial-state audits |
| Explicit optimizer/solver seeds | Construction randomness should not alter demand | Optimizer initialization leaves global state untouched |
| Driver roster accounting | Zero-activity vehicles and costs affect distributions | Hand-checked idle/inactive drivers, cents, and tail-work cases |
| Paired inference across seeds | Drivers within one simulation are not independent replicates | Checked mean/CI/t/Wilcoxon values and explicit undefined cases |
| Input and source audits | Equal seed labels alone do not prove a fair/reproducible run | Actual loaded inputs match; source changes prevent completion |
| Preserved artifacts and documentation | A result without its setup cannot be reviewed | Configs, commands, versions, logs, hashes, reports, and this history retained |

Limits and metric definitions are in `docs/PHASE_1.md`. Single-worker baseline
matching workflows are validated; other stochastic modules and worker
processes are not claimed to be isolated. Earnings are fare/vehicle-cost
proxies, not observed driver compensation. No later phase was implemented.

## Phase 2: promised times and execution uncertainty (2026-10-23)

### Step 1: inspect timing and establish the starting checkpoint

- Continued on local branch `phase-2-execution-noise`, preserving Phase 0/1 work.
- Starting suite: `.venv/bin/python -m pytest -q` → **41 passed in 46.00s**.
- Traced offer creation, booking, movement, boarding/alighting, route replacement,
  and existing `VehiclePlan` keep-feasible handling. Offers express wait relative
  to request time; actual dropoff is recorded at the start of alighting.
- Design: noise affects executed driving time only, once per started route leg;
  plans and quoted ETAs continue using routing estimates. Stationary durations,
  distance, toll calculation, and energy per meter retain their definitions.
- Freeze the selected operator's offer before booking callbacks can change it.
  Record signed actual-minus-promised errors, leaving unserved values missing.
- Defaults remain disabled; zero noise creates no execution RNG. An explicit
  `record_promised_times` flag permits noiseless diagnostics without changing
  the default rider schema. Positive noise enables those diagnostics automatically.

### Step 2: implement and verify the timing boundary

- Added settings validation, private per-vehicle execution streams, mean-one
  lognormal multipliers, wall-clock conversion of router arrival/replay times,
  and per-leg multiplier records when noise is active.
- Added immutable accepted-offer snapshots and optional pickup/dropoff errors.
  Paired evaluation includes error counts, missing counts, mean, population
  standard deviation, MAE, quantiles, and late fraction when these records exist.
- Focused checks cover fast/slow movement across update steps, unchanged-leg
  reassignment, stationary service, distance/energy, replay timestamps, serving
  operator selection, and missing-service accounting. Results recorded below.
- First focused/regression run: **14 passed, 2 failed in 12.61s**. Both failures
  were new assertions referencing a nonexistent replay column. FleetPy stores
  replay as `trajectory` entries `node:time`; corrected the assertions to read
  that existing format. All movement/accounting assertions had passed.
- Added a real `VehiclePlan` case: a previously feasible committed pickup and
  dropoff become late; keep-feasible retains/infeasible-locks their stops, and
  the vehicle boards and finishes the rider after the original deadlines.
- Corrected focused suite: **14 passed in 0.24s**.

### Step 3: run complete examples and extend the paired experiment path

- Ran the original three full 100-request scenarios at sigma 0.6 using fresh
  output directories. All finished, with 86/89/91 completed riders respectively
  for insertion/immediate-batch/batch. Every accepted booking completed; no
  served rider lacked a promise. Completion differences are measured outcomes,
  not a fixed target or evidence of policy superiority.
- Observed signed pickup-error population SDs: 86.47/88.47/99.87 seconds.
  Actual pickup errors reached 322.08/533.11/533.11 seconds respectively.
  These exercise late committed service in all three full workflows.
- Raw smoke artifacts: `/workspace/.setup/phase2/smoke-v1/`; console logs are
  `/workspace/.setup/phase2-{insertion,immediate_batch,batch}-v1.log`.
- Added common `--network-tt-noise-sigma` and `--record-promised-times` CLI
  overrides; they apply to both policies and are retained in commands/configs
  and the experiment manifest. Different exogenous noise settings remain
  disallowed. Error summaries flow into existing paired statistical reports.
- Explicitly reject enabled noise with external MATSim/SUMO movement, and
  promised-time recording with PT brokers, rather than produce misleading
  road-trip promises for an unsupported multimodal workflow.
- Added full sigma-0 recording comparisons and sigma-0.6 stress runs for each
  controller. Original rider/evaluation columns match upstream exactly at zero
  sigma. All noisy bookings finish, and per-driver activity accounting validates.
- Checkpoint: focused tests plus six full examples → **23 passed in 24.86s**.
- Benefit: execution uncertainty is measurable and reproducible while accepted
  commitments and deterministic compatibility are checked end to end.

### Step 4: final paired runs and reproducibility evidence

- Ran insertion versus immediate/batch policies at seeds 0/1/2, separately at
  sigma 0 and 0.3, with promise recording enabled in both arms. Each experiment
  completed six simulations; all three demand/network/initial-state audits
  matched. Both experiments recorded the same working-source digest:
  `481463b26241814fb6c0b38c876e70c05709478399493748285bef5a0f6cde97`.
- Independently compared all six sigma-0 runs with the saved Phase 1 final
  experiment: every original rider column and standard evaluation cell matches
  exactly. Added diagnostics do not change those measured outcomes.
- Mean of per-seed pickup-error population SDs, insertion/immediate-batch:
  sigma 0 → **24.33/32.06s**; sigma 0.3 → **49.20/51.90s**.
  Mean completed requests: **93/93** at sigma 0 and **89.67/89.00** at sigma 0.3.
  Every booked rider completed in all 12 runs. Rejected requests remain present
  and are counted separately from observed timing errors.
- These are small development experiments, not calibrated city results or a
  policy recommendation. Sigma is a model input, not a fitted empirical value;
  changing it can affect which requests are served and which errors are observed.
- Retained raw logs, requests, vehicle activity, final states, input audits,
  configs, and reports at `/workspace/.setup/phase2/verified-sigma-{0,0.3}`.
  Archived both actual manifests, eight reports, config snapshots, and hashes
  of every run's principal outputs in `docs/validation/phase2/`.

### Step 5: final verification and delivered changes

- Final command: `.venv/bin/python -m pytest -q` → **66 passed**, **0 failed**,
  **0 skipped**, in **101.69s**. The suite includes all three unchanged legacy
  reference comparisons, six complete zero/noisy examples, original paired CLI
  cases, and noisy identical-policy/different-policy paired CLI cases.
- Both final experiment source digests still match the current Python source;
  no code changed while experiments/tests were running. `git diff --check`
  passes. Final test output and machine-readable checks are archived beside
  the manifests and reports in `docs/validation/phase2/`.
- Updated README, project summary, improvement log, and `docs/PHASE_2.md` with
  parameters, formulas, columns, reproducible commands, interpretation, and
  scope. All changes remain local; no commits or pushes were performed.

| Change | Reason | Benefit and verification |
| --- | --- | --- |
| Frozen selected-operator promise | Final offer strings can reflect later updates or another operator | Booking callback/multiple-offer test verifies immutable correct promises |
| Mean-one noise per executed leg | Separate uncertain execution from planning estimates | Fast/slow, per-tick, per-leg, replay, distance, and energy checks pass |
| Private per-vehicle execution stream | Execution randomness must not alter exogenous inputs | Global-state isolation and matching input audits pass |
| Disabled-by-default diagnostics and noise | Preserve upstream compatibility | Exact legacy references and six saved Phase 1 run comparisons pass |
| Existing keep-feasible commitments retained | Late riders must not disappear when original deadlines are missed | Delayed-plan test and full examples retain and complete bookings |
| Signed errors and conditional summaries | Quantify bias/spread without assigning zero error to unserved riders | Hand-checked metrics and noisy paired CLI reports pass |
| Retained configs, source/input/output hashes, logs, reports | Make each result reviewable and reproducible | Two complete three-seed experiments plus step-by-step evidence archived |

Validated scope remains single-worker road-trip matching on the example data.
Phase 2 does not establish a calibrated noise level, improve the matching
objective, or implement driver acceptance. Phase 3 is the next planned stage.

## Phase 3: logistic driver acceptance and GitHub publication (2026-10-23)

### Step 1: inspect the plan and preserve the previous milestone

- Re-read the Phase 3 text in the uploaded plan image. Scope: logistic
  acceptance from pickup ETA/direct-trip distance, bounded declines/retries,
  optional probability-weighted assignment reward, driver classes, and logs.
  Multi-driver fallback/future-value matching remain separate later phases.
- Confirmed GitHub push permission on `xiaoyu-su/Mobility_simulation` and
  fetched `origin/main` (still the original upstream commit).
- Committed all completed Phase 0–2 work as `85bb47a`, then created local
  branch `phase-3-driver-acceptance`. This preserves a reviewable prior milestone
  and includes it in the eventual fork update.
- Starting validated checkpoint was **66 passed in 101.69s**, as archived in
  Phase 2. No existing source/user changes were discarded.

### Step 2: implement the driver-side boundary

- Added an off-by-default logistic model with explicit coefficients, minute/km
  units, stable sigmoid, per-vehicle driver classes, per-request/vehicle random
  streams, bounded retries, and final-decision caching.
- A matching round offers to its selected driver. `max_declines` is the number
  of retries after the first attempt (0 means one attempt); retries are
  instantaneous reoffers to that same driver. Exhaustion rejects the request.
  This does not walk other drivers or charge response latency; those require
  the later multi-offer model. Decision logs expose every attempt.
- Gate insertion proposals before a rider offer/booking. For batch assignment,
  remove terminally declined requests through the optimizer's removal API
  before vehicle plans execute; preserve committed/onboard riders.
- Snapshot the round's solver results before processing declined requests.
  The first implementation marked stripped batch plans external; the complete
  noisy batch check found that this deletes the internal trip tree, while the
  subsequent database clear removes its temporary fallback. See correction below.
- Optional objective weighting replaces only uncommitted assignment reward
  `R` by `p × R`. Operating costs and committed-rider rewards are unchanged.
  The supported objective exposes its reward explicitly; other objectives fail
  clearly when weighting is requested. The p=1 path retains base arithmetic.
- Log decisions and a class/units/seed/provenance audit. No numerical default
  is represented as empirical calibration. The screenshot's fare-per-USD
  coefficient is not reused as a trip-km coefficient.
- First unit checkpoint: **73 passed in 0.89s**, covering both new model checks
  and all prior unit cases. Full simulation checks follow below.

### Step 3: full simulation checkpoint and correction

- Ran all three controllers in always-accept, always-decline, and weighted
  logistic-plus-noise modes: **8 passed, 1 failed in 28.06s**.
- All three p=1 runs reproduce every original rider/evaluation cell exactly,
  including with optional objective weighting enabled. All three p=0 cases
  account for 100 requests, serve none, and log bounded terminal declines.
- Noisy logistic insertion and immediate/batch cases passed. The logistic
  batch case exposed `KeyError` in Alonso-Mora's next-round committed-trip
  reconstruction: the newly stripped plan had been marked external, deleting
  internal entries that must survive `clear_databases()`.
- Corrected the integration to retain the internally registered lower-trip
  plan returned by `get_vehicle_plan_without_rid()` and assign it through the
  internal path. This keeps committed-rider trip entries available next round;
  it does not alter the optimizer's global behavior when acceptance is off.
- The next focused run exposed a second lifecycle detail: the removal API
  returns its stored best plan directly, while normal solution retrieval
  returns a copy. A live controller status update could therefore consume a
  stop before the optimizer replayed that same event. Added a copy at this
  boundary, and a focused isolation test that mutates the live reduced plan
  while verifying the stored committed plan remains unchanged.
- The corrected complete noisy weighted/logistic batch case passed in **3.80s**.
- Corrected model checks, all nine acceptance simulations, and the three
  original reference regressions passed together: **35 passed in 43.26s**.

### Step 4: exercise standalone YAML scenarios and paired acceptance

- Added paired CLI cases for identical weighted-acceptance policies and
  disabled-versus-heterogeneous-class policies under common sigma 0.3.
- Their first run failed before simulation: upstream `ScenarioConfig.read_yaml`
  passed the parsed list into a constructor that expects a file path. This is
  the first workflow here to use actual YAML scenario files (the earlier
  override check used a YAML constant mapping).
- Corrected YAML scenario loading to build a list of `ConstantConfig` mappings,
  preserving nested classes and existing constant/scenario merge behavior.
  Added checks for nested coefficients and invalid YAML container shapes.
- Preserved the original failure at
  `/workspace/.setup/phase3-paired-checkpoint.log`. This necessary parser fix
  lets the documented class scenarios run through the actual command-line path.
- Corrected parser/model checks and both paired experiments passed together:
  **29 passed in 25.22s**, with one warning from an existing regex escape literal.
- Added a two-seed heterogeneous-class batch experiment to the integration
  suite and checks that a terminal driver decline cannot reopen either of the
  controller's waiting-window retry queues. These specifically exercise the
  integration boundaries found during full runs.

### Step 5: final audited experiments and retained raw evidence

- Ran two separate three-seed experiments at common sigma 0.3, seeds 0/1/2:
  original insertion versus weighted logistic acceptance with one attempt, and
  original batch assignment versus weighted heterogeneous-class acceptance
  with one retry. All **12 simulations completed**, and all **six paired
  demand/network/initial-fleet audits matched**.
- Every accepted/booked rider completed in all runs. Candidate acceptance logs
  exactly identify completed requests; terminally declined requests never serve.
- Insertion: mean completed requests **89.67 → 44.67**, mean driver declines
  **54.33**. This example uses deliberately illustrative coefficients and no
  retries; its outcome is not a calibrated prediction or a policy improvement.
- Batch classes: mean completed requests **91.00 → 76.33**, mean attempts
  **133.33**, mean declines **57.00**, mean terminal declines **16.00**.
  Attempts/declines include repeated offers, so they are not unique-rider counts.
- Retained all principal raw CSV/JSON outputs, rider/vehicle records, acceptance
  decisions, class audits, configs, console/simulation logs, reports, source
  manifests, and per-run output hashes under `docs/validation/phase3/`.
  Original run directories are `/workspace/.setup/phase3/verified-insertion`
  and `/workspace/.setup/phase3/verified-batch-classes`.
- Both experiments used the same unchanged working-source digest. The broader
  final suite is running; its actual outcome is recorded below before publication.

### Step 6: complete verification and prepare publication

- Final command: `.venv/bin/python -m pytest -q` → **107 passed**, **0 failed**,
  **0 skipped**, in **177.57s**. All earlier compatibility cases remain in the
  suite, including the three independent upstream references.
- Verified that both final experiment source digests equal the tested working
  source: `a899aa49e06c7f4fe31d9714c2a4336a04704151f05acc63cb34f3190a2254b9`.
  No Python source changed during these tests/experiments. Original baseline
  reference files are unchanged. Corrected a documentation EOF blank line, and
  `git diff --check` passes before commit.
- Archived final test output and all run/checkpoint evidence. Added the two
  previously ignored Phase 2 console logs explicitly so their existing
  validation-record hashes also resolve in the published repository.
- Updated README, project summary, improvement log, and Phase 3 documentation
  with configuration, explicit assumptions/units, retry semantics, commands,
  limitations, and measured outcomes.

| Change | Reason | Benefit and evidence |
| --- | --- | --- |
| Off-by-default logistic driver decisions | Previously all driver assignments were treated as accepted | p=0 serves none; p=1 exactly reproduces all three baseline examples |
| Isolated request/vehicle streams and fixed driver classes | Unrelated draws and ordering should not alter driver decisions | Unit isolation and identical-policy separate-process runs pass |
| Bounded retries, caching, and terminal rejection logs | Avoid unlimited offers and hidden redecisions | Per-attempt records; retry and waiting-window regression cases pass |
| Preserve operator commitments | Fresh decisions must not abandon booked/onboard riders | Committed-rider unit checks and every booking completed in 12 final runs |
| Probability-weighted assignment reward | Model expected willingness without scaling operating cost | Analytic reward/cost check, no scoring draws, exact p=1 runs |
| Correctly register/copy reduced batch plans | Declines exposed optimizer tree/plan ownership assumptions | Noisy batch and heterogeneous-class multi-seed experiments pass |
| Repair YAML scenario loading | Nested driver classes could not run through the actual CLI | Real class scenarios, merge and malformed-container checks pass |
| Complete decision/raw-output/source/input evidence | Published behavior must be reviewable | Full records and validation hashes committed alongside the implementation |

### Step 7: publish the completed work to GitHub

- User explicitly requested GitHub publication. Pushed branch
  `phase-3-driver-acceptance` to `xiaoyu-su/Mobility_simulation`.
- Published foundation commit `85bb47a` (Phases 0–2) and implementation/evidence
  commit `7d2caa4f1140a6fb0ad20db14273c6e7dc4238a8` (Phase 3).
- Opened [pull request #1](https://github.com/xiaoyu-su/Mobility_simulation/pull/1),
  targeting `main`. GitHub verified its open state, correct head/base branches,
  implementation commit, and mergeable status.
- This final publication record is a documentation-only follow-up commit.
  The tested Python-source digest remains unchanged; the **107 passing tests**
  and archived experiment checks apply to the published implementation.
- Preserved initial full-check output at
  `/workspace/.setup/phase3-acceptance-checkpoint.log`; the noisy batch case is
  retained as an end-to-end regression for this lifecycle issue.

## Phase 4: future-value matching (2026-10-24)

### Step 1: establish scope, identity, and the starting checkpoint

- Started branch `phase-4-future-value` from corrected-author Phase 3 commit
  `1c45ddf438baba02a30477ca93ae335e5ddbe58b`. Author and committer identity is
  saved locally as Xiaoyu Su, using GitHub's verified noreply address for
  `xiaoyu-su`. The earlier Lina identity was corrected for all three project
  commits; historical run manifests retain their original captured source
  provenance, while file-content hashes remain unchanged by that correction.
- Starting verification: unit cases plus the three original exact upstream
  examples → **85 passed in 13.47s**. PR #1 remains open against `main`;
  Phase 4 is kept on its own branch for a focused follow-up review.
- Implement the plan's score `p + (1 - p) × fallback`, with fallback the
  conditional probability that at least one of the top-k other drivers accepts.
  This estimates matching value and does not implement multi-driver dispatch.

### Step 2: implement a bounded, deterministic fallback estimate

- Added an opt-in scorer separate from actual driver acceptance. Existing
  probability-weighted rewards remain unchanged when it is disabled.
- Rank candidates exactly by direct road-network pickup ETA and vehicle ID,
  considering earliest/latest pickup, positioned/active vehicles, and sufficient
  total passenger capacity. Exclude the selected driver; count colocated
  drivers separately. Busy-driver route/capacity interactions remain an
  explicitly optimistic reachability proxy, not a feasible insertion guarantee.
- Freeze the live fleet once per matching round. Reuse cached nearest k+1
  candidates for every selected-driver exclusion, with one route query per
  unique position. Refresh snapshots/cache at each insertion/batch round,
  including successive requests at the same clock time. Deadline, origin,
  request size, and direct distance are included in the relevant cache keys.
- Use one-to-one routing queries rather than relying on an early-stopped
  multi-origin search for partial-edge vehicles; use the full exact candidate
  set before bounded top-k selection, with no geographic prefilter.
- Added stable chained probability arithmetic, p=1/k=0/p=0 fast paths,
  selected-proposal value records, and final settings/counter audits. Scoring
  never samples driver decisions or consumes demand/vehicle-execution streams.
- Hook the scorer into both insertion controllers and Alonso-Mora matching;
  costs, committed-rider rewards, acceptance probabilities, and offer/retry
  execution retain Phase 3 behavior.

### Step 3: targeted formula, compatibility, and complete-simulation checks

- First checkpoint: **50 passed in 12.78s**, covering new analytical/reference
  cases, Phase 3 model checks, and all three unchanged upstream references.
- Independent full-scan tests compare every selected-driver exclusion at
  k=0/1/3/20, including unreachable/late/inactive/undersized vehicles, ties,
  colocated drivers, and earliest pickup times. Tests verify same-clock snapshot
  refresh, request deadline cache keys, stable tiny probabilities, and no
  acceptance draws during scoring.
- Full-simulation checkpoint: **9 passed in 41.39s**. For each of the three
  controllers: p=1 reproduces every upstream rider/evaluation value, k=0
  reproduces the corresponding Phase 3 run and driver decisions exactly,
  and noisy logistic future-value matching finishes every accepted booking.
  Selected score records satisfy the formula; alternatives exclude the chosen
  driver; zero-fallback/p=1 paths make no routing queries.
- Added real-network partial-edge/colocated-driver comparisons, disabled-output
  checks, and paired CLI cases for identical policies and Phase 3 versus Phase
  4 on insertion and heterogeneous-class batch matching. Results follow below.

### Step 4: verify real-network exactness, reproducibility, and optimization

- Real-network partial-edge/colocation checks, output-suppression checks, and
  three paired CLI cases passed: **29 passed in 43.01s**. Identical future-value
  policies reproduce rider, evaluation, acceptance, selected-score, and counter
  audit records across separate processes. Phase 3/4 comparisons keep exogenous
  demand/network/initial-state audits matched.
- Added `tools/benchmark_future_value.py`, comparing an independent full-scan/
  sort implementation against the cached exact scorer on actual example roads.
  It checks score agreement, records source/network/workload hashes, route-call
  counts, and descriptive wall times using separate fresh network caches.
  Benchmark and final full-suite results are recorded below.

### Step 5: final matched experiments and measured results

- Compared Phase 3 probability weighting against Phase 4 future value at seeds
  0/1/2, sigma 0.3, using identical illustrative coefficients/retry settings
  within each comparison. All **12 simulations finished**, and all **six
  demand/network/initial-state audits matched**. Every accepted booking finished.
- Insertion mean completed requests: **44.67 → 42.67**. Heterogeneous-class
  batch mean completed requests: **76.33 → 71.67**. Neither experiment improved
  completion. Mean wait among served riders fell, but this conditional metric
  cannot offset the reduction in served requests or establish policy superiority.
- This is an important limit: matching value includes an optimistic fallback
  proxy, while actual alternative offers are a later phase. The change is a
  tested opt-in modeling capability, not a demonstrated dispatch improvement.
- Independently compared the six Phase 3 control runs against the archived
  Phase 3 final candidates: all rider, standard-evaluation, and driver-decision
  tables match exactly. Disabled future value preserves that prior milestone.
- Benchmark: **1,920** repeated score evaluations on the actual example network,
  32 vehicles, 12 requests, five repetitions, k=5. Maximum difference from the
  independent full-scan reference: **1.11e-16**. Routing calls **59,520 → 348**;
  measured score-evaluation wall time **93.374s → 1.464s** (63.80× on this run).
- Timing is descriptive only. The random road workload includes disconnected
  routes; the existing routing engine recalculates infinite paths in repeated
  full scans, affecting this measured ratio. It is not a city-scale or full
  simulation speedup claim. Independent query counts and mathematical agreement
  provide the primary optimization evidence.

### Step 6: final verification and commit preparation

- Final command: `.venv/bin/python -m pytest -q` → **145 passed**, **0 failed**,
  **0 skipped**, in **260.74s**. This includes every prior phase's cases,
  all three default/upstream references, Phase 3 always-accept/decline behavior,
  and the new future-value analytical, cache, road-network, complete-example,
  and paired-process checks.
- Both final paired experiments and the benchmark match the tested Python
  source digest: `965dd7abf2874d11ba39ca183328fb866377d1b3a88c858d5868febe9a81477a`.
  No Python source changed during these runs. Approved baseline reference
  files remain unchanged, and `git diff --check` passes.
- Archived full rider/vehicle/decision/selected-score records, counter audits,
  configurations, source/input/output hashes, logs, reports, benchmark JSON,
  compressed complete benchmark console output, and checkpoint/final test logs
  under `docs/validation/phase4/`.
- Reconfirmed repository Git identity before committing: **Xiaoyu Su**, email
  `209944670+xiaoyu-su@users.noreply.github.com`, for author and committer.

| Change | Why | Benefit and evidence |
| --- | --- | --- |
| Optional fallback-value reward | Immediate acceptance weighting omits alternative-driver opportunities | Formula/cost checks pass; actual outcomes recorded without claiming service improvement |
| Exact top-k of other road-ETA candidates | A geographic filter or selected-driver inclusion would change the intended estimate | Independent full scans, ties/colocation, exclusions, and real partial-edge tests agree |
| Round-scoped shortlist/probability caches | Repeated plan scoring should not reroute the whole fleet | Reference agreement within 1.11e-16; benchmark calls 59,520 to 348 |
| Explicit snapshot refresh and request keys | Time, network, availability, or deadline changes can invalidate cached values | Same-clock refresh and geometry/window cases pass |
| Separate deterministic scoring from actual acceptance | An optimistic value must not become an inflated acceptance draw | Selected proposal can still decline at its original p; no offers sent to alternatives |
| Disabled/k=0/p=1 compatibility | Preserve previously validated behavior | Three-controller exact checks and six saved Phase 3 control comparisons pass |
| Selected-score/counter audits and complete artifacts | Modeling assumptions and performance claims need reviewable evidence | Formula inputs, alternatives, counters, raw outcomes, and all hashes archived |

No actual multi-driver fallback, repositioning policy, city calibration, or
guaranteed service improvement is introduced. Those remain separate work.

### Step 7: commit and publish as Xiaoyu Su

- Committed implementation, documentation, tests, benchmark, and complete
  evidence as `3900e84fe6bd2bce61a8ee51e396f7184bde8b7c`.
- Pushed `phase-4-future-value` and opened
  [PR #2](https://github.com/xiaoyu-su/Mobility_simulation/pull/2), based on
  `phase-3-driver-acceptance` for a focused Phase 4 review while PR #1 remains open.
- GitHub verified both author and committer as **Xiaoyu Su**, linked to
  **xiaoyu-su**. No upstream/contributor identities were changed.
- This publication record is a documentation-only follow-up. The tested source
  digest and all archived experiment/benchmark artifact hashes remain unchanged.

## Phase 5: driver choice and conflict resolution (2026-10-23, America/Los_Angeles)

### Step 1: preserve scope, baseline, and author identity

- Re-read the uploaded Phase 5/5b/5c plan. This phase implements logit driver
  choice plus greedy conflict resolution and single-item compatibility. Ranked
  insertion fallback (5b) and Alonso-Mora forbid/rematch (5c) remain separate.
- Started `phase-5-driver-choice` from `c15ce34`, preserving Phase 4 and its
  documented non-improvement results. Starting unit/reference checkpoint:
  **111 passed in 14.80s**. Reconfirmed saved author/committer: **Xiaoyu Su**,
  verified GitHub identity `xiaoyu-su`.

### Step 2: implement choice, conflict resolution, and safe integration

- Added stable multinomial logit choice over request items and an outside
  option. Utilities are `log(p)-log(1-p)` from Phase 3's per-offer probability;
  outside utility is zero. Single-item probabilities retain exact Bernoulli
  arithmetic. Probability-one ties are uniform; impossible items have zero mass.
- Added deterministic greedy conflict resolution, ordered by supplied priority,
  conditional choice probability, driver ID, and request ID. A request and a
  driver can win at most once in an episode; protected commitments are excluded.
- Added disabled-by-default `op_driver_choice_model`: `singleton` delegates
  exact Phase 3 draws/retries and preserves pooled-plan behavior; `logit` builds
  menus from solver-selected new requests and permits one new choice per driver.
  Actual menus require zero retries to avoid silently inventing sequential menu
  dynamics. Insertion still has one selected proposal in Phase 5.
- Batch menus resolve before plans execute. Resolved outcomes are cached; the
  existing reduced-plan path removes declined/unselected items without another
  Bernoulli draw. Committed/onboard riders never enter a new menu.
- Added detailed per-item choice logs, probability intervals, outside choices,
  legacy-delegation flags, settings/stream audits, and final counters. Existing
  acceptance logs retain their schema; categorical outcomes record conditional
  item probability and no fabricated Bernoulli draw.
- Existing unit suite after integration: **108 passed in 2.56s**. First new
  choice run: **20 passed, 1 failed in 0.29s**; disabled output exposed that CSV
  field names were initialized only when writing. Moved field-name setup outside
  the output branch so output suppression remains functional.
- Corrected focused choice tests: **21 passed in 0.25s**. Added cross-episode
  ownership protection so the same uncommitted request cannot be accepted by
  two drivers; later committed-plan reassignment remains allowed.

### Step 3: complete simulations and boundary checks

- Choice unit cases plus complete examples: **30 passed in 55.50s**. For each
  baseline controller, singleton mode exactly reproduces the original rider,
  evaluation, and driver-decision tables under p=1 and stochastic acceptance
  with retries. No choice outputs appear when disabled.
- Actual logit batch menus exercised multi-item episodes both with and without
  Phase 4 future-value scoring. Every accepted booking completed; each episode
  accepted at most one new request, with valid categorical probability totals
  and recorded draw intervals. Existing commitments stayed outside the menus.
- Added a numerical
  tail check for multiple certain items followed by impossible items, ensuring
  logged probability intervals agree with the sampler at the largest valid draw.
- Added separate-process paired cases for Phase 3 versus singleton, identical
  logit menu policies, and Phase 4 versus singleton with future value. Results
  are recorded below before commit/publication.

### Step 4: paired integration correction

- First paired checkpoint: **25 passed, 1 failed in 24.34s**. The actual menu
  case failed at startup because a newly added scope assertion required
  `user_max_decision_time=0`.
- Diagnosis: the existing batch constant config uses 60 seconds to await an
  offer, while `BasicRequest` chooses immediately when it receives that offer.
  Treating this wait window as delayed choice was incorrect. Replaced the
  assertion with explicit `BasicRequest` scope; retained all original scenario
  timings and both arms' exogenous inputs.
- Added choice-specific probability/draw interpretation to the acceptance
  audit only when choice is enabled, avoiding ambiguity for categorical rows
  while leaving default-off audit content unchanged.
- Corrected focused/model/paired checkpoint: **26 passed in 38.03s**. Separate
  processes reproduce actual menu choices and counters; singleton controls
  reproduce Phase 3 results and Phase 4 selected scores exactly.

### Step 5: final verification and controlled experiments

- Started the complete prior/new test suite with stable Python source, plus
  two final three-seed experiments at sigma 0.3: Phase 3 versus singleton, and
  single-attempt batch acceptance versus actual batch menus. Matching seeds,
  network, demand, fleet, coefficients, and retry allowance are retained in each
  pair. Actual outcomes and final test evidence are recorded below.
- Both final experiments completed **12 simulations** and **six matched input
  audits**. Every accepted booking completed; no terminally rejected item served.
- Singleton comparison: mean completed requests **44.67 → 44.67**; mean driver
  attempts **99.00 → 99.00** and item declines **54.33 → 54.33**. Rider,
  evaluation, and decision tables agree exactly in every seed.
- Actual menus: mean completed requests **54.67 → 53.00**, mean wait among
  served riders **125.02s → 136.30s**. No service improvement is demonstrated.
  Seeds 0/1/2 exercised **3/3/4** multi-item episodes respectively, with
  **54/53/52** completed/accepted riders and no abandoned bookings.
- Live solver solutions have unique request ownership, so cross-driver conflict
  rejections are correctly zero in these runs. Explicit competing-driver
  overlap/protection/tie cases exercise the generic greedy resolver separately.
  Offered-item rejection totals are not independent-driver refusal counts.

### Step 6: final configuration round-trip correction

- Initial complete suite: **179 passed**. Final input-format inspection found
  that the existing YAML 1.1/CSV decoder converts bare `off` to boolean `False`;
  explicit disabled choice/acceptance modes were rejected even though omission
  worked. This was an actual configuration-path gap, not an execution failure.
- Normalize decoded false to disabled in both mode checks. Enabled mode logic,
  probability calculations, and random streams are unchanged. Added real YAML
  and CSV round-trip cases, including acceptance enabled with choice disabled.
- Preserve the original full-suite log and first final experiments. Re-run the
  complete suite and final paired experiments from the corrected stable source;
  only those final records are used for publication.
- Corrected choice/round-trip checkpoint: **25 passed in 0.29s**. Repeated
  final runs completed all 12 simulations and six input audits. Every original
  valid-mode rider/evaluation/decision table is unchanged by the decoder fix.
  All six singleton/control tables also match the saved pre-Phase-5 controls.
- Final raw artifacts come from `/workspace/.setup/phase5/verified-v2-singleton`
  and `/workspace/.setup/phase5/verified-v2-batch-menus`. The first experiments
  remain separately preserved under `verified-singleton` and `verified-batch-menus`.

### Step 7: final verification and commit preparation

- Final corrected command: `.venv/bin/python -m pytest -q` → **181 passed**,
  **0 failed**, **0 skipped**, in **364.62s**. The earlier complete run remains
  recorded as **179 passed in 351.49s** before the explicit-off correction.
- Final experiments match the tested source digest:
  `95fee8e047878e397512fdd1a95a4d18daa2e9c0aa798346167ecfbb50452c01`.
  No Python source changed during the corrected full suite or final experiments.
  Approved upstream baseline files are unchanged; `git diff --check` passes.
- Archived final tests, complete raw records, choices, configurations, class/input
  audits, source/output hashes, reports, and development checkpoints under
  `docs/validation/phase5/`.
- Verified local Git author/committer configuration remains **Xiaoyu Su**,
  `209944670+xiaoyu-su@users.noreply.github.com`.

| Change | Reason | Benefit and evidence |
| --- | --- | --- |
| Logit menu with explicit outside option | Independent Bernoulli offers do not express driver choice among items | Analytical odds/probability totals, boundaries, deterministic menu sampling pass |
| Greedy request/driver conflict resolution | Overlapping driver selections must not double-serve a request | Explicit overlap, priority/tie, permutation, protection, and ownership checks pass |
| Exact singleton delegation | A one-item menu must retain the validated existing behavior | All-controller retries and saved Phase 3/4 paired tables match exactly |
| Pre-execution cached menu outcomes | Categorical choices must not be redrawn as Bernoulli acceptances | Actual multi-item batches execute only winners and finish all bookings |
| Commitment and episode ownership guards | Choice must not abandon existing riders or accept an uncommitted request twice | Unit protection and complete-run accepted/completed invariants pass |
| Probability intervals, reasons, and audit counters | Rejected menu items and outside choices need distinct interpretation | Full per-item records and deterministic process replay retained |
| Correct configuration semantics | A wait window is not delayed choice, and bare off decodes to false | Original batch timing preserved; real YAML/CSV round trips pass |
| Complete measured evidence | Modeling functionality does not establish a service improvement | All final outcomes retained, including lower batch completions and increased mean wait |

GitHub API authentication failed during publication preflight (HTTP 401).
Alternate stored CLI credentials are unavailable. The tested work is completed
and will be committed locally before the actual push attempt is recorded.

### Step 8: commit complete; GitHub publication blocked by authentication

- Implementation/evidence commit: `c2f37d4965e25fe9cee043171429e1280ffd3951`,
  branch `phase-5-driver-choice`. Verified both author and committer are
  **Xiaoyu Su**, using the saved `xiaoyu-su` GitHub noreply identity.
- Attempted the authorized push using GitHub CLI's credential helper, with
  terminal prompting disabled. GitHub rejected it: `Invalid username or token`
  and `Authentication failed`; command exited **128**.
- The environment token also receives GitHub API **401 Bad credentials**, and
  no alternative stored CLI credentials are configured. No new Phase 5 remote
  branch or pull request was created. GitHub authentication must be refreshed
  before publication can continue; no user token was requested or exposed.
- All code, source/input/output checks, raw experiments, complete evidence,
  and the **181 passing tests** are committed locally. This final blocked-
  publication record is a documentation-only follow-up; tested source content
  and archived artifact hashes remain unchanged.
