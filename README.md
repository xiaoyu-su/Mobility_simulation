# 🚖 FleetPy – Open-Source Fleet Simulation Framework  

This is the [xiaoyu-su/Mobility_simulation](https://github.com/xiaoyu-su/Mobility_simulation)
fork of [TUM-VT/FleetPy](https://github.com/TUM-VT/FleetPy). Phase 0 adds upstream
regression references and baseline bug fixes; [Phase 1](docs/PHASE_1.md) adds
opt-in independent random streams and audited paired policy evaluation.
[Phase 2](docs/PHASE_2.md) adds accepted pickup/dropoff promises and optional
mean-one travel-time noise during vehicle execution, with unchanged defaults.
[Phase 3](docs/PHASE_3.md) adds optional logistic driver acceptance, bounded
retries, driver classes, and probability-weighted matching rewards.
[Phase 4](docs/PHASE_4.md) adds optional future-value matching with exact
pickup-ETA ranking and cached fallback estimates.
[Phase 5](docs/PHASE_5.md) adds optional driver menus, an outside choice,
deterministic conflict resolution, and exact single-item compatibility.
[Phase 5b](docs/PHASE_5B.md) adds optional ranked insertion fallback: offer to
distinct feasible drivers in cost order and execute the first accepted plan.
[Phase 5c](docs/PHASE_5C.md) adds optional Alonso-Mora rematching by forbidding
declined request/driver edges and re-solving the retained native assignment graph.
[Phase 6](docs/PHASE_6.md) adds full-state baseline snapshots and parallel
same-controller policy windows, with request-time cohorts and explicit censoring.
[Phase 7](docs/PHASE_7.md) adds a local TLC CSV/Parquet market pipeline,
training-only forecasts/travel fitting and optional HiGHS repositioning.
The public Manhattan data is available. The [production corrections and validation](docs/PHASE_7_COMPLETION.md)
fix causal timing, pooling consent, physical service durations and booking
completion, with full-demand real-data comparisons.
Remaining calibration errors and limits of the public observations are reported
alongside the improvements.
[Phase 8](docs/PHASE_8.md) adds a mixed human/AV product with a service-area
fence, deterministic rider opt-in, a dispatch preference and separate AV
repositioning. Validation passes 339 tests; 18 sampled Manhattan runs report allocation benefits,
human-driver trip transfers, rider waits and empty-driving costs together.
[Phase 9](docs/PHASE_9.md) adds cautious AV travel times, ETA-threshold dispatch,
accepted-product protection, moving-empty retargeting, forecast-error sensitivity
and joint human/AV repositioning. Validation passes 370 tests and 56 real-data
physical runs, including six-seed dispatch comparisons and a full-demand pair; [AV_DATA.md](docs/AV_DATA.md)
separates observed inputs from adoption and speed assumptions.
[Phase 10](docs/PHASE_10.md) adds source-verified Munich/Chicago/Manhattan
policy comparisons with shared physical initialization and matched search budgets.
Validation passes **389 tests and66 real-city runs** (60 unique conditions), with
[measured gains and regressions](docs/validation/phase10/RESULTS.md) recorded together.
[Phase 11](docs/PHASE_11.md) adds clean-upstream native-city fidelity checks
and fresh-process/clean-archive repeatability. **403 tests**, **269 regression
simulations** and **15 native physical runs** pass, with exact original-output
comparisons and [complete evidence](docs/validation/phase11/README.md).
[Phase 12](docs/PHASE_12.md) adds separate-reference AV demand repositioning
across three cities and opt-in passenger service priority over soft empty targets.
**424 tests and 72 real policy runs** pass; [measured results](docs/validation/phase12/RESULTS.md)
retain completion, waits, utilization and empty-driving tradeoffs.
[Phase 13](docs/PHASE_13.md) adds exact Chicago threshold/speed time accounting,
same-request and selection diagnostics, and matched load sensitivities.
**433 tests and 64 real physical runs** pass; [results](docs/validation/phase13/RESULTS.md)
separate trip counts, passenger time, overlap, service dwell and window timing.
[Phase 14](docs/PHASE_14.md) adds matched 4/8/12-minute booking-patience
robustness, strict input-stratum checks, actual-lateness reporting and a fixed
8-minute service target. **442 tests and 90 real physical records** pass;
[results](docs/validation/phase14/ROBUSTNESS.md) retain gains and regressions.
[Phase 15](docs/PHASE_15.md) adds matched 0/30/100% rider opt-in robustness,
fixed-group allocation/spillovers and invariant all-human controls.
**452 tests and90 real physical records** pass;
[results](docs/validation/phase15/ROBUSTNESS.md) retain gains and regressions.
See [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md), [UPSTREAM_COMPARISON.md](UPSTREAM_COMPARISON.md),
and [IMPROVEMENT_LOG.md](IMPROVEMENT_LOG.md) for scope, evidence, and changes.

[![GitHub stars](https://img.shields.io/github/stars/TUM-VT/FleetPy?style=social)](https://github.com/TUM-VT/FleetPy)  
FleetPy is an open-source **fleet simulation framework** for modeling and controlling vehicle fleets in **ride-sharing, autonomous mobility, and on-demand transport** applications.  

> Whether you're a **researcher**, **transportation engineer**, or **mobility innovator**, FleetPy helps you analyze and optimize **fleet operations, routing strategies, and demand-responsive services**.

😶‍🌫️ **[Fleetpy for dummies](https://github.com/TUM-VT/FleetPy/wiki/0_Fleetpy_for_dummies)** 📖 **[Read the Wiki](https://github.com/TUM-VT/FleetPy/wiki)** | 🛠 **[Installation Guide](#-installation)** | 🚀 **[Quickstart](#-quickstart)**  

<img src="https://github.com/user-attachments/assets/ea839af5-3465-4bd1-8ed4-79c8fe0fd524" alt="Fleetpy Logo" height="400">

---

## 🎯 Key Features  

✅ **Agent-Based Simulation** – Models individual vehicles, passengers, and operators.  
✅ **Flexible User-Operator Interaction** – Supports multiple request-acceptance models.  
✅ **Multi-Fleet Management** – Simulates **ride-pooling, dispatching, and EV charging**.  
✅ **Customizable Routing Algorithms** – Choose between memory-efficient and fast methods.  
✅ **Modular & Extensible Design** – Easily integrate **new demand models, routing strategies, or data sources**.  
✅ **Optimized for Large-Scale Scenarios** – Handles thousands of vehicles and requests efficiently.  

---

## 🚀 Quickstart  

Get up and running in just a few commands!  

```bash
# Clone the repository
git clone https://github.com/TUM-VT/FleetPy.git
cd FleetPy

# Set up the virtual environment
conda env create -f environment.yml
conda activate fleetpy

# Run an example simulation
python studies/example_study/run_examples.py
```

✔ The results will be saved in `FleetPy/studies/example_study/results/`  
✔ To visualize the results, run:  

```bash
python replay_pyplot.py scenario_result_directory
```

---

## 🛠 Installation  

### 1️⃣ Install with Conda (Recommended)

Ensure you have [Anaconda](https://www.anaconda.com/products/distribution) installed.

```bash
# Fetch the latest updates
git clone https://github.com/TUM-VT/FleetPy.git
cd FleetPy

# Set up a Conda environment
conda env create -f environment.yml
conda activate fleetpy
```

### 2️⃣ Install C++ Router (Recommended)

For improved road network routing efficiency, compile the C++ road router:

```bash
cd FleetPy/src/routing/road/cpp_router
python setup.py build_ext --inplace
```

To enable public transport routing, compile the C++ RAPTOR router:

```bash
cd FleetPy/src/routing/pt/cpp_raptor_router
python setup.py build_ext --inplace
```

**Ensure a C++ compiler and Cython are installed.**

### 3️⃣ Install Optimizer (Optional)

For advanced optimization tasks, install the necessary optimizers:

#### 🏆 **Gurobi**

To install Gurobi:

```bash
python -m pip install gurobipy==12.0.1
```

You can acquire a **free academic license** from [Gurobi](https://www.gurobi.com/academia/academic-program-and-licenses/). 🎓

#### ⚡ **OR-Tools**

To install Google's OR-Tools:

```bash
pip install ortools
```

This is useful for combinatorial optimization and routing problems.

---

## 📂 Data Preparation and Study Setup

For now, you can inspect the data structures and files in the examples provided in GitHub:

* 📁 `FleetPy/data`
* 📁 `FleetPy/studies`

More detailed descriptions of the **data structure, preprocessing steps, and result data** will be provided in upcoming versions.
Additionally, a **GUI to set up scenarios** (with a choice of submodules and data) is planned for the future. 🎨

In general, you can **save your data and study definitions** in the mentioned directories. These are included in `.gitignore`.

<!-- ... (prepare study by config.csv and scenarios.csv) -->
<!-- ... (necessary modules for preprocessing can be installed by "pip3 install -r requirements_with_pp.txt") -->

---

## 📊 Running a Simulation  

To test an example scenario:  

```bash
python studies/example_study/run_examples.py
```

✔ The output will be stored in:  
📂 `FleetPy/studies/example_study/results/`  

### 📊 Output Files

| File Name            | Description |
|----------------------|-------------|
| `1_user_stats.csv`   | User request statistics |
| `2_0_op-stats.csv`   | Fleet vehicle task logs |
| `standard_eval.csv`  | Aggregated evaluation results |

To analyze trends:

```bash
python FleetPy/src/evaluation/temporal.py scenario_result_directory
```

---

## 🎥 Watch a Replay  

To visualize a **previously simulated scenario**, run:  

```bash
python replay_pyplot.py scenario_result_directory <sim_seconds_per_real_second>
```

🛑 *(Optional: Specify start time as an additional argument.)*

---

## Benchmark Data Sets

Input data and corresponding example scenario files are available for large-scale case studies of Manhattan, NY, Chicago, IL, and Munich, Germany. This data can be used as benchmark data sets to test and compare new algorithms or to set up large-scale simulations quickly. The FleetPy input data can be downloaded here and has to be copied into the FleetPy/data folder:

- Manhattan: https://doi.org/10.5281/zenodo.15187906
- Chicago: https://doi.org/10.5281/zenodo.15189440
- Munich: https://doi.org/10.5281/zenodo.15195726

See the studies in `FleetPy/studies` for example scenario files that use this data. Especially the `FleetPy/studies/paper_2025_applications` contains a detailed example for a Manhattan case study.

---

## Reproducability

We encourage users to share their simulation setups, data, and results to foster reproducibility and collaboration. If you use FleetPy for your research or projects, please consider sharing your scenario definitions, input data, and results with the community. You can do this by:

1. Creating a public fork of the FleetPy repository if you have made significant modifications or extensions to the codebase.
2. Setting up all your scenario definitions, preprocessing scripts and evaluation scripts in a structured way within the `studies` directory, following the existing examples.
3. Creating a README file in your study directory that describes the key facts of your study.
4. Using the script "zip_study.py" to create a zip file of your study, which includes specified input data, source code, and files in the `studies` directory.
5. Sharing the zip file on a public repository or platform (e.g., GitHub, Zenodo) and sharing the link when publishing.

---

## 🤝 Contributing  

We welcome contributions from the community! 🚀  
📌 **How to contribute:**  

1. Fork the repo & create a feature branch (`git checkout -b new-feature`).  
2. Commit your changes (`git commit -m "Added a cool feature"`).  
3. Push to your branch (`git push origin new-feature`).  
4. Make sure that the module tests are running (`\studies\module_tests\run_module_tests.py`).
5. Open a Pull Request!  

<!-- ... TODO: contributing.md 
🔍 Check out [CONTRIBUTING.md](link) for guidelines.  
-->

---

## 📢 Get Involved  

💬 **Join the discussion:** [GitHub Discussions](https://github.com/TUM-VT/FleetPy/discussions)  
💻 **Contribute:** Open an issue or PR!  
⭐ **Support FleetPy:** Give us a **star ⭐** on GitHub!  
🚀 **Stay updated:** Follow us on [Homepage](https://www.mos.ed.tum.de/en/vt/home/) & [LinkedIn](https://www.linkedin.com/school/tum-chair-of-traffic-engineering-and-control/)  

---

## 📌 Tested on  

✔ **Windows 10 Pro x64**  
✔ **Chrome 79.0.3945**  
✔ **Python 3.10**  

---

## 🧪 Research Projects Using FleetPy

FleetPy has been applied in various academic and applied research projects across topics like shared mobility, autonomous vehicle operations, and electrified fleets:

### Ongoing Projects

* **[CONDUCTOR](https://conductor-project.eu/?show=consortium)** – Development of an integrated ride-parcel-pooling service using automated vehicles (CCAM), evaluated via FleetPy-Aimsun coupling *(multi-modal integration, AVs, cooperative routing, traffic control, simulation coupling)*
* **[metaCCAZE](https://www.metaccaze-project.eu/)** – Scientific support and simulation-based evaluation of Munich’s Living Lab innovations including multimodal logistics hubs, dynamic curbside management, and connected/autonomous last-mile vehicles. FleetPy contributes to monitoring and optimizing operations *(multimodal hubs, curbside management, AV logistics, LL evaluation, policy support)*
* **[MINGA](https://www.mos.ed.tum.de/en/vt/research/projects/current-projects/minga/)** – Evaluation of AV stop concepts and passenger interactions at TUM’s test field. FleetPy is used alongside MATSim and microscopic traffic simulations to model AV and non-AV traffic, evaluate climate and system-wide impacts, and support accessibility-focused user studies *(AV integration, stop concepts, MATSim coupling, KPI evaluation, accessibility research)*
* **[STADT:up](https://www.mos.ed.tum.de/en/vt/research/projects/current-projects/stadtup/)** – Simulation of autonomous shuttle bus in different inter-mobility scenarios with dynamic stops *(Operation, traffic evaluation)*
* **[SUM (Seamless Shared Urban Mobility)](https://sum-project.eu/)** – Simulation-based evaluation of operational strategies for automated on-demand fleets in Munich using FleetPy, including integration with public transport, pricing strategies, and transferability to future mobility hubs *(on-demand AV fleets, public transport integration, pricing, living lab scalability)*

### Completed Projects

* **[MOIA](https://www.mos.ed.tum.de/en/vt/forschung/projekte/abgeschlossene-projekte/moia-accompanying-research-completed-2021/)** – Implementation of algorithms to represent MOIA’s fleet control *(operation, ride-pooling)*

* **[MCube: STEAM](https://mcube-cluster.de/en/projekt/steam/)** – Simulation of semi-flexible bus lines in Munich using FleetPy, integrated with the TUM-OSM decision support system *(agent-based simulation, semi-flexible transit, DSS coupling, urban mobility, evaluation pipeline)*

> 🧠 Do you use FleetPy in your research? [Let us know!](mailto:florian.dandl@tum.de)

---

## Citation

If you find this framework useful for your work or use it in your project, please consider citing:
Engelhardt, R., Dandl, F., Syed, A., Zhang, Y., Fehn, F., Wolf, F., Bogenberger, K. (2022). FleetPy: A Modular Open-Source Simulation Tool for Mobility On-Demand Services. Arxiv pre-print

```
@misc{engelhardt2022fleetpymodularopensourcesimulation,
      title={FleetPy: A Modular Open-Source Simulation Tool for Mobility On-Demand Services}, 
      author={Roman Engelhardt and Florian Dandl and Arslan-Ali Syed and Yunfei Zhang and Fabian Fehn and Fynn Wolf and Klaus Bogenberger},
      year={2022},
      eprint={2207.14246},
      archivePrefix={arXiv},
      primaryClass={cs.MA},
      url={https://arxiv.org/abs/2207.14246}, 
}
```
