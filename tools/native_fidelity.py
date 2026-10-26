"""Compare clean upstream and fork native scenarios without blessing new baselines."""

import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import tarfile
import time

import numpy as np
import pandas as pd

from tools.fidelity_worker import digest, write_json
from tools.paired_eval.__main__ import ROOT, source_record
from tools.city_av.report import capacity_audit
from tools.synthetic_market.report import request_ids


UPSTREAM = 'c813728b6d188df8dd7fd5d3d36dcb0a55c898a2'
TABLES = ['1_user-stats.csv', '2-0_op-stats.csv', 'standard_eval.csv', 'final_state.csv']


def compare_tables(reference, candidate):
    """Compare every cell and column, keeping original row order and missing values."""
    checks = []
    for name in TABLES:
        a, b = Path(reference) / name, Path(candidate) / name
        left, right = pd.read_csv(a, float_precision='round_trip'), pd.read_csv(b, float_precision='round_trip')
        pd.testing.assert_frame_equal(left, right, check_exact=True)
        checks.append(dict(file=name, rows=len(left), columns=len(left.columns),
                           exact_all_cells=True, byte_identical=a.read_bytes() == b.read_bytes(),
                           upstream_sha256=digest(a), fork_sha256=digest(b)))
    return checks


def audit_physical(folder, vehicle_directory):
    folder = Path(folder)
    contract = json.loads((folder / 'fidelity_contract.json').read_text())
    users = pd.read_csv(folder / '1_user-stats.csv').set_index('request_id')
    legs = pd.read_csv(folder / '2-0_op-stats.csv', low_memory=False)
    if not users.index.is_unique or len(users) != contract['requests']:
        raise RuntimeError('Invalid fidelity request accounting')
    if not np.isfinite(legs[['start_time', 'end_time', 'driven_distance', 'occupancy']].to_numpy(dtype=float)).all():
        raise RuntimeError('Nonfinite fidelity activity')
    if legs.end_time.lt(legs.start_time - 1e-7).any() or legs.driven_distance.lt(0).any():
        raise RuntimeError('Invalid fidelity activity chronology/distance')
    for _, group in legs.groupby(['operator_id', 'vehicle_id']):
        group = group.sort_values(['start_time', 'end_time'])
        if np.any(group.start_time.to_numpy()[1:] < group.end_time.to_numpy()[:-1] - 1e-7):
            raise RuntimeError('Overlapping fidelity vehicle activity')
    capacities = {}
    for row in legs[['vehicle_id', 'vehicle_type']].drop_duplicates().itertuples(index=False):
        path = Path(vehicle_directory) / f'{row.vehicle_type}.csv'
        capacities[row.vehicle_id] = float(pd.read_csv(path, header=None, index_col=0).iloc[:, 0]['maximum_passengers'])
    unions = capacity_audit(legs, users, capacities)
    boarded, alighted = set(), set()
    for leg in legs[legs.status.eq('boarding')].itertuples():
        boarded.update(request_ids(leg.rq_boarding))
        alighted.update(request_ids(leg.rq_alighting))
    served = set(users.index[users.dropoff_time.notna()])
    if boarded != served or alighted != served:
        raise RuntimeError('Fidelity completion lacks physical boarding/alighting')
    if not users.pickup_time.notna().equals(users.dropoff_time.notna()) or users.dropoff_time.lt(users.pickup_time).any():
        raise RuntimeError('Invalid fidelity pickup/dropoff completion')
    return dict(requests=len(users), completed=len(served), chronological_activity=True,
                capacity_valid=True, valid_stationary_union_rows=unions, physical_boarding_alighting_complete=True)


def source_file(root, name):
    path = (root / name).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise ValueError(f'Missing or escaping fidelity source input: {name}')
    return path


def profiles_from(path):
    profiles = json.loads(Path(path).read_text())
    if not isinstance(profiles, list) or not profiles:
        raise ValueError('Fidelity profiles must be a nonempty list')
    names = set()
    for profile in profiles:
        if set(profile) - {'name', 'city', 'constants', 'scenarios', 'scenario', 'data_root', 'overrides', 'description'}:
            raise ValueError('Unknown fidelity profile fields')
        name = profile.get('name', '')
        if not re.fullmatch(r'[a-z][a-z0-9_-]*', name) or name in names:
            raise ValueError('Fidelity profile names must be unique safe identifiers')
        names.add(name)
        for key in ['city', 'constants', 'scenarios', 'scenario', 'data_root']:
            if not isinstance(profile.get(key), str) or not profile[key]:
                raise ValueError(f'Missing fidelity profile {key}')
        # This is a parity gate, not a way to activate a fork feature in upstream.
        allowed = {'op_repo_method', 'network_type', 'op_treebuild_timeout_per_veh', 'op_optimisation_timeout'}
        if set(profile.get('overrides', {})) - allowed:
            raise ValueError('Only declared legacy compatibility adaptations are permitted')
        profile['data_root'] = str(Path(profile['data_root'].replace('{repo}', str(ROOT))).resolve())
    return profiles


def capture_upstream(output, revision):
    commit = subprocess.check_output(['git', 'rev-parse', '--verify', revision + '^{commit}'], cwd=ROOT, text=True).strip()
    archive = output / 'upstream-source.tar'
    subprocess.run(['git', 'archive', commit, '--output', str(archive)], cwd=ROOT, check=True)
    source = output / 'upstream-source'
    source.mkdir()
    with tarfile.open(archive) as contents:
        contents.extractall(source, filter='data')
    files = {str(p.relative_to(source)): digest(p) for p in source.rglob('*') if p.is_file()}
    return source, dict(commit=commit, archive_sha256=digest(archive), original_files_sha256=files)


def stage_runtime(reference):
    """Share only the native binary after verifying all its tracked source inputs."""
    directory = Path('src/routing/road/cpp_router')
    names = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', UPSTREAM, str(directory)], cwd=ROOT, text=True).splitlines()
    hashes = {}
    for name in names:
        if Path(name).suffix in ['.cpp', '.h', '.pyx', '.pxd', '.py']:
            if (ROOT / name).read_bytes() != (reference / name).read_bytes():
                raise ValueError('Installed native router sources differ from clean upstream')
            hashes[name] = digest(ROOT / name)
    binaries = list((ROOT / directory).glob('PyNetwork*.so')) + list((ROOT / directory).glob('PyNetwork*.pyd'))
    if len(binaries) != 1:
        raise ValueError('Exactly one installed native router extension is required')
    binary = binaries[0]
    shutil.copy2(binary, reference / directory / binary.name)
    return dict(source_sha256=hashes, binary=str(directory / binary.name), binary_sha256=digest(binary),
                method='Added identical compiled runtime only after all tracked C++/Cython/setup inputs match; no upstream tracked file changed')


def verify_vehicle_inputs(candidate, reference):
    """Vehicle CSVs belong to each source archive; prove they really are equal."""
    a, b = Path(candidate) / 'data/vehicles', Path(reference) / 'data/vehicles'
    left = {p.name: digest(p) for p in a.glob('*.csv')}
    right = {p.name: digest(p) for p in b.glob('*.csv')}
    if not left or left != right:
        raise ValueError('Native fidelity vehicle inputs differ between source trees')
    return left


def inventory(profile):
    from src.misc.config import ConstantConfig, ScenarioConfig
    p = ConstantConfig(str(source_file(ROOT, profile['constants'])))
    rows = [r for r in ScenarioConfig(str(source_file(ROOT, profile['scenarios']))) if r['scenario_name'] == profile['scenario']]
    if len(rows) != 1:
        raise ValueError('Fidelity scenario must select exactly one original row')
    p += rows[0]
    p.update(profile.get('overrides', {}))
    data = Path(profile['data_root'])
    inputs = [data / 'demand' / p['demand_name'] / 'matched' / p['network_name'] / p['rq_file']]
    inputs += sorted(x for x in (data / 'networks' / p['network_name']).rglob('*') if x.is_file())
    if p.get('op_zone_system'):
        inputs += sorted(x for x in (data / 'zones' / p['op_zone_system'] / p['network_name']).rglob('*') if x.is_file())
    inputs += sorted((ROOT / 'data/vehicles').glob('*.csv'))
    return {str(path): digest(path) for path in inputs}


def run(args):
    output = args.output.resolve()
    if output.exists() or output.is_relative_to(ROOT):
        raise ValueError('Fidelity destination must be a fresh directory outside the repository')
    if args.repeats not in [1, 2] or args.timeout <= 0:
        raise ValueError('Fidelity repeats must be1/2 and timeout positive')
    profiles = profiles_from(args.profiles)
    frozen = source_record()
    profile_hash = digest(args.profiles)
    output.mkdir(parents=True)
    record = dict(status='preparing', source=frozen, profiles_sha256=profile_hash,
                  repeats=args.repeats, runs=[], comparisons=[], replays=[],
                  python=platform.python_version(), dependencies={name: importlib.metadata.version(name)
                      for name in ['numpy', 'pandas', 'scipy', 'pyyaml', 'gurobipy']})
    save = lambda: write_json(output / 'manifest.json', record)
    save()
    try:
        reference, upstream = capture_upstream(output, args.revision)
        record['upstream'] = upstream
        record['native_runtime'] = stage_runtime(reference)
        record['shared_vehicle_inputs_sha256'] = verify_vehicle_inputs(ROOT, reference)
        environment = dict(os.environ, PYTHONHASHSEED='0', OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', MPLBACKEND='Agg', MPLCONFIGDIR=str(output / 'matplotlib'))
        environment.pop('PYTHONPATH', None)
        cpus = sorted(os.sched_getaffinity(0)) if hasattr(os, 'sched_getaffinity') and shutil.which('taskset') else []
        record['runtime'] = dict(cpu=cpus[0] if cpus else None, thread_caps=1, PYTHONHASHSEED='0', sequential_processes=True)
        worker = ROOT / 'tools/fidelity_worker.py'
        for profile in profiles:
            name = profile['name']
            for key in ['constants', 'scenarios']:
                if source_file(ROOT, profile[key]).read_bytes() != source_file(reference, profile[key]).read_bytes():
                    raise ValueError('Native case configuration differs from clean upstream')
            snapshot = output / f'{name}-profile.json'
            write_json(snapshot, profile)
            inputs = inventory(profile)
            write_json(output / f'{name}-inputs.json', inputs)
            for repeat in range(args.repeats):
                folders = {}
                for label, code in [('upstream', reference), ('fork', ROOT)]:
                    folder = output / 'runs' / name / f'repeat_{repeat}' / label
                    folder.parent.mkdir(parents=True, exist_ok=True)
                    command = [sys.executable, str(worker), '--source', str(code), '--profile', str(snapshot), '--output', str(folder)]
                    if cpus:
                        command = ['taskset', '-c', str(cpus[0]), *command]
                    entry = dict(profile=name, repeat=repeat, source=label, command=command, output=str(folder), status='running')
                    record['runs'].append(entry)
                    record['status'] = 'running'
                    save()
                    start = time.monotonic()
                    with folder.with_suffix('.txt').open('w') as log:
                        result = subprocess.run(command, cwd=code, env=environment, stdout=log, stderr=subprocess.STDOUT, timeout=args.timeout)
                    entry.update(returncode=result.returncode, wall_seconds=time.monotonic() - start)
                    if result.returncode:
                        entry['status'] = 'failed'
                        raise RuntimeError(f'Native fidelity worker failed: {folder.with_suffix(".txt")}')
                    entry['physical'] = audit_physical(folder, code / 'data/vehicles')
                    entry['output_sha256'] = {p.name: digest(p) for p in folder.iterdir() if p.is_file()}
                    entry['status'] = 'complete'
                    folders[label] = folder
                    save()
                a, b = [json.loads((folders[x] / 'fidelity_contract.json').read_text()) for x in ['upstream', 'fork']]
                for key in ['initial_request_ids', 'initial_vehicle_positions_soc_sha256', 'initial_vehicle_count', 'accepted', 'rejected']:
                    if a[key] != b[key]:
                        raise RuntimeError(f'Unmatched native fidelity {key}: {name}')
                tables = compare_tables(folders['upstream'], folders['fork'])
                record['comparisons'].append(dict(profile=name, repeat=repeat, tables=tables))
                if repeat:
                    for label, folder in folders.items():
                        previous = folder.parent.parent / 'repeat_0' / label
                        checks = compare_tables(previous, folder)
                        if not all(t['byte_identical'] for t in checks):
                            raise RuntimeError('Fresh-process native replay is not byte-identical')
                        record['replays'].append(dict(profile=name, source=label, tables=checks))
                if inventory(profile) != inputs:
                    raise RuntimeError('Native public inputs changed during validation')
                print(f'{name} repeat{repeat}: {a["completed"]}/{a["requests"]} completed; all four tables match', flush=True)
                save()
        for name, h in upstream['original_files_sha256'].items():
            if digest(reference / name) != h:
                raise RuntimeError('Upstream tracked source archive changed')
        if source_record()['code_digest'] != frozen['code_digest'] or digest(args.profiles) != profile_hash:
            raise RuntimeError('Fork source/profile changed during validation')
        record['status'] = 'complete'
        save()
        return record
    except BaseException as error:
        record.update(status='failed', error=f'{type(error).__name__}: {error}')
        for entry in record['runs']:
            if entry['status'] == 'running':
                entry['status'] = 'failed_or_uncollected'
        save()
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profiles', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--revision', default=UPSTREAM)
    parser.add_argument('--repeats', type=int, default=1)
    parser.add_argument('--timeout', type=int, default=7200)
    run(parser.parse_args())


if __name__ == '__main__':
    main()
