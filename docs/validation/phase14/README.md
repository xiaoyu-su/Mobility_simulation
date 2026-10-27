# Phase 14 validation evidence

All final gates pass: **442 tests**, **360 complete regression simulations**,
**32 restored windows**, **90 real physical records /81 unique conditions** and
**nine exact fresh-process replays**. All 324 prior full cases preserve
2402 checked tables byte for byte; 128 window tables retain exact
values. All 27 default-cutoff historical controls preserve
225 critical comparisons.

Read the [phase guide](../../PHASE_14.md), [original results](RESULTS.md),
[robustness assessment](ROBUSTNESS.md) and [work log](../../WORK_LOG.md).
The offer cutoff is an assumption, not an observed cancellation distribution.
All accepted promises fit that cutoff; actual late pickups remain recorded and
every accepted passenger physically completes. No matching policy changes.

## Review records

- `validation.json`, `full-suite.txt`, `junit.xml`, `suite-integrity.json`,
  `historical-identity.json`: actual full-run/window and historical byte checks.
  Missing promise fields in original upstream outputs are marked unavailable;
  all picked-up bookings still require actual dropoff.
- `source_record.json`: all 269 frozen Python/dependency hashes, digest
  `6fbe2c809b300edbdb28cd54f20d4079706f31d151aba1ffda3219f26e40fd8e`. All 264 prior non-summary source files are unchanged;
  the ordinary summary adds compatible-input validation. Publication binds
  dirty-candidate tested bytes to committed/remote-verified source.
- `p240_manifest.json`, `p480_manifest.json`, `p720_manifest.json`,
  `pilot_manifest.json`: every command, seed, pinned CPU/one BLAS/OMP/MKL thread,
  status, timing and source/input/output hash. Within-stratum background checks
  total60; cross-patience typed background checks total54.
- `manifest.json`: original patience report:90 physical records,81 unique
  conditions, nine strata/replays. All listed outputs remain unchanged.
  `pilot_validation_manifest.json` retains the nine-pilot gate.
- `independent_checks.json`, `independent_seed_checks.csv`: all 90 raw physical,
  accepted-promise/deadline, event/occupancy-sweep, loaded-factor, actual
  initialization, consent/capacity/service/chronology and completion checks.
- `late_pickup_records.csv`: individual actual late pickups with cutoff,
  deadline, accepted promise, actual timestamp, warm-up/evaluation flag and
  study/policy identity. Repeated counterfactual/study records are not unique
  real-world passengers. No cause is inferred from lateness alone.
- `historical_real_identity.json`: all 27 default480s controls and exact files.
- `seed_results.csv`, `configuration_summary.csv`, `paired_effects.csv`,
  `common_rider_effects.csv`: every stratum and seed, within-cutoff policy
  contrasts, baseline480s cutoff contrasts, intervals and same-served-ID waits.
- `policy_effects_by_cutoff.csv`, `policy_stability_by_city.csv`,
  `robustness_manifest.json`:27 policy/cutoff combinations, mean-direction
  changes, fixed480s service and exact supplementary input/output hashes.
  Mean-sign stability is descriptive, not a population significance test.
- `evidence_manifest.json`: original and derived artifact hashes;
  `figure_inspection.json` pins the visually inspected scientific PNG and
  companion PDF. Neither original RESULTS nor simulation raw bytes is rewritten.
- `runtime_environment.json`: Python/platform/package versions. Native binary
  plus C++/Cython source is included in the archive.
- `checkpoint_integrity.json`, `storage_record.json`: affected-scenario gates,
  original/final source snapshots and exact byte/storage-preservation proofs.
- `archive_index.json`, `prepublication_checks.json`, `publication.json`:
  member/part SHA, canonical matrix restore paths, final checks, GitHub source,
  author/committer identity and actual publication.

`within_limit_completed` changes its deadline with the stratum;
`within_480s_completed` holds one common actual-pickup target fixed. Offered
and realized waits differ. All results condition on one provided cohort,
three initialization seeds and assumed supply/adoption/fence/service/traffic.
No geography-only causal, daily AV throughput or empirical calibration claim.

## Restore all raw/source/input records

Concatenate the 12 numbered upload parts and verify before extraction:

```bash
cat records.tar.gz.0* > records.tar.gz
sha256sum records.tar.gz
mkdir restored
tar -tzf records.tar.gz
tar -xzf records.tar.gz -C restored
```

Expected SHA-256: `8c80ec2646fa68acc4a414db677a612f81bf01b80d675d5bf1c58b4002cd1dde`. All names are relative workspace paths;
every member and part byte passes readback. The 16508 records include
both focused/source checkpoints, all full regression/windows, all real studies,
nine fresh input bundles, the immutable Manhattan parent, commands, configs,
audits, runtime and used public inputs. Raw CSV/TXT/XML bytes are unchanged;
plan photographs and reproducible caches are not republished.

For each `omitted_public_matrices` entry, restore `restore_from` to `path` and
verify its exact size/SHA. Only byte-identical large canonical matrices are
omitted; small/private/nonidentical inputs remain. Public data sources are
FleetPy Munich /Zenodo 15195726, Chicago /15189440 and Manhattan /15187906,
with original README/CC BY 4.0 attribution to Roman Engelhardt/Florian Dandl,
download URLs/checksums/extraction metadata and TLC lookup/provenance retained.
Original large public ZIP/Parquet files remain external with verified hashes.

Storage proofs retain every original logical path/byte. Duplicate logical
archive caches were reclaimed only after exact published-part reconstruction.
Identical immutable published data in an older clean-source extraction and
retained Git files may share storage. New input matrices may likewise share
immutable originals only after exact size/SHA checks. No original raw/source/
evidence work is lost; restore commands are explicit in `storage_record.json`.
Rebuilding a native binary changes its hash and requires new recorded checks.
