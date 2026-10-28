"""Loaded nested replacement counts, fixed actual geometry and physical replay."""
import json
from pathlib import Path
import pandas as pd
import pytest
from tests.integration.test_city_av_examples import city_fixture,run_city
from tools.city_av.fleet_share import analyze
from tools.city_av.summary import summarize


@pytest.mark.integration
@pytest.mark.parametrize('router,controller',[('NetworkBasicWithStore','PoolingIRSOnly'),
    ('NetworkBasicWithStoreCpp','PoolingIRSOnly'),('NetworkBasicWithStore','PoolingIRSAssignmentBatchOptimization')])
def test_fleet_shares_keep_actual_positions_soc_and_eligibility_fixed(tmp_path,router,controller):
    if router.endswith('Cpp'):pytest.importorskip('src.routing.road.cpp_router.PyNetwork')
    cfg,c=city_fixture(tmp_path/'source',router);c.update(controller=controller,fleet_size=20,av_share=.1,opt_in_share=.3,max_route_candidates=1)
    grid=tmp_path/'policies.json';grid.write_text(json.dumps([dict(name=f'threshold_{t}',eta_threshold_seconds=t,travel_time_factor=1.25,av_repositioning='off') for t in [0,240]]))
    cfg.write_text(json.dumps(c));legacy=tmp_path/'legacy';run_city(['build','--config',cfg,'--data-root',cfg.parent,'--output',legacy],tmp_path/'legacy-build.txt')
    run_city(['run','--bundles',legacy,'--policies',grid,'--seeds',3,'--output',tmp_path/'legacy-run'],tmp_path/'legacy-run.txt')
    studies=[];bundles=[];c['placement_av_share']=.2
    for share in [.05,.1,.2]:
        c['av_share']=share;config=cfg.parent/f's{share}.json';config.write_text(json.dumps(c));bundle=tmp_path/f'bundle{share}';study=tmp_path/f'study{share}'
        run_city(['build','--config',config,'--data-root',cfg.parent,'--output',bundle],tmp_path/f'build{share}.txt')
        run_city(['run','--bundles',bundle,'--policies',grid,'--seeds',3,'--output',study],tmp_path/f'run{share}.txt');studies.append(study);bundles.append(bundle)
    before={str(p):p.read_bytes() for s in studies for e in json.loads((s/'manifest.json').read_text())['runs'] for p in Path(e['output']).iterdir() if p.is_file()}
    result=analyze(studies,tmp_path/'analysis');assert result['unique_conditions']==result['physical_runs']==9 and result['matched_fleet_share_background_checks']==6
    assert len(result['all_human_partition_checks'])==2 and all(Path(p).read_bytes()==v for p,v in before.items())
    placement=[]
    for share,s in zip([.05,.1,.2],studies):
        m=json.loads((s/'manifest.json').read_text())
        for e in m['runs']:
            folder=Path(e['output']);placement.append((folder/'initial_placement.csv').read_bytes());roster=pd.read_csv(folder/'2_vehicle_types.csv')
            av=set(roster.loc[roster.vehicle_type.eq('av_vehtype'),'vehicle_id']);expected=set(range(20-round(20*share),20)) if e['arm']!='all_human' else set()
            assert av==expected
            anchor=json.loads((folder/'city_placement_anchor.json').read_text());assert anchor['anchor_slots']==list(range(16,20))
    assert len(set(placement))==1
    rows=pd.read_csv(tmp_path/'analysis/seed_results.csv');assert rows[rows.arm.eq('threshold_240')].av_completed.gt(0).all()
    assert rows.groupby('av_share').eligible_requests.nunique().eq(1).all() and rows.eligible_requests.nunique()==1
    with pytest.raises(ValueError,match='Incompatible city input assumptions'):summarize(studies,tmp_path/'unsafe_pool')
    replay=tmp_path/'replay';run_city(['run','--bundles',bundles[1],'--policies',grid,'--seeds',3,'--output',replay],tmp_path/'replay.txt')
    r=analyze([*studies,replay],tmp_path/'replayed');assert r['physical_runs']==12 and len(r['fresh_process_replays'])==3
    assert (tmp_path/'analysis/control_adjusted_share_effects.csv').is_file()
    with pytest.raises(ValueError,match='overwrite'):analyze(studies,tmp_path/'analysis')
    target=bundles[0]/'parameters.json';raw=target.read_bytes()
    try:
        target.write_bytes(raw+b'\n')
        with pytest.raises(ValueError,match='input snapshot changed'):analyze(studies,tmp_path/'tampered')
    finally:target.write_bytes(raw)
