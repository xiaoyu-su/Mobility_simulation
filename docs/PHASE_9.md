# Phase 9: cautious AV timing, threshold dispatch and repositioning follow-ups

This implements AV-product **Round 2 in IMG_3328/3329**. It adds vehicle-type
travel times, an AV-first pickup-ETA threshold, moving-reposition retargeting,
forecast-error sensitivity and joint human/AV demand planning. Cross-city
experiments are the next round. The screenshots' reported numbers are reference
claims, not measurements reproduced by this implementation.

The corrected focused gate passes **72 tests**, including complete simulations
through all three controllers and exact replay. The full regression suite passes
**370 tests with zero failures or skips** in 2045.38 seconds. All **56 final
real-data physical runs** pass independent checks, including the full-demand
pair and three exact control replays. The regression audit covers **234 full
simulations +32 restored windows**. Historical compatibility matches **201
non-AV runs /930 byte-identical tables**, **14 AV-default runs /93 byte-identical
tables**, and **128 exact restored-window tables**.
Read the [measured results and tradeoffs](validation/phase9/RESULTS.md) and
[complete evidence index](validation/phase9/README.md).
[WORK_LOG.md](WORK_LOG.md) records checkpoints, failures and publication status.

All final runs use 245 frozen source/dependency files, digest
`66fe97b5ab63c89a440583da274cb3e1e87841f070285cb322e2b95f0a5ad939`.
Python/dependency files and Git HEAD stay unchanged throughout validation.

## Vehicle-type travel times

A vehicle CSV may declare `travel_time_factor` in **[1,10]**, default 1. A value
of 1.25 means **25% longer travel time**, equivalent to 80% of baseline speed.
This cautious-vehicle profile deliberately excludes factors below one: ordinary
reachability bounds remain optimistic and cannot discard a reachable slower
vehicle. Invalid/nonfinite/boolean values fail explicitly.

The actual CSV loader retains the field and its loaded value. `SimulationVehicle`
uses it on every executed driving update and replay timestamp; execution noise
remains a separate per-leg multiplier with mean one. VehiclePlan arrival times
and intermediary states, native batch vehicle copies, future-value alternative
ETAs, AV proximity diagnostics and repositioning costs use the same factor.
Stationary pickup/drop-off service, distance and energy per meter are unchanged.

The worker's optional per-type timing override is an explicit intervention,
recorded as both loaded and effective factors in `vehicle_time_factors.json`.
`vehicle_travel_time_factor` in actual leg records is separate from
`travel_time_multiplier`, which describes execution noise. When no type factor
is configured, old output columns and timing arithmetic are retained.

Three controller integration cases use the real config/CSV loaders, a declared
constant-traffic/no-noise fixture and independent matrix entries to check actual
route durations. The matrix router rounds event times to centiseconds; checks
bound that known quantization by update count. Separate line-network tests
check exact planned/executed times, replay, stationary duration, distance and
energy, including combined type factor and noise. These checks detect the
loader-whitelist omission described in the source plan.

## AV-first ETA threshold

`op_av_eta_threshold_s` is an alternative to the cost preference. It requires
zero `op_av_preference_s`. For each new request, compare the best feasible AV
pickup ETA to the smallest feasible human pickup ETA in the retained candidate
set. Choose the earliest AV if it is within the threshold; otherwise retain
human candidates under the ordinary cost/acceptance rule. If no feasible human
is retained, a feasible AV can serve. The inclusive boundary is unit-tested.

This lever supports **PoolingIRSOnly** and
**PoolingIRSAssignmentBatchOptimization**. Native global batch threshold
selection is rejected explicitly; all three controllers support the type-factor,
geofence and other product constraints. A global batch graph cannot implement
the same rule by blindly forcing independent rider choices onto shared capacity.

Every policy-grid arm, including cost-based controls, uses the **same separate
human/AV nearest-position search budgets**. The existing limit of 30 bounds
positions per class, potentially several vehicles at one position. This avoids
mixing a threshold effect with an enlarged candidate pool. The rule is exact
over retained feasible plans, not an exhaustive global search guarantee.

The selected product is committed when the booking is accepted. Shared plan
feasibility prevents later reoptimization from changing that booking between
human and AV products; it can optimize within the committed class. The threshold
uses estimates at dispatch, not an actual pickup-time SLA under execution noise.
The output audit checks both the initial selection and the product that actually
completes the trip.

This execution check found a real integration bug: an earlier insertion-plus-
batch fixture selected 34 AV trips but completed only 11 by AV. Reoptimization
silently moved 23 to humans. The corrected fixture completes all 34 by AV;
its independent report rejects any accepted-product mismatch. Earlier runs,
the mismatch list and the interrupted validation checkpoint are preserved.

## Repositioning controls

- `op_av_retarget`: include vehicles on a sole unlocked empty repositioning
  stop, with no onboard passenger, in the AV target assignment. Replace that
  empty target through normal plan APIs. An unchanged target is retained;
  active rider tours and locked tasks are excluded. Audits mark actual retarget
  orders, and chronological empty vehicle activity remains checked.
- `op_av_forecast_sigma`: mean-one lognormal demand-weight errors, default 0,
  bounded to [0,2]. Isolated `av_forecast/operator/time/zone` streams make errors
  reproducible without consuming demand, driver or execution draws. These are
  assumed errors, not a fitted forecast-error distribution.
- `op_av_joint_repositioning`: target AVs using historical trips with both
  endpoints inside the fence, scaled by assumed opt-in. Before human
  repositioning, subtract expected AV coverage, bounded by total forecast
  demand, eligible forecast demand and available/projected AV count. The
  conservative horizon budget is at most one booking per available AV. Residual
  human demand cannot be negative. This policy changes AV targeting and human
  residual-demand planning together; it is not a single mechanism estimate.
  It retains the historical arrival proxy and applies a demand-side correction;
  it does not jointly optimize human/AV vehicle flows.
- `op_av_repositioning_timestep`: separate callback frequency from the historical
  forecast resolution. Forecast-bin overlap interpolates the rolling horizon.
  Retargeting comparisons hold the 300-second callback fixed in both control
  and treatment; ordinary arms retain 900 seconds.

Default settings retain Phase 8's independent repositioning path. In joint mode,
AV target assignment precedes human planning. Coverage is a forecast quantity,
not an observed count of passengers actually served by AVs.

## Actual experiment design

The main study keeps November 26, 2019, 07:00–10:00 as the evaluation cohort,
with two-hour warm-up and training Tuesdays November 5/12/19. Traffic, curb,
patience and supply use training only. Source pooling consent, polygon CRS
override, request-clock causality and physical completion guards remain enabled.
The modeled total fleet stays fixed; AVs replace humans.

| Study | Seeds | Policies | Complete physical runs |
| --- | --- | --- | --- |
| 10% demand, main | 0–5 | cost control; thresholds 0/120/240/480 at 1.25× travel time; equal-speed threshold 240 | 36 |
| 10% demand, follow-ups | 0–2 | exact threshold-240 control repeat; forecast noise .5; joint planning; callback-300 control; callback-300 retarget; combined | 18 |
| Full modeled-zone demand | 0 | threshold 0 versus 240, both cautious | 2 |

The three repeated main/follow-up controls are fresh-process replay checks,
not extra independent replicas. All policies have assumed opt-in **.3**,
19 historical dense-pickup fence zones and zero cost preference. Human
acceptance is off and human HiGHS repositioning on to isolate the AV levers;
human acceptance/future-value/shift coexistence is checked in complete fixtures.

The sampled cohort contains **3,150 evaluation +751 warm-up requests**, and
**775 vehicles =78 AVs +697 humans**. The full cohort contains **32,192
evaluation +7,315 warm-up requests**, and **7,932 vehicles =793 AVs +7,139
humans**. These are retained completed-trip source cohorts in the modeled
zones, not all attempted city demand. The full-demand pair is one seed; it
does not establish six-seed full-demand inference.
The opt-in/fence conjunction leaves **224 sampled /2,377 full-demand evaluation
requests** eligible. Opt-in is keyed per request, rather than persistent rider
identity; the .3 assumption does not make 30% of all requests AV-eligible.
Sampled and full-demand bundles have their own request IDs, fitted input
proxies and resulting CRC32 opt-in sets. Treat the within-bundle policy pairs
as matched comparisons; differences between sample and full demand cannot be
attributed solely to density or fleet scale.

### Full-demand measured pair

The single-seed full-demand pair completes **31720→31831 of 32,192 evaluation requests**, with actual AV completions **317→2139**, AV served share **1.00%→6.72%**, and AV occupied utilization **5.44%→35.23%**. Eligible served mean arrival wait changes **165.99→180.85s**; human trips per online hour change **1.4663→1.3864**. Whole-run AV empty-distance share changes **77.59%→42.42%**, while absolute empty AV distance increases **3715.15→6010.40km**. A lower empty share is not an absolute empty-driving reduction. Across both vehicle classes, whole-run empty distance changes 55159.55→55348.77 km (+0.34%): the AV increase is partly offset by less human empty driving. This fleet-total measure has the same warm-up/completion-tail domain as the per-class distances. Both runs clear every accepted booking and all physical/product checks. This is a one-seed scale check, with no replicated full-demand interval or full-day claim.

### Commands

Prepare inputs as in [Phase 8](PHASE_8.md), additionally declaring:

```text
--av-opt-in-share .3 --av-travel-time-factor 1.25 --av-repositioning
```

`tools.av_eval --policy-grid path.json` accepts named, validated policies and
records each effective override. Example grid:

```json
[
  {"name":"cost_control", "eta_threshold_seconds":null, "travel_time_factor":1.25},
  {"name":"threshold_240", "eta_threshold_seconds":240, "travel_time_factor":1.25},
  {"name":"equal_speed", "eta_threshold_seconds":240, "travel_time_factor":1}
]
```

```bash
.venv/bin/python -m tools.av_eval \
  --bundle /workspace/market_inputs/phase9_final_av_10pct \
  --policy-grid /workspace/.setup/phase9/grids_final/main.json \
  --seeds 0 1 2 3 4 5 --timeout 7200 \
  --output /workspace/market_results/phase9_final/main
```

`run_final_cases.py` and stage execution records in the evidence archive retain
the exact public-input build/run commands for all studies. Existing destinations
are refused. Every worker verifies source, dependencies and private bundle bytes;
within each seed, loaded demand/network/initial-fleet audits must match.

## Evidence and interpretation

### Six-seed measured allocation gains and service costs

For cautious AVs, threshold 240 versus the same-search cost control changes
mean AV completions **14.67→180.50**, AV served share **0.47%→5.76%** and
occupied utilization **2.42%→29.46%**. Human trips per online hour fall
**1.487→1.412 (5.04%)**. Total mean completion increases **3124.50→3133.50**
of 3150, but its conditional six-seed t interval is **[−0.003,18.003]** and
includes zero. It is not a demonstrated completion improvement.

Compared with threshold 0, threshold 240 adds **127.17 AV trips** and only
**1.33 total completions**, while eligible served mean arrival wait rises
**23.17 seconds**. Threshold 120 has lower eligible wait and higher mean
completion than 240 in this cohort; larger thresholds are not uniformly better.
The equal-speed 240 control completes **204.00 AV trips** on average versus
**180.50** with cautious speed, confirming that the actual speed assumption
changes allocation.

Retargeting versus the same 300-second callback control changes whole-run AV
empty-distance share **63.32%→56.59%** and mean AV trips **180.67→187.67**,
with unchanged mean completion **3135.67**. Eligible served wait worsens
**248.91→261.52 seconds**. Combined noise/joint/retarget operation raises empty
distance share to **73.51%**, versus **58.13%** in its ordinary threshold-240
control. All outcomes, including these costs, remain recorded. Forecast-error
sensitivity is not evidence that inaccurate forecasts improve operations.

The complete results retain each seed, configuration, paired interval, common
served rider comparison and actual output hash. Intervals condition on one
fixed source cohort, not a population sample or multiple cities. Main and
follow-up controls have three exact fresh-process replay pairs across seven
raw output/audit files per pair.

Record request-cohort completion, actual AV allocation, same-served-rider wait
changes, occupied-time utilization, human trips per online hour, full-horizon
empty driving and model costs. Keep every policy, including adverse outcomes.
Utilization uses the evaluation clock; trips/waits use evaluation request IDs;
distance/cost includes warm-up and fulfillment tails. Lower idle time can mean
more empty driving. No daily trip rate is extrapolated from this three-hour
cohort, even in the full-demand case.

[AV_DATA.md](AV_DATA.md) separates scenario assumptions, blocked external
benchmark verification and identifiable observations. The .3 opt-in and 1.25
time factor are scenario choices, not fitted Manhattan AV behavior. Phase 7's
unobserved supply/patience/failed-demand and calibration limits remain open.
Mixed multi-item human menus, AV snapshot resumption, arbitrary upstream
charging/reservation workflows and global batch threshold dispatch are outside
this validated profile. Cross-city evaluation belongs to the next round.
