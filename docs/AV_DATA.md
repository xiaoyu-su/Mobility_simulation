# AV data, scenario assumptions and benchmark limits

Phase 9's trip/network inputs are the same verified public sources used in
Phases 7/8: November 2019 NYC TLC High Volume FHV records, the TUM Manhattan
network/zone bundle (Zenodo 15187906, Engelhardt/Dandl, CC BY 4.0), and the
official TLC zone lookup. Private manifests retain URLs, input/output hashes,
source-row identities, filtering, imputation and training/evaluation separation.
The existing large original inputs and public matrices remain outside Git.

Those 2019 completed-trip records contain **no observed AV opt-in, AV fleet
split or per-vehicle AV speed model**. They also omit rejected requests, online
fleet exposure and human refusal coefficients. Consequently this phase measures
conditional policy effects, not an empirically identified AV deployment model.

## Explicit choices

| Quantity | Phase 9 value | Status |
| --- | --- | --- |
| Assumed rider opt-in | .3 | Scenario assumption; fixed CRC32 request IDs within each bundle; not fitted willingness |
| AV fleet share | .1, with reported rounded count | Scenario assumption, with fixed total fleet |
| Service area | 19 dense training-pickup zones | Historical training only; endpoints constrained, road paths may cross other zones |
| Cautious travel-time multiplier | 1.25 | Scenario assumption applied to actual loaded vehicle types, plans and execution |
| Equal-speed control | 1.0 | Explicit timing override with identical physical/cost specifications |
| Forecast error | mean-one lognormal sigma .5 in sensitivity arms | Assumed error; independent reproducible streams |
| Patience/supply | Phase 7 training proxies | Not observed cancellation behavior or online vehicle counts |

The core default opt-in remains .5 for Phase 8 compatibility. Phase 9 commands
explicitly request .3. General trust/fear survey percentages do not directly
identify a ride-request opt-in probability, even when a survey can be accessed.
The opt-in draw is per simulated request, keyed by operator and request ID.
The TLC records do not identify persistent riders, so this does not model a
person's consistent adoption across multiple trips.
The opt-in and both-endpoint fence conditions together leave **224 of 3,150
sampled evaluation requests** and **2,377 of 32,192 full-demand evaluation
requests** eligible. The .3 assumption is not a 30% addressable market share;
actual AV completion is bounded by these eligible request counts.

## External benchmark verification

The supplied plan names Pew 2022/2026 and AAA 2025 survey context, CPUC empty
driving/daily trips and an Obi pickup-wait study. This environment returned
**proxy CONNECT 403** for the attempted Pew, AAA, CPUC and Obi URLs. Public
GitHub repository search for accessible supporting data also returned CONNECT
403. Exact requests and errors are retained in the evidence archive under
`.setup/phase9/research/`. No primary page or benchmark dataset was retrieved.

The screenshot's approximate 46% empty-mile share, 5–6 minute pickup wait and
18–24 trips per vehicle per day are therefore **unverified reference-plan
figures here**, not independently checked observations and not targets used to
tune held-out Manhattan outcomes. No downloaded survey is claimed to justify
the .3 choice. This does not block local simulation: actual TLC/network data
is available and fingerprinted. It limits the empirical calibration claim.

## Definitions required for a valid comparison

- **Empty distance share:** actual AV leg distance with recorded occupancy zero
  divided by all recorded AV distance. It includes empty pickup approaches and
  repositioning over the whole physical run, including warm-up/tail. It is not
  simply the reposition-only distance share.
- **Pickup wait:** model arrival/boarding start minus original source request
  time. Departure after fitted pickup service is a different event. An external
  app quote, arrival measurement or boarding event requires a matching definition.
- **Trips per online hour:** completed evaluation-cohort bookings divided by
  evaluation-clock online hours. Both numerator/denominator domains are labeled.
- **Trips per vehicle per day:** unavailable for this three-hour cohort. Full
  demand is a scale setting, not a full-day observation; no multiplication to
  manufacture a daily value is performed.
- **Forecast coverage:** joint planning's expected AV coverage is bounded by
  forecast eligible demand and projected available AVs. It is not actual unique
  passengers served and should not be added to observed trip counts.

An empirical AV calibration would need compatible actual service-area,
operating-fleet, occupied/empty-mile, request/arrival/boarding and day-long trip
data, with source dates, geography and definitions matched. Those observations
are not supplied by the 2019 TLC file or by inaccessible survey references.
The phase report retains these limits alongside all measured policy outcomes.
