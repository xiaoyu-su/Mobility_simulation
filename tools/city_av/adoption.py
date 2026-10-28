"""Matched opt-in sensitivity with fixed rider groups and explicit spillovers.

Opt-in is a fixed, nested request-level scenario draw, not an estimated choice
model. The physical dispatch policy is unchanged.
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.fleetctrl.av_product import opt_in
from src.misc.seeding import file_digest
from tools.city_av.mechanism import inspect_run, _read
from tools.city_av.patience import deadline_metrics
from tools.city_av.summary import METRICS, REPLAY_FILES, bundle_contract, verified_city_bundle
from tools.paired_eval.__main__ import source_record
from tools.paired_eval.statistics import paired_statistics
from tools.synthetic_market.build import json_write


SHARES = (0., .3, 1.)
GROUPS = ('baseline_eligible', 'additional_opt_in', 'outside_fence')
EXTRA = ['within_480s_completed', 'late_actual_pickups', 'offered_wait_mean_s']


def static_basis(meta):
    """Permit exactly the opt-in intervention; all demand bytes stay fixed."""
    return dict(config={k:v for k,v in meta['config'].items() if k != 'opt_in_share'},
        files={k:v for k,v in meta['output_sha256'].items() if k != 'parameters.json'},
        av_product={k:v for k,v in meta['av_product'].items() if k != 'opt_in_share'},
        dependencies=meta['dependencies'], runtime=meta.get('runtime_files_sha256', {}),
        fleet_size=meta['fleet_size'], reference=meta.get('reference'),
        provenance=meta.get('provenance'), network_type=meta.get('network_type'))


def verify_adoption_change(first_path, first, second_path, second):
    if static_basis(first) != static_basis(second):
        raise ValueError('Opt-in sensitivity changes an uncontrolled input')
    a = _read(first_path, first['output_sha256'], 'parameters.json')
    b = _read(second_path, second['output_sha256'], 'parameters.json')
    if {k:v for k,v in a.items() if k != 'op_av_opt_in_share'} != {k:v for k,v in b.items() if k != 'op_av_opt_in_share'}:
        raise ValueError('Opt-in sensitivity changes other simulation parameters')


def fixed_groups(cohort, mapping, fence):
    """Fixed groups referenced to 30%, including never-geofenced spillovers."""
    inside = cohort.start.map(mapping).isin(fence) & cohort.end.map(mapping).isin(fence)
    baseline = cohort.index.to_series().map(lambda rid:opt_in(rid, 0, .3)) & inside
    return pd.Series(np.where(baseline, GROUPS[0], np.where(inside, GROUPS[1], GROUPS[2])), index=cohort.index)


def group_metrics(frame, groups):
    if not groups.index.is_unique or not frame.index.is_unique or set(groups.index) != set(frame.index):
        raise ValueError('Fixed rider groups do not align with request identities')
    groups = groups.reindex(frame.index)
    rows = []
    for group in GROUPS:
        selected = frame.is_evaluation_request & groups.eq(group)
        served = selected & frame['product'].ne('unserved')
        n = int(selected.sum()); completed = int(served.sum())
        rows.append(dict(group=group, requests=n, completed=completed,
            completion_rate=completed/n if n else None,
            av_completed=int((served & frame['product'].eq('av')).sum()),
            wait_mean_s=float(frame.loc[served, 'wait_s'].mean()) if completed else None,
            within_480s_completed=int((served & frame.wait_s.le(480+1e-6)).sum())))
    return rows


def analyze(experiments, output):
    output = Path(output)
    if output.exists():raise ValueError('Refusing to overwrite opt-in report')
    source = source_record(); inputs = []; bases = {}; regimes = {}; rows = []; group_rows = []
    conditions = {}; frames = {}; fixed = {}; backgrounds = {}; human_controls = {}; human_checks = []; checks = []; replays = []; physical = 0; background_checks = 0
    for path in map(Path, experiments):
        h = file_digest(path/'manifest.json'); manifest = json.loads((path/'manifest.json').read_text())
        if manifest['status'] != 'complete' or manifest['source']['code_digest'] != source['code_digest'] or any(e['status'] != 'complete' or e['returncode'] != 0 for e in manifest['runs']):
            raise ValueError('Opt-in studies must be complete and use the current frozen source')
        for name, digest in manifest['output_sha256'].items():
            if file_digest(path/name) != digest:raise ValueError('Changed opt-in study output')
        bundles = {}
        for city, record in manifest['bundles'].items():
            bundle = Path(record['path']); meta = verified_city_bundle(bundle, record['manifest_sha256'])
            if meta['source']['code_digest'] != source['code_digest']:raise ValueError('Opt-in bundle source changed; rebuild inputs')
            share = meta['config']['opt_in_share']; identity = (city, meta['fleet_size']); stratum = (*identity, share)
            if share not in SHARES or meta['av_product']['opt_in_share'] != share or meta['config']['max_wait_seconds'] != 480:
                raise ValueError('Unsupported opt-in/patience stratum')
            if stratum in regimes and bundle_contract(regimes[stratum][1]) != bundle_contract(meta):raise ValueError('Incompatible snapshots inside an opt-in stratum')
            if identity in bases:verify_adoption_change(*bases[identity], bundle, meta)
            else:bases[identity] = (bundle, meta)
            regimes[stratum] = (bundle, meta); bundles[city] = (bundle, meta, share)
        for entry in manifest['runs']:
            physical += 1; bundle, meta, share = bundles[entry['city']]; folder = Path(entry['output'])
            if entry['arm'] not in ['all_human', 'threshold_0', 'threshold_240']:raise ValueError('Unsupported opt-in policy arm')
            _, frame, _ = inspect_run(entry, bundle, meta); frame = frame.set_index('request_id')
            cohort = _read(bundle, meta['output_sha256'], 'observed_cohort.csv', True).set_index('request_id')
            demand = _read(bundle, meta['output_sha256'], 'demand/requests.csv', True).set_index('request_id')
            users = _read(folder, entry['output_sha256'], '1_user-stats.csv', True).set_index('request_id')
            settings = _read(folder, entry['output_sha256'], '00_config.json')['scenario_parameters']
            params = _read(bundle, meta['output_sha256'], 'parameters.json')
            if params['op_av_opt_in_share'] != share or settings['op_max_wait_time'] != 480:raise ValueError('Actual parameters differ from opt-in stratum')
            report = _read(folder, entry['output_sha256'], 'city_report.json')
            if entry['arm'] != 'all_human':
                audit = _read(folder, entry['output_sha256'], 'av_product_op_0.json')
                if settings['op_av_opt_in_share'] != share or audit['opt_in_share'] != share or report['av_travel_time_factor'] != 1.25 or report['eta_threshold_seconds'] != int(entry['arm'].split('_')[-1]) or report['preference_seconds'] != 0:
                    raise ValueError('Opt-in profile changes declared adoption/threshold/speed/preference')
            mapping = _read(bundle, meta['output_sha256'], 'zones/network/node_zone_info.csv', True).set_index('node_index').zone_id
            groups = fixed_groups(cohort, mapping, meta['av_product']['fence_zones'])
            identity = (entry['city'], meta['fleet_size'])
            if identity in fixed:
                if not groups.equals(fixed[identity]):raise ValueError('Fixed request groups changed across opt-in strata')
            else:fixed[identity] = groups
            if share == 0 and (frame.eligible.any() or report['av_completed']):raise ValueError('Zero opt-in unexpectedly permits AV service')
            if share == 1 and not frame.eligible.equals(groups.reindex(frame.index).ne('outside_fence')):raise ValueError('Full opt-in differs from endpoint fence')
            key = (*identity, share, entry['seed'], entry['arm']); background = (*identity, entry['seed'], entry['arm'])
            random = _read(folder, entry['output_sha256'], 'random_streams.json')
            current = dict(placement=file_digest(folder/'initial_placement.csv'), audit=random)
            if key in conditions:
                names = []
                for name in [*REPLAY_FILES, 'standard_eval.csv', 'final_state.csv']:
                    a, b = conditions[key]/name, folder/name
                    if a.exists() != b.exists() or a.exists() and a.read_bytes() != b.read_bytes():raise ValueError('Fresh-process opt-in replay differs')
                    if a.exists():names.append(name)
                replays.append(dict(city=key[0], fleet_size=key[1], opt_in_share=share, seed=key[3], arm=key[4], byte_identical_files=names))
            else:
                if background in backgrounds:
                    if backgrounds[background] != current:raise ValueError('Opt-in intervention changes placement/SOC/demand/network/random background')
                    background_checks += 1
                else:backgrounds[background] = current
                conditions[key] = folder; frames[key] = frame
                metrics = deadline_metrics(users, cohort, demand, 480)
                rows.append(dict(seed=entry['seed'], arm=entry['arm'], opt_in_share=share, **report, **metrics))
                group_rows.extend(dict(city=key[0], fleet_size=key[1], opt_in_share=share, seed=key[3], arm=key[4], **r) for r in group_metrics(frame, groups))
                if entry['arm'] == 'all_human':
                    control_key = (*identity, entry['seed'])
                    if control_key in human_controls:
                        names = ['1_user-stats.csv','2-0_op-stats.csv','standard_eval.csv','final_state.csv','initial_placement.csv','random_streams.json','city_search_contract.json']
                        for name in names:
                            if (human_controls[control_key]/name).read_bytes() != (folder/name).read_bytes():raise ValueError('Opt-in changes all-human physical control')
                        human_checks.append(dict(city=key[0], fleet_size=key[1], seed=key[3], opt_in_share=share, byte_identical_files=names))
                    else:human_controls[control_key] = folder
            checks.append(dict(city=key[0], fleet_size=key[1], opt_in_share=share, seed=key[3], arm=key[4], all_physical_contracts_pass=True, output=str(folder), output_sha256=entry['output_sha256']))
        inputs.append(dict(path=str(path), manifest_sha256=h))
    if not rows:raise ValueError('No opt-in study records')
    data = pd.DataFrame(rows).sort_values(['city','fleet_size','opt_in_share','seed','arm']); groups_data = pd.DataFrame(group_rows)
    summary = []; effects = []; group_effects = []; common = []
    for (city, fleet, share, arm), g in data.groupby(['city','fleet_size','opt_in_share','arm']):
        row = dict(city=city, fleet_size=int(fleet), opt_in_share=share, arm=arm, seeds=len(g))
        for metric in METRICS+EXTRA:
            v = g[metric].dropna()
            for kind in ['mean','min','max']:row[metric+'_'+kind] = float(getattr(v,kind)()) if len(v) else None
        summary.append(row)
        contrasts = [(share, control, 'policy_within_opt_in') for control in ['all_human','threshold_0'] if control != arm]
        if share != .3:contrasts.append((.3, arm, 'opt_in_at_fixed_policy'))
        for base_share, control, kind in contrasts:
            a = data[data.city.eq(city) & data.fleet_size.eq(fleet) & data.opt_in_share.eq(base_share) & data.arm.eq(control)].set_index('seed'); b = g.set_index('seed'); seeds = sorted(set(a.index)&set(b.index))
            if not seeds:continue
            fields = dict(city=city, fleet_size=int(fleet), opt_in_share=share, arm=arm, control_opt_in_share=base_share, control=control, contrast=kind)
            for metric in METRICS+EXTRA:effects.append(dict(**fields, metric=metric, **paired_statistics(a.loc[seeds,metric], b.loc[seeds,metric])))
            for group in GROUPS:
                x = groups_data[groups_data.city.eq(city) & groups_data.fleet_size.eq(fleet) & groups_data.opt_in_share.eq(base_share) & groups_data.arm.eq(control) & groups_data.group.eq(group)].set_index('seed')
                y = groups_data[groups_data.city.eq(city) & groups_data.fleet_size.eq(fleet) & groups_data.opt_in_share.eq(share) & groups_data.arm.eq(arm) & groups_data.group.eq(group)].set_index('seed')
                for metric in ['completed','completion_rate','av_completed','wait_mean_s','within_480s_completed']:
                    group_effects.append(dict(**fields, group=group, metric=metric, **paired_statistics(x.loc[seeds,metric], y.loc[seeds,metric])))
            for seed in seeds:
                x = frames[city,fleet,base_share,seed,control]; y = frames[city,fleet,share,seed,arm].loc[x.index]
                matched = x.is_evaluation_request & x['product'].ne('unserved') & y['product'].ne('unserved')
                for group in GROUPS:
                    mask = matched & fixed[city,fleet].eq(group); delta = (y.wait_s-x.wait_s)[mask]
                    common.append(dict(**fields, seed=seed, group=group, common_served=int(mask.sum()), mean_wait_change_s=float(delta.mean()) if len(delta) else None, improved=int(delta.lt(-1e-6).sum()), worsened=int(delta.gt(1e-6).sum()), unchanged=int(delta.abs().le(1e-6).sum())))
    output.mkdir(parents=True)
    for name, table in [('seed_results',data),('configuration_summary',pd.DataFrame(summary)),('fixed_group_results',groups_data),('paired_effects',pd.DataFrame(effects)),('fixed_group_effects',pd.DataFrame(group_effects)),('common_rider_effects',pd.DataFrame(common))]:table.to_csv(output/(name+'.csv'), index=False)
    from tools.city_av.adoption_plot import plot_report
    plot_report(data, pd.DataFrame(summary), groups_data, output)
    if source_record()['code_digest'] != source['code_digest'] or any(file_digest(Path(i['path'])/'manifest.json') != i['manifest_sha256'] for i in inputs):raise ValueError('Opt-in source/input changed during reporting')
    result = dict(status='complete', source=source, physical_runs=physical, unique_conditions=len(rows), fresh_process_replays=replays, opt_in_strata=len(regimes), matched_opt_in_background_checks=background_checks, all_human_invariance_checks=human_checks, inputs=inputs, all_physical_contracts_pass=True, fixed_groups=list(GROUPS), baseline_opt_in_share=.3,
        scope='Fixed nested per-request opt-in assumption sensitivity, not observed rider adoption or a dynamic choice model', checks=checks, output_sha256={p.name:file_digest(p) for p in output.iterdir() if p.is_file()})
    json_write(output/'manifest.json', result); return result


def main():
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--experiments',type=Path,nargs='+',required=True); parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args(); r = analyze(args.experiments,args.output)
    print(json.dumps({k:v for k,v in r.items() if k not in ['source','checks','output_sha256','fresh_process_replays']},indent=2))


if __name__ == '__main__':main()
