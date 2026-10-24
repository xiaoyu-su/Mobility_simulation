# Development and validation requirements

The user requires real end-to-end simulation checks for every change to
simulation code or scenario configuration. Unit tests alone do not establish
that a new feature works in the simulation.

- After each behavior change, run a complete affected scenario with the changed
  feature enabled. Exercise each affected matching controller and relevant
  combinations with existing features. Include disabled/default compatibility
  and deterministic boundaries when they apply.
- Check actual outputs: full demand accounting with unique request IDs, final
  state and evaluation files, chronological vehicle activity, completed accepted
  bookings, and absence of service for terminally rejected requests. Verify that
  the intended feature was exercised through its audit/decision records.
  A zero exit code alone is insufficient.
- For stochastic behavior, preserve fixed seeds and matched background inputs;
  check reproducibility and control/candidate compatibility where required.
- Before declaring a phase complete, run `.venv/bin/python -m pytest -q`, which
  includes complete regression and integration simulations. Investigate failures
  and report failed, skipped, and unrun checks explicitly.
- Keep Python source unchanged while full simulations or paired experiments
  run. The paired evaluation pipeline fingerprints the source and rejects
  changes during execution.
- Record each step in `docs/WORK_LOG.md`: what changed, why, intended benefit,
  exact commands, configurations, seeds, results, failures and fixes, and
  evidence locations. Preserve existing evidence and source/input/output hashes.
- Distinguish a successfully executed simulation from a policy improvement.
  Report actual outcomes even when a feature reduces service performance.

Use **Xiaoyu Su** and
`209944670+xiaoyu-su@users.noreply.github.com` as both Git author and committer.
Preserve existing local work; do not create Git worktrees unless the user asks.
