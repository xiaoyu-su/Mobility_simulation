"""Compare cached exact top-k with independent full scans on the example network.

This benchmarks deterministic score evaluations, not city-scale simulation.
Wall-time ratios are descriptive; exact results and query counts are checked.
"""

import argparse
import json
import math
from pathlib import Path
import platform
import time
from types import SimpleNamespace

import numpy as np
import pandas as pd

from src.fleetctrl.acceptance.driver_acceptance import DriverAcceptance
from src.fleetctrl.acceptance.future_value import ENABLED, TOP_K
from src.misc.globals import VRL_STATES
from src.misc.seeding import derive_rng, canonical_digest, file_digest
from src.routing.road.NetworkBasicWithStore import NetworkBasicWithStore
from tools.paired_eval.__main__ import source_record


ROOT = Path(__file__).resolve().parents[1]


class CountingNetwork:
    def __init__(self, directory):
        self.network = NetworkBasicWithStore(str(directory))
        self.queries = 0

    def return_travel_costs_1to1(self, origin, destination):
        self.queries += 1
        return self.network.return_travel_costs_1to1(origin, destination)


def make_request(rid, origin):
    return SimpleNamespace(get_rid_struct=lambda: rid, get_o_stop_info=lambda: (origin, 0, 1e9),
                           nr_pax=1, init_direct_td=1000 + rid * 100)


def full_scan(model, vehicles, network, request, chosen, top_k, current_probability):
    origin, earliest, latest = request.get_o_stop_info()
    candidates = []
    for vehicle in vehicles:
        if vehicle.vid == chosen:
            continue
        _, travel_time, _ = network.return_travel_costs_1to1(vehicle.pos, origin)
        if math.isfinite(travel_time) and 0 <= travel_time <= latest - 100:
            candidates.append((max(0, travel_time, earliest - 100), vehicle.vid))
    reject_all = 1.0
    for eta, vid in sorted(candidates)[:top_k]:
        reject_all *= 1 - model.probability_at_eta(vid, request, eta)
    return current_probability + (1 - current_probability) * (1 - reject_all)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--vehicles", type=int, default=32)
    parser.add_argument("--requests", type=int, default=12)
    parser.add_argument("--repetitions", type=int, default=5)
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()
    if min(args.vehicles, args.requests, args.repetitions) < 1 or args.top_k < 0:
        parser.error("Vehicle/request/repetition counts must be positive; top-k must be nonnegative")
    if args.output.exists():
        parser.error("Refusing to overwrite existing benchmark evidence")
    source = source_record()
    directory = ROOT / "data/networks/example_network"
    edges = pd.read_csv(directory / "base/edges.csv")
    rng = derive_rng(2026, "future_value_benchmark")
    positions = []
    for vid in range(args.vehicles):
        edge = edges.iloc[int(rng.integers(len(edges)))]
        position = ((int(edge.from_node), int(edge.to_node), .25) if vid % 2
                    else (int(edge.from_node), None, None))
        positions.append(positions[-1] if vid > 0 and vid % 8 == 0 else position)
    vehicles = [SimpleNamespace(vid=vid, pos=pos, max_pax=4, status=VRL_STATES.IDLE)
                for vid, pos in enumerate(positions)]
    origins = [(int(edges.iloc[int(rng.integers(len(edges)))].to_node), None, None)
               for _ in range(args.requests)]
    requests = [make_request(rid, origin) for rid, origin in enumerate(origins)]
    attributes = {"op_driver_acceptance_intercept": 0, "op_driver_acceptance_beta_eta": -.15,
                  "op_driver_acceptance_beta_value": .1, "op_driver_acceptance_weight_objective": True,
                  ENABLED: True, TOP_K: args.top_k}
    model = DriverAcceptance(attributes, {"random_seed": 2026, "skip_file_writing": 1}, 0, vehicles, None)
    # Separate fresh network caches: neither implementation receives a warmed
    # copy from the other. Network load time is excluded from both measurements.
    reference_network = CountingNetwork(directory)
    optimized_network = CountingNetwork(directory)
    workload = [(request, vehicle.vid) for _ in range(args.repetitions) for request in requests for vehicle in vehicles]
    started = time.perf_counter()
    reference = [full_scan(model, vehicles, reference_network, request, chosen, args.top_k, .4)
                 for request, chosen in workload]
    reference_time = time.perf_counter() - started
    model.begin_matching_round(100, optimized_network)
    started = time.perf_counter()
    optimized = [model.future_value.estimate(.4, chosen, request, 100, optimized_network).served_value
                 for request, chosen in workload]
    optimized_time = time.perf_counter() - started
    max_error = float(np.max(np.abs(np.asarray(reference) - np.asarray(optimized))))
    if max_error > 1e-12:
        raise RuntimeError(f"Cached scores differ from the independent reference: {max_error}")
    if source_record()["code_digest"] != source["code_digest"]:
        raise RuntimeError("Source changed during the benchmark")
    evidence = {"status": "complete", "kind": "repeated deterministic score evaluation on real example roads",
                "source": source, "python": platform.python_version(), "seed": 2026,
                "workload": {"vehicles": args.vehicles, "requests": args.requests,
                             "repetitions": args.repetitions, "top_k": args.top_k,
                             "score_evaluations": len(workload), "current_probability": .4,
                             "coefficient_status": "illustrative assumptions, not calibrated",
                             "corpus_sha256": canonical_digest({"positions": positions, "origins": origins})},
                "network_input_sha256": {name: file_digest(directory / "base" / name) for name in ("nodes.csv", "edges.csv")},
                "reference": {"wall_time_s": reference_time, "routing_queries": reference_network.queries},
                "optimized": {"wall_time_s": optimized_time, "routing_queries": optimized_network.queries,
                              "counters": model.future_value.counters},
                "max_absolute_score_error": max_error,
                "time_ratio_reference_over_optimized": reference_time / optimized_time,
                "note": "Microbenchmark only; timing is descriptive, not a city-scale or end-to-end runtime claim"}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(evidence, indent=2, allow_nan=False) + "\n")
    print(f"Scores agree within {max_error:.3g}; route queries {reference_network.queries} -> {optimized_network.queries}; "
          f"wall time {reference_time:.3f}s -> {optimized_time:.3f}s")


if __name__ == "__main__":
    main()
