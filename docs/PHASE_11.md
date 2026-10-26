# Phase 11: native upstream fidelity and consolidated validation

This implements section 5, Validation, following AV Round 3 in the supplied plan.
The screenshot's historical test count and served totals are reference claims;
this phase measures the current fork against independently extracted upstream.
It improves the evidence and reproducibility of compatibility checks. It does
not change matching, repositioning, movement or feature defaults, and does not
claim an operational policy improvement.

The focused gate passes **14 tests**, including **12 complete physical runs**
across insertion, insertion-plus-batch and native Alonso-Mora controllers.
The full suite passes **403 tests** in **2521.73s**, covering
**269 complete regression simulations and 32 restored windows**. All **15 native
physical runs** pass (12 upstream/fork runs including six repeats, plus three
clean published-archive runs). All 257 historical complete cases preserve
**1548 byte-identical checked tables** and 128 exact window tables.

[Measured results](validation/phase11/RESULTS.md),
[complete evidence and restoration](validation/phase11/README.md), and
[the work log](WORK_LOG.md) retain all changes, intended benefits, actual outcomes,
failed launches, corrections, commands and source/input/output hashes.

## Independent reference

`python -m tools.native_fidelity` extracts a fresh `git archive` of upstream
`c813728b6d188df8dd7fd5d3d36dcb0a55c898a2`. The same neutral worker runs the
archive and the fork in separate processes. Every imported `src` module must
reside under the selected source tree. The reference imports no fork tools,
matching code, movement code, random-stream helpers or feature implementations.
Original tracked upstream files are hashed and must remain unchanged.

Both versions receive the same original scenario row, public native input
files, vehicle CSVs, configured clock and recorded adaptations. Actual initial
vehicle positions/SOC and full request identities must agree, as must observed
booking/rejection histories. One permitted CPU and one BLAS/OMP/MKL thread are
used; processes run sequentially within a profile.

For native C++ routing, all tracked upstream C++/Cython/header/setup inputs must
equal the installed source inputs before its exact hashed extension is added
to the extracted tree. No tracked Python or native source is replaced. The
loaded extension's path/hash is also recorded. This shares a verified native
runtime, rather than independently rebuilding it under a different compiler.
Python/package/platform versions remain part of the validation record.

## Native profiles and explicit adaptations

| Profile | Original window and inputs | Adaptations applied to both versions |
| --- | --- | --- |
| Munich | 06:00–09:00; `d_10_s_1.csv`, 50 vehicles; native AIMSUN graph | On-demand native C++ router because published partial tables are absent; repositioning off; wall-clock tree/solver cutoffs disabled |
| Chicago | 00:00–24:00; `2022-06-7_sample_10_0.csv`, 100 vehicles; native graph and provided traffic factors | Native preprocessed C++ router; repositioning off; wall-clock tree/solver cutoffs disabled |
| Manhattan | 00:00–24:00; `2018-11-12_sample_5_1.csv`, 80 vehicles; original matrix router/factors | Repositioning off; wall-clock tree/solver cutoffs disabled |

The batch matching strategy, native demand/fleet/objective/service settings and
source inputs remain the original selected scenario's values. Disabling tree
and solver timeouts removes the execution-load confound. These are explicitly
adapted no-repositioning profiles, not a claim that every unmodified city
configuration runs with the installed restricted Gurobi license. Earlier
unmodified repositioning failures remain documented. Assignment still uses the
installed Gurobi; no result is silently substituted from a different optimizer.

These are the original native city requests and default legacy request clocks,
not the rebuilt, causally admitted Phase 10 comparison cohorts. Manhattan here
is 2018, distinct from the Phase 10 November 2019 TLC cohort. Native pooling,
patience and fleet assumptions are retained for fidelity; these results are
not an empirical calibration or an AV policy effect.

## Physical and exact-output checks

The neutral worker observes original broker callbacks without changing their
return values. It requires unique/full demand, identical accepted and rejected
histories, every accepted pickup/dropoff completed, no terminally rejected
service, and no tasks/onboard riders after native final draining. Independent
inspection checks vehicle chronology, moving and pre/post-exchange capacity,
and actual passenger boarding/alighting identities against completed user rows.
Valid stationary event-union occupancy is counted explicitly; raw logs remain
unchanged. The final-state CSV is the native file and need not represent the
post-drain live state; both that CSV and actual post-drain state are checked.

The comparator requires every row, column, numeric value and missing value in
all four tables to agree exactly, including row order:

- `1_user-stats.csv`
- `2-0_op-stats.csv`
- `standard_eval.csv`
- `final_state.csv`

Byte identity is measured separately. With `--repeats 2`, upstream and fork
each run again in fresh processes and require byte-identical tables against
their own first run. No approved baseline is overwritten or silently accepted.
Adversarial tests reject tiny numeric drift, missing/duplicate rows, missing
values, extra columns, vehicle-input drift, source escapes, unsafe/duplicate
profiles and activation of a new feature through compatibility overrides.

## Reproduce

The public sources and checksums are already available from the Phase 10 data
records. Edit only `data_root` paths in a copy of
[`fidelity/profiles.json`](fidelity/profiles.json) to use another local layout.
Both sources must use those same public files. Output must be a fresh directory
outside the repository; the tool refuses existing destinations.

```bash
.venv/bin/python -m tools.native_fidelity \
  --profiles docs/fidelity/profiles.json \
  --repeats 2 --timeout 7200 \
  --output /workspace/native_fidelity_results

.venv/bin/python -m pytest -q
```

`manifest.json` retains source/configuration/input/output/runtime hashes,
exact commands, CPU/thread settings, statuses, measured timings and comparisons.
If a process, physical audit or equality check fails, the study remains failed
with its existing raw records. An interrupted or uncollected run is never
counted as a successful comparison.

Cross-city demand-based AV repositioning, sparse native references, empirical
patience/adoption/speed identification, daily AV throughput and the Chicago
non-monotone policy mechanism remain separate follow-ups. The complete earlier
policy findings and limitations remain in [Phase 10](PHASE_10.md).


## Measured compatibility and validation benefit

Native upstream and fork complete exactly **617/1788 Munich**, **5106/12753
Chicago** and **5399/10700 Manhattan** requests in the declared profiles.
Every accepted booking completes; lower overall completion records rejected
requests, not silently unfinished accepted service. All 6 upstream/fork pairs
match 24 full tables byte for byte, source repeats match another 24 comparisons,
and the clean published archive matches 12 further tables. Full demand, actual
initial geometry/SOC, booking/rejection histories, all rider/vehicle/evaluation/
final-state cells, source isolation and physical state are checked.

The clean artifact is a fresh archive of published Phase10 receipt
`bccbad4bb179f48ba2fa2a53682d3d90f33c3cc3`. All 254 simulator/dependency files
match Phase11 exactly; Phase11 adds only four validation-tool/test Python files.
Every simulator import resolves inside the clean archive. This tests the same
unchanged simulator implementation outside the working checkout. It shares the
explicitly verified native extension/runtime, not a separately compiled binary.

The improvement is broader independent coverage and reproducibility. No dispatch
policy or completed-trip count is improved in these parity runs. Native route
warnings are preserved and counted; actual physical completion is independently
verified. The original scenario adaptations and historical screenshot-number
limits remain explicit. Existing Phase10 gains and regressions are unchanged.
