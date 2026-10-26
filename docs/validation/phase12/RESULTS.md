# Phase 12 cross-city AV repositioning results

All **72 physical runs** finish; there are **63 distinct city/fleet/seed/policy conditions** and **9 exact fresh-process replay records**. Every source/input/output contract passes; the per-run physical checks report zero AV rule violations and complete accepted bookings. Source digest: `649db5e784a7838c98a31d23e21048be09fa4697e2fd5931b25d5897df110a28`.

These are conditional benchmark experiments. Munich demand is sampled from an AIMSUN PV-to-MoD simulation; Chicago is a provided 2022 TNC subsample on a 2023 OSM network; Manhattan is the existing 2019 TLC cohort. Fleet size, patience, AV adoption, fence and service models are assumptions. City and load regimes are not randomized, so differences between cities are not a causal geography effect. The supplied plan's numerical figures are not fit targets.

Human acceptance, human repositioning and execution noise are off. AV repositioning is the declared on/off policy lever, with fixed 900-second callbacks and no retargeting, forecast noise or joint planning. Each city has fixed demand and shared actual initial positions/SOC across controls, with the designated AV slots fenced even in the all-human arm. The all-human comparison replaces vehicle types without adding fleet capacity. All arms have the same retained/designated-slot candidate budgets; designated humans remain unrestricted in the human control. Cautious factor1.25 means25% longer travel time, or80% of baseline speed. Opt-in is per request, not persistent rider behavior.

## chicago

Fleet **100**: 2051 evaluation +639 warm-up requests; 10 designated AV slots; reference **981** rows (strictly_earlier_same_source_clock). Provided source: {"doi": "https://doi.org/10.5281/zenodo.15189440", "license": "CC BY 4.0", "creators": ["Florian Dandl", "Roman Engelhardt"], "demand": "TUM node-matched 10% sample of June 7 2022 Chicago TNC completed trips", "network": "2023 OSM benchmark; provided same-day traffic factors, not a held-out forecast", "fleet": "100 vehicles from supplied upstream example; doubled only in prespecified supply sensitivity"}

Fleet **200**: 2051 evaluation +639 warm-up requests; 20 designated AV slots; reference **981** rows (strictly_earlier_same_source_clock). Provided source: {"doi": "https://doi.org/10.5281/zenodo.15189440", "license": "CC BY 4.0", "creators": ["Florian Dandl", "Roman Engelhardt"], "demand": "TUM node-matched 10% sample of June 7 2022 Chicago TNC completed trips", "network": "2023 OSM benchmark; provided same-day traffic factors, not a held-out forecast", "fleet": "100 vehicles from supplied upstream example; doubled only in prespecified supply sensitivity"}

| Fleet | Policy | Seeds | Completed | AV trips | AV occupied % | Eligible wait s | Other wait s | Retained human trips/h | Fleet empty km |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 100 | all_human | 3 | 531.33 | 0.00 | — | 316.74 | 324.20 | 1.85 | 680.96 |
| 100 | threshold_0 | 3 | 536.00 | 23.00 | 36.18 | 304.99 | 322.18 | 1.90 | 693.07 |
| 100 | threshold_0_repo | 3 | 549.33 | 47.67 | 58.06 | 306.73 | 314.55 | 1.86 | 1132.90 |
| 100 | threshold_240 | 3 | 547.00 | 29.33 | 53.87 | 311.52 | 321.48 | 1.92 | 727.31 |
| 100 | threshold_240_repo | 3 | 549.33 | 40.33 | 59.09 | 320.53 | 318.71 | 1.89 | 1252.75 |
| 200 | all_human | 3 | 1320.00 | 0.00 | — | 269.49 | 289.47 | 2.22 | 1275.26 |
| 200 | threshold_240 | 3 | 1208.67 | 60.67 | 48.79 | 284.79 | 299.45 | 2.13 | 1218.47 |
| 200 | threshold_240_repo | 3 | 1296.00 | 107.67 | 57.07 | 276.86 | 288.10 | 2.20 | 2283.14 |

At fleet100, threshold0→240 changes mean AV occupied utilization **36.18%→53.87%**, eligible served wait **304.99→311.52s**, total completion **536.00→547.00**, and whole-fleet empty distance **693.07→727.31km**. These directions are measured, including adverse changes.


## manhattan

Fleet **775**: 3150 evaluation +751 warm-up requests; 78 designated AV slots; reference **63441** rows (prior_training_dates). Provided source: {"network_doi": "https://doi.org/10.5281/zenodo.15187906", "trip_source": "https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page", "network_license": "CC BY 4.0", "network_creators": ["Roman Engelhardt", "Florian Dandl"], "demand": "Phase 9 verified 10% fixed November 26 2019 NYC TLC cohort; prior Tuesdays supply the fence/reference", "comparison_changes": "Shared placement, constant 480s patience, 30s pickup/dropoff, no execution noise; historical network factors/source pooling consent retained", "fleet": "775 training-workload proxy vehicles retained from Phase 9; not observed online supply"}

| Fleet | Policy | Seeds | Completed | AV trips | AV occupied % | Eligible wait s | Other wait s | Retained human trips/h | Fleet empty km |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 775 | all_human | 3 | 2474.33 | 0.00 | — | 227.08 | 247.98 | 1.08 | 1396.87 |
| 775 | threshold_0 | 3 | 2436.00 | 83.33 | 13.29 | 198.13 | 257.92 | 1.13 | 1418.57 |
| 775 | threshold_0_repo | 3 | 2460.33 | 102.67 | 16.55 | 209.43 | 257.22 | 1.13 | 1777.43 |
| 775 | threshold_240 | 3 | 2441.00 | 134.00 | 20.40 | 257.34 | 253.92 | 1.10 | 1438.85 |
| 775 | threshold_240_repo | 3 | 2482.33 | 175.67 | 27.01 | 245.70 | 253.72 | 1.10 | 1908.51 |

At fleet775, threshold0→240 changes mean AV occupied utilization **13.29%→20.40%**, eligible served wait **198.13→257.34s**, total completion **2436.00→2441.00**, and whole-fleet empty distance **1418.57→1438.85km**. These directions are measured, including adverse changes.


## munich

Fleet **50**: 1892 evaluation +631 warm-up requests; 5 designated AV slots; reference **88** rows (strictly_earlier_same_source_clock). Provided source: {"doi": "https://doi.org/10.5281/zenodo.15195726", "license": "CC BY 4.0", "creators": ["Roman Engelhardt", "Florian Dandl"], "demand": "AIMSUN PV-to-MoD synthetic benchmark; d_10 means 1%, not 10%, of PV trips", "fleet": "50 vehicles from supplied upstream example; doubled only in prespecified supply sensitivity"}

Fleet **100**: 1892 evaluation +631 warm-up requests; 10 designated AV slots; reference **88** rows (strictly_earlier_same_source_clock). Provided source: {"doi": "https://doi.org/10.5281/zenodo.15195726", "license": "CC BY 4.0", "creators": ["Roman Engelhardt", "Florian Dandl"], "demand": "AIMSUN PV-to-MoD synthetic benchmark; d_10 means 1%, not 10%, of PV trips", "fleet": "50 vehicles from supplied upstream example; doubled only in prespecified supply sensitivity"}

| Fleet | Policy | Seeds | Completed | AV trips | AV occupied % | Eligible wait s | Other wait s | Retained human trips/h | Fleet empty km |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 50 | all_human | 3 | 587.33 | 0.00 | — | 329.82 | 325.24 | 3.94 | 1074.74 |
| 50 | threshold_0 | 3 | 557.00 | 23.33 | 36.88 | 303.54 | 327.78 | 3.95 | 1025.30 |
| 50 | threshold_0_repo | 3 | 540.00 | 22.33 | 37.45 | 316.26 | 328.74 | 3.83 | 1118.63 |
| 50 | threshold_240 | 3 | 556.00 | 25.67 | 39.53 | 302.44 | 327.13 | 3.93 | 1033.37 |
| 50 | threshold_240_repo | 3 | 551.67 | 21.00 | 36.90 | 309.73 | 329.65 | 3.93 | 1102.90 |
| 100 | all_human | 3 | 1113.00 | 0.00 | — | 335.01 | 307.52 | 3.73 | 1808.78 |
| 100 | threshold_240 | 3 | 1050.33 | 46.67 | 33.08 | 303.80 | 309.55 | 3.72 | 1780.24 |
| 100 | threshold_240_repo | 3 | 1052.33 | 52.33 | 36.93 | 299.78 | 310.52 | 3.70 | 1944.97 |

At fleet50, threshold0→240 changes mean AV occupied utilization **36.88%→39.53%**, eligible served wait **303.54→302.44s**, total completion **557.00→556.00**, and whole-fleet empty distance **1025.30→1033.37km**. These directions are measured, including adverse changes.

## Reading these comparisons

Means/ranges pool simulation seeds within a fixed city/fleet/source cohort; `paired_effects.csv` includes conditional t intervals, valid-pair counts and insufficient-pair flags. Small seed counts do not establish population or cross-city uncertainty. Every policy and seed is retained. `common_rider_effects.csv` compares identical served request IDs, while served-only aggregate wait means can change composition.

Waits/trips use evaluation request IDs and include later physical fulfillment. Occupied/idle/online time is clipped to the evaluation clock; distance includes warm-up and the completion tail. An empty-distance fraction can decrease while empty kilometers increase; inspect the absolute fleet totals. Retained-human productivity tracks the same original human slots in both replacement and all-human arms. Nearest-idle-AV proximity is not proof that an alternative full plan was feasible. No observed AV adoption, driver wage, full-day throughput, fitted unserved demand or universally superior policy is claimed.

Capacity audits check every moving load and both pre/post loads at stationary exchanges. FleetPy records a union of incoming and departing IDs during a boarding stop; its raw stationary occupancy can exceed seated capacity. `stationary_exchange_union_rows` retains those occurrences explicitly; raw records are unchanged.

## Matched repositioning changes

Repositioning uses stationary, separate-reference counts for trips whose **both endpoints** lie inside the AV fence. These are relative spatial weights, not calibrated future trip volumes. Native reference pickups occur strictly before warm-up; Manhattan references are earlier training dates. No evaluation/warm-up request is used to construct these weights. Uniform assumed opt-in scales mass and cancels from the spatial apportionment. Sparse references and transfer across clocks remain limitations.

All `_repo` effects below compare the same threshold with repositioning off, keeping fleet size, source request identities, placement/SOC, search budgets and type speed fixed. Values are two-condition mean differences; inspect paired seeds and identical-served-rider wait comparisons before interpreting service gains.

| City | Fleet | Threshold | Completion change | AV trips change | AV utilization change, pp | Eligible wait change, s | Fleet empty change, km | AV empty change, km |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| chicago | 100 | threshold_0 | 13.33 | 24.67 | 21.88 | 1.73 | 439.83 | 466.94 |
| chicago | 100 | threshold_240 | 2.33 | 11.00 | 5.22 | 9.01 | 525.44 | 529.06 |
| chicago | 200 | threshold_240 | 87.33 | 47.00 | 8.28 | -7.93 | 1064.67 | 993.34 |
| manhattan | 775 | threshold_0 | 24.33 | 19.33 | 3.27 | 11.30 | 358.85 | 359.50 |
| manhattan | 775 | threshold_240 | 41.33 | 41.67 | 6.61 | -11.64 | 469.66 | 476.69 |
| munich | 50 | threshold_0 | -17.00 | -1.00 | 0.57 | 12.72 | 93.34 | 101.39 |
| munich | 50 | threshold_240 | -4.33 | -4.67 | -2.63 | 7.29 | 69.53 | 78.63 |
| munich | 100 | threshold_240 | 2.00 | 5.67 | 3.85 | -4.02 | 164.72 | 191.80 |

`city_repositioning_contract.json` traces actual empty AV legs to recorded commands and distinguishes target arrivals from interrupted legs. A command can be superseded before movement; intent alone is not counted as physical movement. Increased occupied utilization or lower empty-distance fraction does not by itself establish more completed trips or lower absolute empty driving. Favorable and adverse changes are retained.

## Occupied vehicle time versus passenger duration
Higher occupied utilization is not automatically more completed trips or shorter journeys. These supplementary measures use actual completed evaluation-cohort passenger pickup-to-dropoff time, including service and later fulfillment; they are passenger-level durations, while utilization is occupied vehicle time clipped to the evaluation clock. Pooling and time domains therefore prevent a direct conversion between them.
| City | Fleet | Threshold | Mean AV completed | Mean AV passenger duration s | AV duration q95 s |
| --- | --- | --- | --- | --- | --- |
| chicago | 100 | threshold_0 | 23.00 | 1691.82 | 4150.32 |
| chicago | 100 | threshold_0_repo | 47.67 | 1516.92 | 4495.19 |
| chicago | 100 | threshold_240 | 29.33 | 2010.49 | 4407.49 |
| chicago | 100 | threshold_240_repo | 40.33 | 1625.36 | 4001.37 |
| chicago | 200 | threshold_240 | 60.67 | 1906.93 | 4481.57 |
| chicago | 200 | threshold_240_repo | 107.67 | 1254.11 | 4002.82 |
| manhattan | 775 | threshold_0 | 83.33 | 1373.75 | 2512.67 |
| manhattan | 775 | threshold_0_repo | 102.67 | 1457.22 | 2648.14 |
| manhattan | 775 | threshold_240 | 134.00 | 1316.69 | 2488.53 |
| manhattan | 775 | threshold_240_repo | 175.67 | 1345.04 | 2482.83 |
| munich | 50 | threshold_0 | 23.33 | 883.76 | 1379.91 |
| munich | 50 | threshold_0_repo | 22.33 | 922.00 | 1773.91 |
| munich | 50 | threshold_240 | 25.67 | 864.39 | 1417.15 |
| munich | 50 | threshold_240_repo | 21.00 | 954.94 | 1437.98 |
| munich | 100 | threshold_240 | 46.67 | 785.58 | 1397.46 |
| munich | 100 | threshold_240_repo | 52.33 | 758.38 | 1341.01 |

Values are means of per-seed statistics, not pooled passenger quantiles. Pooling, provided traffic dynamics and limited supply can change passenger durations; these benchmarks do not establish empirical passenger acceptance or a field service-quality gain. Both favorable and adverse duration changes are retained in the supplementary CSVs.

## Identical served eligible riders

At threshold240, the following is the mean of per-seed ON-minus-OFF wait changes for eligible request IDs served in both policies. It conditions on service in both arms, excludes requests served in only one arm, and is not a population treatment effect. These checks distinguish wait changes for the same people from a changing served sample.

| City | Fleet | Mean common-served IDs per seed | Same-rider wait change, s |
| --- | --- | --- | --- |
| chicago | 100 | 96.67 | +1.15 |
| chicago | 200 | 266.67 | -11.38 |
| manhattan | 775 | 188.33 | -15.85 |
| munich | 50 | 26.33 | +21.01 |
| munich | 100 | 61.00 | +2.84 |

In doubled-fleet Munich, the served-only aggregate mean wait falls by4.02s while the same-served-rider mean increases by2.84s. Main-fleet Munich worsens on both measures. Manhattan and doubled-fleet Chicago improve on both, while main-fleet Chicago worsens on both. Means over three initialization seeds remain conditional on one fixed source cohort; inspect each seed and common-served count in the CSV.
