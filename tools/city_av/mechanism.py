"""Read-only, exact time-accounting diagnostics for matched threshold/speed studies.

This attributes recorded utilization algebraically, not causal mechanisms in the
field. Candidate ETAs describe the retained search in each observed policy state.
"""

import argparse
from io import BytesIO
import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.fleetctrl.av_product import opt_in
from src.misc.seeding import file_digest
from tools.city_av.report import capacity_audit
from tools.city_av.run import validate_city_pair
from tools.paired_eval.__main__ import source_record
from tools.synthetic_market.build import json_write
from tools.synthetic_market.report import request_ids
from tools.synthetic_market.worker import verify_bundle


def clipped(first, last, start, end):
    return (np.minimum(last, end) - np.maximum(first, start)).clip(lower=0)


def occupied_accounting(users, legs, av_ids, start, end):
    """Reconcile log occupancy with passenger intervals, alighting dwell and overlap.

    A user dropoff timestamp is the start of alighting. Vehicle logs retain that
    passenger through the end of the boarding/alighting leg. Their difference is
    explicit here; stationary exchange unions are included in logged overlap.
    """
    if not np.isfinite([start, end]).all() or end <= start:
        raise ValueError('Invalid accounting window')
    served = users.dropoff_time.notna() & users.vehicle_id.isin(av_ids)
    a = users[served]
    if a.alighting_end.isna().any() or a.alighting_end.lt(a.dropoff_time).any():
        raise ValueError('Missing/invalid physical alighting endpoint')
    moving = legs.vehicle_id.isin(av_ids)
    duration = clipped(legs.start_time, legs.end_time, start, end)
    occupied = float(duration[moving & legs.occupancy.gt(0)].sum())
    logged_passenger = float((duration[moving] * legs.loc[moving, 'occupancy']).sum())
    sizes = a.number_passenger
    in_window = clipped(a.pickup_time, a.dropoff_time, start, end) * sizes
    held = clipped(a.pickup_time, a.alighting_end, start, end) * sizes
    dwell = clipped(a.dropoff_time, a.alighting_end, start, end) * sizes
    union = 0.0
    for _, group in a.groupby('vehicle_id'):
        intervals = sorted((max(start, x), min(end, y)) for x, y in zip(group.pickup_time, group.alighting_end)
                           if min(end, y) > max(start, x))
        right = start
        for first, last in intervals:
            union += max(0, last - max(first, right))
            right = max(right, last)
    if not np.isclose(union, occupied, rtol=1e-10, atol=1e-6):
        raise ValueError('Occupied vehicle time differs from actual passenger-holding union')
    if not np.isclose(held.sum(), logged_passenger, rtol=1e-10, atol=1e-6):
        raise ValueError('Logged occupancy differs from passenger-holding exposure')
    evaluation = a.is_evaluation_request
    full = (a.dropoff_time - a.pickup_time) * sizes
    before = (np.minimum(a.dropoff_time, start) - a.pickup_time).clip(lower=0) * sizes
    after = (a.dropoff_time - np.maximum(a.pickup_time, end)).clip(lower=0) * sizes
    count = int(evaluation.sum())
    overlap = logged_passenger - occupied
    result = dict(av_completed=count, occupied_vehicle_s=occupied,
        av_online_s=len(av_ids) * (end-start), eval_full_passenger_s=float(full[evaluation].sum()),
        eval_before_window_passenger_s=float(before[evaluation].sum()),
        eval_after_window_passenger_s=float(after[evaluation].sum()),
        warmup_inside_window_passenger_s=float(in_window[~evaluation].sum()),
        alighting_dwell_passenger_s=float(dwell.sum()), logged_overlap_passenger_s=overlap,
        mean_eval_passenger_s_per_booking=float(full[evaluation].sum()/count) if count else 0.0,
        mean_eval_in_vehicle_s=float((a.dropoff_time-a.pickup_time)[evaluation].mean()) if count else None)
    bridge = (result['eval_full_passenger_s']-result['eval_before_window_passenger_s']
              -result['eval_after_window_passenger_s']+result['warmup_inside_window_passenger_s']
              +result['alighting_dwell_passenger_s']-overlap)
    if overlap < -1e-6 or not np.isclose(bridge, occupied, rtol=1e-10, atol=1e-6):
        raise ValueError('Passenger/cohort/service/overlap time bridge does not close')
    result['bridge_residual_s'] = float(bridge-occupied)
    result['av_utilization'] = occupied/result['av_online_s'] if av_ids else None
    return result


def paired_accounting(control, candidate):
    """Symmetric two-factor decomposition, including count-duration interaction."""
    if control['av_online_s'] != candidate['av_online_s'] or not control['av_online_s']:
        raise ValueError('Accounting contrasts require identical nonzero AV online exposure')
    c0, c1 = control['av_completed'], candidate['av_completed']
    d0, d1 = control['mean_eval_passenger_s_per_booking'], candidate['mean_eval_passenger_s_per_booking']
    terms = dict(completion_count_s=(d0+d1)/2*(c1-c0), passenger_duration_s=(c0+c1)/2*(d1-d0))
    for key, sign in [('eval_before_window_passenger_s',-1),('eval_after_window_passenger_s',-1),
                      ('warmup_inside_window_passenger_s',1),('alighting_dwell_passenger_s',1),
                      ('logged_overlap_passenger_s',-1)]:
        terms[key] = sign*(candidate[key]-control[key])
    delta = candidate['occupied_vehicle_s']-control['occupied_vehicle_s']
    if not np.isclose(sum(terms.values()), delta, rtol=1e-10, atol=1e-6):
        raise ValueError('Paired occupied-time components do not reconcile')
    return dict(completed_change=c1-c0, occupied_change_s=delta,
                utilization_change_pp=100*delta/control['av_online_s'], **terms,
                residual_s=float(sum(terms.values())-delta))


def _read(path, hashes, name, table=False):
    if name not in hashes or file_digest(path/name) != hashes[name]:
        raise ValueError(f'Missing/changed mechanism input: {path/name}')
    data = (path/name).read_bytes()
    # Hash the exact bytes that are parsed, not a later read of the same path.
    import hashlib
    if hashlib.sha256(data).hexdigest() != hashes[name]:
        raise ValueError('Mechanism input changed while reading')
    return pd.read_csv(BytesIO(data), low_memory=False) if table else json.loads(data)


def inspect_run(entry, bundle, meta):
    folder = Path(entry['output']); hashes = entry['output_sha256']; inputs = meta['output_sha256']
    for name, h in hashes.items():
        if file_digest(folder/name) != h:
            raise ValueError(f'Raw mechanism output changed: {folder/name}')
    read = lambda name, table=False: _read(folder, hashes, name, table)
    users = read('1_user-stats.csv', True).set_index('request_id')
    legs = read('2-0_op-stats.csv', True); roster = read('2_vehicle_types.csv', True)
    cohort = _read(bundle, inputs, 'observed_cohort.csv', True).set_index('request_id')
    demand = _read(bundle, inputs, 'demand/requests.csv', True).set_index('request_id')
    if not users.index.is_unique or set(users.index) != set(cohort.index) or set(users.index) != set(demand.index):
        raise ValueError('Incomplete/duplicate mechanism demand accounting')
    served = users.dropoff_time.notna()
    if not users.pickup_time.notna().equals(served) or not users.promised_pickup_time.notna().equals(served):
        raise ValueError('Mechanism run contains unfinished accepted service')
    if (users.dropoff_time-users.pickup_time).lt(0).any() or (users.pickup_time-cohort.request_s).lt(-1e-7).any():
        raise ValueError('Noncausal mechanism passenger timestamps')
    config = read('00_config.json')['scenario_parameters']
    if config.get('op_av_repositioning') or config.get('op_repo_method') or config.get('network_tt_noise_sigma',0):
        raise ValueError('Threshold/speed mechanism profile requires repositioning and noise off')
    if config.get('op_driver_acceptance') not in (None,False,'off'):
        raise ValueError('Threshold/speed mechanism profile requires human acceptance off')
    report = read('city_report.json'); tail = read('completion_tail.json'); contract = read('market_input_contract.json')
    if report['rule_violations'] or not contract['all_booked_requests_completed'] or tail['status'] != 'complete' or tail['remaining_tasks'] or tail['onboard_request_ids']:
        raise ValueError('Incomplete/invalid physical mechanism run')
    if contract['booked_requests'] != int(served.sum()) or contract['completed_requests'] != int(served.sum()):
        raise ValueError('Accepted-booking count differs from actual completed demand')
    ids = set(roster.loc[roster.vehicle_type.eq('av_vehtype'),'vehicle_id'])
    if len(roster) != meta['fleet_size'] or roster.vehicle_id.duplicated().any():
        raise ValueError('Invalid mechanism roster')
    if not np.isfinite(legs[['start_time','end_time','occupancy','driven_distance']]).all().all() or legs.end_time.lt(legs.start_time).any():
        raise ValueError('Invalid mechanism vehicle activity')
    for _, group in legs.groupby('vehicle_id'):
        group = group.sort_values(['start_time','end_time'])
        if np.any(group.start_time.to_numpy()[1:] < group.end_time.to_numpy()[:-1]-1e-7):
            raise ValueError('Overlapping mechanism vehicle legs')
    capacities = {r.vehicle_id:float(pd.read_csv(bundle/'vehicles'/f'{r.vehicle_type}.csv',header=None,index_col=0).iloc[:,0]['maximum_passengers']) for r in roster.itertuples()}
    capacity_audit(legs, users, capacities)
    boarded = {}; alighted = {}
    private = set(demand.index[demand.pooling_allowed.eq(0)])
    for leg in legs.itertuples():
        if leg.status == 'out_of_service':
            raise ValueError('Mechanism profile unexpectedly executes shifts')
        if leg.status != 'boarding':
            if leg.status == 'route' and leg.occupancy > 1 and private.intersection(request_ids(leg.rq_on_board)):
                raise ValueError('Mechanism run pools a private booking')
            continue
        incoming = request_ids(leg.rq_boarding); outgoing = request_ids(leg.rq_alighting)
        service = [demand.loc[rid,'pickup_service_time'] for rid in incoming] + [demand.loc[rid,'dropoff_service_time'] for rid in outgoing]
        if service and leg.end_time-leg.start_time < max(service)-1e-7:
            raise ValueError('Mechanism run shortens actual passenger service')
        for column, target, timestamp in [('rq_boarding',boarded,'pickup_time'),('rq_alighting',alighted,'dropoff_time')]:
            for rid in request_ids(getattr(leg,column)):
                if rid in target or rid not in users.index or users.loc[rid,'vehicle_id'] != leg.vehicle_id or not np.isclose(users.loc[rid,timestamp],leg.start_time,rtol=0,atol=1e-6):
                    raise ValueError('Actual passenger event differs from user timestamps/vehicle')
                target[rid] = leg.end_time
    if set(boarded) != set(alighted) or set(boarded) != set(users.index[served]):
        raise ValueError('Mechanism passenger events do not match completed demand')
    users['alighting_end'] = users.index.to_series().map(alighted)
    users['is_evaluation_request'] = cohort.is_evaluation_request
    if report['completed'] != int((served & users.is_evaluation_request).sum()):
        raise ValueError('Evaluation cohort completion differs from physical report')
    mapping = _read(bundle, inputs, 'zones/network/node_zone_info.csv', True).set_index('node_index').zone_id
    fence = set(meta['av_product']['fence_zones']); share = meta['av_product']['opt_in_share']
    users['eligible'] = cohort.start.map(mapping).isin(fence) & cohort.end.map(mapping).isin(fence) & cohort.index.to_series().map(lambda rid:opt_in(rid,0,share))
    users['product'] = np.where(served, np.where(users.vehicle_id.isin(ids),'av','human'),'unserved')
    if ((users['product']=='av') & ~users.eligible).any():
        raise ValueError('Mechanism AV service violates endpoint/opt-in contract')
    users['request_s'] = cohort.request_s; users['wait_s'] = users.pickup_time-cohort.request_s
    users['in_vehicle_s'] = users.dropoff_time-users.pickup_time
    users['decision_reason'] = 'no_threshold_record'; users['retained_eta_gap_s'] = np.nan
    decisions = []
    if ids:
        product = read('av_product_op_0.json')
        if product.get('eta_threshold_seconds') is None:
            raise ValueError('Mechanism profile requires explicit ETA-threshold dispatch')
        if set(product['av_ids']) != ids:
            raise ValueError('Mechanism AV audit roster differs')
        decisions = product['threshold_decisions']
        for event in decisions:
            rid = event['request_id']
            if rid not in users.index:
                raise ValueError('Unknown mechanism threshold request')
            av, human = event['best_av_eta_s'], event['best_human_eta_s']
            if event['threshold_s'] != config['op_av_eta_threshold_s'] or any(x is not None and (not np.isfinite(x) or x < 0) for x in [av,human]):
                raise ValueError('Invalid mechanism threshold/retained ETA')
            qualifies = av is not None and (human is None or av <= human+event['threshold_s']+1e-9)
            expected = 'av' if qualifies else 'human' if human is not None else 'none'
            if event['selected_pool'] != expected:
                raise ValueError('Invalid recorded threshold selection')
            reason = ('ineligible' if not users.loc[rid,'eligible'] else 'no_retained_candidates' if av is None and human is None
                      else 'no_retained_av' if av is None else 'no_retained_human' if human is None
                      else 'av_within_allowance' if qualifies else 'human_outside_allowance')
            users.loc[rid,'decision_reason'] = reason
            users.loc[rid,'retained_eta_gap_s'] = av-human if av is not None and human is not None else np.nan
        last = {e['request_id']:e for e in decisions}
        for rid in users.index[served]:
            if rid in last and (users.loc[rid,'product']=='av') != (last[rid]['selected_pool']=='av'):
                raise ValueError('Actual accepted product differs from final threshold decision')
    start, end = meta['evaluation_start'], meta['evaluation_end']
    accounting = occupied_accounting(users, legs, ids, start, end)
    if accounting['av_completed'] != report['av_completed'] or ids and not np.isclose(accounting['av_utilization'],report['av_utilization'],rtol=0,atol=1e-10):
        raise ValueError('Mechanism time/count differs from published physical report')
    key = dict(city=meta['city'],fleet_size=meta['fleet_size'],seed=entry['seed'],arm=entry['arm'])
    result = dict(**key, **accounting, threshold_s=report['eta_threshold_seconds'],factor=report['av_travel_time_factor'],
                  completed=report['completed'],fleet_empty_distance_km=report['fleet_empty_distance_km'])
    bins = []
    for t in range(start,end,900):
        z = min(t+900,end); duration = clipped(legs.start_time,legs.end_time,t,z)
        chosen = [e for e in decisions if t <= e['time'] < z and users.loc[e['request_id'],'eligible']]
        bins.append(dict(**key,start=t,end=z,av_occupied_s=float(duration[legs.vehicle_id.isin(ids)&legs.occupancy.gt(0)].sum()),
            eligible_arrivals=int((users.eligible & users.request_s.ge(t) & users.request_s.lt(z)).sum()),
            av_pickups=int((users['product'].eq('av') & users.pickup_time.ge(t) & users.pickup_time.lt(z)).sum()),
            eligible_decision_events=len(chosen),no_retained_av_events=sum(e['best_av_eta_s'] is None for e in chosen),av_choice_events=sum(e['selected_pool']=='av' for e in chosen)))
    frame = users[['is_evaluation_request','eligible','product','vehicle_id','request_s','pickup_time','dropoff_time','alighting_end','wait_s','in_vehicle_s','number_passenger','decision_reason','retained_eta_gap_s']].reset_index()
    for name, value in key.items():frame[name] = value
    return result, frame, bins


def analyze(experiments, output):
    output = Path(output)
    if output.exists():raise ValueError('Refusing to overwrite mechanism report')
    source = source_record(); rows = []; frames = []; bins = []; seen = set(); inputs = []; backgrounds = {}; typed = {}; audits = []
    for path in map(Path,experiments):
        manifest_hash = file_digest(path/'manifest.json'); m = json.loads((path/'manifest.json').read_text())
        if m['status'] != 'complete' or m['source']['code_digest'] != source['code_digest']:
            raise ValueError('Mechanism study must be complete and use the current frozen source')
        if any(e['status'] != 'complete' or e['returncode'] != 0 for e in m['runs']):raise ValueError('Incomplete mechanism worker')
        for name,h in m['output_sha256'].items():
            if file_digest(path/name) != h:raise ValueError('Changed mechanism study report')
        bundles = {}
        for city, record in m['bundles'].items():
            bundle = Path(record['path'])
            if file_digest(bundle/'manifest.json') != record['manifest_sha256']:raise ValueError('Changed mechanism input manifest')
            bundles[city] = (bundle,verify_bundle(bundle))
        for entry in m['runs']:
            bundle,meta = bundles[entry['city']]
            key = (meta['city'],meta['fleet_size'],entry['seed'],entry['arm'])
            if key in seen:raise ValueError('Duplicate mechanism condition; analyze exact replays separately')
            seen.add(key); row,frame,time_bins = inspect_run(entry,bundle,meta)
            folder = Path(entry['output']); report = json.loads((folder/'city_report.json').read_text())
            pair = dict(city=row['city'],fleet_size=row['fleet_size'],av_count=report['av_count'],
                shared_placement_sha256=report['shared_placement_sha256'],random_audit=json.loads((folder/'random_streams.json').read_text()))
            background_key = key[:3]
            if background_key in backgrounds:validate_city_pair(backgrounds[background_key],pair)
            else:backgrounds[background_key] = pair
            typed_key = (*background_key, report['av_count'])
            if typed_key in typed:validate_city_pair(typed[typed_key],pair)
            else:typed[typed_key] = pair
            rows.append(row); frames.append(frame); bins.extend(time_bins)
            audits.append(dict(**{k:row[k] for k in ['city','fleet_size','seed','arm']},output=str(folder),output_sha256=entry['output_sha256'],all_physical_checks_pass=True,bridge_residual_s=row['bridge_residual_s']))
        inputs.append(dict(path=str(path),manifest_sha256=manifest_hash))
    if not rows:raise ValueError('No mechanism runs')
    data = pd.DataFrame(rows); paired = []; transitions = []
    for _,group in data[data.av_online_s.gt(0)].groupby(['city','fleet_size','seed']):
        records = {r['arm']:r for r in group.to_dict('records')}
        for arm,candidate in records.items():
            controls = [r for r in records.values() if (r['factor']==candidate['factor'] and r['threshold_s']==0 and candidate['threshold_s']!=0)
                        or (r['threshold_s']==candidate['threshold_s'] and r['factor']==1 and candidate['factor']==1.25)]
            for control in controls:
                contrast = dict(city=candidate['city'],fleet_size=candidate['fleet_size'],seed=candidate['seed'],control=control['arm'],candidate=arm)
                paired.append(dict(**contrast,**paired_accounting(control,candidate)))
                a = next(f for f in frames if (f.city.iloc[0],f.fleet_size.iloc[0],f.seed.iloc[0],f.arm.iloc[0])==(control['city'],control['fleet_size'],control['seed'],control['arm'])).set_index('request_id')
                b = next(f for f in frames if (f.city.iloc[0],f.fleet_size.iloc[0],f.seed.iloc[0],f.arm.iloc[0])==(candidate['city'],candidate['fleet_size'],candidate['seed'],arm)).set_index('request_id')
                if set(a.index)!=set(b.index):raise ValueError('Mechanism contrast has different demand identities')
                for first in ['av','human','unserved']:
                    for last in ['av','human','unserved']:
                        mask=a.is_evaluation_request & a['product'].eq(first) & b['product'].eq(last)
                        wait=b.loc[mask,'wait_s']-a.loc[mask,'wait_s']
                        transitions.append(dict(**contrast,control_product=first,candidate_product=last,requests=int(mask.sum()),common_served_wait_change_s=float(wait.mean()) if wait.notna().any() else None))
    output.mkdir(parents=True)
    data.to_csv(output/'seed_accounting.csv',index=False);pd.concat(frames).to_csv(output/'request_mechanisms.csv',index=False)
    pd.DataFrame(bins).to_csv(output/'time_bins.csv',index=False);pd.DataFrame(paired).to_csv(output/'paired_accounting.csv',index=False)
    pd.DataFrame(transitions).to_csv(output/'product_transitions.csv',index=False)
    numeric=[c for c in data.select_dtypes('number') if c not in ['seed','fleet_size']]
    summary=data.groupby(['city','fleet_size','arm'],as_index=False)[numeric].mean();summary.to_csv(output/'configuration_accounting.csv',index=False)
    from tools.city_av.mechanism_plot import plot_report
    plot_report(data,pd.DataFrame(paired),output)
    if source_record()['code_digest'] != source['code_digest'] or any(file_digest(Path(r['path'])/'manifest.json')!=r['manifest_sha256'] for r in inputs):
        raise ValueError('Mechanism inputs/source changed during analysis')
    result=dict(status='complete',source=source,physical_runs=len(rows),unique_conditions=len(seen),inputs=inputs,
        all_physical_checks_pass=True,all_accounting_bridges_close=True,paired_contrasts=len(paired),checks=audits,
        definition='User pickup-to-dropoff timestamps exclude alighting dwell; logged holding includes that dwell. Logged overlap includes stationary exchange unions and multi-passenger bookings.',
        scope='Exact accounting of observed benchmark policies; no identified causal mediator or field/geography effect. Retained candidate search absence is not proof that no vehicle was feasible.',
        output_sha256={p.name:file_digest(p) for p in output.iterdir() if p.is_file()})
    json_write(output/'manifest.json',result)
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--experiments',nargs='+',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();print(json.dumps({k:v for k,v in analyze(args.experiments,args.output).items() if k not in ['source','checks','output_sha256']},indent=2))


if __name__=='__main__':main()
