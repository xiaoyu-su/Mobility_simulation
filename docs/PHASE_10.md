# Phase 10: cross-city AV policy comparison

This implements Round 3 of the supplied plan: compare the same AV levers in
Munich, Chicago and Manhattan. The city-neutral input builder, isolated runner
and physical-output reporter are available as `python -m tools.city_av`.
The screenshot's numerical results are reference claims, not fit targets.

The focused gate passes **19 tests /23 complete physical simulations** on source
`c8885e74c9661a558177ac56c908e11c403006ebafcb1ae536c7f0c59333caa7`.
All **66 real-city physical runs** and their independent audits pass, including
six exact fresh-process replay records (60 unique conditions). The full regression
suite passes **389 tests** in **2129.86s**, covering **257 complete regression
simulations and32 restored windows**. All234 historical physical cases retain
**1171 byte-identical checked tables**, plus128 exact restored-window tables. [WORK_LOG.md](WORK_LOG.md) records each
change, intended benefit, failure, correction, command and outcome.

## Inputs and interpretation

| City | Data | Main total fleet | Separate reference |
| --- | --- | --- | --- |
| Munich | TUM AIMSUN PV-to-MoD 2020 benchmark; `d_10_s_1` is a 1% PV sample | 50, as in supplied example | Source pickups 00:00–05:00 |
| Chicago | TUM node-matched 10% June 7, 2022 TNC sample; 2023 OSM network | 100, as in supplied example | Source pickups 00:00–05:00 |
| Manhattan | Existing verified 10% November 26, 2019 TLC cohort/network | 775 training-workload proxy | Earlier Tuesdays, as before |

Public TUM bundles come from Zenodo records
[15195726](https://doi.org/10.5281/zenodo.15195726) (Munich) and
[15189440](https://doi.org/10.5281/zenodo.15189440) (Chicago),
Roman Engelhardt/Florian Dandl, CC BY 4.0. Both original ZIPs pass the published
MD5; download manifests also retain SHA-256 and extraction inventories.
Large original public files stay outside Git with verified restoration details.

The builder preserves native request IDs, node matching and provided traffic
dynamics. It counts excluded unmapped/out-of-window rows. No synthetic observed
pickup/drop-off times are fabricated for native sources. The C++ router binary
and its source files are hashed as runtime dependencies. Missing native
centroid flags are supplied using mapped access nodes. Munich explicitly resolves
18 overlapping node memberships by lowest zone ID; original/chosen memberships
and affected request counts are audited. Other maps still reject duplicates.

Manhattan inputs are rebuilt from the verified old dataset: source consent,
request identities, historical network factors and training reference remain;
benchmark patience/service/noise and common initialization are declared new
comparison assumptions. The parent bundle remains byte-identical. This is not
a direct Phase 9 improvement estimate or a new empirical calibration.

All cities use 05:00–07:00 warm-up, 07:00–10:00 evaluation, a causal 60-second
grid, 480-second assumed patience, 30-second pickup/drop-off service and no
execution noise. Native sources have the supplied all-pooling benchmark
assumption; Manhattan keeps actual source pooling consent. Native provided
traffic dynamics are exogenous benchmark inputs, including Chicago's same-day
factors, not a held-out travel forecast. Fleet/adoption/consent/patience and
source-generation differences prevent a geography-only causal conclusion.

## Matched controls

Human acceptance, human repositioning and AV repositioning are off. AVs replace
10% of the fixed fleet; opt-in is assumed .3 per request, with both endpoints
inside the densest 30% of mapped access zones selected from the separate
reference. Factor 1.25 means 25% longer travel time, or 80% baseline speed.

Every arm shares actual initial positions/SOC by vehicle ID. The designated AV
slots start inside the fence even in the all-human control. The saved placement
is checked against the simulator's own complete initialization hash, including
the actual roster. All-human slots remain unrestricted human vehicles.

A naive all-human control would also change candidate search from two groups
to one. A benchmark-only shadow-slot partition preserves the same per-group
nearest-position budgets. It does not impose AV cost/consent restrictions on
humans. All AV arms retain Phase 9's identical human/AV search budgets. This
counterfactual controls fleet size, starting geometry and search limits; it is
not an experiment adding extra AV capacity.

The harness supports the two immediate insertion controllers, with IRSOnly used
for the actual cross-city comparisons. Native global-batch threshold dispatch
and mixed multi-item human menus retain the earlier explicit limitations.
Ordinary controllers have no shadow marker and retain their existing search.

## Prespecified comparisons

| Study | Seeds | City/fleet conditions | Policies | Physical runs |
| --- | --- | --- | --- | --- |
| Main | 0,1 | Munich 50, Chicago 100, Manhattan 775 | all-human; cost; preference 300; thresholds 0/120/240/480; equal-speed 240 | 48 |
| Supply | 0,1 | Munich 100, Chicago 200 | all-human; threshold 0; threshold 240 | 12 |
| Pilot/replay | 0 | Three main city/fleet bundles | all-human; threshold 240 | 6 |

The six pilots are exact fresh-process replay records against main conditions,
not six extra independent samples. Supply sensitivity doubles both fleet
classes at fixed share; policy comparisons remain matched within each regime.
Across fleet sizes, designated-slot IDs and their seeded layout also change, so
the load sensitivity is not an identical-background policy pair.
Actual completion/load outcomes are measured rather than tuned to the plan.
These demo-fleet profiles can be strongly supply constrained; they do not
reproduce the screenshot's stated load regimes. Native reference sizes are
88 Munich and981 Chicago trips, compared with63441 earlier-training context
rows for Manhattan; sparse/unequal references also limit cross-city inference.

The bounded runner pins each child to an available logical CPU and caps BLAS,
OMP and MKL threads at one. Real comparisons use deterministic insertion without
a wall-clock optimization cutoff. Source/configuration stays frozen during runs.

## Commands

The tracked configurations use paths relative to extracted dataset roots:

```bash
.venv/bin/python -m tools.city_av build \
  --config studies/cross_city_av/configs/munich.json \
  --data-root /workspace/market_inputs/cross_city/munich/FleetPy_Munich \
  --output /workspace/market_inputs/phase10/munich

.venv/bin/python -m tools.city_av run \
  --bundles /workspace/market_inputs/phase10/munich \
            /workspace/market_inputs/phase10/chicago \
            /workspace/market_inputs/phase10/manhattan \
  --policies studies/cross_city_av/configs/policies.json \
  --seeds 0 1 --workers 3 --timeout 7200 \
  --output /workspace/market_results/phase10/main

.venv/bin/python -m tools.city_av report \
  --experiments /workspace/market_results/phase10/main \
                /workspace/market_results/phase10/supply \
                /workspace/market_results/phase10/pilot \
  --output /workspace/market_results/phase10/report
```

Use `--fleet-multiplier 2` when building the two supply bundles. Existing output
destinations are refused. The report verifies every recorded raw output hash,
requires completed studies on one source version, and accepts duplicate
conditions only when the critical physical/audit files match byte for byte.

Per-run checks cover unique/full demand, actual pickup/drop-off IDs, accepted
promise coverage, completion tails, chronology, capacity, physical service
minima, private consent, AV fence/opt-in, accepted product and loaded/executed
timing factors. Pooled reports retain seed results, ranges, conditional paired
intervals, identical-served-rider wait changes, absolute fleet empty kilometers,
retained-human productivity and scientific PNG/PDF curves. Trips/waits use the
evaluation request cohort; utilization uses the evaluation clock; distances
include warm-up and fulfillment tails. Small seed counts do not establish
population uncertainty or universal policy superiority.

Stationary boarding records contain the union of incoming and departing riders.
Capacity checks use actual vehicle limits, every moving load, and both pre/post
exchange loads; valid stationary unions are counted explicitly. Raw logs are
unchanged. Genuine before/after/moving over-capacity cases are rejected.


## Measured outcomes and complete evidence

[RESULTS.md](validation/phase10/RESULTS.md) reports every seed, pooled means,
conditional paired effects, identical-served-rider waits and actual passenger
trip durations. [Validation records](validation/phase10/README.md) retain all
successful and failed candidates, source snapshots, inputs, raw physical outputs,
commands, runtime dependencies, hashes and reproduction instructions.

For threshold0→240, two-seed main AV occupied utilization is **33.64→52.80%**
in Chicago100, **13.12→20.00%** in Manhattan775 and **38.75→38.66%** in Munich50.
Completion changes **523.5→540 /2438→2444 /552.5→560**, respectively. Manhattan
eligible served mean wait increases **199.81→262.53s**. Relative to matched
all-human fleets, threshold240 completion changes **+19.5 /−30 /−29.5**.
There is no universal improvement claim.

The doubled-fleet sensitivity reverses the threshold completion effect:
**1195.5→1181.5 Chicago200** and **1063.5→1051.5 Munich100**. Chicago200 AV
occupied utilization rises **42.75→48.26%**, but AV trips fall **79.5→56** and
mean completed AV passenger duration increases **1264.33→1970.18s**. Occupied
vehicle time and completed passenger time have different domains; these are
conditional co-movements, not an identified causal explanation. The two-seed,
sparse-reference, differently generated city datasets and configured load
regimes limit transfer claims. Full-day field calibration and reproduction of
the screenshot's numerical load regimes remain outside the validated result.
