# Phase 7 production corrections and validation

This follow-up implements the engineering gaps identified in
[the real-data investigation](REAL_MANHATTAN_INVESTIGATION.md). Public trip,
network and zone inputs remain available and fingerprinted. Actual market
identification is a separate question: completed-trip records do not identify
unserved demand, online fleet exposure or driver decision coefficients.

## Implemented contracts

- Market requests enter on the first simulation grid boundary **at or after**
  the source request. Patience stays anchored to the source clock. If the last
  original request rounds to the evaluation end, the simulator extends just
  far enough to load it; the evaluation cohort does not grow.
- The builder retains full historical-day context for supply and arrival
  forecasts. Travel fitting uses a separate training window. Optional warm-up
  carries additional target-day requests with separate IDs; original evaluation
  IDs remain stable and reporting excludes warm-up requests.
- Mapped road-node imputation is deterministic by source-row identity, role
  and seed. Polygon constraints use explicit CRS conversion and fail on empty
  pools. Centroids remain an explicit control. Intrazonal demand can be included
  only with distinct road endpoints. Imputed coordinates are never called GPS.
- Source shared-request consent can constrain pooling per request. The shared
  plan-feasibility check enforces exclusive/private riders across insertion and
  batch matching; batch vehicle structures retain the constraint map. Missing
  flags and all/none sensitivity policies are recorded explicitly.
- Pickup and drop-off service durations are separate request constraints.
  Pickup service can use a historical on-scene-to-pickup median; this no longer
  changes drop-off dwell. The constraints affect planning and actual executed
  stop durations. Legacy scenarios without the operator option retain their
  prior behavior.
- Travel factors use the same imputed endpoint geometry as simulation. Known
  unshared training trips are preferred to avoid fitting pooled detours as road
  speeds; the fallback population is reported. Noise uses within-bin residual
  variation, keeping bin means out of the stochastic variance.
- The default patience assumption uses a historical wait quantile plus explicit
  slack, with no held-out wait in the deadline. Historical waits are a proxy
  for a patience assumption, not observed cancellation behavior. The old
  retrospective observed-wait replay is an explicit option.
- Infrastructure loaders validate and cast integral node IDs, including CSVs
  with blank charging-unit columns. Physical depots need no string-format trick.
- The market pipeline opts into a bounded, audited completion tail. It keeps
  the original driving time step and vehicle order, skips inactive idle updates,
  and raises if assignments/passengers remain at the bound. It does not clip
  execution noise or label truncated bookings complete. Scenarios without the
  new option keep the original tail implementation.
- Reports separate raw-clock vehicle arrival/boarding start, departure after
  boarding and post-boarding riding. Comparisons match served IDs with the
  corresponding observed event and show coverage. Early pickup and private
  pooling are hard failures. Evaluation-window utilization and whole-run cost
  domains are labeled separately; the old grid-wait statistic is retained.

## Validation record

The corrected focused gate passed **37 tests**, including complete fixture
runs across all three affected controllers, source pooling consent, pickup-only
fitted service, warm-up, last-request horizon retention and changing-fleet
matrix-router depots. The first integration checkpoint caught an unused
service-duration attribute; the public setter correction is covered by both
planned-timing and actual physical-duration checks.

The full regression gate passed **327 tests, zero failures/errors/skips**, in
1946.09 seconds. Independent output checks cover **201 complete simulations**
and **32 restored windows**, including chronology, unique accounting and
completed picked-up trips. All runs use frozen source
`e4736dcf5bc0829f654b12ea6025c1a7065e45920c6190cf19dfdd7c002570a2`.

Both originally failed real-data booking cases now complete all original
assignments, including requests 2665 and 1510. Before the horizon, numerical
vehicle activity and all original completed trip times/fares are identical.
Explicit numeric service values can change integer time strings to `.0` in
trajectory text; parsed trajectory event values remain exactly identical.

A separate immutable old-source reference and the corrected source reproduce
five byte-identical output files for the TUM 24-hour insertion control with
repositioning explicitly disabled. The unmodified original repositioning case
hits the same size-limited Gurobi license error; it is not replaced silently by
a different policy and is not declared reproduced.

All **22 new real policy simulations (11 complete pairs)** have finished:
three seeds on November 26, three on November 19 with intrazonal demand,
two full-demand seeds, one shorter-warm-up seed and two changing-fleet seeds.
All accepted bookings complete; every loaded request is accounted for exactly
once. Independent checks validate chronology, capacity, physical service minima,
actual repositioning activity and zero early pickups/private pooling violations.

## Measured improvements and remaining calibration gaps

The original centroid/floor repositioning benchmark had **2,031 pickups before
the raw request clock**; the corrected runs have zero. An independent audit
also found **738 private riders pooled** in the previous road/exact-second arm;
the corrected runs have zero. These are comparisons of engineering violations
across different configurations, not isolated estimates of a policy effect.
Both original noisy-tail booking failures are repaired without changing their
accepted assignments or completed trip times/fares.

For the full-demand November 26 cohort, each arm receives **32,192 evaluation
requests +7,315 warm-up requests**, with a modeled fleet of 7,932. The two seeds
have 19 byte-identical bundle files. Requests use a 60-second causal grid,
source pooling consent, 94-second historically fitted pickup service and
separate 30-second drop-off service. Historical patience is 717+300 seconds.
The fleet and patience remain explicit proxies, not observed online drivers
or cancellation behavior. These real runs use insertion matching; the other
controllers and driver-choice combinations are validated in complete fixtures,
not claimed calibrated against Manhattan observations.

| Full-demand seed | Completed, no repositioning | Completed, repositioning | Arrival median error, no repositioning → repositioning | Pickup median error, no repositioning → repositioning |
| --- | --- | --- | --- | --- |
| 0 | 26,172 | 31,842 | 92.9s → 24.0s | 22.2s → 40.1s |
| 1 | 26,278 | 31,865 | 96.3s → 24.4s | 22.3s → 39.2s |

Repositioning serves **5,587–5,670 more requests** in these full-demand pairs.
Arrival Wasserstein distribution distance falls from about 195–197s to 52–53s, and pickup
distribution distance falls from 101–104s to about 35–36s. The pickup median
error nevertheless grows: one statistic improving does not establish that all
aspects of fit improve. Costs and effects on riders served in both arms appear
in the complete results; some riders wait longer and some experiments have
lower modeled net earnings.

At 10% demand, the three-seed repositioning pickup-median error averages 4.0s
on November 26 and 9.5s on November 19, but corresponding arrival-median errors
are 55.7s and 64.7s. **Those small-sample pickup numbers do not close the
full-demand calibration gap.** Sampling changes pooling density and local
availability; full demand and changing-fleet checks also use a 60-second grid
instead of the sampled static runs' one-second grid. Full-demand modeled pooled
share is about 13%, versus roughly 22% source shared-match among served riders.

[All configurations, individual seeds, matched coverage, provider diagnostics,
policy benefits and costs](validation/phase7-completion/RESULTS.md) are recorded
without omitting adverse outcomes. The public data is ready and the tested
engineering defects are fixed. Numerical arrival/pickup/ride/pooling fit remains
imperfect. Closed-zone cropping, imputed road points, one passenger per booking,
provider heterogeneity, selective on-scene reporting and supply/behavioral
proxies remain limitations. Actual online exposure, rejected requests and true
driver coefficients cannot be recovered from public completed trips alone.

## Reproducibility and publication record

[The evidence index](validation/phase7-completion/README.md) contains all raw
regression/real outputs, source/input/output hashes, failed checkpoints and
repairs, exact commands, independent checks and public-data restoration paths.
Large public sources and repeated matrices stay outside Git with verified
download URLs/hashes. Original evidence is preserved. See
[WORK_LOG.md](WORK_LOG.md) for each change, reason, benefit, command and result.

## Metric semantics

The fixed evaluation cohort is separate from warm-up demand. Model-arrival
wait uses the raw source request clock. Source on-scene comparison includes
only the served IDs with valid on-scene records and reports that coverage.
Departure-after-boarding wait is compared to source pickup wait on the same
served IDs. Whole-run financial fields include warm-up and fulfillment tails;
they are not observed NYC wages or a three-hour window earnings estimate.

`simulated_pickup_wait_median_s` is a retained alias for boarding-start wait;
`legacy_simulation_grid_wait_median_s` exposes the previous rounded-clock
statistic explicitly. `simulated_ride_median_s` retains boarding-start-to-
drop-off duration and `observed_ride_median_s` describes the entire evaluation
cohort. The new post-boarding ride statistic excludes pickup dwell. The
independent validation table pairs it with observed ride time on exactly the
served IDs; compare those matched fields when assessing ride-time fit.
