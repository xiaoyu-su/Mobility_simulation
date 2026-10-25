from argparse import Namespace
import json

import pytest

from src.misc.seeding import file_digest
from tools.synthetic_market.build import build
from tools.synthetic_market.run import experiment
from tools.synthetic_market.worker import verify_bundle
from tools.synthetic_market import records


@pytest.mark.parametrize('damage',['source','dependencies','status','payload','path'])
def test_corrupt_or_incompatible_bundles_fail_before_simulation(tmp_path,monkeypatch,damage):
    monkeypatch.setattr('tools.synthetic_market.worker.source_record',lambda:{'code_digest':'current'})
    monkeypatch.setattr('tools.synthetic_market.worker.market_dependencies',lambda:{'pandas':'current'})
    payload=tmp_path/'parameters.json';payload.write_text('{}')
    metadata=dict(status='complete',source={'code_digest':'current'},dependencies={'pandas':'current'},
                  output_sha256={'parameters.json':file_digest(payload)})
    if damage=='source':metadata['source']['code_digest']='other'
    elif damage=='dependencies':metadata['dependencies']['pandas']='other'
    elif damage=='status':metadata['status']='failed'
    elif damage=='path':metadata['output_sha256']={'../outside':'unknown'}
    else:payload.write_text('{"changed":true}')
    (tmp_path/'manifest.json').write_text(json.dumps(metadata))
    with pytest.raises(ValueError):verify_bundle(tmp_path)


@pytest.mark.parametrize('action',[build,experiment])
def test_preexisting_outputs_are_preserved_before_any_input_read(tmp_path,action):
    marker=tmp_path/'keep.txt';marker.write_text('user work')
    with pytest.raises(ValueError,match='overwrite'):
        action(Namespace(output=tmp_path,bundle=tmp_path/'missing'))
    assert marker.read_text()=='user work'


def test_trip_source_changes_during_streaming_are_rejected(tmp_path,monkeypatch):
    path=tmp_path/'trips.csv'
    path.write_text('hvfhs_license_num,request_datetime,pickup_datetime,dropoff_datetime,PULocationID,DOLocationID\nHV0003,2019-11-05 07:00:00,2019-11-05 07:01:00,2019-11-05 07:02:00,1,2\n')
    original=records.chunks
    def changed(source,size):
        yield from original(source,size)
        path.write_text(path.read_text()+'\n')
    monkeypatch.setattr(records,'chunks',changed)
    with pytest.raises(ValueError,match='changed'):
        records.read_records([path],['2019-11-05'],{1,2},0,1)
