import json

import numpy as np
import pandas as pd
import pytest

from src.misc.seeding import file_digest
from tools.paired_eval.metrics import per_driver_metrics


@pytest.fixture
def inactive_output(tmp_path):
    costs=tmp_path/'vehicles';costs.mkdir();(costs/'test.csv').write_text('per_km_cost [cent],0\ndaily_fix_cost [cent],0\n')
    (tmp_path/'00_config.json').write_text(json.dumps(dict(scenario_parameters=dict(start_time=100,end_time=1000),directories={'vehicles':str(costs)})))
    pd.DataFrame(dict(operator_id=[0],vehicle_id=[0],vehicle_type=['test'])).to_csv(tmp_path/'2_vehicle_types.csv',index=False)
    pd.DataFrame(dict(request_id=[0],operator_id=[np.nan],vehicle_id=[np.nan],pickup_time=[np.nan],dropoff_time=[np.nan],fare=[np.nan])).to_csv(tmp_path/'1_user-stats.csv',index=False)
    pd.DataFrame(dict(vehicle_id=[0],status=['out_of_service'],start_time=[40],end_time=[400],
                      driven_distance=[0],occupancy=[0],toll=[0],start_pos=['1'],end_pos=['1'])).to_csv(tmp_path/'2-0_op-stats.csv',index=False)
    return tmp_path


def test_initial_inactivity_is_explicitly_bounded_without_changing_raw_records(inactive_output):
    path=inactive_output/'2-0_op-stats.csv';before=file_digest(path)
    with pytest.raises(ValueError):per_driver_metrics(inactive_output)
    row=per_driver_metrics(inactive_output,clip_initial_inactivity=True).iloc[0]
    assert row.online_time_s==600 and row.idle_time_s==600 and row.driving_time_s==0
    assert file_digest(path)==before


@pytest.mark.parametrize('field,value',[
    ('status','route'),('driven_distance',1),('occupancy',1),('toll',1),('end_pos',2),('end_time',90),
])
def test_boundary_option_does_not_hide_moving_loaded_or_invalid_records(inactive_output,field,value):
    path=inactive_output/'2-0_op-stats.csv';rows=pd.read_csv(path);rows.loc[0,field]=value;rows.to_csv(path,index=False)
    with pytest.raises(ValueError):per_driver_metrics(inactive_output,clip_initial_inactivity=True)


def test_actual_overlap_remains_an_error_with_boundary_option(inactive_output):
    path=inactive_output/'2-0_op-stats.csv';rows=pd.read_csv(path)
    second=rows.copy();second.loc[0,['start_time','end_time']]=[300,500]
    pd.concat([rows,second]).to_csv(path,index=False)
    with pytest.raises(ValueError,match='Overlapping'):per_driver_metrics(inactive_output,clip_initial_inactivity=True)
