# Project completion evidence

This is the final engineering/proposal audit, not a new numbered phase. Start
with [results](RESULTS.md), [project acceptance](../../PROJECT_COMPLETION.md),
[proposal reconciliation](../../PROPOSAL_AUDIT.md),
[workflow](../../POLICY_COMPARISON.md) and [KPI definitions](../../KPI_GUIDE.md).

- **485 tests passed**, zero failures/errors/skips. The full suite physically
  executes **509 complete simulations and32 restored windows**. Six explicitly
  marked hand-computed unit fixtures and ten deliberately incomplete negative
  fixtures are excluded from physical simulation counts.
- All **441 prior full cases** preserve **4124 checked
  output files byte for byte. All32 windows preserve128 exact cohort/state tables.
  Matching/AV dispatch algorithms, protected references and previous evidence
  remain unchanged; one existing metric helper accepts an optional archived-spec
  directory, preserving its default behavior.
- Focused tests independently passed20/20 with68 actual full simulations.
  Fresh demonstrations complete57 physical runs:48 matching plus9 city,
 42 unique conditions and15 verified reference replays. All three matching
  controllers and all three cities are exercised. New AV repositioning reporting
  is physically exercised in the focused city tests on Python/C++ routing.
- Independent raw-event/chronology/capacity/privacy/product/completion checks
  agree with core reported KPIs. Nine fresh city controls preserve102 historical
  physical/audit files. Retry KPIs agree with actual nonzero decision records.
- Read-only historical analysis covers72 records (27 allocation,45 repositioning),
  with the original simulation sources explicitly separate from reporting source.
- Final source digest: `7cdb1f6cd12b9a1fa0b9c951ed4aa7779d13e61cc65d1b6d37b4eca6c0ed7418` (285 Python/dependency files).
  All276 other previous source files retain exact hashes. Five new example
  configuration files match their frozen snapshots.

## Inspect the evidence

- `portfolio/`: six separate current-source controller/city strata, all-human city
  controls,46 KPIs, full paired effects, same-served waits, parameter differences
  and PNG/PDF figures. The matching examples have three seeds; fresh cities one.
- `current_av/`: direct threshold240 versus0, using the fresh city bridge.
- `historical_av/`, `historical_repositioning/`: three-seed historical reanalysis,
  no source retagging or fresh-run claims.
- `validation.json`, `full-suite.txt`, `junit.xml`: final full-suite results.
- `suite-integrity.json`, `historical-identity.json`: every physical case and
  exact historical output/window comparison.
- `independent_checks.json`, `independent_seed_checks.csv`,
  `physical_identity.json`: separate raw-event/KPI readback and physical bridges.
- `checkpoint_integrity.json`: collection failure, failed reporting checkpoint,
  corrected unit/focused runs, deliberately interrupted superseded full attempt,
  and final full run. Failures/partial runs are preserved, not counted as success.
- `runtime_environment.json`, `source_record.json`, `figure_inspection.json`:
  environment/source and inspected scientific figure bytes.
- `archive_index.json`, `archive_coverage_checks.json`,
  `prepublication_checks.json`, `publication.json`: member/part readback,
  restorable coverage, protected-history checks and actual GitHub publication.

## Restore complete records

Join the 11 numbered parts in order and verify the logical SHA256:

```bash
cat records.tar.gz.0* > /tmp/project-completion-records.tar.gz
sha256sum /tmp/project-completion-records.tar.gz
# f1c90b5f2f6b8c51608ed1ecf76c4538a388b3c5c88f28ef5982b1be946a98e9
tar -tzf /tmp/project-completion-records.tar.gz
```

The archive has **29591 verified logical files** under paths
relative to `/workspace`: all audit attempts, raw outputs/logs, exact current and
historical source snapshots, actual simulation inputs, study/configuration
snapshots, original proposal images and native runtime. Extract to a suitable
workspace; saved city manifests use their original absolute paths. New matching
comparison directories can also be relocated and re-reported.

`omitted_public_matrices` lists only files whose bytes/size exactly match one of
four large canonical public matrices. Restore each listed logical path from its
`restore_from` entry after verifying SHA256 and size. Their TLC/Zenodo/public
source download records are archived. Original full TLC Parquet/Zenodo download
caches are not re-uploaded; the actual derived simulation inputs are preserved.
Previous published archives remain intact. Storage records identify exact
immutable duplicates shared without changing any logical file bytes.

Archive logical SHA256: `f1c90b5f2f6b8c51608ed1ecf76c4538a388b3c5c88f28ef5982b1be946a98e9`.
