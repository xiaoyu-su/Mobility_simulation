"""Scientific reports that keep assumption strata and actual timing separate."""
import numpy as np
import pandas as pd


def plot_report(data,summary,output):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    cities=sorted(data.city.unique());fig,axes=plt.subplots(len(cities),4,figsize=(16,3.6*len(cities)),squeeze=False,layout='constrained')
    panels=[('completion_rate',100,'Evaluation completion (%)'),('eligible_wait_mean_s',1,'Eligible served mean wait (s)'),
            ('av_utilization',100,'AV occupied utilization (%)'),('fleet_empty_distance_km',1,'Whole-fleet empty distance (km)')]
    for city,axrow in zip(cities,axes):
        for ax,(metric,scale,title) in zip(axrow,panels):
            subset=summary[summary.city.eq(city)]
            for (fleet,arm),g in subset.groupby(['fleet_size','arm']):
                g=g.sort_values('patience_s');g=g[g[metric+'_mean'].notna()]
                if g.empty:continue
                x=g.patience_s.to_numpy(dtype=float)/60;mean=g[metric+'_mean'].to_numpy(dtype=float)*scale
                low=g[metric+'_min'].to_numpy(dtype=float)*scale;high=g[metric+'_max'].to_numpy(dtype=float)*scale
                line,=ax.plot(x,mean,marker='o',label=f'N={fleet}, {arm}')
                ax.vlines(x,low,high,color=line.get_color());ax.hlines(low,x-.08,x+.08,color=line.get_color());ax.hlines(high,x-.08,x+.08,color=line.get_color())
            ax.set_title(city+': '+title,fontsize=9);ax.set_xlabel('Assumed booking-patience cutoff (minutes)');ax.grid(alpha=.2);ax.legend(fontsize=7)
    fig.suptitle('Patience sensitivity on matched source cohorts\nWhiskers: initialization-seed ranges; cutoff applies to accepted offers, not guaranteed actual arrival')
    fig.savefig(output/'patience_sensitivity.png',dpi=160);fig.savefig(output/'patience_sensitivity.pdf');plt.close(fig)
    lines=['# Phase 14: booking-patience robustness\n\n',
        f'All **{len(data)} unique city/fleet/patience/seed/policy conditions** pass complete physical checks. Fresh-process repetitions are listed separately in the manifest. Every assumption stratum remains distinct.\n\n',
        'These are assumed offer/booking limits, not measured rider cancellation behavior. No accepted passenger is silently cancelled when actual execution is late. Accepted promises must fit the source-clock deadline; actual pickups after that deadline are explicitly retained and counted.\n\n',
        '| City | Fleet | Cutoff s | Policy | Seeds | Completed | AV trips | Eligible wait s | Within own limit | Within fixed 480s | Late actual pickups | Fleet empty km |\n',
        '| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n']
    def number(x):return '—' if pd.isna(x) else f'{x:.2f}'
    for r in summary.itertuples():
        lines.append(f'| {r.city} | {r.fleet_size} | {r.patience_s:g} | {r.arm} | {r.seeds} | {number(r.completed_mean)} | {number(r.av_completed_mean)} | {number(r.eligible_wait_mean_s_mean)} | {number(r.within_limit_completed_mean)} | {number(r.within_480s_completed_mean)} | {number(r.late_actual_pickups_mean)} | {number(r.fleet_empty_distance_km_mean)} |\n')
    lines+=['\n## Interpreting robustness\n\n',
        '`paired_effects.csv` distinguishes policy changes at fixed patience from patience changes at a fixed policy. `common_rider_effects.csv` compares the same served request IDs. Aggregate served wait means may change because the served sample changes. Completion need not be monotone: the intervention changes later fleet trajectories and allocation. Retain every seed and adverse direction.\n\n',
        'Every city/fleet has the same immutable source cohort, initial distribution, fence, vehicle specifications, service assumptions, routing runtime and exogenous network inputs across cutoffs. Only `op_max_wait_time` and source-clock request deadlines change. Actual placement/SOC and typed random backgrounds are checked across cutoffs. Demand-file audit hashes intentionally change with those deadline bytes; all non-deadline demand fields are verified separately.\n\n',
        'The ordinary city summary rejects incompatible input assumptions. This report groups explicitly by patience and refuses other uncontrolled changes. Conditions sharing city/fleet/seed/policy but differing in cutoff are neither pooled seed repetitions nor replay samples.\n\n',
        'Trips, waits and late-pickup counts use evaluation request IDs and include later fulfillment. Occupied utilization is clipped to the evaluation clock; empty distance includes warm-up and fulfillment tails. `within_limit_completed` counts served evaluation requests whose actual pickup fits their own assumed cutoff; that deadline differs across strata. `within_480s_completed` holds a common 8-minute actual-pickup target fixed across every stratum. Offered wait and actual wait are distinct.\n\n',
        'The 4/8/12-minute main grid is prespecified. Total fleet and 10% AV replacement, 0.3 per-request opt-in, cautious factor1.25, endpoint fence and 0/240-second dispatch thresholds remain fixed within each native city profile. Human acceptance, human/AV repositioning and execution noise remain off. Patience and the source-specific fleet are unverified assumptions; completed-trip data do not identify rejected demand or real cancellations. Provided traffic and replanning can produce timing error; no cause is inferred solely from a late pickup.\n\n',
        'Three initialization seeds on one fixed cohort provide conditional sensitivity, not population uncertainty or field calibration. Munich is simulated AIMSUN-derived demand, Chicago is a provided TNC subsample and Manhattan is the fixed TLC cohort. City/year/source-generation/load differences prevent geography-only causal comparisons. No daily AV throughput is extrapolated.\n']
    (output/'RESULTS.md').write_text(''.join(lines))
