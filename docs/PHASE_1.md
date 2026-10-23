# Phase 1: independent streams and paired policy evaluation

## Purpose and benefits

Previously passenger loading, parcel loading, and optimizer construction reset
the same global NumPy stream. Optimizer draws could also share randomness with
traveler choices. This makes policy comparisons sensitive to unrelated draw
order. Phase 1 introduces explicit named streams and verifies shared exogenous
inputs before comparing policies. It changes experiment reliability, not the
matching objective, driver acceptance, ETA execution, or AV dispatch rules.

The default remains `random_stream_mode=legacy`. All three Phase 0 references
continue to compare exactly, with no changes to the approved baseline CSVs.

## Configuration and implementation

Add this row to a constant scenario CSV to opt in:

```csv
random_stream_mode,independent
```

Use `n_cpu_per_sim=1` when calling the simulator. Optimizer worker processes
are not yet ported; independent mode rejects larger worker counts. Invalid
mode names raise an error instead of silently falling back.

`src/misc/seeding.py` provides `derive_rng(master_seed, name)`. It derives
entropy from the master seed and the SHA-256 digest of a UTF-8 stream name,
then constructs NumPy SeedSequence/PCG64. It does not use Python's salted
`hash()`, an order-dependent spawn counter, or process-global mutable state.
Callers retain their generator rather than re-deriving it for each draw.

| Stream | Owner and purpose |
| --- | --- |
| `demand` | Passenger request-class assignment during input loading |
| `parcels` | Parcel request-class assignment, independently of passengers |
| `traveler/<type>/<id>` | Each request's stochastic offer choices |
| `vehicle_initialization/<operator>/<vehicle>` | Initial location and battery state, stable for shared vehicle identities |
| `batch_optimizer/<operator>` | Batch optimizer's randomized construction order |
| `batch_optimizer/<operator>/solver` | Explicit Gurobi seed for Alonso-Mora |

In legacy mode the original global calls, reseeding points, and call order are
retained. Optional advanced modules that have not been ported still have
global randomness, initialized as before. This is not a claim that every
random call in FleetPy has been isolated.

The supported paired runner currently covers one operator and the three
baseline matching controllers: PoolingIRSOnly,
PoolingIRSAssignmentBatchOptimization, and
RidePoolingBatchAssignmentFleetcontrol with Alonso-Mora. It rejects explicit
repositioning strategies, other batch optimizers, existing initial-state
snapshots, and differing exogenous configuration. Advanced forecasting,
reservation, coupled simulators, and multiprocess optimizers require their
own stream and input audits before extending this experiment scope.

## Input identity checks

Independent-mode simulations write `random_streams.json`. It records:

- The seed, stream scheme/version, and passenger/parcel counts.
- Source demand file hashes and fingerprints of the actual loaded request
  inputs, including assigned request classes, locations, and time constraints.
- Road node/edge file hashes.
- A fingerprint of initial vehicle identities, types, positions, and SOC.

The paired evaluator requires these records to match within each seed before
performing inference. It also verifies that every loaded request appears
exactly once in final rider output. Matching only the numeric seed or demand
filename is insufficient. Fingerprints establish equality of these recorded
inputs, not identity of all counterfactual outcomes or causal identification
for every possible model extension.

## Run a complete comparison

From the repository root in the prepared Python 3.10 environment:

```bash
source .venv/bin/activate
python -m tools.paired_eval \
  --constant-config studies/example_study/scenarios/constant_config_ir.csv \
  --baseline-scenarios studies/example_study/scenarios/example_ir_only.csv \
  --candidate-scenarios studies/example_study/scenarios/example_ir_batch.csv \
  --seeds 0 1 2 \
  --output /tmp/fleetpy-phase1-comparison
```

Each policy file must contain one scenario. Configuration snapshots preserve
their CSV/YAML extension. Seeds must be unique and within FleetPy's existing
NumPy legacy-seed range, 0 through 2**32-1. The runner forces independent mode,
one optimization thread, fresh output, and exception propagation. It uses a
fresh process for each simulation, stable Python hashing, and one BLAS/OpenMP
thread. Its process-local directory override changes only the result location.

The output directory must not exist. A failed experiment is retained with
`status=failed`, logs, and the error; it is never silently overwritten or
presented as a completed comparison. Start another attempt in a new directory.

## Outputs and accounting definitions

| File | Contents |
| --- | --- |
| `manifest.json` | Status, commands and exit codes, seeds, copied-config hashes, package versions, Git HEAD plus hashes of tracked/untracked Python sources, validated input audits, and report hashes |
| `configs/` | Exact configuration snapshots used by workers |
| `runs/seed_<n>/<arm>/` | Full unmodified simulation result files, including input audits |
| `runs/seed_<n>/<arm>.log` | Captured stdout/stderr for that simulation |
| `per_driver.csv` | Every roster vehicle, including idle and inactive vehicles |
| `driver_distribution.csv` | Per-seed/arm mean, population SD, CV, p10/p50/p90, Gini, and finite-value counts |
| `seed_summary.csv` | Rider/fleet metrics and flattened driver distributions per seed/arm |
| `paired_comparison.csv` | Candidate-minus-baseline differences, paired 95% t intervals, paired t-tests, and two-sided Wilcoxon tests across seeds |

Source hashes include uncommitted and untracked Python files, because Git HEAD
alone does not identify the code under development. Source changes during an
experiment prevent a `complete` status. Report hashes allow checking the
retained artifacts against the manifest.

Times are seconds and monetary amounts are **cents**:

- Driving time includes all moving statuses, including empty repositioning.
- Occupied time is logged time with positive occupancy, including boarding
  when the output records passengers on board. It overlaps driving time;
  these are not mutually exclusive categories.
- Idle time is unlogged gaps plus explicitly logged idle time. Logged waiting
  on an assigned task is not automatically classified as idle.
- Online time excludes logged `out_of_service` time. No new human shift model
  is inferred or implemented.
- FleetPy drains pending assignments after `end_time`. All exact recorded tail
  legs and completed request-cohort fares are included. Each vehicle's exposure
  ends at the later of the configured end or its own final recorded leg;
  `accounting_end_time` and `tail_time_s` expose that choice. Other vehicles are
  not charged idle time until the last vehicle finishes.
- Gross fare revenue sums fares from completed rides assigned to that vehicle.
- Modeled net earnings subtract distance-based vehicle costs, actual tolls,
  and daily fixed cost prorated to that vehicle's accounting exposure.
- Earnings per online hour divide that proxy by online hours; zero-online-hour
  vehicles have an undefined rate rather than a fabricated zero.

These are **fare/vehicle-cost proxies**, not observed driver compensation.
Commissions, wage guarantees, tips, taxes, and actual driver labor costs are
not available and are not invented. The cost allocation is separate from the
upstream evaluator's accounting conventions.

Quantiles use NumPy's default linear interpolation. CV is population SD divided
by the absolute mean; all-zero samples have CV zero. Gini is zero for all-zero
samples and undefined when any value is negative. Missing/undefined values
are counted explicitly, not silently converted to zero.

## Statistical interpretation

The independent replicate is a **seed**, not a driver or request. Confidence
intervals use paired differences and the Student-t distribution. P-values are
unadjusted across metrics; the report does not automatically declare a winner.

Identical paired values report a zero difference/interval and p=1. A constant
nonzero difference has an undefined t-test and is labeled accordingly. Fewer
than two finite pairs produce `insufficient_pairs`. Every metric reports
omitted-pair counts; missing values are not evidence of no effect.

The three-seed development demonstration completed with matching inputs for
all seeds. Mean completed requests were 93 in both policies; mean rider wait
was 150.81 s versus 141.35 s. The paired difference was -9.46 s, with a 95% t
interval of [-16.16, -2.76] s, t-test p=0.026, and Wilcoxon p=0.25. This is a
small demonstration of the reporting pipeline, not a general policy finding.

## Validation and records

```bash
python -m pytest -q
```

Checks cover stable streams across process hash salts; demand/parcel and
optimizer interference; per-request stochastic choice; legacy regression
parity; hand-computed time, cost, inequality and inference examples; tail work;
input mismatch rejection; and complete CLI experiments for identical and
different policies on multiple seeds. Identical policies must reproduce exact
rider/evaluation outputs and zero finite paired effects. Existing experiment
directories are tested for overwrite refusal.

`docs/WORK_LOG.md` records intermediate failures, diagnoses, fixes, commands,
and outcomes. `IMPROVEMENT_LOG.md` summarizes the delivered change and benefits.
Final verification: **41 passed, 0 failed, 0 skipped**. The final three-seed
demonstration completed six simulations and three matched input audits.
Its actual manifest, CSV reports, and test evidence are retained in
`docs/validation/phase1/`.
