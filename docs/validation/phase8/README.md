# Phase 8 validation records

See [the implementation and reproduction guide](../../PHASE_8.md),
[WORK_LOG.md](../../WORK_LOG.md) and the final `RESULTS.md` in this directory.
These records cover AV-product **Round 1**, not speed/threshold dispatch or
cross-city experiments. The screenshot's numbers are not imported as results.

## Reviewable outputs

- `validation.json`, `junit.xml`, `full-suite.txt`, `suite-integrity.json`:
  final regression gate and independent complete-simulation/window audits.
- `legacy-identity.json`: default/AV-disabled outputs compared directly against
  the archived previous-phase runs, including exact table hashes and restored
  window comparisons. New runs are distinguished from historical controls.
- `source_record.json`: the exact 242-file frozen source/dependency snapshot,
  base Git commit and hashes. The recorded base predates publication; the
  code digest identifies the tested working source.
- `prepublication.json`, `publication.json`: final source/archive/link checks
  and independently verified GitHub implementation commit and authorship.
- `seed_results.csv`, `configuration_summary.csv`, `paired_comparison.csv`:
  complete per-seed outcomes, ranges and matched-seed statistical comparisons.
- `common_rider_effects.csv`: effects on the same riders served in both arms,
  separately for synthetic AV-eligible and other riders.
- `independent_checks.json`: all actual full-run accounting, physical completion,
  event chronology, capacity, service minima, consent and AV product checks,
  with raw output hashes.
- `av_policy_tradeoffs.png` and `.pdf`: standalone scientific figures showing
  both allocation benefits and rider/human-driver/empty-driving tradeoffs.
- `archive_index.json`: all original archived member sizes and SHA256 hashes,
  upload-part checksums and explicit public-matrix restoration information.

`RESULTS.md` reports measured outcomes without filtering out adverse policies.
The corresponding source/commands, failed checkpoints, fixes and raw outputs
are preserved in the archive. Source plan photos are not republished.

## Complete archive

The logical `records.tar.gz` is stored directly when small enough, or split
into numerically ordered `records.tar.gz.001`, `.002`, etc. Every part stays
below GitHub's 100 MB file limit. The index names the actual files and logical
archive SHA256. All member bytes are read back and verified against their
original checksums; split parts are concatenated and checked byte for byte.
Generated logs, XML and SVG artifacts retain their original bytes.

The archive preserves full regression and focused/checkpoint simulations,
source snapshots, failed test/JUnit logs, complete real-data input bundles,
all 18 physical policy runs, actual parameter overrides, traces and audits,
forecasts/cohorts/supply, comparison reports and analysis/packaging scripts.
The runner and `real/execution.json` retain exact commands, return codes and
elapsed times. Existing earlier-phase evidence is preserved unchanged.

Restore into a fresh directory **outside the checkout**. When split:

```bash
mkdir -p /workspace/phase8-restored
cat docs/validation/phase8/records.tar.gz.[0-9][0-9][0-9] \
  > /workspace/phase8-restored/records.tar.gz
sha256sum /workspace/phase8-restored/records.tar.gz
# Compare with archive_index.json, then extract:
tar -xzf /workspace/phase8-restored/records.tar.gz -C /workspace/phase8-restored
```

For a directly stored archive, use that file instead. Do not unpack source
snapshots inside the repository: extra Python files change the simulation
fingerprint. Reproduction manifests retain the original `/workspace` paths;
use an isolated matching workspace or explicitly record path remapping.
Never overwrite recorded input/output bundles when rerunning an experiment.

## Large public inputs and licenses

The original November 2019 TLC Parquet and the public TUM Manhattan ZIP stay
outside Git. Download URLs, original file sizes and verified checksums are
preserved in the archived `market_inputs/download_manifest.json`:

- [NYC TLC High Volume FHV November 2019](https://d37ci6vzurychx.cloudfront.net/trip-data/fhvhv_tripdata_2019-11.parquet):
  SHA256 `b874a6c03589669a6a1d56ef477c536ed13710c4d13adfca35fd1677d9473d50`.
- [FleetPy Manhattan data, Zenodo 15187906](https://doi.org/10.5281/zenodo.15187906),
  Roman Engelhardt and Florian Dandl, CC BY 4.0: ZIP SHA256
  `d9e86f33645e5eec287d387f8d63ad41ddf41d4ef648138b65d636482e2c599e`,
  published MD5 `8b11882ae9c6d87f666bf6e006806744`.

Repeated 155 MB matrix files are omitted from private bundles. For each omitted
file the index gives destination `path`, original `restore_from`, size and
SHA256. Extract the verified ZIP outside the checkout and restore those exact
files, then verify their hashes before worker bundle validation. All private
input manifests and network text files are retained. The original Parquet is
needed to rebuild inputs; prepared-bundle runs need only the verified matrices
restored. Full extraction/zone-adaptation manifests and explicit EPSG:32618
override are preserved. Keep dataset attribution separate from the repository
MIT source license.

## Scope of the evidence

All policy arms hold source demand, hardware, total fleet and initial states
fixed within each seed. AV adoption, opt-in, geofence and supply are explicit
scenario assumptions. The real AV experiment is at 10% demand with a 60-second
causal grid; it does not establish full-demand or cross-city AV effects or
close the previously recorded calibration gaps. Lower idle time can reflect
more empty driving, so inspect productive utilization and repositioning distance
together. Financial metrics are illustrative whole-run model quantities.
