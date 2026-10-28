# Comparing matching policies and AV allocation

Use the shared comparison tool for full matching runs and sealed city AV
experiments. It reports conditional policy movements on matched inputs; it does
not select a best policy from a single score.

## Run a complete multi-policy example

From the repository root, activate your installed environment (`source .venv/bin/activate`
in the prepared cloud workspace, or `conda activate fleetpy` after the README
installation). The commands use that environment's `python`; native optimization
requires Gurobi.

```bash
python -m tools.policy_compare run \
  --spec studies/policy_comparison/insertion.json \
  --output /tmp/my_matching_comparison
```

The specification compares acceptance-weighted insertion with future value,
ranked fallback and their combination. The output includes full worker runs,
sealed scenario/vehicle-cost snapshots, policy differences and `report/`.
Other supplied specifications exercise immediate insertion with batch
reoptimization and native Alonso–Mora assignment:

```bash
python -m tools.policy_compare run \
  --spec studies/policy_comparison/immediate_batch.json \
  --output /tmp/my_immediate_batch_comparison

python -m tools.policy_compare run \
  --spec studies/policy_comparison/alonso_mora.json \
  --output /tmp/my_assignment_comparison
```

Each uses three fixed seeds and illustrative driver coefficients with the same
execution-noise assumption in each arm. These examples demonstrate comparison
mechanisms, not fitted marketplace behavior. Some candidates change more than
one operator option; `policy_differences` and `policy_parameters.json` disclose
those changes. Use new output directories; existing results are never emptied.
A Gurobi license is required for native optimization; bundled small examples
fit its restricted license.

## Design a comparison

1. Copy an example spec to a new file and give each arm an unambiguous name.
   Relative paths resolve from that spec's directory. Use existing supported
   controller scenario files or create new ones alongside the spec.
2. Hold demand, fleet, starting state, network, execution noise, time horizon and
   the reference policy fixed. Change a declared matching/acceptance/AV lever.
   Start with one lever; label combined interventions explicitly.
3. Keep the same seed list in every arm. The runner launches a fresh reference
   for each candidate, verifies repeated references and counts each seed once.
4. Inspect `policy_parameters.json` before interpreting results. Read completion
   first, then served/common-served waits, promises, human decisions/activity and
   fleet/AV movement costs. Check each candidate's adverse effects too.

Native insertion, immediate insertion with batch reoptimization, and Alonso–Mora
are supported single-operator matching controllers. The examples separate them
because their reference policies/search differ. Supported controller changes can
be candidates under a common declared reference; compare the actual parameter
changes and matched inputs, not the labels of separate experiments. AV studies
must use verified city bundles so eligibility and actual AV identity can be
checked independently.

The runner refuses changed background settings and empty/duplicate seed lists.
The comparison contract binds source, reference settings, execution-noise
override, physical input hashes and vehicle specifications. A named arm must
keep the same operator/noise parameters across seeds. Different days, source
versions or assumption profiles are separate experiments/strata, not additional
replications of one condition.

## Re-report matching or city AV runs

```bash
python -m tools.policy_compare report \
  --experiments /tmp/my_matching_comparison \
  --output /tmp/my_matching_report

python -m tools.policy_compare report \
  --experiments /workspace/market_results/phase16/s10 \
  --reference threshold_0 \
  --output /tmp/my_av_allocation_report
```

The second example uses an existing full city study. Build/run your own city
bundles with [the city workflow](PHASE_10.md), including independently sourced
reference weights for [AV repositioning](PHASE_12.md), before reporting a new
study. Actual paths in the saved manifests must resolve. The reporter accepts
full `city_av run` manifests and new sealed matching comparison manifests.

A matching run uses its declared reference. City AV runs default to the matched
`all_human` control; `--reference threshold_0` compares threshold240/repositioning
and the all-human control against threshold0. Use the direct threshold contrast
when asking about the AV-priority lever, and the all-human contrast when asking
about replacement/allocation. A changed fleet share, opt-in, fence, patience,
source version or placement profile creates a distinct stratum. These are not
extra seeds or replays of the same experimental condition.

Keep Python, dependency versions and native builds fixed when combining matching
experiments. Child manifests record those versions; matching code/input strata
alone do not certify equivalence across runtimes. City contracts also retain
their recorded dependency/native-runtime hashes.

The tool can read multiple compatible experiments. Different input/source
strata remain separate. Missing reference arms, unmatched seed sets, changed raw
files and non-identical duplicate conditions fail before paired inference.
Repeated reference runs with the same seed are checked as physical replays and
counted once. Reporting source and historical simulation source are recorded
separately; historical runs are never retagged as current-source simulations.

## Read the results

- `RESULTS.md`, `policy_comparison.png` and `.pdf`: completion, served waits,
  AV allocation and whole-run empty driving with seed ranges.
- `seed_kpis.csv`: every unique condition and KPI, retaining zero denominators
  and unavailable values explicitly.
- `kpi_movements.csv`: candidate-minus-reference means, paired seed intervals,
  pair/omission counts, movement direction, fraction percentage-point changes
  and relative percentages (unavailable at a zero baseline).
- `common_rider_waits.csv`: waits for identical request IDs served in both arms.
  This conditions on service and does not represent unserved riders.
- `policy_parameters.json`: actual changed operator/noise parameters against
  the reference, rather than relying on an arm's name.
- `kpi_catalog.json`, `strata.json`: definitions, clocks, denominators, source
  digests and input assumptions.
- `manifest.json`: exact raw/input hashes, physical checks, matched backgrounds,
  replay records, reporting source, simulation sources and output hashes.

Read coverage together with waits. Lower served-only waits can reflect changed
composition. More AV trips may transfer work from humans while total service
falls. Higher occupied utilization may reflect longer passenger journeys.
Modeled earnings are cost/fare proxies, not observed driver wages; AV vehicle
net proxies are separate from human-driver earnings distributions. Fixed-human
prefix trip metrics preserve the same driver IDs within each input regime.

Matching result folders are relocatable for re-reporting: raw directories and
archived vehicle specifications resolve relative to the comparison snapshot.
Original raw configuration files are unchanged. Original case-file hashes remain
provenance; snapshot hashes bind the actual reporting inputs. City historical
bundles retain their recorded paths and full manifests.

## Retain specialized comparison semantics

The shared tool deliberately rejects unsealed legacy paired/AV and windowed
manifests. Use their existing reports, with their source/evidence archives:

- [Windowed comparisons](PHASE_6.md): same-controller state restoration, request
  cohorts and explicit right censoring. Windows are not complete independent days.
- [Market/repositioning and calibration](PHASE_7_COMPLETION.md): observed-event
  availability, reference training and residual calibration errors.
- [AV preference/speed/forecast/joint planning](PHASE_9.md): dedicated policy
  grids, actual type timing and coverage accounting.
- [Patience](PHASE_14.md), [opt-in](PHASE_15.md) and
  [AV supply](PHASE_16.md): dedicated intervention and adjusted-response reports.

This preserves their definitions instead of silently merging incompatible
clocks, partial windows or unverified historical raw snapshots. New matching
runs should use the sealed workflow above; existing legacy artifacts remain
unchanged and reviewable.
