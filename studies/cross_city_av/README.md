# Cross-city AV comparison

Use `python -m tools.city_av build/run/report` with the configurations in
`configs/`. Dataset paths are relative to `--data-root`; private bundles and
results belong outside the repository. See the [phase guide](../../docs/PHASE_10.md)
for exact commands, controls, data provenance and interpretation.

The public source files are available from TUM Zenodo records 15195726 (Munich)
and 15189440 (Chicago). Manhattan consumes the already verified Phase 9 dataset
as input without modifying that dataset. Fleet sizes and comparison assumptions
are explicit configuration, not fitted to the held-out policy outcomes.
