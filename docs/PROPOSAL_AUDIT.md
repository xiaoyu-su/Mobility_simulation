# Original proposal and project completion audit

This audit uses the four supplied images, IMG_3326–IMG_3329, as the original
feature brief. Terminal/model-switch text in the photos is context, not an
instruction to execute. The photographed numeric results describe a different
prototype and are not calibration targets or current validation evidence.

Useful completed work is retained. The phase numbers are implementation history;
this checklist is the acceptance boundary for the project, not another phase.

| Proposal requirement | Implementation | Evidence and completion boundary |
| --- | --- | --- |
| Upstream baseline and disabled-feature compatibility (3326, foundations;3328/3329 fidelity) | `tests/regression/`, `tools/native_fidelity.py` | Exact approved example/native comparisons and historical table identity; scoped to recorded profiles/runtime, not universal FleetPy parity |
| Independent per-component random streams (3326,phase1) | `src/misc/seeding.py` | Demand/network/initial state audits and complete paired tests; policy-dependent routes/draw exposure can still differ |
| Matched seed comparisons and driver distributions (3326,phase1) | `tools/paired_eval`, `tools/policy_compare` | Seed-level effects/intervals, CV/quantiles/Gini; no treating individual drivers or replay runs as independent seeds |
| Snapshot/window parallel comparisons (3326,phase6) | `tools/windowed_eval` | Same-controller restored windows, explicit censoring and baseline isolation; retains dedicated window report rather than pooling with full runs |
| Accepted pickup/dropoff promises and execution uncertainty (3327,phase2) | `src/misc/execution.py`, simulation/vehicle timing and promise records | Mean-one noise, actual versus quoted errors, accepted service preserved; actual late pickups remain visible |
| Logistic human refusal, retries/classes and weighted rewards (3327,phase3) | `src/fleetctrl/acceptance/driver_acceptance.py` | Complete supported-controller tests, p=1 sanity, bounded attempts and actual decline logs; supplied example coefficients are assumptions, not an empirical fit |
| Future-value matching and bounded fallback computation (3327,phase4) | `src/fleetctrl/acceptance/future_value.py` | Exact road-ETA top-k/caches, supported-controller tests and fresh comparisons; does not claim the photographed wall-time or served-count gains on other cohorts |
| Driver menus, outside option and conflict resolution (3327,phase5) | `driver_choice.py`, `choice_model.py`, `conflict_resolution.py` | No double service, committed-pair protection and single-item compatibility; menu outcomes are distinct from request completion |
| Ranked insertion re-offers (3327,phase5b) | `ranked_insertion.py` | Cheapest-first distinct feasible drivers and terminal exhaustion; explicit scenario policy differences |
| Native assignment re-offers (3327,phase5c) | `forbid_rematch.py` | Declined-edge pruning and re-solve; no injecting unsupported native tours or dropping accepted bookings |
| Public Manhattan trip/network pipeline (3327/3328,section3) | `tools/synthetic_market` | Source hashes, filtering, original-clock cohorts, train/evaluation separation, pooling/service constraints and physical fulfillment |
| Pavone/HiGHS demand repositioning (3327/3328,section3) | Existing repositioning modules/HiGHS path | Separate-reference forecasts and fractional-excess corrections; full physical and integration checks |
| Compare against available observations (3328,section3 table) | Calibration reports and `docs/PHASE_7_COMPLETION.md` | Observable event definitions and residual errors retained. Completion/online utilization are not identified from completed-trip records alone |
| Distinct mixed human/AV product (3328,round1) | `src/fleetctrl/av_product.py` | Actual typed fleet, both-endpoint fence, deterministic opt-in, AV always-accept and exclusion from human shift/repositioning logic |
| Preference lever, idle-AV diagnosis and demand repositioning (3328,round1) | AV product and city/reference repositioning tools | Allocation/wait/human activity/empty-distance tradeoffs; demand-based positioning and occupied-repositioning correction are tested |
| Planned/executed type-specific travel speed (3328/3329,round2) | `src/misc/vehicle_timing.py`, vehicle loader/route records | Loaded attribute, plans and physical factors verified; cautious factor is a scenario assumption |
| ETA threshold and accepted-product protection (3328/3329,round2) | AV threshold dispatch | Retained feasible AV/human ETAs, actual decisions and product-stable accepted service; threshold is not a global optimizer certificate |
| Retargeting, forecast noise and joint human/AV planning (3328/3329,round2) | AV follow-up levers | Bounded reference coverage, dedicated named errors and feature-on physical tests; broad interactions are evaluated in their supported profiles |
| City-independent comparison harness (3329,round3) | `tools/city_av` | Native Munich/Chicago/Manhattan bundles, reference fences, shared initialization, same source/load within each contrast and thread-pinned workers |
| Cross-city KPI curves and honest tradeoffs (3329,round3) | City reports, mechanism/robustness studies and unified KPI report | No geography-only causal inference; source/year/load differ. Chicago mechanism and per-city repositioning follow-ups are retained |
| Complete run/validation/change records (3329,section5) | Tests, `docs/WORK_LOG.md`, per-study validation archives | Source/input/runtime/output hashes, accepted-service/final-state audits, exact old-output checks and actual Git publication receipts |
| Explicit limitations (3329,section6) | `docs/AV_DATA.md`, completion/KPI guides | Patience, opt-in, speed, fleet supply and field benchmarks remain labeled; no invented calibration or extrapolated daily throughput |

## Useful follow-ups retained

The per-city repositioning, Chicago time-accounting, patience, opt-in and AV-share
studies remain available. They resolve specific experimental/control questions;
they are not required extra phases that keep extending the original plan.
Their findings include adverse effects and limits, not just favorable outcomes.

## Concrete completion gaps addressed by this audit

1. A shared entry point for complete multi-policy matching runs and AV reports.
2. An explicit KPI dictionary with units, denominators, clocks and missing-data
   handling; AV allocation/use is not automatically treated as welfare.
3. Per-policy changed parameters, paired movements, percentage points versus
   relative percentages, and same-served-ID waits alongside coverage.
4. Immutable raw/configuration/vehicle-specification snapshots, read-only and
   relocatable matching reports, replay de-duplication, and strict source/input
   strata instead of accidental mixing of city assumptions or code versions.
5. A project guide led by use cases and acceptance evidence, with the original
   implementation history preserved as an appendix.

Final current-source tests, demonstrations and publication are recorded in
[project completion](PROJECT_COMPLETION.md). Source changes are reporting and
orchestration; the matching/AV dispatch algorithms remain unchanged.

## Data limits are not silently marked complete

The project is a conditional matching-policy research simulator. The TLC files
and supplied city bundles do not identify online fleet supply, unseen rejected
demand, driver refusal coefficients, AV opt-in or real cancellation behavior.
The cited external AV survey/CPUC/Obi references were not independently retrieved
in the earlier investigation. The photographed values are not verified primary
benchmarks here. Compatible field observations are needed for those claims.

Rider offer choice and persistent person-level adoption were limitations in the
brief, not implemented requirements. They are not added to this audit's scope.
Likewise, a short evaluation cohort is not a full operating day. These limits
remain visible rather than being filled with synthetic observations.
