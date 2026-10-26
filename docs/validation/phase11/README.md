# Phase 11 validation evidence

Final gates:403 passing tests,269 complete regression simulations,32 restored
windows and15 native physical runs. All257 historical full cases retain
1548 byte-identical checked tables;128 window tables retain exact values.
See [the phase guide](../../PHASE_11.md), [results](RESULTS.md) and
[complete step-by-step record](../../WORK_LOG.md).

The frozen258-file Python/dependency digest is
`d05aa8b2c2bcf7892e20d3016d7c05d8b3993c0ecb99fce8ca27417b716d1caa`. `source_record.json` records every file hash. The precommit
Git parent in run manifests is preserved; publication checks tie the exact tested
bytes to a GitHub implementation commit. Validation coverage improves; matching,
movement, repositioning and feature defaults are unchanged in this phase.

## Review files

- `validation.json`, `full-suite.txt`, `junit.xml`, `suite-integrity.json`:
  complete test outcome and independent physical/full-demand/window inspection.
- `historical-identity.json`: every257 previous full case and32 window comparison.
- `munich_manifest.json`, `chicago_manifest.json`, `manhattan_manifest.json`:
  clean upstream source archive, original file hashes, declared profiles/inputs,
  runtime equality, commands, CPU/thread settings, statuses, exact table checks.
- `clean_artifact_manifest.json`: fresh published Phase10 archive,254 simulator/
  dependency files proved equal to Phase11, isolated imports and three full runs.
- `independent_checks.json`: all15 native physical runs, full raw-output/source/
  input/runtime readback,24 paired table comparisons,24 repeat comparisons and12
  clean-archive comparisons. All60 full-table comparisons are byte-identical.
- `runtime_environment.json`: actual Python/package/platform versions and
  native/full-suite CPU/thread assignments.
- `native_results.csv`, `RESULTS.md`: actual original-profile service and scope;
  these are fidelity results, not a Phase10 policy effect or screenshot fit.
- `native_warnings.json`: original warnings/errors per source/repeat, with raw
  messages preserved; warnings do not replace the independent physical checks.
- `archive_index.json`: every raw member and upload-part hash plus explicit
  public-matrix omissions and canonical restoration paths/sizes/hashes.
- `prepublication_checks.json`, `publication.json`: final source/config/output/
  archive/history/link checks and verified GitHub implementation identity.

## Restore the complete raw record

The logical archive is split into21 upload parts. From this directory:

```bash
cat records.tar.gz.0* > records.tar.gz
sha256sum records.tar.gz
mkdir restored
tar -tzf records.tar.gz
tar -xzf records.tar.gz -C restored
```

Check the logical SHA-256 against `archive_index.json` before extraction:
`bc93ab8faa693505c2e55067e69263f3128fb17b087e3845aed65dc3b35bb01a`. All members are relative workspace paths. All stored member
bytes and every upload-part byte are verified by readback; raw CSV/TXT/XML logs
are preserved. The archive includes both focused checkpoints/source snapshots,
invalid-CPU launch errors (zero physical runs), full-suite raw runs/windows,
all original/fork/repeated city runs, the clean published-source archive/runs,
neutral tools, analysis/check/package scripts, commands, profiles, input inventories,
original public request/map/network/README files used, runtime binaries/sources
and source/input/output hashes. The duplicate1.5GB published-source tar and
protected historical upload parts are not duplicated in this archive: the index
records their exact size/SHA and pinned Git reconstruction/canonical-copy paths.
No current-phase physical output is omitted. Pytest current-directory symlinks/caches are
excluded; the actual target records are retained.

Large public matrices are omitted only after exact size/SHA comparison with
canonical public files. For every `omitted_public_matrices` row, copy the
`restore_from` canonical file to its `path` and verify size/SHA-256. Chicago's
canonical matrices come from FleetPy Chicago ZIP/Zenodo15189440; Manhattan's
from FleetPy Manhattan ZIP/Zenodo15187906. Munich is Zenodo15195726 and does
not supply partial preprocessed matrices. Full download URLs, published MD5,
SHA-256 and extraction provenance remain in the archived manifests. Used
nonidentical/private/small matrices are included; original large public ZIPs
stay external. Native TUM source README/CC BY4.0 attribution to Roman Engelhardt
and Florian Dandl is preserved. No private plan photos are republished.

For `omitted_duplicate_historical_parts`, copy the verified existing repository
payload from `restore_from` to `path`, checking size/SHA. It is pinned to the
recorded published commit; alternatively obtain its `git_member` from that exact
Git revision. For `omitted_reproducible_published_archives`, use the recorded
`restore_argv` in this repository to recreate the exact original `git archive`,
then verify size/SHA. All original extracted-source member hashes remain in the
clean-artifact manifest; current simulator source files and all new physical
outputs remain included. This removes duplicate protected evidence, preserving
exact restoration rather than copying earlier Git payloads twice again.

Use the recorded environment and original workspace layout, restore all omitted
public files, and use the recorded exact native profiles/commands. The native
router is a verified shared compiled extension; verify ABI/runtime hashes or
rebuild its recorded sources and create a new explicitly recorded validation.
Do not claim the same binary proof after a different build or silently bypass
source/runtime/input guards. These are adapted no-repositioning profiles, not
proof that unmodified native Gurobi repositioning fits the restricted license.
