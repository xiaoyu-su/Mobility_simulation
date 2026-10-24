"""One simulation per fresh process; output redirection does not change policy."""

import argparse
import json
from pathlib import Path

import pandas as pd

from src.FleetSimulationBase import FleetSimulationBase
from src.misc.config import ConstantConfig, ScenarioConfig
from src.misc.globals import G_DIR_OUTPUT
from run_scenarios import run_single_simulation


def load_parameters(constants, scenarios):
    parameters = ConstantConfig(str(constants))
    scenarios = ScenarioConfig(str(scenarios))
    if len(scenarios) != 1:
        raise ValueError("Each policy file must contain exactly one scenario")
    return parameters + scenarios[0]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--constant-config", type=Path, required=True)
    parser.add_argument("--scenarios", type=Path, required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--study-name", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--network-tt-noise-sigma", type=float)
    parser.add_argument("--record-promised-times", action="store_true")
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists():
        parser.error(f"Refusing to empty existing simulation output: {output}")
    parameters = load_parameters(args.constant_config, args.scenarios)
    parameters.update(random_seed=args.seed, random_stream_mode="independent",
                      study_name=args.study_name, n_cpu_per_sim=1, evaluate=1,
                      log_level="warning", show_progress_bar=False, keep_old=False, bugfix=False)
    if args.network_tt_noise_sigma is not None:
        parameters["network_tt_noise_sigma"] = args.network_tt_noise_sigma
    if args.record_promised_times:
        parameters["record_promised_times"] = True
    original = FleetSimulationBase.get_directory_dict

    def directories(parameters, operators):
        result = original(parameters, operators)
        result[G_DIR_OUTPUT] = str(output)
        return result

    FleetSimulationBase.get_directory_dict = staticmethod(directories)
    run_single_simulation(parameters)
    for filename in ("final_state.csv", "1_user-stats.csv", "standard_eval.csv", "random_streams.json"):
        if not (output / filename).is_file():
            raise RuntimeError(f"Simulation failed to produce {filename}")
    audit = json.loads((output / "random_streams.json").read_text())
    expected = sum(inputs["count"] for inputs in audit["demand"].values())
    users = pd.read_csv(output / "1_user-stats.csv")
    if len(users) != expected or users.request_id.duplicated().any():
        raise RuntimeError("Simulation output does not account for every loaded request exactly once")


if __name__ == "__main__":
    main()
