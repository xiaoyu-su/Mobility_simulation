# Phase 5 validation evidence

- `validation.json`, `pytest.txt`: final test outcome, source digest, and evidence hashes.
- `run_checks.json`: return codes, request/completion checks, unique winners,
  saved-control comparisons, and output hashes for all 12 final simulations.
- `singleton/` and `batch-menus/`: actual paired manifests, configuration
  snapshots, statistical/driver reports, and evaluator console output.
- Each `runs/seed_N/{baseline,candidate}/` preserves complete raw CSV/JSON
  records: riders, vehicle activity, final state, input/class audits, acceptance
  decisions, console/simulation logs, and enabled choice probabilities,
  intervals/draws, outcomes, and final counters.
- `checkpoints/`: starting/prior-unit results, the output-suppression failure,
  corrected full examples, the batch wait-window validation failure and its
  correction, the first 179-test full run, and explicit-off round-trip checks.

Both experiments use seeds 0/1/2 and common sigma 0.3. All six input-pairing
audits match, and every accepted booking completes. Singleton mode exactly
preserves the original rider/evaluation/decision tables, including the saved
pre-Phase-5 control records. Repeating the final experiments after the disabled
flag-decoding fix leaves all valid-mode outcomes unchanged.

Actual batch menus complete 53.00 trips on average versus 54.67 for the
single-attempt control, with mean served-rider wait 136.30s versus 125.02s.
This is not a service improvement. Seeds 0/1/2 exercise 3/3/4 multi-item
episodes; each driver episode chooses at most one new request. Offered-item
rejections are not independent-driver refusal counts.

Live solver request ownership is already disjoint, so actual cross-driver
conflict rejections are zero here. Explicit overlapping-driver, protected
request, tie, order-invariance, and cross-episode cases test the generic
resolver separately. Ranked driver fallback (5b) and optimizer forbid/rematch
(5c) remain later phases.

Original final artifacts remain under
`/workspace/.setup/phase5/verified-v2-singleton` and
`/workspace/.setup/phase5/verified-v2-batch-menus`. Archived provenance retains
those original paths; the earlier first-run directories are preserved separately.
Configuration and assumptions: `docs/PHASE_5.md`. Full changes, reasons,
benefits, corrections, verification, and publication: `docs/WORK_LOG.md`.
