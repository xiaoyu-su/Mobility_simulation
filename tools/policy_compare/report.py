"""A shared, read-only comparison surface with explicit input/source strata."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from src.misc.seeding import canonical_digest,file_digest
from tools.city_av.summary import bundle_contract,verified_city_bundle
from tools.paired_eval.__main__ import source_record,validate_pair
from tools.paired_eval.statistics import paired_statistics
from tools.policy_compare.metrics import CATALOG,catalog,measure
from tools.synthetic_market.build import json_write

CRITICAL=['1_user-stats.csv','2-0_op-stats.csv','2_vehicle_types.csv','standard_eval.csv','final_state.csv','random_streams.json','initial_placement.csv','driver_acceptance_op_0.csv','driver_choice_op_0.csv','av_product_op_0.json','city_search_contract.json','city_placement_anchor.json']


def verify_files(root,hashes):
    root=Path(root).resolve()
    for name,h in hashes.items():
        path=(root/name).resolve()
        if not path.is_relative_to(root) or not path.is_file() or file_digest(path)!=h:raise ValueError(f'Changed or invalid sealed input/output: {root/name}')


def load_records(experiments,reference):
    records=[];inputs=[];groups={}
    for directory in map(Path,experiments):
        directory=directory.resolve();m=json.loads((directory/'manifest.json').read_text());digest=file_digest(directory/'manifest.json')
        if m['status']!='complete' or not m.get('runs') or any(e.get('status','complete')!='complete' or e.get('returncode',0)!=0 for e in m['runs']):raise ValueError('Comparison requires complete successful experiments')
        source=m['source']['code_digest']
        if m.get('kind')=='policy_comparison_v1':
            kind='matching';ref=reference or m['reference']
            if ref!=m['reference']:raise ValueError('Matching reference must equal its declared paired control')
            verify_files(directory/'configs',m['configuration_sha256']);verify_files(directory/'vehicle_specs',m['cost_files_sha256'])
            for child in m['children']:
                path=(directory/child['directory']).resolve()
                if not path.is_relative_to(directory) or file_digest(path/'manifest.json')!=child['manifest_sha256']:raise ValueError('Changed paired child manifest')
                c=json.loads((path/'manifest.json').read_text());verify_files(path/'configs',c['config_sha256']);verify_files(path,c['report_sha256'])
            sid=canonical_digest(dict(kind=kind,source=source,context=m['comparison_context']))[:20]
            groups[sid]=dict(kind=kind,label=m['name'],simulation_source_digest=source,reference=ref,context=m['comparison_context'])
            for e in m['runs']:
                folder=(directory/e['directory']).resolve()
                if not folder.is_relative_to(directory):raise ValueError('Comparison run escapes its snapshot')
                records.append(dict(stratum=sid,kind=kind,reference=ref,seed=e['seed'],arm=e['arm'],folder=folder,hashes=e['output_sha256'],bundle=None,meta=None,cost_hashes=m['cost_files_sha256'],specification_directory=directory/'vehicle_specs'))
        elif 'bundles' in m and isinstance(m['bundles'],dict):
            kind='city';ref=reference or 'all_human';verify_files(directory,m['output_sha256']);bundles={}
            for city,b in m['bundles'].items():
                path=Path(b['path']);meta=verified_city_bundle(path,b['manifest_sha256'])
                if meta['source']['code_digest']!=source:raise ValueError('City input and simulation source versions differ')
                sid=canonical_digest(dict(kind=kind,source=source,city=city,contract=bundle_contract(meta)))[:20]
                groups[sid]=dict(kind=kind,label=f"{city}, N{meta['fleet_size']}, AV target {meta['config']['av_share']*100:g}%",simulation_source_digest=source,reference=ref,city=city,fleet_size=meta['fleet_size'],config=meta['config'],bundle_manifest_sha256=b['manifest_sha256'])
                bundles[city]=(sid,path,meta)
            for e in m['runs']:
                sid,bundle,meta=bundles[e['city']]
                records.append(dict(stratum=sid,kind=kind,reference=ref,seed=e['seed'],arm=e['arm'],folder=Path(e['output']),hashes=e['output_sha256'],bundle=bundle,meta=meta,cost_hashes=None,specification_directory=bundle/'vehicles'))
        else:raise ValueError('Unsealed/unsupported legacy manifest: use policy_compare run for matching, city_av run for AVs; windowed/market/legacy AV studies retain their dedicated cohort-aware reports')
        inputs.append(dict(path=str(directory),manifest_sha256=digest))
    return records,groups,inputs


def matched(reference,candidate,kind):
    a=json.loads((reference['folder']/'random_streams.json').read_text());b=json.loads((candidate['folder']/'random_streams.json').read_text())
    if kind=='matching':validate_pair(a,b)
    else:
        for field in ['scheme','mode','master_seed','demand','network_input_sha256','initial_vehicle_count']:
            if a[field]!=b[field]:raise ValueError(f'Unmatched city background: {field}')
        if a['mode']!='independent':raise ValueError('City comparisons require independent named random streams')
        if (reference['folder']/'initial_placement.csv').read_bytes()!=(candidate['folder']/'initial_placement.csv').read_bytes():raise ValueError('City policy comparison changes positions/SOC')
        if reference['values']['av_count']==candidate['values']['av_count'] and a['initial_vehicle_state_sha256']!=b['initial_vehicle_state_sha256']:raise ValueError('City comparison changes typed initial state')
    x=reference['frame'];y=candidate['frame']
    if set(x.index)!=set(y.index):raise ValueError('Policy comparisons require the same request IDs')
    try:pd.testing.assert_frame_equal(x[['request_s','is_evaluation_request']],y.loc[x.index,['request_s','is_evaluation_request']],check_exact=True)
    except AssertionError as e:raise ValueError('Policy comparison changes request clock/cohort') from e


def movement(stats,unit):
    delta=stats['mean_difference'];base=stats['baseline_mean']
    return dict(direction='unavailable' if not np.isfinite(delta) else 'increase' if delta>1e-12 else 'decrease' if delta < -1e-12 else 'unchanged',
        relative_change_percent=float(100*delta/abs(base)) if np.isfinite(delta) and np.isfinite(base) and abs(base)>1e-12 else None,
        change_percentage_points=float(100*delta) if unit=='fraction' and np.isfinite(delta) else None)


def report(experiments,output,reference=None):
    output=Path(output)
    if output.exists():raise ValueError('Refusing to overwrite comparison report')
    renderer=source_record();records,groups,inputs=load_records(experiments,reference);unique={};rows=[];checks=[];replays=[];background_checks=[]
    if not records:raise ValueError('No complete records to compare')
    for r in records:
        verify_files(r['folder'],r['hashes']);key=(r['stratum'],r['seed'],r['arm'])
        if key in unique:
            old=unique[key];names=[]
            for name in CRITICAL:
                a,b=old['folder']/name,r['folder']/name
                if a.exists()!=b.exists() or a.exists() and a.read_bytes()!=b.read_bytes():raise ValueError('Duplicate condition is not an exact physical replay')
                if a.exists():names.append(name)
            replays.append(dict(stratum=key[0],seed=key[1],arm=key[2],byte_identical_files=names));continue
        values,frame,check=measure(r['folder'],r['bundle'],r['meta'],r['cost_hashes'],r['specification_directory']);r.update(values=values,frame=frame);unique[key]=r
        if r['kind']=='city':
            expected=0 if r['arm']=='all_human' else r['meta']['av_product']['av_count']
            if values['av_count']!=expected:raise ValueError('City actual AV roster differs from its policy regime')
        rows.append(dict(stratum=key[0],seed=key[1],arm=key[2],**values));checks.append(dict(stratum=key[0],seed=key[1],arm=key[2],folder=str(r['folder']),output_sha256=r['hashes'],**check))
    data=pd.DataFrame(rows);summaries=[];effects=[];common=[];policy_parameters={}
    for sid,group in data.groupby('stratum'):
        ref=groups[sid]['reference'];policies=sorted(group.arm.unique())
        if ref not in policies:raise ValueError(f'Missing reference policy {ref} in stratum {sid}')
        base=group[group.arm.eq(ref)].set_index('seed');base_parameters=json.loads((unique[sid,int(base.index[0]),ref]['folder']/'00_config.json').read_text())['scenario_parameters'];policy_parameters[sid]={}
        for arm in policies:
            g=group[group.arm.eq(arm)].set_index('seed')
            if set(g.index)!=set(base.index):raise ValueError('Unmatched seed sets; refusing partial paired comparison')
            seeds=sorted(base.index)
            actual=json.loads((unique[sid,int(seeds[0]),arm]['folder']/'00_config.json').read_text())['scenario_parameters']
            signature=lambda p:{k:v for k,v in p.items() if k.startswith('op_') or k=='network_tt_noise_sigma'}
            for seed in seeds:
                parameters=json.loads((unique[sid,int(seed),arm]['folder']/'00_config.json').read_text())['scenario_parameters']
                if signature(parameters)!=signature(actual):raise ValueError('Named policy changes operator/noise parameters across seeds')
            policy_parameters[sid][arm]={k:dict(reference=base_parameters.get(k),candidate=actual.get(k)) for k in sorted(set(base_parameters)|set(actual)) if (k.startswith('op_') or k=='network_tt_noise_sigma') and base_parameters.get(k)!=actual.get(k)}
            for seed in seeds:
                matched(unique[sid,seed,ref],unique[sid,seed,arm],groups[sid]['kind']);background_checks.append(dict(stratum=sid,seed=int(seed),reference=ref,arm=arm))
            for metric,(unit,preference,definition) in CATALOG.items():
                values=g[metric].dropna();summaries.append(dict(stratum=sid,arm=arm,metric=metric,unit=unit,seeds=len(g),n_available=len(values),mean=float(values.mean()) if len(values) else None,min=float(values.min()) if len(values) else None,max=float(values.max()) if len(values) else None))
                if arm==ref:continue
                stats=paired_statistics(base.loc[seeds,metric].to_numpy(dtype=float),g.loc[seeds,metric].to_numpy(dtype=float))
                effects.append(dict(stratum=sid,reference=ref,arm=arm,metric=metric,unit=unit,preference=preference,definition=definition,**stats,**movement(stats,unit)))
            if arm==ref:continue
            for seed in seeds:
                a=unique[sid,seed,ref]['frame'];b=unique[sid,seed,arm]['frame'].loc[a.index];mask=a.is_evaluation_request&a.served&b.served;delta=b.wait_s-a.wait_s
                selections={'all':mask}
                if 'eligible' in a:selections.update(eligible=mask&a.eligible,other=mask&~a.eligible)
                for name,selected in selections.items():common.append(dict(stratum=sid,reference=ref,arm=arm,seed=seed,group=name,common_served=int(selected.sum()),wait_change_mean_s=float(delta[selected].mean()) if selected.any() else None))
    if not effects:raise ValueError('At least one candidate policy is required in each comparison')
    # Validate snapshots again before publishing any report artifacts.
    for i in inputs:
        if file_digest(Path(i['path'])/'manifest.json')!=i['manifest_sha256']:raise ValueError('Experiment changed during report generation')
    if source_record()['code_digest']!=renderer['code_digest']:raise ValueError('Reporting source changed during analysis')
    output.mkdir(parents=True);data.to_csv(output/'seed_kpis.csv',index=False);pd.DataFrame(summaries).to_csv(output/'policy_summary.csv',index=False);pd.DataFrame(effects).to_csv(output/'kpi_movements.csv',index=False);pd.DataFrame(common).to_csv(output/'common_rider_waits.csv',index=False)
    json_write(output/'policy_parameters.json',policy_parameters);json_write(output/'kpi_catalog.json',catalog());json_write(output/'strata.json',groups)
    from tools.policy_compare.plot import render
    render(data,pd.DataFrame(effects),groups,output)
    result=dict(schema_version=1,status='complete',reporting_source=renderer,simulation_sources=sorted({g['simulation_source_digest'] for g in groups.values()}),physical_records=len(records),unique_conditions=len(unique),replays=replays,strata=len(groups),inputs=inputs,physical_checks=checks,matched_background_checks=background_checks,
        inference='Paired seed uncertainty conditional on fixed source cohorts; no pooling across source/input strata, no automatic policy winner; common-served waits exclude riders not served in both arms',output_sha256={p.name:file_digest(p) for p in output.iterdir() if p.is_file()})
    json_write(output/'manifest.json',result);return result
