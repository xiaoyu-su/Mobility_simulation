"""Loaded opt-in boundaries, fixed request groups, controls and exact replay."""
import json
from pathlib import Path
import pandas as pd
import pytest
from tests.integration.test_city_av_examples import city_fixture, run_city
from tools.city_av.adoption import analyze, GROUPS
from tools.city_av.summary import summarize


@pytest.mark.integration
@pytest.mark.parametrize('router,controller',[('NetworkBasicWithStore','PoolingIRSOnly'),
    ('NetworkBasicWithStoreCpp','PoolingIRSOnly'),('NetworkBasicWithStore','PoolingIRSAssignmentBatchOptimization')])
def test_opt_in_full_runs_preserve_cohort_controls_and_show_nested_access(tmp_path,router,controller):
    if router.endswith('Cpp'):pytest.importorskip('src.routing.road.cpp_router.PyNetwork')
    cfg,c=city_fixture(tmp_path/'source',router);c.update(controller=controller,max_route_candidates=1)
    policies=[dict(name=f'threshold_{t}',eta_threshold_seconds=t,travel_time_factor=1.25,av_repositioning='off') for t in [0,240]]
    grid=tmp_path/'policies.json';grid.write_text(json.dumps(policies));studies=[];bundles=[]
    for share in [0,.3,1]:
        c['opt_in_share']=share;config=cfg.parent/f's{share}.json';config.write_text(json.dumps(c));bundle=tmp_path/f'bundle{share}';study=tmp_path/f'study{share}'
        run_city(['build','--config',config,'--data-root',cfg.parent,'--output',bundle],tmp_path/f'build{share}.txt')
        run_city(['run','--bundles',bundle,'--policies',grid,'--seeds',3,'--output',study],tmp_path/f'run{share}.txt');studies.append(study);bundles.append(bundle)
    for name in ['observed_cohort.csv','demand/requests.csv','initial_distribution.csv']:
        assert all((b/name).read_bytes()==(bundles[0]/name).read_bytes() for b in bundles)
    before={str(p):p.read_bytes() for s in studies for e in json.loads((s/'manifest.json').read_text())['runs'] for p in Path(e['output']).iterdir() if p.is_file()}
    result=analyze(studies,tmp_path/'analysis');assert result['unique_conditions']==result['physical_runs']==9
    assert result['matched_opt_in_background_checks']==6 and len(result['all_human_invariance_checks'])==2
    assert all(Path(p).read_bytes()==v for p,v in before.items())
    rows=pd.read_csv(tmp_path/'analysis/seed_results.csv');assert rows[rows.opt_in_share.eq(0)].av_completed.eq(0).all()
    assert rows[rows.opt_in_share.eq(1)&rows.arm.eq('threshold_240')].av_completed.gt(0).all()
    groups=pd.read_csv(tmp_path/'analysis/fixed_group_results.csv');assert set(groups.group)==set(GROUPS)
    assert groups.groupby(['opt_in_share','arm']).requests.sum().eq(48).all()
    for group in GROUPS:assert groups[groups.group.eq(group)].requests.nunique()==1
    assert groups[groups.opt_in_share.eq(1)&groups.group.eq('additional_opt_in')].av_completed.gt(0).any()
    assert groups[groups.group.eq('outside_fence')].av_completed.eq(0).all()
    with pytest.raises(ValueError,match='Incompatible city input assumptions'):summarize(studies,tmp_path/'unsafe_pool')
    replay=tmp_path/'replay';run_city(['run','--bundles',bundles[1],'--policies',grid,'--seeds',3,'--output',replay],tmp_path/'replay.txt')
    result=analyze([*studies,replay],tmp_path/'replayed');assert result['physical_runs']==12 and result['unique_conditions']==9 and len(result['fresh_process_replays'])==3
    with pytest.raises(ValueError,match='overwrite'):analyze(studies,tmp_path/'analysis')
    target=bundles[0]/'parameters.json';original=target.read_bytes()
    try:
        target.write_bytes(original+b'\n')
        with pytest.raises(ValueError,match='input snapshot changed'):analyze(studies,tmp_path/'tampered')
    finally:target.write_bytes(original)
