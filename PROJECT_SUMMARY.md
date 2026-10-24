# Mobility simulation: implemented scope

This project extends TUM-VT/FleetPy from upstream commit
`c813728b6d188df8dd7fd5d3d36dcb0a55c898a2`.

| Phase | Delivered capability | Evidence |
| --- | --- | --- |
| 0: baseline hygiene | Independent upstream references, exact example regressions, fixes for retry/rejection/forecast handling, default debug dumps disabled | `UPSTREAM_COMPARISON.md` |
| 1: experiment reliability | Opt-in named random streams, audited paired runs, driver accounting and inequality metrics, paired statistical reports | `docs/PHASE_1.md` |
| 2: service uncertainty | Frozen accepted pickup/dropoff promises, optional per-leg execution noise, signed error reporting, delayed-commitment checks | `docs/PHASE_2.md` |
| 3: driver acceptance | Opt-in logistic decisions, bounded selected-driver retries, driver classes, probability-weighted assignment reward, decision audits | `docs/PHASE_3.md` |
| 4: future-value matching | Opt-in fallback-value rewards, exact road-ETA top-k candidates, round-scoped caching, selected-score/counter audits | `docs/PHASE_4.md` |
| 5: driver choice | Opt-in logit menus/outside option, greedy conflict resolution, committed-request protection, single-item compatibility, choice audits | `docs/PHASE_5.md` |
| 5b: ranked insertion fallback | Opt-in cheapest-first feasible driver offers, one decision per driver, cached first acceptance, terminal-exhaustion/candidate audits | `docs/PHASE_5B.md` |

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
Optimizer forbid/rematch (5c), AV dispatch,
cross-city calibration, and windowed evaluation remain later phases.

- [Change history](IMPROVEMENT_LOG.md)
- [Step-by-step work and verification record](docs/WORK_LOG.md)
- [Phase 1 commands, assumptions, and metric definitions](docs/PHASE_1.md)
- [Phase 2 execution model, timing records, and validation](docs/PHASE_2.md)
- [Phase 3 acceptance model, coefficients, retry assumptions, and validation](docs/PHASE_3.md)
- [Phase 4 fallback estimate, candidate definition, caching, and validation](docs/PHASE_4.md)
- [Phase 5 menu probabilities, compatibility modes, conflict policy, and validation](docs/PHASE_5.md)
- [Phase 5b ranked insertion, per-driver decisions, exhaustion, and validation](docs/PHASE_5B.md)
