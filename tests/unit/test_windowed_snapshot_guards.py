import json
import sys

import pytest

from src.misc.seeding import file_digest
from tools.windowed_eval.runtime import restore


@pytest.mark.parametrize('damage',['python','source','dependencies','payload','prefix'])
def test_restore_rejects_mismatched_state_before_unpickling(tmp_path,monkeypatch,damage):
    monkeypatch.setattr('tools.windowed_eval.runtime.source_record',lambda:{'code_digest':'current'})
    monkeypatch.setattr('tools.windowed_eval.runtime.dependencies',lambda:{'numpy':'current'})
    payload=tmp_path/'state.pickle.gz';payload.write_bytes(b'not a pickle: must never be loaded')
    prefix=tmp_path/'prefix';prefix.mkdir();(prefix/'users.csv').write_text('original')
    metadata=dict(format=1,python=list(sys.version_info[:3]),source={'code_digest':'current'},
                  dependencies={'numpy':'current'},snapshot_sha256=file_digest(payload),
                  prefix_sha256={'users.csv':file_digest(prefix/'users.csv')})
    if damage=='python':metadata['python']=[0,0,0]
    elif damage=='source':metadata['source']['code_digest']='other'
    elif damage=='dependencies':metadata['dependencies']['numpy']='other'
    elif damage=='payload':payload.write_bytes(b'changed')
    else:(prefix/'users.csv').write_text('changed')
    (tmp_path/'metadata.json').write_text(json.dumps(metadata))
    with pytest.raises(ValueError,match='match'):
        restore(tmp_path)
