# Phase 11 native fidelity results

The frozen source is `d05aa8b2c2bcf7892e20d3016d7c05d8b3993c0ecb99fce8ca27417b716d1caa` across258 Python/dependency files.
All15 native physical runs pass:12 upstream/fork runs (six original source/city
conditions plus six fresh-process repeats) and three clean published-archive
runs. The three bundled controllers also pass in the focused and full-suite
validation; their synthetic cases are counted separately from these native runs.

| City | Original clock | Fleet | Unique requests | Completed, upstream = fork | Completion |
| --- | --- | --- | --- | --- | --- |
| munich | 21600–32400s | 50 | 1788 | 617 | 34.51% |
| chicago | 0–86400s | 100 | 12753 | 5106 | 40.04% |
| manhattan | 0–86400s | 80 | 10700 | 5399 | 50.46% |

All six upstream/fork pairs match **24 complete output tables byte for byte**;
fresh-process source repeats match another24 table comparisons. The clean
published archive matches12 additional full tables. These include every rider,
every vehicle leg, every standard evaluation row and every native final-state
cell; no column, row or missing-value difference is normalized away.

Actual initial geometry/SOC, demand identities and booking/rejection histories
match. Every accepted rider is physically picked up and dropped off; no terminally
rejected rider is served. Vehicle chronology, actual capacity before/after stops
and while moving, boarding/alighting identities and live post-drain state pass.
All raw/source/input/runtime hashes are independently read back and verified.
Native original warnings, including shared upstream route warnings, remain in
`native_warnings.json` and raw logs; equality is not a claim that upstream has no
warning paths. Actual booking completion and final state are independently checked.

## What improved

The baseline regression previously checked two output tables for each of three
bundled matching examples. This gate adds complete four-table comparisons,
per-source fresh-process repeatability, actual simulator import isolation,
vehicle/native-runtime/input identity, and three full native city profiles.
Coverage expands beyond small bundled fixtures; no approved baseline is updated.
The improvement is the breadth and reproducibility of validation. The policies,
served totals and physical behavior are intentionally unchanged in these profiles.

## Interpretation and limits

These native no-repositioning profiles use their original demand, fleet, clock,
batch matching and service assumptions. C++ routing adaptations and disabled
wall-clock tree/solver timeouts apply equally to both versions and are recorded
before outcomes. They do not prove that every unmodified original configuration
runs with the restricted Gurobi license. The loader's legacy request-clock behavior
is preserved for fidelity; this is not a new causal demand-admission calibration.
Manhattan uses the native2018 sample, unlike Phase10's2019 cohort. Therefore
neither completion levels nor served counts are a direct Phase10 policy gain,
a field target or reproduction of the screenshot's historical numbers.

The clean artifact is a fresh archive of the published Phase10 receipt
`bccbad4bb179f48ba2fa2a53682d3d90f33c3cc3`. Every one of its254 simulator/dependency
files equals the Phase11 working source; the four additional Phase11 Python
files are this validation harness and its tests. No simulator implementation is
substituted from the working checkout; all actual imports resolve inside the
extracted archive. The native runtime is shared only after tracked C++/Cython/
setup source identity and exact binary hashes are proved. This is a verified
shared runtime, not an independently compiled binary/toolchain experiment.

Full regression totals and historical table identity are recorded separately
in `validation.json`, `suite-integrity.json` and `historical-identity.json`.
Per-city AV repositioning, causal policy mechanisms, empirical patience/adoption
identification and daily AV throughput remain follow-ups, as already documented.
