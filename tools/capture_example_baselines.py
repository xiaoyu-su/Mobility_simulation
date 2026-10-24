"""Capture references from a Git source archive, never from working-tree code.

Write to a NEW directory, review the results, and only then replace approved
fixtures. This tool never updates tests/regression/baselines automatically.
"""

import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import runpy
import shutil
import subprocess
import sys
import tarfile
import tempfile


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "tests/regression/run_example.py"
UPSTREAM_COMMIT = "c813728b6d188df8dd7fd5d3d36dcb0a55c898a2"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--revision", default=UPSTREAM_COMMIT)
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists():
        parser.error(f"Refusing to overwrite existing references: {output}")
    commit = subprocess.check_output(
        ["git", "rev-parse", "--verify", args.revision + "^{commit}"],
        cwd=ROOT, text=True,
    ).strip()
    examples = runpy.run_path(str(RUNNER))["EXAMPLES"]
    with tempfile.TemporaryDirectory(prefix="fleetpy-upstream-reference-") as temporary:
        temporary = Path(temporary)
        archive = temporary / "source.tar"
        source = temporary / "source"
        source.mkdir()
        subprocess.run(["git", "archive", commit, "--output", str(archive)], cwd=ROOT, check=True)
        with tarfile.open(archive) as contents:
            contents.extractall(source, filter="data")

        staged = temporary / "references"
        staged.mkdir()
        for example in examples:
            results = temporary / "results" / example
            environment = dict(os.environ, PYTHONHASHSEED="0", MPLBACKEND="Agg",
                               MPLCONFIGDIR=str(temporary / "matplotlib"),
                               OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1",
                               MKL_NUM_THREADS="1")
            result = subprocess.run(
                [sys.executable, str(RUNNER), example, "--source-root", str(source),
                 "--output", str(results)],
                cwd=source, env=environment, capture_output=True, text=True, timeout=180,
            )
            if result.returncode:
                raise RuntimeError(f"{example} failed:\n{result.stdout}\n{result.stderr}")
            import pandas as pd
            users = pd.read_csv(results / "1_user-stats.csv")
            if len(users) != 100 or not users.request_id.is_unique:
                raise RuntimeError(f"{example} did not execute all 100 unique requests")
            destination = staged / example
            destination.mkdir()
            for filename in ("standard_eval.csv", "1_user-stats.csv"):
                shutil.copyfile(results / filename, destination / filename)
            print(f"{example}: {len(users)} requests; {users.pickup_time.notna().sum()} picked up", flush=True)

        inputs = {
            "data/demand/example_demand/matched/example_network/example_100.csv",
            "data/networks/example_network/base/nodes.csv",
            "data/networks/example_network/base/edges.csv",
            "data/vehicles/default_vehtype.csv",
        }
        for pair in examples.values():
            inputs.update("studies/example_study/scenarios/" + name for name in pair)
        manifest = {
            "source": "https://github.com/TUM-VT/FleetPy",
            "upstream_commit": commit,
            "capture_method": "git archive of the unmodified upstream commit; the same isolated-output runner used by regression tests",
            "python": platform.python_version(),
            "dependencies": {name: importlib.metadata.version(name)
                             for name in ("numpy", "pandas", "scipy", "pyyaml", "gurobipy")},
            "runtime": {"PYTHONHASHSEED": "0", "n_cpu_per_sim": 1, "evaluate": 1,
                        "log_level": "warning", "show_progress_bar": False,
                        "OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1", "MKL_NUM_THREADS": "1"},
            "examples": examples,
            "input_sha256": {name: hashlib.sha256((source / name).read_bytes()).hexdigest()
                             for name in sorted(inputs)},
        }
        (staged / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
        output.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(staged, output)
    print(f"References captured from {commit} to {output}")


if __name__ == "__main__":
    main()
