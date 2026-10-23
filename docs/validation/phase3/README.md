# Phase 3 validation evidence

This archive contains actual outputs from the final insertion and heterogeneous
driver-class batch experiments. Both use seeds 0/1/2 and common execution-noise
sigma 0.3; the supplied acceptance coefficients/shares are illustrative.

- `validation.json` and `pytest.txt`: final verification outcome and hashes.
- `run_checks.json`: return codes, request/completion counts, acceptance checks,
  and principal-output hashes for all 12 simulations.
- `insertion/` and `batch-classes/`: actual source/config/input manifests, paired
  reports, configuration snapshots, and evaluator console output.
- Each experiment's `runs/seed_N/{baseline,candidate}/`: complete raw CSV/JSON
  records, rider/vehicle activity, final states, audits, and console/simulation
  logs. Enabled candidates also contain every driver decision and class audit.
- `checkpoints/`: development failures and corrected-checkpoint logs, including
  the optimizer lifecycle and YAML scenario integration issues recorded in the
  work log.

The original artifacts remain at `/workspace/.setup/phase3/verified-insertion`
and `/workspace/.setup/phase3/verified-batch-classes`. Archived copies retain
the original paths in their configuration/manifest provenance. The actual
commands and hashes identify the runs even if that environment is replaced.

All final paired input audits matched; every booked/accepted rider completed.
Decline counts include repeated attempts. A lower mean wait among served riders
does not establish improvement when fewer requests are served. These small
development experiments verify the implementation and reporting pipeline;
they are not city calibration or a general policy result.

Model assumptions, units, examples, and commands: `docs/PHASE_3.md`.
Changes, corrections, verification, and GitHub publication: `docs/WORK_LOG.md`.
