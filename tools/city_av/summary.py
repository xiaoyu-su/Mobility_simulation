"""Pool seeds, inspect exact replays, and retain favorable and adverse policy effects."""

import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.fleetctrl.av_product import opt_in
from src.misc.seeding import file_digest
from tools.paired_eval.statistics import paired_statistics
from tools.synthetic_market.build import json_write


METRICS=['completed','completion_rate','av_completed','human_completed','av_served_share',
         'av_utilization','av_idle_share','eligible_av_service_rate','eligible_wait_mean_s','other_wait_mean_s',
         'retained_human_trips_per_online_hour','fleet_empty_distance_km','av_empty_distance_km',
         'human_empty_distance_km','av_empty_distance_share','human_won_while_idle_av_closer']
REPLAY_FILES=['1_user-stats.csv','2-0_op-stats.csv','initial_placement.csv','city_report.json','random_streams.json',
              'city_search_contract.json','av_dispatch_op_0.csv','av_product_op_0.json','city_repositioning_contract.json']
REPOSITION_METRICS=['av_repositioning_assignments','av_repositioning_distance_km',
                    'av_repositioning_time_s','av_repositioning_arrivals','av_repositioning_interrupted_legs']


def bundle_contract(meta):
    """The declared input regime, distinct from initialization-seed variation."""
    return dict(config=meta['config'],files=meta['output_sha256'],
                dependencies=meta['dependencies'],runtime=meta.get('runtime_files_sha256',{}))


def verified_city_bundle(path, manifest_sha256):
    """Verify the full recorded input snapshot without retagging historical source."""
    path=Path(path).resolve()
    if file_digest(path/'manifest.json')!=manifest_sha256:raise ValueError('City input manifest changed')
    meta=json.loads((path/'manifest.json').read_text())
    if meta['status']!='complete':raise ValueError('Incomplete city input snapshot')
    for name,h in meta['output_sha256'].items():
        target=(path/name).resolve()
        if not target.is_relative_to(path) or not target.is_file() or file_digest(target)!=h:
            raise ValueError(f'City input snapshot changed: {name}')
    return meta


def summarize(experiments, output):
    output=Path(output)
    if output.exists():raise ValueError('Refusing to overwrite city summary')
    rows=[];conditions={};replays=[];source=None;inputs=[];physical=0;checks=0;cohorts={};folders={};contracts={}
    for experiment in map(Path,experiments):
        m=json.loads((experiment/'manifest.json').read_text())
        if m['status']!='complete' or any(r['status']!='complete' or r['returncode']!=0 for r in m['runs']):raise ValueError('Cannot summarize incomplete city studies')
        if source is not None and source!=m['source']['code_digest']:raise ValueError('Cannot pool different simulation source versions')
        source=m['source']['code_digest'];checks+=len(m['validated_pairs'])
        for name,h in m['output_sha256'].items():
            if file_digest(experiment/name)!=h:raise ValueError('City study report changed after completion')
        inputs.append(dict(path=str(experiment),manifest_sha256=file_digest(experiment/'manifest.json')))
        for city,record in m['bundles'].items():
            meta=verified_city_bundle(record['path'],record['manifest_sha256'])
            cohort_key=(city,meta['fleet_size']);contract=bundle_contract(meta)
            if cohort_key in contracts and contracts[cohort_key]!=contract:
                raise ValueError('Incompatible city input assumptions; report patience/input strata separately')
            contracts[cohort_key]=contract
        for entry in m['runs']:
            physical+=1;folder=Path(entry['output']);city=entry['city'];bundle=Path(m['bundles'][city]['path'])
            if file_digest(bundle/'manifest.json')!=m['bundles'][city]['manifest_sha256']:raise ValueError('City input manifest changed')
            for name,h in entry['output_sha256'].items():
                if file_digest(folder/name)!=h:raise ValueError(f'Raw city output changed: {folder/name}')
            report=json.loads((folder/'city_report.json').read_text());key=(city,report['fleet_size'],entry['seed'],entry['arm'])
            if key in conditions:
                old=folders[key];names=[]
                for name in REPLAY_FILES:
                    a,b=old/name,folder/name
                    if a.exists()!=b.exists() or a.exists() and a.read_bytes()!=b.read_bytes():raise ValueError(f'Fresh-process city replay differs: {key} {name}')
                    if a.exists():names.append(name)
                replays.append(dict(city=city,fleet_size=report['fleet_size'],seed=entry['seed'],arm=entry['arm'],byte_identical_files=names))
                continue
            row=dict(seed=entry['seed'],arm=entry['arm'],**report);rows.append(row);conditions[key]=row;folders[key]=folder
            cohort_key=(city,report['fleet_size'])
            if cohort_key not in cohorts:
                meta=json.loads((bundle/'manifest.json').read_text());cohort=pd.read_csv(bundle/'observed_cohort.csv').set_index('request_id')
                mapping=pd.read_csv(bundle/'zones/network/node_zone_info.csv').set_index('node_index').zone_id
                zones=set(meta['av_product']['fence_zones'])
                eligible=(cohort.start.map(mapping).isin(zones)&cohort.end.map(mapping).isin(zones)&cohort.index.to_series().map(lambda rid:opt_in(rid,0,meta['av_product']['opt_in_share'])))
                cohorts[cohort_key]=(cohort,eligible,meta)
    if not rows:raise ValueError('No complete city conditions')
    output.mkdir(parents=True);data=pd.DataFrame(rows).sort_values(['city','fleet_size','seed','arm'])
    reposition_study='av_repositioning_enabled' in data
    metrics=METRICS+REPOSITION_METRICS if reposition_study else METRICS
    data.to_csv(output/'seed_results.csv',index=False)
    summary=[];effects=[];riders=[]
    for (city,fleet,arm),group in data.groupby(['city','fleet_size','arm'],sort=True):
        row=dict(city=city,fleet_size=int(fleet),arm=arm,seeds=len(group))
        for metric in metrics:
            values=group[metric].dropna()
            for kind in ['mean','min','max']:row[metric+'_'+kind]=float(getattr(values,kind)()) if len(values) else None
        summary.append(row)
        controls=[c for c in ['all_human','threshold_0'] if c!=arm and (data.city.eq(city)&data.fleet_size.eq(fleet)&data.arm.eq(c)).any()]
        matched_off=arm.removesuffix('_repo') if arm.endswith('_repo') else None
        if matched_off and matched_off not in controls and (data.city.eq(city)&data.fleet_size.eq(fleet)&data.arm.eq(matched_off)).any():controls.append(matched_off)
        for control in controls:
            base=data[data.city.eq(city)&data.fleet_size.eq(fleet)&data.arm.eq(control)].set_index('seed')
            candidate=group.set_index('seed');seeds=sorted(set(base.index)&set(candidate.index))
            for metric in metrics:
                effects.append(dict(city=city,fleet_size=int(fleet),arm=arm,control=control,metric=metric,
                    **paired_statistics(base.loc[seeds,metric].to_numpy(dtype=float),candidate.loc[seeds,metric].to_numpy(dtype=float))))
            cohort,eligible,_=cohorts[city,fleet]
            for seed in seeds:
                first=pd.read_csv(folders[city,fleet,seed,control]/'1_user-stats.csv').set_index('request_id')
                second=pd.read_csv(folders[city,fleet,seed,arm]/'1_user-stats.csv').set_index('request_id')
                if set(first.index)!=set(second.index):raise ValueError('Different request identities in city contrast')
                common=cohort.is_evaluation_request&first.dropoff_time.notna()&second.dropoff_time.notna()
                delta=second.pickup_time-first.pickup_time
                for name,mask in [('all',pd.Series(True,index=cohort.index)),('eligible',eligible),('other',~eligible)]:
                    values=delta[common&mask]
                    riders.append(dict(city=city,fleet_size=int(fleet),seed=seed,arm=arm,control=control,group=name,
                        common_served=len(values),mean_wait_change_s=float(values.mean()) if len(values) else None,
                        median_wait_change_s=float(values.median()) if len(values) else None,
                        improved=int(values.lt(-1e-7).sum()),worsened=int(values.gt(1e-7).sum()),unchanged=int(values.abs().le(1e-7).sum())))
    grouped=pd.DataFrame(summary);grouped.to_csv(output/'configuration_summary.csv',index=False)
    pd.DataFrame(effects).to_csv(output/'paired_effects.csv',index=False);pd.DataFrame(riders).to_csv(output/'common_rider_effects.csv',index=False)
    json_write(output/'integrity.json',dict(simulation_source_digest=source,physical_runs=physical,unique_seed_conditions=len(rows),
        within_study_background_comparisons=checks,fresh_process_replay_records=replays,inputs=inputs,
        all_raw_output_hashes_verified=True,all_complete_bookings=True,rule_violations=0))
    def number(value,scale=1):return '—' if pd.isna(value) else f'{value*scale:.2f}'
    text=f'''# Phase 10 cross-city policy results

All **{physical} physical runs** finish; there are **{len(rows)} distinct city/fleet/seed/policy conditions** and **{len(replays)} exact fresh-process replay records**. Every source/input/output contract passes; the per-run physical checks report zero AV rule violations and complete accepted bookings. Source digest: `{source}`.

These are conditional benchmark experiments. Munich demand is sampled from an AIMSUN PV-to-MoD simulation; Chicago is a provided 2022 TNC subsample on a 2023 OSM network; Manhattan is the existing 2019 TLC cohort. Fleet size, patience, AV adoption, fence and service models are assumptions. City and load regimes are not randomized, so differences between cities are not a causal geography effect. The supplied plan's numerical figures are not fit targets.

Human acceptance, human repositioning, AV repositioning and execution noise are off. Each city has fixed demand and shared actual initial positions/SOC across controls, with the designated AV slots fenced even in the all-human arm. The all-human comparison replaces vehicle types without adding fleet capacity. All arms have the same retained/designated-slot candidate budgets; designated humans remain unrestricted in the human control. Cautious factor1.25 means25% longer travel time, or80% of baseline speed. Opt-in is per request, not persistent rider behavior.
'''
    for city in sorted(data.city.unique()):
        text+='\n## '+city+'\n\n'
        for (c,fleet),(cohort,_,meta) in cohorts.items():
            if c!=city:continue
            text+=f"Fleet **{fleet}**: {meta['evaluation_count']} evaluation +{meta['warmup_count']} warm-up requests; {meta['av_product']['av_count']} designated AV slots; reference **{meta['reference']['rows']}** rows ({meta['reference']['kind']}). Provided source: {json.dumps(meta['provenance'],ensure_ascii=False)}\n\n"
        text+='| Fleet | Policy | Seeds | Completed | AV trips | AV occupied % | Eligible wait s | Other wait s | Retained human trips/h | Fleet empty km |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n'
        for r in grouped[grouped.city.eq(city)].itertuples():
            text+=f'| {r.fleet_size} | {r.arm} | {r.seeds} | {number(r.completed_mean)} | {number(r.av_completed_mean)} | {number(r.av_utilization_mean,100)} | {number(r.eligible_wait_mean_s_mean)} | {number(r.other_wait_mean_s_mean)} | {number(r.retained_human_trips_per_online_hour_mean)} | {number(r.fleet_empty_distance_km_mean)} |\n'
        text+='\n'
        for fleet in sorted(data.loc[data.city.eq(city),'fleet_size'].unique()):
            values=grouped[grouped.city.eq(city)&grouped.fleet_size.eq(fleet)].set_index('arm')
            if not {'threshold_0','threshold_240'}<=set(values.index):continue
            a,b=values.loc['threshold_0'],values.loc['threshold_240']
            text+=f"At fleet{fleet}, threshold0→240 changes mean AV occupied utilization **{number(a.av_utilization_mean,100)}%→{number(b.av_utilization_mean,100)}%**, eligible served wait **{number(a.eligible_wait_mean_s_mean)}→{number(b.eligible_wait_mean_s_mean)}s**, total completion **{number(a.completed_mean)}→{number(b.completed_mean)}**, and whole-fleet empty distance **{number(a.fleet_empty_distance_km_mean)}→{number(b.fleet_empty_distance_km_mean)}km**. These directions are measured, including adverse changes.\n\n"
    text+='''## Reading these comparisons

Means/ranges pool simulation seeds within a fixed city/fleet/source cohort; `paired_effects.csv` includes conditional t intervals, valid-pair counts and insufficient-pair flags. Small seed counts do not establish population or cross-city uncertainty. Every policy and seed is retained. `common_rider_effects.csv` compares identical served request IDs, while served-only aggregate wait means can change composition.

Waits/trips use evaluation request IDs and include later physical fulfillment. Occupied/idle/online time is clipped to the evaluation clock; distance includes warm-up and the completion tail. An empty-distance fraction can decrease while empty kilometers increase; inspect the absolute fleet totals. Retained-human productivity tracks the same original human slots in both replacement and all-human arms. Nearest-idle-AV proximity is not proof that an alternative full plan was feasible. No observed AV adoption, driver wage, full-day throughput, fitted unserved demand or universally superior policy is claimed.

Capacity audits check every moving load and both pre/post loads at stationary exchanges. FleetPy records a union of incoming and departing IDs during a boarding stop; its raw stationary occupancy can exceed seated capacity. `stationary_exchange_union_rows` retains those occurrences explicitly; raw records are unchanged.
'''
    if reposition_study:
        text=text.replace('# Phase 10 cross-city policy results','# Phase 12 cross-city AV repositioning results',1)
        text=text.replace('Human acceptance, human repositioning, AV repositioning and execution noise are off.',
            'Human acceptance, human repositioning and execution noise are off. AV repositioning is the declared on/off policy lever, with fixed 900-second callbacks and no retargeting, forecast noise or joint planning.')
        text+='''\n## Matched repositioning changes\n\nRepositioning uses stationary, separate-reference counts for trips whose **both endpoints** lie inside the AV fence. These are relative spatial weights, not calibrated future trip volumes. Native reference pickups occur strictly before warm-up; Manhattan references are earlier training dates. No evaluation/warm-up request is used to construct these weights. Uniform assumed opt-in scales mass and cancels from the spatial apportionment. Sparse references and transfer across clocks remain limitations.\n\nAll `_repo` effects below compare the same threshold with repositioning off, keeping fleet size, source request identities, placement/SOC, search budgets and type speed fixed. Values are two-condition mean differences; inspect paired seeds and identical-served-rider wait comparisons before interpreting service gains.\n\n| City | Fleet | Threshold | Completion change | AV trips change | AV utilization change, pp | Eligible wait change, s | Fleet empty change, km | AV empty change, km |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- |\n'''
        for (city,fleet),g in grouped.groupby(['city','fleet_size']):
            values=g.set_index('arm')
            for arm in sorted(a for a in values.index if a.endswith('_repo')):
                off=arm.removesuffix('_repo')
                if off not in values.index:continue
                a,b=values.loc[off],values.loc[arm]
                text+=f'| {city} | {fleet} | {off} | {number(b.completed_mean-a.completed_mean)} | {number(b.av_completed_mean-a.av_completed_mean)} | {number(b.av_utilization_mean-a.av_utilization_mean,100)} | {number(b.eligible_wait_mean_s_mean-a.eligible_wait_mean_s_mean)} | {number(b.fleet_empty_distance_km_mean-a.fleet_empty_distance_km_mean)} | {number(b.av_empty_distance_km_mean-a.av_empty_distance_km_mean)} |\n'
        text+='\n`city_repositioning_contract.json` traces actual empty AV legs to recorded commands and distinguishes target arrivals from interrupted legs. A command can be superseded before movement; intent alone is not counted as physical movement. Increased occupied utilization or lower empty-distance fraction does not by itself establish more completed trips or lower absolute empty driving. Favorable and adverse changes are retained.\n'
    (output/'RESULTS.md').write_text(text)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    cities=sorted(data.city.unique());fig,axes=plt.subplots(len(cities),3,figsize=(13,3.5*len(cities)),squeeze=False,layout='constrained')
    panels=[('av_utilization',100,'AV occupied utilization (%)'),('eligible_wait_mean_s',1,'Eligible served: mean wait (s)'),('completion_rate',100,'Evaluation completion (%)')]
    for city,axrow in zip(cities,axes):
        for ax,(metric,scale,title) in zip(axrow,panels):
            for fleet in sorted(data.loc[data.city.eq(city),'fleet_size'].unique()):
                g=grouped[grouped.city.eq(city)&grouped.fleet_size.eq(fleet)&grouped.arm.isin(['threshold_0','threshold_120','threshold_240','threshold_480'])].copy()
                g=g[pd.to_numeric(g[metric+'_mean'],errors='coerce').notna()]
                if g.empty:continue
                g['threshold']=g.arm.str.split('_').str[-1].astype(int);g=g.sort_values('threshold')
                mean=g[metric+'_mean'].to_numpy(dtype=float)*scale;lo=g[metric+'_min'].to_numpy(dtype=float)*scale;hi=g[metric+'_max'].to_numpy(dtype=float)*scale
                ax.errorbar(g.threshold,mean,yerr=[mean-lo,hi-mean],marker='o',capsize=3,label=f'N={fleet}')
            ax.set_title(city+': '+title,fontsize=10);ax.set_xlabel('AV ETA allowance (seconds)');ax.set_xticks([0,120,240,480]);ax.grid(alpha=.2);ax.legend(fontsize=8)
    fig.suptitle('Cross-city AV threshold comparison\nFixed source cohorts; whiskers show initialization-seed ranges, not city-level uncertainty')
    fig.savefig(output/'city_policy_curves.png',dpi=160);fig.savefig(output/'city_policy_curves.pdf');plt.close(fig)
    if reposition_study:
        fig,axes=plt.subplots(len(cities),4,figsize=(16,3.5*len(cities)),squeeze=False,layout='constrained')
        panels=[('completed',1,'Completion change'),('av_utilization',100,'AV occupied change (pp)'),
                ('eligible_wait_mean_s',1,'Eligible wait change (s)'),('fleet_empty_distance_km',1,'Fleet empty change (km)')]
        for city,axrow in zip(cities,axes):
            subset=data[data.city.eq(city)];pairs=[]
            for fleet in sorted(subset.fleet_size.unique()):
                values=subset[subset.fleet_size.eq(fleet)]
                for arm in sorted(a for a in values.arm.unique() if a.endswith('_repo')):
                    off=arm.removesuffix('_repo')
                    if off not in set(values.arm):continue
                    a=values[values.arm.eq(off)].set_index('seed');b=values[values.arm.eq(arm)].set_index('seed');seeds=sorted(set(a.index)&set(b.index))
                    pairs.append((f'N={fleet}\n{off.replace("threshold_","T")}',a.loc[seeds],b.loc[seeds]))
            for ax,(metric,scale,title) in zip(axrow,panels):
                for index,(_,a,b) in enumerate(pairs):
                    delta=(b[metric]-a[metric]).dropna().to_numpy()*scale
                    if not len(delta):continue
                    mean=delta.mean();ax.errorbar([index],[mean],yerr=[[mean-delta.min()],[delta.max()-mean]],fmt='o',capsize=4)
                ax.axhline(0,color='black',linewidth=.8);ax.set_xticks(range(len(pairs)),[x[0] for x in pairs],fontsize=8)
                ax.set_title(city+': '+title,fontsize=10);ax.grid(alpha=.2)
        fig.suptitle('AV demand repositioning ON minus OFF at matched thresholds\nStationary separate-reference spatial weights; whiskers show paired-seed ranges')
        fig.savefig(output/'av_repositioning_comparison.png',dpi=160);fig.savefig(output/'av_repositioning_comparison.pdf');plt.close(fig)
    return dict(physical_runs=physical,unique_conditions=len(rows),replay_records=len(replays),source_digest=source)
