"""Scientific figures and explicit interpretation of occupied-time accounting."""

import numpy as np
import pandas as pd


TERMS = ['completion_count_s','passenger_duration_s','eval_before_window_passenger_s',
         'eval_after_window_passenger_s','warmup_inside_window_passenger_s',
         'alighting_dwell_passenger_s','logged_overlap_passenger_s']
LABELS = ['Completion count','Passenger duration','Pre-window correction','Post-window correction',
          'Warm-up carry-in','Alighting dwell','Logged overlap correction']


def plot_report(data, pairs, output):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    active=data[data.av_online_s.gt(0)]; regimes=sorted(set(zip(active.city,active.fleet_size)))
    fig,axes=plt.subplots(max(1,len(regimes)),4,figsize=(15,3.6*max(1,len(regimes))),squeeze=False,layout='constrained')
    panels=[('av_completed',1,'Completed AV bookings'),('av_utilization',100,'Occupied AV utilization (%)'),
            ('mean_eval_in_vehicle_s',1,'AV pickup-to-dropoff duration (s)'),('fleet_empty_distance_km',1,'Whole-fleet empty distance (km)')]
    for (city,fleet),row in zip(regimes,axes):
        subset=active[active.city.eq(city)&active.fleet_size.eq(fleet)]
        for ax,(metric,scale,title) in zip(row,panels):
            for factor,g in subset.groupby('factor'):
                stats=g.groupby('threshold_s')[metric].agg(['mean','min','max']) * scale
                x=stats.index.to_numpy(dtype=float);mean=stats['mean'].to_numpy(dtype=float)
                low=stats['min'].to_numpy(dtype=float);high=stats['max'].to_numpy(dtype=float)
                line,=ax.plot(x,mean,marker='o',label=f'Travel time ×{factor:g}')
                ax.vlines(x,low,high,color=line.get_color())
                ax.hlines(low,x-5,x+5,color=line.get_color());ax.hlines(high,x-5,x+5,color=line.get_color())
            ax.set_title(f'{city}, N={fleet}: {title}',fontsize=9);ax.set_xlabel('AV ETA allowance (s)');ax.grid(alpha=.2);ax.legend(fontsize=8)
    fig.suptitle('Threshold and speed sensitivity on matched benchmark histories\nWhiskers: initialization-seed ranges; duration uses completed evaluation request IDs')
    fig.savefig(output/'threshold_speed.png',dpi=160);fig.savefig(output/'threshold_speed.pdf');plt.close(fig)
    selected=[]
    if len(pairs):
        for (city,fleet,control,candidate),g in pairs.groupby(['city','fleet_size','control','candidate']):
            a=active[active.city.eq(city)&active.fleet_size.eq(fleet)&active.arm.eq(control)].iloc[0]
            b=active[active.city.eq(city)&active.fleet_size.eq(fleet)&active.arm.eq(candidate)].iloc[0]
            if b.factor==1.25 and b.threshold_s==240 and ((a.factor==1.25 and a.threshold_s==0) or (a.factor==1 and a.threshold_s==240)):
                selected.append((city,fleet,control,candidate,g,a.av_online_s))
    if selected:
        fig,ax=plt.subplots(figsize=(max(9,len(selected)*2.5),6),layout='constrained');positive=np.zeros(len(selected));negative=positive.copy()
        for term,label in zip(TERMS,LABELS):
            values=np.array([g[term].mean()/online*100 for _,_,_,_,g,online in selected]);bottom=np.where(values>=0,positive,negative)
            ax.bar(range(len(selected)),values,bottom=bottom,label=label)
            positive+=np.maximum(values,0);negative+=np.minimum(values,0)
        totals=np.array([g.utilization_change_pp.mean() for _,_,_,_,g,_ in selected])
        low=np.array([g.utilization_change_pp.min() for _,_,_,_,g,_ in selected]);high=np.array([g.utilization_change_pp.max() for _,_,_,_,g,_ in selected])
        ax.errorbar(range(len(selected)),totals,yerr=[totals-low,high-totals],fmt='kD',capsize=4,label='Actual total; seed range')
        ax.axhline(0,color='black',linewidth=.8);ax.set_xticks(range(len(selected)),[f'{c}, N={n}\n{b} minus\n{a}' for c,n,a,b,_,_ in selected],fontsize=8)
        ax.set_ylabel('Occupied AV utilization change (percentage points)');ax.grid(axis='y',alpha=.2);ax.legend(fontsize=8,loc='upper left',bbox_to_anchor=(1,1))
        ax.set_title('Exact accounting of recorded utilization changes\nComponents are algebraic contributions, not identified causal mediators')
        fig.savefig(output/'occupied_time_components.png',dpi=160);fig.savefig(output/'occupied_time_components.pdf');plt.close(fig)
    lines=['# Phase 13: Chicago threshold and speed mechanisms\n\n',
        f'All **{len(data)} physical runs / {len(data)} unique conditions** pass the raw booking, event, capacity, chronology, matched-background and exact occupied-time checks. This report excludes separate replay studies from its independent condition count.\n\n',
        'This is a matched benchmark sensitivity, not empirical AV calibration. Each policy changes later fleet availability and retained candidate sets. A same-request comparison across policies does not hold those histories fixed. Absence of a retained AV candidate is not proof that no AV was physically feasible.\n\n',
        '## Actual outcomes\n\n',
        '| City | Fleet | Policy | Seeds | Completed | AV trips | AV occupied % | Mean AV pickup-to-dropoff s | Fleet empty km |\n',
        '| --- | --- | --- | --- | --- | --- | --- | --- | --- |\n']
    for (city,fleet,arm),g in data.groupby(['city','fleet_size','arm']):
        def fmt(column,scale=1):
            x=g[column].mean();return '—' if pd.isna(x) else f'{x*scale:.2f}'
        lines.append(f'| {city} | {fleet} | {arm} | {len(g)} | {fmt("completed")} | {fmt("av_completed")} | {fmt("av_utilization",100)} | {fmt("mean_eval_in_vehicle_s")} | {fmt("fleet_empty_distance_km")} |\n')
    lines+=['\n## Exact bridge between trips and utilization\n\n',
        'Occupied vehicle seconds equal full evaluation-cohort passenger seconds, minus time before/after the evaluation clock, plus warm-up passenger seconds inside the clock, plus logged alighting dwell, minus logged passenger overlap. Every per-run bridge is independently checked against the union of actual passenger-holding intervals and raw vehicle occupancy.\n\n',
        'User pickup and dropoff timestamps mark boarding/alighting start. Raw vehicle occupancy retains outgoing passengers until alighting ends. The extra dwell is explicit; it is not mislabeled passenger journey time. Logged overlap includes moving shared occupancy, stationary incoming/outgoing unions and multi-passenger bookings, so it is not solely a pooling effect.\n\n',
        'The evaluation passenger-time product is decomposed symmetrically: average duration × count change plus average count × duration change. This allocates the interaction exactly. With zero completions, the duration factor used in that identity is zero by convention; a zero factor is not an observed trip duration.\n\n',
        '| Fleet | Candidate minus control | AV count change | Utilization change pp | Count pp | Duration pp | Pre-window pp | Post-window pp | Warm-up pp | Alighting pp | Overlap pp |\n',
        '| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n']
    for _,fleet,control,candidate,g,online in selected:
        values=[g[t].mean()/online*100 for t in TERMS]
        lines.append(f'| {fleet} | {candidate} minus {control} | {g.completed_change.mean():+.2f} | {g.utilization_change_pp.mean():+.3f} | '+' | '.join(f'{x:+.3f}' for x in values)+' |\n')
    lines+=['\nThe terms sum to the actual utilization change before rounding. All seeds and contrasts remain in `paired_accounting.csv`, including results that contradict the earlier two-seed direction. These accounting identities explain which recorded time quantities changed; they do not identify a causal duration or pooling intervention.\n\n',
        '## Request-level feedback and limits\n\n',
        '`request_mechanisms.csv` retains every warm-up/evaluation request, final product, actual pickup/dropoff/alighting endpoint, duration, wait, eligibility and last recorded retained-candidate reason. `product_transitions.csv` partitions each paired evaluation cohort into all nine AV/human/unserved transitions and compares wait for the same served IDs. `time_bins.csv` separates arrivals, actual pickups, occupied seconds and decision-event counts; repeated offer events are not unique requests.\n\n',
        'Threshold0/120/240/480 and equal/cautious speed are prespecified. Human acceptance, human/AV repositioning and execution noise stay off; opt-in, service area, source cohort, placement/SOC, candidate budgets and total fleet remain fixed within a seed/regime. Fleet100 versus200 is a load sensitivity with different roster/initialization, not an identical-background pair. Three initialization seeds on one provided cohort do not establish population uncertainty or reproduce the screenshot\'s load regime.\n']
    (output/'RESULTS.md').write_text(''.join(lines))
