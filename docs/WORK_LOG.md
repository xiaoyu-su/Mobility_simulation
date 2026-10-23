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
