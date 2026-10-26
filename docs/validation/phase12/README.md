# Phase 12 validation evidence

All final gates pass: 424 tests, 306 complete regression simulations, 32 restored
windows and 72 real policy runs. There are 63 unique conditions and nine exact
fresh-process replay records. All 269 old full cases retain
1596 checked tables byte for byte, with 128 exact window tables.
All 26 old real off/human conditions retain 214 critical file comparisons.

Read [the phase guide](../../PHASE_12.md), [full results](RESULTS.md) and
[complete work log](../../WORK_LOG.md). New repo-on runs require actual empty
AV movement and passenger service priority; earlier legacy profiles retain their
recorded behavior. Conditional policy gains and adverse effects are both retained.

Frozen 261-file Python/dependency digest:
`649db5e784a7838c98a31d23e21048be09fa4697e2fd5931b25d5897df110a28`. `source_record.json` lists every file hash. Manifests retain
the dirty-candidate Git parent; publication checks bind those exact tested bytes
to a committed and remote-verified implementation.

## Review records

- `validation.json`, `full-suite.txt`, `junit.xml`, `suite-integrity.json`:
  final counts, independent physical demand/completion/chronology/window audit.
- `historical-identity.json`, `historical_real_identity.json`:
  all 269 old full simulations, 32 windows and 26 old real-control comparisons.
- `main_manifest.json`, `supply_manifest.json`, `pilot_manifest.json`:
  exact commands, seeds, CPU/thread settings, input/source/output hashes,
  statuses and 54 matched background comparisons.
- `independent_checks.json`, `integrity.json`: all 72 raw physical/source/input/
  native-runtime readbacks,63 unique conditions and nine exact replay records.
- `occupied-reposition-diagnostic.json`, `pilot-validation.json`: the failed
  Chicago 8-leg/18.99km waypoint case and corrected nine-pilot actual movement,
  private/booking checks, committed preemptions and critical control identity.
- `seed_results.csv`, `configuration_summary.csv`, `paired_effects.csv`,
  `common_rider_effects.csv`: every seed/policy, favorable/adverse changes,
  conditional uncertainty and actual identical-served-rider wait changes.
- `passenger_duration_seed_results.csv`, `passenger_duration_summary.csv`:
  actual completed evaluation-cohort pickup-to-dropoff duration, distinct from
  occupied vehicle time clipped to evaluation.
- `av_repositioning_comparison.png` / `.pdf`: scientific paired off/on changes
  with seed-range whiskers. `city_policy_curves.png` / `.pdf` retain off controls.
- `runtime_environment.json`: interpreter/package/platform versions; exact
  native binary and its C++/Cython source dependencies are archived.
- `archive_index.json`: every archive member/upload-part size/SHA and explicit
  canonical public-matrix omissions with exact restoration paths.
- `prepublication_checks.json`, `publication.json`: final review gates and
  verified remote implementation/source/author identity.

## Restore complete raw records

Concatenate the 13 parts in numeric order and verify the logical archive:

```bash
cat records.tar.gz.0* > records.tar.gz
sha256sum records.tar.gz
mkdir restored
tar -tzf records.tar.gz
tar -xzf records.tar.gz -C restored
```

Expected SHA-256:`e5faeb681807eefb0dca4dbc73535f4c5d92245daeb0fbbb105171d744041904`. All names are relative workspace paths.
All member bytes and every upload part pass readback. Raw CSV/TXT/XML bytes
remain unchanged. Archives include all failed/corrected focused source snapshots,
JUnit, raw physical outputs, real failed and corrected studies, input builds,
reference exports/forecasts, source/input/output hashes, commands, independent
audits, report scripts, figures, runtime binaries/sources and used public inputs.
Intentional legacy contrast cases are retained and are not asserted to satisfy
the new opt-in service-priority rule.

Large public matrices are omitted only after exact size/SHA comparison with
canonical files. For every `omitted_public_matrices` row, restore its
`restore_from` file to `path` and verify size/SHA. Chicago base matrices come
from FleetPy Chicago ZIP/Zenodo 15189440; Manhattan from FleetPy Manhattan
ZIP/Zenodo 15187906. Munich is Zenodo 15195726 and supplies no partial preprocessed
tables. All used nonidentical/private/small matrices remain included. Original
large public ZIPs/TLC source remain external with URLs, published checksums,
SHA-256 and extraction provenance in archived records. TUM source README files
and CC BY 4.0 attribution to Roman Engelhardt/Florian Dandl are preserved.

The immutable old Manhattan dataset is included to rebuild new comparison
inputs without source retagging. Identical immutable failed/corrected input
matrices may share local storage; each logical path/content/hash is retained.
A redundant Phase11 published-source tar cache was removed only after byte and
actual Git-stream reconstruction proof; the action/exact pinned restore command
is recorded, while all original physical records remain preserved.

Restore under the recorded workspace layout and use the source/configuration/
runtime/dependency versions. Rebuilding the native extension changes its binary
hash and requires a new explicitly recorded validation. No unverified input,
modified source or incomplete study may enter a pooled result. The native night
reference and stationary temporal transfer are benchmark assumptions, not field
demand-volume calibration or adoption evidence.
