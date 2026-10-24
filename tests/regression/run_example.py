"""Run one complete bundled example in a fresh process and isolated output folder.

The same runner is used for upstream reference capture and fork validation.
It changes only the output destination and progress display, not dispatch logic.
"""

import argparse
from pathlib import Path
import sys


EXAMPLES = {
    "insertion": ("constant_config_ir.csv", "example_ir_only.csv"),
    "immediate_batch": ("constant_config_ir.csv", "example_ir_batch.csv"),
    "batch": ("constant_config_pool.csv", "example_pool.csv"),
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("example", choices=EXAMPLES)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--network-tt-noise-sigma", type=float)
    parser.add_argument("--record-promised-times", action="store_true")
    parser.add_argument("--driver-acceptance-config", type=Path,
                        help="YAML mapping containing only op_driver_acceptance settings")
    args = parser.parse_args()
    root = args.source_root.resolve()
    output = args.output.resolve()
    # FleetPy empties an existing output folder; never pass it an existing path.
    if output.exists():
        parser.error(f"Output already exists: {output}")
    sys.path.insert(0, str(root))

    from src.FleetSimulationBase import FleetSimulationBase
    from src.misc.config import ConstantConfig, ScenarioConfig
    from src.misc.globals import G_DIR_OUTPUT
    from run_scenarios import run_single_simulation

    directory_dict = FleetSimulationBase.get_directory_dict

    def isolated_directories(parameters, operators):
        directories = directory_dict(parameters, operators)
        directories[G_DIR_OUTPUT] = str(output)
        return directories

    FleetSimulationBase.get_directory_dict = staticmethod(isolated_directories)
    constants, scenarios = EXAMPLES[args.example]
    scenario_dir = root / "studies/example_study/scenarios"
    parameters = ConstantConfig(str(scenario_dir / constants))
    scenario_parameters = ScenarioConfig(str(scenario_dir / scenarios))
    if len(scenario_parameters) != 1:
        raise ValueError("A reference example must contain exactly one scenario")
    parameters += scenario_parameters[0]
    parameters.update(study_name="example_study", n_cpu_per_sim=1, evaluate=1,
                      log_level="warning", keep_old=False, show_progress_bar=False)
    if args.network_tt_noise_sigma is not None:
        parameters["network_tt_noise_sigma"] = args.network_tt_noise_sigma
    if args.record_promised_times:
        parameters["record_promised_times"] = True
    if args.driver_acceptance_config is not None:
        settings = ConstantConfig(str(args.driver_acceptance_config))
        if any(not key.startswith("op_driver_acceptance") for key in settings):
            raise ValueError("Driver acceptance overrides may contain only op_driver_acceptance settings")
        parameters.update(settings)
    run_single_simulation(parameters)
    for filename in ("standard_eval.csv", "1_user-stats.csv", "final_state.csv"):
        if not (output / filename).is_file():
            raise RuntimeError(f"Simulation did not produce {filename}")


if __name__ == "__main__":
    main()
