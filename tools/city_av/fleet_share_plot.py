"""Opt-in curves with fixed rider groups to expose allocation spillovers."""
import pandas as pd


def plot_report(data, summary, groups, output):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    cities=sorted(data.city.unique());colors=dict(all_human='C0',threshold_0='C1',threshold_240='C2')
    fig,axes=plt.subplots(len(cities),4,figsize=(16,3.7*len(cities)),squeeze=False,layout='constrained')
    panels=[('completion_rate',100,'Evaluation completion (%)'),('av_utilization',100,'AV occupied utilization (%)'),('fleet_empty_distance_km',1,'Whole-fleet empty distance (km)'),('common_human_trips_per_online_hour',1,'Fixed human slots: trips / online hour')]
    for city,axrow in zip(cities,axes):
        for ax,(metric,scale,title) in zip(axrow,panels):
            for arm in ['all_human','threshold_0','threshold_240']:
                g=summary[summary.city.eq(city)&summary.arm.eq(arm)].copy()
                for stat in ['mean','min','max']:g[stat]=g[metric+'_'+stat]
                g=g[g['mean'].notna()].sort_values('av_share')
                if g.empty:continue
                x=g.av_share.to_numpy()*100
                ax.plot(x,g['mean']*scale,marker='o',color=colors[arm],label=arm)
                ax.vlines(x,g['min']*scale,g['max']*scale,color=colors[arm])
            ax.set_title(city+': '+title,fontsize=9);ax.set_xlabel('Requested AV replacement (%)');ax.set_xticks([5,10,20]);ax.grid(alpha=.2);ax.legend(fontsize=7)
    fig.suptitle('AV fleet-share robustness: total vehicles, positions/SOC, demand and eligibility fixed\nWhiskers: initialization-seed ranges; actual-type search partitions vary, with matched all-human controls')
    fig.savefig(output/'fleet_share_sensitivity.png',dpi=160);fig.savefig(output/'fleet_share_sensitivity.pdf');plt.close(fig)
    def number(x):return '—' if pd.isna(x) else f'{x:.2f}'
    lines=['# Phase 16: AV fleet-share robustness\n\n',f'**{len(data)} unique conditions**; every accepted booking physically completes. Repetitions are separate replay records.\n\n',
        '| City | Fleet | Requested AV % | Policy | Seeds | Completed | AV trips | AV occupied % | Eligible served wait s | Fixed 480s service | Late actual pickups | Empty km |\n',
        '| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n']
    for r in summary.itertuples():
        lines.append(f'| {r.city} | {r.fleet_size} | {r.av_share*100:g} | {r.arm} | {r.seeds} | {number(r.completed_mean)} | {number(r.av_completed_mean)} | {number(r.av_utilization_mean*100)} | {number(r.eligible_wait_mean_s_mean)} | {number(r.within_480s_completed_mean)} | {number(r.late_actual_pickups_mean)} | {number(r.fleet_empty_distance_km_mean)} |\n')
    lines+=['\n## Definitions and interpretation\n\n',
        'AV replacement targets5/10/20% use integer rounded counts (minimum one AV and one human); exact roster counts remain in every seed row. Total fleet and fixed20% placement anchor are unchanged. The anchored slots start inside the fence at every share, including when human. AV types replace nested final vehicle IDs. Opt-in stays0.3 and both endpoints must stay inside the unchanged fence.\n\n',
        'Candidate-search budgets remain30 positions per group in native studies, but actual-type partitions change with replacement count. All-human shadow partitions follow each share and may change service despite identical geometry. These outcomes are retained explicitly. `paired_effects.csv` separates within-share policy effects from direct share changes at fixed policy. `control_adjusted_share_effects.csv` compares mixed-minus-matched-human responses across shares against10%; this diagnostic does not identify a field effect or remove every search interaction.\n\n',
        '`fixed_group_results.csv` and `fixed_group_effects.csv` retain the same request groups/denominators: baseline_eligible means the fixed0.3 opted-in in-fence requests; additional_opt_in means in-fence requests outside that draw (they remain non-opted-in throughout this study); outside_fence never qualifies. `common_rider_effects.csv` conditions on identical IDs served in both conditions. Served-only mean waits can change composition.\n\n',
        '`common_human_completed` and `common_human_trips_per_online_hour` use exactly the same first N-minus-anchor vehicle IDs in every stratum and policy. The existing retained-human metric instead uses the actual human roster, which changes membership with share. AV occupied utilization and AV throughput use the actual number of AVs, so allocation gains can coexist with falling per-AV use or changes to fixed human slots.\n\n',
        'Trips/waits refer to evaluation requests including later fulfillment. Occupied utilization/online hours use the evaluation clock; empty distance includes warm-up and fulfillment. Accepted promises fit the original480s deadline and every accepted rider completes; actual late pickups remain visible. Human acceptance, repositioning and execution noise stay off; cautious AV factor1.25, fence, demand/pooling consent, patience/service and source traffic stay fixed.\n\n',
        'The optional placement anchor leaves legacy initialization unchanged when omitted. Separate fresh legacy10% seed0 bridge runs retain historical byte comparisons; they are not pooled with the anchored grid as replications. Three seeds on one fixed cohort give conditional robustness, not population uncertainty or observed AV market penetration. Munich is AIMSUN-derived demand, Chicago the provided TNC sample and Manhattan the fixed TLC cohort. No geography-only causal comparison or daily throughput extrapolation is made.\n']
    (output/'RESULTS.md').write_text(''.join(lines))
