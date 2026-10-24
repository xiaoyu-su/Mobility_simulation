# Phase 5c verification evidence

Final complete suite: **240 passed, 0 failed, 0 skipped in 1039.69s**.
The **76** regression/integration cases execute **151** complete simulations;
**164** unit cases include actual small native Gurobi graph/constraint problems.
Three additional controlled comparisons complete **18** simulations and
**nine matched input pairs**. All **169 final-source runs** were independently
audited after completion.

The source fingerprint stayed unchanged throughout the full suite/comparisons:
`ecd18b9476dcd7bbd56ba17def85723e502bfa26d05b74c00e31f9d7499e3b23`.
Recorded Git HEAD is the development parent; file hashes include the
then-uncommitted implementation/tests. This is original test provenance,
not a claim that the parent commit alone contains the implementation.

## Measured controlled outcomes

Seeds are 0/1/2, noise sigma is 0.3, and each run records all 100 requests.
Within each pair, only the scenario name and rematch flag differ. The driver
classes, retry allowance, objective/menu/future parameters, network, demand,
and initial fleet are matched. All accepted bookings complete.

| Configuration | Mean completed: control → rematch | Mean served-rider wait: control → rematch |
| --- | --- | --- |
| Standard batch | 54.67 → 77.33 | 125.02s → 151.18s |
| Actual logit menus | 53.00 → 78.67 | 136.30s → 157.00s |
| Future-value scoring | 52.67 → 76.67 | 107.79s → 149.83s |

These are small-example service gains with longer conditional waits, not
calibrated marketplace/city-scale claims. Original reports retain seed values,
uncertainty estimates, genuine offer counts, and other metrics.

Six standard/menu controls match **24** saved Phase 5 tables exactly. The
current suite's **22** ranked-fallback runs also match **115** archived Phase 5b
tables exactly, covering existing acceptance, choice, insertion, periodic batch,
noise, future value, and ranked dispatch behavior.

## Evidence files

- `validation.json`: final source, counts, outcomes, scope, and artifact hashes.
- `source.json`, `command.txt`, `pytest.txt`, `junit.xml`: exact snapshot,
  invocation, complete console output, and per-case results.
- `run_checks.json`: all 169 run audits and output SHA-256 hashes. Checks cover
  complete/unique demand, final state, evaluation, completed pickups/bookings,
  absent service for terminally rejected riders, and chronological accounting.
  Active rematch runs also check unique request/driver pairs, genuine consecutive
  attempts, exactly one final terminal refusal for unassigned offered requests,
  agreement of attempt/event logs, recovered/counter totals, solver-pass counts,
  and the one-new-item-per-driver-per-round rule for logit menus.
- `comparison-audit.json`: final comparison audits and six historical controls.
- `phase5b-compatibility.json`: 22 ranked-run historical comparisons and their
  exact file lists.
- Checkpoint `.txt` files preserve initial failures and corrections: implicit
  solver default, optional-field test-double compatibility, and the intentionally
  empty weighted-zero-offer case. The corrected focused suite and fresh-process
  replay pass; earlier failures are not overwritten or counted as final successes.
- `simulation_records.tar.gz`: **2,544** regular files, all read back and
  hash-verified against their originals. `suite/` contains all 76 complete-run
  case directories and 151 simulations; `comparisons/` contains complete saved
  configs, commands, worker logs, outputs, manifests, and reports for all three
  comparisons. `checkpoints/` separately preserves the failed initialization and
  first corrected legacy-initialization smoke. Neither checkpoint is counted
  among the 169 final-source runs.

Empty decision/operator-evaluation tables are valid in weighted probability-zero
cases where the optimizer makes no offers. The separate unweighted always-refuse
scenario forces real proposals and verifies graph removal and final rejection.
Both retain complete demand and driver accounting.

## Reproduction and scope

```bash
.venv/bin/python -m pytest -q
```

Run from the repository root. Comparison commands and assumptions are in
[PHASE_5C.md](../../PHASE_5C.md), and exact final commands are also preserved in
the archive's `comparisons/` directory. Original absolute temporary paths are
provenance; rerunning creates new isolated destinations.

Validated enabled scope: one simulation worker, pure Alonso-Mora/Gurobi batch
matching, BasicRequest, retained heuristic-filtered feasible trips, instantaneous
decisions, driver classes, menus, future value, and travel noise. Costs and
first-offer decisions are frozen; accepted pairs are required during re-solving.
No manual fallback plans, replayed vehicle updates, or extended rider patience
are used. [WORK_LOG.md](../../WORK_LOG.md) records all changes, corrections,
benefits/tradeoffs, checks, and publication.
