# Phase 10 cross-city policy results

All **66 physical runs** finish; there are **60 distinct city/fleet/seed/policy conditions** and **6 exact fresh-process replay records**. Every source/input/output contract passes; the per-run physical checks report zero AV rule violations and complete accepted bookings. Source digest: `c8885e74c9661a558177ac56c908e11c403006ebafcb1ae536c7f0c59333caa7`.

These are conditional benchmark experiments. Munich demand is sampled from an AIMSUN PV-to-MoD simulation; Chicago is a provided 2022 TNC subsample on a 2023 OSM network; Manhattan is the existing 2019 TLC cohort. Fleet size, patience, AV adoption, fence and service models are assumptions. City and load regimes are not randomized, so differences between cities are not a causal geography effect. The supplied plan's numerical figures are not fit targets.

Human acceptance, human repositioning, AV repositioning and execution noise are off. Each city has fixed demand and shared actual initial positions/SOC across controls, with the designated AV slots fenced even in the all-human arm. The all-human comparison replaces vehicle types without adding fleet capacity. All arms have the same retained/designated-slot candidate budgets; designated humans remain unrestricted in the human control. Cautious factor1.25 means25% longer travel time, or80% of baseline speed. Opt-in is per request, not persistent rider behavior.

## chicago

Fleet **100**: 2051 evaluation +639 warm-up requests; 10 designated AV slots; reference **981** rows (strictly_earlier_same_source_clock). Provided source: {"doi": "https://doi.org/10.5281/zenodo.15189440", "license": "CC BY 4.0", "creators": ["Florian Dandl", "Roman Engelhardt"], "demand": "TUM node-matched 10% sample of June 7 2022 Chicago TNC completed trips", "network": "2023 OSM benchmark; provided same-day traffic factors, not a held-out forecast", "fleet": "100 vehicles from supplied upstream example; doubled only in prespecified supply sensitivity"}

Fleet **200**: 2051 evaluation +639 warm-up requests; 20 designated AV slots; reference **981** rows (strictly_earlier_same_source_clock). Provided source: {"doi": "https://doi.org/10.5281/zenodo.15189440", "license": "CC BY 4.0", "creators": ["Florian Dandl", "Roman Engelhardt"], "demand": "TUM node-matched 10% sample of June 7 2022 Chicago TNC completed trips", "network": "2023 OSM benchmark; provided same-day traffic factors, not a held-out forecast", "fleet": "100 vehicles from supplied upstream example; doubled only in prespecified supply sensitivity"}

| Fleet | Policy | Seeds | Completed | AV trips | AV occupied % | Eligible wait s | Other wait s | Retained human trips/h | Fleet empty km |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 100 | all_human | 2 | 520.50 | 0.00 | — | 316.10 | 326.06 | 1.81 | 666.40 |
| 100 | cost_control | 2 | 531.50 | 37.00 | 33.51 | 311.90 | 326.23 | 1.83 | 687.87 |
| 100 | equal_speed_240 | 2 | 548.00 | 45.00 | 53.90 | 324.13 | 314.91 | 1.86 | 716.13 |
| 100 | preference_300 | 2 | 561.50 | 41.50 | 40.98 | 315.72 | 319.86 | 1.93 | 711.74 |
| 100 | threshold_0 | 2 | 523.50 | 24.00 | 33.64 | 307.60 | 319.16 | 1.85 | 669.95 |
| 100 | threshold_120 | 2 | 525.50 | 29.00 | 47.35 | 313.44 | 319.75 | 1.84 | 711.76 |
| 100 | threshold_240 | 2 | 540.00 | 28.00 | 52.80 | 307.61 | 322.96 | 1.90 | 718.15 |
| 100 | threshold_480 | 2 | 538.00 | 31.00 | 54.73 | 311.26 | 320.80 | 1.88 | 710.62 |
| 200 | all_human | 2 | 1295.50 | 0.00 | — | 269.21 | 290.72 | 2.19 | 1251.38 |
| 200 | threshold_0 | 2 | 1195.50 | 79.50 | 42.75 | 271.92 | 297.47 | 2.07 | 1208.64 |
| 200 | threshold_240 | 2 | 1181.50 | 56.00 | 48.26 | 287.78 | 300.06 | 2.08 | 1191.69 |

At fleet100, threshold0→240 changes mean AV occupied utilization **33.64%→52.80%**, eligible served wait **307.60→307.61s**, total completion **523.50→540.00**, and whole-fleet empty distance **669.95→718.15km**. These directions are measured, including adverse changes.

At fleet200, threshold0→240 changes mean AV occupied utilization **42.75%→48.26%**, eligible served wait **271.92→287.78s**, total completion **1195.50→1181.50**, and whole-fleet empty distance **1208.64→1191.69km**. These directions are measured, including adverse changes.


## manhattan

Fleet **775**: 3150 evaluation +751 warm-up requests; 78 designated AV slots; reference **63441** rows (prior_training_dates). Provided source: {"network_doi": "https://doi.org/10.5281/zenodo.15187906", "trip_source": "https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page", "network_license": "CC BY 4.0", "network_creators": ["Roman Engelhardt", "Florian Dandl"], "demand": "Phase 9 verified 10% fixed November 26 2019 NYC TLC cohort; prior Tuesdays supply the fence/reference", "comparison_changes": "Shared placement, constant 480s patience, 30s pickup/dropoff, no execution noise; historical network factors/source pooling consent retained", "fleet": "775 training-workload proxy vehicles retained from Phase 9; not observed online supply"}

| Fleet | Policy | Seeds | Completed | AV trips | AV occupied % | Eligible wait s | Other wait s | Retained human trips/h | Fleet empty km |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 775 | all_human | 2 | 2474.00 | 0.00 | — | 230.28 | 247.04 | 1.07 | 1389.89 |
| 775 | cost_control | 2 | 2431.00 | 48.50 | 7.80 | 208.70 | 256.16 | 1.14 | 1412.67 |
| 775 | equal_speed_240 | 2 | 2456.00 | 155.50 | 18.58 | 244.48 | 251.11 | 1.10 | 1443.99 |
| 775 | preference_300 | 2 | 2437.50 | 103.00 | 14.00 | 220.12 | 254.28 | 1.12 | 1409.50 |
| 775 | threshold_0 | 2 | 2438.00 | 84.50 | 13.12 | 199.81 | 256.66 | 1.13 | 1409.62 |
| 775 | threshold_120 | 2 | 2439.00 | 116.00 | 17.66 | 221.90 | 253.42 | 1.11 | 1407.43 |
| 775 | threshold_240 | 2 | 2444.00 | 133.00 | 20.00 | 262.53 | 252.65 | 1.11 | 1426.15 |
| 775 | threshold_480 | 2 | 2445.50 | 135.50 | 20.48 | 270.47 | 251.37 | 1.10 | 1433.88 |

At fleet775, threshold0→240 changes mean AV occupied utilization **13.12%→20.00%**, eligible served wait **199.81→262.53s**, total completion **2438.00→2444.00**, and whole-fleet empty distance **1409.62→1426.15km**. These directions are measured, including adverse changes.


## munich

Fleet **50**: 1892 evaluation +631 warm-up requests; 5 designated AV slots; reference **88** rows (strictly_earlier_same_source_clock). Provided source: {"doi": "https://doi.org/10.5281/zenodo.15195726", "license": "CC BY 4.0", "creators": ["Roman Engelhardt", "Florian Dandl"], "demand": "AIMSUN PV-to-MoD synthetic benchmark; d_10 means 1%, not 10%, of PV trips", "fleet": "50 vehicles from supplied upstream example; doubled only in prespecified supply sensitivity"}

Fleet **100**: 1892 evaluation +631 warm-up requests; 10 designated AV slots; reference **88** rows (strictly_earlier_same_source_clock). Provided source: {"doi": "https://doi.org/10.5281/zenodo.15195726", "license": "CC BY 4.0", "creators": ["Roman Engelhardt", "Florian Dandl"], "demand": "AIMSUN PV-to-MoD synthetic benchmark; d_10 means 1%, not 10%, of PV trips", "fleet": "50 vehicles from supplied upstream example; doubled only in prespecified supply sensitivity"}

| Fleet | Policy | Seeds | Completed | AV trips | AV occupied % | Eligible wait s | Other wait s | Retained human trips/h | Fleet empty km |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 50 | all_human | 2 | 589.50 | 0.00 | — | 334.48 | 321.04 | 3.95 | 1064.09 |
| 50 | cost_control | 2 | 559.00 | 23.00 | 34.54 | 306.32 | 326.74 | 3.97 | 1033.27 |
| 50 | equal_speed_240 | 2 | 554.50 | 33.50 | 42.85 | 313.59 | 331.10 | 3.86 | 1094.18 |
| 50 | preference_300 | 2 | 542.50 | 28.00 | 40.63 | 312.59 | 331.78 | 3.81 | 1032.64 |
| 50 | threshold_0 | 2 | 552.50 | 25.00 | 38.75 | 305.00 | 329.05 | 3.91 | 1033.28 |
| 50 | threshold_120 | 2 | 549.00 | 23.50 | 37.31 | 285.76 | 332.82 | 3.89 | 1015.05 |
| 50 | threshold_240 | 2 | 560.00 | 25.00 | 38.66 | 301.96 | 329.22 | 3.96 | 1057.23 |
| 50 | threshold_480 | 2 | 550.50 | 28.50 | 42.22 | 320.56 | 330.95 | 3.87 | 1071.60 |
| 100 | all_human | 2 | 1108.50 | 0.00 | — | 341.18 | 306.50 | 3.72 | 1801.20 |
| 100 | threshold_0 | 2 | 1063.50 | 41.50 | 32.79 | 270.28 | 312.41 | 3.79 | 1768.76 |
| 100 | threshold_240 | 2 | 1051.50 | 45.50 | 33.28 | 301.71 | 310.17 | 3.73 | 1788.73 |

At fleet50, threshold0→240 changes mean AV occupied utilization **38.75%→38.66%**, eligible served wait **305.00→301.96s**, total completion **552.50→560.00**, and whole-fleet empty distance **1033.28→1057.23km**. These directions are measured, including adverse changes.

At fleet100, threshold0→240 changes mean AV occupied utilization **32.79%→33.28%**, eligible served wait **270.28→301.71s**, total completion **1063.50→1051.50**, and whole-fleet empty distance **1768.76→1788.73km**. These directions are measured, including adverse changes.

## Reading these comparisons

Means/ranges pool simulation seeds within a fixed city/fleet/source cohort; `paired_effects.csv` includes conditional t intervals, valid-pair counts and insufficient-pair flags. Small seed counts do not establish population or cross-city uncertainty. Every policy and seed is retained. `common_rider_effects.csv` compares identical served request IDs, while served-only aggregate wait means can change composition.

Waits/trips use evaluation request IDs and include later physical fulfillment. Occupied/idle/online time is clipped to the evaluation clock; distance includes warm-up and the completion tail. An empty-distance fraction can decrease while empty kilometers increase; inspect the absolute fleet totals. Retained-human productivity tracks the same original human slots in both replacement and all-human arms. Nearest-idle-AV proximity is not proof that an alternative full plan was feasible. No observed AV adoption, driver wage, full-day throughput, fitted unserved demand or universally superior policy is claimed.

Capacity audits check every moving load and both pre/post loads at stationary exchanges. FleetPy records a union of incoming and departing IDs during a boarding stop; its raw stationary occupancy can exceed seated capacity. `stationary_exchange_union_rows` retains those occurrences explicitly; raw records are unchanged.

## Occupied vehicle time versus passenger duration
Higher occupied utilization is not automatically more completed trips or shorter journeys. These supplementary measures use actual completed evaluation-cohort passenger pickup-to-dropoff time, including service and later fulfillment; they are passenger-level durations, while utilization is occupied vehicle time clipped to the evaluation clock. Pooling and time domains therefore prevent a direct conversion between them.
| City | Fleet | Threshold | Mean AV completed | Mean AV passenger duration s | AV duration q95 s |
| --- | --- | --- | --- | --- | --- |
| chicago | 100 | threshold_0 | 24.00 | 1570.96 | 3959.20 |
| chicago | 100 | threshold_240 | 28.00 | 1998.81 | 4341.21 |
| chicago | 200 | threshold_0 | 79.50 | 1264.33 | 3720.92 |
| chicago | 200 | threshold_240 | 56.00 | 1970.18 | 4525.65 |
| manhattan | 775 | threshold_0 | 84.50 | 1332.10 | 2490.83 |
| manhattan | 775 | threshold_240 | 133.00 | 1304.53 | 2478.41 |
| munich | 50 | threshold_0 | 25.00 | 856.03 | 1344.47 |
| munich | 50 | threshold_240 | 25.00 | 856.87 | 1420.13 |
| munich | 100 | threshold_0 | 41.50 | 850.40 | 1602.35 |
| munich | 100 | threshold_240 | 45.50 | 807.34 | 1395.05 |

Values are means of per-seed statistics, not pooled passenger quantiles. Pooling, provided traffic dynamics and limited supply can change passenger durations; these benchmarks do not establish empirical passenger acceptance or a field service-quality gain. Both favorable and adverse duration changes are retained in the supplementary CSVs.
