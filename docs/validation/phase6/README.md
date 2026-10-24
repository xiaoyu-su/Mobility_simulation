# Phase 6 verification evidence

Final complete suite: **270 passed, 0 failed, 0 skipped in 1243.77s**.
The 80 regression/integration cases execute **163 complete simulations** and
**32 restored window continuations**. There are 190 unit cases.

Six additional timing experiments execute **18 full baselines +108 windows**.
A plain-router/acceptance-disabled/no-noise/no-cooldown check adds **one full
baseline +four windows**. Total final-source evidence: **182 complete
simulations and 144 bounded restored windows**, kept separate because windows
intentionally report unfinished observations. Every full simulation accounts
for all 100 requests, finishes accepted bookings and validates chronological
driver/vehicle accounting. Window output audits check identity, cohorts,
censoring, actual policy flags, completed-fare attribution and vehicle activity.

All **72 snapshot pairs** validate the baseline window against the corresponding
projection of the complete baseline. Both arms restore the same payload, and
every configured request belongs to exactly one cohort per arm. Original
baseline/snapshot/prefix files remain unchanged after worker execution.

All **151** corresponding prior-phase full simulations match **849** saved
rider/evaluation/physical/decision tables exactly. All **208** pre-existing
Python/dependency source files and **nine** approved original input/configuration
hashes are unchanged. The ordinary three upstream example regressions pass.

Final source fingerprint:
`c417e89db72c1dc66ccd110047494f332635f04074601d965918d4e92dbb9249`.
Source and Git HEAD stayed fixed during final execution. Recorded HEAD is the
development parent; file fingerprints include the then-uncommitted new tool
and tests. Publication changes the Git commit, not these tested Python bytes.

## Measurements

Seeds 0/1/2, sigma .3, request windows `[0,2400)`, `[2400,4800)`, `[4800,7200)`,
each with 300 seconds of cooldown. Within each comparison only scenario name
and the ranked/rematch flag differ. Both reports and **72** individual output
tables per configuration match exactly between one and two workers.

| Configuration | Window task time: 1 → 2 workers | Task speed ratio | Total time: 1 → 2 workers | Total speed ratio |
| --- | --- | --- | --- | --- |
| Ranked insertion | 60.74s → 30.42s | 2.00× | 79.50s → 49.50s | 1.61× |
| Native rematch | 71.23s → 36.79s | 1.94× | 97.35s → 60.65s | 1.60× |
| Rematch with actual menus | 69.50s → 39.04s | 1.78× | 93.91s → 65.89s | 1.43× |

Total time includes full baselines and snapshots. These are single measured
timing runs in this environment while regression/compatibility work also ran;
they are not a guaranteed speedup or the plan's handwritten 4× example.

The following are means across three seeds within each window:

| Configuration | Window | Completed by cutoff: control → candidate | Observed pickup wait: control → candidate |
| --- | --- | --- | --- |
| Ranked insertion | 0 | 13.67 → 23.00 | 122.89s → 145.99s |
| Ranked insertion | 1 | 15.67 → 23.33 | 128.33s → 134.55s |
| Ranked insertion | 2 | 14.00 → 24.00 | 103.42s → 134.71s |
| Native rematch | 0 | 16.00 → 25.00 | 127.54s → 160.58s |
| Native rematch | 1 | 18.33 → 26.67 | 124.17s → 150.10s |
| Native rematch | 2 | 19.33 → 26.67 | 128.08s → 152.65s |
| Rematch with menus | 0 | 14.00 → 25.33 | 134.43s → 155.44s |
| Rematch with menus | 1 | 19.67 → 24.33 | 143.98s → 147.65s |
| Rematch with menus | 2 | 18.00 → 26.00 | 135.39s → 154.39s |

Higher conditional waits accompany increased horizon completions. Menu window
1 also increases mean censored requests from .67 to 1.33. Reports retain all
seed outcomes, censor counts and paired inference. Each candidate window begins
with baseline history, so these local outcomes are not a full-day candidate
trajectory. Do not treat windows as independent seeds or sum this table into
that claim. Coefficients/data remain illustrative bundled examples.

## Files and reproduction

- `validation.json`: counts, source fingerprint, measured timings/outcomes,
  experiment summaries, scope and artifact hashes.
- `source.json`, `command.txt`, `pytest.txt`, `junit.xml`: original source
  snapshot, exact invocation, complete console and case-level results.
- `run_checks.json`: all 182 full-run and 144 window audits, actual loaded
  policy flags, statuses, snapshot identities and individual output hashes.
- `historical_compatibility.json`: all 151 prior-phase comparisons and their
  849 exact table matches.
- Three `*-seed_window_summary.csv` and `*-paired_window_comparison.csv` pairs:
  original parallel-run reports, verified equal to serial reports.
- `archive_index.json`: original path/hash for every regular archived file,
  read back and checked against the source bytes after compression.
  **10,820 regular files** verify: 3,833 suite, 4,057 benchmark/recorder and
  2,930 checkpoint files.
- `suite_records.tar.gz`: complete final suite's raw outputs, fixtures,
  full baselines, snapshots/prefixes, restored states, jobs, manifests and logs.
- `benchmark_records.tar.gz`: six timing experiments and the separate router
  compatibility case, including full raw states, configs, commands, reports and
  worker logs. Original recording/audit/archive scripts are included inside the
  archive, without changing tested Python source after the freeze.
- `checkpoint_records.tar.gz` and checkpoint console/XML files: graph-pickle
  failures and correction probes, early smoke windows, pre-correction timing
  experiments, and the interrupted first full suite. The three-seed rematch
  experiment correctly fails its immutable-log gate; parent initialization was
  appending warnings to the previous seed's log. The fix and targeted test are
  recorded in `corrected-logging.txt` and `docs/WORK_LOG.md`. These checkpoints
  are excluded from final counts. Some original absolute metadata paths predate
  relocation into checkpoint folders and remain unmodified provenance.
- `final-audit-selection-error.txt`: first standalone recorder counted only
  runs with `random_streams.json`, inadvertently excluding 75 valid legacy-mode
  controls. Corrected the external audit to check all full outputs, using the
  stream audit when present. This changed no tested simulation/tool source;
  the corrected independent audit passes for all 182 runs in `final-audit.txt`.

Run the repository's full gate with `.venv/bin/python -m pytest -q`.
Window CLI commands, model limits, cutoff semantics and interpretation are in
[PHASE_6.md](../../PHASE_6.md). Pickles are trusted local full-state artifacts
for the recorded source/interpreter/dependency versions; rerun baselines for a
new environment. Original absolute paths document this cloud execution.
