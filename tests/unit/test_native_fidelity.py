import json

import pandas as pd
import pytest

from tools.native_fidelity import TABLES, compare_tables, profiles_from, source_file, verify_vehicle_inputs


@pytest.mark.parametrize('change', ['value', 'column', 'missing_row', 'duplicate_row', 'missing_value'])
def test_fidelity_comparison_never_blesses_changed_outputs(tmp_path, change):
    a, b = tmp_path / 'reference', tmp_path / 'candidate'
    a.mkdir()
    b.mkdir()
    for name in TABLES:
        frame = pd.DataFrame(dict(request_id=[1, 2], value=[3., 4.]))
        frame.to_csv(a / name, index=False)
        frame.to_csv(b / name, index=False)
    frame = pd.read_csv(b / TABLES[0])
    if change == 'value':
        frame.loc[1, 'value'] = 4.000000000001
    elif change == 'column':
        frame['unreviewed'] = 1
    elif change == 'missing_row':
        frame = frame.iloc[:1]
    elif change == 'duplicate_row':
        frame = pd.concat([frame, frame.iloc[:1]], ignore_index=True)
    else:
        frame.loc[1, 'value'] = float('nan')
    frame.to_csv(b / TABLES[0], index=False)
    with pytest.raises(AssertionError):
        compare_tables(a, b)
    assert pd.read_csv(a / TABLES[0]).value.tolist() == [3., 4.]


@pytest.mark.parametrize('problem', ['duplicate_name', 'unsafe_name', 'new_feature', 'unknown_field'])
def test_fidelity_rejects_ambiguous_or_feature_enabled_profiles(tmp_path, problem):
    p = dict(name='native', city='test', constants='a', scenarios='b', scenario='one', data_root='{repo}/data')
    profiles = [p]
    if problem == 'duplicate_name':
        profiles.append(dict(p))
    elif problem == 'unsafe_name':
        p['name'] = '../overwrite'
    elif problem == 'new_feature':
        p['overrides'] = dict(op_av_opt_in_share=1)
    else:
        p['ignore_errors'] = True
    path = tmp_path / 'profiles.json'
    path.write_text(json.dumps(profiles))
    with pytest.raises(ValueError):
        profiles_from(path)


def test_fidelity_source_paths_cannot_escape_selected_tree(tmp_path):
    source = tmp_path / 'source'
    source.mkdir()
    (tmp_path / 'foreign.py').write_text('')
    with pytest.raises(ValueError, match='escaping'):
        source_file(source, '../foreign.py')


def test_fidelity_rejects_changed_vehicle_inputs_before_simulating(tmp_path):
    a, b = tmp_path / 'a', tmp_path / 'b'
    for directory in [a, b]:
        (directory / 'data/vehicles').mkdir(parents=True)
        (directory / 'data/vehicles/car.csv').write_text('maximum_passengers,4\n')
    assert verify_vehicle_inputs(a, b)
    (b / 'data/vehicles/car.csv').write_text('maximum_passengers,5\n')
    with pytest.raises(ValueError, match='vehicle inputs differ'):
        verify_vehicle_inputs(a, b)
