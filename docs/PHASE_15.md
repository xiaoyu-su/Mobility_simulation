# Phase 15: rider opt-in robustness

The original plan leaves rider adoption unverified. This follow-up tests the
existing opt-in assumption at **0%, 30% and 100%** on the same three source
cohorts. The comparison holds the 480-second booking cutoff, 10% replacement
fleet, endpoint fence, cautious AV speed factor1.25, service times, traffic,
initialization and candidate-search budgets fixed. No matching-policy code is
changed. These are scenario flags per request, not measured adoption rates or
persistent person-level preferences. Riders still do not dynamically choose
between offers.

The [prespecified study](adoption/study.json) uses three initialization seeds
(0/1/2), all-human and threshold0/240-second dispatch arms. There are81 unique
conditions and nine separate seed0 pilot/replay records. All-human placement
preserves the same designated slots/search groups. Zero opt-in retains AV
replacement vehicles which cannot serve any rider; it therefore differs from
converting those vehicles back to human service. At full opt-in, both trip
endpoints must still lie inside the fixed fence; through-routes can cross other
zones. Human/AV repositioning, driver acceptance and execution noise stay off.

The CRC32 request/operator draw is fixed across seeds. Increasing the opt-in
share creates nested eligible sets without resampling demand or vehicle
placement. The study verifies exact demand bytes, unchanged parameters except
`op_av_opt_in_share`, fence, fleet, routing/runtime and named random streams.
All-human physical outputs must remain byte-identical across opt-in strata.

Three fixed groups retain exactly the same request IDs and denominators:

- `baseline_eligible`: endpoints inside the fence and opted in under30%.
- `additional_opt_in`: endpoints inside the fence, outside the baseline draw.
- `outside_fence`: at least one endpoint outside; AV service remains forbidden.

The first group retains its name even at0%, when it loses eligibility. Fixed
group completion, AV allocation, actual service within480s and served waits show
allocation and spillovers. The same-served-ID comparison conditions on service
in both arms and does not represent rejected riders. Ordinary eligible served
wait changes membership with opt-in. Missing waits/rates at zero denominators
remain missing and paired statistics count omitted seed pairs.

Every accepted promise must fit the original request-clock cutoff. Actual late
pickups remain visible and accepted bookings finish. Physical validation checks
unique/full demand accounting, rejected versus served events, final/tail state,
chronological vehicle activity, endpoint/opt-in eligibility, privacy, capacity,
loaded AV travel factors and pickup/dropoff service. An independent event sweep
reconstructs occupancy through actual alighting end; user dropoff is its start.

## Reproduce

Build all nine tracked [city/opt-in configs](adoption), using the same public
FleetPy Munich/Chicago native sources and immutable Phase9 Manhattan parent
recorded in each config. For example:

```bash
.venv/bin/python -m tools.city_av build \
  --config docs/adoption/chicago_s0.json \
  --data-root /workspace/market_inputs/cross_city/chicago/FleetPy_Chicago \
  --output /workspace/market_inputs/adoption_run/chicago_s0

.venv/bin/python -m tools.city_av run \
  --bundles /workspace/market_inputs/adoption_run/munich_s0 \
            /workspace/market_inputs/adoption_run/chicago_s0 \
            /workspace/market_inputs/adoption_run/manhattan_s0 \
  --policies docs/adoption/policies.json --seeds 0 1 2 --workers 1 \
  --output /workspace/market_results/adoption_run/s0

.venv/bin/python -m tools.city_av.adoption \
  --experiments /workspace/market_results/adoption_run/s0 \
                /workspace/market_results/adoption_run/s30 \
                /workspace/market_results/adoption_run/s100 \
  --output /workspace/market_results/adoption_run/report
```

Build and run the corresponding s30/s100 inputs. Existing outputs are refused;
rebuild fresh inputs under the frozen source rather than retagging historical
evidence. The ordinary summary rejects mixed opt-in assumptions; the opt-in
report uses explicit strata and separates within-stratum policy effects from
opt-in changes at fixed policy. Exact command/checkpoint/source/input/output
records are retained in the [work log](WORK_LOG.md) and final evidence.

Three seeds on a single cohort provide conditional robustness, not population
uncertainty or empirical calibration. Munich uses AIMSUN-derived simulated
demand, Chicago uses the supplied TNC subsample and Manhattan preserves its TLC
cohort and source pooling consent. City, year, network, demand generation and
load differ; cross-city results are not geography-only causal effects. Completed
trip data do not identify rejected demand, cancellation behavior, AV adoption or
online supply. No daily AV throughput is extrapolated.

## Validation and measured results

**452 tests pass** in 2300.98 seconds, with no
failures/errors/skips. This covers **396 complete regression simulations and32
restored windows**. All360 previous full cases preserve **2738 checked
tables byte for byte**; all128 window tables retain exact values. All90 real
physical records pass: **81 unique conditions and nine exact fresh-process
replays**. The27 historical30% controls preserve **225 critical comparisons**.

There are60 within-study background checks,54 cross-opt-in background checks,
18 all-human invariance checks (126 identical files), and nine zero-opt-in
threshold0/240 equivalence checks (63 identical files). Independent event sweeps
reconcile physical AV occupancy/passenger exposure; all270 physical fixed-group
rows match the original analysis. All accepted promises fit480s, every accepted
booking completes, and actual late pickups remain visible.

The following threshold240 results are means over three initialization seeds on
one source cohort per city. Fixed-baseline wait uses the same30%-eligible group
at every opt-in level, including0%; the served subset can still change.

| City | Opt-in % | Completed | AV trips | Fixed baseline-group served wait s | Within480s | Actual late pickups | Whole-fleet empty km |
| --- | --- | --- | --- | --- | --- | --- | --- |
| chicago | 0 | 507.00 | 0.00 | 309.72 | 504.33 | 2.67 | 646.46 |
| chicago | 30 | 547.00 | 29.33 | 311.52 | 543.67 | 3.33 | 727.31 |
| chicago | 100 | 537.67 | 51.00 | 309.85 | 533.67 | 4.00 | 708.77 |
| manhattan | 0 | 2398.67 | 0.00 | 243.31 | 2379.67 | 19.00 | 1419.32 |
| manhattan | 30 | 2441.00 | 134.00 | 257.34 | 2423.33 | 17.67 | 1438.85 |
| manhattan | 100 | 2464.33 | 250.67 | 253.99 | 2448.67 | 15.67 | 1461.68 |
| munich | 0 | 536.67 | 0.00 | 325.51 | 535.33 | 1.33 | 965.97 |
| munich | 30 | 556.00 | 25.67 | 302.44 | 554.67 | 1.33 | 1033.37 |
| munich | 100 | 564.33 | 37.33 | 303.89 | 563.33 | 1.00 | 1054.27 |

30%→100% opt-in at fixed threshold240, using fixed request-group denominators:

| City | Fixed group | Requests | Completion change | AV trip change | Within480s service change | Served wait change s |
| --- | --- | --- | --- | --- | --- | --- |
| chicago | additional_opt_in | 860 | -1.00 | +38.00 | -0.67 | -3.77 |
| chicago | baseline_eligible | 370 | +0.00 | -16.33 | -1.33 | -1.67 |
| chicago | outside_fence | 821 | -8.33 | +0.00 | -8.00 | -10.87 |
| manhattan | additional_opt_in | 525 | +16.67 | +185.67 | +17.00 | +22.95 |
| manhattan | baseline_eligible | 224 | -3.00 | -69.00 | -2.33 | -3.35 |
| manhattan | outside_fence | 2401 | +9.67 | +0.00 | +10.67 | -5.59 |
| munich | additional_opt_in | 191 | +16.67 | +19.00 | +16.67 | -2.32 |
| munich | baseline_eligible | 113 | -4.33 | -7.33 | -4.00 | +1.46 |
| munich | outside_fence | 1588 | -4.00 | +0.00 | -4.00 | +0.76 |

These are measured sensitivities, including adverse outcomes. The fixed-group
served wait comparison can change service composition; identical-ID wait
contrasts are in `common_rider_effects.csv`. Policy effects and paired seed
intervals for every opt-in level are retained in the
[robustness assessment](validation/phase15/ROBUSTNESS.md). The
[original results](validation/phase15/RESULTS.md),
[complete evidence/restoration](validation/phase15/README.md) and
[work log](WORK_LOG.md) retain every setting, command, failure/fix and source/input/
output hash. These checks improve the credibility of adoption assumptions;
changed eligibility does not establish real adoption or a superior policy.
