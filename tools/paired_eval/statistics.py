"""Paired inference across seeds, not across individual drivers."""

import numpy as np
from scipy import stats


def paired_statistics(baseline, candidate):
    baseline, candidate = np.asarray(baseline, dtype=float), np.asarray(candidate, dtype=float)
    if baseline.ndim != 1 or baseline.shape != candidate.shape or not len(baseline):
        raise ValueError("Matched nonempty one-dimensional samples are required")
    valid = np.isfinite(baseline) & np.isfinite(candidate)
    omitted = int((~valid).sum())
    baseline, candidate = baseline[valid], candidate[valid]
    count = len(baseline)
    row = {"n_pairs": count, "n_omitted_pairs": omitted,
           "baseline_mean": float(baseline.mean()) if count else np.nan,
           "candidate_mean": float(candidate.mean()) if count else np.nan,
           "mean_difference": np.nan, "ci95_low": np.nan, "ci95_high": np.nan,
           "paired_t_statistic": np.nan, "paired_t_pvalue": np.nan, "wilcoxon_pvalue": np.nan}
    if count:
        differences = candidate - baseline
        row["mean_difference"] = float(differences.mean())
    if count < 2:
        row["status"] = "insufficient_pairs"
        return row
    spread = float(differences.std(ddof=1))
    half_width = float(stats.t.ppf(.975, count - 1) * spread / np.sqrt(count))
    row.update(ci95_low=row["mean_difference"] - half_width,
               ci95_high=row["mean_difference"] + half_width)
    if np.all(differences == 0):
        row.update(paired_t_statistic=0.0, paired_t_pvalue=1.0,
                   wilcoxon_pvalue=1.0, status="identical_pairs")
    else:
        row["wilcoxon_pvalue"] = float(stats.wilcoxon(differences, alternative="two-sided", method="auto").pvalue)
        if spread == 0:
            row["status"] = "constant_difference_t_test_undefined"
        else:
            test = stats.ttest_rel(candidate, baseline)
            row.update(paired_t_statistic=float(test.statistic), paired_t_pvalue=float(test.pvalue), status="ok")
    return row
