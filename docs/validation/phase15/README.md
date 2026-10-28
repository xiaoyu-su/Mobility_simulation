# Phase 15 validation evidence

**452 tests**, **396 complete regression simulations**, **32 restored windows**,
**90 real physical records /81 unique conditions** and **nine exact replays**
pass. All360 prior full cases preserve2738 checked tables byte for byte;
128 window tables retain exact values. All27 historical30% controls preserve
225 critical comparisons. All269 previous source files are unchanged.

Read the [phase guide](../../PHASE_15.md), [original results](RESULTS.md),
[policy/spillover assessment](ROBUSTNESS.md) and [work log](../../WORK_LOG.md).
Per-request nested opt-in is a scenario assumption, not measured adoption or a
dynamic rider-choice model. Zero opt-in retains unusable AV replacement slots;
all-human is a distinct control. At100%, endpoint fencing still applies.

## Review records

- `validation.json`, `full-suite.txt`, `junit.xml`, `suite-integrity.json`,
  `historical-identity.json`: actual full-run/window and historical byte checks.
  Original upstream promise fields can be unavailable; actual completion is
  always required and that unavailable check is explicitly recorded.
- `source_record.json`:273 frozen Python/dependency files, digest
  `34413610b2a4764f0a8dce01f65de5edece6bce01e292a723f819433ba1b88fe`. Four files are new; all269 existing files match Phase14.
  Eleven tracked configurations are snapshotted with the tested source.
- `s0_manifest.json`, `s30_manifest.json`, `s100_manifest.json`,
  `pilot_manifest.json`: every command/seed, CPU pinning and one-thread runtime,
  status, timing and source/input/output hashes.60 within-study and54
  cross-opt-in background checks pass; source demand bytes remain identical.
- `manifest.json`: original report with90 physical records /81 unique
  conditions /nine strata /nine replays,18 all-human physical invariance checks
  and54 cross-opt-in background comparisons. Every listed artifact remains
  unchanged. `pilot_validation_manifest.json` retains the nine-pilot gate.
- `independent_checks.json`, `independent_seed_checks.csv`: all90 physical,
  promise/deadline, occupancy/event-sweep, native-factor, actual initialization,
  consent/capacity/privacy/service/chronology/completion checks.
- `boundary_invariance.json`:18 all-human cross-share checks /126 files and
  nine zero-opt-in threshold equivalence checks /63 files.
  `independent_fixed_group_checks.csv`:270 physical group rows independently
  match IDs, denominators, completions, AV counts, actual waits and480s service.
- `late_pickup_records.csv`: each retained late actual pickup, original request
  clock/deadline, promised/actual time, study/policy/opt-in/warm/evaluation key.
  Counterfactual/replay records are not unique observed people.
- `historical_real_identity.json`:27 unchanged baseline30% controls.
- `seed_results.csv`, `configuration_summary.csv`, `paired_effects.csv`,
  `fixed_group_results.csv`, `fixed_group_effects.csv`,
  `common_rider_effects.csv`: all strata/seeds, fixed group denominators,
  within-stratum and fixed-policy intervention effects, seed intervals and
  same-served-ID waits. Missing zero-denominator waits/rates remain missing.
- `policy_effects_by_opt_in.csv`, `policy_stability_by_city.csv`,
  `fixed_group_spillovers.csv`, `robustness_manifest.json`:27 policy contrasts,
  54 fixed-group adoption contrasts, mean-direction ranges and exact derived
  input/output hashes. Descriptive sign stability is not a significance test.
- `evidence_manifest.json`, `figure_inspection.json`: exact original/derived
  analysis hashes and inspected PNG/companion PDF hashes. Original reports and
  raw output bytes are never rewritten by later interpretation.
- `runtime_environment.json`: Python/platform/packages; native C++/Cython
  sources and binary hashes are archived.
- `input_preflight.json`, `pilot_historical_identity.json`: fresh input-byte
  identity and the nine-pilot /75 historical-file gate before main experiments.
- `checkpoint_integrity.json`, `storage_record.json`, `postrun_storage_record.json`: original two failed report
  checkpoints (27/63 physically completed scenarios), final19-test/72-scenario
  focused gate, full source snapshots, and exact storage-preservation proof.
- `archive_index.json`, `prepublication_checks.json`, `publication.json`:
  all member/part hashes and public-matrix restore paths; source/raw/runtime,
  author/committer and actual remote publication verification.

Trip/wait metrics use evaluation request IDs including later fulfillment;
utilization clips physical occupancy to evaluation clock, and empty distance
includes warm-up/tail. Actual late pickups are retained while accepted promises
fit480s and every booked rider completes. Three initialization seeds on fixed
source cohorts do not identify population uncertainty, empirical adoption,
cancellations or geography-only effects. Daily throughput is not extrapolated.

## Restore all raw/source/input records

Concatenate the10 numbered parts and verify before extraction:

```bash
cat records.tar.gz.0* > records.tar.gz
sha256sum records.tar.gz
mkdir restored
tar -tzf records.tar.gz
tar -xzf records.tar.gz -C restored
```

Expected SHA256: `35666eb97f694de7de795fa3e762973b83972897bbfec6647acd20351748c3ed`. All archive names are relative workspace
paths. All18600 members and every upload part pass byte
readback. Records include all three focused checkpoints, full regression/
window histories, all real studies, fresh bundles, the immutable Manhattan
parent, source/runtime snapshots, commands/configs and all used public inputs.
Raw CSV/TXT/XML bytes are unchanged. Plan photographs and reproducible caches
are not republished.

For each `omitted_public_matrices` entry, restore `restore_from` to `path` and
verify its exact size/SHA. Only identical large public matrices are omitted;
private/nonidentical/small files remain included. Original public ZIP/Parquet
files remain external with verified hashes. Used sources are FleetPy Munich
/Zenodo15195726, Chicago /15189440 and Manhattan /15187906. Original README/
CC BY4.0 attribution to Roman Engelhardt/Florian Dandl, public download URLs,
checksums, extraction/zone metadata and TLC provenance are retained.

Storage proofs preserve all original logical paths and bytes. The redundant
Phase14 logical archive cache is reconstructible from published parts only
after exact concatenated size/SHA verification.337 immutable duplicate old
files share storage with exact retained originals. After full completion,45
additional full-suite files likewise share verified identical originals. No unique raw/source work
was deleted. Fresh input matrices share immutable originals only after exact
size/SHA checks. Rebuilding native binaries changes hashes and requires new
checks. No secret or saved repository selection is changed.
