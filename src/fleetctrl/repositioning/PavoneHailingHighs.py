"""Opt-in integer Pavone rebalancing with SciPy/HiGHS and isolated randomness."""

import json
import math
from pathlib import Path

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import lil_matrix

from src.fleetctrl.repositioning.PavoneHailingFC import PavoneHailingRepositioningFC
from src.fleetctrl.planning.VehiclePlan import RoutingTargetPlanStop
from src.misc.globals import G_PLANSTOP_STATES
from src.misc.seeding import derive_rng


INPUT_PARAMETERS_PavoneHailingHighs = {
    'doc': 'License-free Pavone rebalancing with integer-safe forecast excess.',
    'inherit': 'PavoneHailingRepositioningFC', 'input_parameters_mandatory': [],
    'input_parameters_optional': [], 'mandatory_modules': [], 'optional_modules': []}


def integer_rebalance(zones, excess, idle, eligible, costs):
    """Conserve vehicles; never promise fractional forecast excess as a whole car."""
    if len(set(zones)) != len(zones):
        raise ValueError('Rebalancing zones must be unique')
    for zone in zones:
        if not math.isfinite(excess[zone]) or not 0 <= excess[zone] <= idle[zone] or int(idle[zone]) != idle[zone]:
            raise ValueError('Excess must be finite and bounded by integer idle supply')
    available = {zone: int(math.floor(excess[zone])) for zone in zones}
    mean = sum(available.values()) // len(zones) if zones else 0
    targets = {zone: mean if zone in eligible else 0 for zone in zones}
    arcs = [(a,b) for a in zones for b in zones if a != b]
    if not arcs or all(available[z] >= targets[z] for z in zones):
        return [], dict(excess=available, targets=targets, objective=0.0, status=0)
    c = np.array([costs[a,b] for a,b in arcs],dtype=float)
    if not np.isfinite(c).all() or (c < 0).any():
        raise ValueError('Zone travel costs must be finite and nonnegative')
    matrix = lil_matrix((2*len(zones),len(arcs)),dtype=float)
    indices = {zone:i for i,zone in enumerate(zones)}
    for j,(a,b) in enumerate(arcs):
        matrix[indices[a],j] = -1
        matrix[indices[b],j] = 1
        matrix[len(zones)+indices[a],j] = 1
    lower = [targets[z]-available[z] for z in zones] + [-np.inf]*len(zones)
    upper = [np.inf]*len(zones) + [idle[z] for z in zones]
    result = milp(c,integrality=np.ones(len(arcs)),
                  bounds=Bounds(np.zeros(len(arcs)),[idle[a] for a,b in arcs]),
                  constraints=LinearConstraint(matrix.tocsr(),lower,upper),
                  options={'time_limit':30,'mip_rel_gap':0})
    if not result.success:
        raise RuntimeError(f'HiGHS repositioning failed: {result.message}')
    solution = np.rint(result.x).astype(int)
    if not np.allclose(solution,result.x,atol=1e-6,rtol=0):
        raise RuntimeError('HiGHS returned a fractional vehicle flow')
    flows = [(a,b) for (a,b),count in zip(arcs,solution) for _ in range(count)]
    for zone in zones:
        outgoing = sum(a == zone for a,b in flows); incoming = sum(b == zone for a,b in flows)
        if outgoing > idle[zone] or available[zone]+incoming-outgoing < targets[zone]:
            raise RuntimeError('Rebalancing solution violates vehicle conservation')
    return flows,dict(excess=available,targets=targets,objective=float(result.fun),status=int(result.status))


class PavoneHailingHighs(PavoneHailingRepositioningFC):
    def __init__(self,fleetctrl,operator_attributes,dir_names,solver='HiGHS'):
        super().__init__(fleetctrl,operator_attributes,dir_names,solver='HiGHS')
        self.rng = derive_rng(fleetctrl.scenario_parameters['random_seed'],f'repositioning/{fleetctrl.op_id}')
        self.audit = dict(strategy='PavoneFCHiGHS',solver='scipy.optimize.milp/HiGHS',
                          integer_rule='floor excess before computing uniform target',rounds=[])
        self.audit_path = None if fleetctrl.scenario_parameters.get('skip_file_writing',False) else Path(self.output_dir)/f'repositioning_op_{fleetctrl.op_id}.json'

    def _centroid(self,zone):
        nodes = (self.zone_system.zone_centroids or {}).get(zone,[])
        return min(nodes) if nodes else -1

    def determine_and_create_repositioning_plans(self,sim_time,lock=None):
        self.zone_system.time_trigger(sim_time);self.sim_time = sim_time
        if lock is None:lock = self.lock_repo_assignments
        t0,t1 = [sim_time+h for h in self.list_horizons]
        zones = sorted(z for z in self.zone_system.get_all_zones() if z >= 0)
        demand = self._get_demand_forecasts(t0,t1);supply = self._get_historic_arrival_forecasts(t0,t1)
        av_coverage={}
        product=getattr(self.fleetctrl,'av_product',None)
        if product is not None:
            demand,av_coverage=product.human_forecast(demand,t0,t1)
        weight = 1 if self._weight_on_forecast is None else self._weight_on_forecast
        if not math.isfinite(weight) or weight < 0:raise ValueError('Forecast weight must be nonnegative and finite')
        for values in [demand,supply]:
            if any(not math.isfinite(v) or v < 0 for v in values.values()):
                raise ValueError('Repositioning forecasts must be finite and nonnegative')
        state = self._get_current_veh_plan_arrivals_and_repo_idle_vehicles(t0,t1)
        for z in zones:
            self.record_df.loc[(sim_time,z,t0,t1),'tot_fc_supply']=weight*supply.get(z,0)
            self.record_df.loc[(sim_time,z,t0,t1),'tot_fc_demand']=weight*demand.get(z,0)
        idle = {z:len(state[z][2]) for z in zones}
        excess = {z:max(idle[z]+min(len(state[z][1])+weight*(supply.get(z,0)-demand.get(z,0)),0),0) for z in zones}
        eligible = {z for z in zones if self._centroid(z) >= 0}
        positions = {z:self.routing_engine.return_node_position(self._centroid(z)) for z in eligible}
        costs = {}
        for a in zones:
            for b in zones:
                if a != b:
                    costs[a,b] = (self.routing_engine.return_travel_costs_1to1(positions[a],positions[b])[1]
                                  if a in eligible and b in eligible else 1e8)
        flows,result = integer_rebalance(zones,excess,idle,eligible,costs)
        changed = []
        for a,b in flows:
            vehicles = state[a][2]
            vehicle = sorted(vehicles,key=lambda v:v.vid)[int(self.rng.integers(len(vehicles)))]
            plan = self.fleetctrl.veh_plans[vehicle.vid]
            if plan.list_plan_stops:raise RuntimeError('Repositioning attempted to replace an active tour')
            stop = RoutingTargetPlanStop(positions[b],locked=lock,planstop_state=G_PLANSTOP_STATES.REPO_TARGET)
            plan.add_plan_stop(stop,vehicle,sim_time,self.routing_engine)
            self.fleetctrl.assign_vehicle_plan(vehicle,plan,sim_time)
            if lock:self.fleetctrl.lock_current_vehicle_plan(vehicle.vid)
            vehicles.remove(vehicle);changed.append(vehicle.vid)
        self.audit['rounds'].append(dict(time=sim_time,idle=idle,forecast_weight=weight,forecast_demand=demand,forecast_arrivals=supply,
            **result,flows=[list(pair) for pair in flows],assigned_vehicles=changed))
        if av_coverage:self.audit['rounds'][-1]['av_coverage']=av_coverage
        if self.audit_path is not None:self.audit_path.write_text(json.dumps(self.audit,indent=2,allow_nan=False)+'\n')
        return changed
