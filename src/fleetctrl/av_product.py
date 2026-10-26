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
from src.misc.seeding import file_digest,derive_rng
from src.misc.vehicle_timing import planned_time


PARAMETERS = ['op_av_vehicle_types', 'op_av_zones', 'op_av_opt_in_share',
              'op_av_preference_s', 'op_av_repositioning', 'op_av_repositioning_timestep',
              'op_av_eta_threshold_s','op_av_retarget','op_av_forecast_sigma',
              'op_av_joint_repositioning','op_av_eligible_forecast_f','op_av_separate_search']


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
        if attributes.get('op_driver_choice_model') not in (None,False,'off','singleton'):
            raise ValueError('Mixed AV acceptance currently supports off/singleton, not human multi-item menus')
        self.threshold=attributes.get('op_av_eta_threshold_s')
        self.separate_search=attributes.get('op_av_separate_search',False)
        if self.separate_search not in (True,False,0,1):raise ValueError('AV separate-search flag must be boolean')
        if self.separate_search and attributes.get('op_module') not in {'PoolingIRSOnly','PoolingIRSAssignmentBatchOptimization'}:
            raise ValueError('Separate AV search currently supports the two immediate insertion controllers')
        if self.threshold is not None:
            if isinstance(self.threshold,bool) or not math.isfinite(float(self.threshold)) or not 0<=float(self.threshold)<=3600:
                raise ValueError('AV ETA threshold must be finite within [0,3600] seconds')
            self.threshold=float(self.threshold)
            if self.preference!=0:raise ValueError('AV ETA threshold and preference bonus are alternative policies')
            if attributes.get('op_module') not in {'PoolingIRSOnly','PoolingIRSAssignmentBatchOptimization'}:
                raise ValueError('AV ETA threshold currently supports the two immediate insertion controllers')
        self.retarget=attributes.get('op_av_retarget',False)
        self.joint=attributes.get('op_av_joint_repositioning',False)
        if any(v not in (True,False,0,1) for v in [self.retarget,self.joint]):raise ValueError('AV retarget/joint flags must be boolean')
        self.forecast_sigma=float(attributes.get('op_av_forecast_sigma',0))
        if not math.isfinite(self.forecast_sigma) or not 0<=self.forecast_sigma<=2:raise ValueError('AV forecast sigma must be in [0,2]')
        self.seed=scenario['random_seed']
        self.repositioning = attributes.get('op_av_repositioning', False)
        if self.repositioning not in (True, False, 0, 1):
            raise ValueError('op_av_repositioning must be boolean')
        if not self.repositioning and (self.retarget or self.joint or self.forecast_sigma):
            raise ValueError('AV repositioning follow-ups require AV repositioning enabled')
        self.timestep = attributes.get('op_av_repositioning_timestep', attributes.get('op_temporal_resolution', 900))
        self.forecast_resolution=attributes.get('op_temporal_resolution',900)
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
        self.av_vehicles=tuple(v for v in fleetctrl.sim_vehicles if v.vid in self.av_ids)
        for v in fleetctrl.sim_vehicles:
            v.is_av = v.vid in self.av_ids
            v.av_product = self
        self.forecasts = None
        self.eligible_forecasts=None
        provenance = dict(zone_map_sha256=file_digest(mapping_path))
        if self.repositioning:
            forecast_path = Path(directories[G_DIR_FC]) / attributes['op_forecast_f']
            self.forecasts = pd.read_csv(forecast_path)
            values = self.forecasts['out aggregate_o_and_d']
            if not np.isfinite(values).all() or values.lt(0).any():
                raise ValueError('AV forecasts must be finite and nonnegative')
            provenance['forecast_sha256'] = file_digest(forecast_path)
            if self.joint:
                eligible_path=Path(directories[G_DIR_FC])/attributes['op_av_eligible_forecast_f']
                self.eligible_forecasts=pd.read_csv(eligible_path)
                values=self.eligible_forecasts['out aggregate_o_and_d']
                if not np.isfinite(values).all() or values.lt(0).any():raise ValueError('Invalid AV-eligible forecast')
                provenance['av_eligible_forecast_sha256']=file_digest(eligible_path)
        self.diagnosed = set()
        self.rounds = []
        self.initial_nodes = {}
        self.threshold_decisions=[]
        self.threshold_products={}
        self.coverage_rounds=[]
        self.output = None if scenario.get('skip_file_writing', False) else Path(directories[G_DIR_OUTPUT])
        self.audit = dict(enabled=True,vehicle_types=types,av_ids=sorted(self.av_ids),zones=sorted(self.zones),
                          opt_in_share=self.share,opt_in_scheme='crc32 av-opt-in-v1/operator/request; fixed across simulation seeds',
                          preference_seconds=self.preference,preference_units='rider seconds multiplied by objective vot, subtracted per AV passenger',
                          repositioning=bool(self.repositioning),repositioning_timestep=self.timestep,
                          geofence='both trip endpoints; routes may cross other zones',assumption_status='scenario assumptions, not observed AV adoption',**provenance)
        if self.threshold is not None:self.audit['eta_threshold_seconds']=self.threshold
        if self.separate_search:self.audit['candidate_search_scope']='Separate human/AV nearest-position budgets; identical across policy-grid arms'
        if self.retarget or self.joint or self.forecast_sigma:
            self.audit.update(retarget_repositioning=bool(self.retarget),joint_repositioning=bool(self.joint),forecast_sigma=self.forecast_sigma,
                              forecast_error_scheme='mean-one lognormal; independent av_forecast/operator/time/zone streams')
        self.columns = ['simulation_time','request_id','vehicle_id','is_av','av_eligible','idle_av_count',
                        'nearest_idle_av_eta_s','winning_pickup_eta_s','idle_av_minus_winner_eta_s']
        if self.output is not None:
            self.output.mkdir(parents=True, exist_ok=True)
            with (self.output/f'av_dispatch_op_{self.operator_id}.csv').open('w', newline='') as f:
                csv.DictWriter(f, fieldnames=self.columns).writeheader()
            self.write_audit()

    def threshold_candidates(self,candidates,request,time):
        if self.threshold is None:return candidates
        rid=request.get_rid_struct()
        if getattr(request,'status',0)>=G_PRQS_ACC_OFFER and rid in self.threshold_products:
            return [c for c in candidates if (c[0] in self.av_ids)==self.threshold_products[rid]]
        av=[c for c in candidates if c[0] in self.av_ids]
        humans=[c for c in candidates if c[0] not in self.av_ids]
        eta=lambda c:max(0,c[1].pax_info[rid][0]-time)
        best_av=min(av,key=lambda c:(eta(c),c[2],c[0])) if av else None
        best_human=min((eta(c) for c in humans),default=None)
        choose_av=best_av is not None and (best_human is None or eta(best_av)<=best_human+self.threshold+1e-9)
        if choose_av or humans:self.threshold_products[rid]=choose_av
        self.threshold_decisions.append(dict(time=time,request_id=rid,threshold_s=self.threshold,
            av_candidates=len(av),human_candidates=len(humans),best_av_eta_s=None if best_av is None else eta(best_av),
            best_human_eta_s=best_human,selected_pool='av' if choose_av else 'human' if humans else 'none',
            selected_av_id=best_av[0] if choose_av else None))
        return [best_av] if choose_av else humans

    def forecast_weights(self,time,eligible=False):
        source=self.eligible_forecasts if eligible else self.forecasts
        resolution=self.forecast_resolution
        rows=source[source.time.lt(time+resolution)&(source.time+resolution).gt(time)].copy()
        overlap=(np.minimum(rows.time+resolution,time+resolution)-np.maximum(rows.time,time))/resolution
        rows['weight']=rows['out aggregate_o_and_d']*overlap
        weights=rows.groupby('zone_id').weight.sum().to_dict()
        factors={z:float(derive_rng(self.seed,f'av_forecast/{self.operator_id}/{time}/{z}').lognormal(-self.forecast_sigma**2/2,self.forecast_sigma))
                 if self.forecast_sigma else 1.0 for z in sorted(self.zones)}
        result={z:float(weights.get(z,0))*(self.share if eligible else 1)*factors[z] for z in sorted(self.zones)}
        if any(not math.isfinite(v) for v in result.values()):raise ValueError('Unrepresentable AV forecast noise')
        return result,factors

    def human_forecast(self,demand,t0,t1):
        if not self.joint:return demand,{}
        eligible,_=self.forecast_weights(t0,eligible=True)
        available={z:0 for z in self.zones}
        for v in self.fleetctrl.sim_vehicles:
            if not v.is_av:continue
            plan=self.fleetctrl.veh_plans[v.vid]
            if not plan.list_plan_stops:
                node=v.pos[0];ready=t0
            else:
                last=plan.list_plan_stops[-1];node=last.get_pos()[0]
                arrival,departure=last.get_planned_arrival_and_departure_time();ready=departure if departure is not None else arrival
            zone=self.node_zones.get(node)
            if zone in available and ready is not None and ready<t1:available[zone]+=1
        coverage={z:min(float(demand.get(z,0)),eligible.get(z,0),available.get(z,0)) for z in self.zones}
        adjusted={z:max(0,v-coverage.get(z,0)) for z,v in demand.items()}
        details=dict(original_demand=dict(demand),expected_av_eligible=eligible,available_av=available,expected_av_coverage=coverage,
                     adjusted_human_demand=adjusted,scope='At most one booking per available/projected AV in the horizon')
        self.coverage_rounds.append(dict(time=t0,**details))
        return adjusted,details

    def eligible(self, request):
        return (self.node_zones.get(request.get_o_stop_info()[0][0]) in self.zones
                and self.node_zones.get(request.get_d_stop_info()[0][0]) in self.zones
                and opt_in(request.get_rid(), self.operator_id, self.share))

    def allows_plan(self, vehicle, plan):
        if self.threshold is not None:
            for stop in plan.list_plan_stops:
                for rid in stop.get_list_boarding_rids():
                    if rid in self.threshold_products and self.requests[rid].status>=G_PRQS_ACC_OFFER:
                        if vehicle.is_av!=self.threshold_products[rid]:return False
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
            raise RuntimeError('Assignment violates the AV product dispatch, opt-in or endpoint contract')
        for rid, times in plan.pax_info.items():
            request = self.requests[rid]
            if rid in self.diagnosed or request.status < G_PRQS_ACC_OFFER:
                continue
            self.diagnosed.add(rid)
            eligible = self.eligible(request)
            idle = [v for v in self.av_vehicles if not self.fleetctrl.veh_plans[v.vid].list_plan_stops and not v.pax]
            eta = min((planned_time(v,self.fleetctrl.routing_engine.return_travel_costs_1to1(v.pos, request.get_o_stop_info()[0])[1]) for v in idle),default=None) if eligible else None
            winner = max(0, times[0]-time)
            values = [time,rid,vehicle.vid,vehicle.is_av,eligible,len(idle),eta,winner,None if eta is None else eta-winner]
            if self.output is not None:
                with (self.output/f'av_dispatch_op_{self.operator_id}.csv').open('a', newline='') as f:
                    csv.DictWriter(f,fieldnames=self.columns).writerow(dict(zip(self.columns,values)))

    def reposition(self, time):
        if not self.repositioning or time % self.timestep:
            return
        from src.fleetctrl.planning.VehiclePlan import RoutingTargetPlanStop,VehiclePlan
        fleet = self.fleetctrl
        def movable(v):
            stops=fleet.veh_plans[v.vid].list_plan_stops
            return v.is_av and not v.pax and (not stops or self.retarget and len(stops)==1 and stops[0].get_state()==G_PLANSTOP_STATES.REPO_TARGET and not stops[0].is_locked())
        idle = [v for v in self.av_vehicles if movable(v)]
        moving_ids={v.vid for v in idle if fleet.veh_plans[v.vid].list_plan_stops}
        weights,factors=self.forecast_weights(time,eligible=self.joint)
        targets = integer_targets(weights,len(self.av_ids))
        busy = {z:0 for z in self.zones}
        for v in fleet.sim_vehicles:
            if v.is_av and v.vid not in moving_ids and fleet.veh_plans[v.vid].list_plan_stops:
                z = self.node_zones.get(fleet.veh_plans[v.vid].list_plan_stops[-1].get_pos()[0])
                if z in busy:busy[z] += 1
        slots_by_zone = integer_targets({z:max(targets.get(z,0)-busy[z],0) for z in sorted(self.zones)},len(idle)) if targets else {}
        slots = [z for z in sorted(slots_by_zone) for _ in range(slots_by_zone[z])]
        assignments = []
        if slots and idle:
            positions = {z:fleet.routing_engine.return_node_position(n) for z,n in self.centroids.items()}
            costs = np.array([[planned_time(v,fleet.routing_engine.return_travel_costs_1to1(v.pos,positions[z])[1]) for z in slots] for v in idle])
            if not np.isfinite(costs).all():raise RuntimeError('AV repositioning found unreachable targets')
            a,b = linear_sum_assignment(costs)
            for i,j in zip(a,b):
                v=idle[i];z=slots[j]
                if v.pos==positions[z]:continue
                plan=fleet.veh_plans[v.vid]
                retargeted=v.vid in moving_ids
                if retargeted and plan.list_plan_stops[-1].get_pos()==positions[z]:continue
                if retargeted:plan=VehiclePlan(v,time,fleet.routing_engine,[])
                stop=RoutingTargetPlanStop(positions[z],locked=False,planstop_state=G_PLANSTOP_STATES.REPO_TARGET)
                plan.add_plan_stop(stop,v,time,fleet.routing_engine)
                fleet.assign_vehicle_plan(v,plan,time)
                assignment=dict(vehicle_id=v.vid,zone_id=z,node_index=self.centroids[z],travel_time_s=float(costs[i,j]))
                if self.retarget:assignment['retargeted']=retargeted
                assignments.append(assignment)
        record=dict(time=time,forecast_demand=weights,fleet_targets=targets,busy_projected=busy,
                    idle_count=len(idle),idle_targets=slots_by_zone,assignments=assignments)
        if self.forecast_sigma:record['forecast_error_factors']=factors
        if self.retarget:record['moving_reposition_candidates']=len(moving_ids)
        self.rounds.append(record)
        self.write_audit()

    def write_audit(self):
        if self.output is not None:
            data={**self.audit,'initial_nodes':self.initial_nodes,'dispatch_records':len(self.diagnosed),'repositioning_rounds':self.rounds}
            if self.threshold is not None:data['threshold_decisions']=self.threshold_decisions
            if self.joint:data['human_coverage_rounds']=self.coverage_rounds
            (self.output/f'av_product_op_{self.operator_id}.json').write_text(json.dumps(data,indent=2,allow_nan=False)+'\n')


def create_av_product(fleetctrl, attributes, scenario, directories):
    if attributes.get('op_av_vehicle_types') is None:
        if any(attributes.get(p) is not None for p in PARAMETERS[1:]):
            raise ValueError('AV settings require op_av_vehicle_types')
        return None
    return AVProduct(fleetctrl,attributes,scenario,directories)
