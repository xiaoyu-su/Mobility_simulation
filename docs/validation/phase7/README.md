# Phase 7 verification evidence

Final complete gate: **310 passed, 0 failed, 0 skipped in 1506.82s**.
The 84 regression/integration cases execute **195 complete simulations +32
bounded restored windows**; 226 unit cases exercise actual solver/input guards.
Additional fixture comparisons add 24 full runs: **219 full simulations +32
restored windows** in final evidence. The new market pipeline accounts for 56
of those complete runs. All accepted full-run bookings finish.

Historical compatibility: **163 full runs /921 output tables exact**, plus all
**128** cohort/driver/physical/activity window tables. All nine approved original
input/configuration hashes remain unchanged. Only the strategy registration,
explicit optional accounting boundary and PyArrow dependency modify pre-existing
source; the other 217 pre-existing Python/dependency files match exactly.

The final source fingerprint is
`d0dd474cef8aae0ccbd1f5c94008788b02648efb523a167c3bbe11c1722f84da`.
Recorded Git HEAD is the development parent; file fingerprints include the
then-uncommitted implementation. No source or HEAD changed during final runs.
Publication changes the commit, not these tested Python bytes.

This phase implements the market-input/calibration pipeline and opt-in HiGHS
repositioning. **Every market-data simulation here uses a labeled fixture.**
The repository has no local TLC/Manhattan sources, and actual requests to TLC,
NYC Open Data and Zenodo fail at the cloud proxy with CONNECT 403.

The public nature of the data does not make it part of the code repository.
TUM's GitHub release contains software archives; its city data is hosted
separately on Zenodo. Required local inputs, public URLs, source assumptions
and build/run commands are in [PHASE_7.md](../../PHASE_7.md). No real NYC
calibration, full-scale city result or real-city parity result is claimed.

## Complete additional fixture comparisons

Four configurations, seeds 0/1/2, 07:00–10:00, 100 unique requests per run:
**24 complete simulations and 12 matched policy pairs**. Both arms of each pair
use the same private network/demand/forecast/fleet/vehicle specification bundle;
only repositioning is enabled in the candidate. All accepted bookings finish.

Means across seeds, control → HiGHS repositioning:

| Fixture configuration | Completed trips | Served-rider wait | Candidate empty repositioning distance | Modeled fleet net earnings (cents) |
| --- | --- | --- | --- | --- |
| Insertion | 100.00 → 100.00 | 2.17s → .76s | 7.21 km | 10462.44 → 10282.08 |
| Immediate/batch, proxy times, classes, future value | 54.33 → 55.33 | 33.78s → 6.23s | 18.68 km | 4148.55 → 4348.25 |
| Native batch, classes, matrix router | 63.33 → 64.00 | 39.48s → 17.00s | 14.75 km | 5245.49 → 5363.24 |
| Changing active fleet | 99.00 → 99.00 | 47.49s → 34.29s | 1.13 km | 10279.03 → 10190.22 |

Waiting falls in these fixtures, but empty driving increases, and modeled net
earnings fall in the insertion and changing-fleet cases. Two configurations
complete slightly more trips; two do not. These illustrate a functioning
comparison/reporting path and real tradeoff accounting. They do not demonstrate
calibrated marketplace benefits. Fares, costs, driver coefficients, centroid
locations and supply are model/fixture assumptions. Conditional wait means can
refer to different served populations. Full paired statistics and seed results
are retained without replacing them with favorable summaries.

## Verification and files

- `validation.json`: final gate counts, source fingerprint, exact historical
  compatibility, fixture outcomes and explicit unrun real-data checks.
- `source.json`, `command.txt`, `pytest.txt`, `junit.xml`: original source,
  exact full-gate command, console and per-case results.
- `run_checks.json`: individual full-run/window output hashes, cohort and
  chronological driver-accounting checks, booked completion and input contracts.
- `historical_compatibility.json`: exact full-run outcome table comparisons
  against the prior phase. Window cohort/driver/physical/activity tables are
  checked separately against their original saved artifacts.
- `vehicle_isolation_compatibility.json`: final comparisons against the
  preserved pre-isolation checkpoint. Moving vehicle specifications into the
  hashed bundle changes data isolation, not physical or decision outcomes.
- Four `*-paired_comparison.csv`, `*-seed_summary.csv` and
  `*-calibration_report.json` groups: original complete fixture reports. The
  proxy case has null observed waits. Observed completion/utilization are null
  in every report because the source schema lacks failed requests and online
  fleet exposure. Duplicate identities fail before calibration joins.
- `data-access.json`: original public-endpoint requests and their actual cloud
  proxy errors. This is an availability restriction, not a private-data paywall.
- Checkpoint console/XML files: preserve the initial 20-unit gate, failed and
  corrected combined checks, final focused replay gate, integrity guards and
  dependency-install correction. The 32-case focused gate covers complete
  replay through all three baseline controllers and road routers, driver
  classes, future value, actual execution noise and dynamic fleets. Eight
  further input guards pass; native HiGHS tests solve 2,070 variables.
- `archive_index.json`: every regular archived file and its original SHA-256,
  all read back and verified after compression.
  **8,394 regular files** verify: 5,017 final and 3,377 checkpoint files.
- `simulation_records.tar.gz`: all final suite and additional comparison raw
  inputs, private bundles, snapshots/prefixes, simulation outputs, worker
  commands/logs, reports and manifests. Original external recorder/audit/archive
  scripts are retained inside the archive without changing frozen source.
- `checkpoint_records.tar.gz`: timely failed/corrected probes, earlier complete
  focused runs and comparisons, and the interrupted first final suite. Their
  original source fingerprints and logs remain unchanged and they are excluded
  from final-source success counts. Original absolute temporary paths may
  predate relocation into checkpoint folders and remain provenance.
  Raw console and failed-checkpoint XML traceback whitespace is preserved;
  these generated artifacts are excluded from the source whitespace check.

The accounting boundary option is explicit and limited to initially parked,
empty, stationary out-of-service time. Raw activity retains its actual recorded
start before the horizon. Moving/displaced/loaded/toll-bearing records and
overlapping activity remain errors; the ordinary API's strict default is
unchanged. Loader contracts verify actual `latest_start_time` values and
complete broker-confirmed bookings rather than just configuration presence.

## Outstanding real-data checks

The November 2019 Manhattan 10% and full-scale runs, real-data patience/supply
sensitivity and calibration, and TUM city-level parity comparisons are **unrun**.
They require public datasets not present or downloadable here. The plan's
original empirical numbers are not copied into validation results. Enable
network access for `d37ci6vzurychx.cloudfront.net`, `zenodo.org` and `doi.org`,
or provide those local source files, then execute the documented build/run
commands. Inspect the actual source schema before using observed wait metrics.

Implementation/evidence commit: `f98f2469a56d0ee83d14d694259c54bc736a07dc`,
published as Xiaoyu Su on
[phase-7-market-data-pipeline](https://github.com/xiaoyu-su/Mobility_simulation/tree/phase-7-market-data-pipeline).
Native push and independent remote-tip verification succeeded. A documentation
follow-up records publication without changing validated implementation bytes
or claiming the outstanding real Manhattan experiments have run.
