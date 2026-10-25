# Full fixed-cohort results

All rows use the same 3,150 source trip IDs. Successful individual arms of failed pairs remain in the CSV with pair_status=failed and are not valid paired policy evidence. Arrival error compares served IDs with valid source on-scene records; departure error compares the served source pickup cohort. Early source-clock service invalidates floor-based benchmarks. Values below are rounded; the CSV retains full precision.

| case | arm | completed | raw_wait_negative_count | raw_wait_median_s | arrival_median_abs_error_s | boarding_departure_wait_median_s | pickup_total_median_abs_error_s | post_boarding_ride_median_s | model_pooled_share_served |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline | no_repo | 3039 | 1411 | 18.79 | 105.00 | 48.79 | 219.21 | 1113.55 | 0.56 |
| baseline | repo | 3147 | 2031 | -13.00 | 128.00 | 17.00 | 248.00 | 1087.79 | 0.42 |
| clock_1s | no_repo | 3047 | 0 | 50.01 | 64.03 | 80.01 | 187.99 | 1099.94 | 0.48 |
| uniform_ceil_60s | no_repo | 3031 | 0 | 198.04 | 81.27 | 228.04 | 39.96 | 1177.14 | 0.52 |
| uniform_ceil_60s | repo | 3140 | 0 | 173.19 | 53.06 | 203.19 | 61.81 | 1132.67 | 0.41 |
| uniform_ceil_60s_train_curb | no_repo | 3000 | 0 | 217.99 | 103.02 | 311.99 | 43.99 | 1157.19 | 0.46 |
| uniform_ceil_60s_train_curb | repo | 3128 | 0 | 180.28 | 61.56 | 274.28 | 8.28 | 1103.34 | 0.30 |
| uniform_clock_1s | no_repo | 3059 | 0 | 149.85 | 38.86 | 179.85 | 87.15 | 1150.49 | 0.47 |
| uniform_clock_1s | repo | 3138 | 0 | 127.06 | 11.41 | 157.06 | 107.94 | 1117.04 | 0.33 |
| uniform_clock_1s_train_curb | no_repo | 3031 | 0 | 160.90 | 47.07 | 254.90 | 13.10 | 1179.91 | 0.40 |
| uniform_clock_warmup_1h | no_repo | 3021 | 0 | 177.74 | 58.63 | 207.74 | 59.26 | 1185.33 | 0.53 |
| uniform_clock_warmup_1h | repo | 3141 | 0 | 134.51 | 18.27 | 164.51 | 100.49 | 1111.08 | 0.33 |
| uniform_clock_warmup_2h | no_repo | 3016 | 0 | 203.76 | 76.64 | 233.76 | 35.24 | 1178.40 | 0.56 |
| uniform_clock_warmup_2h | repo | 3144 | 0 | 135.00 | 20.45 | 165.00 | 100.00 | 1098.07 | 0.33 |
| uniform_clock_warmup_2h_dynamic_typed | no_repo | 3051 | 0 | 215.44 | 91.83 | 245.44 | 22.56 | 1203.91 | 0.57 |
| uniform_clock_warmup_2h_dynamic_typed | repo | 3136 | 0 | 169.15 | 52.87 | 199.15 | 65.85 | 1154.67 | 0.40 |
| uniform_requests | no_repo | 3047 | 217 | 174.24 | 54.90 | 204.24 | 64.76 | 1189.15 | 0.54 |
| uniform_requests | repo | 3138 | 256 | 139.64 | 22.37 | 169.64 | 95.36 | 1141.51 | 0.42 |
| uniform_requests_initial | no_repo | 3052 | 396 | 142.75 | 21.99 | 172.75 | 94.75 | 1202.40 | 0.53 |
| uniform_requests_initial | repo | 3140 | 363 | 120.06 | 4.56 | 150.06 | 114.94 | 1134.81 | 0.43 |
| uniform_single | no_repo | 2720 | 366 | 174.90 | 48.58 | 204.90 | 71.10 | 1010.35 | 0.00 |
| uniform_single | repo | 3102 | 368 | 127.67 | 11.74 | 157.67 | 108.83 | 1026.90 | 0.00 |
| uniform_single_clock_1s | no_repo | 2733 | 0 | 197.08 | 70.75 | 227.08 | 48.92 | 1027.26 | 0.00 |
| uniform_single_clock_1s | repo | 3094 | 0 | 166.55 | 49.23 | 196.55 | 70.95 | 1039.61 | 0.00 |
