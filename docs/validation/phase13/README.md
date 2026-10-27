# Phase 13 validation evidence

All final gates pass: **433 tests**, **324 complete regression simulations**,
**32 restored windows** and **64 real physical runs**. The latter are
**54 unique conditions and ten exact fresh-process replays**. All 306 previous
full cases preserve 2234 checked tables byte for byte, with 128 exact window
tables. All 23 matched historical real controls preserve
195 critical file comparisons.

Read [the phase guide](../../PHASE_13.md), [main results](RESULTS.md),
[same-request and overlap supplement](REQUEST_COMPOSITION.md), and
[step-by-step work log](../../WORK_LOG.md). This phase improves diagnostics;
all 261 earlier Python/dependency files and existing policies are unchanged.

## Evidence and definitions

- `validation.json`, `full-suite.txt`, `junit.xml`, `suite-integrity.json`,
  `historical-identity.json`: actual full-run/window accounting and old-output
  comparisons. Original upstream outputs without promise fields are explicitly
  unavailable; picked-up bookings still require actual dropoff.
- `source_record.json`: all 265 tested source/dependency SHA-256 values,
  digest `cb250f100fdc138d8d2dbc10a55f1190f8fb4d601e8c99f744c5322c06b7a944`. Publication binds exact dirty-candidate bytes
  to a committed and remote-verified implementation; no input is source-retagged.
- `main_manifest.json`, `supply_manifest.json`, `pilot100_manifest.json`,
  `pilot200_manifest.json`: exact commands, seeds, pinned CPUs/one BLAS/OMP/MKL
  thread, statuses, timings, input/source/output hashes and 56 background checks.
- `manifest.json`: original reusable mechanism-report manifest for 54 unique
  conditions /60 accounting contrasts. Its listed file bytes remain unchanged.
  `pilot_accounting_manifest.json` records the ten-pilot physical/accounting gate.
- `independent_checks.json`, `independent_sweep_results.csv`: all 64 raw physical,
  type-factor, booking, privacy, service, capacity, chronology, initialization
  and independent event-sweep checks; ten exact replay file comparisons.
- `historical_real_identity.json`: all 23 old physical controls and exact files.
- `seed_accounting.csv`, `configuration_accounting.csv`, `paired_accounting.csv`:
  every seed/policy, exact count/duration interaction and service/window/overlap
  corrections. Higher utilization is not automatically more completed service.
- `request_mechanisms.csv`, `product_transitions.csv`, `time_bins.csv`: all
  request IDs/outcomes, nine product transitions, same-served waits, clock and
  retained-candidate diagnostics. Decision events are not unique passengers.
- `request_composition_seed.csv`, `request_composition_summary.csv`,
  `request_composition_manifest.json`: independently verified within-request,
  gained/lost-selection, moving/stationary-overlap identities and input/output
  hashes. These are additional derivatives, not rewritten original results.
- `evidence_manifest.json`: hashes of original and supplementary analysis;
  `figure_inspection.json` pins the visually inspected scientific PNGs.
  PNG/PDF pairs show threshold/speed outcomes and exact utilization components.
- `runtime_environment.json`: interpreter/package/platform versions. Exact
  native binary and its C++/Cython source files are included in the raw archive.
- `checkpoint_integrity.json`, `storage_reclaim.json`: all initial failures,
  corrected focused tests, source/raw records and byte-proved reconstruction of
  removed duplicate archive caches. No original raw/source/evidence work is lost.
- `archive_index.json`: every member/part size/SHA and explicit canonical matrix
  restoration paths. `prepublication_checks.json` and `publication.json` bind
  final checks, actual GitHub implementation, source and Xiaoyu Su identity.

User dropoff timestamps mark alighting start; logged holding ends at physical
alighting completion. Logged overlap includes moving passenger sharing,
stationary exchanges and group size. Three-seed benchmark sensitivities are
conditional on one fixed cohort and assumed fleet/opt-in/fence/patience/service;
they do not establish geography-only causality or empirical AV calibration.

## Restore complete raw records

Concatenate the 9 numbered parts and verify before extraction:

```bash
cat records.tar.gz.0* > records.tar.gz
sha256sum records.tar.gz
mkdir restored
tar -tzf records.tar.gz
tar -xzf records.tar.gz -C restored
```

Expected SHA-256: `7af9519f9afe4608b09ad1487cf3a1c282b6340cda8bdf760a3d974d18a7f856`. All member paths are relative to the
recorded workspace. Every archived member and upload-part byte passes readback.
Archive includes 12992 records: failed/corrected source/JUnit/raw histories,
full regression/windows, all real studies, fresh inputs, commands, independent
audits, reporting helpers, configurations, runtime and used public inputs.
CSV/TXT/XML bytes are retained unchanged. Plan photographs are not republished.

For each `omitted_public_matrices` row, copy its `restore_from` file to `path`
and verify exact size/SHA. Only byte-identical canonical large public matrices
are omitted; all private/small/nonidentical inputs remain. Chicago source is
FleetPy Chicago /Zenodo 15189440, with source README, CC BY 4.0 attribution to
Florian Dandl/Roman Engelhardt, metadata, URLs, published MD5 and SHA-256.
Manhattan canonical data, if referenced by inherited native fixtures, comes
from FleetPy Manhattan /Zenodo 15187906. All relative restore paths are explicit.
Original large public ZIPs remain external with verified download provenance.

Duplicate logical archive caches for earlier phases were reclaimed only after
exact concatenated-published-part proof; `storage_reclaim.json` records their
hashes and restoration commands. Every original physical/source record and
published part remains preserved. Verified identical immutable input matrices
may share local storage, with every logical path/byte retained. Restore under
the recorded workspace/dependency layout; rebuilding the native binary changes
its hash and requires explicitly recorded validation.
