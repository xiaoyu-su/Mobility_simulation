"""Run matching policies on matched seeds and retain complete experiment records."""

import argparse
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys

import pandas as pd

from src.misc.seeding import canonical_digest, file_digest, STREAM_SCHEME
from src.misc.execution import validate_execution_settings
from tools.paired_eval.metrics import per_driver_metrics, distribution_metrics, seed_summary
from tools.paired_eval.statistics import paired_statistics
from tools.paired_eval.worker import load_parameters


ROOT = Path(__file__).resolve().parents[2]
SUPPORTED = {"PoolingIRSOnly", "PoolingIRSAssignmentBatchOptimization", "RidePoolingBatchAssignmentFleetcontrol"}


def check_policy_pair(baseline, candidate):
    for parameters in (baseline, candidate):
        if parameters.get("op_module") not in SUPPORTED or parameters.get("nr_mod_operators") != 1:
            raise ValueError("Phase 1 paired runs support the three single-operator baseline matching controllers")
        if parameters.get("op_repo_method") is not None:
            raise ValueError("Stochastic repositioning needs its own stream audit before paired evaluation")
        if parameters.get("op_rp_batch_optimizer") not in (None, "AlonsoMora"):
            raise ValueError("The paired optimizer audit currently covers AlonsoMora")
        if parameters.get("initial_state_scenario") is not None:
            raise ValueError("Paired runs currently require freshly initialized fleets")
    mutable = {"scenario_name", "random_seed", "random_stream_mode"}
    def background(parameters):
        return {key: value for key, value in parameters.items()
                if not key.startswith("op_") and key not in mutable}
    if background(baseline) != background(candidate):
        raise ValueError("Policy files differ in exogenous simulation/demand settings")


def validate_pair(baseline_audit, candidate_audit):
    required = ("scheme", "mode", "master_seed", "demand", "network_input_sha256",
                "initial_vehicle_count", "initial_vehicle_state_sha256")
    for key in required:
        if key not in baseline_audit or key not in candidate_audit:
            raise ValueError(f"Missing paired input audit field: {key}")
        if baseline_audit[key] != candidate_audit[key]:
            raise ValueError(f"Policy pair has different {key}; refusing paired inference")
    if baseline_audit["mode"] != "independent" or baseline_audit["scheme"] != STREAM_SCHEME:
        raise ValueError("Pair does not use the reviewed independent-stream scheme")
    if baseline_audit["demand"].get("demand", {}).get("count", 0) <= 0:
        raise ValueError("Paired simulation did not load any passenger demand")


def source_record():
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    files = subprocess.check_output(["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"], cwd=ROOT).decode().split("\0")
    hashes = {name: file_digest(ROOT / name) for name in sorted(set(files))
              if name and (name.endswith(".py") or name in ("environment.yml", "requirements-dev.txt"))}
    return {"git_head": head, "code_files_sha256": hashes,
            "code_digest": canonical_digest(hashes)}


def run_experiment(args):
    seeds = args.seeds
    if not seeds or len(set(seeds)) != len(seeds) or any(seed < 0 or seed >= 2**32 for seed in seeds):
        raise ValueError("Seeds must be unique integers in FleetPy's supported range 0..2**32-1")
    output = args.output.resolve()
    if output.exists():
        raise ValueError(f"Refusing to overwrite existing experiment: {output}")
    constants = args.constant_config.resolve()
    originals = {"baseline": args.baseline_scenarios.resolve(), "candidate": args.candidate_scenarios.resolve()}
    parameters = {arm: load_parameters(constants, path) for arm, path in originals.items()}
    execution_overrides = {}
    if args.network_tt_noise_sigma is not None:
        execution_overrides["network_tt_noise_sigma"] = args.network_tt_noise_sigma
    if args.record_promised_times:
        execution_overrides["record_promised_times"] = True
    for values in parameters.values():
        values.update(execution_overrides)
        validate_execution_settings(values)
    check_policy_pair(parameters["baseline"], parameters["candidate"])
    output.mkdir(parents=True)
    configs = output / "configs"
    configs.mkdir()
    snapshots = {"constants": configs / ("constants" + constants.suffix)}
    shutil.copyfile(constants, snapshots["constants"])
    for arm, path in originals.items():
        snapshots[arm] = configs / (arm + path.suffix)
        shutil.copyfile(path, snapshots[arm])
    dependencies = {}
    for name in ("numpy", "pandas", "scipy", "pyyaml", "gurobipy"):
        try:
            dependencies[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            dependencies[name] = None
    manifest = {"status": "running", "scheme": STREAM_SCHEME, "seeds": seeds,
                "difference_direction": "candidate minus baseline", "python": platform.python_version(),
                "dependencies": dependencies, "source": source_record(),
                "config_sha256": {path.name: file_digest(path) for path in configs.iterdir()},
                "runtime": {"n_cpu_per_sim": 1, "random_stream_mode": "independent",
                            "execution_overrides": execution_overrides,
                            "PYTHONHASHSEED": "0", "OMP_NUM_THREADS": "1",
                            "OPENBLAS_NUM_THREADS": "1", "MKL_NUM_THREADS": "1"},
                "runs": [], "validated_pairs": []}
    manifest_path = output / "manifest.json"
    def save_manifest():
        manifest_path.write_text(json.dumps(manifest, indent=2, allow_nan=False) + "\n")
    save_manifest()
    drivers_all, distribution_all, summaries = [], [], {}
    try:
        for seed in seeds:
            audits = {}
            for arm in ("baseline", "candidate"):
                folder = output / "runs" / f"seed_{seed}"
                folder.mkdir(parents=True, exist_ok=True)
                result_directory = folder / arm
                command = [sys.executable, "-m", "tools.paired_eval.worker",
                           "--constant-config", str(snapshots["constants"]),
                           "--scenarios", str(snapshots[arm]), "--seed", str(seed),
                           "--study-name", constants.parent.parent.name, "--output", str(result_directory)]
                if args.network_tt_noise_sigma is not None:
                    command.extend(["--network-tt-noise-sigma", str(args.network_tt_noise_sigma)])
                if args.record_promised_times:
                    command.append("--record-promised-times")
                log = folder / f"{arm}.log"
                environment = dict(os.environ, PYTHONHASHSEED="0", MPLBACKEND="Agg",
                                   MPLCONFIGDIR=str(output / "matplotlib"),
                                   OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")
                with log.open("w") as stream:
                    result = subprocess.run(command, cwd=ROOT, env=environment,
                                            stdout=stream, stderr=subprocess.STDOUT, timeout=args.timeout)
                manifest["runs"].append({"seed": seed, "arm": arm, "returncode": result.returncode,
                                         "directory": str(result_directory.relative_to(output)),
                                         "command": command, "log": str(log.relative_to(output))})
                save_manifest()
                if result.returncode:
                    raise RuntimeError(f"Simulation failed; see {log}")
                audits[arm] = json.loads((result_directory / "random_streams.json").read_text())
                drivers = per_driver_metrics(result_directory)
                distribution = distribution_metrics(drivers)
                summaries[(seed, arm)] = seed_summary(result_directory, drivers, distribution)
                drivers_all.append(drivers.assign(seed=seed, arm=arm))
                distribution_all.append(distribution.assign(seed=seed, arm=arm))
            validate_pair(audits["baseline"], audits["candidate"])
            manifest["validated_pairs"].append({"seed": seed, "audit": audits["baseline"]})
            save_manifest()
            print(f"seed {seed}: both simulations complete; demand, network, and initial state match", flush=True)

        comparisons = []
        for metric in sorted(summaries[(seeds[0], "baseline")]):
            baseline = [summaries[(seed, "baseline")][metric] for seed in seeds]
            candidate = [summaries[(seed, "candidate")][metric] for seed in seeds]
            comparisons.append({"metric": metric, **paired_statistics(baseline, candidate)})
        pd.concat(drivers_all, ignore_index=True).to_csv(output / "per_driver.csv", index=False)
        pd.concat(distribution_all, ignore_index=True).to_csv(output / "driver_distribution.csv", index=False)
        rows = [{"seed": seed, "arm": arm, "metric": metric, "value": value}
                for (seed, arm), values in summaries.items() for metric, value in values.items()]
        pd.DataFrame(rows).to_csv(output / "seed_summary.csv", index=False)
        pd.DataFrame(comparisons).to_csv(output / "paired_comparison.csv", index=False)
        manifest["report_sha256"] = {name: file_digest(output / name) for name in
                                     ("per_driver.csv", "driver_distribution.csv", "seed_summary.csv", "paired_comparison.csv")}
        if source_record()["code_digest"] != manifest["source"]["code_digest"]:
            raise RuntimeError("Source code changed during the experiment; rerun from a stable revision")
        manifest["status"] = "complete"
        save_manifest()
    except Exception as error:
        manifest.update(status="failed", error=f"{type(error).__name__}: {error}")
        save_manifest()
        raise
    print(f"Reports and full run records: {output}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--constant-config", type=Path, required=True)
    parser.add_argument("--baseline-scenarios", type=Path, required=True)
    parser.add_argument("--candidate-scenarios", type=Path, required=True)
    parser.add_argument("--seeds", type=int, nargs="+", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--network-tt-noise-sigma", type=float,
                        help="Common execution-noise sigma for both policies (default: use config)")
    parser.add_argument("--record-promised-times", action="store_true",
                        help="Record accepted promises and timing errors in both policies, even at sigma=0")
    parser.add_argument("--timeout", type=int, default=180, help="Timeout in seconds per simulation")
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error("Timeout must be positive")
    run_experiment(args)


if __name__ == "__main__":
    main()
