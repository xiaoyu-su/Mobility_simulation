"""Opt-in curves with fixed rider groups to expose allocation spillovers."""
import pandas as pd


def plot_report(data, summary, groups, output):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    cities=sorted(data.city.unique());colors=dict(all_human='C0',threshold_0='C1',threshold_240='C2')
    fig,axes=plt.subplots(len(cities),4,figsize=(16,3.7*len(cities)),squeeze=False,layout='constrained')
    panels=[('completion_rate',100,'Evaluation completion (%)'),('av_utilization',100,'AV occupied utilization (%)'),
        ('fleet_empty_distance_km',1,'Whole-fleet empty distance (km)'),('baseline_wait',1,'Fixed baseline group: served wait (s)')]
    for city,axrow in zip(cities,axes):
        for ax,(metric,scale,title) in zip(axrow,panels):
            for arm in ['all_human','threshold_0','threshold_240']:
                if metric=='baseline_wait':
                    subset=groups[groups.city.eq(city)&groups.arm.eq(arm)&groups.group.eq('baseline_eligible')]
                    g=subset.groupby('opt_in_share').wait_mean_s.agg(['mean','min','max']).reset_index()
                else:
                    g=summary[summary.city.eq(city)&summary.arm.eq(arm)].copy()
                    for stat in ['mean','min','max']:g[stat]=g[metric+'_'+stat]
                g=g[g['mean'].notna()].sort_values('opt_in_share')
                if g.empty:continue
                x=g.opt_in_share.to_numpy()*100
                ax.plot(x,g['mean']*scale,marker='o',color=colors[arm],label=arm)
                ax.vlines(x,g['min']*scale,g['max']*scale,color=colors[arm])
            ax.set_title(city+': '+title,fontsize=9);ax.set_xlabel('Assumed per-request opt-in (%)');ax.set_xticks([0,30,100]);ax.grid(alpha=.2);ax.legend(fontsize=7)
    fig.suptitle('Opt-in sensitivity: demand, fleet, endpoint fence and 480s offer limit held fixed\nWhiskers: three initialization-seed ranges; fixed baseline group defined by 30% opt-in, including at 0%')
    fig.savefig(output/'opt_in_sensitivity.png',dpi=160);fig.savefig(output/'opt_in_sensitivity.pdf');plt.close(fig)
    def number(x):return '—' if pd.isna(x) else f'{x:.2f}'
    lines=['# Phase 15: rider opt-in robustness\n\n',f'**{len(data)} unique conditions**; every accepted booking physically completes. Repetitions are separate replay records.\n\n',
        '| City | Fleet | Opt-in % | Policy | Seeds | Completed | AV trips | AV occupied % | Eligible served wait s | Fixed 480s service | Late actual pickups | Empty km |\n',
        '| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n']
    for r in summary.itertuples():
        lines.append(f'| {r.city} | {r.fleet_size} | {r.opt_in_share*100:g} | {r.arm} | {r.seeds} | {number(r.completed_mean)} | {number(r.av_completed_mean)} | {number(r.av_utilization_mean*100)} | {number(r.eligible_wait_mean_s_mean)} | {number(r.within_480s_completed_mean)} | {number(r.late_actual_pickups_mean)} | {number(r.fleet_empty_distance_km_mean)} |\n')
    lines+=['\n## Definitions and interpretation\n\n',
        'Only the opt-in parameter changes across strata. A CRC32 request/operator draw fixed across seeds creates nested eligible sets. Zero opt-in keeps the AV replacement vehicles in the roster but makes them ineligible for passenger service; this is distinct from the all-human control. At full opt-in, both endpoints must still be inside the unchanged fence. This per-request flag is not a persistent person-level willingness or a dynamic offer-choice model.\n\n',
        '`fixed_group_results.csv` partitions the same evaluation requests into baseline_eligible (inside fence and opted in at 30%), additional_opt_in (inside fence and outside that baseline draw), and outside_fence. These labels remain fixed even at zero opt-in. Their completion denominators are fixed. The ordinary eligible served wait changes membership across opt-in and must not be interpreted as a same-rider effect. `common_rider_effects.csv` retains only identical IDs served in both compared conditions, by fixed group; it does not represent rejected riders.\n\n',
        '`paired_effects.csv` separates policy contrasts within fixed opt-in from opt-in contrasts at fixed policy against 30%. `fixed_group_effects.csv` reports both on fixed groups. Missing wait means and AV rates with zero denominators remain missing; paired statistics record omitted pairs rather than replacing them with zero. All-human physical outputs must be invariant across opt-in; its reported eligible-group means can change membership. No policy is selected after observing results.\n\n',
        'Trips/waits use evaluation request IDs and later fulfillment; AV occupied utilization clips physical passenger occupancy to the evaluation clock. Empty distance includes warm-up and the fulfillment tail. Promises must meet the original request-clock 480s cutoff. Actual late pickups remain counted, and accepted riders are completed. Human/AV repositioning, driver acceptance and execution noise stay off; cautious AV travel factor1.25, 10% replacement fleet, placement/SOC, source demand/consent and candidate-search budget stay fixed.\n\n',
        'Three seeds on one fixed source cohort describe conditional robustness, not empirical AV adoption, cancellation behavior or population confidence. Munich demand is AIMSUN-derived simulation; Chicago is the provided TNC subsample; Manhattan preserves its TLC cohort and pooling consent. Source year, network, fleet load and generation differ across cities. Completion need not increase with opt-in because changed assignments alter later trajectories. Gains and adverse results are retained. Daily AV throughput is not inferred from partial-day service.\n']
    (output/'RESULTS.md').write_text(''.join(lines))
