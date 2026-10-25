# Real Manhattan investigation evidence

This record supplements the original fixture validation in `../phase7/`.
Real-data calibration remains incomplete. See
[`../../REAL_MANHATTAN_INVESTIGATION.md`](../../REAL_MANHATTAN_INVESTIGATION.md)
for findings, definitions, actual trade-offs and outstanding production fixes.

## Read the results

- `validation.json` and `run_inventory.json`: actual successful/failed attempts,
  complete validated policy pairs and the explicitly unrun arm of the failed
  original dynamic setup. The observer replay is counted separately.
- `cohort_diagnostics.csv`: independent fixed-cohort results for every completed
  arm, including an individual successful arm of an unsuccessful pair. Check
  `pair_status` before treating rows as a complete policy comparison.
- `wait_quantiles.csv`, `timebin_diagnostics.csv`: distributions and half-hour
  cohorts. Waits use the actual source request clock; negatives are retained.
- `results_table.md`: readable full completed-arm table. `policy_effects.csv`
  compares complete policy pairs, includes the common-served cohort and
  improved/worsened/unchanged counts, and preserves whole-run modeled costs.
  Marginal-median differences are not median individual improvements.
- `source_context.json`, `training_supply_carry_in.csv`: source event coverage,
  pooling, training-only curb/noise diagnostics and historical carry-in.
- `integrity.json`: unique/full demand, accepted completion, chronological
  vehicle activity, route capacity, boarding-event alignment, fixed cohort IDs,
  actual repositioning orders/legs, early-service counts and raw output hashes.
- `failed_leg_continuation.json`, `observer_replay_identity.json`: the finite
  tail-cutoff diagnosis and exact replay identity. Isolated continuation does
  **not** count as a successful policy simulation.
- `calibration_diagnostics.svg`/`.png`: exportable median-error and completion
  figures, one seed. These are diagnostics, not confidence bounds or evidence
  of policy superiority.
- `evidence.tar.xz`, `archive_index.json`: complete raw simulation outputs,
  original and failed logs/manifests, private input files, source-row cohorts,
  source context caches, provenance, preparation/runner/analysis scripts and
  frozen simulator source. Every archived regular file was independently read
  back and SHA256-checked against its original.

The original CLI calibration report subtracts the discretized simulation
request time, compares boarding start to TLC passenger pickup and includes
warm-up requests in its all-request aggregate. Those original reports are
preserved as evidence. Use the independent diagnostics for the corrected
07:00–10:00 cohort and event definitions. Arrival comparisons use exactly the
served source IDs with valid on-scene records. Completion is relative to
recorded completed trips; it is not an observed marketplace acceptance rate.

## Reproduce

The simulator source digest is
`d0dd474cef8aae0ccbd1f5c94008788b02648efb523a167c3bbe11c1722f84da`.
Source and Git HEAD remained frozen throughout the runs. No production Python
changed during this investigation. The previous 310-test regression gate has
this same source digest; it was not rerun for data/documentation-only changes.

1. Use the pinned environment (`environment.yml`, `requirements-dev.txt`),
   including Python 3.10.22, PyArrow 19.0.1 and the archived dependency versions.
2. Read the archive index, then extract `evidence.tar.xz` under `/workspace`.
   Its `market_inputs/`, `market_results/` and `.setup/phase7-investigation/`
   paths preserve the original commands and records. `frozen_source/` is an
   independent source snapshot, not an overlay on the working repository.
3. The unchanged public matrix binaries are omitted to avoid duplicating large
   downloads in Git. Download the Manhattan archive using the archived
   `download_manifest.json`, verify its SHA256 and published MD5, extract it,
   and restore its exact `nn_fastest_tt.npy` and `nn_fastest_distance.npy`
   files into each private bundle's `network/ff/tables/`. Use the filenames
   and expected hashes in `archive_index.json`; both matrix hashes are also
   verified by the ordinary bundle guard. The full raw TLC Parquet and public
   network ZIP are available from their recorded URLs and are not in Git.
4. The archived private bundles are ready to run after matrix restoration. For
   example, use a **new** output directory to preserve original results:

   ```bash
   PYTHONHASHSEED=0 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
     .venv/bin/python -u -m tools.synthetic_market run \
     --bundle /workspace/market_inputs/ablation_bundles/uniform_clock_1s \
     --seeds 0 --timeout 3600 \
     --output /workspace/market_results/reproductions/uniform_clock_1s
   ```

   Every case uses this command pattern. Per-case command JSON, original
   manifests, runner console logs and full worker commands are archived.
5. Input derivations are in `prepare_variants.py`, `ablation_lib.py`,
   `prepare_context.py`, `prepare_ceil.py`, `prepare_curb.py`,
   `prepare_curb_exact.py` and `prepare_typed_depots.py`. They refuse to
   overwrite an existing bundle. `rebuild_cache.py` reconstructs the sampled
   full-day source rows and extra event/flag records from the original Parquet.
6. `analyze.py`, `context_diagnostics.py`, `plot_results.py`,
   `policy_effects.py`, `make_table.py`, `debug_completion.py`,
   `continue_failed_leg.py` and `archive_evidence.py`
   contain the recorded diagnostics and verification. The original analysis
   targets the archived original output layout; point a copy at a reproduction
   layout when independently analyzing a rerun. Keep the original scripts and
   outputs intact for provenance.

## Data attribution

NYC TLC supplies the November 2019 high-volume trip records and official taxi
zone lookup at the public URLs in `download_manifest.json`.

Road/zone data: Roman Engelhardt and Florian Dandl, Technical University of
Munich, *FleetPy: Input Data for Manhattan Case Study*, April 10, 2025,
[doi:10.5281/zenodo.15187906](https://doi.org/10.5281/zenodo.15187906),
**CC BY 4.0**. Original metadata is archived in `zenodo_record.json`.
Derived bundles adapt internal zone IDs to TLC IDs, choose representative road
nodes, impute trip/initial positions and add fitted traffic factors; these
changes are recorded explicitly. Original matrices remain byte-identical.
FleetPy simulator source retains its original MIT license in the source archive.
