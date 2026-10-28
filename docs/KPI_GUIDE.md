# KPI interpretation and comparison contract

The executable dictionary is `tools.policy_compare.metrics.catalog()`. Export
it with `python -m tools.policy_compare catalog --output /tmp/my_kpis.json`.
Each entry includes its unit, preference direction and precise population/time
scope. The report retains missing values; it does not fill unserved waits,
zero-denominator AV use or negative-earnings Gini with zero.

## Populations and clocks

**Service:** evaluation request IDs. Original `request_s` is used for city
bundles, not rounded grid admission time. Native examples use their loaded
`rq_time`. Accepted evaluation bookings may finish after the evaluation clock;
those trips remain in completion and wait calculations. Unserved requests stay
in the completion denominator.

**Activity:** actual leg overlap with the declared evaluation clock. Online
seconds exclude out-of-service legs. Occupied time includes physical boarding/
alighting occupancy; user dropoff is alighting start. Implicit and explicit
idle time are retained, with offline time removed once. AV denominators use the
actual loaded AV count/exposure, not a nominal percentage.

**Distance and costs:** whole physical run, including warm-up and fulfillment
tails. Exact within-leg distance is not invented by proportional time clipping.
Full-run cost/earnings proxies are not three-hour evaluation-cohort wages.

## Primary decision dimensions

| Dimension | Read together | Interpretation |
| --- | --- | --- |
| Service coverage | requests, completed, unserved, completion rate | All evaluation demand, including rejection; no conditional wait metric substitutes for coverage |
| Rider experience | mean/median/p95 wait, in-vehicle duration, same-served wait changes | Served-only samples may change; identical served IDs reduce that composition issue but exclude unserved people |
| Reliability | pickup promise MAE, late fraction, completed accepted bookings | Quoted and actual times differ. A valid offer does not guarantee an on-time realized arrival |
| Human decisions | actual attempts, declines, acceptances, terminal rejected requests, re-offers, repeated attempts, menu outside/conflict events | Attempt rates, unique requests and menu choices have different denominators |
| Driver activity/economics | same-human-prefix trips/hour; human modeled earnings mean/CV/p10/p50/p90/Gini | Preserve driver membership for activity. Costs/earnings are assumptions, not observed pay; Gini unavailable for negative values |
| Fleet operations | occupied use, idle share, empty distance/share, reposition-only distance | Higher use can mean longer journeys; lower absolute distance can accompany lost service |
| AV allocation | actual AV count, AV/human completed trips, AV share of served, eligible service rate, eligible/other waits, idle-AV-closer diagnosis | Allocation and idle use are tradeoffs, not automatic welfare improvements |
| Integrity | rule violations, accepted completion, actual events/capacity/chronology/eligibility/privacy | Zero violations is reported only after applicable physical checks pass |

## Statistical movements

Effects are **candidate minus reference**, paired on seed within one compatible
source/input stratum. Fraction change0.05 is **5 percentage points**. A rate
from0.25 to0.30 is also **20% relative growth**; these must not be conflated.
Relative change at a zero baseline is unavailable. Missing KPI pairs are counted
and omitted, not replaced by zeros. One seed has no paired95% interval.

Intervals use a paired t calculation over initialization seeds, not over drivers
or individual trip rows. They condition on the source cohort and assumptions;
three seeds do not identify population uncertainty. Numerous exploratory KPI
intervals are not a multiple-testing-adjusted superiority claim. There is no
single automatic policy ranking.

Named streams isolate exogenous demand/network/initialization and component
randomness. They do not force different policies to execute identical routes,
service events or the same number of stochastic decisions. Matching input audits
must pass before inference. Replay duplicates never increase the seed count.

## AV and driver controls

City all-human controls preserve the declared slot geometry and candidate-search
partition. Actual-type groups can vary with replacement share. Those controls
and source assumptions remain visible; source versions and intervention profiles
are separate strata. The optional placement anchor fixes positions/SOC across
AV-share profiles. Human earnings distributions exclude AV IDs; the all-vehicle
modeled net metric is a separate vehicle-economics proxy. A changing human roster
can still change mean earnings, so fixed human-ID activity is reported alongside.

The full calibration/adoption boundaries are in [AV data](AV_DATA.md) and
[the proposal audit](PROPOSAL_AUDIT.md). A matched simulation effect does not
establish field AV benefits, surveyed willingness, unseen rejected demand or
online supply that the data does not observe.
