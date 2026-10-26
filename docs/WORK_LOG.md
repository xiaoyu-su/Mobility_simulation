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

### Step 9: authentication diagnosis and successful publication

- Earlier HTTPS Git and public API probes received **401** through the
  platform proxy, including requests with no explicit Authorization header.
  The platform injects scoped GitHub authentication; a `GH_TOKEN` binding can
  be a proxy placeholder. Calling that variable an invalid raw token was an
  unsupported diagnosis. Neither expiry nor revocation was established.
- After the latest configuration was published, fresh probes returned **200**
  for the selected repository's Git read and push discovery endpoints, and for
  upstream public Git reads. The workspace has no configured Git credential
  helper or URL rewrite. Native Git now works with platform authentication;
  no personal token or successful local CLI login was needed.
- The GitHub API has a separate current failure: HTTPS CONNECT to
  `api.github.com` returns **403 Forbidden**. The latest saved restricted
  network policy has no custom API domain rule; the earlier configuration
  included that rule. API/CLI failure therefore does not establish that Git
  push is still broken. No network policy or repository selection was changed
  during this diagnosis.
- `GIT_TERMINAL_PROMPT=0 git push -u origin phase-5-driver-choice` succeeded.
  Independent `git ls-remote` verification confirmed remote tip
  `83646a05fdf5dbf59b80c04c802d9a07d4c2dff3`, including implementation
  `c2f37d4965e25fe9cee043171429e1280ffd3951` and the original failure record.
  Both commits retain **Xiaoyu Su** as author and committer. No Phase 5 PR was
  created because API access remains blocked.
- Before suggesting any runtime refresh, created a complete Git metadata
  backup outside the checkout, including shallow-history boundaries, and
  restored it into an independent temporary directory. Verified the exact
  Phase 5 HEAD and a clean restored working tree. This protects unpublished
  history independently of environment snapshot behavior.
- This follow-up records the successful publication and corrects the earlier
  authentication explanation. Python source and archived experiment artifacts
  are unchanged; the existing **181 passing tests** remain the code validation.
  The precise backend reason for the earlier credential rejection cannot be
  established from the workspace.

## Cross-phase end-to-end audit and ongoing validation gate (2026-10-23)

- User requirement: check every simulation change end to end and retain the
  complete record. Audited every completed Phase 0–5 rather than relying on
  unit-test totals or source screenshots. All phases have successful complete
  simulation evidence: three independent baseline references, six final Phase 1
  runs, and twelve final runs in each of Phases 2–5, plus their integration suites.
- Verified all **587** files covered by the Phase 1–5 archive hash maps and all
  **nine** approved upstream input/configuration hashes. Confirmed Phase 1's
  six raw simulation outputs remain present at their recorded experiment path.
- Reran `.venv/bin/python -m pytest -q` with JUnit output and a unique retained
  temporary root. Result: **181 passed, 0 failed, 0 skipped in 616.97s**.
  The 48 regression/integration cases executed **96 complete simulations**;
  133 additional cases exercise individual invariants and boundary conditions.
  Thirteen paired experiments validated **26 matched input pairs**.
- Separately audited all 96 outputs: each contains all 100 unique demand
  records and final state, all picked-up riders finish, accepted-request sets
  equal completed-request sets where acceptance is active, terminally declined
  riders are not served, and chronological activity/driver accounting validates.
  Feature settings and choice/future counters are retained per run. The full
  suite includes actual menus with noise and future value enabled together.
- The post-suite output audit initially required every evaluation table to be
  nonempty. The three intentional always-decline cases correctly have no
  served operator and therefore no operator metric rows in the upstream
  evaluator. Corrected this audit assumption, while retaining full zero-service
  demand/decision/accounting checks. Simulation source and tests were unchanged;
  the correction is recorded in `audit-checkpoint.txt`.
- Added root `AGENTS.md` so future work must run a complete affected scenario
  after each simulation behavior/configuration change, check enabled features
  and combinations through real outputs, preserve evidence and stable source,
  and pass the full suite before completing a phase. Retained the required
  **Xiaoyu Su** author/committer identity in those instructions.
- Archived the audit, exact command, console/JUnit results, historical check,
  all per-run checks/hashes, and compressed raw records under
  `docs/validation/end_to_end_audit/`. Read back and hash-verified all **1,311**
  archived regular files. Python source matches the existing Phase 5 digest;
  no implementation, scenario, dependency, or approved baseline changed.
- Limits remain explicit: bundled small single-worker scenarios, illustrative
  driver coefficients, no demonstrated service gain, and unit coverage for
  generic overlapping-driver conflicts because live solver menus are disjoint.
  No later phase is being marked implemented by this audit.

## Phase 5b — ranked insertion fallback (2026-10-23)

### Step 1: scope, implementation, and first complete run

- Re-read the uploaded dispatch plan. This phase walks insertion candidates
  cheapest-first and stops at the first willing driver. Alonso-Mora graph-edge
  prohibition/rematching remains Phase 5c. Created `phase-5b-ranked-insertion`
  from the fully published Phase 5/audit branch; preserved the clean source and
  required Xiaoyu Su Git identity.
- Added opt-in `op_driver_acceptance_ranked_fallback` for both immediate
  insertion controllers. Freeze the existing feasible, heuristic-filtered
  candidate list, retain the cheapest plan per driver, and preserve original
  stable cost ties. Declined plans are never assigned; the normal booking path
  executes only the first accepted plan.
- Require a single decision per distinct driver (`max_declines=0`). Reuse
  existing per-request/driver streams and optional singleton choice ownership;
  do not let the legacy global retry budget suppress later drivers. Only an
  exhausted candidate list makes the last refusal a terminal request decline.
- Added candidate-order, probability, decision, and exhaustion records plus
  final counters. Reservation requests, delayed traveler models, and pure batch
  rematching are outside this phase and are explicitly rejected when enabled.
  The disabled path retains the original stable minimum and decision logic.
- First checkpoint: existing unit suite **133 passed in 4.72s**. First complete
  insertion run with sigma 0.3 processed all 100 requests, completed **73**,
  and recorded **26 fallback acceptances** out of 159 driver offers. Accepted
  requests exactly matched completed rides; no terminally declined request
  served. This smoke used the baseline's legacy initialization; the later
  paired comparisons use independent named streams and a different starting
  fleet. This is a functionality check, not a controlled service-gain claim.
- Evidence: `/workspace/.setup/phase5b/initial-unit.txt`, `smoke-insertion.txt`,
  and `smoke-insertion/`. Added focused ordering, draw/cache, boundary, and
  complete-controller integration checks before final paired experiments.

### Step 2: focused complete-controller and replay verification

- Focused ordering/draw checks plus complete simulations: **25 passed in
  102.43s**. Both insertion controllers complete always-accept, always-decline,
  logistic/noisy, and future-value/noisy runs. Probability-one output tables
  match the same first-driver controls exactly; explicit false matches omission
  for all three baseline controllers.
- Added independent-process paired replay for both insertion controllers and
  the future-value combination, plus live driver-class runs with choice off and
  logit singleton adaptation. Corrected the enabled choice-audit description
  to identify ranked singleton episodes; disabled audit content is unchanged.
- Replay/classes/scope checkpoint: **10 passed, 22 deselected in 94.69s**.
  Deselection was deliberate for this focused command; all cases remain in the
  final full-suite gate. No simulation or test failure occurred at these
  checkpoints. Reserved Phase 5c remains rejected explicitly.
- Added an otherwise identical single-attempt immediate/batch control scenario
  for fair comparison. Freeze Python source before the final full suite and
  three seed-0/1/2 comparisons: insertion, immediate/batch, and insertion with
  future value. Preserve commands, actual results, source/input/output hashes,
  and complete raw records before publication.

### Step 3: controlled comparisons on stable source

- All three final seed-0/1/2 experiments completed: **18 simulations** and
  **nine matched input pairs**, sigma 0.3. Independently compared the saved
  baseline/candidate settings: only the scenario name and ranked-fallback flag
  differ. Both arms have the same single-attempt allowance, classes,
  objective/choice configuration, demand, network, and starting fleet per seed.
- Mean completed trips: insertion **44.67 → 70.33**, immediate/batch
  **49.67 → 71.67**, future-value insertion **42.67 → 69.67**. Candidate seed
  completions are **69/69/73**, **70/70/75**, and **68/70/71**, respectively.
- Mean wait among served riders changes **118.61s → 149.66s**,
  **113.46s → 107.07s**, and **107.85s → 153.28s**, respectively. These
  conditional means involve different served riders; extra completions do not
  imply every rider waits less. Driver-offer means increase from **99.00 →
  157.67**, **98.33 → 176.00**, and **98.00 → 158.00**.
- Every accepted request in all 18 runs completed; no terminally declined
  request served. These are measured gains in the small illustrative examples,
  not a calibrated marketplace or city-scale result. Preserve the unfavorable
  waiting-time changes alongside the service gains. Complete logs/configs/raw
  outputs remain under `/workspace/.setup/phase5b/final-comparisons/` while the
  full regression/integration suite continues on the same frozen Python source.
- Independently matched **six historical control runs** against saved Phase 5
  insertion and Phase 4 future-value artifacts: **24 rider/evaluation/decision/
  choice-or-score tables** are exactly unchanged. This checks compatibility
  with already recorded history, in addition to new explicit-false comparisons.
  All 18 final runs also pass chronological vehicle/driver accounting.

### Step 4: final complete suite, output audit, and publication preparation

- Final complete command: `.venv/bin/python -m pytest -q`, with retained JUnit
  and unique temporary output paths as recorded in `command.txt`.
  Result: **213 passed, 0 failed, 0 skipped in 818.86s**. The 64 regression/
  integration cases execute **126** complete simulations, alongside 149 unit
  cases. Together with the 18 controlled comparisons, **144 final-source
  simulation runs** completed successfully.
- Independently audited all 144 outputs for 100 unique demand records, final
  state, completed pickups/bookings, absence of terminally declined riders in
  served output, valid evaluation, and chronological driver accounting. Active
  fallback runs additionally verify unique request/driver offers, consecutive
  ranks, ordered candidate costs, one winner, stop-on-acceptance, exhaustion-
  only terminal refusal, counter totals, and agreement of both decision logs.
  Zero-service boundary evaluations are handled explicitly as in the prior
  cross-phase audit.
- Source digest stayed exactly
  `7dc26b80c54bc239a727b4da04762dc66c4d48caaf901746c7ced12b47d641a1`
  across the full suite and every final experiment. All approved upstream
  input/config hashes remain unchanged. The original Phase 0 CSVs were not
  modified. `git diff --check` passes.
- A provenance probe was initially invoked with system Python, which lacks
  `tqdm`; reran it successfully with the repository `.venv/bin/python`.
  Simulations and pytest used the correct virtual environment throughout;
  no dependency or simulation-code change was needed for that tooling error.
- Archived exact commands, console/JUnit evidence, source/input/output hashes,
  per-run audits, all comparison reports, checkpoint logs, and compressed raw
  records under `docs/validation/phase5b/`. Read back and hash-verified all
  **2,165** regular archived files, including the separately labeled earlier
  smoke. Full-source runs exclude that checkpoint from their count.
- Updated phase documentation and the project/change summaries with actual
  benefits and waiting-time tradeoffs. The feature remains opt-in and the
  next optimizer forbidding/rematching work remains Phase 5c. Prepare the
  implementation/evidence commit with Xiaoyu Su as both author and committer,
  then verify the pushed branch tip independently.
- Staged whitespace preflight flagged an extra final blank line in the original
  smoke console output. Preserve the raw log bytes and their recorded hash;
  apply the staged whitespace gate to source/docs/data while excluding the
  generated phase console `.txt` files. This is an evidence-formatting issue,
  not a simulation or test failure.

### Step 5: committed and published

- Implementation/evidence commit:
  `06e2fb8edcc684c6fdc04b22699ecbe745b5bd12`. Both author and committer are
  **Xiaoyu Su**, `209944670+xiaoyu-su@users.noreply.github.com`.
- Native `git push -u origin phase-5b-ranked-insertion` succeeded. An independent
  `git ls-remote` confirmed that exact commit on the fork's branch. The branch
  tracks its origin counterpart; the working tree was clean after publication.
- Rechecked the committed Python digest and every principal archived artifact
  hash against the actual tested evidence. This publication-status follow-up
  changes documentation only; the verified simulation source is unchanged.
- Published branch:
  https://github.com/xiaoyu-su/Mobility_simulation/tree/phase-5b-ranked-insertion

## Phase 5c — Alonso-Mora forbid/rematch (2026-10-24)

### Step 1: native graph constraints and first complete simulation

- Continue the uploaded plan on `phase-5c-forbid-rematch`, based on the fully
  published Phase 5b branch. The change is opt-in and scoped to the pure
  single-worker Alonso-Mora/Gurobi batch controller with BasicRequest.
- Add `op_driver_acceptance_forbid_rematch`. Remove declined request/driver
  edges from both RV directions and every cached trip containing that edge.
  Retain exclusions across graph rebuilds until request deletion. Re-solve the
  existing native ILP at the same simulation time, without injecting plans,
  rebuilding vehicle state, replaying finished legs, or extending rider patience.
- Temporarily require every new accepted request to remain with its accepting
  driver during subsequent solves. Existing commitments retain their normal
  protection. With actual logit menus, exclude additional new items from a
  driver after its first acceptance in that round, preserving the one-new-item
  limit across all passes.
- Reuse one cached request/driver decision, with `max_declines=0`. Buffer genuine
  attempt rows until the solve sequence settles; only the last actual refusal
  for a still-unassigned request becomes terminal. Do not add fabricated offers
  or mark refusals terminal before another driver can accept.
- First existing-unit checkpoint: **148 passed, 1 failed** because an older
  controller test double lacked the new optional field. Use a guarded feature
  lookup. The first smoke also exposed an overly strict solver check: honor
  the existing implicit Gurobi default. Corrected existing-unit checkpoint:
  **149 passed in 5.38s**.
- Corrected complete noisy/class-based batch smoke: all **100** requests
  recorded, **78** completed, **25** accepted after an earlier refusal, **62**
  native solver re-solves, and **149** unique offered request/driver pairs.
  Accepted riders all finished; terminally declined riders were not served;
  driver accounting validates. This uses legacy initialization and demonstrates
  functionality, not a matched service-gain estimate.
- Evidence: `/workspace/.setup/phase5c/initial-unit.txt`, `corrected-unit.txt`,
  `smoke-batch.txt`, `smoke-batch-v2.txt`, and `smoke-batch-v2/`.

### Step 2: focused native-solver and complete-run checks

- Added actual small Gurobi graph tests for both-direction edge/trip pruning,
  idempotence and persistence, committed-request protection, accepted-pair
  constraints, and the logit round capacity. Coordinator tests cover recovery,
  genuine-attempt terminal labeling, cached draws, finite progress, fail-closed
  accepted-request loss, and output suppression.
- Added complete batch simulations for probability boundaries, singleton
  choice, actual menus, noise/future value, and explicit-disabled compatibility
  for all three baseline controllers.
- First new focused checkpoint: **22 passed, 1 failed in 80.22s**. The zero-
  probability test retained reward weighting, so the optimizer correctly made
  no offers; the test incorrectly treated the header-only decision table as a
  populated boolean frame. Preserve that valid no-offer boundary separately,
  use boolean-safe empty-table indexing, and disable weighting in the distinct
  always-refuse scenario so it exercises actual driver decisions/rematching.
  No dispatch implementation change was needed for this test correction.
- Complete corrected checks and fresh-process replay precede final source
  freezing, the full suite, and matched seed comparisons. All earlier failed
  checkpoints are preserved rather than overwritten.

### Step 3: corrected focused checks and source freeze

- Corrected native-graph/controller checkpoint: **24 passed in 80.57s**.
  Always-refuse and correctly-empty weighted-zero-service cases both complete.
  Probability-one outputs match the first-driver control exactly; actual menu
  and future-value runs complete and preserve all bookings; explicit false
  matches omission on all three baseline controllers.
- Fresh-process paired replay: **3 passed in 99.77s**, covering standard,
  actual-menu, and future-value scenarios at seeds 5 and 11. Rider/evaluation/
  decision/rematch tables and counters repeat exactly; conditional menu and
  future-score records also match. Input pairs are audited by the CLI.
- Freeze Python source before the complete suite and three final seed-0/1/2
  control comparisons at sigma 0.3. Controls differ only by scenario name and
  the rematch flag; single-attempt allowance, classes, objectives, and optional
  menu/future settings remain matched. Preserve all outputs and unfavorable
  tradeoffs before committing/pushing as Xiaoyu Su.

### Step 4: matched measured outcomes and historical controls

- All three final comparisons completed **18 simulations** and **nine matched
  input pairs**, seeds 0/1/2, sigma 0.3. Saved configuration comparison confirms
  that only the scenario name and rematch flag differ within each pair.
- Mean completed trips: standard batch **54.67 → 77.33**, actual logit menus
  **53.00 → 78.67**, future-value batch **52.67 → 76.67**. Candidate seed
  completions: **75/75/82**, **80/78/78**, and **75/74/81**, respectively.
- Mean served-rider waits increase **125.02s → 151.18s**, **136.30s →
  157.00s**, and **107.79s → 149.83s**. Mean genuine offer counts increase
  **99.00 → 143.67**, **98.00 → 141.67**, and **98.67 → 146.33**. Retain
  these unfavorable waiting/offer-count changes alongside increased service.
  Conditional means compare different served populations; this is a small
  illustrative comparison, not calibration or a general marketplace claim.
- Every accepted booking in all 18 runs completed; terminally declined riders
  were not served, per-pair decisions are unique, driver accounting validates,
  and actual-menu drivers accept at most one new request per matching round.
- Independently matched **six** control runs against saved Phase 5 standard/
  menu artifacts: **24** rider/evaluation/decision/activity-or-choice tables
  are exactly unchanged. The full suite continues on the same frozen source;
  detailed records remain at `/workspace/.setup/phase5c/final-comparisons/`.

### Step 5: complete gate, output audit, and prior-phase compatibility

- Final complete suite: **240 passed, 0 failed, 0 skipped in 1039.69s**.
  Its 76 regression/integration cases execute **151** complete simulations;
  164 unit cases include actual native Gurobi constraints. With 18 controlled
  comparisons, **169 final-source simulation runs** complete successfully.
- Independently audited all 169 outputs: all 100 demand records are unique,
  every picked-up/accepted rider finishes, terminally declined riders are not
  served, evaluation is valid for the service boundary, and chronological
  driver/vehicle accounting validates.
- Active rematch audits additionally verify one decision per request/driver,
  consecutive genuine attempts, one terminal flag only for an offered request
  still unassigned, agreement of decision/event logs, recovered/forbidden/
  accepted/terminal counts, solver re-solve pass counts, and actual logit's
  one-new-acceptance-per-driver limit over all passes in a round.
- Independently matched **22** current ranked-dispatch runs against the archived
  Phase 5b suite: **115** rider/evaluation/acceptance/ranked/choice-or-future
  tables agree exactly. Together with the six prior controls/24 tables, this
  checks existing behavior against history, not just same-version replay.
- Final source digest is
  `ecd18b9476dcd7bbd56ba17def85723e502bfa26d05b74c00e31f9d7499e3b23`.
  The full suite and every final comparison retain that exact fingerprint.
  All nine original input/configuration hashes and approved baseline CSVs are
  unchanged. No Python implementation changed during final validation.
- Archived final tests, original source/config/input/output fingerprints,
  per-run audits, raw reports/decisions/plans/stats/logs, historical comparisons,
  and preserved failure/correction checkpoints under `docs/validation/phase5c/`.
  Read back and hash-verified all **2,544** regular archived files. The separate
  first corrected smoke and failed initialization are excluded from final-run
  counts.
- Updated project and phase/change documentation with actual service gains and
  increased conditional waits. Keep raw console bytes unchanged; exclude
  generated checkpoint `.txt` logs from the source whitespace gate, as in
  Phase 5b. Prepare the implementation/evidence commit as Xiaoyu Su and verify
  its published branch tip independently.

### Step 6: committed and published Phase 5c

- Implementation/evidence commit:
  `a7bab5eb8abb82ce6664b3b7278a4836856d3a17`. Both Git author and committer
  are **Xiaoyu Su**, `209944670+xiaoyu-su@users.noreply.github.com`.
- Native `git push -u origin phase-5c-forbid-rematch` succeeded; independent
  `git ls-remote` confirmed that exact commit on the fork. The local branch
  tracks origin and was clean after publication.
- Rechecked the committed Python fingerprint and all principal artifact hashes
  against the actual tested evidence. This publication-status follow-up changes
  documentation only; simulation code remains the verified source.
- Published branch:
  https://github.com/xiaoyu-su/Mobility_simulation/tree/phase-5c-forbid-rematch

## Phase 6: windowed parallel evaluation (2026-10-24)

### Step 1: confirm the plan and preserve prior work

- Started `phase-6-windowed-evaluation` at published Phase 5c record
  `168aba897217279d7ad48f076351a24a374babc6`. Repository was clean; Git identity
  remains Xiaoyu Su. Read the actual Phase 6 handwritten plan in IMG_3326:
  full baseline/boundary snapshots, in-place policy swaps, independent parallel
  windows, and request-cohort/censor-horizon accounting. Its 36/36 and 4× notes
  are examples, not claimed measurements. Later-city/AV work remains separate.
- Added only opt-in `tools/windowed_eval/` and focused tests. Ordinary simulation
  controllers, data, saved repository selection, prior features and approved
  baseline references are untouched. Useful scope is same-controller policy
  intervention: fleet/controller/search changes are rejected before execution.

### Step 2: implement live snapshots and fix graph serialization

- Capture the complete simulator, every loaded request reference, booking and
  rejection times, named/legacy RNG state, live vehicle/noise state and optimizer
  caches. Save flushed output prefixes and exact source/dependency/hash records.
  New workers restore state, isolate all paths, replace policy models/objectives
  without replaying execution or dropping commitments, and retain baseline
  history separately from changed-policy decision logs.
- A first live 600-second insertion snapshot failed with RecursionError:
  generic pickle traversed the cyclic road graph. A second flattening attempt
  still recursed because Edge.edge_index contains Node objects, not node IDs.
  Preserve ordered adjacency, node search markers and shared edge identities
  explicitly, including reconstruction of edge_index from restored nodes.
  The third live ranked+future/noise probe serialized the 7,617-node world,
  restored routing aliases and successfully advanced the next simulation tick.
  No global recursion-limit increase is used. Probe folders are retained under
  `/workspace/.setup/phase6/probe-*`.
- Initial real experiments: `smoke-ranked` (driver-choice → ranked insertion,
  sigma 0) and `smoke-rematch` (batch control → native rematch, sigma .3),
  seed 0, 3,600-second windows +300-second cooldown, two workers. Each executes
  one full baseline and four restored windows, reaches two concurrent workers,
  validates actual policy flags and exact baseline cohort/full-run references.
  These precede final source and are excluded from final-source run counts.

### Step 3: cohorts, worker failures and independent replay checks

- Assign each request once by request time and report events strictly before
  the fixed cutoff. Preserve explicit accepted/picked-up/unresolved censoring;
  do not label unfinished observation as terminal rejection. Attribute completed
  cohort gross fare to the actual driver, including zero-service roster rows;
  avoid speculative proration of operating costs. Compare seeds within each
  window rather than treating dependent windows as extra seeds.
- A bounded pool launches fresh single-simulation subprocesses, with per-task
  timeout, logs, commands, status and cancellation. Source/payload/prefix/version
  guards and post-job immutable-baseline checks prevent mixed-source or shared
  output results. Refuse overwrites and unsupported replacements before work.
- First focused unit gate: 20 passed in 1.63s. Corrected a pandas empty-credit
  fill warning by explicitly converting numeric credit columns. Added full
  integration coverage for two insertion controllers, batch rematch with actual
  menus, future-value swaps on cached optimizer state, ordinary-baseline exact
  equality and serial/parallel exact replay. Capture all checkpoint results.

### Step 4: freeze source and run final gates

- Focused command: `.venv/bin/python -m pytest tests/unit/test_windowed_state.py
  tests/unit/test_windowed_pool.py tests/integration/test_windowed_eval.py -q
  --junitxml=/workspace/.setup/phase6/checkpoint-junit.xml
  --basetemp=/workspace/.setup/phase6/checkpoint-tests`; **24 passed in 212.20s**.
  The four real integration cases each complete two full baselines, eight
  restored windows and one independent ordinary full run. Ordinary rider,
  evaluation, acceptance, vehicle-activity and final-state tables match exactly;
  serial/parallel cohort, credit, physical-state and activity tables match.
- Extended output rebinding to the simulator's stored user/network/PT path
  attributes; record actual runtime settings and verify exhaustive cohort
  coverage. Added five pre-unpickle integrity failures: Python, source,
  dependency, payload and prefix mismatches. **5 passed in .64s**.
- Froze all Python and dependency source files; save `final-suite/source.json`.
  Complete command: `.venv/bin/python -m pytest -q
  --junitxml=/workspace/.setup/phase6/final-suite/junit.xml
  --basetemp=/workspace/.setup/phase6/final-suite/simulation-runs`, console at
  `final-suite/pytest.txt`. Do not commit or edit Python while runs are active.
- Launch six final window experiments with seeds 0/1/2, sigma .3, 2,400-second
  windows, 300-second cooldown, one versus two workers: ranked insertion,
  native rematch, and rematch with actual menus. Each compares policies differing
  only by scenario name and the respective dispatch flag. Exact commands/env
  and fresh-process logs are retained in `final-benchmarks/`; runner invocation:
  `.venv/bin/python /workspace/.setup/phase6/run-benchmarks.py`.
- These timings run while the full regression suite is also active. Report
  actual task and total wall times, baseline/snapshot overhead and output
  equivalence; they are descriptive of this environment, not guaranteed speedups.

### Step 5: diagnose and correct a multi-seed logging failure

- The initial three-seed rematch benchmark completed all 18 worker processes
  but **failed** the immutable-baseline check: seed 0/1 `00_simulation.log`
  gained an initialization warning. PIDs in those lines identify the parent
  baseline process, not a restored worker. Batch simulation logs a warning
  before its base initializer installs the next seed's handler; the preceding
  seed's handler was still active. Single-seed integration checks could not
  reveal this cross-seed output contamination.
- Stopped the concurrently running full suite before editing source, preserving
  its incomplete console/output/source record as `checkpoint-interrupted-suite/`.
  Preserve the two completed initial ranked experiments and the failed rematch
  experiment as `checkpoint-logging-benchmarks/`. They are excluded from final
  source counts. Original absolute paths in their metadata predate relocation.
- In the new window tool's `build`, close/rebind prior handlers to the current
  baseline console before constructing the next simulation. The normal engine
  then installs its own file handler as usual. Keep the strict immutable-output
  gate; the correction addresses the cause rather than weakening the check.
- A dedicated unit test reproduces a pre-initializer warning and verifies that
  it reaches the current console without appending to the previous baseline.
  Together with snapshot guard cases: **6 passed in .69s**, retained as
  `corrected-logging.txt`. Restarted the entire suite and all six benchmark
  experiments on a newly frozen source. No prior run is reused as final evidence.

### Step 6: corrected experiments and compatibility boundary

- All six measured experiments complete: **18 full baselines, 108 restored
  windows, 54 reference-checked snapshot pairs**. Confirmed that within each
  comparison only scenario name and ranked/rematch flag differ. Serial and
  parallel summary/statistics reports agree exactly for all three cases.
- One → two worker window times: ranked **60.74s → 30.42s (2.00×)**,
  rematch **71.23s → 36.79s (1.94×)**, menus **69.50s → 39.04s (1.78×)**.
  Total times including baseline/capture: **79.50s → 49.50s**, **97.35s →
  60.65s**, **93.91s → 65.89s**. Actual total ratios **1.43–1.61×**.
  Earlier pre-correction timings are separate checkpoint evidence.
- Completion by the fixed horizon improves in every local intervention window;
  conditional observed-pickup waiting means increase in all nine case/windows.
  Menu window 1 also increases mean censored requests from .67 to 1.33. Preserve
  these tradeoffs and do not sum baseline-history interventions into a full-day
  candidate claim. Full per-window/seed results remain in saved reports.
- Added an independent real boundary run using a derived external constant
  config with **NetworkBasic**, acceptance absent, baseline=candidate, sigma 0,
  cooldown 0, seed 7 and two workers. It completes **one full baseline + four
  windows** with exact reference checks. The original nine inputs are untouched.
  Command is in its manifest; output `final-benchmarks/router-compatibility/`
  and console `router-compatibility.txt`. Final counts distinguish this
  compatibility run from the six measured policy comparisons.
- While the full suite continues, independently compared the first **64**
  completed historical case outputs against Phase 5c: all **339** checked
  rider/evaluation/physical/decision tables match exactly. Extend this to every
  corresponding complete run once the suite finishes.

### Step 7: complete suite, all-output audit and immutable evidence

- Complete gate: **270 passed, 0 failed, 0 skipped in 1243.77s**. Its **80**
  regression/integration cases execute **163 full simulations +32 restored
  windows**; **190** unit cases cover graph/closure/RNG preservation, invalid
  inputs, boundary censoring, real subprocess failure/timeout/cancellation,
  corruption guards and the multi-seed logging correction.
- With 18 measured full baselines/108 windows and one additional router full
  baseline/four windows: **182 complete full simulations +144 bounded restored
  windows**. All 72 window pairs match full-baseline reference cohorts and use
  identical per-pair snapshot identities. Audit output chronology, completed
  cohort fares, actual policy flags, cutoff statuses and complete unique cohort
  coverage. All accepted full-run bookings finish; censored windows remain
  explicitly bounded observations rather than falsely completed simulations.
- Independent historical comparison: **151 full runs, 849 output tables exact**.
  All **208** pre-existing Python/dependency files and all **nine** original
  input/configuration hashes remain unchanged; the approved upstream example
  baseline regressions pass. New functionality is isolated to the opt-in tool.
- Frozen source fingerprint:
  `c417e89db72c1dc66ccd110047494f332635f04074601d965918d4e92dbb9249`.
  The complete suite, all benchmarks, router check and window workers retain
  that exact fingerprint and the development parent HEAD. No Python changed
  while final validation ran. Later documentation/publication does not alter
  tested source bytes.
- The first standalone output-audit script mistakenly required the independent
  `random_streams.json` file, selecting only 107 full runs and excluding 75 valid
  legacy-mode controls. Preserved its count assertion; corrected only the
  external recorder to audit all final-state/evaluation outputs and validate
  stream records where applicable. Corrected audit passes all 182 runs and
  144 windows. No simulation/tool code or scenario changed and no final run
  was repeated for this recorder-only correction.
- Preserve source/commands/JUnit/consoles, raw full simulations, snapshots,
  prefixes, states, decision/cohort/credit reports, fixed-seed experiments,
  historical comparisons, failed/interrupted checkpoints, and original
  file hashes in `docs/validation/phase6/`. Read back every archived regular
  file and match its hash to the source bytes before publication.
- Archive verification completed for **10,820 regular files**: final suite
  **3,833**, final benchmarks/recorders **4,057**, and preserved checkpoints
  **2,930**. All read-back hashes match original bytes. Preserve raw console
  `.txt` endings and exclude those generated logs from the source whitespace
  check, as in preceding phases. Stage the tested implementation and complete
  evidence, commit with Xiaoyu Su as both author/committer, then verify the
  fork's branch tip after native Git push.

### Step 8: commit and verify GitHub publication

- Implementation/evidence commit:
  `6e9a67364f5837ccbcac83c05aae1c7cb31c238c`. Git author **and** committer
  verified as **Xiaoyu Su**, `209944670+xiaoyu-su@users.noreply.github.com`.
  Explicit author/committer environment variables were used for this commit.
- Native `git push -u origin phase-6-windowed-evaluation` succeeded.
  Independent `git ls-remote origin refs/heads/phase-6-windowed-evaluation`
  returned the exact implementation commit. The local branch tracks origin
  and was clean after publication.
- GitHub accepted all three evidence archives. It emitted its non-blocking
  recommendation about the 55.42 MiB benchmark archive exceeding 50 MiB;
  the push completed successfully and no evidence was omitted.
- Recomputed the committed Python fingerprint and checked every recorded
  principal artifact hash: they still match the final suite and experiments.
  This follow-up records publication in documentation only; tested Python and
  raw evidence remain unchanged. Publish this record under the same identity
  and verify the final branch tip and clean working tree.
- Published branch:
  https://github.com/xiaoyu-su/Mobility_simulation/tree/phase-6-windowed-evaluation

## Phase 7: market-data and calibration pipeline (2026-10-24, client date)

### Step 1: confirm the next section and verify data availability

- Started `phase-7-market-data-pipeline` from published Phase 6 record
  `c65f4509171fcdc44ae41c4c240c4a0cc7c48d29`; working tree was clean.
  Re-read IMG_3327/3328: the next section is the real-data Manhattan case study,
  before mixed AV fleets and cross-city comparisons. Its numerical outcomes
  describe the supplied reference plan, not measurements reproduced here.
- The repository contains Manhattan scenario templates but no Manhattan network,
  taxi-zone mapping or high-volume trip records. Actual requests to TLC's
  November 2019 Parquet and taxi-zone lookup endpoints, the official NYC page,
  Socrata and Zenodo fail at the cloud proxy with CONNECT 403. Public GitHub
  documentation is reachable; no matching local trip/network copy was found.
  Saved a fresh diagnostic in `/workspace/.setup/phase7/data-access.json` and
  asked asynchronously for an existing workspace path or accessible input link.
- Continue all implementable work: a reproducible local-input pipeline and real
  complete simulation checks with explicitly marked fixtures on the bundled
  road network. Real Manhattan calibration, the plan's reported real-city
  outcomes and large-scale/three-hour public-data experiments remain unrun
  until those sources are available. Never label fixtures as observed NYC data.

### Step 2: implement data preparation and a license-free repositioning strategy

- Add `tools/synthetic_market/`: chunked CSV/Parquet input with explicit source
  hashes/row identities, deterministic nested sampling, date/zone/time filters,
  disjoint rejection counts, held-out target day and strictly earlier matching
  weekdays for forecast/travel fitting. Required high-volume schema includes
  `hvfhs_license_num`; arbitrary FHV data is not silently relabeled HVFHV.
- Require an explicit request-time proxy when the source has no
  `request_datetime`. Proxy waits remain unavailable in observed-wait reports.
  Exclude/count intrazonal trips that a single centroid cannot represent.
  The supplied zone map, original network and every generated input are hashed.
- Fit travel factors/log-noise from training ride-duration/road-ETA ratios with
  mean-one execution-noise arithmetic; record the coarsening/non-driving
  limitations. Build historical departure/arrival forecasts, training workload
  fleet/profile estimates under an explicit utilization assumption, initial
  positions, optional depot/TimeBasedFS inputs and illustrative driver classes.
  Demand writes actual `latest_start_time` attributes read by BasicRequest:
  observed wait lower bound plus explicit additional patience, or additional
  patience alone when request time is assumed. Patience is not claimed observed.
- Add opt-in **PavoneFCHiGHS**, registered separately from existing strategies.
  It uses SciPy MILP, floors fractional available excess before deriving integer
  uniform targets, checks vehicle conservation, selects vehicles from a private
  named RNG and uses native assignment APIs. Existing Pavone/Gurobi behavior
  and default scenarios are unchanged. Per-round forecast/flow/vehicle/objective
  audits demonstrate actual use and retain unfavorable repositioning outcomes.
- Install/pin PyArrow 19.0.1 for Parquet (`environment.yml`). Initial `uv pip`
  failed on a read-only `/home/agent/.cache/uv`; corrected with task-local
  `UV_CACHE_DIR=/workspace/.setup/phase7/uv-cache`. Preserve both install logs;
  no home-directory or permission change was needed.

### Step 3: timely checks and early corrections

- First unit gate: **20 passed in 1.15s**. Covers real CSV/Parquet parsing,
  chunk-invariant nested sampling, absent timestamps/proxies, exclusive filter
  counts, duplicate source rejection, target/future-date leakage, fractional
  interval forecasts, known travel-factor fits, duplicate-report merge guards,
  exact integer transport, invalid/empty supply, and **2,070** real HiGHS MILP
  variables (above the restricted commercial solver limit).
- First combined gate: **22 passed, 2 failed in 83.29s**. Insertion and native
  batch cases complete paired full simulations/replays with real repositioning.
  One fixture's 120-second proxy correctly moved its first request before the
  request-time cohort start: target count became 99. Correct the fixture to an
  explicit 60-second proxy; do not admit an out-of-window request to satisfy a
  hard-coded count. Add separate window-exclusion counts to the manifest.
- Dynamic fleet initialization failed because the generated config used
  `infra_depot_file`, whereas FleetPy loads operator depots from `op_depot_file`.
  Correct the generated operator setting and retain the failed child traceback.
  Parse mixed valid/invalid timestamp strings explicitly to remove pandas'
  inference warning. No original simulation behavior was altered for these
  corrections. Rerun all four affected end-to-end combinations on the corrected
  source before the full regression gate.

### Step 4: boundary accounting, loaded contracts and all-router replay

- Corrected depot initialization exposed a separate accounting boundary:
  TimeBasedFS's initial parked legs begin one tick before simulation start.
  The original strict accounting rejects those pre-horizon records. Preserve
  the raw activity and add explicit `clip_initial_inactivity=False` to driver
  accounting; only the market runner with TimeBasedFS enables it. It truncates
  stationary, empty, zero-distance/toll inactivity to the accounting start.
  Moving, loaded, toll-bearing, displaced and overlapping records still fail.
- Added hand-checked online/idle exposure, unchanged-raw-byte and invalid-record
  tests. Corrected dynamic-fleet scenarios and exact replay now pass. The
  intermediate gate is **12 passed in 161.09s**, with one test-data dtype
  warning corrected by writing a numeric position value.
- Every market worker now verifies that all loaded BasicRequest IDs and actual
  `latest_start_time` values match generated inputs, then checks all
  broker-confirmed bookings finish after the ordinary complete simulation.
  `market_input_contract.json` records the verified counts. Real vehicle logs
  must show execution-noise multipliers and actual repositioning where expected.
- Expanded the four end-to-end cases to cover NetworkBasicWithStore,
  NetworkBasic and NetworkTTMatrix. The matrix test uses an explicitly labeled
  three-node fixture derived from example-road OD travel costs; it is not a
  Manhattan network. Preserve every full run, source input, bundle and replay.
- Focused gate: **32 passed in 286.33s**. Command:
  `.venv/bin/python -m pytest tests/unit/test_market_inputs.py
  tests/unit/test_highs_repositioning.py tests/unit/test_market_accounting.py
  tests/integration/test_market_pipeline.py -q
  --junitxml=/workspace/.setup/phase7/final-focused-junit.xml
  --basetemp=/workspace/.setup/phase7/final-focused-tests`.
- Add source-file mutation detection, exact dependency versions, private bundle
  path/hash validation and preexisting-output preservation. Eight additional
  guard cases pass in .69s (`tests/unit/test_market_guards.py`). Parent/worker
  code and data fingerprints remain fixed throughout an experiment.

### Step 5: complete input isolation and final frozen-source gates

- The first final comparison recorder, located outside the repository, lacked
  the repository on Python's import path and stopped before any simulation.
  Preserve `initial-final-case-recorder.txt`; correct only that recorder with
  an explicit root path. Its scripts are provenance, not part of the tested
  application source.
- Initial final-source comparisons completed all four configurations, but input
  review found vehicle specifications still referenced the shared repository
  file. Preserve those 24 completed runs as
  `checkpoint-shared-vehicle-cases/`, excluded from final counts. Stop the
  concurrently running suite before changing Python and preserve its partial
  outputs/source/console as `checkpoint-interrupted-suite/`.
- Copy the original vehicle specification bytes into the private bundle, verify
  source/copy hashes and use that directory for both simulator and financial
  accounting. The bundle now protects network, demand, forecasts, supply,
  depots, vehicle physics/costs and policy parameters together. An end-to-end
  assertion checks the actual loaded vehicle directory. No vehicle numbers or
  source specification contents change.
- Freeze source again and restart the complete command:
  `.venv/bin/python -m pytest -q
  --junitxml=/workspace/.setup/phase7/final-suite/junit.xml
  --basetemp=/workspace/.setup/phase7/final-suite/simulation-runs`, with source
  record and console retained there. Do not edit Python or commit until all
  simulations and comparisons finish.
- Restart four additional fixture cases at seeds 0/1/2 over **07:00–10:00**:
  insertion; immediate/batch with proxy times, classes and future value;
  native batch with classes and a matrix router; and a changing active fleet.
  Each case compares only repositioning off versus HiGHS. All exact commands,
  environments, original inputs and bundles are retained in `final-cases/`.
  Invocation: `.venv/bin/python /workspace/.setup/phase7/run-final-cases.py`.
  These are functional fixture comparisons, not actual NYC calibration.

### Step 6: complete final gate and independent output checks

- Complete suite: **310 passed, 0 failed, 0 skipped in 1506.82s**. Its **84**
  regression/integration cases execute **195 complete simulations +32 bounded
  restored windows**; **226** unit cases include native HiGHS, actual input
  corruption/mutation, accounting boundaries and existing native solver tests.
- With **24** additional three-seed fixture comparisons: **219 full simulation
  runs +32 restored windows**, including **56** full market-pipeline runs. Every
  full run retains all 100 unique requests. Accepted bookings finish, terminally
  declined riders are not served, and chronological vehicle/driver accounting
  validates with the explicit initial-inactivity option only where configured.
- All eight final market bundles verify original/source/copied hashes, exact
  dependency/source versions, 300 independent historical training trips and
  100 held-out trips. Every paired experiment matches demand, network and
  initial fleet fingerprints. Loaded patience/booked-completion contracts and
  actual noise/repositioning/optional-model traces demonstrate feature use.
- Independent historical comparison: **163 full runs, 921 exact output tables**
  plus **128** exact cohort/credit/physical/activity window tables. The vehicle
  isolation correction additionally preserves exact physical/evaluation/
  decision tables in all **24** prior fixture comparison runs. No original
  dataset/configuration or approved baseline was changed: all nine input hashes
  still match. Apart from the registry, optional accounting boundary and
  environment dependency declaration, all 217 pre-existing source files match.
- Final frozen source digest:
  `d0dd474cef8aae0ccbd1f5c94008788b02648efb523a167c3bbe11c1722f84da`.
  Full suite, comparisons and workers retain this fingerprint. Original
  source/commands/JUnit, independent per-run hashes, source cohorts, bundles,
  original logs and outcomes are saved in `docs/validation/phase7/`.
- Actual three-hour fixture means (control → repositioning): insertion
  completion **100 → 100**, wait **2.17s → .76s**, extra empty driving
  **7.21 km**, modeled fleet net **10462.44 → 10282.08 cents**;
  immediate/future/proxy completion **54.33 → 55.33**, wait **33.78s →
  6.23s**, extra empty **18.68 km**; native batch/classes completion **63.33 →
  64**, wait **39.48s → 17s**, extra empty **14.75 km**; changing-fleet
  completion **99 → 99**, wait **47.49s → 34.29s**, extra empty **1.13 km**,
  modeled fleet net **10279.03 → 10190.22 cents**. Preserve the unfavorable
  driving/net changes. These are illustrative fixtures, not observed NYC
  earnings or calibrated real-city policy gains.
- Revisited the user's public-data question: yes, the datasets are public.
  Verified TUM's reachable GitHub release contains software archives, while the
  datasets are separate Zenodo/TLC downloads blocked at the proxy. Investigated
  an accessible GitHub HVFHV analysis repository; it supplies documentation,
  not the required raw files. Explain the concrete network-domain requirement,
  rather than suggesting credentials or treating public data as private.
- **Unrun:** real November 2019 Manhattan 10%/full-scale calibration, real-data
  patience/supply sensitivity, and TUM city-level parity comparisons. Public
  host access or supplied local trip/network/zone files is still required.
  Keep this limitation explicit in the project summary, phase docs and final
  validation status; do not reuse the plan's historical numbers as evidence.
- Byte verification completes for **8,394 regular archived files**: **5,017**
  final-suite/comparison/recorder files and **3,377** checkpoint files. Every
  archived byte sequence hashes identically to its original. A separate
  chosen-operator check also confirms no booked-but-unfinished request in any
  of the 219 full outputs. Preserve raw `.txt` console bytes and exclude those
  generated logs from the whitespace gate, as in prior phases.
- The staged whitespace check also identified trailing spaces inside the raw
  failed-checkpoint JUnit traceback text. Preserve those original XML bytes and
  hashes; exclude `checkpoint-junit.xml` and `corrected-junit.xml` along with
  raw console `.txt` files from the source/document whitespace gate. All
  implementation, ordinary documentation and other evidence pass that gate.

### Step 7: verified GitHub publication

- Implementation/evidence commit:
  `f98f2469a56d0ee83d14d694259c54bc736a07dc`. Explicit author/committer
  environment variables and Git inspection verify **Xiaoyu Su**,
  `209944670+xiaoyu-su@users.noreply.github.com`, for both identities.
- Native `git push -u origin phase-7-market-data-pipeline` succeeded.
  Independent `git ls-remote origin refs/heads/phase-7-market-data-pipeline`
  returned that exact implementation commit. The branch tracks origin and
  was clean after publication. All final code and principal artifact hashes
  still match tested bytes after committing.
- This follow-up records publication only. It does not change Python, raw
  evidence or the explicit real-data-blocked status. Publish the documentation
  under the same Xiaoyu Su identity, then verify final remote tip/clean tree.
- Published branch:
  https://github.com/xiaoyu-su/Mobility_simulation/tree/phase-7-market-data-pipeline

## Phase 7 follow-up: real data access and controlled investigation

### Data readiness and baseline

- Published network egress configuration resolved the public TLC/Zenodo download
  block. Downloaded the 21,635,568-row November 2019 source, official lookup and
  TUM Manhattan archive; checked SHA256, published archive MD5 and extracted
  files. Data manifests are retained. Joined TUM internal zone IDs to 63 official
  TLC zones and resolved projected polygon coordinates against network CRS.
- Built `/workspace/market_inputs/manhattan_10pct_seed0` with the unchanged market
  CLI: TLC public data, corrected TUM matrix network, adapted zone map,
  `--sample-fraction .1 --seed 0`. Training November 5/12/19, held-out November
  26, 07:00–10:00, 3,150 target requests, 775 modeled vehicles. Ran both policies
  end to end. Initial-grid median waits were 47.28/0 seconds versus 265 seconds
  observed. This exposed a calibration gap; successful execution does not close
  Phase 7.

### Controlled diagnosis (in progress)

- Kept all 232 source/dependency files and Git HEAD frozen. Digest remains
  `d0dd474cef8aae0ccbd1f5c94008788b02648efb523a167c3bbe11c1722f84da`.
  Created separate, hashed input bundles and preserved their ancestry. The
  baseline and all earlier evidence are unchanged.
- Found source-clock early pickups (1,411/2,031), centroid instant-service
  artifacts, missing training carry-in, all-request pooling and arrival-versus-
  boarding event mismatch. See `REAL_MANHATTAN_INVESTIGATION.md` for definitions,
  exact populations and limitations. These are measured defects/assumptions,
  not explanations inferred only from aggregate performance.
- Run commands use `python -m tools.synthetic_market run --bundle <variant>
  --seeds 0 --timeout 3600 --output <fresh-output>` with fixed Python/BLAS seeds.
  Outside-repository preparation, runner and analysis scripts retain exact
  commands and provenance without changing frozen simulation source.
- Completed spatial ablations improve the apparent wait discrepancy but still
  admit requests early. Exact-second inputs are under test. The centroid
  exact-second/repositioning run failed booked completion for request 2665;
  preserved raw logs, manifest and outputs, and launched an observer-only replay
  to inspect the stuck vehicle. Do not count that run as successful.
- Planned evidence includes every tested case, failed outcomes, matched-cohort
  wait distributions, arrival coverage, ride/pooling regressions, source and
  input/output hashes, and all booking/activity integrity checks. No production
  source fix or completed real-data calibration is claimed at this checkpoint.

### Failure diagnosis and additional controlled checks

- Observer-only replay reproduces five key output files byte for byte for the
  failed centroid/exact-second repositioning case. Vehicle 356 is still moving
  with request 2665 at the four-hour tail cutoff; execution multiplier is
  3.493786. Isolated continuation of that recorded state using the existing
  movement code reaches its original destination 512.63s after the cutoff.
  Preserve the failure and observer trace separately; continuation is forensic
  evidence, not a successful policy run. The first isolated calculation needed
  network-factor initialization corrected before its final 512.63s result;
  retain both console logs and use the corrected result.
- Two-hour dynamic initialization exposed a matrix-router type error. Blank
  depot charging-unit values promote numeric `iterrows` values to float. A
  separate bundle explicitly encodes zero sockets (`0:0`) while preserving depot
  IDs, locations, parking and empty physical socket lists. Verified the row node
  IDs are integers before rerunning both policies; source remains unchanged.
- Added training-only curb sensitivity: 30 to 94 seconds, median of 6,906 valid
  earlier-Tuesday peak arrival records. Both minute-ceiling and exact-second
  alternatives are tested. The minute-grid case improves total-wait error with
  repositioning to 8.28s but reduces completions to 3,128 and worsens arrival
  error versus the same 30-second-board candidate. Do not present this as an
  unconditional improvement or calibrate against the held-out target.
- Checked the stop-duration implementation: the existing constant boarding
  parameter also controls drop-off dwell. The 94s cases are therefore generic
  dwell sensitivities, not a separately fitted pickup-curb model. The exact-
  second 94s repositioning arm fails booked completion for request 1510/vehicle
  727 and logs the finite-tail cutoff. Preserve its successful individual
  no-repositioning arm, but exclude the failed pair from policy conclusions.

### Final real-data outcomes and evidence

- Finished all 14 configurations (original plus 13 input/config variants).
  **27 canonical attempts: 24 full booked-completion successes, three failures,
  11 complete input-validated pairs.** The original failed dynamic setup's
  repositioning arm was not launched. A separate observer replay reproduces
  one failed run; it is not an additional successful simulation. Failed cases
  remain `clock_1s/repo`, `uniform_clock_1s_train_curb/repo`, and the original
  dynamic setup's first arm. The typed-depot replacement completes both arms.
- Independently checked all 24 completed outputs for unique/full demand,
  completed accepted bookings, no service for unserved users, chronological
  activity, route capacity and actual boarding-event timing. Successful
  repositioning arms contain real orders/physical repositioning legs, with
  distinct assigned vehicles within each round. Eight completed floor-clock
  outputs still violate source-clock causality; preserve these failed validity
  checks. The other 16 completed outputs have zero early pickups.
- In the repositioning arm, original centroid/floor → uniform road nodes with
  exact-second clock changes early pickups **2,031 → 0**, matched arrival-median
  absolute error **128.00 → 11.41s**, and arrival-distribution Wasserstein
  distance **109.83 → 18.64s**. Completions regress **3,147 → 3,138** and
  post-boarding ride-median error regresses **100.79 → 130.04s**. This is a
  benchmark correction/sensitivity, not proof of the imputed real geography.
- Within the valid exact-second road-node pair, repositioning completes
  **3,059 → 3,138** (+79, +2.51 percentage points). Among the same 3,054
  common-served trips, marginal wait medians are **149.46 → 124.74s**, but
  median individual wait change is **0**; 1,457 improve, 1,164 worsen and
  433 are unchanged (mean change −40.04s). Repositioning adds **2,663.29km**
  of reposition driving and modeled fleet net falls **58,142.83 cents**.
  Costs/fares are illustrative and include recorded fulfillment tails.
- Warm-up alters results rather than uniformly improving fit. No-repositioning
  median source-clock wait: cold **149.85s**, one-hour **177.74s**, two-hour
  **203.76s**; repositioning: **127.06 / 134.51 / 135.00s**. The two-hour
  dynamic-supply case gives **215.44 / 169.15s**. Supply remains an assumption,
  not observed online exposure. All values use exactly the original 3,150
  evaluation source IDs; warm-up demand is additional simulation context.
- Exact final diagnostics commands, run from the repository:

  ```bash
  .venv/bin/python /workspace/.setup/phase7-investigation/analyze.py
  PYTHONPATH=/workspace/Mobility_simulation .venv/bin/python /workspace/.setup/phase7-investigation/context_diagnostics.py
  .venv/bin/python /workspace/.setup/phase7-investigation/policy_effects.py
  .venv/bin/python /workspace/.setup/phase7-investigation/make_table.py
  MPLCONFIGDIR=/workspace/.setup/phase7-investigation/mpl .venv/bin/python /workspace/.setup/phase7-investigation/plot_results.py
  PYTHONPATH=/workspace/Mobility_simulation .venv/bin/python /workspace/.setup/phase7-investigation/archive_evidence.py
  ```

- Preserved raw public-data download/extraction provenance, source-row context
  caches, every private input derivation/config, full raw runs including
  failures, exact commands/logs, observer traces, diagnostics, policy trade-offs
  and frozen source in `docs/validation/phase7-real/`. The readable report is
  `docs/REAL_MANHATTAN_INVESTIGATION.md`; README/project/improvement summaries now
  reflect available data and incomplete calibration. TUM data attribution and
  CC BY 4.0 metadata accompany the derived network/zone inputs.
- Production Python and Git HEAD remained unchanged throughout simulation.
  All 232 source/dependency hashes still match the earlier 310-test gate.
  The full suite was **not rerun** for this data/documentation-only investigation.
  No new phase completion is claimed. Production floor admission/reporting,
  integer depot handling, completion-aware tails and model identifiability
  still need correction/validation; additional seeds/dates, full demand and
  TUM city-level parity remain unrun.
- Archive verification reads back and checks **976 regular files** byte for
  byte. Final `evidence.tar.xz`: **51,639,272 bytes**, SHA256
  `309861418b9818b3c913d361dcc8cac5d74dfa5ad4d8b51d7eaf96c94f5244dd`.
  The intermediate verified gzip package is preserved outside Git under
  `/workspace/.setup/phase7-evidence-checkpoint.tar.gz`; the XZ package saves
  space without changing archived raw records. Standalone JSON parsing,
  report/source fingerprints, archive SHA and source/document whitespace
  checks pass with the generated SVG exception below. New local documentation/evidence links resolve; the upstream
  README's existing `(link)` placeholder is unchanged.
- Publish the investigation/evidence on `phase-7-manhattan-validation` with
  explicit **Xiaoyu Su** author and committer identity. This publication records
  the investigation and outstanding fixes; it does not declare Phase 7 complete.
- The first staged whole-artifact whitespace check flags Matplotlib's generated
  SVG path-data trailing spaces. Preserve its original bytes (matching the
  verified scientific archive) and exclude that specific generated SVG from
  the source/document whitespace gate, as with original raw console artifacts
  in prior phases. `git diff HEAD^ HEAD --check -- .
  ':!docs/validation/phase7-real/calibration_diagnostics.svg'` then passes with
  empty output. The scientific source, simulations and figure are unchanged.

### Verified investigation publication

- Evidence/report commit:
  `cfba80aa86bf6557eb785cdbd35287ac0d7ba5ad`. Git confirms both author and
  committer are **Xiaoyu Su**, `209944670+xiaoyu-su@users.noreply.github.com`.
- `git push -u origin phase-7-manhattan-validation` succeeded. Independent
  `git ls-remote origin refs/heads/phase-7-manhattan-validation` returned that
  exact commit; the working tree was clean. Production source still has digest
  `d0dd474cef8aae0ccbd1f5c94008788b02648efb523a167c3bbe11c1722f84da`,
  and the scientific archive retains its verified SHA256.
- Branch:
  https://github.com/xiaoyu-su/Mobility_simulation/tree/phase-7-manhattan-validation
- This follow-up records publication only. It changes no source, input,
  simulation output or calibration status. Publish under the same explicit
  Xiaoyu Su identity and verify the final remote tip and clean working tree.

## Phase 7 production corrections requested after investigation

- The user explicitly requested finishing the missing work. Created
  `phase-7-production-fixes` from published `a3b67f6`, preserving the complete
  earlier investigation and raw public sources.
- Implemented causal admission with horizon-safe cohort retention, full-history
  supply context, warm-up with separate evaluation IDs, deterministic optional
  polygon-constrained road positions and intrazonal support, source pooling
  consent, separate pickup/drop-off service, training-only patience, geometry-
  consistent unshared travel fitting and within-bin residual noise.
- Added opt-in shared request constraints at plan feasibility and batch vehicle
  structures. Legacy controllers without the option keep their existing path.
  Infrastructure loaders now validate/cast integral road-node IDs. An opt-in
  strict completion tail preserves the driving grid and update order, skips
  idle tail work and writes an audit; exhaustion raises rather than claiming a
  completed booking. Legacy tail handling remains available when unspecified.
- Replaced ambiguous market reporting with matched event/cohort diagnostics;
  raw-clock early pickup, physical booking completion, chronological activity
  and private-request pooling violations are hard failures. Whole-horizon costs
  and evaluation-window utilization have explicit domains.
- Initial command: `.venv/bin/python -m pytest -q
  tests/unit/test_market_corrections.py tests/unit/test_market_inputs.py
  tests/unit/test_market_guards.py
  --junitxml=/workspace/.setup/phase7-fixes/initial-unit.xml`:
  **34 passed in 1.14s**. New tests exercise real CSV float promotion, causal
  last-boundary admission, stable intrazonal imputation, source event coverage,
  noise detrending, private-request overlap/handoff, pickup/drop-off dwell, and
  long-trip completion versus explicit tail exhaustion.
- Froze checkpoint source
  `53a469d879446d12704f7cf48e4b76f33599ed6641a597305f9e0d4d70ddec1b`
  (236 files), then launched complete market integration checks including all
  three controllers. Logs/JUnit/raw outputs are under
  `/workspace/.setup/phase7-fixes/checkpoint-*`. No source edits are made while
  these complete simulations run. Final results will follow this checkpoint.
- Checkpoint integration results: **38 passed, three failed in 402.96s**.
  All three enhanced controller checks detected pickup dwell still executing as
  30s instead of fitted 20s. The first implementation set an unused `duration`
  attribute; FleetPy uses `direct_duration` through its public setter. Corrected
  the implementation to use `set_duration_and_earliest_end_time`, and corrected
  the unit check to assert the public duration and actual planned timing.
  Preserved the failed checkpoint source/logs/outputs. Rerunning all enhanced
  controller cases plus the focused unit/guard checks on the corrected source.
- Attempted the original TUM 24-hour `ex1_IH` scenario with the provided 2018
  demand, hourly road factors and original Alonso-Mora repositioning. It reaches
  the repositioning solver and fails at 25,200s with **Gurobi model too large
  for the size-limited license**. Preserve this concrete external limit; do not
  present a changed solver/policy as an exact reproduction of published results.
- Corrected focused gate: **37 passed in 18.96s**, including actual physical
  pickup/drop-off durations for all three matching controllers and dynamic
  matrix-router depots with blank charging fields. Snapshot of all 236
  corrected source/dependency files is preserved under `final-source/`.
  Frozen final source:
  `e4736dcf5bc0829f654b12ea6025c1a7065e45920c6190cf19dfdd7c002570a2`.
- The first full-suite invocation used a nested pytest `--basetemp` whose
  parent directory did not yet exist. Pytest reported **131 passed, 196 setup
  errors in 8.51s**, all due to that missing temporary parent. Preserved the
  invocation/log/JUnit and created the parent before restarting the entire
  suite in `full-final/`. No source change was involved.
- Started corrected production CLI builds directly from verified public
  Parquet: November 26 and November 19 (earlier training dates only), seeds
  0/1/2; full demand, one-hour warm-up and changing-fleet checks follow in the
  same runner. Every source cohort, configuration, command and output is
  fingerprinted. `run_real_cases.py` records stage exit codes and elapsed time;
  complete runs use new output directories under `production_fixes/`.
- Final regression gate: **327 passed in 1946.09s**, zero failures, errors or
  skips. `audit_suite.py` independently checks **201 complete simulation
  outputs** and **32 restored windows**. The source remained frozen at
  `e4736dcf5bc0829f654b12ea6025c1a7065e45920c6190cf19dfdd7c002570a2`.
- Rebuilt the exact two former failed-case inputs with explicit legacy
  all-pooling/service assumptions and the new strict completion bound, rather
  than refitting geometry/travel/supply. Both now finish every original
  accepted request, including 2665 and 1510. `verify_repaired_cases.py` confirms
  original assignments and completed-trip times/fares are unchanged, and
  **10,585 / 13,709** pre-horizon activity rows are numerically identical.
  Trajectory integer-versus-float text formatting can differ; parsed node/time
  events are exactly identical. Final tails contain zero tasks/onboard riders.
- Full-day TUM control validation: reference source exported from `fd2a76e`
  and corrected code both complete the actual 21,400-request, 24-hour IH
  dataset with repositioning explicitly disabled. Five files are byte-identical:
  users, vehicle activity, final state, standard evaluation and vehicle types.
  The first comparison harness expected a random-stream audit absent in legacy
  mode; preserved that harness error and corrected the comparison to actual
  available output files. This is not an exact original-repositioning-policy
  reproduction. The original Gurobi repositioning case is separately attempted
  on the reference, checkpoint and final corrected sources and remains blocked
  by the restricted commercial license.
- Independent consent audit of the previous published real benchmark finds
  **738 private riders pooled** in the prior road/exact-second repositioning
  arm (916 in the earlier centroid/floor arm). Completed corrected real-data
  arms have **zero private-pooling violations**. Source shared-request flags
  define consent; source shared-match flags are reported separately as outcomes.
- Finished **all 22 new real policy simulations /11 complete pairs**. There
  are no pending new real policy arms: November 26 10% (seeds 0/1/2), November
  19 10% with intrazonal demand (0/1/2), full November 26 demand (0/1), one-hour
  warm-up (0) and changing fleets (0/1). Each case executes full no-reposition
  and HiGHS-repositioning runs. Main `run_real_cases.py` and separate
  `run_full_seed1.py` stage records have zero build/run return codes. Frozen
  code/dependencies and Git base stayed unchanged through all physical runs.
- Exact reproducible build/run argument arrays, stage runtime and source/input
  fingerprints are in `.setup/phase7-fixes/real/*/execution.json` in the real
  archive. All builds stream the original public Parquet, use the 4,411-node
  matrix network/63 mapped zones, explicit EPSG:32618 polygon constraints,
  source sampling/imputation seed 0, source pooling consent, training-only
  pickup service and native immediate-search bound 30 origin positions. That
  bound can include multiple vehicles and is not exhaustive global matching.
  All real runs use insertion matching; other controllers and driver-choice
  combinations have complete fixture validation rather than real-data
  coefficient calibration.
- The principal held-out November 26 cohort is 07:00–10:00, trained only on
  earlier Tuesdays November 5/12/19. Two-hour warm-up begins at 05:00. The
  second held-out day, November 19, trains only on November 5/12 and includes
  134 intrazonal evaluation bookings. The one-hour warm-up keeps the same
  3,150 November 26 evaluation IDs. The source file's raw-row identities are
  retained throughout; road points are deterministic imputations, not GPS.
- Full-demand seeds receive **32,192 evaluation +7,315 warm-up requests** and
  modeled fleet 7,932. All 19 hashed bundle files are identical across the two
  seed-specific bundles; simulation seeds alone differ. Causal grid is 60s,
  fitted pickup service 94s, separate drop-off 30s, training patience 717+300s.
  Sampled static cases use a 1s grid; changing-fleet checks use 60s. These
  resolution/density differences are disclosed, not presented as one-factor
  calibration comparisons.
- Full-demand seed 0: no repositioning **26,172/32,192 completed**, repositioning
  **31,842/32,192** (+5,670). Matched arrival-median error **92.907→23.956s**;
  matched pickup-median error **22.237→40.140s**. Seed 1: **26,278→31,865**
  (+5,587); arrival error **96.324→24.433s**, pickup error **22.292→39.184s**.
  The pickup median error worsens even though pickup Wasserstein distance falls
  from **101–104s to 35–36s** and arrival distance from **195–197s to 52–53s**.
  Repositioning is not claimed to improve every measure. Every accepted booking
  finishes; unserved source requests remain in full accounting and are not
  counted as completed.
- Among riders served in both full-demand arms, mean individual arrival wait
  changes by **−128.439s /−124.131s** (seeds 0/1). Still **9,820 /9,782 riders
  wait longer**. Whole-run reposition distance is **43,505.7 /42,281.0 km**,
  and illustrative model net change is **+$4,195.22 /+$4,253.76**. These include
  warm-up and the fulfillment tail, not just three evaluation hours, and are
  not observed NYC wages. Two November 19 sampled seeds instead have lower
  modeled net earnings; every pair's cost and common-rider effects are retained.
- Sampled three-seed repositioning pickup-median errors average **3.957s** on
  November 26 and **9.539s** on November 19; arrival errors remain **55.737s /
  64.709s**. Full-demand modeled pooling is about **12.9%**, compared with
  **21.7%** source shared matches on the same served population. A near-matched
  sampled pickup median does not establish full-city arrival/ride/pooling fit.
- Final independent commands: `.venv/bin/python
  /workspace/.setup/phase7-fixes/analyze_results.py`, then
  `provider_diagnostics.py`, then `final_report.py` from the same directory.
  All exit successfully. Independent checks report **22 runs, no pending
  cases**, unique/full accounting, all accepted bookings physically complete,
  chronological legs, capacity, physical pickup/drop-off minima, actual
  reposition orders and zero early/private-pooling violations. Event metrics
  use raw request clocks and matched observed IDs. Exact-row provider joins
  cover 35,845 distinct evaluation source identities; 66 provider/arm diagnostics
  disclose selective arrival reporting and heterogeneous pickup fit. They are
  diagnostics only, never inputs to held-out tuning.
- Reproduction of the final full test gate uses `.venv/bin/python -m pytest
  -q`, with `--basetemp=/workspace/.setup/phase7-fixes/full-final/runs` and
  `--junitxml=/workspace/.setup/phase7-fixes/full-final/junit.xml`; final stdout
  is `full-final.txt`. The earlier missing-parent setup failure and the three
  genuine service-duration failures remain preserved with their fixes.
- Packaging commands: `.venv/bin/python
  /workspace/.setup/phase7-fixes/package_suite.py` and `package_real.py`.
  Regression archive contains **6,429 original files**, 39,566,931 bytes,
  SHA256 `687d5d5f75cb146af20ea7c73c63d4a9d500ff9471dc06bfeb66fc3e75ba474b`.
  Every member is read back and verified against its original SHA256. Real
  archive retains complete inputs/cohorts/outputs/audits/commands/failures and
  comparison source, splitting upload parts below GitHub's file-size limit as
  needed. Repeated public 155MB matrices and original large public downloads
  stay outside Git with exact restoration URLs/paths/hashes; private input
  manifests remain unchanged. Original scientific logs/SVG/XML bytes are
  preserved; source/document whitespace checks exclude raw generated artifacts.
- Complete readable tables, per-seed CSVs, checks and inspected standalone PNG/
  PDF figures are indexed in `docs/validation/phase7-completion/README.md`.
  `docs/PHASE_7_COMPLETION.md` separates finished engineering work from residual
  numerical calibration, public-data identification limits and the original
  TUM solver-license constraint. README/project/improvement summaries now link
  to this evidence; the earlier investigation and its archive remain unchanged.
- Real archive packaging completed: **862 original files**, **281,523,022
  bytes**, logical SHA256
  `fa34cd1d41040439c0818b1e311881cd0d40bc7e8acd642091381309d6d93da7`.
  Nine ordered upload parts are at most 32 MiB each. Every member and every
  concatenated part byte was verified. `validation.json` records all final
  gates and explicitly sets `fully_identified_real_market=false`.
- Final publication gate verifies all 236 working source/dependency files equal
  the tested snapshot, all nine real archive part hashes and concatenation,
  the regression archive hash, six completed real manifests/11 validated pairs,
  and all new report/summary links. The first broad README link scan also
  matched an unchanged upstream `[CONTRIBUTING.md](link)` placeholder; scoped
  the scan to the new project summary and reports. No simulation source change
  was required. The previous `phase7-real` scientific evidence is unchanged.
- Published implementation commit **`6a7f22f26623decb7381aa9f685df589c2a22325`**
  to GitHub branch **`phase-7-production-fixes`** using native HTTPS Git.
  Both author and committer are **Xiaoyu Su**. `git ls-remote` exactly matched
  local HEAD, and the working tree was clean before adding this publication
  record. Verified at **2026-10-25 13:43 Pacific**; machine-readable receipt is
  `docs/validation/phase7-completion/publication.json`. This final follow-up
  only records publication and links; the tested source digest is unchanged.

## Phase 8: mixed human/AV product (2026-10-25, Pacific)

### Step 1: recover the next planned section and preserve the published base

- Started clean branch `phase-8-mixed-av-fleet` from published
  `e7b32ca21f4e2d0ff6129005f14e31f5b489f84c`. Both Git identities remain Xiaoyu
  Su. Re-read the actual IMG_3328/3329 source images: next is AV-product Round
  1, before speed/threshold dispatch and cross-city work. The screenshots'
  numerical outcomes are reference claims, not results measured by this fork.
- Scope: separate loaded AV type, both-endpoint fence, deterministic nested
  rider opt-in, rider-second preference, AV acceptance/initial placement,
  exclusion from human shifts/repositioning, idle diagnostics and independent
  historical-demand AV repositioning. Fixed total fleet avoids attributing
  extra supply to a dispatch preference. Existing public data is ready.

### Step 2: implement and check real loaders and complete simulations

- Added opt-in `src/fleetctrl/av_product.py` and plan-feasibility/assignment
  checks shared by insertion and native batch matching. Batch vehicle copies
  retain the same product constraints. Immediate search filters ineligible AV
  positions before its route-position limit. Objective preference uses the
  existing rider-time value, preserving units and credits on incumbent riders.
- AVs use probability one, a separate audit class and no human class draw;
  their initial distribution is conditioned on the fence. TimeBasedFS applies
  active shares only to humans, and human repositioning ignores AV supply.
  AV repositioning uses largest-remainder forecast targets, busy final-zone
  offsets and Hungarian idle-to-target assignment, retaining active tours.
- Extended the private market builder with explicit AV assumptions and a
  separately named, actually loaded AV vehicle file. Added `tools/av_eval/`
  for immutable matched-seed preference/repositioning sweeps and actual-output
  reports. Workers reject executed fence/opt-in, shift, human-repositioning or
  selected-AV refusal violations. Existing booking/clock/pooling/tail guards
  remain active. Diagnostics and online/cohort/whole-run domains are labeled.
- First checkpoint source
  `1233628d2b285a903cc9feddc46fa1f14054485055915d65040b2b8198755434`:
  pytest stopped with one collection error because new unit/integration files
  had the same basename. No simulations ran. Renamed the integration file;
  preserved the source/JUnit/log rather than counting this as a passed check.
- Next source `8b4847c1a2fee43eab28521d74fc10f0e25d9f67fe38eb582a8b1f5c0aafc776`:
  **7 passed, 4 failed in 39.74s**. All 16 physical simulations completed;
  four test assertions mistakenly compared a set of loaded type names to a
  string. Corrected the assertion to a singleton set. Also strengthened mixed
  fixtures with source private flags and historical pickup-only service fit,
  moved commitment diagnostics after timing refresh, retained legacy audit
  bytes when no AVs exist and guarded nonbaseline initial-state hooks.
- Corrected focused gate: **12 passed in 39.56s**, including 16 complete
  physical simulations, all three controllers, human acceptance/classes,
  execution noise, future value, private consent, separate physical service,
  changing human fleets, zero-opt-in boundaries and byte-exact replay. The
  actual roster/configuration loaders confirm distinct `av_vehtype` vehicles.
- Froze all **242** source/dependency files at
  `890505b3db913cbab61c12c3c79b29659de0e296bec1c4dce9499ea7d4f4aeee`.
  Snapshots and every failed/corrected log/JUnit/raw run are under
  `/workspace/.setup/phase8/{checkpoint,focused,corrected}`. No repository
  Python/dependency edits or Git HEAD changes occur during final experiments.

### Step 3: run final regression and public Manhattan experiments

- Full regression command: `.venv/bin/python -m pytest -q
  --basetemp=/workspace/.setup/phase8/full/runs
  --junitxml=/workspace/.setup/phase8/full/junit.xml`, stdout/stderr in
  `full/tests.txt`. Results will be recorded after completion and independent
  output checks; this entry does not claim a passed gate in advance.
- Public-data runner: `.venv/bin/python -u
  /workspace/.setup/phase8/run_real.py`, preserving exact argument arrays,
  return codes and elapsed times in `real/execution.json`. It builds directly
  from the verified public Parquet/network/zones, using explicit EPSG:32618,
  10% source sampling/imputation seed 0, two-hour warm-up, a causal 60s grid,
  training-only curb/patience/travel/supply and source pooling consent.
- The planned factorial comparison is preferences **−300/0/+300s**, AV
  repositioning **off/demand**, simulation seeds **0/1/2**: 18 complete runs,
  with fixed 10% AV share, 50% assumed opt-in, a densest-training-zone 30%
  fence and identical background inputs within each seed. Human repositioning
  is HiGHS in every arm; human acceptance is off to isolate these AV levers.
  AV/human acceptance coexistence is separately checked in full fixtures.
  Measured benefits and adverse outcomes will be recorded after validation.
- All 18 real policy runs completed successfully: build **58.70s**, full
  experiment **1043.38s**. Actual bundle contains **3,150 evaluation +751
  warm-up requests**, fixed **775 vehicles =78 AVs +697 humans**, 19 fence
  zones selected only from historical pickups, and **391** synthetically
  AV-eligible evaluation riders. All three seeds share the same input sample
  and opt-in identities; only simulator randomness varies.
- Final real-data independent command `.venv/bin/python
  /workspace/.setup/phase8/analyze_real.py` completed successfully. It checks
  every loaded ID once, every accepted booking complete, source-clock causality,
  chronological legs, capacity, physical service minima, private pooling,
  actual AV endpoints/opt-in, initial fence, human shift/reposition exclusion,
  unique AV repositioning orders and runtime override/config agreement. All
  **18 runs /15 background comparisons pass**, zero rule violations. Raw
  hashes and audit results are in `analysis/independent_checks.json`.
- Three-seed control (preference 0, AV repo off): **3,133.7 completed**, **102.7
  AV /3,031.0 human trips**, AV served share **3.28%**, productive utilization
  **13.9%**, idle share **84.7%**, eligible mean arrival wait **247.2s**.
  Combined +300s/demand-repo: **3,144.0 completed**, **305.0 AV /2,839.0 human**,
  AV share **9.70%**, productive utilization **40.6%**, idle share **36.1%**,
  eligible mean wait **243.4s**, other riders **273.6s versus 291.7s**.
  Human trips/online hour fall **6.33%**; whole-run AV repositioning averages
  **827.1 km**. Improved AV allocation is mostly a transfer from humans; true
  additional completion is only **10.3 requests on average**.
- Adverse outcomes are retained: +300s preference without AV repositioning
  yields **3,126.3 completions**, eligible mean wait **266.8s**, and lower human
  trips. At preference 0, AV repositioning yields **3,142.0 completions**,
  **109.0 AV trips**, eligible mean wait **225.4s**, **742.8 km** empty AV
  repositioning and only **14.9%** productive utilization. Idle share can fall
  because vehicles are driving empty. Conditional nearest-idle-AV gap averages
  **94.8→49.2s** across per-seed medians; it measures proximity among eligible
  human-winning dispatches, not guaranteed alternative insertion feasibility.
- At preference 0/repo versus combined +300s/repo, most extra AV trips replace
  human trips (about 194 fewer human trips for only two additional completions),
  and eligible mean wait increases by **18.0s**. Complete per-seed/common-rider
  effects and model financial totals are retained, with evaluation-window
  utilization versus whole-run distance/cost domains labeled. Inspected the
  generated standalone scientific PNG and PDF figures. No held-out tuning,
  AV-specific ground-truth calibration or full-demand AV claim is made.

### Step 4: close regression, compatibility and complete evidence gates

- Final full command completed: **339 passed in 1874.71s (31:14)**, zero
  failures/errors/skips. `audit_suite.py` independently audits **217 full
  simulation outputs +32 restored windows** for unique accounting, completed
  picked-up trips, chronological activity and explicit window censoring.
  Real market workers additionally compare accepted-event IDs to completed
  trips, so every accepted real booking is physically complete.
- Compared AV-disabled outputs directly to the preserved Phase 7 full-suite
  evidence: **201 common full simulations /930 tables are byte-identical**,
  including users, vehicle activity, standard evaluation and acceptance/choice/
  future/ranked/rematch decision records where present. The same **32 windows
  match 128 exact cohort/driver/request/final-state tables**. This establishes
  actual historical compatibility, not merely same-version replay. Approved
  Phase 0 baseline CSVs and older validation archives remain unchanged.
- Exact final source remains
  `890505b3db913cbab61c12c3c79b29659de0e296bec1c4dce9499ea7d4f4aeee`
  (242 files). The complete suite, focused corrections and all 18 real policy
  runs use this source; no Python/dependency or Git HEAD edits occurred during
  final physical validation.
- Final orchestration: `.venv/bin/python
  /workspace/.setup/phase8/finish_validation.py` waits for the completed pytest
  summary, runs `audit_suite.py`, then `package.py`. Both exit zero. Packaging
  stdout is outside the archived folder to avoid collecting a live log.
- Complete archive: **7,383 original files**, **119,393,714 bytes**, SHA256
  `8ae8c913e6f7db1872e2157f4b5b22448d9de174471c6508f242dd80dadecf9d`.
  Four upload parts are at most 32 MiB each. Every archived member was read back
  and verified against its original SHA256, and concatenated part bytes were
  checked against the complete archive. All failed collection/assertion logs,
  exact source snapshots, full/focused/real outputs, cohorts/forecasts/supply,
  executed parameters/commands and independent scripts are retained.
- The two 155 MB public matrices and original large public downloads remain
  outside Git with verified restoration URLs/paths/hashes. Private manifests
  are retained unchanged. Source plan photos are not republished. Data
  attribution remains Roman Engelhardt/Florian Dandl, Zenodo 15187906, CC BY 4.0;
  source license remains MIT. Raw scientific SVG/XML/log bytes are preserved;
  whitespace checks exclude generated artifacts rather than normalizing them.
- Updated Phase 8, project summary, README and improvement history with actual
  measured gains/costs and clear future scope. Full-demand AV, cautious-speed,
  ETA-threshold, joint forecast accounting and cross-city work are not claimed
  delivered by this Round 1. Phase 7 calibration limits remain visible.
- Mixed-product human acceptance is validated off/singleton, as generated by
  the market builder; multi-item human logit menus and AV snapshot resumption
  are outside this phase's supported profile. Previous human-only menu and
  window features retain exact historical outputs. The AV experiment runner
  uses complete physical runs rather than unsupported in-place AV policy swaps.

### Step 5: publish and verify GitHub

- Final prepublication gate verifies all **242** source/dependency files match
  the tested snapshot, report/summary links resolve, all four part hashes and
  the logical archive SHA256 match, and each part is below 100 MB. Source/doc
  whitespace gate passes, excluding preserved raw generated logs/XML/SVG.
  Earlier Phase 7 evidence and approved Phase 0 baseline CSVs are unchanged.
- Committed implementation/evidence as
  **`369ed70e2d1af9e3b5d0252ac2a43e4904bf626f`**. Both author and committer are
  **Xiaoyu Su**, `209944670+xiaoyu-su@users.noreply.github.com`.
  Native `git push -u origin phase-8-mixed-av-fleet` succeeded.
- Independent `git ls-remote` exactly matches that implementation commit; the
  working tree was clean before adding the publication receipt. Verified at
  **2026-10-25 20:23 Pacific /2026-10-26 03:23 UTC**. Receipt is
  `docs/validation/phase8/publication.json`. This follow-up records publication
  and links only; tested source/inputs/results remain unchanged.
- Published branch:
  https://github.com/xiaoyu-su/Mobility_simulation/tree/phase-8-mixed-av-fleet

## Phase 9: AV speed, ETA threshold and repositioning follow-ups (2026-10-25, Pacific)

### Step 1: confirm the next round and preserve the published base

- Started clean branch `phase-9-av-threshold-and-speed` from published
  `59b8ff04519947fda4c2fdeb46c8ec8870ef03ac`. Both Git identities remain Xiaoyu
  Su. Re-read IMG_3328/3329: next is AV Round 2, before cross-city evaluation.
  Preserve every prior source/input/output reference and keep the screenshot's
  outcome numbers separate from actual measurements in this fork.
- Scope: consistent cautious-vehicle plans/execution, actual CSV-loader
  retention, AV-first ETA threshold, empty moving-reposition retargeting,
  forecast-noise sensitivity, joint expected-demand accounting and full-scale
  simulation checks. Explicit .3 opt-in is a scenario choice; it is not inferred
  from the 2019 trip records.
- Attempted primary survey/benchmark access (Pew, AAA, CPUC, Obi) and accessible
  public-repository search. All return proxy CONNECT 403; exact URLs/errors
  remain in `.setup/phase9/research/`. Actual trip/network inputs remain fully
  local and verified. `docs/AV_DATA.md` records the resulting empirical boundary;
  no inaccessible reference number is presented as independently validated.

### Step 2: implement the controls and exercise complete simulations

- Added validated `travel_time_factor` [1,10], default 1, retained by the actual
  vehicle-file loader. Record loaded/effective factors and actual leg values.
  VehiclePlan arrivals/intermediary states, batch vehicle copies, future-value
  alternative ETAs, AV proximity/reposition costs and physical driving/replay
  use the same factor. Noise remains separate; stationary duration, distance
  and energy per meter are unchanged. Factors below one are rejected because
  existing reachability pruning is a safe optimistic bound for slower vehicles.
- Future-value alternatives now exclude AVs ineligible for the request. This
  corrects an old mixed-product proxy issue; it can intentionally change old
  AV+future-value fixture outputs. Human-only/AV-disabled behavior remains the
  compatibility target. Human multi-item menus are explicitly rejected in this
  mixed-product profile instead of silently using incompatible probabilities.
- Added inclusive ETA-threshold dispatch for the two immediate insertion
  controllers. Threshold and cost preference are alternatives. Native global
  batch threshold is rejected explicitly, while speed/product constraints are
  tested under all three controllers. Every policy-grid arm has the same
  separate human/AV nearest-position budgets, including cost controls, so a
  search-budget expansion is not mislabeled a threshold benefit.
- Added unlocked empty-target retargeting without replacing rider tours,
  isolated mean-one lognormal forecast errors, rolling forecast-bin overlap
  and a joint policy using eligible historical OD demand plus conservative AV
  availability coverage subtracted from human forecast demand. AV planning
  precedes human planning only in joint mode. Raw forecast adjustments/orders
  and physical type/threshold/coverage checks are exported.
- Expanded `tools.av_eval` with immutable named JSON policy grids and explicit
  timing/threshold/opt-in/noise/retarget/joint overrides. Source/dependency/bundle
  guards, every-request accounting and physical completion remain hard checks.
  Real reports distinguish evaluation-cohort waits/trips, evaluation-clock
  utilization and whole-run empty distance/cost; no daily extrapolation.

### Step 3: failed checks, correction and actual-service commitment bug

- First frozen checkpoint
  `280077197ff10707d98b1a9e0327ac918bde3e18085f4951fdd31946cbe710f6`
  (245 files): **27 passed /3 failed in 51.99s**. The physics assertion assumed
  sub-microsecond matrix movement precision; NetworkTTMatrix explicitly rounds
  event times to centiseconds. Bound this known rounding by movement updates,
  retaining exact independent line-network checks. Another physics fixture
  reoptimized all AV proposals onto humans, so the intended AV physics never
  executed. Add an explicit +300s preference to that fixture to exercise AVs
  after reoptimization; do not count a zero-AV run as an AV physics check.
- Corrected candidate
  `f9d6be73805299aee0d37d76fb24a2153c3ce090b648a80abe838e2803df47d5`:
  **71 passed in 53.89s**. Then an independent check of actual service exposed
  a real threshold integration gap: insertion-plus-batch chose **34 AV trips**
  but completed **11 by AV**, with **23 completed product mismatches**. The
  selection-only threshold audit did not detect later reoptimization.
  `threshold-commitment-failure.json` preserves the affected rider IDs.
- Stopped the owned full-suite/three real-worker process trees before changing
  source; `interruption.json` preserves commands/PIDs/reason. The initial full
  gate and real studies were interrupted, not passed. Existing partial/completed
  outputs and original private bundles remain unchanged in their own paths;
  old study manifests explicitly say interrupted for this fix.
- Fix: commit the selected service product at acceptance in the shared plan
  feasibility check. Native optimization can move a booking within its human/
  AV class but cannot undo the accepted class. Repeated committed selection
  retains the product. Actual completed user rows are independently checked
  against threshold decisions. Strengthened end-to-end assertions compare AV
  completion with chosen AV products, not only proposal logs.
- Final focused candidate
  `66fe97b5ab63c89a440583da274cb3e1e87841f070285cb322e2b95f0a5ad939`
  (245 files): **72 passed in 54.88s**, including 17 complete physical runs.
  The corrected insertion-plus-batch fixture now has **34 AV choices /34 AV
  completions** in both physical arms and their exact replays. Forecast noise,
  moving retargets, joint adjustments, private consent, human shifts/acceptance,
  future value, loaded speed factors and all three controllers are exercised.

### Step 4: fresh final full gate and real experiments

- Keep repository Python/dependencies and Git HEAD frozen on the final digest.
  Full gate: `.venv/bin/python -m pytest -q
  --basetemp=/workspace/.setup/phase9/full-final/runs
  --junitxml=/workspace/.setup/phase9/full-final/junit.xml`, with stdout/stderr
  at `full-final/tests.txt`. Earlier interrupted `full/` remains separate.
- Fresh real runner: `.venv/bin/python -u
  /workspace/.setup/phase9/run_final_cases.py`. Final inputs are
  `/workspace/market_inputs/phase9_final_av_10pct` and `phase9_final_av_full`;
  final outputs are `/workspace/market_results/phase9_final/{main,followup,full}`.
  Exact grids, commands, return codes, runtimes and logs are in
  `.setup/phase9/{grids_final,real_final}`. Fresh builds pass in **57.0s /66.8s**.
  The earlier runner, inputs and `market_results/phase9/` remain preserved.
- Main: six seeds0–5 ×six arms =36 full physical runs, comparing cost control,
  thresholds0/120/240/480 at1.25× travel time and equal-speed threshold240.
  Follow-ups: seeds0–2 ×six arms =18 runs: exact threshold240 control repeat,
  noise.5, joint, callback300 control, callback300 retarget, combined. Three
  repeated controls are replay checks, not extra independent replicas.
  Full demand: seed0, threshold0 versus240, two full physical runs.
- Sample inputs: **3,150 evaluation +751 warm-up requests**, **775 vehicles
  =78 AVs +697 humans**. Full inputs: **32,192 evaluation +7,315 warm-up**,
  **7,932 vehicles =793 AVs +7,139 humans**. Same19 training-derived fence
  zones, .3 opt-in, zero cost preference, human acceptance off and human HiGHS
  repositioning on. Forecasts/travel/curb/patience/supply use only earlier
  training days. All56 final physical runs, source, inputs and paired audits
  will be finalized before publication; this entry does not claim their gates
  passed while they are still running.

### Step 5: independent output inspection and follow-up outcomes

- Independent checker: `.venv/bin/python
  /workspace/.setup/phase9/analyze_final.py`. It verifies final source and all
  private bundle bytes, then independently reconstructs eligibility and actual
  pickup/drop-off IDs from raw vehicle activity. Checks include accepted promise
  coverage, full unique demand, completion tail, chronology, capacity, private
  consent, physical curb minima, actual human/AV product commitment, effective
  type factors, retarget occupancy, human/AV operation separation, forecast error
  validity and bounded residual human demand. Matched random-input audits and
  three fresh-process control replays are checked independently of CLI success.
- Early `--partial` inspection passed **35 completed final physical runs**;
  it does not produce or substitute for a final all-run validation result.
  A separate interim historical comparison matched **140 full non-AV runs /
  638 byte-identical tables**; the final full-suite audit will cover every
  historical counterpart. Source remains the same 245-file digest.
- All **18 follow-up runs** finish successfully in **1173.7s**. Actual changed
  empty targets number **191/189/210** in retarget-only seeds 0/1/2 and
  **831/827/797** in combined cases. Joint expected coverage is bounded and
  positive; forecast-error factors are positive, finite and reproducible.
- Retarget-only versus the same 300-second callback control: mean completion
  is **3135.67 in both**; AV trips rise **180.67→187.67**; whole-run AV empty
  distance share falls **63.32%→56.59%**, but eligible served mean arrival wait
  rises **248.91→261.52s**. Completion changes by seed are **+8/−2/−6**, so
  this is not a robust completion improvement. Retargeting and callback-frequency
  effects are kept separate in the paired tables.
- Native GitHub read access succeeds (`git ls-remote origin`); configured identity
  is Xiaoyu Su /209944670+xiaoyu-su@users.noreply.github.com. No token is printed
  or changed. Publication remains gated on final regression, all real runs and
  complete archived evidence, including the slower full-demand pair.

### Step 6: final regression and historical compatibility gate

- Final `.venv/bin/python -m pytest -q` command from Step 4 finishes with
  **370 passed, 0 failed/errors/skipped, 2045.38s**. Source and Git parent
  remain unchanged throughout. Original JUnit/XML and stdout bytes are retained.
- Independent audit: `.venv/bin/python
  /workspace/.setup/phase9/audit_suite.py >
  /workspace/.setup/phase9/suite-audit.txt 2>&1` succeeds. It checks **234 full
  physical simulations +32 restored windows**, unique accounting, matching
  pickup/drop-off completeness, final states and nonoverlapping vehicle activity.
- Every unchanged historical non-AV counterpart matches Phase 8: **201 full
  runs /930 byte-identical output tables**, plus **32 restored windows /128
  exact tables**. The approved Phase 0 references and old published evidence
  remain unchanged. The deliberate AV-aware future-value/product corrections
  are exercised by new physical cases and are not mislabeled unchanged history.
- Evidence: `.setup/phase9/suite-integrity.json`, `legacy-identity.json`,
  `suite-audit.txt`, `full-final/{tests.txt,junit.xml,runs}`. All are included
  in the final archive; standalone review copies are under
  `docs/validation/phase9/` after packaging.

### Step 7: sampled real results and replay gate

- Main six-seed experiment finishes **36/36 physical runs, return code 0,
  2258.23s**. Together with the 18 follow-ups, all **54 sampled physical runs**
  are complete. The two full-demand physical runs are still running at this
  checkpoint and are not counted as passed here.
- `.venv/bin/python /workspace/.setup/phase9/analyze_final.py --sample >
  /workspace/.setup/phase9/sample-analysis.txt 2>&1` passes all independent
  physical checks on the 54 runs. All three fresh-process threshold-240 control
  replays match **seven raw user/vehicle/product/dispatch/human-reposition/report/
  random-audit files byte for byte**. These are 51 distinct sampled seed/config
  conditions plus three replays. `sample-analysis/` explicitly excludes the
  unfinished full-demand results; final all-run analysis will supersede it.
- Cautious threshold240 versus same-search cost control, means over six seeds:
  completed **3124.50→3133.50** of3150; actual AV trips **14.67→180.50**;
  AV served share **0.47%→5.76%**; AV occupied utilization **2.42%→29.46%**;
  whole-run AV empty-distance share **94.31%→58.22%**. Human trips/online hour
  fall **1.487→1.412**, approximately5.04%. Higher allocation/productive AV use
  is verified, but this is not an unconditional social-benefit claim.
- The **+9.0** mean completion change has conditional six-seed t interval
  **[−0.003,18.003]**, including zero. Eligible served mean wait changes by
  **−3.12s**, interval **[−19.87,13.63]**. Do not claim either is a demonstrated
  completion/wait improvement. These intervals condition on one fixed source
  cohort and do not establish population or cross-city inference.
- Cautious threshold240 versus threshold0 adds **127.17 AV trips** on average
  but only **1.33 total completions** (interval[−4.88,7.55]); eligible served
  mean wait rises **23.17s** (interval[11.66,34.68]). Larger threshold480 raises
  AV share to **6.69%**, with eligible wait **288.63s** versus226.60s at threshold0.
  Threshold120 gives lower eligible wait and higher mean completion than240 in
  this fixed cohort; no policy is selected after seeing held-out outcomes.
- Matplotlib scientific PNG/PDF is generated from all six seeds; whiskers show
  seed ranges, not confidence intervals. Visual inspection confirms legible
  titles, units, control label and domain definitions. `paired_effects.csv`
  preserves actual paired intervals; `common_rider_effects.csv` preserves
  comparisons on identical served rider IDs, including adverse effects.

### Step 8: full-demand physical control

- Full-demand threshold0 completes with **return code 0 in2962.72s** on the
  same frozen source and full private bundle. It accounts for all **39,507
  unique requests** (32,192 evaluation +7,315 warm-up). Evaluation completion is
  **31,720**, including **317 AV /31,403 human** trips. All accepted bookings
  finish; actual AV opt-in/fence/product checks report zero violations.
- The eligibility cohort contains **2,377 evaluation requests**; AV eligibility
  service rate is13.34% and AV share of completed trips1.00%. Occupied AV
  utilization is5.44%, idle share86.09%, and whole-run AV empty-distance share
  77.59%. Eligible served mean arrival wait is165.99s; human trips per online
  hour1.4663. These are the control's model outcomes, not improvement claims.
- The threshold240 full-demand counterpart starts only after this worker
  succeeds. Final all-run publication still waits for that counterpart and
  its paired/output audit. The existing driver-metrics CSV read emits a
  nonfatal pandas mixed-column DtypeWarning on the large vehicle table; raw
  logs are retained. Independent vehicle-output inspection reads with
  `low_memory=False` and checks physical activity directly.

### Step 9: old AV-default compatibility extension

- `.venv/bin/python /workspace/.setup/phase9/audit_av_defaults.py` checks the
  16 previously published Phase 8 full AV cases against their final-suite
  counterparts. With the new controls disabled, **14 runs /93 user, vehicle,
  evaluation, dispatch, product, repositioning and acceptance tables match byte
  for byte**. Two AV/future-value cases are recorded separately because the
  eligibility-aware fallback-value correction is intentional; they are not
  claimed unchanged. Every counterpart finishes under the full regression gate.
- This extends the 201-run non-AV compatibility proof to the AV-default
  repositioning/dispatch path. Evidence: `av-default-compatibility.json` and
  its exact command/output log, both retained in the complete archive.
- The independent real-data checker now passes **55 completed runs**, including
  the full-demand threshold0 control; the final threshold240 case remains
  running. The 55-run checkpoint is stored in
  `full-control-independent-check.txt`; it is not a substitute for final
  56-run validation and is not used to declare the unfinished phase complete.

- The full-demand control's actual completion tail ends at **53,580s (14:53)**,
  **17,520s after the 10:00 cohort endpoint**, with **0 remaining tasks /0
  onboard request IDs**. No incomplete trip is hidden by stopping at the
  request horizon. The report distinguishes this full physical fulfillment
  domain from evaluation-clock utilization and request-cohort trip counts.

- Focused checkpoint selections are preserved by JUnit and
  `focused_reproduction.json`. The 30-case first checkpoint selects
  `tests/unit/test_av_round2.py tests/integration/test_av_round2_examples.py`.
  The 71/72-case corrected gates additionally select
  `tests/unit/test_av_product.py tests/unit/test_highs_repositioning.py
  tests/unit/test_future_value.py`. Equivalent exact argument-vector reproduction
  commands use `.venv/bin/python -m pytest -q` with those files and fresh
  basetemp/JUnit paths under `.setup/phase9-reproduction/<checkpoint>/`.
  These are archived reproduction recipes derived from actual JUnit selections,
  not a claim of an additional rerun. Restore each matching source digest first;
  controller/config/seed details remain in its complete physical run outputs.


### Step 10: final full-demand counterpart and all-run audit

- All three final real-study commands finish with return code0: main **36 runs
  /2258.23s**, follow-ups **18 runs /1173.74s**, full-demand **2 runs
  /5731.69s**. Exact commands, runtime and logs are
  retained under `.setup/phase9/real_final`; the outer runner writes
  `execution.json` only after all studies succeed.
- The single-seed full-demand pair completes **31720→31831 of 32,192 evaluation requests**, with actual AV completions **317→2139**, AV served share **1.00%→6.72%**, and AV occupied utilization **5.44%→35.23%**. Eligible served mean arrival wait changes **165.99→180.85s**; human trips per online hour change **1.4663→1.3864**. Whole-run AV empty-distance share changes **77.59%→42.42%**, while absolute empty AV distance increases **3715.15→6010.40km**. A lower empty share is not an absolute empty-driving reduction. Both runs clear every accepted booking and all physical/product checks. This is a one-seed scale check, with no replicated full-demand interval or full-day claim.
- `.venv/bin/python /workspace/.setup/phase9/analyze_final.py >
  /workspace/.setup/phase9/analysis.txt 2>&1` passes all **56 final physical
  runs /53 unique seed-configurations**, **49 matched input comparisons** and
  **three exact fresh-process control replays across seven files each**.
  All accepted bookings physically board/alight; all unique demand is accounted
  for; tails clear; product commitment, fence/opt-in, chronology, capacity,
  service minima, effective timing factors, retarget occupancy and joint bounds
  pass. Source/dependencies remain the frozen245-file digest recorded above.
- Final outputs include per-seed/range tables, paired effects/conditional
  intervals, common-served-rider changes, all file hashes, scientific PNG/PDF
  and explicit sampling/benchmark/financial/domain limits. The earlier
  `sample-analysis/` checkpoint remains archived; final `analysis/` supersedes it.

### Step 11: complete raw evidence and upload-byte verification

- `.venv/bin/python /workspace/.setup/phase9/package_final.py >
  /workspace/.setup/phase9-package.txt 2>&1` retains final and failed/interrupted
  raw runs, complete regression/windows, original/corrected frozen sources,
  private training/demand/supply/forecast inputs, all scripts/grids/execution
  logs, public source manifests and independent analyses.
- Archive contains **11834 files**, logical compressed
  size **494712640 bytes**, in **15 upload part(s)**.
  SHA-256: `5508b17d1dd3e191a9bbeb88fdc2029a94bf06e9842f3578dfd745bf37c58027`. Every stored member's bytes and all upload parts
  pass readback verification. Repeated large public matrices are explicitly
  listed with exact size/hash/restoration path; original large public Parquet/
  ZIP inputs stay outside Git with verified source URLs and hashes.
- No raw SVG/XML/TXT whitespace is rewritten. Source/documentation whitespace
  gates exclude generated raw artifacts. No plan photographs are republished.
- `.venv/bin/python /workspace/.setup/phase9/prepublish.py` checks the final
  source/snapshot, all real output hashes, final manifests/input bundles,
  uploaded archive bytes and omitted-matrix restoration hashes, report links,
  inspected figure identity and unchanged old evidence before commit/push.
- Final profile retains assumptions: .3 opt-in, cautious travel time1.25, fixed
  replacement fleet and training proxies. External AV benchmarks remain
  unverified; calibration closure, full-day inference, cross-city validation,
  global-batch threshold dispatch and mixed human multi-item menus are not claimed.

- Final presentation clarification derives full-demand fleet empty totals as
  `av_empty_distance_km + human_empty_distance_km` from the published
  `seed_results.csv`: **55159.55→55348.77km (+0.34%)**. The AV-only
  increase is partly offset by reduced human empty kilometers. This note is
  added to the standalone derived report/phase guide after raw packaging;
  the archive's original analysis and all component values remain unchanged.
  This is presentation arithmetic, not an extra simulation or altered output.
- The post-analysis command `.venv/bin/python
  /workspace/.setup/phase9/augment_results.py >
  /workspace/.setup/phase9/absolute-distance-analysis.txt` adds the explicit
  AV absolute-distance/percentage distinction before archiving. Its script
  and output are included in the raw record. Final inspected/scientific figure
  bytes match the earlier sample figure exactly.


### Step 12: publish as Xiaoyu Su and verify GitHub

- Source/documentation whitespace and final prepublication checks pass before
  commit. Commit **`35d437d81475462156e0945122fca6154ec28f59`** contains the complete Phase 9 implementation,
  regression/real experiment evidence, source snapshots and measured tradeoffs.
- Native `git push -u origin phase-9-av-threshold-and-speed` succeeds.
  `git ls-remote origin refs/heads/phase-9-av-threshold-and-speed` returns
  that exact implementation commit. Both author and committer are **Xiaoyu Su
  /209944670+xiaoyu-su@users.noreply.github.com**, verified from the actual commit.
- Every committed source/dependency blob matches the frozen245-file digest
  `66fe97b5ab63c89a440583da274cb3e1e87841f070285cb322e2b95f0a5ad939`. All370 tests,56 physical real runs and byte-verified evidence
  belong to those exact bytes. Earlier evidence remains unchanged.
- `docs/validation/phase9/publication.json` records the verified implementation
  tip, identity, source and evidence hashes. It is added in a documentation-only
  receipt commit; remote equality and checkout cleanliness are checked again
  after that receipt push before reporting the phase complete. No token was
  printed or changed and no saved repository selection was modified.

## Phase 10: cross-city AV policy transfer (2026-10-26, UTC)

### Step 1: recover the next planned round and preserve the published base

- Created `phase-10-cross-city-av-comparison` from published Phase 9 receipt
  `c8a85ffb659f1a6958b69a302fdf1a8c8aeafe01`, with a clean checkout. Preserve
  every earlier record and use Xiaoyu Su /209944670+xiaoyu-su@users.noreply.github.com
  as both author and committer.
- Re-read IMG_3329: Round 3 asks whether Manhattan policy findings transfer to
  Munich and Chicago. Implement a generic city bundle/runner/reporter, a
  reference-derived dense-zone fence, city load configurations and thread-pinned
  comparisons. Human acceptance and repositioning stay off. The screenshot's
  numerical results are reference claims, not targets or reproduced evidence.
- Both public Zenodo records are accessible: Munich15195726 and Chicago15189440.
  Downloaded 144,829,706-byte `FleetPy_Munich.zip` and344,440,784-byte
  `FleetPy_Chicago.zip`, checked published MD5s
  `cf70c1631a8faad46ba4e2f2d7d7f71a` and
  `ab03f64c88dc4f1dba4f84e286e7e520`, computed SHA-256s and safely extracted
  246/305 files. Record URLs, metadata, checksums and file inventories under
  `/workspace/market_inputs/cross_city/`; execution log is
  `.setup/phase10/downloads.txt`. Authors Roman Engelhardt/Florian Dandl,
  CC BY4.0; original source README bytes remain unchanged.
- Important provenance: Munich `d_10` is **1%** of PV trips, generated from an
  AIMSUN traffic simulation; it is not a10% observed taxi sample. Chicago's
  `sample_10` is a10% TNC completed-trip sample for June7,2022, on the provided
  2023 OSM network. Neither supplies actual AV opt-in or online fleet exposure.

### Step 2: implement immutable city inputs and fair counterfactual controls

- `tools.city_av build/run/report` handles native node-matched requests, city
  zone maps, provided network dynamics and the existing verified Manhattan
  dataset. Parent input hashes/source identity are checked before rebuilding
  the Manhattan comparison; the parent bundle is never retagged or changed.
- Native fence/initial placement use only00:00–05:00 pickups, before05:00–07:00
  warm-up and07:00–10:00 evaluation. Manhattan retains earlier-Tuesday training
  references. Evaluation pickups cannot choose the fence. Missing native
  centroid flags are supplied using actual mapped access nodes; unmapped rows
  are counted explicitly. Original request IDs remain stable; causal admission
  uses ceiling to the60-second grid.
- Prespecified fleets: Munich50, Chicago100 (supplied upstream examples),
  Manhattan775 (existing training-workload proxy). Additional supply cases double
  total fleet at fixed10% AV share. Opt-in.3 and cautious travel time1.25 are
  assumptions. All benchmark arms use480s patience,30s pickup/drop-off service,
  no execution noise, no human acceptance, and no human/AV repositioning.
  Native ride-pooling is an explicit benchmark assumption; Manhattan's original
  source pooling consent remains enforced. This is not a new empirical calibration
  or a direct numerical comparison with differently configured Phase 9 results.
- All-human and AV replacement arms share actual initial position/SOC for each
  vehicle ID, with designated AV slots fenced in both arms. Actual simulator
  initialization hashes are reconstructed independently from the recorded
  placement plus actual roster. All-human slots remain unrestricted humans.
- Found a design confound before real experiments: a conventional all-human
  control would search one candidate pool, while AV arms search two. Added a
  benchmark-only shadow-slot partition with the same per-group position budget;
  it adds no AV cost/consent restrictions to humans. Ordinary matching is
  unchanged when the marker is absent. Both immediate insertion controllers
  are exercised with a one-position budget to test the actual partition.
- City workers reuse the existing physical booking/consent/tail guards. Added
  explicit city-only shared-placement/all-human flags, per-run full output
  hashes, actual boarding/alighting and service-duration checks, type-factor
  checks, fixed retained-human productivity and absolute empty-distance totals.
  Native C++ binary/source hashes are additional dependencies, not implicit
  untracked runtime assumptions. Private input/runtime tampering fails closed.
- The bounded runner caps BLAS/OMP/MKL at one thread and reuses available CPU
  slots via `taskset`. It launches at most the declared1–4 isolated workers;
  unlaunched jobs after a failure are labeled unrun. No real matching decision
  depends on a wall-clock optimization timeout in the IRSOnly comparison.
- Pooled reports retain every city/fleet/seed/policy, separate duplicate exact
  replays from independent conditions, compute paired conditional intervals,
  compare identical served rider IDs, and plot city curves with seed ranges.
  Source/data/load differences prevent a geography-only causal interpretation.

### Step 3: timely focused checks, failure and correction

- Initial frozen source `fa5558ad039bf75ff7be0a5a56870cab0b2092b30a4c92a0ed9f5347f1c22623`
  (253 files) stops during pytest collection: unit/integration files shared a
  basename. **1 collection error in0.96s; no simulations executed.** Renamed
  integration file to `test_city_av_examples.py`; retain original JUnit/log/source
  under `.setup/phase10/checkpoint/`.
- Corrected source `0844ab8377002d9c840660c4e858ebcc14579ccb95f04ff9ba1fe91ee777c095`
  (253 files) passes **12 tests in22.47s**, including **16 complete physical
  simulations**, actual Python/C++ route timing, exact human/AV replay and
  nonmutating Manhattan fixture adaptation. Evidence: `corrected/`.
- Added pooled reporting, actual initialization-audit reconstruction and the
  shadow search-budget control. Source
  `d7535c20af2beeb0cc9ba570e3f700f07f742d1f13692987835953ddb6a8bdcd`
  (254 files) passes **14 tests in40.05s /23 complete physical simulations**.
  Both immediate insertion controllers and Python/C++ routers pass. Modified
  report bytes are rejected, source-reference isolation passes, and input/runtime
  corruption fails before a result can be counted.
- Exact gate command: `.venv/bin/python -m pytest -q tests/unit/test_city_av.py
  tests/integration/test_city_av_examples.py
  --basetemp=/workspace/.setup/phase10/corrected-v2/runs
  --junitxml=/workspace/.setup/phase10/corrected-v2/junit.xml`, stdout/stderr at
  `corrected-v2/tests.txt`. Matching source snapshots and config files accompany
  all three checkpoints. Python/configuration remains frozen during physical runs.

### Step 4: real city builds and pilots (in progress at this checkpoint)

- `.venv/bin/python -u /workspace/.setup/phase10/prepare_pilots.py`, stdout/stderr
  at `pilots-console.txt`, builds five new immutable bundles under
  `/workspace/market_inputs/phase10/{munich,chicago,manhattan,munich_supply2x,chicago_supply2x}`.
  It then runs human-only and threshold240 pilots in all three cities, seed0,
  three pinned workers. Per-stage argument vectors, return codes, runtimes and
  logs are saved under `.setup/phase10/real/`.
- Prespecified main grid: two seeds0/1 ×three cities ×eight arms =48 physical
  runs: matched all-human; cost control; preference300; thresholds0/120/240/480;
  equal-speed threshold240. Supply sensitivity: two seeds ×two cities ×three
  arms (all-human /threshold0 /threshold240) =12 further runs at double fleet.
  Six seed0 pilots are replay checks against main conditions, not independent
  replicas: total66 physical runs /60 distinct conditions if all pass unchanged.
- No final success or policy improvement is claimed while these real cases or
  the required full regression gate remain unfinished. All failures, adverse
  outcomes and limits will remain in the published record.

### Step 5: real-input failures, explicit mapping and capacity semantics

- The first real build attempt on source `d7535c...` completes Chicago,
  Chicago2x and Manhattan inputs, but rejects both Munich builds before any
  pilot starts: its original map has **18 nodes with two memberships each**,
  all in overlapping zones28/29. Original30288 rows cover30270 unique nodes.
  It would be incorrect to silently accept a nonunique AV fence map.
- Add optional `zone_overlap_policy=lowest_zone_id` only in the Munich config.
  Default remains error for ambiguous maps. Record all original and chosen
  memberships, exact source-map hash and counts of retained/evaluation requests
  touching those nodes. This is an explicit deterministic benchmark convention,
  not a claim about the true administrative boundary. The original map is
  unchanged. New unit test proves default rejection and audited opt-in behavior.
- Source `985dc2bc330a341d56f2cfa65a4f35311a88f980962a890d23ebe6a6c924b03d`
  (254 files) passes **15 tests in40.27s /23 complete fixture simulations**.
  Five fresh real bundles under `market_inputs/phase10_final/` then build.
- The next real pilot group fails its reporting check after **54.4s**, before
  three later jobs launch. Chicago's all-human raw log contains one boarding
  row with occupancy5 in a four-seat vehicle; moving loads remain≤4. Investigation
  of the source and raw IDs shows a **4→4 passenger exchange**: FleetPy adds
  the incoming rider at stop start and removes the departing rider at stop end,
  so the raw stationary log is their five-ID union. This is an event-recording
  convention, not five seated riders travelling. Do not silently discard the row.
- Correct the city audit to check actual roster capacities, every moving load,
  pre-exchange load (union minus incoming), post-exchange load (union minus
  outgoing), passenger ID/occupancy consistency and exchange membership. Explicitly
  count stationary unions. Unit cases still reject five moving, five before,
  or five after an exchange. The underlying simulator and its raw output are
  unchanged. `capacity_diagnostic.json` preserves the vehicle46 event at
  35072.506623–35102.506623s, incoming201621/outgoing201488, and the independently
  verified0 moving violations/1 valid union. Past failed raw records stay intact.
- The failed pilot manifest labels three jobs uncollected after failure and
  three jobs unrun; it is not counted as a successful six-run experiment.
  Preserve `real_final/`, `phase10_final/` inputs/results and their frozen source.
- New source
  `95a9203fb932370c5edc9332070e8eb4ca0ab5621d7a28b5adf119b517214956`
  (254 files) is now frozen for the corrected focused gate and fresh validated
  pilots. Exact command uses the same two test modules, with paths under
  `corrected-v4/{runs,junit.xml,tests.txt}`. Fresh inputs/results use
  `market_inputs/phase10_validated/` and `market_results/phase10_validated/`;
  `prepare_validated_pilots.py` and `real_validated/` retain exact commands.

### Step 6: final focused gate and successful real pilots

- Source `95a920...` produces **17 passed /2 failed in41.18s**: the negative
  capacity fixtures used literal empty strings, while the actual CSV parser
  represents empty request fields as missing values. Both failures stop in the
  ID parser before reaching the expected capacity assertion. All23 physical
  fixture simulations finish; fresh real pilots do not start because the shell
  uses `set -e`. Preserve the failed JUnit/log/source under `corrected-v4/`.
- Correct the two negative fixtures to use missing values. The capacity audit
  and simulation behavior are unchanged. Frozen source
  `c8885e74c9661a558177ac56c908e11c403006ebafcb1ae536c7f0c59333caa7`
  (254 files) passes **19 tests in39.04s /23 complete physical simulations**.
  Evidence: `corrected-v5/`, including the actual source/config snapshots.
- Five fresh validated bundles build in approximately1.4s Munich,3.9s Chicago,
  2.1s Manhattan,1.4s Munich2x and4.1s Chicago2x. All six real seed0 human/AV
  pilots complete in **90.0s**, with complete accepted bookings, consistent
  actual initial states, pre/post/moving capacity, source consent, AV product,
  chronology, service duration and timing checks.
- Pilot evaluation completion (all-human →threshold240): Munich **586→544**,
  Chicago **529→554**, Manhattan **2464→2437**. AV trips are27/25/131.
  These are preliminary single-seed replacement outcomes, not universal gains.
  Neither fleet settings nor policies are retuned to the screenshot or these
  held-out results. The six pilots become exact replay checks against main runs.
- Actual final inputs: Munich **1892 evaluation +631 warm-up**, fence30 zones,
  50 vehicles5AV; Chicago **2051 +639**, fence234 zones,100 vehicles10AV;
  Manhattan **3150 +751**, fence19 zones,775 vehicles78AV. Native reference
  sizes are **88 /981** earlier rows; Manhattan has **63441** prior-training
  context rows. These differences are disclosed, especially Munich's sparse
  reference. Munich excludes54 unmapped rows from the full provided source;
  only **one evaluation request** touches a resolved duplicate-map node.

### Step 7: full regression and prespecified main/supply studies running

- With Python/configuration and Git parent held fixed, launch
  `.venv/bin/python -m pytest -q
  --basetemp=/workspace/.setup/phase10/full/runs
  --junitxml=/workspace/.setup/phase10/full/junit.xml`, stdout/stderr at
  `full/tests.txt`. This is the required complete gate, not only city tests.
- In parallel run `.venv/bin/python -u
  /workspace/.setup/phase10/run_final_studies.py`, stdout/stderr at
  `final-studies-console.txt`. Main uses two pinned CPUs/workers; supply uses
  one separate pinned CPU/worker. Exact CPU masks, commands, statuses, runtimes
  and per-case records remain under `real_validated/` and the final manifests.
  Outputs use `market_results/phase10_validated/{main,supply,pilot}`.
- Main48 and supply12 runs plus the six successful pilot/replay records are
  still being finalized. Do not count incomplete cases or declare the phase
  complete until all required gates and independent audits pass. No source
  changes are made while those simulations run.

### Step 8: all real studies complete and independent audit passes

- All **66 final physical runs** complete: main48 in **947.7s**, supply12 in
  **693.9s**, pilot6 in **90.0s**. All study return codes are0, with no source
  change. There are **60 distinct city/fleet/seed/policy conditions**; the six
  pilot cases are fresh-process repeats, not extra independent replicas.
- `.venv/bin/python /workspace/.setup/phase10/analyze_real.py >
  /workspace/.setup/phase10/analysis.txt 2>&1` independently checks all66 raw
  outputs, all5 private bundles and runtime hashes. All full unique demand,
  promise/boarding/alighting IDs, accepted completion, causal grid/deadlines,
  chronology, actual roster capacities, pre/post exchanges, private consent,
  AV fence/opt-in/product, actual type factors, common initialization and search
  budgets pass. Final tails have no remaining tasks/onboard riders.
- Generic pooled reporter verifies all raw output hashes, **53 within-study
  background comparisons** and **6 exact replay records**: three all-human
  controls each match6 critical physical/audit files; three threshold240 cases
  each match8. It excludes duplicate conditions from seed means. Scientific
  PNG/PDF is visually inspected; labels/units/fleet legends and two-seed range
  whiskers are legible. Analysis includes environment/package versions and a
  byte-exact native C++ binary/source runtime snapshot for reproduction.
- The analysis prints a nonfatal font-cache warning; the generated figure is
  readable and verified. No simulation/raw output is changed. The full pytest
  gate remains running at this checkpoint; all real runs passing does not
  substitute for that separate required gate.

### Step 9: measured policy transfer, adverse outcomes and load limits

- Main threshold0→240 mean AV occupied utilization: Chicago100 **33.64→52.80%**,
  Manhattan775 **13.12→20.00%**, Munich50 **38.75→38.66%**. Munich is essentially
  unchanged; there is no universal utilization-gain claim. Actual AV trip means
  are **24→28 /84.5→133 /25→25**, respectively.
- Main evaluation completion: Chicago **523.5→540.0**, Manhattan **2438→2444**,
  Munich **552.5→560.0**. Eligible served mean wait changes **307.60→307.61s**,
  **199.81→262.53s**, **305.00→301.96s**, respectively. These fixed two-seed
  mean effects do not establish a population benefit; paired intervals and
  common-served rider identities are retained separately.
- Against the matched all-human control, threshold240 main completion changes
  **+19.5 Chicago /−30 Manhattan /−29.5 Munich**. This is replacement of a
  fixed-size fleet with slower/constrained AV slots, not additional capacity.
  Do not describe AVs as universally adding completed trips.
- The doubled-fleet regimes change the threshold effect: Chicago200 completion
  **1195.5→1181.5** and eligible wait **271.92→287.78s**; Munich100 completion
  **1063.5→1051.5**, wait **270.28→301.71s**. Chicago200 AV trips fall
  **79.5→56** even as occupied utilization rises **42.75→48.26%**. Higher
  occupied time is not automatically more trips or better rider service.
- Supplementary `.venv/bin/python
  /workspace/.setup/phase10/service_duration_analysis.py >
  /workspace/.setup/phase10/service-duration-analysis.txt` derives actual
  completed passenger pickup-to-dropoff durations from unchanged raw outputs.
  Chicago200 mean AV duration rises **1264.33→1970.18s** across thresholds;
  Chicago100 **1570.96→1998.81s**. Passenger-time statistics, occupied vehicle
  time, warm-up carry-in and evaluation clipping have distinct domains, so
  these co-movements do not isolate one causal mechanism. CSVs retain all
  seed/product mean/median/q95/duration totals and both favorable/adverse changes.
- Fleet configuration matters much more to completion here: all-human means
  **589.5→1108.5 Munich** and **520.5→1295.5 Chicago** between main/double-fleet
  regimes. Across fleet sizes the designated-slot IDs and their starting layout
  also change; this is a configured load sensitivity, not an identical-background
  policy pair or a causal capacity estimate. Within each regime geometry and
  search are rigorously matched. The strongly scarce demo-fleet cases do not
  reproduce the screenshot's near-saturated/balanced numerical regimes.
- An unqualified adjective about detour bounds was removed from the derived
  passenger-duration explanation after checking the source: the existing40
  parameter denotes a percentage. The original analysis stdout and all numbers
  remain unchanged; `presentation_corrections.json` records this prose correction.


### Step 10: final full regression and historical compatibility

- `.venv/bin/python -m pytest -q --basetemp=/workspace/.setup/phase10/full/runs
  --junitxml=/workspace/.setup/phase10/full/junit.xml` passes **389 tests** in
  **2129.86s**, with **0 failures/errors/skips**. Source/configuration stayed
  frozen throughout all final real and regression runs.
- `.venv/bin/python /workspace/.setup/phase10/audit_suite.py` independently
  inspects **257 complete physical simulations +32 restored windows**. Unique
  demand, complete pickups/dropoffs, final state, chronology and explicit window
  censoring pass. All **201 historical non-AV cases /930 checked tables** are
  byte-identical, with **128 exact restored-window tables**.
- `.venv/bin/python /workspace/.setup/phase10/audit_av_history.py` verifies all
  **33 historical AV cases /241 checked tables** byte for byte, including the
  prior accepted-product/future-value combinations. Thus every234 old physical
  regression case remains unchanged across1171 checked tables.
- `.venv/bin/python /workspace/.setup/phase10/finalize_docs.py` updates phase,
  project and improvement records with actual counts and measured adverse
  outcomes. Markdown-only finalization does not alter tested code/configuration.


### Step 11: package and verify the complete reviewable record

- `.venv/bin/python /workspace/.setup/phase10/package_final.py >
  /workspace/.setup/phase10-package.txt 2>&1` archives **13064
  files**, preserving all failed/corrected focused gates, all full-suite physical
  records/windows, attempted and successful real studies, exact frozen source,
  runtime binary/sources, immutable parent input, public used inputs, build and
  analysis scripts, commands, logs, figures and checksums.
- Logical archive is **250483623 bytes**, split into **8
  upload parts** below GitHub's individual-file limit. Every member hash and
  every upload-part byte is verified by readback. SHA-256:
  `3b529a9cf8bedaeb83394035b17dc51238e39ae925c5f62abe6219dcbce9ac6d`. Large byte-identical public matrices alone are omitted with
  explicit canonical restoration paths, sizes and hashes; unknown/private and
  small fixture matrices remain included. Original ZIP download provenance and
  README attribution remain in the record.
- `.venv/bin/python /workspace/.setup/phase10/prepublish.py >
  /workspace/.setup/phase10-prepublication.txt 2>&1` passes: frozen254-file
  source equals the tested snapshot, all6 tracked configuration files match,
  every native runtime/input and all66 final raw-output hashes agree, all
  archive-part/logical hashes and canonical restore files agree, inspected plot
  matches, review links resolve, and historical evidence remains unchanged.
- README, project summary, improvement log, phase guide, complete RESULTS and
  evidence restoration guide are updated with actual benefits, adverse outcomes
  and remaining empirical/load limitations. No root simulation code or scenario
  configuration changes after the final validation freeze.


### Step 12: publish as Xiaoyu Su and verify GitHub

- Source/documentation whitespace and prepublication checks pass. Implementation
  **`5b6ca17d2321c3a45d661d032b6b066fa3ffab80`** contains the complete Phase10 code, configurations, records,
  source snapshots and measured policy tradeoffs.
- `git push -u origin phase-10-cross-city-av-comparison` succeeds; `git ls-remote origin
  refs/heads/phase-10-cross-city-av-comparison` returns that exact commit. Both author and committer
  are **Xiaoyu Su /209944670+xiaoyu-su@users.noreply.github.com**.
- Every committed source/dependency blob matches the frozen254-file source
  `c8885e74c9661a558177ac56c908e11c403006ebafcb1ae536c7f0c59333caa7`. All389 tests,257 regression simulations,32 windows and66
  real physical runs belong to these exact bytes; prior evidence is unchanged.
- `docs/validation/phase10/publication.json` records remote implementation tip,
  identity and evidence hashes. A documentation-only receipt commit follows;
  final remote equality, identity and checkout cleanliness are checked after
  its push before reporting completion. No token was printed/changed or saved
  repository selection modified.


## Phase 11: native upstream fidelity and consolidated validation

### Step 1: identify the next numbered plan section and preserve the base

- Continue from published Phase10 receipt `bccbad4bb179f48ba2fa2a53682d3d90f33c3cc3`
  on `phase-11-native-fidelity-validation`; checkout was clean. Author and
  committer remain Xiaoyu Su. Re-read original IMG_3329: after cross-city Round3
  comes section5, Validation, followed by section6, Limitations. Per-city AV
  repositioning is explicitly a follow-up, not a secretly added Round4 requirement.
- Scope: reusable clean-Git-archive native fidelity validation, feature-off
  proof for all3 bundled controllers and the3 full native city profiles; fresh
  process repeatability, physical completion and exact output comparisons;
  complete regression and preserved input/source/output/publication records.
  This phase improves validation coverage, not an AV dispatch policy.
- Native profile adaptations are declared before outcomes: no repositioning
  in both versions (prior original repo runs exceeded the Gurobi license); native
  C++ routers for Munich/Chicago; no wall-clock tree/solver cutoff in either
  version. Munich lacks the partial preprocessed tables the default example
  expects. All tracked upstream C++/Cython/setup sources match the installed
  binary source inputs; share only its exact hashed native binary, never fork
  Python, and audit every actual simulator import. Original tracked archive
  source/configuration hashes must remain unchanged.

### Step 2: implement an independent fidelity gate

- Added `tools/native_fidelity.py` orchestration and neutral
  `tools/fidelity_worker.py`, invoked by absolute filename in each source tree.
  Reference is fresh `git archive` of upstream
  `c813728b6d188df8dd7fd5d3d36dcb0a55c898a2`, never regenerated from fork
  outputs. Both versions use identical original scenario rows, data and
  explicit adaptations, one pinned CPU/thread and isolated fresh outputs.
- Observe actual booking/rejection callbacks, initialization/SOC, simulator
  imports, full unique demand, final task/rider drain and physical boarding/
  alighting. Independently audit chronology and real capacity. Compare every
  column/cell of users, vehicle legs, standard evaluation and final state with
  exact numeric/missing-value equality; report raw byte identity separately.
  Duplicate runs additionally require exact replay bytes. Never update approved
  baselines. All source/input/config/output hashes and failures are recorded.
- Added ten adversarial validation tests and3 complete bundled-controller
  comparisons, each with two upstream/fork pairs (12 physical runs). These
  verify source isolation, all accepted completions, exact comparisons and
  replays; they reject tiny value drift, missing/duplicate rows, schema changes,
  missing values, unsafe sources, ambiguous profiles and feature activation.
- No simulator/controller matching, movement, repositioning or defaults changed.
  Begin a focused complete simulation gate before running real native profiles.


### Step 3: focused gates pass and final source freezes

- First focused gate:13 tests pass in122.66s, including12 complete physical
  upstream/fork simulations across all3 native bundled controllers. All4 output
  tables agree exactly and fresh-process repeats are byte-identical.
- Added an explicit shared-vehicle-input equality guard and a negative drift
  test before real runs. Guarded gate:14 tests pass in126.16s, again12 complete
  physical simulations. Both snapshots/JUnit/raw runs remain preserved.
- Final source freezes at258 Python/dependency files, digest
  `d05aa8b2c2bcf7892e20d3016d7c05d8b3993c0ecb99fce8ca27417b716d1caa`.
  Source maps/snapshots and the exact native profiles are saved externally.
- Initial launches fail before Python/simulation startup: the new environment
  permits CPUs0–4, unlike the previous environment's24+. Preserve taskset error
  logs in `.setup/phase11/launch-failure`. No tests or physical runs occurred in
  these launches; no source changes are needed. Relaunch native cities pinned
  to0/1/2 and the full suite on3–4. Native real comparisons and the full suite
  remain pending until their actual successful completion and output audits.


### Step 4: full native city and clean published-archive fidelity pass

- For each city, run `taskset -c CPU .venv/bin/python -m tools.native_fidelity
  --profiles /workspace/.setup/phase11/profiles/CITY.json
  --output /workspace/.setup/phase11/native/CITY --repeats 2 --timeout 7200`,
  with CPUs0/1/2 for Munich/Chicago/Manhattan. All12 physical runs complete
  successfully: each source/city condition plus its fresh-process repeat.
- Both sources complete exactly **617/1788 Munich**, **5106/12753 Chicago**,
  **5399/10700 Manhattan**. Original full unique demand, actual initial position/
  SOC, acceptance/rejection histories, every user/vehicle/evaluation/final-state
  cell agree. All6 pairs match24 full tables byte for byte; the6 source
  repeats match another24 table comparisons. No baseline or policy is retuned.
- `taskset -c 4 .venv/bin/python /workspace/.setup/phase11/clean_artifact.py >
  /workspace/.setup/phase11/clean-artifact-console.txt 2>&1` extracts published
  Phase10 receipt `bccbad4bb179f48ba2fa2a53682d3d90f33c3cc3`, proves all254
  shared simulator/dependency files equal current Phase11, and runs all3 full
  native profiles with simulator imports confined to that extracted tree.
  The only4 new Python files are validation harness/tests. All3 runs complete;
  they match12 further complete tables against clean upstream byte for byte.
  Exact shared native binary/source/vehicle hashes are recorded. This is a
  clean published-source reproduction with verified shared runtime, not a
  separate compiler/toolchain rebuild.
- `.venv/bin/python /workspace/.setup/phase11/analyze_native.py >
  /workspace/.setup/phase11/analysis-native.txt 2>&1` independently reads back
  all15 native runs, source archives, original source members, used inputs,
  loaded native runtimes and raw output hashes. Full unique demand, completed
  accepted bookings, no rejected service, actual capacity/chronology, physical
  boarding/alighting and post-drain zero tasks/onboard riders pass. All60 full
  table comparisons are byte-identical. Native Chicago includes valid raw
  stationary occupancy unions; pre/post loads and moving loads fit actual seats.
- Native route warnings are preserved and counted in `native_warnings.json`;
  they occur on the original source too. Physical completion is verified
  independently. Full regression remains pending, so native success alone
  does not complete the phase. No simulator behavior or policy improvement
  is inferred from these same-output checks. Lower native completion counts
  describe rejected requests under the original clock/fleet/no-repo profile;
  they are not a direct Phase10 policy change or a screenshot-served-total fit.


### Step 5: complete regression, correct audit bookkeeping and verify all history

- `taskset -c 3-4 .venv/bin/python -m pytest -q
  --basetemp=/workspace/.setup/phase11/full/runs
  --junitxml=/workspace/.setup/phase11/full/junit.xml >
  /workspace/.setup/phase11/full/tests.txt 2>&1` passes **403 tests** in
  **2521.73s** (console), **0 failures/errors/skips**. Final source remains
  frozen at `d05aa8b2c2bcf7892e20d3016d7c05d8b3993c0ecb99fce8ca27417b716d1caa`.
- The first external `audit_suite.py` pass misclassifies10 deliberate malformed
  CSV negative-test fixtures as full simulations and raises a missing pickup
  column error. Preserve the exact failed helper as `audit_suite-first.py` and
  its traceback as `audit-suite-first.txt`. All403 tests and actual physical
  runs had passed; this is evidence-classification bookkeeping, not a simulation
  failure or a reason to modify tested simulator source.
- Correct the external audit to require the real simulator's `00_config.json`
  marker, with an explicit assertion that exactly10 excluded directories are
  the known five reference/candidate negative fixtures. All257 old physical
  records and all12 new controller records have the real marker. Unknown
  missing-marker outputs still fail; malformed inputs are never silently blessed.
  No root Python/configuration or raw output changes.
- `.venv/bin/python /workspace/.setup/phase11/audit_suite.py >
  /workspace/.setup/phase11/audit-suite-console.txt 2>&1` then passes independent
  inspection of **269 complete physical simulations +32 restored windows**.
  Full unique demand, completed pickups/dropoffs, final state and chronology
  pass, with explicit window censoring. Every **257 historical full case**
  retains **1548 checked tables byte for byte**, including user/vehicle/evaluation/
  final state and applicable driver/AV/repositioning audits; **128 window tables**
  retain exact values. The source fingerprint is checked again and unchanged.
- All15 native city/clean-artifact runs and60 full-table comparisons already
  pass independent physical/source/input/runtime/output readback. The original
  published1,552,353,280-byte Git source tar is additionally reconstructed as a
  hash stream by `verify_archive_restore.py`; SHA-256 matches exactly in3.35s,
  proving the indexed Git restoration command without storing another huge copy.
  Environment/package/ABI and actual CPU assignments are recorded separately.
- Improvement versus the prior gate:14 additional adversarial/controller tests,
  12 additional complete regression simulations, three full native city profiles
  on both source trees with repeats, three clean-source reproductions and
  exact four-table comparisons. Policies and matched service outcomes remain
  unchanged; no operational performance gain is claimed from fidelity results.


### Step 6: archive and complete reviewable documentation

- `.venv/bin/python /workspace/.setup/phase11/package_final.py >
  /workspace/.setup/phase11-package.txt 2>&1` archives13421
  records as701879937 bytes in21 upload parts. Every archived
  member hash and every part byte passes readback. Logical SHA-256:
  `bc93ab8faa693505c2e55067e69263f3128fb17b087e3845aed65dc3b35bb01a`. All raw logs/output/source/failed-launch histories remain;
  only byte-proved public matrices/duplicate historical payloads, reproducible
  pinned Git archives and caches/symlink aliases are omitted with
  explicit restoration records. No original evidence is overwritten.
- `.venv/bin/python /workspace/.setup/phase11/finalize_docs.py` updates phase
  guide, README, project summary, improvement log, upstream comparison and
  evidence restoration guide with actual counts, exact service equality,
  validation benefit and remaining field/profile limitations. Markdown-only
  finalization does not change frozen tested source or native profile bytes.


### Step 7: final prepublication gates and review

- `.venv/bin/python /workspace/.setup/phase11/prepublish.py >
  /workspace/.setup/phase11-prepublication.txt 2>&1` passes:258 source/dependency
  files equal the frozen tested snapshot; tracked root profiles equal the
  guarded snapshot and actual per-city CLI profiles; all native C++ source/
  binary hashes, used public inputs and all15 final raw outputs agree.
- All archive upload parts/logical SHA and explicitly omitted canonical public
  matrices/protected historical payloads verify. The omitted large published
  archive additionally passes actual pinned-Git reconstruction by hash stream.
  Every review link resolves; historical evidence and approved baselines remain
  unchanged. Markdown spacing is reviewed without altering any source, native
  profile, test result or raw physical record.
- Earlier `git push --dry-run origin HEAD:refs/heads/phase-11-native-fidelity-validation`
  confirms current push authentication without creating/updating a remote ref.
  This is not publication: the tested implementation is committed and actually
  pushed next, followed by exact remote-tip/source/identity verification.
- Source/documentation whitespace is checked before commit; generated raw
  TXT/XML logs remain byte-exact. Validation coverage improves by14 tests,
  12 complete regression simulations and the15 native/clean checks; actual
  policy outputs remain unchanged in the declared matched native profiles.


### Step 8: publish as Xiaoyu Su and verify GitHub

- Implementation **`56edc2424ac90a6d30282a49ba127b0201e0838e`** contains the full Phase11 native-fidelity
  harness, profile assumptions, tests, raw evidence and measured validation
  coverage. Native `git push -u origin phase-11-native-fidelity-validation` succeeds, and `git ls-remote`
  returns that exact implementation tip. Author and committer both verify as
  **Xiaoyu Su /209944670+xiaoyu-su@users.noreply.github.com**.
- All258 committed Python/dependency blobs match frozen source
  `d05aa8b2c2bcf7892e20d3016d7c05d8b3993c0ecb99fce8ca27417b716d1caa`. The403 tests,269 regression simulations,32 restored windows
  and15 native physical runs belong to those exact bytes. Earlier evidence and
  approved baselines remain unchanged. No simulator policy/default changed.
- Publication receipt records verified remote implementation, identity and
  evidence hashes. A documentation-only receipt commit is pushed next; final
  remote equality, identity and clean checkout are checked after that push.
  No tokens are printed/changed and no saved repository selection is modified.


## Phase 12: cross-city demand-based AV repositioning

### Step 1: identify the documented follow-up and preserve the published base

- Continue published Phase11 receipt `6623109ce1f60ad73314184c4c7ef8abc233823b`
  on `phase-12-cross-city-av-repositioning`; initial checkout clean, author and
  committer remain Xiaoyu Su. The source plan's final limitations and Phase11
  guide explicitly identify per-city demand-based AV repositioning as follow-up.
- Scope: use a strictly separate AV-eligible origin/destination reference to
  position idle AVs in Munich/Chicago/Manhattan; compare identical threshold0/240
  fleets with AV repositioning off/on, fixed speed/search/geometry/SOC/opt-in.
  Human acceptance/repositioning, retargeting, noise and joint planning stay off.
  Measure actual trips, waits, utilization, retained-human productivity and
  absolute empty driving, preserving favorable and adverse effects.
- Forecast method is prespecified: stationary spatial weights from native
  pre-warmup reference or prior Manhattan Tuesdays, filtering both endpoints
  through the existing fence. Relative counts allocate AV target shares; they
  are not calibrated future demand volumes. Sparse native references and
  temporal transfer remain limitations. No evaluation/warm-up trip enters
  construction. Source/map/initial placement and source consent remain intact.
- Workspace space was insufficient for indefinite cache duplication. Removed
  only the redundant1,552,353,280-byte published-source Git tar already omitted
  from the Phase11 Git evidence with exact pinned restoration metadata. Its
  size/SHA and prior actual Git-stream reconstruction are verified, and the
  pinned commit exists. `reclaimed-reproducible-cache.json` preserves the action
  and exact restoration command. All physical records and source edits remain.

### Step 2: optional causal reference inputs and physical repositioning checks

- Added `tools/city_av/reposition.py`: approved-reference dates/clock and unique
  IDs, mapped endpoints, explicit eligible OD counts and source hashes; relative
  weights for every fence zone/time interval; complete reference evidence.
  No eligible reference fails closed. A new explicit build flag opts in;
  existing bundles/parameters/reports retain the old default shape.
- Extended city runner to enable the existing AV demand repositioner only with
  the declared separate-reference bundle. All-human controls and old no-repo
  bundles retain their previous behavior. No core matching/movement/reposition
  algorithm changes. Both immediate insertion controllers and C++ routing are
  exercised in complete feature-on runs, alongside defaults.
- New physical contract verifies loaded forecast bytes, callback grid, actual
  reference weights/target allocation, unique AV-only fenced centroid commands
  and empty actual repositioning legs. Every real leg traces to a prior
  command; target arrivals and interrupted legs are distinguished. A command
  alone is not physical feature exercise. Existing full unique demand, accepted
  completion, service, privacy, capacity, chronology and product checks remain.
- Reporter adds matched off/on paired-seed and common-served-rider comparisons,
  actual repositioning distance/time/arrivals/interruption statistics and
  standalone scientific PNG/PDF changes. Existing no-feature report fields
  remain unchanged. Five tracked configurations declare all assumptions.

### Step 3: first focused failure, fix and complete rerun

- First focused checkpoint:22 pass/8 fail in17.70s, before worker startup. The
  capability preflight accesses an AV-only field after the all-human control
  is inserted; missing `av_repositioning` raises KeyError. No physical
  simulation launched. Preserve exact source/logs/JUnit in `checkpoint`.
- Fix only the preflight boundary: all-human's missing AV lever defaults to
  off. Add the explicit private-rider/earlier-date Manhattan-style full case,
  alongside invalid future/unapproved dates, absent eligible OD, unknown
  methods, target/warmup perturbation invariance, immutable reference inputs
  and unsupported missing-reference preflight rejection.
- Corrected focus command: `.venv/bin/python -m pytest -q
  tests/unit/test_city_av_repositioning.py
  tests/integration/test_city_av_repositioning_examples.py
  tests/unit/test_city_av.py tests/integration/test_city_av_examples.py
  --basetemp=/workspace/.setup/phase12/corrected/runs
  --junitxml=/workspace/.setup/phase12/corrected/junit.xml`. **31 tests pass**
  in103.59s, covering50 complete physical runs (27 new +23 previous city
  checks), including both insertion controllers/Python+C++ routing, real
  empty AV movement with physically correct type speed, private consent,
  exact off/on replays and disabled/default compatibility.
- Source freezes at261 Python/dependency files, digest
  `a1a49b82e8c4cdd5027017c4decdaa596020cfb60424e5da83e14193ff1ecdb3`.
  Both successful/failed source maps and all five configuration snapshots are
  preserved. No Python/config edits while final physical studies run.
- Prespecified real design: main3 cities×3 seeds(0,1,2)×5 arms(all-human;
  threshold0/240 crossed with AV repositioning off/on)=45 physical runs.
  Double-fleet sensitivity2 cities×3 seeds×3 arms(all-human;threshold240
  off/on)=18. Nine seed0 pilot records repeat main conditions exactly and
  are excluded from independent means. Total72 physical/63 unique conditions
  plus9 replays. Main/supply keep source cohorts/fleet assumptions from Phase10;
  controls on seeds0/1 can additionally be compared against earlier raw runs.
  Run9 real pilots and inspect actual contracts before main/full experiments.


### Step 4: real pilot exposes a soft-waypoint passenger-service gap

- `.venv/bin/python /workspace/.setup/phase12/prepare_pilot.py >
  /workspace/.setup/phase12/prepare-pilot-console.txt 2>&1` builds all5 real
  bundles successfully under frozen a1a49 source. Separate eligible reference
  counts are23 Munich/651 Chicago/15951 Manhattan. Nine pilot cases are planned.
- Pilot reporting fails on Chicago threshold240+repo: **8 actually moving
  repositioning legs carry passengers over18.986561km**. All are real AV IDs;
  raw chronology shows pickup, travel to an old empty target, then service
  continuation. Preserve all raw outputs, manifest statuses, source and exact
  diagnostic rows in `occupied-reposition-diagnostic.json`.
- Four pilot cases report complete; Munich repo is uncollected after peer
  failure, Chicago repo fails physical policy audit, and3 Manhattan cases
  are unrun. Six workers physically finish, but this is not a successful
  nine-case study. No main/supply/full-suite run launches at this point.
- Diagnosis: shared insertion can retain an unlocked empty repositioning
  waypoint between passenger pickup/dropoff. The reporter correctly rejects
  occupied repositioning; do not relax it or relabel output to hide the gap.

### Step 5: opt-in service priority, locked-work preservation and feature combinations

- Add `op_av_service_priority`, off by default and scoped to the two immediate
  insertion controllers with AV repositioning. Both ordinary insertion and
  fallback cost/ETA evaluation remove only cancellable AV goals from a copy
  before scoring. Shared insertion also covers native batch vehicle copies.
  Live plans/caches stay unchanged during proposals; accepted tours replace
  soft goals, and actual committed preemptions are audited. Existing profiles
  without the flag retain previous behavior and output fields. City repo-on
  workers enable the flag; no-repo/human controls receive no override.
- Expanded first priority gate:75 pass/3 fail in177.21s;77 physical runs
  finish. One lock test catches that an existing plan-copy method drops the
  infeasible-lock marker, causing the first cleanup implementation to remove
  that stop. Fix by deciding removal against original stops and restoring
  infeasible-lock flags on retained copies. Add explicit lock-state assertion.
- Two targeted contrast fixtures also fail their legacy-reproduction assertion:
  all real workers succeed, but the synthetic waypoint is too far from the
  direct route for the legacy optimizer to retain it with a rider. Tighten
  only the synthetic geometry to an almost-collinear waypoint, reproducing
  the exact bug in IRSOnly. Batch can already discard some soft targets later;
  both controllers still require priority before booking and correct physics.
  No real data, forecast or outcome target is tuned. Preserve the failed
  priority source/JUnit/raw outputs.
- Final expanded gate command includes the two city test files, previous
  city checks, `test_av_product.py`, `test_av_round2.py`, and
  `test_av_round2_examples.py`, using `priority-v2/runs` and JUnit output.
  **78 tests /77 complete physical simulations pass in178.79s**. Covers
  explicit/end/infeasible locks, unchanged legacy/human plans, old occupied
  waypoint contrast, both insertion controllers, C++ routing, private riders,
  human acceptance/future value/shifts and joint/noisy/retargeted repositioning,
  along with exact replay.
- Final source freezes at261 Python/dependency files, digest
  `649db5e784a7838c98a31d23e21048be09fa4697e2fd5931b25d5897df110a28`.
  Rebuild all5 input bundles into fresh `phase12_priority` directories rather
  than changing source labels on old bundles. Verified identical large matrices
  share storage between the immutable failed/corrected snapshots; every path,
  byte/hash and original raw run is preserved and sharing is recorded.
- Rerun9 real pilots using `prepare_priority_pilot.py`; final studies and the
  full suite wait for actual successful output inspection. No Python or
  configuration edits while these source-guarded simulations run.


### Step 6: corrected native pilot passes and prespecified final studies start

- Corrected pilot completes all9 cases successfully. Every repo-on case
  physically moves empty AVs only, consumes the verified reference, clears
  all accepted bookings and passes all product/privacy/service/capacity checks.
  Actual service-preemption counts are9 Munich,22 Chicago,44 Manhattan.
  Chicago occupied reposition legs change from8 in the preserved old pilot
  to0 under service priority. Do not equate the old18.99km label total with
  an independently identified avoided-driving distance.
- Seed0 threshold240 off→on: Munich completion544→552, AV trips27→21;
  Chicago554→560, AV25→43; Manhattan2437→2486, AV131→175. Preserve the
  adverse Munich AV-allocation direction. These are pilot values, not final
  three-seed means or a universal policy benefit.
- External pilot result collector initially raises duplicate-city TypeError
  because city already exists in the per-run report. Preserve its original
  helper and error record; fix only dictionary construction. Real pilot
  simulations/reports were already complete. No root Python/input/raw output
  changes. Corrected collector verifies all9 plus all6 seed0 historical
  off/human controls byte for byte across physical/initialization/audit files.
- Final real command launcher: .venv/bin/python
  /workspace/.setup/phase12/run_final_studies.py >
  /workspace/.setup/phase12/final-studies-console.txt 2>&1.
  Main45 uses2 pinned workers onCPUs0/1; supply18 uses1 onCPU2. Both use
  seeds0,1,2 and immutable priority input bundles. Exact child commands,
  environments, statuses, output hashes and timings are retained.
- Full gate starts: taskset -c 3-4 .venv/bin/python -m pytest -q
  --basetemp=/workspace/.setup/phase12/full/runs
  --junitxml=/workspace/.setup/phase12/full/junit.xml >
  /workspace/.setup/phase12/full/tests.txt 2>&1.
  Expected424 tests,306 complete regression simulations and32 restored
  windows; these remain pending until actual completion/audit. No source/
  configuration/HEAD changes while paired studies or this suite run.
- Current GitHub push authentication is separately checked by a native
  dry run; no remote branch/ref is created by that check. Actual tested
  implementation/evidence publication follows only after final gates pass.


### Step 7: independently verify all real outcomes and retain measured tradeoffs

- Main45, supply18 and pilot9 all finish successfully under frozen649db5
  source. Commands: `.venv/bin/python /workspace/.setup/phase12/analyze_real.py`,
  `historical_real_controls.py` and `service_duration_analysis.py` (same external
  helper directory). Capture their exact source/console outputs in the archive.
- First independent reference readback fails because public Munich IDs are
  float-valued CSV fields (`22.0`) while the builder validates/canonicalizes
  them as integers (`22`). Preserve the first audit helper and traceback.
  Validate finite integer-valued original fields before canonicalizing IDs in
  the independent reader; no source/input/raw simulation output changes or
  requirement is relaxed. Every exported identity, reference time, mapped OD,
  endpoint flag, prior-date boundary, stationary weight and apportioned fleet
  target then matches its independent reconstruction in all72 runs.
- Full raw readback verifies unique whole-demand identities, causal grid and
  patience, all promised bookings picked up/dropped off, zero tail tasks,
  chronological activity, moving/pre-post capacity, explicitly retained
  stationary exchange unions, physical service minima, private rider consent,
  AV fence/opt-in/product, native runtime hashes, actual placement/SOC and
  matched search/random backgrounds. All72 runs have zero rule violations.
- All27 repo-on physical cases actually move empty AVs; zero occupied repo
  legs. Their587 committed service-preemption events are independently traced
  to real served requests and previously commanded target nodes. These counts
  include the nine-pilot replay study; they are physical record totals, not an
  independent-sample count. There are63 unique conditions, nine exact fresh-
  process replay records and54 matched-background comparisons. All26 comparable
  historical off/human controls retain214 critical files byte for byte.
- Threshold240 OFF→ON three-seed means (completion; AV trips; occupied AV %;
  eligible served wait seconds; whole-fleet empty kilometers):

  | City/fleet | Completed | AV trips | Occupied % | Wait s | Empty km |
  | --- | --- | --- | --- | --- | --- |
  | Munich50 | 556.00→551.67 | 25.67→21.00 | 39.53→36.90 | 302.44→309.73 | 1033.37→1102.90 |
  | Chicago100 | 547.00→549.33 | 29.33→40.33 | 53.87→59.09 | 311.52→320.53 | 727.31→1252.75 |
  | Manhattan775 | 2441.00→2482.33 | 134.00→175.67 | 20.40→27.01 | 257.34→245.70 | 1438.85→1908.51 |
  | Munich100 | 1050.33→1052.33 | 46.67→52.33 | 33.08→36.93 | 303.80→299.78 | 1780.24→1944.97 |
  | Chicago200 | 1208.67→1296.00 | 60.67→107.67 | 48.79→57.07 | 284.79→276.86 | 1218.47→2283.14 |

- Preserve threshold0 results, every seed, paired uncertainty, identical-served-
  rider wait changes, human allocation and actual passenger duration. Chicago100
  threshold240 completion changes by+6/+26/−25 across seeds; Munich100 by
  +43/0/−37. These are conditional mixed effects, with more empty driving in
  every regime. The safety/accounting correction is a verified improvement;
  repositioning is not uniformly a service improvement or a field calibration.
- Visually inspect the12-panel scientific figure: readable city/fleet/threshold
  labels, explicit ON-minus-OFF and paired-seed-range whiskers, negative outcomes
  and absolute empty-driving costs intact. Save inspected-image SHA and checks.
  Source/configuration/HEAD remain unchanged while the full suite continues.
- Additional report command: `.venv/bin/python
  /workspace/.setup/phase12/interpretation.py`. At threshold240 the mean of
  same-served eligible riders' per-seed wait changes is+21.01s Munich50,
  +1.15s Chicago100,−15.85s Manhattan775,+2.84s Munich100 and−11.38s Chicago200.
  Munich100's served-only aggregate wait falls4.02s while these same riders'
  wait rises2.84s. The report explicitly retains this compositional difference,
  per-seed common-served counts and the conditioning limit; it does not turn a
  changing served sample into a claim that all riders benefit.


### Step 8: full regression and independent historical gates pass

- Full command from Step6 exits0: **424 passed in2449.99s (40m49s)**,
  zero failures/errors/skips. Exact JUnit time2449.986s, start2026-10-26
  19:17:25 UTC, pinnedCPUs3/4 and completion observation are retained in
  `full/execution.json`. Source/configuration/HEAD remain frozen throughout.
- `.venv/bin/python /workspace/.setup/phase12/audit_suite.py >
  /workspace/.setup/phase12/suite-audit-console.txt 2>&1` independently checks
  **306 full physical simulations and32 restored windows**. Full request IDs
  are unique; every picked-up request is dropped off, chronological vehicle
  rows are valid, and all available accepted-promise records complete.
  Original upstream outputs without promise fields remain explicitly marked
  unavailable, not inferred. Exclude exactly10 known negative comparison CSV
  fixtures, which have no physical scenario configuration. Archived source
  tables without a physical final/user record are not counted as runs.
- All **269 previous full regression cases retain1596 checked tables byte for
  byte**. All32 previous windows retain128 exact table values. Comparisons
  cover the primary physical outputs and applicable acceptance, choice, future
  value, ranked/rematching, AV dispatch/product and repositioning audits.
  The inherited baseline/reference files and all previous evidence remain
  unchanged. New source is opt-in and preserves old defaults in actual output.
- External audit is strengthened to check available accepted promises as well
  as pickup/dropoff pairing; retain the initial audit helper. Four earlier
  focused checkpoints are reconciled to their JUnit/source/raw-folder counts
  in `checkpoint_integrity.json`, including all recorded failures/corrections.
- Final gates therefore establish424 passing tests,306 complete regression
  simulations,32 restored windows,72 real policy runs/63 unique conditions,
  nine exact replay records,54 matched-background checks and26 historical
  real controls/214 byte-identical critical comparisons. No simulation code
  or configuration changes follow; remaining work is documentation/evidence
  packaging, final readback, commit and GitHub publication.


### Step 9: complete evidence archive and final review documents

- Package 18809 records as414161120 bytes in
  13 upload parts; every archived member hash and every part byte
  passes readback. Logical SHA-256:e5faeb681807eefb0dca4dbc73535f4c5d92245daeb0fbbb105171d744041904.
- Complete failed/corrected source/test/raw histories, both real input versions,
  old Manhattan parent, all final/failed physical studies, independent audits,
  commands, configurations, scientific figures and runtime dependencies are
  retained. Only byte-proved canonical public matrices and caches/symlink
  aliases are omitted with explicit reconstruction metadata.
- Finalize phase guide, README, project summary, improvement log and evidence
  restoration guide with measured three-seed outcomes, lower/worse effects,
  intended/verified benefits, actual service-priority fix and empirical limits.
  Markdown changes do not alter tested source/configuration or raw records.
- Documentation-only finalizer first stops before writing because a spacing
  cleanup changed its expected draft paragraph (`and77` versus `and 77`).
  Correct the text match in the external helper; save exact corrected helper
  as `documentation_finalizer.py.txt` and the failure/correction description
  alongside published evidence. The first helper remains in the sealed archive.
  Final docs receive spacing/table rendering cleanup. No Python/dependency,
  experiment configuration, simulation output or sealed archive bytes change.


### Step 10: final publication gates pass

- `.venv/bin/python /workspace/.setup/phase12/prepublish.py >
  /workspace/.setup/phase12-prepublish-console.txt 2>&1` exits0. It rechecks
  all261 frozen source hashes, all5 configuration snapshots, all5 verified
  input bundles/native runtime, all72 final raw output hashes and final study
  manifests. The63 unique conditions, nine exact replays,54 matched backgrounds,
  306 full regressions/32 windows,269 old full cases and26 historical real
  controls match the independently audited counts.
- All13 archive upload parts and logical archive SHA are verified again:
  `e5faeb681807eefb0dca4dbc73535f4c5d92245daeb0fbbb105171d744041904`.
  There are18809 member records in414161120 bytes. All16 omitted public-matrix
  paths have exact size/SHA-verified canonical restoration data. Scientific
  PNG/PDF copies match the inspected analysis, and all local report links exist.
- Historical evidence, regression baselines and approved reference files are
  unchanged against parent6623109. Whitespace checks cover Python/Markdown/JSON;
  raw CSV/TXT/XML bytes are retained unchanged. All changes are ready for a
  Xiaoyu Su implementation/evidence commit and native GitHub push. A publication
  receipt binds the tested source to the actual remote-verified commit afterward.
