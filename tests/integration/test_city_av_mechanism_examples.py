"""Complete matched runs on both controllers, C++ physics, replays and read-only audits."""
import json
from pathlib import Path

import pandas as pd
import pytest

from tests.integration.test_city_av_examples import city_fixture,run_city
from tools.city_av.mechanism import analyze


@pytest.mark.integration
@pytest.mark.parametrize('router,controller',[('NetworkBasicWithStore','PoolingIRSOnly'),
    ('NetworkBasicWithStoreCpp','PoolingIRSOnly'),('NetworkBasicWithStore','PoolingIRSAssignmentBatchOptimization')])
def test_threshold_mechanism_reconciles_full_physics_and_preserves_raw_replays(tmp_path,router,controller):
    if router.endswith('Cpp'):pytest.importorskip('src.routing.road.cpp_router.PyNetwork')
    cfg,c=city_fixture(tmp_path/'source',router);c['controller']=controller;c['max_route_candidates']=1
    cfg.write_text(json.dumps(c));bundle=tmp_path/'bundle'
    run_city(['build','--config',cfg,'--data-root',cfg.parent,'--output',bundle],tmp_path/'build.txt')
    policies=[dict(name='threshold_0',eta_threshold_seconds=0,travel_time_factor=1.25,av_repositioning='off'),
        dict(name='threshold_240',eta_threshold_seconds=240,travel_time_factor=1.25,av_repositioning='off'),
        dict(name='equal_speed_240',eta_threshold_seconds=240,travel_time_factor=1,av_repositioning='off')]
    grid=tmp_path/'policies.json';grid.write_text(json.dumps(policies));first=tmp_path/'first'
    run_city(['run','--bundles',bundle,'--policies',grid,'--seeds',3,'--workers',2,'--output',first],tmp_path/'first.txt')
    m=json.loads((first/'manifest.json').read_text());assert m['status']=='complete' and len(m['runs'])==4
    original={str(p):p.read_bytes() for e in m['runs'] for p in Path(e['output']).iterdir() if p.is_file()}
    result=analyze([first],tmp_path/'analysis')
    assert result['physical_runs']==4 and result['all_accounting_bridges_close'] and result['paired_contrasts']==2
    assert all(Path(p).read_bytes()==data for p,data in original.items())
    rows=pd.read_csv(tmp_path/'analysis/seed_accounting.csv');pairs=pd.read_csv(tmp_path/'analysis/paired_accounting.csv')
    assert rows.bridge_residual_s.abs().max()<1e-6 and pairs.residual_s.abs().max()<1e-6
    assert rows.alighting_dwell_passenger_s.gt(0).any()
    transitions=pd.read_csv(tmp_path/'analysis/product_transitions.csv')
    assert transitions.groupby(['candidate','control']).requests.sum().eq(48).all()
    assert (tmp_path/'analysis/occupied_time_components.png').exists()
    with pytest.raises(ValueError,match='overwrite'):analyze([first],tmp_path/'analysis')
    # Fresh processes are separate evidence, never extra independent conditions.
    grid2=tmp_path/'replay.json';grid2.write_text(json.dumps([policies[1]]));replay=tmp_path/'replay'
    run_city(['run','--bundles',bundle,'--policies',grid2,'--seeds',3,'--output',replay],tmp_path/'replay.txt')
    for arm in ['all_human','threshold_240']:
        for name in ['1_user-stats.csv','2-0_op-stats.csv','city_report.json','random_streams.json','av_product_op_0.json']:
            a=first/'runs/fixture_city/seed_3'/arm/name;b=replay/'runs/fixture_city/seed_3'/arm/name
            assert a.exists()==b.exists() and (not a.exists() or a.read_bytes()==b.read_bytes())
    with pytest.raises(ValueError,match='Duplicate mechanism condition'):
        analyze([first,replay],tmp_path/'duplicate')
    target=Path(m['runs'][1]['output'])/'2-0_op-stats.csv';raw=target.read_bytes()
    try:
        target.write_bytes(raw+b'\n')
        with pytest.raises(ValueError,match='Raw mechanism output changed'):
            analyze([first],tmp_path/'tampered')
    finally:target.write_bytes(raw)
