# Phase 7 production validation evidence

Read [the completion report](../../PHASE_7_COMPLETION.md) for engineering changes
and [RESULTS.md](RESULTS.md) for all measured improvements and residual errors.
The earlier [real-data investigation](../phase7-real/README.md) and its archive
are preserved unchanged.

## Records

- `validation.json`: final gates, scope and explicit unresolved limits.
- `junit.xml`, `full-suite.txt`, `suite-integrity.json`: 327 passing tests,
  201 complete simulation outputs and 32 restored windows independently audited.
- `source_record.json`: all 236 frozen Python/dependency file hashes, package
  versions and source digest. The recorded Git base predates the publication
  commit; the code digest identifies the actual tested working source.
- `calibration_results.csv`, `configuration_summary.csv`: every real policy
  arm/seed, matched event errors, coverage, completion, pooling and distributions.
- `policy_results.csv`: effects on common served riders, additional completed
  requests, repositioning distance and illustrative whole-run financial change.
- `provider_diagnostics.csv`: exact raw-row provider joins and selective
  on-scene coverage; diagnostics were not used for held-out tuning.
- `real_run_inventory.json`, `independent_checks.json`: all real full-run
  statuses, actual feature execution and independent integrity checks.
- `repaired-case-identity.json`: both original truncation failures repaired
  without changing their accepted assignments or completed trip times/fares.
- `reference-identity.json`: five byte-identical files for the old/new TUM
  24-hour **no-reposition control**. Original commercial-solver repositioning
  attempts fail the restricted Gurobi size limit and are preserved separately.
- `full-scale-input-identity.json`: both full-demand seeds use 19 identical
  bundle files. `prior-private-violations.json` audits old actual consent
  violations; the corrected runs have none.
- `calibration_and_service.png` and `.pdf`: standalone scientific figures.

## Complete raw records and verification

`regression_records.tar.gz` contains 6,429 original files: final full-suite
outputs and restored windows, the failed integration checkpoint, corrected
focused simulations, exact failed/final source snapshots, logs and JUnit.
`regression_archive_index.json` gives every original file size/SHA256 and the
archive SHA256. All archived file bytes were read back and verified.

`real_records.tar.gz` is stored either directly or as ordered
`real_records.tar.gz.001`, `.002`, etc. Parts are ordinary byte splits; join
them before extraction. `real_archive_index.json` identifies the actual parts,
their sizes and SHA256, the complete archive SHA256 and every original member.
It includes complete private input bundles (except the public matrices described
below), source/filtered cohorts, raw users/vehicle activity, plans/audits,
forecasts/factors/supply, executed commands, stdout/stderr, failures, analysis
scripts and public-data provenance. Every archived file was read back and
verified, and concatenated part bytes were checked against the logical archive.
No raw logs, XML or generated SVG bytes were normalized for whitespace.

Verify and restore into a fresh directory **outside the Git checkout**:

```bash
mkdir -p /workspace/phase7-restored
# If split parts exist, join in lexical/numeric order:
cat docs/validation/phase7-completion/real_records.tar.gz.[0-9][0-9][0-9] \
  > /workspace/phase7-restored/real_records.tar.gz
sha256sum /workspace/phase7-restored/real_records.tar.gz
# Compare against real_archive_index.json before extraction.
tar -xzf /workspace/phase7-restored/real_records.tar.gz -C /workspace/phase7-restored
tar -xzf docs/validation/phase7-completion/regression_records.tar.gz \
  -C /workspace/phase7-restored
```

If the logical archive is stored directly, use that file instead of `cat`.
Extracting source snapshots inside the checkout changes the simulation source
fingerprint by introducing additional Python files. Existing manifests retain
original absolute `/workspace` paths; use an isolated matching workspace for
exact command replay, or explicitly remap paths and record that change. Use a
new output directory for every replay.

## Public data restoration and attribution

The 561,011,664-byte original November 2019 TLC Parquet and the 408,878,341-byte
TUM archive remain outside Git. `market_inputs/download_manifest.json` inside
the real archive records their public URLs, sizes and SHA256 checksums:

- [NYC TLC November 2019 High Volume FHV records](https://d37ci6vzurychx.cloudfront.net/trip-data/fhvhv_tripdata_2019-11.parquet),
  SHA256 `b874a6c03589669a6a1d56ef477c536ed13710c4d13adfca35fd1677d9473d50`.
  These are public completed-trip records, not all requested demand.
- [FleetPy Manhattan data, Zenodo 15187906](https://doi.org/10.5281/zenodo.15187906),
  by Roman Engelhardt and Florian Dandl, licensed CC BY 4.0. Archive SHA256
  `d9e86f33645e5eec287d387f8d63ad41ddf41d4ef648138b65d636482e2c599e`,
  published MD5 `8b11882ae9c6d87f666bf6e006806744`.

The two 155,655,496-byte public matrix files are omitted from each repeated
private bundle. `omitted_public_matrices` in `real_archive_index.json` gives
each required destination, source restoration path, size and SHA256. Download
and verify the public ZIP, extract it outside the checkout, then copy each
listed matrix from its `restore_from` path into its listed `path`. Verify the
copied SHA256 before running the worker's bundle validator. Network/zone text
files, derived filters and all original private input manifests are archived.
The original TUM demand and other public assets can be restored from the same
verified ZIP; `extraction_manifest.json` records the extracted file hashes.

The source GeoJSON incorrectly labels projected coordinates as CRS84. The
recorded builds explicitly use EPSG:32618. Adaptations and methods appear in
`zone_mapping_manifest.json` and the production report. The FleetPy source and
fork modifications remain under the repository MIT license; dataset licensing
is separate. Keep source/data attribution when redistributing these artifacts.

## Reproduction

The real archive includes `.setup/phase7-fixes/run_real_cases.py`,
`run_full_seed1.py` and `real/*/execution.json` with exact build/run arguments,
seeds, stage return codes and runtime. `analyze_results.py`,
`provider_diagnostics.py`, `final_report.py`, `verify_repaired_cases.py`,
`audit_suite.py` and comparison scripts reconstruct the independent checks.
The regression archive contains both 236-file frozen source snapshots.

The final source digest is
`e4736dcf5bc0829f654b12ea6025c1a7065e45920c6190cf19dfdd7c002570a2`.
The complete test command and its initial setup failure/fix are recorded in
[WORK_LOG.md](../../WORK_LOG.md). The original repositioning license limit and
remaining full-demand calibration errors are disclosed, not counted as passed.
