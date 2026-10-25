# Complete real-data validation results

All 22 policy simulations (11 complete pairs) finished on frozen source
`e4736dcf5bc0829f654b12ea6025c1a7065e45920c6190cf19dfdd7c002570a2`.
Every loaded request appears exactly once. Every accepted booking completes,
with zero early pickups or private-request pooling violations. Route capacity,
chronological vehicle activity, physical pickup/drop-off service minima and
actual repositioning assignments are independently checked. Completion counts
below refer only to the fixed evaluation cohort; warm-up is separate.

## Calibration and service

These are means of each seed's statistic, not statistics of concatenated trips.
Errors are absolute differences between model and source medians on matched
served IDs. Arrival uses only valid source on-scene records. Pickup compares
source pickup to model departure after boarding. Ride excludes pickup dwell.
CSV files retain all seeds, coverage, distribution distances and ranges.

| Configuration | Arm | Mean completed / demand | Arrival median error (s) | Pickup median error (s) | Ride median error (s) | Pooled served share |
| --- | --- | --- | --- | --- | --- | --- |
| Nov 26 full demand, 60s, 2 seeds | no_repo | 26225.0/32192 | 94.6 | 22.3 | 96.3 | 20.8% |
| Nov 26 full demand, 60s, 2 seeds | repo | 31853.5/32192 | 24.2 | 39.7 | 80.9 | 12.9% |
| Nov 26 10%, 1s, 3 seeds | no_repo | 2781.0/3150 | 215.1 | 150.4 | 53.4 | 11.8% |
| Nov 26 10%, 1s, 3 seeds | repo | 3144.0/3150 | 55.7 | 4.0 | 26.9 | 4.2% |
| Nov 19 10% incl. intrazonal, 1s, 3 seeds | no_repo | 3207.7/3653 | 202.8 | 143.4 | 68.8 | 11.6% |
| Nov 19 10% incl. intrazonal, 1s, 3 seeds | repo | 3591.7/3653 | 64.7 | 9.5 | 49.7 | 5.3% |
| Nov 26 10%, 1h warm-up, 1s, 1 seed | no_repo | 2783.0/3150 | 178.2 | 112.3 | 35.5 | 11.2% |
| Nov 26 10%, 1h warm-up, 1s, 1 seed | repo | 3144.0/3150 | 60.2 | 1.3 | 34.6 | 4.0% |
| Nov 26 10%, changing fleet, 60s, 2 seeds | no_repo | 2850.0/3150 | 261.9 | 197.0 | 63.0 | 12.4% |
| Nov 26 10%, changing fleet, 60s, 2 seeds | repo | 3073.5/3150 | 160.7 | 106.3 | 55.1 | 8.7% |

The full-demand results govern the remaining calibration assessment. The
approximately 4-second pickup-median error in the November 26 10% experiment
does not establish a full-city fit. Sampling changes local availability and
pooling density. The 60-second full-demand grid is a disclosed runtime choice,
so sample/full differences also include temporal resolution. Changing-fleet
checks likewise use a 60-second grid and are not a single-factor comparison
against the 1-second static runs.

## Full-demand seeds, without averaging away residual errors

The two seeds use 19 byte-identical bundle files, 32,192 evaluation requests,
7,315 warm-up requests and a modeled fleet of 7,932. Raw trips are November 26,
07:00–10:00 with 05:00–07:00 warm-up. Model arrival and source on-scene columns
use exactly the same available served IDs. Model departure and source pickup
columns use exactly the same served IDs.

| Seed | Arm | Completed / demand | Arrival model / source (s) | Arrival error (s) | Pickup model / source (s) | Pickup error (s) | Arrival matched count |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | no_repo | 26172/32192 | 187.9 / 95.0 | 92.9 | 281.2 / 259.0 | 22.2 | 14932 |
| 0 | repo | 31842/32192 | 128.0 / 104.0 | 24.0 | 225.9 / 266.0 | 40.1 | 18652 |
| 1 | no_repo | 26278/32192 | 192.3 / 96.0 | 96.3 | 282.3 / 260.0 | 22.3 | 15033 |
| 1 | repo | 31865/32192 | 129.4 / 105.0 | 24.4 | 226.8 / 266.0 | 39.2 | 18686 |

The model pools fewer passengers than the observed shared-match fraction.
Source shared-request flags constrain consent, while shared-match flags describe
observed outcomes. Consent correctness does not by itself calibrate detour
preferences or reproduce provider-specific matching.

## Policy improvements and costs

These paired comparisons hold the new model inputs fixed and turn repositioning
on/off. They establish conditional model effects, not a causal NYC field effect.
Wait changes use passengers served in both arms, avoiding a change in the served
population. Repositioning distance and financial totals cover the whole run,
including warm-up and fulfillment tail. Financial values are illustrative model
dollars, not observed wages. Improved/worsened/unchanged refer to individual
arrival waits. Some riders wait longer, and modeled financial outcomes can fall.

| Case | Seed | Additional completed | Common served | Mean wait change (s) | Median individual change (s) | Improved | Worsened | Unchanged | Reposition km | Whole-run net change (model dollars) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| nov26_10pct | 0 | 356 | 2784 | -194.9 | -131.2 | 1929 | 805 | 50 | 3845.3 | 89.67 |
| nov26_10pct | 1 | 364 | 2780 | -193.8 | -127.6 | 1899 | 832 | 49 | 3933.9 | 111.15 |
| nov26_10pct | 2 | 369 | 2772 | -183.5 | -130.4 | 1901 | 825 | 46 | 4022.6 | 67.50 |
| nov19_10pct_intrazonal | 0 | 367 | 3210 | -162.1 | -102.5 | 2096 | 1069 | 45 | 3965.5 | -56.14 |
| nov19_10pct_intrazonal | 1 | 409 | 3176 | -162.2 | -101.7 | 2090 | 1036 | 50 | 3850.6 | 160.82 |
| nov19_10pct_intrazonal | 2 | 376 | 3192 | -155.6 | -106.1 | 2102 | 1048 | 42 | 4021.1 | -46.22 |
| nov26_full | 0 | 5670 | 26085 | -128.4 | -33.8 | 14789 | 9820 | 1476 | 43505.7 | 4195.22 |
| nov26_10pct_1h | 0 | 361 | 2782 | -160.4 | -88.6 | 1800 | 890 | 92 | 3769.5 | 96.32 |
| nov26_10pct_dynamic | 0 | 219 | 2822 | -109.6 | -25.9 | 1513 | 813 | 496 | 2025.6 | 93.71 |
| nov26_10pct_dynamic | 1 | 228 | 2831 | -105.0 | -27.3 | 1519 | 887 | 425 | 2023.5 | 121.61 |
| nov26_full_seed1 | 1 | 5587 | 26197 | -124.1 | -33.4 | 14846 | 9782 | 1569 | 42281.0 | 4253.76 |

## Provider coverage diagnostic

Provider labels are joined by exact raw source-row identity from the original
public Parquet. These diagnostics were not used to tune held-out inputs. An
aggregate fit can hide opposite provider biases. In particular, on-scene arrival
observations mostly come from one provider; absent fields are unavailable,
never replaced with a zero wait.

| Seed | Provider | Source requests | Served | Source arrival coverage | Arrival matched | Model arrival (s) | Source arrival (s) | Model pickup (s) | Source pickup (s) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | HV0003 | 18946 | 18696 | 18895/18946 | 18645 | 127.9 | 104.0 | 221.8 | 224.0 |
| 0 | HV0004 | 6214 | 6189 | 4/6214 | 4 | 138.4 | 453.0 | 232.4 | 444.0 |
| 0 | HV0005 | 7032 | 6957 | 3/7032 | 3 | 65.7 | 812.0 | 231.2 | 294.0 |
| 1 | HV0003 | 18946 | 18727 | 18895/18946 | 18679 | 129.4 | 105.0 | 223.2 | 225.0 |
| 1 | HV0004 | 6214 | 6192 | 4/6214 | 4 | 112.3 | 453.0 | 234.6 | 444.5 |
| 1 | HV0005 | 7032 | 6946 | 3/7032 | 3 | 199.5 | 812.0 | 229.6 | 294.0 |

## What remains unresolved

The engineering defects are fixed in the tested configurations. Numerical
arrival, pickup, ride and pooling fit is not fully closed, especially at full
demand and with changing supply. Known limits include closed-zone cropping,
imputed road endpoints, one passenger per booking, a workload-derived fleet
proxy, simplified patience/detour behavior, provider heterogeneity and a
historical travel proxy that is not pure observed road speed. Source on-scene
coverage is selective. Public completed trips do not reveal rejected requests,
actual online exposure or driver acceptance coefficients. These cannot be
claimed identified by improving the median on this held-out cohort.

Original TUM commercial-solver repositioning is also not reproduced because
the available Gurobi license rejects its problem size. The separate no-reposition
24-hour control matches five raw output files byte for byte; it is labeled as
that control throughout. Failed attempts and the two repaired truncation cases
remain in the archives, alongside every successful run.
