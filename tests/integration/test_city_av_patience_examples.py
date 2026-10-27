"""Loaded patience intervention, physical completion, replay and separation guards."""
import json
from pathlib import Path
import pandas as pd
import pytest
from tests.integration.test_city_av_examples import city_fixture,run_city
from tools.city_av.patience import analyze
from tools.city_av.summary import summarize


@pytest.mark.integration
@pytest.mark.parametrize('router,controller',[('NetworkBasicWithStore','PoolingIRSOnly'),
    ('NetworkBasicWithStoreCpp','PoolingIRSOnly'),('NetworkBasicWithStore','PoolingIRSAssignmentBatchOptimization')])
def test_patience_full_runs_change_feasibility_preserve_cohort_and_replay(tmp_path,router,controller):
    if router.endswith('Cpp'):pytest.importorskip('src.routing.road.cpp_router.PyNetwork')
    cfg,c=city_fixture(tmp_path/'source',router);c.update(controller=controller,fleet_size=2,fence_share=1,max_route_candidates=2)
    source=pd.read_csv(cfg.parent/'requests.csv');reference=source[source.rq_time.lt(900)].copy();reference['start']=0;reference['end']=1
    pd.concat([reference,pd.DataFrame([dict(request_id=0,rq_time=1801,start=1,end=2),dict(request_id=1,rq_time=4201,start=0,end=1)])]).to_csv(cfg.parent/'requests.csv',index=False)
    edges=cfg.parent/'network/base/edges.csv';frame=pd.read_csv(edges);frame['travel_time']=300;frame.to_csv(edges,index=False)
    policies=[dict(name=f'threshold_{t}',eta_threshold_seconds=t,travel_time_factor=1.25,av_repositioning='off') for t in [0,240]]
    grid=tmp_path/'policies.json';grid.write_text(json.dumps(policies));studies=[];bundles=[]
    for patience in [240,480,720]:
        c['max_wait_seconds']=patience;config=cfg.parent/f'p{patience}.json';config.write_text(json.dumps(c));bundle=tmp_path/f'bundle{patience}';study=tmp_path/f'study{patience}'
        run_city(['build','--config',config,'--data-root',cfg.parent,'--output',bundle],tmp_path/f'build{patience}.txt')
        run_city(['run','--bundles',bundle,'--policies',grid,'--seeds',3,'--output',study],tmp_path/f'run{patience}.txt');studies.append(study);bundles.append(bundle)
    assert all((b/'observed_cohort.csv').read_bytes()==(bundles[0]/'observed_cohort.csv').read_bytes() for b in bundles)
    before={str(p):p.read_bytes() for s in studies for e in json.loads((s/'manifest.json').read_text())['runs'] for p in Path(e['output']).iterdir() if p.is_file()}
    result=analyze(studies,tmp_path/'analysis');assert result['unique_conditions']==result['physical_runs']==9 and result['matched_patience_background_checks']==6
    assert result['all_booking_deadline_promises_valid'] and all(Path(p).read_bytes()==v for p,v in before.items())
    rows=pd.read_csv(tmp_path/'analysis/seed_results.csv');assert rows[rows.patience_s.eq(240)].completed.eq(1).all() and rows[rows.patience_s.eq(480)].completed.eq(2).all()
    with pytest.raises(ValueError,match='Incompatible city input assumptions'):summarize(studies,tmp_path/'unsafe_pool')
    replay=tmp_path/'replay';run_city(['run','--bundles',bundles[1],'--policies',grid,'--seeds',3,'--output',replay],tmp_path/'replay.txt')
    result=analyze([*studies,replay],tmp_path/'replayed');assert result['physical_runs']==12 and result['unique_conditions']==9 and len(result['fresh_process_replays'])==3
    with pytest.raises(ValueError,match='overwrite'):analyze(studies,tmp_path/'analysis')
    # Input mutation is rejected even if completed raw outputs were untouched.
    target=bundles[0]/'demand/requests.csv';raw=target.read_bytes()
    try:
        target.write_bytes(raw+b'\n')
        with pytest.raises(ValueError,match='input snapshot changed'):analyze(studies,tmp_path/'tampered')
    finally:target.write_bytes(raw)
