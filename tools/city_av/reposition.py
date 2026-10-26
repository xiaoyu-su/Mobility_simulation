"""Separate-reference AV spatial weights and actual empty-movement inspection."""

import math
from pathlib import Path

import numpy as np
import pandas as pd

from src.fleetctrl.av_product import integer_targets
from src.misc.seeding import file_digest
from tools.synthetic_market.build import json_write


MODE = 'reference_od_stationary_v1'
FORECAST = 'city_av_reference.csv'


def reference_weights(reference, config, mapping, fence, parent=None):
    """Use only the declared pre-warmup or earlier-date reference, never target OD."""
    if config.get('av_repositioning_forecast') != MODE:
        raise ValueError('Unknown city AV repositioning reference method')
    zones = mapping.set_index('node_index').zone_id
    identity = 'trip_id' if parent else 'request_id'
    clock = 'request_s' if parent else 'rq_time'
    if reference.empty or reference[identity].duplicated().any():
        raise ValueError('Repositioning reference needs nonempty unique requests')
    if parent:
        dates = pd.to_datetime(reference.service_date)
        if not dates.lt(pd.Timestamp(parent['target_date'])).all() or not reference.service_date.isin(parent['training_dates']).all():
            raise ValueError('Repositioning reference includes an unapproved/future date')
    elif not reference[clock].ge(config['reference_start']).all() or not reference[clock].lt(config['reference_end']).all():
        raise ValueError('Repositioning reference crosses its pre-warmup cutoff')
    if not np.isfinite(reference[clock]).all():
        raise ValueError('Invalid reference clock')
    frame = pd.DataFrame(dict(reference_id=reference[identity].astype(str),
        reference_time=reference[clock], origin_zone=reference.start.map(zones), destination_zone=reference.end.map(zones)))
    if frame[['origin_zone', 'destination_zone']].isna().any().any():
        raise ValueError('Repositioning reference contains unmapped endpoints')
    if parent:
        frame['reference_date'] = reference.service_date
    frame['av_endpoint_eligible'] = frame.origin_zone.isin(fence) & frame.destination_zone.isin(fence)
    eligible = frame[frame.av_endpoint_eligible]
    if eligible.empty:
        raise ValueError('No independent AV-eligible OD reference; cannot invent a forecast')
    outgoing = eligible.origin_zone.value_counts().to_dict()
    incoming = eligible.destination_zone.value_counts().to_dict()
    metadata = dict(method=MODE, reference_rows=len(frame), eligible_reference_rows=len(eligible),
        positive_origin_zones=len(outgoing), resolution_seconds=900,
        endpoint_rule='Both reference endpoints lie inside the existing reference-selected AV fence',
        units='Relative reference OD counts repeated each interval; not calibrated future trip volumes',
        opt_in='Uniform per-request assumed opt-in changes mass, not these normalized spatial targets',
        temporal_scope='Stationary spatial weights; native reference precedes warmup, Manhattan dates precede target',
        uncertainty='Sparse native reference and temporal transfer remain benchmark assumptions')
    return frame.sort_values('reference_id').reset_index(drop=True), outgoing, incoming, metadata


def write_reference(output, prepared, fence, start, end, source_path):
    frame, outgoing, incoming, metadata = prepared
    rows = [dict(time=t, zone_id=int(z), **{'out aggregate_o_and_d':int(outgoing.get(z, 0)),
            'in aggregate_o_and_d':int(incoming.get(z, 0))})
            for t in range(start // 900 * 900, math.ceil(end / 900) * 900 + 900, 900) for z in sorted(fence)]
    frame.to_csv(output / 'repositioning_reference.csv', index=False)
    target = output / 'forecasts/900' / FORECAST
    pd.DataFrame(rows).to_csv(target, index=False)
    return dict(metadata, file='forecasts/900/' + FORECAST, file_sha256=file_digest(target),
                reference_file='repositioning_reference.csv', reference_file_sha256=file_digest(output / 'repositioning_reference.csv'),
                source_sha256=file_digest(source_path), source_path=str(source_path))


def inspect_repositioning(bundle, meta, config, product, legs, output, ids):
    """Trace physical repositioning legs to actual commands, including interruptions."""
    enabled = bool(config.get('op_av_repositioning', False))
    reference = meta['av_repositioning_reference']
    active = legs[legs.status.eq('reposition')]
    if active.vehicle_id.isin(ids).eq(False).any() or active.occupancy.ne(0).any():
        raise RuntimeError('City repositioning moved a human vehicle or carried passengers')
    if not enabled and len(active):
        raise RuntimeError('Disabled city repositioning executed movement')
    rounds = product.get('repositioning_rounds', []) if product else []
    if product and bool(product['repositioning']) != enabled:
        raise RuntimeError('Actual city AV repositioning mode differs from configuration')
    commands = []
    if enabled:
        if not config.get('op_av_service_priority') or not product or not product.get('service_priority'):
            raise RuntimeError('City AV repositioning requires passenger-service priority')
        if not product or product.get('retarget_repositioning') or product.get('joint_repositioning') or product.get('forecast_sigma', 0):
            raise RuntimeError('City repositioning comparison unexpectedly changes a follow-up lever')
        if product.get('forecast_sha256') != reference['file_sha256'] or config.get('op_forecast_f') != FORECAST:
            raise RuntimeError('City AV product did not consume the verified reference forecast')
        expected = [t for t in range(config['start_time'], config['end_time'], config['time_step'])
                    if t % config['op_av_repositioning_timestep'] == 0]
        if [r['time'] for r in rounds] != expected:
            raise RuntimeError('City AV repositioning callbacks are missing or off-grid')
        # A full interval contains the same strictly separate stationary counts.
        reference_frame = pd.read_csv(Path(bundle) / reference['reference_file'])
        mapping = pd.read_csv(Path(bundle) / 'zones/network/node_zone_info.csv')
        counts = reference_frame[reference_frame.av_endpoint_eligible].origin_zone.value_counts().to_dict()
        expected_weights = {int(z):float(counts.get(z, 0)) for z in meta['av_product']['fence_zones']}
        centroids = {int(z):int(g.loc[g.is_centroid.eq(1), 'node_index'].min())
                     for z, g in mapping.groupby('zone_id') if z in expected_weights}
        for record in rounds:
            weights = {int(k):v for k,v in record['forecast_demand'].items()}
            if set(weights) != set(expected_weights) or any(not np.isclose(weights[z], expected_weights[z], rtol=0, atol=1e-9) for z in weights):
                raise RuntimeError('City repositioning weights differ from separate-reference OD counts')
            if {int(k):v for k,v in record['fleet_targets'].items()} != integer_targets(expected_weights, len(ids)):
                raise RuntimeError('City repositioning fleet target apportionment changed')
            assigned = set()
            for command in record['assignments']:
                vid, zone, node = command['vehicle_id'], command['zone_id'], command['node_index']
                if vid not in ids or vid in assigned or zone not in centroids or node != centroids[zone]:
                    raise RuntimeError('City repositioning command violates AV roster/fence/centroid')
                if not math.isfinite(command['travel_time_s']) or command['travel_time_s'] < 0:
                    raise RuntimeError('Invalid city repositioning command travel time')
                assigned.add(vid)
                commands.append(dict(time=record['time'], **command))
    elif rounds:
        raise RuntimeError('Disabled city AV repositioning issued commands')
    physical = []
    for leg in active.itertuples():
        candidates = [c for c in commands if c['vehicle_id'] == leg.vehicle_id and c['time'] <= leg.start_time + 1e-7]
        if not candidates:
            raise RuntimeError('Physical city repositioning has no preceding AV command')
        command = max(candidates, key=lambda c:c['time'])
        position = str(leg.end_pos).split(';')
        arrived = int(position[0]) == command['node_index'] and position[1] == '-1'
        physical.append(dict(vehicle_id=int(leg.vehicle_id), start_time=leg.start_time, end_time=leg.end_time,
            command_time=command['time'], target_node=command['node_index'], target_zone=command['zone_id'],
            actual_end_position=leg.end_pos, arrived_at_target=arrived, distance_m=leg.driven_distance))
    contract = dict(enabled=enabled, forecast_sha256=reference['file_sha256'], rounds=len(rounds),
        commands=commands, physical_legs=physical, physical_movement_exercised=bool(active.driven_distance.gt(0).any()),
        no_human_repositioning=True, empty_repositioning_only=True,
        endpoint_interpretation='A leg ending before its assigned target is interrupted; no passenger-preemption cause is inferred')
    json_write(Path(output) / 'city_repositioning_contract.json', contract)
    return dict(av_repositioning_enabled=enabled, av_repositioning_rounds=len(rounds),
        av_repositioning_assignments=len(commands), av_repositioning_legs=len(active),
        av_repositioning_distance_km=float(active.driven_distance.sum()) / 1000,
        av_repositioning_time_s=float((active.end_time - active.start_time).sum()),
        av_repositioning_arrivals=sum(p['arrived_at_target'] for p in physical),
        av_repositioning_interrupted_legs=sum(not p['arrived_at_target'] for p in physical),
        av_repositioning_physically_exercised=contract['physical_movement_exercised'])
