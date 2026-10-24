# Phase 6: windowed parallel policy evaluation

`tools/windowed_eval/` runs one complete baseline per seed, saves its live world
before each window boundary, and evaluates both policies from those same states.
This avoids rerunning the entire lead-in for every policy/window. Ordinary
simulation and Phase 1 paired evaluation keep their existing behavior.

## Run

From the repository root with its Python environment and Gurobi available:

```bash
PYTHONHASHSEED=0 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
.venv/bin/python -m tools.windowed_eval \
  --constant-config studies/example_study/scenarios/constant_config_pool.csv \
  --baseline-scenarios studies/example_study/scenarios/example_batch_driver_choice_control.yaml \
  --candidate-scenarios studies/example_study/scenarios/example_batch_forbid_rematch.yaml \
  --seeds 0 1 2 --window-seconds 2400 --cooldown-seconds 300 \
  --network-tt-noise-sigma .3 --workers 2 --timeout 180 \
  --output /tmp/windowed-rematch
```

The output must be new. Windows partition the configured request interval;
window/cooldown durations must align with the integer simulation step. The last
window may be shorter. Every optimization remains single-worker; `--workers`
limits independent fresh simulation processes. Each has a timeout and its own
log/output directory. Failed jobs retain their logs/status, stop pending
launches, and cancel other active jobs. A failed experiment is never reported
as complete.

## What a snapshot preserves

The full object graph includes vehicles and their active routes/remaining
noisy leg times, travelers and commitments, demand, broker, routing weights and
caches, controller/optimizer graphs and plans, driver decisions/classes and
choice ownership, future-value state, named generators, and legacy NumPy/Python
random states. Completed traveler objects remain available for cohort metrics.
Booking/rejection hooks call the original broker methods exactly once and keep
event times; the ordinary traveler decision-time column does not reliably
record booking time.

The custom pickler serializes objective closures, referenced modules, defaults,
and closure cells. It flattens the road graph's cyclic links, preserving ordered
incoming/outgoing adjacency and shared edge identities, to avoid deep-recursion
failures. It restores the existing graph rather than reinitializing a network.
These are local, trusted Python pickles, tied to the recorded exact Python,
dependency versions and source fingerprint. They are not a portable snapshot
interchange format. Restore verifies these and payload/prefix hashes first.

At capture, pending output is flushed into a prefix copy. Restored workers get
isolated copies and all active output paths are rebound. Changed-policy logs
begin at intervention; their baseline history remains in `inherited_history/`.
After jobs finish, the parent checks that original baseline outputs, snapshots,
and prefix hashes are unchanged.

## Policy intervention

The supported intervention changes acceptance/choice/reward/future-value/ranked
or native-rematch settings within the **same controller**. Policy construction
is validated before the full baseline is run. Existing plans, riders, active
physical execution, request/driver outcomes, draws, decline counts and relevant
choice ownership survive. The objective is replaced in both controller and
optimizer; cached utilities are invalidated for native recomputation. No past
leg is replayed and no incumbent booking is resampled. Each worker records the
models actually loaded in `window_state.json`.

Scope: the three single-operator baseline road controllers, BasicRequest,
ImmediateDecisionsSimulation/BatchOfferSimulation, Python NetworkBasic or
NetworkBasicWithStore, and single-worker Gurobi. Repositioning, C++ router state,
other controller swaps, fleet/search/capacity changes, initial-state scenarios,
other traveler models and CPLEX are rejected rather than silently approximated.
The wrapper is opt-in; it does not broaden the validated scope of any policy.

## Cohorts, cutoff and interpretation

A request belongs to exactly one cohort by **request time** in `[start,end)`.
Both policies restore the same baseline state and receive exactly that cohort.
They simulate the window plus cooldown, including normal dispatch of later
requests during a cooldown before the original simulation end. Beyond that end,
only physical fleet draining continues, as in the standard simulator. The
physical state is observed at the cutoff without admitting requests or running
dispatch at the excluded right endpoint. Only events strictly before the
cutoff enter metrics.

Each cohort request is `completed`, `rejected`, `accepted_censored`,
`picked_up_censored`, or `unresolved_censored`. The last three are reported
separately, not treated as terminal rejection. Waiting/ride/error means use
observed events and can be undefined (JSON null/CSV blank). Censored requests
can finish after the cutoff; completion here means completion **by this fixed
horizon**, not eventual service. `cohort_drivers.csv` credits completed cohort
trips and their gross fares to their actual serving drivers, including zero
rows for inactive drivers. It does not invent prorated operating costs or net
income. Prior full-day driver-accounting reports remain in the paired runner.

Every baseline window's observations must match the corresponding time-cutoff
projection of the complete baseline exactly. Arm identity and disjoint cohort
membership are checked before reporting success. Serial and parallel outputs
must match exactly in integration checks.

`seed_window_summary.csv` retains metrics by seed/window/arm.
`paired_window_comparison.csv` compares candidate minus baseline **across seeds
within each window**, using the existing paired statistics and explicit omitted
undefined pairs. Windows are not counted as independent seeds. Each candidate
window starts from **baseline history**; these local intervention effects are
not a continuous full-day candidate trajectory, and window results should not
be summed into that claim. Conditional waiting means can also refer to
different served populations.

## Records and validation

`manifest.json` records source/config/dependency fingerprints, seeds/windows,
worker commands/status/timing, snapshot identities, reference checks and report
hashes. `baselines/` holds full simulations, events, snapshot metadata/payloads,
prefixes and reference cohorts. `tasks/` holds each restored worker's job, log,
inherited history, actual-policy state, cohort/driver/physical-state outputs.

The implementation was checked first with live mid-run snapshots, then real
ranked/rematch smoke windows. End-to-end tests cover both insertion controllers,
native batch rematching, actual logit menus, future-value intervention on an
existing optimizer graph, ordinary full-baseline equivalence and exact replay
with one versus two workers. Unit checks cover closures/RNG/graph identity,
cohort boundaries/censoring, zero-service metrics, invalid swaps, subprocess
failure/cancellation and timeouts. Complete-suite and measured benchmark
results are retained in `docs/validation/phase6/`; the step and correction record
is in `docs/WORK_LOG.md`.

Snapshot/baseline overhead and hardware affect speed. The plan's handwritten
4× example is not an asserted result or a correctness criterion. Report measured
serial/parallel times alongside matching outputs.

The fixed-seed example measurements (three seeds, three windows, 18 restored
jobs per experiment) are:

| Policy comparison | Window jobs: 1 → 2 workers | Window speed ratio | Total including baseline/snapshots: 1 → 2 workers |
| --- | --- | --- | --- |
| Ranked insertion | 60.74s → 30.42s | 2.00× | 79.50s → 49.50s |
| Native rematch | 71.23s → 36.79s | 1.94× | 97.35s → 60.65s |
| Rematch with actual menus | 69.50s → 39.04s | 1.78× | 93.91s → 65.89s |

Total speed ratios are **1.43–1.61×**, including the unavoidable full baseline
and capture overhead. Regression/compatibility work also ran in this
environment, so these single timing observations are descriptive. Both summary
reports agree exactly between worker counts; the final audit also compares
individual cohort, credit, physical-state and vehicle-activity tables.

These dispatch interventions complete more requests by the horizon in all nine
case/windows, but their conditional observed-pickup waiting means also increase
in every case/window. With menus, mean censored requests in window 1 increase
from .67 to 1.33. Original per-seed outcomes and omitted/defined statistical
pairs remain in the reports. This demonstrates a usable comparison tool and
its tradeoff reporting; it does not establish a new calibrated policy gain.
