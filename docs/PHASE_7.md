# Phase 7: market inputs and calibration reports

`tools/synthetic_market/` prepares TLC-style high-volume ride records for
FleetPy, fits training travel inputs, builds historical repositioning forecasts
and supply assumptions, then compares complete simulations with repositioning
off and with the new `PavoneFCHiGHS` strategy. Each run uses a private input
bundle; the repository's original data and scenarios are unchanged.
Vehicle physics/cost specifications are copied into and verified with that
bundle, so later edits to a shared vehicle file cannot change a policy pair.

**The public data is downloaded and verified. Production corrections and
full-demand validation are delivered; numerical calibration remains incomplete.** Publishing the cloud
network allowlist resolved the earlier CONNECT 403 responses. The November
2019 TLC records and TUM road/zone bundle are available locally. Initial real
runs exposed timing, spatial, initialization and measurement problems that
fixture success did not identify. See [the production completion report](PHASE_7_COMPLETION.md)
for fixes, all 22 new real policy runs and residual calibration errors, and
[the preserved investigation](REAL_MANHATTAN_INVESTIGATION.md) for the earlier
controlled experiments and failures. The plan's
real-city figures are not results reproduced by this implementation.

## Prepare actual data

Obtain these inputs on a machine with access, or allow their domains in the
cloud environment, and put them under a workspace directory:

1. November 2019 NYC TLC High Volume FHV trip records:
   https://d37ci6vzurychx.cloudfront.net/trip-data/fhvhv_tripdata_2019-11.parquet
2. A FleetPy road network and its node/taxi-zone mapping restricted to the
   modeled Manhattan zones. The upstream Manhattan bundle is at
   https://doi.org/10.5281/zenodo.15187906. Keep its license/provenance.
3. If needed when restricting the map, the official zone lookup:
   https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv

The node map requires `node_index,zone_id,is_centroid`; every modeled zone
needs a valid representative node. The tool uses the supplied map, rather than
guessing geography from a zone number. It does not synthesize a Manhattan road
network from the bundled example. Router choices are `NetworkBasic`,
`NetworkBasicWithStore` and `NetworkTTMatrix`; the matrix router additionally
requires its original `ff/tables/nn_fastest_tt.npy` and distance table.

Install the runtime dependencies in `environment.yml`, including PyArrow
19.0.1 for Parquet, plus the existing test/commercial-optimizer development
requirements when running the full regression suite. The repositioning MILP
uses SciPy's bundled HiGHS and needs no commercial license. Pure batch matching
still uses its existing Gurobi solver; choose insertion for large inputs when
using a restricted Gurobi license.

Example with the verified public files, actual request times, two-hour warm-up,
source pooling consent and training-only pickup service fitting:

```bash
.venv/bin/python -m tools.synthetic_market build \
  --trips /workspace/market_inputs/fhvhv_tripdata_2019-11.parquet \
  --network /workspace/market_inputs/fleetpy_manhattan/FleetPy_Manhattan/networks/Manhattan_2019_corrected \
  --network-type NetworkTTMatrix \
  --zone-map /workspace/market_inputs/manhattan_tlc_node_zone_info.csv \
  --zone-polygons /workspace/market_inputs/fleetpy_manhattan/FleetPy_Manhattan/zones/Manhattan_Taxi_Zones/polygon_definition.geojson \
  --zone-polygons-crs EPSG:32618 \
  --data-kind tlc_public --target-date 2019-11-26 \
  --training-dates 2019-11-05 2019-11-12 2019-11-19 \
  --start-seconds 25200 --end-seconds 36000 --sample-fraction .1 \
  --warmup-seconds 7200 --time-step 1 --pickup-service training_curb \
  --patience-extra-seconds 300 --max-route-candidates 30 \
  --seed 0 --output /workspace/market_inputs/my_manhattan_seed0

.venv/bin/python -m tools.synthetic_market run \
  --bundle /workspace/market_inputs/my_manhattan_seed0 \
  --seeds 0 1 2 --timeout 3600 --output /workspace/market_results/my_manhattan_seed0
```

The large public source files are local workspace inputs, not binaries in Git.
A request-time proxy is required only when the schema lacks `request_datetime`;
use `--request-time-proxy-seconds` explicitly for that case.
Do not label assumed requests/waits as observed. `--data-kind fixture` is
required for synthetic test inputs; use `tlc_public` only for genuine sourced
records. Source hashes and row identity retain the provenance of either kind.

## Data preparation and assumptions

- Stream CSV or Parquet batches; require `hvfhs_license_num`, pickup/dropoff
  timestamps and pickup/dropoff taxi-zone IDs. Record exclusive counts for
  invalid times, unmapped zones, unrepresented intrazonal trips, missing license
  identifiers, other dates and sampling exclusions, plus time-window exclusions.
  Repeated identical zone/time tuples may be distinct trips; row identity is
  retained. Supplying the same source bytes twice is rejected.
- Parse local New York wall-clock timestamps explicitly. Select the evaluation
  request cohort in `[start,end)`. Admit each request at the next grid boundary,
  preserve its source clock and extend the simulation if needed to retain the
  last original request. Warm-up requests have separate IDs. Road endpoints and
  initial positions use stable source-row/role hashes within mapped node pools;
  optional polygons constrain the pools with explicit CRS handling. Use
  `--spatial-mapping centroid` for the old spatial control. Intrazonal requests
  remain excluded unless `--include-intrazonal` is specified with road nodes;
  those requests require distinct eligible origin/destination nodes.
- Sampling uses source-byte/row/seed hashes. Higher fractions contain lower
  fractions' source trips and changing batch size does not change membership.
  Generated FleetPy numeric IDs index each selected bundle; rebuilding with
  another fraction is a different demand scenario, not a matched policy arm.
- Forecast and travel training dates must be distinct, strictly earlier than
  the held-out day, and match its weekday. Source-row samples and full training
  cohorts are retained. Same-service-day historical context before the
  simulation start supplies carry-in and arrivals; travel fitting uses its
  separate training window. Target records never enter fitting or forecasts.
- Fit log ride-duration/imputed-road-ETA ratios, preferring known unshared
  training trips and reporting an explicit fallback when unavailable.
  Within-bin residual standard deviation controls mean-one execution noise;
  per-bin log means determine
  factors `exp(mean_log_ratio + sigma²/2)`, falling back to the global mean
  below three training pairs. This is an empirical proxy: boarding, stops,
  network coarsening and routing error are not separately identified.
- Average training departures/arrivals by zone/bin for forecasts. Integrate
  occupied intervals across bins for a modeled fleet profile, divided by an
  explicit utilization assumption (default .58). This estimates workload-based
  supply; trip files do not identify online driver counts or idle exposure.
- Static fleet size defaults to the measured-window maximum modeled profile,
  independent of warm-up length, with an explicit
  `--fleet-size` override. `--dynamic-fleet` activates the profile through
  existing TimeBasedFS, using generated centroid depots with sufficient parking
  and no charging. Those depot locations are model assumptions. Planned shift
  changes may wait for a driver to finish an accepted booking.
- Default patience uses a historical observed-wait quantile (default .95) plus
  assumed slack (default 300s). It is a proxy for patience, not observed
  cancellation behavior. Held-out waits do not enter these deadlines.
  `--patience-model observed_replay` explicitly retains the earlier
  retrospective experiment. Deadlines remain on the original source clock and
  are verified against every loaded request.
- `--pooling-policy source` enforces known shared-request consent; all/none
  controls are available and missing flags are counted. Pickup service may use
  a historical curb median (`--pickup-service training_curb`) while drop-off
  service stays independently specified (default 30s). These request constraints
  apply in planning and execution under all three supported controllers.
- `--max-route-candidates` configures the existing immediate-search route
  bound. This bounds origin positions, which may contain multiple vehicles;
  it is an explicit heuristic, not a guarantee of globally exhaustive search.
- Optional `--driver-model classes` uses existing illustrative Phase 3 values
  and an explicit full-time share (default .42). `--future-value` enables the
  already implemented reward proxy. These coefficients are not estimated from
  TLC. All three baseline matching controllers have end-to-end coverage.
  Fare and operating-cost values also remain illustrative example parameters;
  reports do not estimate observed driver wages, platform commissions or tips.

## HiGHS repositioning

`op_repo_method: PavoneFCHiGHS` is a separately registered opt-in strategy.
Existing Pavone/Gurobi/CPLEX implementations and disabled behavior are retained.
It reads historical departures/arrivals, current idle supply, incoming plans
and already repositioning vehicles using the existing base helpers.

Fractional historical forecasts produce fractional excess. Floor each zone's
nonnegative excess before computing uniform integer targets; deriving targets
from the fractional sum can demand more whole cars than exist. Minimize road
travel time subject to integer flows, outgoing idle limits and post-move zone
targets. Recheck integrality and conservation before assigning any route.
Failure to solve is explicit; it is not silently counted as successful empty
repositioning. Native plan APIs dispatch only currently idle vehicles and leave
booked tours intact. A private named generator chooses vehicles; the strategy
does not reseed global Python or NumPy streams.

Per-round JSON records forecast inputs/weight, integer excess/targets, objective,
solver status, actual flows and selected vehicles. The normal forecast stats
also retain weighted demand/arrival values. Optional unlocked plans permit later
ordinary assignment to interrupt repositioning through existing behavior.

## Complete runs and reports

Every seed runs both policies in fresh subprocesses. The full request cohort,
network/factors and initial fleet fingerprints must match. The worker verifies
loader IDs/patience, ordinary final/evaluation artifacts, unique complete demand
and completion of every broker-confirmed booking. Driver and vehicle accounting
then checks chronology, costs and fares. Existing independent randomness is
required; optimizer parallelism remains one worker.

The market worker opts into a strict completion tail (default bound 24 hours,
configurable through `--completion-tail-max-seconds`). It keeps the driving
grid, drains assignments and audits remaining tasks/passengers, skipping idle
tail updates. Exhaustion raises. The last fitted traffic factor remains in
force beyond the available profile; tail costs are model quantities, not
observations. Scenarios without the option retain the original tail behavior.

TimeBasedFS may log an initially parked leg beginning one tick before the
configured horizon. The market runner explicitly enables left truncation for
that stationary, empty, zero-distance/toll inactivity only. Its raw log stays
unchanged. All moving or overlapping records still fail. The ordinary paired
accounting API keeps its previous strict default.

`seed_summary.csv`, `per_driver.csv` and `paired_comparison.csv` retain service,
waiting, driver finance/distribution, promise errors, repositioning distance and
inactive-leg counts. Differences are candidate minus control, paired across
seeds. The market-specific runner audits repositioning; the older paired and
window tools retain their existing restriction against unaudited repositioning.

`calibration_report.json` compares held-out source rides/waits where observed.
Duplicate user or source IDs fail before a one-to-one join. Proxy waits are
null, and observed completion/utilization are null because completed-trip files
omit failed requests and fleet online exposure. The supplied rides are not the
universe of attempted marketplace demand. Conditional simulated service means
may describe a different subset from the full source cohort.

Primary arrival/departure comparisons use the same served IDs with the
corresponding observed event, show coverage and reject early service/private
pooling. Warm-up requests are excluded from the evaluation cohort. Legacy
grid/ride summaries remain separately labeled; see the precise semantics and
matched ride-time validation in [the production follow-up](PHASE_7_COMPLETION.md).

All bundle files, source/dependencies and reports are fingerprinted. Existing
destinations are refused. Changing tested source requires rebuilding the bundle.
Failed builds/runs preserve status/logs and never produce a complete manifest.
See `docs/validation/phase7/` for the original fixtures, the
[historical investigation](REAL_MANHATTAN_INVESTIGATION.md), and
[production corrections](PHASE_7_COMPLETION.md) for current gates and limits.
