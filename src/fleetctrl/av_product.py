"""Opt-in mixed-fleet product rules, independent of the matching algorithm."""

import csv
import json
import math
from pathlib import Path
import zlib

import numpy as np
import pandas as pd
from scipy.optimize import linear_sum_assignment

from src.misc.globals import G_DIR_FC, G_DIR_OUTPUT, G_DIR_ZONES, G_PRQS_ACC_OFFER, G_PLANSTOP_STATES
from src.misc.seeding import file_digest


PARAMETERS = ['op_av_vehicle_types', 'op_av_zones', 'op_av_opt_in_share',
              'op_av_preference_s', 'op_av_repositioning', 'op_av_repositioning_timestep']


def opt_in(request_id, operator_id, share):
    """A fixed request draw: increasing share creates a nested eligible set."""
    draw = zlib.crc32(f'av-opt-in-v1/{operator_id}/{request_id}'.encode()) / 2**32
    return draw < share


def integer_targets(weights, total):
    """Largest-remainder apportionment with stable zone-ID tie breaks."""
    zones = sorted(weights)
    if total < 0 or any(not math.isfinite(weights[z]) or weights[z] < 0 for z in zones):
        raise ValueError('AV demand weights and fleet size must be nonnegative and finite')
    mass = sum(weights.values())
    if not zones or mass <= 0:
        return {}
    raw = {z: total * weights[z] / mass for z in zones}
    result = {z: math.floor(raw[z]) for z in zones}
    for z in sorted(zones, key=lambda z: (-(raw[z] - result[z]), z))[:total-sum(result.values())]:
        result[z] += 1
    return result


class AVProduct:
    def __init__(self, fleetctrl, attributes, scenario, directories):
        self.fleetctrl = fleetctrl
        self.operator_id = fleetctrl.op_id
        self.requests = None  # the controller's live PlanRequest map, attached after construction
        if scenario.get('random_stream_mode', 'legacy') != 'independent' or scenario.get('n_cpu_per_sim', 1) != 1:
            raise ValueError('AV product requires independent random streams and one optimizer worker')
        if attributes.get('op_module') not in {'PoolingIRSOnly', 'PoolingIRSAssignmentBatchOptimization', 'RidePoolingBatchAssignmentFleetcontrol'}:
            raise ValueError('AV product supports the three baseline pooling controllers')
        if scenario.get('sim_env') not in {'ImmediateDecisionsSimulation', 'BatchOfferSimulation'} or scenario.get('rq_type') != 'BasicRequest':
            raise ValueError('AV product requires baseline immediate BasicRequest road-trip simulation')
        if attributes.get('op_dyn_fs_method') not in (None, 'TimeBasedFS'):
            raise ValueError('Mixed AV shifts currently support TimeBasedFS only')
        if attributes.get('op_repo_method') not in (None, 'PavoneFCHiGHS'):
            raise ValueError('Mixed AV human repositioning currently supports PavoneFCHiGHS only')
        objective = attributes.get('op_vr_control_func_dict', {})
        if objective.get('func_key') != 'distance_and_user_times_with_walk' or not math.isfinite(float(objective.get('vot', 0))) or objective.get('vot', 0) <= 0:
            raise ValueError('AV preference requires distance_and_user_times_with_walk with positive finite vot')
        types = attributes['op_av_vehicle_types']
        zones = attributes.get('op_av_zones')
        if not isinstance(types, list) or not types or any(not isinstance(t, str) or not t for t in types) or len(set(types)) != len(types):
            raise ValueError('op_av_vehicle_types must be a nonempty unique list')
        if not isinstance(zones, list) or not zones or any(isinstance(z, bool) or not isinstance(z, int) or z < 0 for z in zones) or len(set(zones)) != len(zones):
            raise ValueError('op_av_zones must be a nonempty unique list of nonnegative zone IDs')
        self.zones = set(zones)
        self.share = float(attributes.get('op_av_opt_in_share', .5))
        self.preference = float(attributes.get('op_av_preference_s', 0))
        if not math.isfinite(self.share) or not 0 <= self.share <= 1 or not math.isfinite(self.preference) or abs(self.preference) > 3600:
            raise ValueError('AV opt-in must be in [0,1] and preference finite within +/-3600 seconds')
        self.repositioning = attributes.get('op_av_repositioning', False)
        if self.repositioning not in (True, False, 0, 1):
            raise ValueError('op_av_repositioning must be boolean')
        self.timestep = attributes.get('op_av_repositioning_timestep', attributes.get('op_temporal_resolution', 900))
        if isinstance(self.timestep, bool) or not isinstance(self.timestep, int) or self.timestep <= 0 or self.timestep % scenario['time_step']:
            raise ValueError('AV repositioning timestep must align with the driving grid')
        mapping_path = Path(directories[G_DIR_ZONES]) / 'node_zone_info.csv'
        mapping = pd.read_csv(mapping_path)
        if mapping.node_index.duplicated().any() or not self.zones <= set(mapping.zone_id):
            raise ValueError('AV fence needs unique mapped nodes and all declared zones')
        self.node_zones = dict(zip(mapping.node_index.astype(int), mapping.zone_id.astype(int)))
        self.nodes = {n for n, z in self.node_zones.items() if z in self.zones}
        if not self.nodes:
            raise ValueError('AV fence contains no network nodes')
        self.centroids = {}
        for z in sorted(self.zones):
            candidates = mapping[mapping.zone_id.eq(z)]
            centers = candidates[candidates.is_centroid.eq(1)]
            self.centroids[z] = int((centers if len(centers) else candidates).node_index.min())
        actual_types = {v.veh_type for v in fleetctrl.sim_vehicles}
        if not set(types) <= actual_types:
            raise ValueError('AV vehicle types are absent from the loaded vehicle roster')
        self.av_ids = {v.vid for v in fleetctrl.sim_vehicles if v.veh_type in types}
        for v in fleetctrl.sim_vehicles:
            v.is_av = v.vid in self.av_ids
            v.av_product = self
        self.forecasts = None
        provenance = dict(zone_map_sha256=file_digest(mapping_path))
        if self.repositioning:
            forecast_path = Path(directories[G_DIR_FC]) / attributes['op_forecast_f']
            self.forecasts = pd.read_csv(forecast_path)
            values = self.forecasts['out aggregate_o_and_d']
            if not np.isfinite(values).all() or values.lt(0).any():
                raise ValueError('AV forecasts must be finite and nonnegative')
            provenance['forecast_sha256'] = file_digest(forecast_path)
        self.diagnosed = set()
        self.rounds = []
        self.initial_nodes = {}
        self.output = None if scenario.get('skip_file_writing', False) else Path(directories[G_DIR_OUTPUT])
        self.audit = dict(enabled=True,vehicle_types=types,av_ids=sorted(self.av_ids),zones=sorted(self.zones),
                          opt_in_share=self.share,opt_in_scheme='crc32 av-opt-in-v1/operator/request; fixed across simulation seeds',
                          preference_seconds=self.preference,preference_units='rider seconds multiplied by objective vot, subtracted per AV passenger',
                          repositioning=bool(self.repositioning),repositioning_timestep=self.timestep,
                          geofence='both trip endpoints; routes may cross other zones',assumption_status='scenario assumptions, not observed AV adoption',**provenance)
        self.columns = ['simulation_time','request_id','vehicle_id','is_av','av_eligible','idle_av_count',
                        'nearest_idle_av_eta_s','winning_pickup_eta_s','idle_av_minus_winner_eta_s']
        if self.output is not None:
            self.output.mkdir(parents=True, exist_ok=True)
            with (self.output/f'av_dispatch_op_{self.operator_id}.csv').open('w', newline='') as f:
                csv.DictWriter(f, fieldnames=self.columns).writeheader()
            self.write_audit()

    def eligible(self, request):
        return (self.node_zones.get(request.get_o_stop_info()[0][0]) in self.zones
                and self.node_zones.get(request.get_d_stop_info()[0][0]) in self.zones
                and opt_in(request.get_rid(), self.operator_id, self.share))

    def allows_plan(self, vehicle, plan):
        if not vehicle.is_av:
            return True
        return all(self.eligible(self.requests[rid]) for stop in plan.list_plan_stops for rid in stop.get_list_boarding_rids())

    def initial_distribution(self, distribution):
        filtered = {n: p for n, p in distribution.items() if n in self.nodes and p > 0}
        mass = sum(filtered.values())
        return {n:p/mass for n,p in filtered.items()} if mass > 0 else {n:1/len(self.nodes) for n in sorted(self.nodes)}

    def check_initial_state(self):
        for v in self.fleetctrl.sim_vehicles:
            if v.is_av:
                if v.pos[0] not in self.nodes or v.assigned_route:
                    raise ValueError('AV initial state must be idle inside the declared fence')
                self.initial_nodes[v.vid] = int(v.pos[0])
        self.write_audit()

    def record_assignment(self, vehicle, plan, time):
        if not self.allows_plan(vehicle, plan):
            raise RuntimeError('AV assignment violates rider opt-in or trip endpoint fence')
        for rid, times in plan.pax_info.items():
            request = self.requests[rid]
            if rid in self.diagnosed or request.status < G_PRQS_ACC_OFFER:
                continue
            self.diagnosed.add(rid)
            eligible = self.eligible(request)
            idle = [v for v in self.fleetctrl.sim_vehicles if v.is_av and not self.fleetctrl.veh_plans[v.vid].list_plan_stops and not v.pax]
            eta = min((self.fleetctrl.routing_engine.return_travel_costs_1to1(v.pos, request.get_o_stop_info()[0])[1] for v in idle),default=None) if eligible else None
            winner = max(0, times[0]-time)
            values = [time,rid,vehicle.vid,vehicle.is_av,eligible,len(idle),eta,winner,None if eta is None else eta-winner]
            if self.output is not None:
                with (self.output/f'av_dispatch_op_{self.operator_id}.csv').open('a', newline='') as f:
                    csv.DictWriter(f,fieldnames=self.columns).writerow(dict(zip(self.columns,values)))

    def reposition(self, time):
        if not self.repositioning or time % self.timestep:
            return
        from src.fleetctrl.planning.VehiclePlan import RoutingTargetPlanStop
        fleet = self.fleetctrl
        idle = [v for v in fleet.sim_vehicles if v.is_av and not fleet.veh_plans[v.vid].list_plan_stops and not v.pax]
        forecasts = self.forecasts[self.forecasts.time.ge(time)&self.forecasts.time.lt(time+self.timestep)]
        weights = forecasts.groupby('zone_id')['out aggregate_o_and_d'].sum().to_dict()
        weights = {z:float(weights.get(z,0)) for z in sorted(self.zones)}
        targets = integer_targets(weights,len(self.av_ids))
        busy = {z:0 for z in self.zones}
        for v in fleet.sim_vehicles:
            if v.is_av and fleet.veh_plans[v.vid].list_plan_stops:
                z = self.node_zones.get(fleet.veh_plans[v.vid].list_plan_stops[-1].get_pos()[0])
                if z in busy:busy[z] += 1
        slots_by_zone = integer_targets({z:max(targets.get(z,0)-busy[z],0) for z in sorted(self.zones)},len(idle)) if targets else {}
        slots = [z for z in sorted(slots_by_zone) for _ in range(slots_by_zone[z])]
        assignments = []
        if slots and idle:
            positions = {z:fleet.routing_engine.return_node_position(n) for z,n in self.centroids.items()}
            costs = np.array([[fleet.routing_engine.return_travel_costs_1to1(v.pos,positions[z])[1] for z in slots] for v in idle])
            if not np.isfinite(costs).all():raise RuntimeError('AV repositioning found unreachable targets')
            a,b = linear_sum_assignment(costs)
            for i,j in zip(a,b):
                v=idle[i];z=slots[j]
                if v.pos==positions[z]:continue
                plan=fleet.veh_plans[v.vid]
                stop=RoutingTargetPlanStop(positions[z],locked=False,planstop_state=G_PLANSTOP_STATES.REPO_TARGET)
                plan.add_plan_stop(stop,v,time,fleet.routing_engine)
                fleet.assign_vehicle_plan(v,plan,time)
                assignments.append(dict(vehicle_id=v.vid,zone_id=z,node_index=self.centroids[z],travel_time_s=float(costs[i,j])))
        self.rounds.append(dict(time=time,forecast_demand=weights,fleet_targets=targets,busy_projected=busy,
                                idle_count=len(idle),idle_targets=slots_by_zone,assignments=assignments))
        self.write_audit()

    def write_audit(self):
        if self.output is not None:
            data={**self.audit,'initial_nodes':self.initial_nodes,'dispatch_records':len(self.diagnosed),'repositioning_rounds':self.rounds}
            (self.output/f'av_product_op_{self.operator_id}.json').write_text(json.dumps(data,indent=2,allow_nan=False)+'\n')


def create_av_product(fleetctrl, attributes, scenario, directories):
    if attributes.get('op_av_vehicle_types') is None:
        if any(attributes.get(p) is not None for p in PARAMETERS[1:]):
            raise ValueError('AV settings require op_av_vehicle_types')
        return None
    return AVProduct(fleetctrl,attributes,scenario,directories)
