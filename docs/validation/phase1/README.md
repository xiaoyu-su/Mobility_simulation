# Phase 1 development validation artifacts

These files are actual outputs from the final development verification, not
targets or results copied from the source screenshots.

- `validation.json`: final test command/outcome, scope, demonstration summary,
  and hashes of the archived artifacts.
- `manifest.json`: the CLI's complete experiment record, including working-code
  fingerprints, dependency versions, configuration hashes, commands and exit
  codes, matched input audits, and report hashes.
- `per_driver.csv`, `driver_distribution.csv`, `seed_summary.csv`, and
  `paired_comparison.csv`: unedited CLI-generated reports.

The demonstration compares the bundled insertion and immediate/batch matching
examples at seeds 0, 1, and 2. All six simulations completed and all three pairs
had identical recorded exogenous inputs and initial fleets. It is a small
pipeline validation, not a general claim that one policy is superior.

Full raw simulation outputs and worker logs remain at the local artifact path
recorded in the manifest. Those absolute paths identify this development run;
they are not portable dependencies. Reproduction commands and definitions are
in `../../PHASE_1.md`, and the development history is in `../../WORK_LOG.md`.
