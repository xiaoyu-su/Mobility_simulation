"""Matched booking-patience sensitivity with explicit realized pickup lateness.

The cutoff limits accepted offers. Actual execution can arrive later; this
report preserves those observations and never cancels an accepted passenger.
"""
import argparse
from io import BytesIO
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.misc.seeding import canonical_digest,file_digest
from tools.city_av.mechanism import inspect_run,_read
from tools.city_av.summary import METRICS,REPLAY_FILES,bundle_contract,verified_city_bundle
from tools.paired_eval.__main__ import source_record
from tools.paired_eval.statistics import paired_statistics
from tools.synthetic_market.build import json_write


EXTRA=['offered_wait_mean_s','within_limit_completed','within_480s_completed','late_actual_pickups',
       'late_actual_pickup_rate','late_actual_pickup_mean_s','late_actual_pickup_max_s']


def static_basis(meta):
    """Permit exactly the declared patience/config/deadline intervention."""
    config={k:v for k,v in meta['config'].items() if k!='max_wait_seconds'}
    files={k:v for k,v in meta['output_sha256'].items() if k not in ['parameters.json','demand/requests.csv']}
    return dict(config=config,files=files,dependencies=meta['dependencies'],
                runtime=meta.get('runtime_files_sha256',{}),fleet_size=meta['fleet_size'],av_product=meta['av_product'])


def deadline_metrics(users,cohort,demand,patience):
    """Check accepted-offer limits; quantify actual lateness without hiding it."""
    if not np.isfinite(patience) or patience<=0:raise ValueError('Invalid patience cutoff')
    users=users.loc[cohort.index];demand=demand.loc[cohort.index]
    if not np.allclose(demand.latest_start_time,cohort.request_s+patience,rtol=0,atol=1e-6):
        raise ValueError('Patience deadline is not anchored to original request time')
    served=users.dropoff_time.notna();promised=users.promised_pickup_time.notna()
    if not promised.equals(served):raise ValueError('Incomplete accepted patience booking')
    promise_gap=users.promised_pickup_time-demand.latest_start_time
    if promise_gap.gt(1e-6).any():raise ValueError('Accepted offer exceeds declared booking-patience deadline')
    gap=users.pickup_time-demand.latest_start_time;selected=served&cohort.is_evaluation_request
    late=selected&gap.gt(1e-6);n=int(selected.sum());count=int(late.sum())
    return dict(offered_wait_mean_s=float((users.promised_pickup_time-cohort.request_s)[selected].mean()) if n else None,
        within_limit_completed=int((selected&~late).sum()),
        within_480s_completed=int((selected&(users.pickup_time-cohort.request_s).le(480+1e-6)).sum()),late_actual_pickups=count,
        late_actual_pickup_rate=count/n if n else None,
        late_actual_pickup_mean_s=float(gap[late].mean()) if count else 0.,
        late_actual_pickup_max_s=float(gap[late].max()) if count else 0.,
        full_late_actual_pickups=int((served&gap.gt(1e-6)).sum()),accepted_offer_deadline_violations=0)


def verify_patience_change(first_path,first,second_path,second):
    if static_basis(first)!=static_basis(second):raise ValueError('Patience sensitivity changes an uncontrolled input')
    a=_read(first_path,first['output_sha256'],'parameters.json');b=_read(second_path,second['output_sha256'],'parameters.json')
    if {k:v for k,v in a.items() if k!='op_max_wait_time'}!={k:v for k,v in b.items() if k!='op_max_wait_time'}:
        raise ValueError('Patience sensitivity changes other simulation parameters')
    x=_read(first_path,first['output_sha256'],'demand/requests.csv',True);y=_read(second_path,second['output_sha256'],'demand/requests.csv',True)
    try:pd.testing.assert_frame_equal(x.drop(columns='latest_start_time'),y.drop(columns='latest_start_time'),check_exact=True)
    except AssertionError as e:raise ValueError('Patience sensitivity changes request identities or non-deadline fields') from e


def analyze(experiments,output):
    output=Path(output)
    if output.exists():raise ValueError('Refusing to overwrite patience report')
    source=source_record();inputs=[];regimes={};bases={};conditions={};frames={};rows=[];replays=[];checks=[];backgrounds={};background_checks=0;physical=0
    for path in map(Path,experiments):
        h=file_digest(path/'manifest.json');m=json.loads((path/'manifest.json').read_text())
        if m['status']!='complete' or m['source']['code_digest']!=source['code_digest'] or any(e['status']!='complete' or e['returncode']!=0 for e in m['runs']):
            raise ValueError('Patience studies must be complete and use the current frozen source')
        for name,digest in m['output_sha256'].items():
            if file_digest(path/name)!=digest:raise ValueError('Changed patience study output')
        bundles={}
        for city,record in m['bundles'].items():
            bundle=Path(record['path']);meta=verified_city_bundle(bundle,record['manifest_sha256'])
            if meta['source']['code_digest']!=source['code_digest']:raise ValueError('Patience bundle source changed; rebuild inputs')
            patience=meta['config']['max_wait_seconds'];identity=(city,meta['fleet_size']);stratum=(*identity,patience)
            if stratum in regimes and bundle_contract(regimes[stratum][1])!=bundle_contract(meta):raise ValueError('Incompatible input snapshots inside a patience stratum')
            if identity in bases:verify_patience_change(*bases[identity],bundle,meta)
            else:bases[identity]=(bundle,meta)
            regimes[stratum]=(bundle,meta);bundles[city]=(bundle,meta,patience)
        for entry in m['runs']:
            physical+=1;bundle,meta,patience=bundles[entry['city']];folder=Path(entry['output'])
            if entry['arm'] not in ['all_human','threshold_0','threshold_240']:raise ValueError('Unsupported patience policy arm')
            _,frame,_=inspect_run(entry,bundle,meta)
            users=_read(folder,entry['output_sha256'],'1_user-stats.csv',True).set_index('request_id')
            cohort=_read(bundle,meta['output_sha256'],'observed_cohort.csv',True).set_index('request_id')
            demand=_read(bundle,meta['output_sha256'],'demand/requests.csv',True).set_index('request_id')
            params=_read(bundle,meta['output_sha256'],'parameters.json');settings=_read(folder,entry['output_sha256'],'00_config.json')['scenario_parameters']
            if params['op_max_wait_time']!=patience or settings['op_max_wait_time']!=patience:raise ValueError('Actual patience parameter differs from its stratum')
            metrics=deadline_metrics(users,cohort,demand,patience);report=_read(folder,entry['output_sha256'],'city_report.json')
            if entry['arm']!='all_human' and (report['av_travel_time_factor']!=1.25 or report['eta_threshold_seconds']!=int(entry['arm'].split('_')[-1]) or report['preference_seconds']!=0):
                raise ValueError('Patience profile changes threshold/speed/preference outside its declared grid')
            audit=_read(folder,entry['output_sha256'],'random_streams.json')
            # Round-trip float parsing is needed to reproduce the recorded SOC hash.
            placement_bytes=(folder/'initial_placement.csv').read_bytes()
            if hashlib.sha256(placement_bytes).hexdigest()!=entry['output_sha256']['initial_placement.csv']:raise ValueError('Patience initial placement changed')
            placement=pd.read_csv(BytesIO(placement_bytes),float_precision='round_trip')
            roster=_read(folder,entry['output_sha256'],'2_vehicle_types.csv',True).set_index('vehicle_id').vehicle_type
            actual=[[int(r.operator_id),int(r.vehicle_id),str((int(r.node_index),None,None)),float(r.soc),roster.loc[r.vehicle_id]] for r in placement.sort_values(['operator_id','vehicle_id']).itertuples()]
            if canonical_digest(actual)!=audit['initial_vehicle_state_sha256']:raise ValueError('Actual patience initial state differs from its audit')
            key=(meta['city'],meta['fleet_size'],patience,entry['seed'],entry['arm']);background=(key[0],key[1],key[3],key[4])
            if key in conditions:
                old=conditions[key];names=[]
                for name in [*REPLAY_FILES,'standard_eval.csv','final_state.csv']:
                    a,b=old/name,folder/name
                    if a.exists()!=b.exists() or a.exists() and a.read_bytes()!=b.read_bytes():raise ValueError('Fresh-process patience replay differs')
                    if a.exists():names.append(name)
                replays.append(dict(city=key[0],fleet_size=key[1],patience_s=patience,seed=key[3],arm=key[4],byte_identical_files=names))
            else:
                if background in backgrounds:
                    old=backgrounds[background]
                    if old['placement_sha256']!=file_digest(folder/'initial_placement.csv'):raise ValueError('Patience comparison changes geometry/SOC')
                    for field in ['scheme','mode','master_seed','network_input_sha256','initial_vehicle_count','initial_vehicle_state_sha256']:
                        if old['audit'][field]!=audit[field]:raise ValueError(f'Patience comparison changes {field}')
                    background_checks+=1
                else:backgrounds[background]=dict(placement_sha256=file_digest(folder/'initial_placement.csv'),audit=audit)
                conditions[key]=folder;frames[key]=frame.set_index('request_id')
                rows.append(dict(seed=entry['seed'],arm=entry['arm'],patience_s=patience,**report,**metrics))
            checks.append(dict(city=key[0],fleet_size=key[1],patience_s=patience,seed=key[3],arm=key[4],all_physical_contracts_pass=True,**metrics,output=str(folder),output_sha256=entry['output_sha256']))
        inputs.append(dict(path=str(path),manifest_sha256=h))
    if not rows:raise ValueError('No patience study records')
    data=pd.DataFrame(rows).sort_values(['city','fleet_size','patience_s','seed','arm']);summary=[];effects=[];common=[]
    metrics=METRICS+EXTRA
    for (city,fleet,patience,arm),g in data.groupby(['city','fleet_size','patience_s','arm']):
        row=dict(city=city,fleet_size=int(fleet),patience_s=float(patience),arm=arm,seeds=len(g))
        for metric in metrics:
            values=g[metric].dropna()
            for kind in ['mean','min','max']:row[metric+'_'+kind]=float(getattr(values,kind)()) if len(values) else None
        summary.append(row)
        contrasts=[]
        for control in ['all_human','threshold_0']:
            if control!=arm:contrasts.append((patience,control,'policy_within_patience'))
        if patience!=480:contrasts.append((480,arm,'patience_at_fixed_policy'))
        for base_patience,control,kind in contrasts:
            base=data[data.city.eq(city)&data.fleet_size.eq(fleet)&data.patience_s.eq(base_patience)&data.arm.eq(control)].set_index('seed');candidate=g.set_index('seed');seeds=sorted(set(base.index)&set(candidate.index))
            if not seeds:continue
            fields=dict(city=city,fleet_size=int(fleet),patience_s=float(patience),arm=arm,control_patience_s=float(base_patience),control=control,contrast=kind)
            for metric in metrics:effects.append(dict(**fields,metric=metric,**paired_statistics(base.loc[seeds,metric].to_numpy(dtype=float),candidate.loc[seeds,metric].to_numpy(dtype=float))))
            for seed in seeds:
                a=frames[city,fleet,base_patience,seed,control];b=frames[city,fleet,patience,seed,arm].loc[a.index]
                mask=a.is_evaluation_request&a['product'].ne('unserved')&b['product'].ne('unserved')
                delta=b.wait_s-a.wait_s
                for label,selection in [('all',mask),('eligible',mask&a.eligible),('other',mask&~a.eligible)]:
                    v=delta[selection];common.append(dict(**fields,seed=seed,group=label,common_served=int(selection.sum()),mean_wait_change_s=float(v.mean()) if len(v) else None,improved=int(v.lt(-1e-6).sum()),worsened=int(v.gt(1e-6).sum()),unchanged=int(v.abs().le(1e-6).sum())))
    output.mkdir(parents=True)
    data.to_csv(output/'seed_results.csv',index=False);pd.DataFrame(summary).to_csv(output/'configuration_summary.csv',index=False)
    pd.DataFrame(effects).to_csv(output/'paired_effects.csv',index=False);pd.DataFrame(common).to_csv(output/'common_rider_effects.csv',index=False)
    from tools.city_av.patience_plot import plot_report
    plot_report(data,pd.DataFrame(summary),output)
    if source_record()['code_digest']!=source['code_digest'] or any(file_digest(Path(i['path'])/'manifest.json')!=i['manifest_sha256'] for i in inputs):raise ValueError('Patience source/input changed during reporting')
    result=dict(status='complete',source=source,physical_runs=physical,unique_conditions=len(rows),fresh_process_replays=replays,patience_strata=len(regimes),matched_patience_background_checks=background_checks,inputs=inputs,
        all_physical_contracts_pass=True,all_booking_deadline_promises_valid=True,actual_lateness_preserved=True,checks=checks,
        scope='Assumed booking/offer cutoff sensitivity, not identified cancellation behavior or field calibration; accepted bookings complete even when execution is late',
        output_sha256={p.name:file_digest(p) for p in output.iterdir() if p.is_file()})
    json_write(output/'manifest.json',result);return result


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--experiments',type=Path,nargs='+',required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();r=analyze(args.experiments,args.output);print(json.dumps({k:v for k,v in r.items() if k not in ['source','checks','output_sha256','fresh_process_replays']},indent=2))


if __name__=='__main__':main()
