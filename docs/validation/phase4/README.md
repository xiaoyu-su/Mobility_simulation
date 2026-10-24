# Phase 4 validation evidence

- `validation.json`, `pytest.txt`: final verification outcome and evidence hashes.
- `run_checks.json`: 12 actual simulation outcomes, principal-output hashes,
  accepted/completed checks, and exact comparisons of six control runs against
  the saved Phase 3 rider, evaluation, and driver-decision tables.
- `insertion/` and `batch-classes/`: actual paired manifests, reports, configuration
  snapshots, evaluator console output, and complete raw run CSV/JSON records.
  Both experiments use seeds 0/1/2, sigma 0.3, and matched acceptance assumptions.
- Each `runs/seed_N/{baseline,candidate}/` preserves rider/vehicle records, driver
  decisions, final states, input/class audits, and console/simulation logs.
  Candidates also preserve selected future values, alternatives, and final counters.
- `benchmark.json`: independent full-scan versus cached exact-top-k scores on
  real example roads, with source/network/workload hashes, query counts, and times.
- `benchmark-console.txt.gz`: complete benchmark stdout/stderr, including existing
  router warnings for disconnected routes. Read with `gzip -dc`.
- `checkpoints/`: actual starting, focused, full-example, and paired test logs.

Neither final example improves served-trip counts: insertion means
44.67 → 42.67 and batch means 76.33 → 71.67. Future value is an optimistic
matching estimate; actual alternative-driver dispatch is a later phase.
Every accepted booking completed, but lower conditional waits among served
riders do not establish policy improvement when fewer requests complete.

The benchmark's 1,920 scores agree within 1.11e-16; routing calls reduce from
59,520 to 348. Wall times 93.374s → 1.464s are descriptive and affected by the
router's repeated disconnected-route handling. This is not a full-simulation
or city-scale speedup claim.

Original run directories remain at `/workspace/.setup/phase4/verified-insertion`
and `/workspace/.setup/phase4/verified-batch-classes`; archived provenance retains
those original paths. Model assumptions, parameters, and reproduction commands
are in `docs/PHASE_4.md`; full work and commit/publication records are in
`docs/WORK_LOG.md`.
