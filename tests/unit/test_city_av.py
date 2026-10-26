import copy
import json
from types import SimpleNamespace

import pandas as pd
import pytest

from src.misc.seeding import STREAM_SCHEME,file_digest
from tests.integration.test_city_av_examples import city_fixture
from tools.city_av.build import build,integer_column
from tools.city_av.run import validate_city_pair
from tools.synthetic_market.worker import verify_bundle


@pytest.mark.parametrize('value',[1.5,float('inf'),float('nan')])
def test_native_city_ids_reject_nonintegral_or_missing_values(value):
    with pytest.raises(ValueError):integer_column(pd.Series([value]),'request_id')


def test_reference_fence_and_placement_do_not_consume_evaluation_pickups(tmp_path):
    cfg,_=city_fixture(tmp_path/'source');first=tmp_path/'first';build(cfg,cfg.parent,first)
    demand=pd.read_csv(cfg.parent/'requests.csv');demand.to_csv(cfg.parent/'requests_before.csv',index=False)
    demand.loc[demand.rq_time.ge(1800),'start']=2;demand.loc[demand.rq_time.ge(1800),'end']=0
    demand.to_csv(cfg.parent/'requests.csv',index=False);second=tmp_path/'second';build(cfg,cfg.parent,second)
    a=json.loads((first/'manifest.json').read_text());b=json.loads((second/'manifest.json').read_text())
    assert a['av_product']['fence_zones']==b['av_product']['fence_zones']==[10]
    assert (first/'initial_distribution.csv').read_bytes()==(second/'initial_distribution.csv').read_bytes()
    assert set(a['reference']['request_ids']).isdisjoint(set(pd.read_csv(first/'demand/requests.csv').request_id))


@pytest.mark.parametrize('problem',['duplicate_request','duplicate_node','future_reference'])
def test_invalid_city_input_fails_before_bundle_creation(tmp_path,problem):
    cfg,c=city_fixture(tmp_path/'source')
    if problem=='duplicate_request':
        d=pd.read_csv(cfg.parent/'requests.csv');d.loc[1,'request_id']=d.loc[0,'request_id'];d.to_csv(cfg.parent/'requests.csv',index=False)
    elif problem=='duplicate_node':
        d=pd.read_csv(cfg.parent/'zones.csv');d.loc[1,'node_index']=d.loc[0,'node_index'];d.to_csv(cfg.parent/'zones.csv',index=False)
    else:c['reference_end']=1800;cfg.write_text(json.dumps(c))
    with pytest.raises(ValueError):build(cfg,cfg.parent,tmp_path/'bundle')
    assert not (tmp_path/'bundle').exists()


def test_private_bundle_and_routing_runtime_tampering_fail_closed(tmp_path):
    cfg,_=city_fixture(tmp_path/'source');bundle=tmp_path/'bundle';build(cfg,cfg.parent,bundle)
    manifest=json.loads((bundle/'manifest.json').read_text());assert verify_bundle(bundle)['status']=='complete'
    manifest['runtime_files_sha256']={'tools/city_av/__init__.py':'0'*64};(bundle/'manifest.json').write_text(json.dumps(manifest))
    with pytest.raises(ValueError,match='routing runtime'):verify_bundle(bundle)
    manifest.pop('runtime_files_sha256');(bundle/'manifest.json').write_text(json.dumps(manifest))
    with (bundle/'demand/requests.csv').open('a') as f:f.write('\n')
    with pytest.raises(ValueError,match='hash mismatch'):verify_bundle(bundle)


def test_public_overlapping_memberships_need_explicit_audited_tie_rule(tmp_path):
    cfg,c=city_fixture(tmp_path/'source')
    zones=pd.read_csv(cfg.parent/'zones.csv');zones=pd.concat([zones,pd.DataFrame([dict(node_index=0,zone_id=20)])],ignore_index=True)
    zones.to_csv(cfg.parent/'zones.csv',index=False)
    with pytest.raises(ValueError,match='Duplicate mapped node'):build(cfg,cfg.parent,tmp_path/'rejected')
    c['zone_overlap_policy']='lowest_zone_id';cfg.write_text(json.dumps(c));bundle=tmp_path/'accepted';build(cfg,cfg.parent,bundle)
    meta=json.loads((bundle/'manifest.json').read_text());audit=meta['mapping_normalization']
    assert audit['duplicate_nodes']==1 and audit['selected_memberships']==[{'node_index':0,'zone_id':10}]
    assert audit['affected_evaluation_requests']>0 and len(audit['original_memberships'])==2
    assert file_digest(cfg.parent/'zones.csv')==meta['zone_source_sha256']


def test_city_replacement_allows_only_type_change_not_background_drift():
    audit=dict(scheme=STREAM_SCHEME,mode='independent',master_seed=3,demand={'demand':{'count':5}},network_input_sha256={'nodes':'n'},initial_vehicle_count=6,initial_vehicle_state_sha256='human')
    first=dict(city='test',fleet_size=6,av_count=0,shared_placement_sha256='positions_soc',random_audit=audit)
    second=copy.deepcopy(first);second['av_count']=3;second['random_audit']['initial_vehicle_state_sha256']='mixed'
    validate_city_pair(first,second)
    second['shared_placement_sha256']='different'
    with pytest.raises(ValueError,match='placement'):validate_city_pair(first,second)
    second=copy.deepcopy(first);second['random_audit']['master_seed']=4
    with pytest.raises(ValueError,match='master_seed'):validate_city_pair(first,second)


def test_human_counterfactual_retains_separate_slot_search_budget():
    from src.fleetctrl.pooling.immediate.searchVehicles import veh_search_for_immediate_request
    from src.misc.globals import G_RH_I_NWS
    cars=[SimpleNamespace(pos=(n,None,None),vid=n,status=0,is_av=False) for n in range(3)]
    def route(positions,destination,max_routes,max_cost_value):
        return [(p,p[0]+1,p[0]+1,100) for p in sorted(positions)[:max_routes]]
    fc=SimpleNamespace(sim_vehicles=cars,pos_veh_dict_time=-1,pos_veh_dict={},av_product=None,city_shadow_av_ids={2},
                       rv_heuristics={G_RH_I_NWS:1},routing_engine=SimpleNamespace(return_travel_costs_Xto1=route))
    request=SimpleNamespace(get_o_stop_info=lambda:((5,None,None),0,100))
    found,_=veh_search_for_immediate_request(0,request,fc)
    assert [v.vid for v in found]==[0,2]  # one position from each slot group
    del fc.city_shadow_av_ids
    ordinary,_=veh_search_for_immediate_request(0,request,fc)
    assert [v.vid for v in ordinary]==[0]  # unchanged ordinary human-only search


@pytest.mark.parametrize('status,incoming,outgoing,valid',[
    ('boarding','5','4',True),  # actual four-seat exchange: 4 before, 4 after
    ('boarding','5',None,False),  # five remain seated; missing CSV field
    ('boarding',None,'4',False), # five arrive seated
    ('route',None,None,False),   # five travelling is never allowed
])
def test_stationary_exchange_union_is_not_a_license_to_exceed_capacity(status,incoming,outgoing,valid):
    from tools.city_av.report import capacity_audit
    legs=pd.DataFrame([dict(vehicle_id=0,status=status,occupancy=5,rq_on_board='1;2;3;4;5',rq_boarding=incoming,rq_alighting=outgoing)])
    users=pd.DataFrame(dict(request_id=[1,2,3,4,5],number_passenger=[1]*5)).set_index('request_id')
    if valid:assert capacity_audit(legs,users,{0:4})==1
    else:
        with pytest.raises(RuntimeError,match='capacity violation'):capacity_audit(legs,users,{0:4})
