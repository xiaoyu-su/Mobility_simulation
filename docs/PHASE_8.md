# Phase 8: a mixed human/AV fleet

This implements **Round 1 of the AV product section in IMG_3328**: separate AV
rules, rider opt-in, geofenced service, a preference in matching, idle diagnostics
and demand-proportional AV repositioning. The numerical outcomes in that source
plan are reference claims, not measurements reproduced by this fork. Speed
factors, AV-first ETA thresholds and joint forecast corrections belong to the
next round; cross-city comparison follows afterward.

The final full gate passed **339 tests, zero failures/errors/skips**, in
1874.71 seconds. Independent checks cover **217 complete simulations +32
restored windows**. AV-disabled history matches **201 previous full runs /930
byte-identical tables**, plus **128 exact window tables**. All 18 public
Manhattan policy runs also pass independent physical and input checks.
The [evidence index](validation/phase8/README.md) preserves source/inputs/outputs,
failed checkpoints, exact commands, comparisons and archive checksums.

All final checks use 242 frozen source/dependency files, digest
`890505b3db913cbab61c12c3c79b29659de0e296bec1c4dce9499ea7d4f4aeee`.
Source and Git HEAD remained unchanged during the final simulations.
Publication status is recorded in [WORK_LOG.md](WORK_LOG.md).

## Measured results

Three simulation seeds use 3,150 evaluation requests plus 751 warm-up requests,
78 AVs and 697 humans, holding the total fleet at 775. The 19-zone fence comes
only from the three historical training days; 391 evaluation riders are
synthetically AV-eligible. All 18 physical runs finish every accepted booking,
with zero AV-rule, early-service or private-pooling violations. Every policy in
each seed has matching loaded demand/network/initial-fleet audit hashes.

| Policy | Mean completed /3,150 | Mean AV trips | Mean human trips | AV productive utilization | Eligible riders' mean arrival wait |
| --- | --- | --- | --- | --- | --- |
| Preference 0, AV repo off | 3,133.7 | 102.7 | 3,031.0 | 13.9% | 247.2s |
| Preference +300s, AV repo off | 3,126.3 | 180.0 | 2,946.3 | 21.8% | 266.8s |
| Preference 0, AV demand repo | 3,142.0 | 109.0 | 3,033.0 | 14.9% | 225.4s |
| Preference +300s, AV demand repo | 3,144.0 | 305.0 | 2,839.0 | 40.6% | 243.4s |

The combined policy raises AV share of completed trips **3.28%→9.70%** and
productive AV utilization **13.9%→40.6%** relative to the first control. Total
completion rises by only **10.3 trips on average**: most of the AV allocation
gain transfers trips from humans. Human trips/online hour fall **6.33%**, and
whole-run AV repositioning adds **827.1 km on average**. These are conditional
model results, not deployment or income estimates.

The comparisons also retain adverse outcomes. Preference alone reduces mean
completion and raises eligible riders' mean wait. At zero preference, demand
repositioning improves eligible wait by **21.8s** with **742.8 km** of empty
repositioning; the mean of each seed's median nearest-idle-AV proximity gap
falls **94.8s→49.2s** among eligible human-winning dispatches with an idle AV.
That diagnostic population can differ across policies. Productive utilization
barely changes in this comparison, despite lower idle share: empty driving must
not be mislabeled productive service. Relative to repositioning alone, adding
the +300s preference shifts about 194 more trips from humans to AVs but adds
only two completed trips and increases eligible riders' mean wait by 18.0s.

See [all six policies, every seed and paired effects](validation/phase8/RESULTS.md)
for complete results, including negative preference controls. Same-served-rider
wait changes are retained separately to avoid attributing changes in the
served population to a wait improvement. Every individual rider's wait need
not improve even when a group mean falls.

## Product and dispatch rules

`src/fleetctrl/av_product.py` is opt-in. An explicit AV vehicle-type list marks
actual loaded roster vehicles. Both trip endpoint nodes must map to declared
fence zones and the rider must opt in. Roads between those endpoints may cross
other zones; this is an endpoint service area, not a restriction on every road
edge. Rules apply to every boarding in route feasibility, including copied
Alonso-Mora vehicle structures, and are checked again at plan assignment and
against executed service. Humans remain available to both rider groups.

Opt-in is `crc32("av-opt-in-v1/operator/request") / 2**32 < share`.
It is deterministic, independent of simulation seeds and iteration order, and
nested as share increases. It requires no request file rebuild. The keys use
stable request IDs within a bundle, not an inferred observed AV preference.

`op_av_preference_s` subtracts the configured number of **rider seconds times
the objective's value of time** for each passenger assigned to an AV. Positive
values favor AVs; negative values penalize them. Insertion deltas cancel the
credit on existing riders, while native batch objectives use the same term.
It is a matching incentive, not an ETA change or a payment. Supported objective
is `distance_and_user_times_with_walk`, with positive finite `vot`; invalid
units/settings are rejected. Preference is bounded to ±3,600 seconds.

AVs accept selected feasible requests with probability one, including when a
human acceptance model is active. They have the distinct audit class `av` and
are excluded from human class draws. Existing committed trips remain protected.
With the product disabled, original random streams and matching arithmetic are
retained. The immediate search excludes ineligible AV positions before applying
its search-position limit, so they do not consume an ineligible rider's budget.

Supported workflows are the three baseline controllers, independent random
streams, one optimizer worker and immediate BasicRequest road trips. Human
acceptance in the validated mixed product is off or singleton; multi-item human
logit menus are outside this phase's supported mixed-product profile. The market
builder's `--driver-model classes` selects singleton acceptance.
Human shifts support TimeBasedFS; human repositioning supports PavoneFCHiGHS. Other
mixed-fleet shift/repositioning combinations fail explicitly. Complete checks
exercise all three controllers, execution noise, source private-pooling consent,
separate fitted service durations, human acceptance/classes, future value and
changing human shifts. This does not establish all combinations of upstream
charging, reservation, public-transport or multiprocessing modules.
The AV sweep uses complete physical runs. Phase 6's in-place policy whitelist
rejects changes to AV policy parameters; AV snapshot resumption is outside
this phase's validated combinations.

## Positioning and fleet operations

Initial AV node draws condition the operator's existing initial distribution
on the fence using the same per-vehicle initialization stream. If that
distribution has no positive mass in the fence, the explicit fallback is uniform
over mapped fence nodes. Loaded explicit AV states outside the fence or already
carrying tasks are rejected. The audit records every initial AV node.

TimeBasedFS applies its active-share curve to the **human roster**, leaving AVs
available. Its initial parking and later deactivation selection exclude AVs;
direct attempts to deactivate an AV through human shifts raise. Human
repositioning excludes AV idle vehicles and projected arrivals. AVs therefore
cannot be silently sent outside their area by the human strategy.

Optional AV repositioning uses only historical departure forecasts inside the
fence. Largest-remainder apportionment assigns total AV fleet targets by demand
share with stable zone-ID tie breaks. Busy AVs count at their projected final
zone; remaining idle targets are reapportioned to the available idle fleet.
SciPy's Hungarian assignment minimizes travel time from idle AVs to repeated
zone-centroid slots. Empty demand produces no orders. All targets stay inside
the fence and each AV receives at most one order per round. Active rider tours
and AVs already repositioning are retained. Retargeting moving AVs is a later
round's feature. Targets are unlocked, so a matching request can interrupt an
empty repositioning trip through the normal plan APIs.

This is a separate AV forecast policy. It does not yet subtract forecast AV
coverage from human demand; jointly planning both products is a later step.

## Reproduce a market experiment

Use the verified public inputs and CRS override from [Phase 7](PHASE_7.md):

```bash
.venv/bin/python -m tools.synthetic_market build \
  --trips /workspace/market_inputs/fhvhv_tripdata_2019-11.parquet \
  --network /workspace/market_inputs/fleetpy_manhattan/FleetPy_Manhattan/networks/Manhattan_2019_corrected \
  --network-type NetworkTTMatrix \
  --zone-map /workspace/market_inputs/manhattan_tlc_node_zone_info.csv \
  --zone-polygons /workspace/market_inputs/fleetpy_manhattan/FleetPy_Manhattan/zones/Manhattan_Taxi_Zones/polygon_definition.geojson \
  --zone-polygons-crs EPSG:32618 --data-kind tlc_public \
  --sample-fraction .1 --seed 0 --warmup-seconds 7200 --time-step 60 \
  --pickup-service training_curb --max-route-candidates 30 \
  --av-share .1 --av-fence-share .3 --av-opt-in-share .5 \
  --output /workspace/market_inputs/phase8_mixed_av

.venv/bin/python -m tools.av_eval \
  --bundle /workspace/market_inputs/phase8_mixed_av \
  --seeds 0 1 2 --preferences -300 0 300 \
  --repositioning off demand --human-policy repo --timeout 3600 \
  --output /workspace/market_results/phase8_mixed_av
```

Existing destinations are refused. Builds and workers reject changed source,
dependencies or bundle bytes. Each run retains its actual overrides, return
code, runtime, loaded parameters, outputs and physical completion tail. All
policies in each seed must have identical demand/network/initial-fleet audit
hashes. The AV runner requires a prepared AV bundle and never mutates it.

The builder holds **total fleet size fixed**: AVs replace humans. AV count is
rounded, with at least one AV for a positive share, and the actual roster is
reported. Default AV fence is the densest 30% of mapped zones by historical
training-day pickup counts, with deterministic ID tie breaks. `--av-zones`
instead accepts an explicit mapped zone list. Selection never uses the held-out
target day. AV physical/cost specifications are a separately named copy of the
private base vehicle, not an empirically measured AV hardware model.

Raw FleetPy scenario parameters use per-operator list nesting, for example
`op_av_vehicle_types: [[av_vehtype]]` and `op_av_zones: [[101, 102]]` for one
operator. The controller receives flat lists. This is covered through the
actual JSON/configuration/vehicle loaders, not only direct object construction.

## Diagnostics and interpretation

- `av_product_op_0.json`: actual AV IDs/types, fence and input hashes, opt-in
  scheme, initial nodes and every repositioning target/order.
- `av_dispatch_op_0.csv`: first committed assignment per rider, eligibility,
  winning pickup ETA, idle AV count and nearest idle AV travel time at that
  decision. The gap measures proximity, not full alternative insertion
  feasibility; it does not prove that every closer AV could win the request.
- `av_report.json`: executed rule checks, evaluation-cohort AV/human/eligible/
  other-rider service and waits, physical evaluation-window utilization,
  AV idle share, trips per online hour and whole-run repositioning distance.
- `seed_summary.csv`, `paired_comparison.csv`, `per_driver.csv` and manifest:
  complete seeded outcomes, comparisons to preference-zero/no-AV-repositioning
  control, and illustrative whole-run vehicle costs and revenue.

The cohort excludes warm-up. Utilization and trips per online hour use the
evaluation clock window; cohort trips can finish afterward. Repositioning
distance and financial records include warm-up and the completion tail.
All accepted bookings must physically finish. Outputs separately retain
unserved source requests, censored window observations in legacy tests and
missing observed events. A successful run is distinct from a policy benefit.

Preferring AVs may transfer trips from humans, increase some riders' waits or
add empty distance. The experiment reports those outcomes even if AV share
improves. Three simulation seeds quantify conditional model variability for one
sampled demand input; they are not independent city samples or field confidence
intervals. Phase 7's residual calibration errors remain open. Public TLC records
contain no observed AV adoption, geofence, online supply, human refusal model
or AV operating-cost ground truth. No claimed deployment benefit is identified
by these simulations alone.
