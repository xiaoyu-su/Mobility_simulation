# Phase 16 validation evidence

**465 tests**, **441 complete regression simulations**, **32 restored windows**,
**99 real physical records /90 distinct settings** pass. These are81 anchored
grid settings, nine extra anchored pilot/replays and nine separate legacy bridge
settings. All396 previous full cases preserve3074 tables byte for byte;
128 window tables retain exact values. Nine legacy controls reproduce84 old
critical files including city reports. All270 non-anchor existing source files
remain unchanged; three tool files add optional placement/audits, with unchanged
legacy matching behavior.

Read the [phase guide](../../PHASE_16.md), [original results](RESULTS.md),
[policy/share/placement assessment](ROBUSTNESS.md) and [work log](../../WORK_LOG.md).
This is supply-assumption robustness, not calibrated AV penetration. Fixed
placement/SOC and opt-in do not imply fixed search partitions: actual-type
partitions change and the matched all-human outcomes are explicitly retained.

## Review records

- `validation.json`, `full-suite.txt`, `junit.xml`, `suite-integrity.json`,
  `historical-identity.json`: full/window checks and exact old-table identity.
  Unavailable original promise columns are marked unavailable; actual
  completion is always required for picked-up riders.
- `source_record.json`:277 frozen source/dependency hashes, digest
  `e3e70ac0eb6d716b90491ece20701abad3afb61da924464a427a5e952a29dc5c`. Four new files; three existing tool changes,270 prior
  files unchanged. Fourteen configurations are snapshotted with tested source.
- `s5_manifest.json`, `s10_manifest.json`, `s20_manifest.json`,
  `pilot_manifest.json`, `legacy_manifest.json`: every command, seed, one-thread
  CPU pinning, status, timing and raw/source/input hashes. Main anchored90
  physical records pass60 within-study and54 cross-share background checks.
- `manifest.json`: original anchored report with81 unique settings /nine
  replays /nine strata /18 all-human search-partition comparisons. All listed
  artifacts remain unchanged. `pilot_validation_manifest.json` pins the gate.
- `legacy_bridge_checks.json`: nine legacy physical/offer/deadline audits and84
  exact historical file comparisons. Their raw trajectories are identical to
  previously independently sweep-verified records. `input_preflight.json`
  verifies12 fresh bundles, rounded roster/anchor counts and old default input
  identity; no historical source is retagged.
- `independent_checks.json`, `independent_seed_checks.csv`: all90 anchored
  raw/source/runtime checks, original-clock promises, actual rosters and
  initialization, physical service/consent/privacy/capacity/chronology, actual
  completion and independent passenger event sweeps through alighting END.
- `all_human_trajectory_identity.csv` separates actual trajectory differences
  (11/18 versus5% partition) from changed search metadata, with identical
  placement/typed audits. `search_partition_checks.json`: all18 comparisons retain changing
  physical outcomes at fixed actual geometry. `independent_fixed_group_checks.csv`
  independently matches270 physical group rows and fixed denominators.
- `seed_results.csv`, `configuration_summary.csv`, `paired_effects.csv`,
  `control_adjusted_share_effects.csv`, `fixed_group_results.csv`,
  `fixed_group_effects.csv`, `common_rider_effects.csv`: all policies/seeds and
  direct, paired, adjusted and fixed-ID outcomes. Same-served waits condition
  on service; adjusted responses are diagnostic, not field identification.
- `policy_effects_by_fleet_share.csv`, `policy_stability_by_city.csv`,
  `fixed_group_spillovers.csv`, `placement_profile_bridge.csv`,
  `robustness_manifest.json`:27 policy contrasts,54 fixed-group share contrasts,
  separate one-seed geometry effects, stability ranges and derived hashes.
- `late_pickup_records.csv`: actual late pickups with original deadline,
  promise, actual time and study/seed/policy/share/warm/evaluation keys. Repeated
  counterfactual/replay records are not unique observed people.
- `evidence_manifest.json`, `figure_inspection.json`: exact original/derived
  hashes and visually inspected PNG/companion PDF. Original raw/reports remain
  unchanged by supplementary interpretation.
- `runtime_environment.json`: Python/platform/package versions; native C++/
  Cython sources and binary hashes are archived.
- `checkpoint_integrity.json`, `storage_record.json`,
  `postrun_storage_record.json`:13-test /45-physical-scenario focused gate,
  exact snapshots and byte-preserving duplicate storage proofs.
- `archive_index.json`, `prepublication_checks.json`, `publication.json`:
  member/part hashes, public-matrix restore paths, source/config/raw/runtime/
  archive/link checks, identities and actual GitHub publication verification.

Every accepted promise fits480s and every accepted rider completes; actual late
pickups remain visible. Trips/waits use evaluation request IDs and later
fulfillment; occupied utilization/online hours clip to evaluation time, while
empty distance includes warm-up/tail. Fixed human-prefix metrics preserve the
same driver IDs. Actual-type retained-human metrics change membership with
share. Three seeds on single source cohorts do not provide population, field
adoption, geography-only or daily-throughput identification.

`archive_coverage_checks.json` binds every recorded full/focused/window/real
output, fresh input, source and configuration file to an exact archive member
or canonical-matrix restore entry. Its verifier source is embedded.

## Restore complete records

Concatenate11 parts and verify before extraction:

```bash
cat records.tar.gz.0* > records.tar.gz
sha256sum records.tar.gz
mkdir restored
tar -tzf records.tar.gz
tar -xzf records.tar.gz -C restored
```

Expected SHA256: `0ef42a0ad9e932dd3fd747c642299d367119b886b2cd414209d5e716fb746aeb`. All16704 relative-workspace
members and every upload part pass byte readback. Included are focused/full
histories and windows, all five real studies,12 fresh bundles, immutable
Manhattan parent, all used source/native/runtime/config/helper/command records
and public input provenance. Raw CSV/TXT/XML bytes are unchanged.

Restore each `omitted_public_matrices` entry from `restore_from` to `path` and
verify exact size/SHA. Only identical large canonical public matrices are
omitted; small/private/nonidentical inputs stay included. Original external
ZIP/Parquet hashes are retained. Public sources: FleetPy Munich /Zenodo15195726,
Chicago /15189440 and Manhattan /15187906, retaining original README/CC BY4.0
attribution to Roman Engelhardt/Florian Dandl, URLs/checksums/extraction/zone/TLC
provenance. Plan photographs and reproducible caches are not republished.

Storage proofs preserve every old/new logical raw/source path and byte.
Redundant logical archive caches are removed only after exact published-part
reconstruction; immutable duplicate files may share storage after size/SHA
verification. Completed full-suite copies are shared only after the test process
finishes. No unique work, secret or repository selection is changed.
