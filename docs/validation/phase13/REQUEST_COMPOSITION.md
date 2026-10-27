# Supplementary request composition and overlap analysis

## Same AV requests, changed selection and actual overlap

The full evaluation AV passenger-time difference is independently split into time changes for request IDs served by AVs in both policies, passenger time from newly AV-served IDs, and passenger time removed with lost AV IDs. All 60 per-seed contrasts close exactly. This separates within-request changes from a changing AV trip sample; it is still conditional on each realized policy history.

| Fleet | Candidate minus control | Common AV IDs | Gained AV IDs | Lost AV IDs | Same AV duration change s | Same-served eligible wait change s |
| --- | --- | --- | --- | --- | --- | --- |
| 100 | threshold_240 minus equal_speed_240 | 9.33 | 20.00 | 35.33 | +210.88 | -1.71 |
| 100 | threshold_240 minus threshold_0 | 5.67 | 23.67 | 17.33 | -12.82 | +13.17 |
| 200 | threshold_240 minus equal_speed_240 | 29.67 | 31.00 | 66.33 | +182.97 | +1.51 |
| 200 | threshold_240 minus threshold_0 | 12.33 | 48.33 | 59.00 | +1.94 | +16.92 |

Values are means of per-seed statistics, not pooled passenger effects. Gained/lost IDs may switch between human and AV service or between service and rejection; all nine transitions remain in `product_transitions.csv`. A common-served wait contrast excludes requests served in only one arm.

| Fleet | Candidate minus control | Moving-route overlap change, passenger-hours | Stationary boarding overlap change, passenger-hours | Other overlap change, passenger-hours |
| --- | --- | --- | --- | --- |
| 100 | threshold_240 minus equal_speed_240 | -4.642 | -0.450 | +0.000 |
| 100 | threshold_240 minus threshold_0 | +1.112 | +0.069 | +0.000 |
| 200 | threshold_240 minus equal_speed_240 | -10.362 | -1.086 | +0.000 |
| 200 | threshold_240 minus threshold_0 | +1.723 | +0.114 | +0.000 |

These quantities integrate actual `(occupancy−1)` time, with zero contribution from empty/single-passenger legs. Stationary boarding includes exchange unions; moving-route overlap reflects actual simultaneous passenger load. Multi-passenger bookings also contribute. The three terms sum to the logged-overlap change and enter vehicle-time accounting with the opposite sign. No causal pooling intervention is inferred from this descriptive split.
