# Mobility simulation: implemented scope

This project extends TUM-VT/FleetPy from upstream commit
`c813728b6d188df8dd7fd5d3d36dcb0a55c898a2`.

| Phase | Delivered capability | Evidence |
| --- | --- | --- |
| 0: baseline hygiene | Independent upstream references, exact example regressions, fixes for retry/rejection/forecast handling, default debug dumps disabled | `UPSTREAM_COMPARISON.md` |
| 1: experiment reliability | Opt-in named random streams, audited paired runs, driver accounting and inequality metrics, paired statistical reports | `docs/PHASE_1.md` |
| 2: service uncertainty | Frozen accepted pickup/dropoff promises, optional per-leg execution noise, signed error reporting, delayed-commitment checks | `docs/PHASE_2.md` |

Defaults retain upstream random behavior. New independent-stream mode is
explicit and currently scoped to single-worker baseline matching experiments.
The approved Phase 0 CSV references are unchanged.

Phase 1 improves the credibility and reproducibility of comparisons. It does
not establish a new matching policy's superiority or model observed driver wages.
Phase 2 separates quoted service times from uncertain executed driving times.
Driver acceptance, AV dispatch, cross-city calibration, and windowed evaluation
remain later phases.

- [Change history](IMPROVEMENT_LOG.md)
- [Step-by-step work and verification record](docs/WORK_LOG.md)
- [Phase 1 commands, assumptions, and metric definitions](docs/PHASE_1.md)
- [Phase 2 execution model, timing records, and validation](docs/PHASE_2.md)
