# Phase 2 validation evidence

- `validation.json`: actual final test outcome, commands, source digest, and
  evidence hashes; `pytest.txt` is the captured final suite output.
- `sigma-0/` and `sigma-0.3/`: actual final paired experiment manifests, four
  reports each, and copied constant/scenario configurations. The manifest
  records the common execution overrides, dependencies, source hashes, run
  commands, return codes, and matched input audits.
- `run_checks.json`: principal output hashes and booking/completion counts for
  all 12 actual simulations. For each of the six sigma-0 runs, exact comparisons
  passed against saved Phase 1 original rider columns and standard evaluation
  cells. Every booked rider completed across both noise settings.
- `sigma-0.log`, `sigma-0.3.log`: captured final evaluator console logs.

Raw simulation outputs and individual logs remain at
`/workspace/.setup/phase2/verified-sigma-{0,0.3}`. These paths refer to the
development environment; archived manifests/hashes preserve their provenance
if that environment is later replaced. Reproduction commands are in
`docs/PHASE_2.md` and the exact run commands are retained in each manifest.

These are small example-network validation runs. Noise settings were supplied
as modeling inputs. They are not fitted city parameters or general evidence
that a matching policy is superior. Error summaries are conditional on service;
consult completion counts alongside timing results.
