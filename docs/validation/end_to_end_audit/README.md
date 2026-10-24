# End-to-end validation audit for completed Phases 0–5

Every completed phase has successful complete-simulation evidence. This audit
also reran the entire current suite against the combined Phase 5 source:
**181 passed, 0 failed, 0 skipped, in 616.97 seconds**.

| Completed phase | Historical passing tests | Final recorded simulation experiment |
| --- | ---: | --- |
| 0: baseline hygiene | 8 | Three independently captured upstream controller examples; 100 requests and 93 completed rides in each |
| 1: independent randomness and paired evaluation | 41 | Six runs, three matched seed pairs |
| 2: execution noise and promises | 66 | Twelve runs covering zero and positive noise |
| 3: driver acceptance and classes | 107 | Twelve insertion/batch-class runs with noise |
| 4: future-value reward | 145 | Twelve insertion/batch-class runs with noise |
| 5: driver choice | 181 | Twelve singleton/batch-menu runs with noise |

Historical test counts are cumulative phase checkpoints. The experiment counts
exclude additional complete simulations inside those test suites and earlier
development checkpoints. All **587** files covered by the Phase 1–5 validation
hash maps matched their saved hashes. All nine approved upstream input/config
hashes are unchanged. See `historical-audit.json` and the original sibling
`phase1` through `phase5` directories for the underlying records.

## Fresh combined-source verification

The new suite contains **48 end-to-end regression/integration test cases** and
**133 unit cases**. Those end-to-end cases completed **96 simulations**, each
loading all 100 bundled requests over the 7,200-second horizon and draining
pending accepted service as required. Thirteen paired experiments validated
**26 matched input pairs**. The audited source digest matches the previously
tested Phase 5 Python source exactly.

The checks exercise insertion, immediate/batch, and batch matching; default
compatibility; independent random streams and fresh-process replay; zero and
positive execution noise; promised versus actual timing; always-accept,
always-decline, logistic decisions and driver classes; future-value scoring and
zero-fallback compatibility; singleton menus and retries; actual multi-item
menus; and menus combined with future value and execution noise.

An additional output audit checked every run for complete/unique demand
records, final state, evaluation output, valid chronological driver accounting,
and completion of every picked-up rider. Where acceptance is enabled, accepted
requests exactly match completed requests, with no duplicate acceptance or
terminally declined request served. Choice counters agree with decision rows.

Three intentional always-decline boundary runs serve nobody. The upstream
operator-grouped standard evaluator emits no operator metric rows in that
case; demand, acceptance, and driver accounting still verify zero service.
An initial post-suite audit incorrectly required every evaluation table to be
nonempty. It was corrected to distinguish this boundary from missing output;
no simulation source or tests changed. `audit-checkpoint.txt` preserves that
correction.

## Evidence and reproduction

- `pytest.txt` and `junit.xml`: actual complete test result and per-case timing.
- `command.txt`: exact command, including unique output destinations.
- `run_checks.json`: all 96 run checks, enabled settings, counters, and original
  output-file SHA-256 hashes.
- `validation.json`: source fingerprint, counts, scope, and artifact hashes.
- `simulation_records.tar.gz`: complete raw files from the 48 end-to-end case
  directories, including all 96 simulations and their configs, logs, decisions,
  evaluations, paired manifests, and reports. All **1,311** archived regular
  files were read back and checked against their original hashes.

From the repository root, reproduce the full gate with:

```bash
.venv/bin/python -m pytest -q
```

Raw records preserve original temporary paths for provenance. Those paths are
not portable runtime dependencies; rerunning the suite creates fresh isolated
directories. The existing uncompressed run path is in `validation.json`.

## Ongoing requirement and limits

[AGENTS.md](../../../AGENTS.md) now requires a real affected simulation after
each simulation behavior/configuration change, explicit output checks,
relevant feature combinations, and the complete suite before phase completion.
[WORK_LOG.md](../../WORK_LOG.md) records changes, reasons, results, and fixes.

This validates the bundled small scenarios with one simulation worker. It does
not establish city-scale performance, calibrated driver behavior, or a service
improvement. Competing-driver conflict resolution has separate unit coverage:
the current live solver gives each request one owner, so the simulated menus do
not create cross-driver conflicts. Later phases remain unimplemented and are
not covered by a claim of completion.
