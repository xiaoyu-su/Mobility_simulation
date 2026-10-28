"""Shared geometry for human-only and replacement-AV counterfactual fleets."""

import pandas as pd

from src.misc.globals import G_V_INIT_NODE, G_V_INIT_SOC, G_V_INIT_TIME
from src.misc.seeding import derive_rng
from tools.synthetic_market.build import json_write


def initialize_shared(simulation, bundle, manifest):
    """Initialize the same positions/SOC before changing the designated slots' type.

    Designated AV slots start inside the fence even in the human-only control.
    No rider tours, shifts or snapshot resumption are supported by this profile.
    """
    if manifest.get('shared_initialization') != 'city-av-placement-v1':
        raise ValueError('Shared placement requires an explicit city AV bundle')
    distribution = pd.read_csv(bundle/'initial_distribution.csv')
    probabilities = dict(zip(distribution.node_index.astype(int), distribution.probability))
    zones = set(manifest['av_product']['fence_zones'])
    mapping = pd.read_csv(bundle/'zones/network/node_zone_info.csv').set_index('node_index').zone_id
    fenced = {n:p for n,p in probabilities.items() if mapping.loc[n] in zones and p > 0}
    if not fenced:
        nodes = sorted(mapping.index[mapping.isin(zones)])
        fenced = {int(n):1/len(nodes) for n in nodes}
    else:
        mass = sum(fenced.values());fenced = {n:p/mass for n,p in fenced.items()}
    first_av = manifest['av_product']['human_count']
    anchor_count=manifest.get('placement_anchor_av_count',manifest['av_product']['av_count'])
    if type(anchor_count) is not int or not manifest['av_product']['av_count']<=anchor_count<manifest['fleet_size']:
        raise ValueError('Invalid city placement anchor count')
    first_anchored=manifest['fleet_size']-anchor_count
    shadow_ids=set(range(first_av,manifest['fleet_size']))
    all_human=simulation.operators[0].av_product is None
    if all_human:simulation.operators[0].city_shadow_av_ids=shadow_ids
    rows = []
    for (operator, vid), vehicle in sorted(simulation.sim_vehicles.items()):
        if operator != 0 or vehicle.pos is not None:
            raise ValueError('City shared initialization requires one fresh, unshifted fleet')
        choices = fenced if vid >= first_anchored else probabilities
        rng = derive_rng(simulation.scenario_parameters['random_seed'], f'vehicle_initialization/{operator}/{vid}')
        draw = rng.random();cumulative = 0;node = next(reversed(choices))
        for candidate, probability in choices.items():
            cumulative += probability
            if cumulative >= draw:
                node = candidate;break
        node=int(node);soc = .5*(1+rng.random());time = simulation.scenario_parameters['start_time']
        vehicle.set_initial_state(simulation.operators[operator], simulation.routing_engine,
                                  {G_V_INIT_NODE:node,G_V_INIT_TIME:time,G_V_INIT_SOC:soc},
                                  time, simulation.init_blocking)
        if vehicle.pos!=(node,None,None) or vehicle.assigned_route:
            raise RuntimeError('Shared initialization did not produce the declared idle position')
        rows.append(dict(operator_id=operator,vehicle_id=vid,node_index=int(vehicle.pos[0]),soc=float(vehicle.soc)))
    pd.DataFrame(rows).to_csv(simulation.dir_names['output']+'/initial_placement.csv',index=False)
    json_write(simulation.dir_names['output']+'/city_search_contract.json',dict(
        designated_slots=sorted(shadow_ids),per_group_position_budget=simulation.scenario_parameters['op_rh_immediate_max_routes'],
        all_human_shadow_groups=all_human,shadow_humans_remain_unrestricted=all_human,
        scope='Same retained/designated slot search budgets; AV eligibility removes designated AV candidates only in mixed arms'))
    if 'placement_anchor_av_count' in manifest:
        path=simulation.dir_names['output']+'/city_placement_anchor.json'
        json_write(path,dict(anchor_slots=list(range(first_anchored,manifest['fleet_size'])),
            actual_av_slots=sorted(shadow_ids),scope='Fixed placement only; search groups still follow actual replacement slots'))
