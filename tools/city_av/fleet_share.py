"""AV replacement-share sensitivity at fixed total fleet and anchored geometry.

Actual-type candidate-search partitions vary; paired all-human controls retain
that effect separately. Legacy placement remains the default.
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from io import BytesIO
from src.misc.seeding import canonical_digest
from tools.city_av.adoption import fixed_groups, group_metrics, GROUPS
from src.misc.seeding import file_digest
from tools.city_av.mechanism import inspect_run, _read
from tools.city_av.patience import deadline_metrics
from tools.city_av.summary import METRICS, REPLAY_FILES, bundle_contract, verified_city_bundle
from tools.paired_eval.__main__ import source_record
from tools.paired_eval.statistics import paired_statistics
from tools.synthetic_market.build import json_write


SHARES = (.05, .1, .2)
EXTRA = ['within_480s_completed', 'late_actual_pickups', 'offered_wait_mean_s','av_trips_per_online_hour','retained_human_completed','common_human_completed','common_human_trips_per_online_hour']


def static_basis(meta):
    """Permit exactly the fleet-share intervention; all demand bytes stay fixed."""
    return dict(config={k:v for k,v in meta['config'].items() if k != 'av_share'},
        files={k:v for k,v in meta['output_sha256'].items() if k != 'parameters.json'},
        av_product={k:v for k,v in meta['av_product'].items() if k not in ['requested_share','av_count','human_count']},
        dependencies=meta['dependencies'], runtime=meta.get('runtime_files_sha256', {}),
        fleet_size=meta['fleet_size'], placement_anchor_av_count=meta.get('placement_anchor_av_count'), reference=meta.get('reference'),
        provenance=meta.get('provenance'), network_type=meta.get('network_type'))


def verify_fleet_share_change(first_path, first, second_path, second):
    if static_basis(first) != static_basis(second):
        raise ValueError('Fleet-share sensitivity changes an uncontrolled input')
    a = _read(first_path, first['output_sha256'], 'parameters.json')
    b = _read(second_path, second['output_sha256'], 'parameters.json')
    for params,meta in [(a,first),(b,second)]:
        if params['op_fleet_composition']!={'default_vehtype':meta['av_product']['human_count'],'av_vehtype':meta['av_product']['av_count']}:
            raise ValueError('Fleet-share bundle composition differs from its declared counts')
    if {k:v for k,v in a.items() if k != 'op_fleet_composition'} != {k:v for k,v in b.items() if k != 'op_fleet_composition'}:
        raise ValueError('Fleet-share sensitivity changes other simulation parameters')


def analyze(experiments, output):
    output = Path(output)
    if output.exists():raise ValueError('Refusing to overwrite fleet-share report')
    source = source_record(); inputs = []; bases = {}; regimes = {}; rows = []; group_rows = []
    conditions = {}; frames = {}; fixed = {}; backgrounds = {}; human_controls = {}; human_checks = []; checks = []; replays = []; physical = 0; background_checks = 0
    for path in map(Path, experiments):
        h = file_digest(path/'manifest.json'); manifest = json.loads((path/'manifest.json').read_text())
        if manifest['status'] != 'complete' or manifest['source']['code_digest'] != source['code_digest'] or any(e['status'] != 'complete' or e['returncode'] != 0 for e in manifest['runs']):
            raise ValueError('Fleet-share studies must be complete and use the current frozen source')
        for name, digest in manifest['output_sha256'].items():
            if file_digest(path/name) != digest:raise ValueError('Changed fleet-share study output')
        bundles = {}
        for city, record in manifest['bundles'].items():
            bundle = Path(record['path']); meta = verified_city_bundle(bundle, record['manifest_sha256'])
            if meta['source']['code_digest'] != source['code_digest']:raise ValueError('Fleet-share bundle source changed; rebuild inputs')
            share = meta['config']['av_share']; identity = (city, meta['fleet_size']); stratum = (*identity, share)
            if share not in SHARES or meta['av_product']['opt_in_share'] != .3 or meta['config']['max_wait_seconds'] != 480 or meta['config'].get('placement_av_share') != .2:
                raise ValueError('Unsupported fleet-share/patience stratum')
            if stratum in regimes and bundle_contract(regimes[stratum][1]) != bundle_contract(meta):raise ValueError('Incompatible snapshots inside an fleet-share stratum')
            if identity in bases:verify_fleet_share_change(*bases[identity], bundle, meta)
            else:bases[identity] = (bundle, meta)
            regimes[stratum] = (bundle, meta); bundles[city] = (bundle, meta, share)
        for entry in manifest['runs']:
            physical += 1; bundle, meta, share = bundles[entry['city']]; folder = Path(entry['output'])
            if entry['arm'] not in ['all_human', 'threshold_0', 'threshold_240']:raise ValueError('Unsupported fleet-share policy arm')
            _, frame, _ = inspect_run(entry, bundle, meta); frame = frame.set_index('request_id')
            cohort = _read(bundle, meta['output_sha256'], 'observed_cohort.csv', True).set_index('request_id')
            demand = _read(bundle, meta['output_sha256'], 'demand/requests.csv', True).set_index('request_id')
            users = _read(folder, entry['output_sha256'], '1_user-stats.csv', True).set_index('request_id')
            settings = _read(folder, entry['output_sha256'], '00_config.json')['scenario_parameters']
            params = _read(bundle, meta['output_sha256'], 'parameters.json')
            if params['op_av_opt_in_share'] != .3 or settings['op_max_wait_time'] != 480:raise ValueError('Actual parameters differ from fleet-share stratum')
            report = _read(folder, entry['output_sha256'], 'city_report.json')
            if entry['arm'] != 'all_human':
                audit = _read(folder, entry['output_sha256'], 'av_product_op_0.json')
                if settings['op_av_opt_in_share'] != .3 or audit['opt_in_share'] != .3 or report['av_travel_time_factor'] != 1.25 or report['eta_threshold_seconds'] != int(entry['arm'].split('_')[-1]) or report['preference_seconds'] != 0:
                    raise ValueError('Fleet-share profile changes declared adoption/threshold/speed/preference')
            mapping = _read(bundle, meta['output_sha256'], 'zones/network/node_zone_info.csv', True).set_index('node_index').zone_id
            groups = fixed_groups(cohort, mapping, meta['av_product']['fence_zones'])
            identity = (entry['city'], meta['fleet_size'])
            if identity in fixed:
                if not groups.equals(fixed[identity]):raise ValueError('Fixed request groups changed across fleet-share strata')
            else:fixed[identity] = groups
            key = (*identity, share, entry['seed'], entry['arm']); background = (*identity, entry['seed'], entry['arm'])
            random = _read(folder, entry['output_sha256'], 'random_streams.json')
            placement=pd.read_csv(BytesIO((folder/'initial_placement.csv').read_bytes()),float_precision='round_trip')
            roster=_read(folder,entry['output_sha256'],'2_vehicle_types.csv',True).set_index('vehicle_id').vehicle_type
            actual=[[int(r.operator_id),int(r.vehicle_id),str((int(r.node_index),None,None)),float(r.soc),roster.loc[r.vehicle_id]] for r in placement.sort_values(['operator_id','vehicle_id']).itertuples()]
            if canonical_digest(actual)!=random['initial_vehicle_state_sha256']:raise ValueError('Actual fleet-share typed initialization differs from its audit')
            expected=0 if entry['arm']=='all_human' else meta['av_product']['av_count']
            if report['av_count']!=expected or report['human_count']!=meta['fleet_size']-expected:raise ValueError('Actual replacement roster count differs')
            expected_types={i:'av_vehtype' if i>=meta['fleet_size']-expected else 'default_vehtype' for i in range(meta['fleet_size'])}
            if roster.to_dict()!=expected_types:raise ValueError('Actual replacement vehicle IDs/types differ')
            current = dict(placement=file_digest(folder/'initial_placement.csv'), audit={k:v for k,v in random.items() if k!='initial_vehicle_state_sha256'})
            if key in conditions:
                names = []
                for name in [*REPLAY_FILES, 'standard_eval.csv', 'final_state.csv','city_placement_anchor.json']:
                    a, b = conditions[key]/name, folder/name
                    if a.exists() != b.exists() or a.exists() and a.read_bytes() != b.read_bytes():raise ValueError('Fresh-process fleet-share replay differs')
                    if a.exists():names.append(name)
                replays.append(dict(city=key[0], fleet_size=key[1], av_share=share, seed=key[3], arm=key[4], byte_identical_files=names))
            else:
                if background in backgrounds:
                    if backgrounds[background] != current:raise ValueError('Fleet-share intervention changes placement/SOC/demand/network/random background')
                    background_checks += 1
                else:backgrounds[background] = current
                conditions[key] = folder; frames[key] = frame
                metrics = deadline_metrics(users, cohort, demand, 480)
                common_humans=meta['fleet_size']-meta['placement_anchor_av_count']
                metrics['common_human_completed']=int((users.dropoff_time.notna()&cohort.is_evaluation_request&users.vehicle_id.lt(common_humans)).sum())
                metrics['common_human_trips_per_online_hour']=metrics['common_human_completed']/(common_humans*(meta['evaluation_end']-meta['evaluation_start'])/3600)
                rows.append(dict(seed=entry['seed'], arm=entry['arm'], av_share=share, **report, **metrics))
                group_rows.extend(dict(city=key[0], fleet_size=key[1], av_share=share, seed=key[3], arm=key[4], **r) for r in group_metrics(frame, groups))
                if entry['arm'] == 'all_human':
                    control_key = (*identity, entry['seed'])
                    if control_key in human_controls:
                        names = ['1_user-stats.csv','2-0_op-stats.csv','standard_eval.csv','final_state.csv','initial_placement.csv','random_streams.json','city_search_contract.json']
                        identical={name:(human_controls[control_key]/name).read_bytes()==(folder/name).read_bytes() for name in names}
                        human_checks.append(dict(city=key[0],fleet_size=key[1],seed=key[3],av_share=share,physical_files_identical=identical,scope='Search partition sensitivity at fixed geometry; different physical outcomes are retained'))
                    else:human_controls[control_key] = folder
            checks.append(dict(city=key[0], fleet_size=key[1], av_share=share, seed=key[3], arm=key[4], all_physical_contracts_pass=True, output=str(folder), output_sha256=entry['output_sha256']))
        inputs.append(dict(path=str(path), manifest_sha256=h))
    if not rows:raise ValueError('No fleet-share study records')
    data = pd.DataFrame(rows).sort_values(['city','fleet_size','av_share','seed','arm']); groups_data = pd.DataFrame(group_rows)
    summary = []; effects = []; group_effects = []; common = []
    for (city, fleet, share, arm), g in data.groupby(['city','fleet_size','av_share','arm']):
        row = dict(city=city, fleet_size=int(fleet), av_share=share, arm=arm, seeds=len(g))
        for metric in METRICS+EXTRA:
            v = g[metric].dropna()
            for kind in ['mean','min','max']:row[metric+'_'+kind] = float(getattr(v,kind)()) if len(v) else None
        summary.append(row)
        contrasts = [(share, control, 'policy_within_fleet_share') for control in ['all_human','threshold_0'] if control != arm]
        if share != .1:contrasts.append((.1, arm, 'fleet_share_at_fixed_policy'))
        for base_share, control, kind in contrasts:
            a = data[data.city.eq(city) & data.fleet_size.eq(fleet) & data.av_share.eq(base_share) & data.arm.eq(control)].set_index('seed'); b = g.set_index('seed'); seeds = sorted(set(a.index)&set(b.index))
            if not seeds:continue
            fields = dict(city=city, fleet_size=int(fleet), av_share=share, arm=arm, control_av_share=base_share, control=control, contrast=kind)
            for metric in METRICS+EXTRA:effects.append(dict(**fields, metric=metric, **paired_statistics(a.loc[seeds,metric], b.loc[seeds,metric])))
            for group in GROUPS:
                x = groups_data[groups_data.city.eq(city) & groups_data.fleet_size.eq(fleet) & groups_data.av_share.eq(base_share) & groups_data.arm.eq(control) & groups_data.group.eq(group)].set_index('seed')
                y = groups_data[groups_data.city.eq(city) & groups_data.fleet_size.eq(fleet) & groups_data.av_share.eq(share) & groups_data.arm.eq(arm) & groups_data.group.eq(group)].set_index('seed')
                for metric in ['completed','completion_rate','av_completed','wait_mean_s','within_480s_completed']:
                    group_effects.append(dict(**fields, group=group, metric=metric, **paired_statistics(x.loc[seeds,metric], y.loc[seeds,metric])))
            for seed in seeds:
                x = frames[city,fleet,base_share,seed,control]; y = frames[city,fleet,share,seed,arm].loc[x.index]
                matched = x.is_evaluation_request & x['product'].ne('unserved') & y['product'].ne('unserved')
                for group in GROUPS:
                    mask = matched & fixed[city,fleet].eq(group); delta = (y.wait_s-x.wait_s)[mask]
                    common.append(dict(**fields, seed=seed, group=group, common_served=int(mask.sum()), mean_wait_change_s=float(delta.mean()) if len(delta) else None, improved=int(delta.lt(-1e-6).sum()), worsened=int(delta.gt(1e-6).sum()), unchanged=int(delta.abs().le(1e-6).sum())))
    adjusted=[]
    for (city,fleet,share,arm),g in data.groupby(['city','fleet_size','av_share','arm']):
        if share==.1 or arm=='all_human':continue
        select=lambda sh,ar:data[data.city.eq(city)&data.fleet_size.eq(fleet)&data.av_share.eq(sh)&data.arm.eq(ar)].set_index('seed')
        base,base_human,candidate,candidate_human=select(.1,arm),select(.1,'all_human'),select(share,arm),select(share,'all_human')
        seeds=sorted(set(base.index)&set(base_human.index)&set(candidate.index)&set(candidate_human.index))
        if not seeds:continue
        for metric in ['completed','within_480s_completed','fleet_empty_distance_km','eligible_wait_mean_s','other_wait_mean_s']:
            adjusted.append(dict(city=city,fleet_size=int(fleet),av_share=share,arm=arm,control_av_share=.1,metric=metric,**paired_statistics(base.loc[seeds,metric]-base_human.loc[seeds,metric],candidate.loc[seeds,metric]-candidate_human.loc[seeds,metric])))
    output.mkdir(parents=True)
    for name, table in [('control_adjusted_share_effects',pd.DataFrame(adjusted)),('seed_results',data),('configuration_summary',pd.DataFrame(summary)),('fixed_group_results',groups_data),('paired_effects',pd.DataFrame(effects)),('fixed_group_effects',pd.DataFrame(group_effects)),('common_rider_effects',pd.DataFrame(common))]:table.to_csv(output/(name+'.csv'), index=False)
    from tools.city_av.fleet_share_plot import plot_report
    plot_report(data, pd.DataFrame(summary), groups_data, output)
    if source_record()['code_digest'] != source['code_digest'] or any(file_digest(Path(i['path'])/'manifest.json') != i['manifest_sha256'] for i in inputs):raise ValueError('Fleet-share source/input changed during reporting')
    result = dict(status='complete', source=source, physical_runs=physical, unique_conditions=len(rows), fresh_process_replays=replays, fleet_share_strata=len(regimes), matched_fleet_share_background_checks=background_checks, all_human_partition_checks=human_checks, inputs=inputs, all_physical_contracts_pass=True, fixed_groups=list(GROUPS), baseline_av_share=.1,
        scope='Fixed total fleet and anchored placement; actual-type search partitions vary and their all-human outcomes are retained; scenario sensitivity, not observed AV supply', checks=checks, output_sha256={p.name:file_digest(p) for p in output.iterdir() if p.is_file()})
    json_write(output/'manifest.json', result); return result


def main():
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--experiments',type=Path,nargs='+',required=True); parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args(); r = analyze(args.experiments,args.output)
    print(json.dumps({k:v for k,v in r.items() if k not in ['source','checks','output_sha256','fresh_process_replays']},indent=2))


if __name__ == '__main__':main()
