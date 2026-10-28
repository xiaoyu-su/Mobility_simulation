"""Portable scientific comparison artifacts; no single-score policy ranking."""
import numpy as np
import pandas as pd


def render(data,effects,groups,output):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    metrics=[('completed','Completed requests'),('wait_mean_s','Served wait (s)'),('av_share_served','AV share of served (fraction)'),('empty_distance_km','Whole-run empty distance (km)')]
    fig,axes=plt.subplots(len(groups),4,figsize=(16,max(3.6,3.2*len(groups))),squeeze=False,layout='constrained')
    lines=['# Matching policy and AV allocation comparison\n\n',
        'Differences are candidate minus reference within matched source/input strata. Units, denominators and time scopes are in `kpi_catalog.json`. No welfare score or automatic best policy is inferred. Rates use percentage-point changes separately from relative percent. Missing/zero-denominator metrics remain unavailable.\n\n']
    def num(x):return '—' if pd.isna(x) else f'{x:.3f}'
    for (sid,context),row in zip(sorted(groups.items()),axes):
        g=data[data.stratum.eq(sid)];policies=sorted(g.arm.unique());ref=context['reference']
        lines += [f'## {context["label"]}: {sid}\n\n',f'Reference: `{ref}`. Simulation source: `{context["simulation_source_digest"]}`. Input assumptions stay inside this stratum.\n\n',
            '| Policy | Seeds | Completed | Served wait s | AV trips | AV occupied % | Empty km |\n','| --- | --- | --- | --- | --- | --- | --- |\n']
        for arm,frame in g.groupby('arm'):
            lines.append(f'| {arm} | {len(frame)} | {num(frame.completed.mean())} | {num(frame.wait_mean_s.mean())} | {num(frame.av_completed.mean())} | {num(frame.av_utilization.mean()*100)} | {num(frame.empty_distance_km.mean())} |\n')
        selected=effects[effects.stratum.eq(sid)&effects.metric.isin(['completed','wait_mean_s','av_completed','av_utilization','empty_distance_km'])]
        lines+=['\n| Candidate | KPI | Mean change | Conditional paired95% interval | Pairs /omitted |\n','| --- | --- | --- | --- | --- |\n']
        for r in selected.itertuples():lines.append(f'| {r.arm} | {r.metric} ({r.unit}) | {num(r.mean_difference)} | [{num(r.ci95_low)}, {num(r.ci95_high)}] | {r.n_pairs} /{r.n_omitted_pairs} |\n')
        for ax,(metric,title) in zip(row,metrics):
            means=[];low=[];high=[]
            for arm in policies:
                v=g.loc[g.arm.eq(arm),metric].dropna();means.append(v.mean() if len(v) else np.nan);low.append(v.min() if len(v) else np.nan);high.append(v.max() if len(v) else np.nan)
            x=np.arange(len(policies));ax.plot(x,means,marker='o');ax.vlines(x,low,high);ax.set_xticks(x,policies,rotation=25,ha='right',fontsize=7);ax.set_title(context['label']+'\n'+title,fontsize=8);ax.grid(alpha=.2)
    lines+=['\n## Interpretation and scope\n\n',
        '`kpi_movements.csv` retains every KPI, paired seed interval/status, missing pairs, fraction percentage-point changes and relative changes (unavailable for zero baseline). Three seeds are not population uncertainty. No multiple-testing or policy-superiority claim is made from these exploratory intervals.\n\n',
        'Served-only means can change who is served; `common_rider_waits.csv` compares identical request IDs served in both policies. Include completion and unserved counts whenever interpreting waits or promise errors. AV trip share is allocation; utilization can rise with longer journeys. Neither is a welfare score. Driver costs/earnings are model proxies over the full run/tail, not observed wages. Clock-clipped utilization and request-cohort service differ from full-run distance/cost scopes.\n\n',
        'City AV assumptions, actual fleet shares/placement anchors, search partitions and source versions remain separate strata in `strata.json`. All-human controls preserve the original declared shadow search groups. No cross-city/year or source-version pooling is performed. Existing windowed, market-calibration and older unsealed AV reports retain their specialized censoring/calibration definitions and are linked in the project guide.\n\n',
        'The report is read-only. Raw hashes, physical bookkeeping and named random backgrounds are checked before paired inference. `manifest.json` preserves the reporting source separately from original simulation sources. Historical simulations are never retagged as current-source runs.\n']
    (output/'RESULTS.md').write_text(''.join(lines));fig.suptitle('Policy KPI movements on matched inputs\nWhiskers: initialization-seed ranges; displayed policies do not imply a ranking')
    fig.savefig(output/'policy_comparison.png',dpi=160);fig.savefig(output/'policy_comparison.pdf');plt.close(fig)
