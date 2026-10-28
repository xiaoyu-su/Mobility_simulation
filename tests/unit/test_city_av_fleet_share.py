"""Fleet composition isolation, fixed geometry and legacy-default contracts."""
from copy import deepcopy
import json
import pytest
from tests.integration.test_city_av_examples import city_fixture
from tools.city_av.build import build
from tools.city_av.fleet_share import static_basis
from tools.city_av.summary import bundle_contract


def meta(share):
    n=int(100*share)
    return dict(config=dict(av_share=share,opt_in_share=.3,placement_av_share=.2,max_wait_seconds=480),
        output_sha256={'parameters.json':str(share),'demand/requests.csv':'same'},
        av_product=dict(requested_share=share,av_count=n,human_count=100-n,opt_in_share=.3,fence_zones=[1]),
        fleet_size=100,placement_anchor_av_count=20,dependencies={})


def test_share_changes_only_composition_and_explicit_stratum():
    assert static_basis(meta(.05))==static_basis(meta(.1))==static_basis(meta(.2))
    assert bundle_contract(meta(.05))!=bundle_contract(meta(.1))


@pytest.mark.parametrize('change',['patience','fleet','anchor','demand'])
def test_share_comparisons_reject_other_input_changes(change):
    a=meta(.1);b=deepcopy(a)
    if change=='patience':b['config']['max_wait_seconds']=720
    elif change=='fleet':b['fleet_size']=200
    elif change=='anchor':b['placement_anchor_av_count']=30
    else:b['output_sha256']['demand/requests.csv']='other'
    assert static_basis(a)!=static_basis(b)


@pytest.mark.parametrize('anchor',[.04,0,1,float('nan')])
def test_builder_rejects_anchor_below_av_share_or_invalid_boundaries(tmp_path,anchor):
    cfg,c=city_fixture(tmp_path/'source');c.update(av_share=.1,placement_av_share=anchor);cfg.write_text(json.dumps(c))
    with pytest.raises(ValueError,match='Placement AV share'):build(cfg,cfg.parent,tmp_path/'bad')


def test_legacy_default_does_not_add_anchor_metadata(tmp_path):
    cfg,c=city_fixture(tmp_path/'source');c['av_share']=.1;cfg.write_text(json.dumps(c));m=build(cfg,cfg.parent,tmp_path/'legacy')
    assert m['status']=='complete' and 'placement_anchor_av_count' not in m
