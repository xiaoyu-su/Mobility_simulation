# Mobility simulation: implemented scope

This project extends TUM-VT/FleetPy from upstream commit
`c813728b6d188df8dd7fd5d3d36dcb0a55c898a2`.

The current user-facing product is a matching-policy comparison simulator with
human/AV allocation diagnostics. The [completion review](docs/PROJECT_COMPLETION.md)
reconciles the original proposals, tests and remaining empirical limits. Use the
[comparison workflow](docs/POLICY_COMPARISON.md) and [KPI guide](docs/KPI_GUIDE.md)
to run policies and interpret movements. Completed studies below remain evidence;
this review does not add another numbered phase.

| Phase | Delivered capability | Evidence |
| --- | --- | --- |
| 0: baseline hygiene | Independent upstream references, exact example regressions, fixes for retry/rejection/forecast handling, default debug dumps disabled | `UPSTREAM_COMPARISON.md` |
| 1: experiment reliability | Opt-in named random streams, audited paired runs, driver accounting and inequality metrics, paired statistical reports | `docs/PHASE_1.md` |
| 2: service uncertainty | Frozen accepted pickup/dropoff promises, optional per-leg execution noise, signed error reporting, delayed-commitment checks | `docs/PHASE_2.md` |
| 3: driver acceptance | Opt-in logistic decisions, bounded selected-driver retries, driver classes, probability-weighted assignment reward, decision audits | `docs/PHASE_3.md` |
| 4: future-value matching | Opt-in fallback-value rewards, exact road-ETA top-k candidates, round-scoped caching, selected-score/counter audits | `docs/PHASE_4.md` |
| 5: driver choice | Opt-in logit menus/outside option, greedy conflict resolution, committed-request protection, single-item compatibility, choice audits | `docs/PHASE_5.md` |
| 5b: ranked insertion fallback | Opt-in cheapest-first feasible driver offers, one decision per driver, cached first acceptance, terminal-exhaustion/candidate audits | `docs/PHASE_5B.md` |
| 5c: native optimizer rematching | Opt-in declined-edge/trip pruning, same-tick Gurobi re-solves, accepted-pair protection, logit round capacity, genuine-attempt terminal audits | `docs/PHASE_5C.md` |
| 6: windowed parallel evaluation | Full baseline snapshots, same-controller interventions, bounded isolated workers, disjoint request cohorts and explicit horizon censoring | `docs/PHASE_6.md` |
| 7: market-data pipeline | Verified public Manhattan inputs, causal requests, source pooling consent, fitted pickup service, physical completion and event-aligned reports; 327 passing tests and full-demand comparisons; residual calibration errors reported | `docs/PHASE_7.md`, `docs/PHASE_7_COMPLETION.md` |
| 8: mixed human/AV product | Loaded AV vehicle types, geofenced/opt-in service, rider-second preference, human-operation separation, idle diagnostics and historical-demand AV repositioning; 339 passing tests, 18 sampled real policy runs and exact historical compatibility retain benefits and costs | `docs/PHASE_8.md` |
| 9: cautious AV policy experiments | Consistent planned/executed vehicle-type travel times, ETA-threshold dispatch with accepted-product protection, moving-empty retargeting, isolated forecast noise and bounded joint demand accounting; 370 passing tests, 56 real physical runs, six-seed dispatch comparisons and a full-demand pair | `docs/PHASE_9.md`, `docs/AV_DATA.md` |
| 10: cross-city AV comparison | Native Munich/Chicago/Manhattan inputs, matched all-human/AV initialization and search, bounded CPU workers, audited policy/load comparisons; 389 passing tests, 66 physical runs /60 unique conditions; mixed policy transfer | `docs/PHASE_10.md` |
| 11: native fidelity validation | Fresh upstream archive and isolated imports, original city profiles, four-table exact comparison, repeatability and clean published-source reproduction; 403 tests /269 regression simulations /15 native runs; validation improvement, unchanged policies | `docs/PHASE_11.md` |
| 12: cross-city AV repositioning | Strictly separate reference OD weights, empty AV movement contracts, opt-in pre-booking service priority, paired off/on/supply experiments; 424 tests, 306 regression simulations, 72 real runs /63 conditions; gains and adverse outcomes retained | `docs/PHASE_12.md` |
| 13: Chicago mechanism diagnostics | Read-only exact occupied/passenger-time bridges, symmetric count/duration accounting, same-request and selection/overlap diagnostics; 433 tests, 324 regression simulations, 64 real runs /54 unique conditions; all prior policy source unchanged | `docs/PHASE_13.md` |
| 14: booking-patience robustness | Explicit 4/8/12-minute strata, source-clock offer bounds, actual lateness and fixed 480s service target; compatible-input guards, 442 tests, 360 regression simulations, 90 physical records /81 unique conditions; no matching-policy change | `docs/PHASE_14.md` |
| 15: rider opt-in robustness | Nested0/30/100% request eligibility, fixed-group allocation/spillovers, all-human invariance, zero-boundary equivalence and paired same-ID effects; 452 tests, 396 regression simulations, 90 physical records /81 unique conditions; all269 previous source files unchanged | `docs/PHASE_15.md` |
| 16: AV fleet-share robustness | Fixed-total-fleet5/10/20% replacement, optional common geometry, actual-type search controls, fixed-human-ID activity, physical legacy bridge and adjusted responses;465 tests,441 regression simulations,99 physical records /90 settings | `docs/PHASE_16.md` |

Defaults retain upstream random behavior. New independent-stream mode is
explicit and currently scoped to single-worker baseline matching experiments.
The approved Phase 0 CSV references are unchanged.

Phase 1 improves the credibility and reproducibility of comparisons. It does
not establish a new matching policy's superiority or model observed driver wages.
Phase 2 separates quoted service times from uncertain executed driving times.
Phase 3 adds configurable driver acceptance while preserving committed riders.
Phase 4 estimates alternative-driver fallback in the matching reward.
Phase 5 adds the choice/conflict layer and solver-selected driver menus.
Phase 5b dispatches declined insertion requests to later feasible drivers.
Phase 5c lets the native batch optimizer find another driver after refusals.
Phase 6 compares local policy interventions from identical baseline histories
without repeating every lead-in. Phase 10 supplies the cross-city benchmark.
Phase 7 prepares reproducible market inputs and adds license-free repositioning;
the public TLC/Zenodo inputs are available and verified. Production corrections
enforce source-clock timing, source pooling consent, physical pickup/drop-off
service and complete bookings, and add spatial/warm-up controls with matched
event reporting. Full-demand validation measures the remaining calibration
errors; public completed trips do not identify online supply or unserved demand.
See the [completion evidence](docs/PHASE_7_COMPLETION.md) and preserved
[earlier investigation](docs/REAL_MANHATTAN_INVESTIGATION.md).
Phase 8 separates AVs from human shift/acceptance/repositioning rules and
compares allocation policies with a fixed total fleet. In the sampled Manhattan
experiment, stronger AV preference plus AV repositioning increases AV trip share
and utilization while reducing human trips and increasing empty driving. These
are conditional model effects, with synthetic adoption and service-area assumptions.
Phase 9 applies cautious type-specific travel times consistently to planning and
physical execution. Its threshold compares retained feasible AV/human pickup
ETAs and preserves the accepted service product during reoptimization. Experiments
retain completion, rider waits, human trip transfers and empty-distance outcomes;
the opt-in, speed and supply assumptions do not establish field AV benefits.

- [Change history](IMPROVEMENT_LOG.md)
- [Step-by-step work and verification record](docs/WORK_LOG.md)
- [Phase 1 commands, assumptions, and metric definitions](docs/PHASE_1.md)
- [Phase 2 execution model, timing records, and validation](docs/PHASE_2.md)
- [Phase 3 acceptance model, coefficients, retry assumptions, and validation](docs/PHASE_3.md)
- [Phase 4 fallback estimate, candidate definition, caching, and validation](docs/PHASE_4.md)
- [Phase 5 menu probabilities, compatibility modes, conflict policy, and validation](docs/PHASE_5.md)
- [Phase 5b ranked insertion, per-driver decisions, exhaustion, and validation](docs/PHASE_5B.md)
- [Phase 5c native graph constraints, rematching, accepted-pair protection, and validation](docs/PHASE_5C.md)
- [Phase 6 snapshots, window cohorts, parallel workers, and interpretation](docs/PHASE_6.md)
- [Phase 7 market inputs, HiGHS repositioning, calibration limits and data requirements](docs/PHASE_7.md)
- [Phase 7 production corrections, full-demand results and remaining limits](docs/PHASE_7_COMPLETION.md)
- [Phase 8 mixed-fleet rules, complete policy experiments and tradeoffs](docs/PHASE_8.md)
- [Phase 9 cautious AV timing, threshold dispatch and repositioning experiments](docs/PHASE_9.md)
- [Observed AV study inputs, scenario assumptions and benchmark boundaries](docs/AV_DATA.md)


Phase 10 validates the same policy levers against three native city datasets.
All234 historical physical cases retain1171 byte-identical checked tables;
32 restored windows retain128 exact tables. Chicago and Manhattan AV utilization
increase under threshold240 versus0 in the main fleets, while Munich is stable.
Higher utilization can coincide with fewer trips and longer passenger journeys;
completion gains reverse under the doubled-fleet sensitivity. These conditional
benchmark results do not establish field AV benefits or a geography-only effect.
See [Phase 10](docs/PHASE_10.md) and [complete results](docs/validation/phase10/RESULTS.md).


Phase11 expands original-output parity from the bundled examples to complete
native Munich, Chicago and Manhattan profiles. It compares all four physical
output tables, verifies actual booking completion, source/runtime/input isolation
and repeats each source in a fresh process. A clean published archive reproduces
the same outputs. Both sides use explicit matched no-repositioning/native-router/
no-timeout adaptations; these checks do not establish universal upstream parity
or a new policy gain. See [Phase11](docs/PHASE_11.md) and
[measured results](docs/validation/phase11/RESULTS.md).


Phase 12 positions idle AVs using separate-reference eligible OD weights and
clears cancellable empty goals before passenger ETA/cost evaluation. The real
pilot detects eight occupied repositioning legs; the corrected policy records
zero, with all accepted bookings complete. Locked work and legacy defaults remain
preserved. Main/supply experiments retain paired three-seed completion, waits,
human allocation, absolute empty driving and actual passenger durations.
See [Phase12](docs/PHASE_12.md) and [complete results](docs/validation/phase12/RESULTS.md).


Phase 13 diagnoses Chicago's non-monotone threshold/speed outcomes with exact
physical accounting. It separates evaluation-cohort trip count/duration,
window boundaries, warm-up carry-in, alighting dwell and logged overlap. The
supplementary analysis separates the same AV request IDs from gained/lost AV
selection and actual moving overlap from stationary boarding unions. All earlier
simulation source and policy defaults are unchanged. The recorded components
are algebraic contributions, not identified causal mediators or field benefits.
See [Phase 13](docs/PHASE_13.md) and [results](docs/validation/phase13/RESULTS.md).


Phase 14 measures whether city policy conclusions survive an unverified
booking-patience assumption. Controlled source/geometry/runtime inputs remain
fixed while deadline and max-wait parameters change. Offered limits, actual
lateness and service within a fixed 480-second target are reported separately.
The ordinary summary rejects incompatible assumptions. All prior non-summary
source and matching policies remain unchanged. See [Phase 14](docs/PHASE_14.md)
and [robustness results](docs/validation/phase14/ROBUSTNESS.md).
