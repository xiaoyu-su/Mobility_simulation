"""Hand-computed KPI units/denominators, snapshots and input guards."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from src.misc.seeding import file_digest
from tools.policy_compare.metrics import CATALOG,measure
from tools.policy_compare.report import movement
from tools.policy_compare.run import parse_spec
from tools.paired_eval.statistics import paired_statistics


@pytest.fixture
def physical(tmp_path):
    specs=tmp_path/'archived_specs';specs.mkdir();(specs/'test.csv').write_text('maximum_passengers,4\nper_km_cost [cent],100\ndaily_fix_cost [cent],2400\n')
    (tmp_path/'00_config.json').write_text(json.dumps(dict(non_simulation_fixture='hand_computed_kpi_accounting',scenario_parameters=dict(start_time=0,end_time=600),directories={'vehicles':'/missing/original/location'})))
    pd.DataFrame(dict(operator_id=[0]*3,vehicle_id=[0,1,2],vehicle_type=['test']*3)).to_csv(tmp_path/'2_vehicle_types.csv',index=False)
    pd.DataFrame(dict(request_id=[0,1],operator_id=[0,np.nan],vehicle_id=[0,np.nan],rq_time=[0,100],pickup_time=[200,np.nan],dropoff_time=[300,np.nan],promised_pickup_time=[100,np.nan],fare=[1000,np.nan],number_passenger=[1,1])).to_csv(tmp_path/'1_user-stats.csv',index=False)
    rows=[]
    for vid,status,start,end,distance,occupancy,onboard,incoming,outgoing in [(0,'route',0,200,1000,0,'','',''),(0,'boarding',200,230,0,1,'0','0',''),(0,'route',230,300,1000,1,'0','',''),(0,'boarding',300,330,0,1,'0','','0'),(2,'out_of_service',0,600,0,0,'','','')]:
        rows.append(dict(operator_id=0,vehicle_id=vid,status=status,start_time=start,end_time=end,driven_distance=distance,occupancy=occupancy,toll=0,rq_on_board=onboard,rq_boarding=incoming,rq_alighting=outgoing))
    pd.DataFrame(rows).to_csv(tmp_path/'2-0_op-stats.csv',index=False)
    (tmp_path/'random_streams.json').write_text(json.dumps({'demand':{'demand':{'count':2}}}));(tmp_path/'final_state.csv').write_text('vehicle_id\n0\n1\n2\n');(tmp_path/'standard_eval.csv').write_text('metric,value\ncompleted,1\n')
    return tmp_path,specs,{'test.csv':file_digest(specs/'test.csv')}


def test_hand_computed_clock_idle_completion_and_snapshot_costs(physical):
    root,specs,hashes=physical;v,frame,checks=measure(root,cost_hashes=hashes,specification_directory=specs)
    assert set(v)==set(CATALOG)
    assert v['requests']==2 and v['completed']==1 and v['unserved']==1 and v['completion_rate']==.5
    assert v['wait_mean_s']==v['wait_p95_s']==200 and v['pickup_late_rate']==1
    assert v['utilization']==pytest.approx(130/1200) and v['idle_share']==pytest.approx(870/1200)
    assert v['empty_distance_km']==1 and v['empty_distance_share']==.5
    assert v['human_earnings_per_online_hour_mean_cent']==pytest.approx(2300)
    assert v['human_earnings_gini'] is None and v['av_utilization'] is None and v['eligible_wait_mean_s'] is None
    assert checks['accepted_promises_checked'] and frame.served.sum()==1
    decisions=pd.DataFrame(dict(operator_id=[0]*4,request_id=[0,0,1,1],vehicle_id=[1,0,0,0],attempt=[1,2,1,2],accepted=[False,True,False,False],terminal_decline=[False,False,False,True],probability=[.5]*4))
    decisions.to_csv(root/'driver_acceptance_op_0.csv',index=False)
    v,_,_=measure(root,cost_hashes=hashes,specification_directory=specs)
    assert v['reoffered_requests']==1 and v['repeat_driver_offer_attempts']==1 and v['terminal_declined_requests']==1
    assert v['driver_offer_attempts']==4 and v['driver_acceptances']==1
    decisions.loc[0,'terminal_decline']=True;decisions.to_csv(root/'driver_acceptance_op_0.csv',index=False)
    with pytest.raises(ValueError,match='Terminally declined'):measure(root,cost_hashes=hashes,specification_directory=specs)


def test_fraction_changes_distinguish_pp_from_relative_percent():
    s=paired_statistics([.5,.5],[.6,.6]);v=movement(s,'fraction')
    assert v['change_percentage_points']==pytest.approx(10) and v['relative_change_percent']==pytest.approx(20)


def test_zero_baseline_relative_change_is_unavailable():
    v=movement(paired_statistics([0,0],[1,1]),'requests')
    assert v['relative_change_percent'] is None and v['change_percentage_points'] is None


@pytest.mark.parametrize('fault',['duplicate','unfinished','chronology','unknown_vehicle','cost'])
def test_physical_and_cost_corruption_is_rejected(physical,fault):
    root,specs,hashes=physical
    if fault=='cost':(specs/'test.csv').write_text('maximum_passengers,4\nper_km_cost [cent],900\ndaily_fix_cost [cent],2400\n')
    elif fault in ['duplicate','unfinished','unknown_vehicle']:
        p=root/'1_user-stats.csv';u=pd.read_csv(p)
        if fault=='duplicate':u.loc[1,'request_id']=0
        elif fault=='unfinished':u.loc[0,'dropoff_time']=np.nan
        else:u.loc[0,'vehicle_id']=99
        u.to_csv(p,index=False)
    else:
        p=root/'2-0_op-stats.csv';legs=pd.read_csv(p);legs.loc[1,'start_time']=190;legs.to_csv(p,index=False)
    with pytest.raises((ValueError,RuntimeError)):measure(root,cost_hashes=hashes,specification_directory=specs)


@pytest.mark.parametrize('fault',['names','seeds','unknown','missing','boolean_seed','noise'])
def test_spec_rejects_ambiguous_policy_identity_and_unmatched_setup(tmp_path,fault):
    original=Path('studies/policy_comparison/insertion.json').resolve();s=json.loads(original.read_text())
    s['constant_config']=str((original.parent/s['constant_config']).resolve())
    for p in [s['reference'],*s['policies']]:p['scenario']=str((original.parent/p['scenario']).resolve())
    if fault=='names':s['policies'][0]['name']=s['reference']['name']
    elif fault=='seeds':s['seeds']=[0,0]
    elif fault=='unknown':s['extra']='unrecognized'
    elif fault=='missing':del s['reference']
    elif fault=='boolean_seed':s['seeds']=[True]
    else:s['network_tt_noise_sigma']=-1
    p=tmp_path/'spec.json';p.write_text(json.dumps(s))
    with pytest.raises(ValueError):parse_spec(p)
