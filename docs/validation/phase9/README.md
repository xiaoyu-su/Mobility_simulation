# Phase 9 validation evidence

All final gates pass: 370 tests, 234 regression simulations, 32 restored windows
and 56 real-data physical runs. `validation.json` and the independent checks
record the authoritative counts; the archive retains failed/interrupted history
separately from the final successful runs.

Read [the phase guide](../../PHASE_9.md) for implementation and experiment design,
[AV input assumptions](../../AV_DATA.md) for empirical limits, and
[the work log](../../WORK_LOG.md) for the complete change/check/failure record.
`RESULTS.md` and the CSVs report measured benefits and adverse outcomes together.

The final source digest is
`66fe97b5ab63c89a440583da274cb3e1e87841f070285cb322e2b95f0a5ad939`
across 245 Python/dependency files. `source_record.json` lists every file hash.
The run manifests retain the prepublication Git parent; the complete frozen
source snapshots are archived so dirty-candidate validation is reproducible.

## Review files

- `validation.json`: final gate counts and scope.
- `full-suite.txt`, `junit.xml`, `suite-integrity.json`: full pytest outcome and
  independent physical simulation/window inspection.
- `legacy-identity.json`: exact historical non-AV output comparisons.
- `av-default-compatibility.json`: 14 unchanged old AV cases /93 byte-identical
  tables; two AV/future-value cases retain the intentional eligibility correction.
- `main_manifest.json`, `followup_manifest.json`, `full_manifest.json`: exact
  commands, seeds, inputs, source guard, exit status and matched-input audits.
- `seed_results.csv`, `configuration_summary.csv`: all policy/seed results,
  means and ranges, including unfavorable outcomes.
- `paired_effects.csv`: matched-seed changes; intervals are conditional on one
  fixed source cohort and are absent for the single-seed full-demand pair.
- `common_rider_effects.csv`: wait changes for identical served rider IDs.
- `independent_checks.json`: every physical run's booking, product, chronology,
  capacity, service, consent/fence, type-factor and output-byte checks.
- `threshold_tradeoffs.png` / `.pdf`: scientific figure with seed ranges.
- `archive_index.json`: archive member hashes, upload-part hashes and explicit
  public-matrix omissions with restoration paths.
- `prepublication_checks.json`: source, output, archive, link and history checks.
- `publication.json`: verified remote implementation commit and author identity.

## Complete raw record

The logical archive is `records.tar.gz`. If split, concatenate parts in numeric
order before extracting, then check its SHA-256 against `archive_index.json`:

```bash
cat records.tar.gz.0* > records.tar.gz
sha256sum records.tar.gz
mkdir restored
# Inspect member names before extraction; all paths are relative workspace paths.
tar -tzf records.tar.gz
tar -xzf records.tar.gz -C restored
```

For an unsplit archive, omit the concatenation command. Archive members retain
original raw SVG/XML/TXT bytes. All stored member bytes and every upload part
are verified by readback. Archives include:

- `.setup/phase9/checkpoint`, `corrected`, `corrected-v2`: failed and corrected
  focused tests, JUnit, complete physical outputs and frozen source snapshots.
- `.setup/phase9/threshold-commitment-failure.json`, `interruption.json`,
  `checkpoint_status.json`: the 23 accepted-product mismatches and explicit
  interruption of obsolete validation. Partial old manifests are evidence of
  interrupted candidates, not successful final results.
- `.setup/phase9/full-final`: final full regression logs and every simulation
  and restored-window output, including test-private input bundles.
- `.setup/phase9/real_final`, `grids_final`, `analysis`: exact build/run commands,
  runtime/return codes, all grids, analysis code and derived results.
- `market_inputs/phase9_final_av_10pct` and `phase9_final_av_full`: final private
  demand/training/forecast/supply/network metadata; their earlier candidate
  counterparts and interrupted `market_results/phase9` are preserved too.
- `market_results/phase9_final`: all 56 complete physical policy outputs, logs,
  audits, reports and manifests (53 distinct seed/configurations plus three
  exact fresh-process control replays).
- Public input download/extraction/zone-mapping manifests, polygon/node mapping,
  zone lookup and Zenodo metadata. The original TLC Parquet and Zenodo ZIP stay
  outside Git with their source URLs, sizes and SHA-256 in those manifests.

Repeated public `.npy` matrices larger than 10 MiB are omitted only when their
exact size, SHA-256 and public restoration path are listed in the index. Restore
those bytes and verify every bundle hash before rerunning. The canonical network
comes from TUM's FleetPy Manhattan dataset (Roman Engelhardt and Florian Dandl,
CC BY 4.0); source code retains its MIT license. The screenshot plan is not
republished as research data.

Run analysis scripts from the restored workspace with the same Python 3.10
virtual environment/dependency versions recorded by the source/run manifests;
edit only explicit workspace path constants when relocating. Large native batch
instances still require an appropriate Gurobi license. Real experiments here use
insertion and license-free HiGHS human repositioning; all three controllers are
exercised by complete small integration cases.

To reproduce an earlier failed checkpoint, first restore its matching archived
source snapshot and use its recorded command. Each private bundle is tied to its
source digest; the final source intentionally rejects a bundle built from an
older candidate. Keep those original manifests unchanged.
