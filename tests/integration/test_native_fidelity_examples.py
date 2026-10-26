"""Fresh, clean-upstream physical parity; references never use fork simulator code."""

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from tools.native_fidelity import UPSTREAM
from tools.paired_eval.__main__ import ROOT


@pytest.mark.integration
@pytest.mark.parametrize('scenario', ['example_ir_only.csv', 'example_ir_batch.csv', 'example_pool.csv'])
def test_clean_archive_and_fork_complete_all_three_native_controllers(tmp_path, scenario):
    from src.misc.config import ScenarioConfig
    row = ScenarioConfig(str(ROOT / 'studies/example_study/scenarios' / scenario))[0]
    constants = 'constant_config_pool.csv' if scenario == 'example_pool.csv' else 'constant_config_ir.csv'
    profile = dict(name='bundled', city='bundled_example', constants='studies/example_study/scenarios/' + constants,
                   scenarios='studies/example_study/scenarios/' + scenario, scenario=row['scenario_name'], data_root='{repo}/data')
    path = tmp_path / 'profiles.json'
    path.write_text(json.dumps([profile]))
    output = tmp_path / 'check'
    command = [sys.executable, '-m', 'tools.native_fidelity', '--profiles', str(path), '--output', str(output), '--repeats', '2']
    with (tmp_path / 'run.txt').open('w') as log:
        result = subprocess.run(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, timeout=300,
                                env=dict(os.environ, OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1'))
    assert result.returncode == 0, (tmp_path / 'run.txt').read_text()
    m = json.loads((output / 'manifest.json').read_text())
    assert m['status'] == 'complete' and m['upstream']['commit'] == UPSTREAM
    assert len(m['runs']) == 4 and len(m['comparisons']) == 2 and len(m['replays']) == 2
    for entry in m['runs']:
        assert entry['physical']['requests'] == 100 and entry['physical']['completed'] == 93
        folder = Path(entry['output'])
        c = json.loads((folder / 'fidelity_contract.json').read_text())
        assert c['all_accepted_complete'] and c['remaining_tasks'] == c['onboard_passengers'] == 0
        expected = output / 'upstream-source' if entry['source'] == 'upstream' else ROOT
        assert all(Path(p).is_relative_to(expected) for p in c['imported_simulator_files'].values())
        assert not (folder / 'av_product_op_0.json').exists()
        assert not (folder / 'driver_acceptance_op_0.csv').exists()
    assert all(t['exact_all_cells'] for pair in m['comparisons'] for t in pair['tables'])
    assert all(t['byte_identical'] for pair in m['replays'] for t in pair['tables'])
