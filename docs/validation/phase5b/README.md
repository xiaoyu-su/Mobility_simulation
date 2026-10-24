# Phase 5b verification evidence

Final complete suite: **213 passed, 0 failed, 0 skipped in 818.86s**.
The **64** regression/integration cases completed **126** real simulations;
**149** unit cases check individual invariants and boundaries. Three additional
controlled comparisons completed **18** simulations and **nine matched input
pairs**. All **144 final-source runs** were independently audited after testing.

The source stayed unchanged throughout the final suite and comparisons:
`7dc26b80c54bc239a727b4da04762dc66c4d48caaf901746c7ced12b47d641a1`.
Recorded Git HEAD is the parent used during development; file hashes include
the then-uncommitted implementation and tests. Preserve this original provenance
rather than replacing it with a later publication commit.

## Controlled outcomes

Both arms use identical settings except scenario name and the fallback flag.
Seeds are 0/1/2, execution noise sigma is 0.3, and each run processes all 100
bundled requests. Every accepted booking completes; terminally declined riders
are not served. Driver accounting and output chronology validate for all runs.

| Experiment | Mean completed: control → fallback | Mean served-rider wait: control → fallback |
| --- | --- | --- |
| Insertion | 44.67 → 70.33 | 118.61s → 149.66s |
| Immediate insertion + batch reoptimization | 49.67 → 71.67 | 113.46s → 107.07s |
| Future-value insertion | 42.67 → 69.67 | 107.85s → 153.28s |

The measurements demonstrate more completions in these examples, with longer
conditional waits in two configurations. They are not calibrated marketplace
estimates or a city-scale claim. Six historical control runs also match saved
Phase 4/5 artifacts exactly across **24** output tables.

## Files

- `validation.json`: source, test counts, measured metrics, scope, artifact hashes.
- `source.json`, `command.txt`, `pytest.txt`, `junit.xml`: original final-source
  snapshot, exact invocation, full console result, and individual test records.
- `run_checks.json`: checks and output hashes for all 144 final-source runs.
  Active ranked runs also validate unique driver offers, consecutive ranks,
  sorted candidate costs, stop-on-acceptance, exhaustion-only terminal refusal,
  counters, and agreement between ranked/acceptance logs.
- `comparison-audit.json`: the 18 final comparisons and six exact historical
  control comparisons.
- `initial-unit.txt`, `ranked-checkpoint.txt`, `replay-checkpoint.txt`, and
  `smoke-insertion.txt`: development checkpoints. Deliberate focused-test
  deselection is distinct from skipping in the final complete suite.
- `simulation_records.tar.gz`: **2,165** regular files, all read back and checked
  against original hashes. `suite/` preserves the 64 end-to-end test directories
  and 126 simulations; `comparisons/` preserves all three complete experiments,
  worker logs, saved configs, raw outputs, reports, commands, and audits;
  `checkpoints/smoke-insertion/` preserves the first smoke separately. That
  earlier smoke is not counted among the 144 final-source runs.

The always-decline boundary cases correctly have zero service and no operator
rows in the upstream standard evaluation. Their complete demand/decision/driver
accounting still validates. Raw records preserve original paths for provenance;
reproducing the commands creates new isolated destinations.

## Reproduction and scope

From the repository root:

```bash
.venv/bin/python -m pytest -q
```

Controlled comparison commands and assumptions are in
[PHASE_5B.md](../../PHASE_5B.md); the exact final commands are also inside the
compressed `comparisons/` records. [WORK_LOG.md](../../WORK_LOG.md) documents the
changes, reasons, intended benefits, checkpoints, outcomes, and corrections.

Validated scope: bundled small single-worker scenarios, both immediate insertion
controllers, zero/positive noise, driver classes, optional singleton choice,
future-value combinations, probability boundaries, exact disabled behavior,
and deterministic replay. Candidate heuristics remain in force; driver responses
are instantaneous, each retained driver is offered once, and only the winner's
plan executes. Alonso-Mora forbid/rematch remains Phase 5c.
