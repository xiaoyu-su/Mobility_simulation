# Phase 10 validation evidence

All final gates pass: **389 tests**, **257 full regression simulations**,
**32 restored windows**, and **66 real-city physical runs /60 unique conditions**.
Six pilot records are exact fresh-process repeats, excluded from seed means.
All234 historical full cases retain1171 byte-identical checked tables;128
restored-window tables retain exact values. Failures and fixes remain archived.

Read [the phase guide](../../PHASE_10.md), [measured results](RESULTS.md), and
[the complete work log](../../WORK_LOG.md). Policy gains and adverse outcomes
are reported together. Native city sources, fleet loads and reference sizes
differ; these are conditional two-seed benchmark comparisons, not geography-only
causality, field calibration or replication of the screenshot's numerical claims.

The frozen254-file Python/dependency digest is
`c8885e74c9661a558177ac56c908e11c403006ebafcb1ae536c7f0c59333caa7`.
`source_record.json` lists all file hashes. Run manifests record the precommit
parent and dirty source snapshot; the publication receipt ties those exact bytes
to the committed and remote-verified implementation.

## Review records

- `validation.json`, `full-suite.txt`, `junit.xml`, `suite-integrity.json`: gate
  counts, independent full-demand/chronology/completion inspection.
- `legacy-identity.json`, `av-history-identity.json`: all historical non-AV/AV
  full-case compatibility and restored-window values.
- `main_manifest.json`, `supply_manifest.json`, `pilot_manifest.json`: exact
  commands, pinned CPU/thread settings, seeds, private inputs, source hashes,
  run statuses, matched backgrounds and raw-output hashes.
- `independent_checks.json`, `integrity.json`: all66 physical audits,53 matched
  background checks and six exact replay records (42 critical file comparisons).
- `seed_results.csv`, `configuration_summary.csv`, `paired_effects.csv`,
  `common_rider_effects.csv`: results, ranges, small-sample conditional intervals
  and comparisons for identical served rider IDs.
- `passenger_duration_seed_results.csv`, `passenger_duration_summary.csv`:
  actual completed pickup-to-dropoff durations, distinct from vehicle occupied
  time. `RESULTS.md` explains domains and limitations.
- `city_policy_curves.png` / `.pdf`: standalone scientific plot, seed ranges.
- `runtime_environment.json`: Python/package/platform versions. Exact native
  compiled router and its C++/Cython sources are archived as runtime dependencies.
- `archive_index.json`: logical archive, every member and split-part SHA-256,
  omitted public-matrix paths/sizes/hashes and canonical restoration paths.
- `prepublication_checks.json`, `publication.json`: final source/output/archive
  checks and verified remote implementation identity (added at publication).

## Restore the complete record

From this directory, concatenate numeric upload parts and verify the logical
archive SHA-256 against `archive_index.json` before extraction:

```bash
cat records.tar.gz.0* > records.tar.gz
sha256sum records.tar.gz
mkdir restored
tar -tzf records.tar.gz
tar -xzf records.tar.gz -C restored
```

All members are relative workspace paths. The archive preserves the original
raw TXT/XML/SVG bytes. Every member and upload part is verified by readback.
It contains all focused failed/corrected candidates and frozen source snapshots
(`.setup/phase10/checkpoint`, `corrected`, `corrected-v2` through `corrected-v5`),
full-suite outputs, real attempted/final runs, analysis helpers/outputs, input
build records, C++ runtime snapshot, the immutable Phase9 parent input bundle,
and the used public request/map/README/network files. Do not count partial
failed-study outputs as successful final cases. `presentation_corrections.json`
records a prose-only report correction while preserving original stdout.

Large public network matrices are omitted only after exact byte comparison to
canonical public files. Restore **every** `omitted_public_matrices` entry by
copying its `restore_from` file to its `path`, then verify size and SHA-256.
Obtain canonical Chicago files from the FleetPy Chicago ZIP (Zenodo15189440)
and Manhattan files from the FleetPy Manhattan ZIP (Zenodo15187906; authoritative
URL/record and checksums are in the archived download manifests). Do not infer
missing matrices from another network or recompute them. The original large ZIPs
and full TLC originals stay outside Git; archive manifests retain download URLs,
published MD5, SHA-256 and extraction/source provenance. Munich's used native
routing files and all nonidentical/private/small matrices are included.

Restore records under the original `/workspace` paths, use the source snapshot
and recorded environment, check the native extension ABI or rebuild its recorded
sources, then use the archived exact build/run/report commands. The tracked
`studies/cross_city_av/configs` and phase guide also show CLI examples. Rebuilding
the native extension changes binary bytes and requires a new verified bundle;
do not silently bypass runtime/input/source guards. Requests/maps/metadata from
the public TUM Munich/Chicago sources retain CC BY4.0 attribution to Roman
Engelhardt and Florian Dandl and their original README files.
